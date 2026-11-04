import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import ANCVisit, RiskFactor
from ..schemas.clinical import ANCVisitCreate, ANCVisitUpdate
from ..services.auth_service import get_current_user, require_role, log_audit
from ..services.clinical_rules import evaluate_clinical_rules

router = APIRouter(prefix="/api/anc", tags=["Antenatal Care (ANC) Tracking"])

@router.get("/due-list")
def get_anc_due_list(
    status_filter: Optional[str] = None, # DUE_SOON, OVERDUE, COMPLETED
    village: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.date.today()
    query = db.query(ANCVisit).join(PregnancyRecord, ANCVisit.pregnancy_id == PregnancyRecord.pregnancy_id)\
                              .join(Beneficiary, ANCVisit.beneficiary_id == Beneficiary.beneficiary_id)\
                              .filter(PregnancyRecord.status == "ACTIVE")

    if current_user.role == UserRole.ASHA and current_user.village:
        query = query.filter(Beneficiary.village == current_user.village)
    elif village:
        query = query.filter(Beneficiary.village.ilike(f"%{village}%"))

    visits = query.order_by(ANCVisit.scheduled_date.asc()).all()
    results = []

    for v in visits:
        # Dynamic check of status against today's date if not yet completed
        calc_status = v.status
        if v.status not in ("COMPLETED", "DEFERRED"):
            if v.scheduled_date < today:
                calc_status = "OVERDUE"
            elif v.scheduled_date <= today + datetime.timedelta(days=7):
                calc_status = "DUE_SOON"
            else:
                calc_status = "NOT_YET_DUE"

        if status_filter and calc_status != status_filter:
            continue

        v_dict = v.to_dict()
        v_dict["calculated_status"] = calc_status
        ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == v.beneficiary_id).first()
        prg = db.query(PregnancyRecord).filter(PregnancyRecord.pregnancy_id == v.pregnancy_id).first()
        v_dict["beneficiary_name"] = ben.full_name if ben else "Unknown"
        v_dict["village"] = ben.village if ben else "Unknown"
        v_dict["contact_phone"] = ben.contact_phone if ben else None
        v_dict["high_risk_flag"] = prg.high_risk_flag if prg else False
        results.append(v_dict)

    return results

@router.post("/record-visit")
def record_anc_visit(
    visit_data: ANCVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    prg = db.query(PregnancyRecord).filter(PregnancyRecord.pregnancy_id == visit_data.pregnancy_id).first()
    if not prg:
        raise HTTPException(status_code=404, detail="Pregnancy record not found")

    v_uuid = visit_data.visit_uuid or f"ANC-{uuid.uuid4().hex[:8].upper()}"
    anc = db.query(ANCVisit).filter(ANCVisit.visit_uuid == v_uuid).first()

    if not anc:
        anc = ANCVisit(
            visit_uuid=v_uuid,
            pregnancy_id=visit_data.pregnancy_id,
            beneficiary_id=visit_data.beneficiary_id,
            anc_period=visit_data.anc_period,
            scheduled_date=visit_data.scheduled_date,
            actual_visit_date=visit_data.actual_visit_date or datetime.date.today(),
            status=visit_data.status or "COMPLETED",
            gestational_age_weeks=visit_data.gestational_age_weeks,
            recorded_by_user_id=current_user.id,
            weight_kg=visit_data.weight_kg,
            bp_systolic=visit_data.bp_systolic,
            bp_diastolic=visit_data.bp_diastolic,
            hemoglobin_g_dl=visit_data.hemoglobin_g_dl,
            urine_albumin=visit_data.urine_albumin or "NOT_DONE",
            urine_sugar=visit_data.urine_sugar or "NOT_DONE",
            ultrasound_status=visit_data.ultrasound_status,
            ifa_tablets_issued=visit_data.ifa_tablets_issued or 0,
            calcium_tablets_issued=visit_data.calcium_tablets_issued or 0,
            tt_td_dose=visit_data.tt_td_dose or "NONE",
            counselling_topics=visit_data.counselling_topics,
            deferral_reason=visit_data.deferral_reason,
            clinical_notes=visit_data.clinical_notes,
            sync_status="SYNCHRONIZED"
        )
        db.add(anc)
    else:
        anc.actual_visit_date = visit_data.actual_visit_date or datetime.date.today()
        anc.status = visit_data.status or "COMPLETED"
        anc.weight_kg = visit_data.weight_kg
        anc.bp_systolic = visit_data.bp_systolic
        anc.bp_diastolic = visit_data.bp_diastolic
        anc.hemoglobin_g_dl = visit_data.hemoglobin_g_dl
        anc.urine_albumin = visit_data.urine_albumin or anc.urine_albumin
        anc.urine_sugar = visit_data.urine_sugar or anc.urine_sugar
        anc.counselling_topics = visit_data.counselling_topics or anc.counselling_topics
        anc.clinical_notes = visit_data.clinical_notes or anc.clinical_notes
        anc.recorded_by_user_id = current_user.id

    # Evaluate clinical rules on measured metrics
    risk_flags = evaluate_clinical_rules(
        bp_systolic=visit_data.bp_systolic,
        bp_diastolic=visit_data.bp_diastolic,
        hemoglobin_g_dl=visit_data.hemoglobin_g_dl,
        urine_albumin=visit_data.urine_albumin
    )
    if risk_flags:
        prg.high_risk_flag = True
        for flag in risk_flags:
            rf = RiskFactor(
                risk_uuid=f"RISK-{uuid.uuid4().hex[:8].upper()}",
                pregnancy_id=prg.pregnancy_id,
                rule_code=flag.get("rule_code"),
                risk_title=flag.get("risk_title"),
                risk_detail=flag.get("risk_detail"),
                severity=flag.get("severity", "HIGH"),
                status=flag.get("status", "RULE_FLAGGED"),
                requires_professional_review=True,
                recorded_by_user_id=current_user.id
            )
            db.add(rf)

    db.commit()
    db.refresh(anc)

    log_audit(
        db,
        action="RECORD_ANC_VISIT",
        user=current_user,
        target_entity="anc_visit",
        target_id=anc.visit_uuid,
        details=f"Recorded {anc.anc_period} for beneficiary {anc.beneficiary_id}. Flags triggered: {len(risk_flags)}"
    )

    return {
        "message": "ANC visit recorded successfully",
        "visit": anc.to_dict(),
        "risk_flags_detected": risk_flags
    }


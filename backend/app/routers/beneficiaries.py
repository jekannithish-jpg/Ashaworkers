import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import ANCVisit, RiskFactor, PNCVisit, Referral, HomeVisit
from ..schemas.beneficiary import BeneficiaryCreate, BeneficiaryUpdate, DuplicateCheckRequest, DuplicateCheckResponse
from ..services.auth_service import get_current_user, require_role, log_audit
from ..services.clinical_rules import calculate_edd, generate_standard_anc_schedule, evaluate_clinical_rules

router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiary Registration & Profiles"])

@router.post("/duplicate-check", response_model=DuplicateCheckResponse)
def check_duplicates(
    req: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Beneficiary).filter(Beneficiary.village.ilike(f"%{req.village}%"))
    if req.contact_phone:
        query = query.filter((Beneficiary.contact_phone == req.contact_phone) | (Beneficiary.full_name.ilike(f"%{req.full_name}%")))
    else:
        query = query.filter(Beneficiary.full_name.ilike(f"%{req.full_name}%"))

    matches = query.limit(5).all()
    results = [m.to_dict() for m in matches]
    return DuplicateCheckResponse(
        is_possible_duplicate=len(results) > 0,
        matches=results
    )

@router.post("", status_code=status.HTTP_201_CREATED)
def register_beneficiary(
    ben_in: BeneficiaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    # Determine unique stable internal beneficiary ID
    ben_id = ben_in.beneficiary_id
    if not ben_id:
        count = db.query(Beneficiary).count() + 1
        ben_id = f"BEN-{datetime.date.today().year}-{count:04d}"

    # Verify uniqueness
    if db.query(Beneficiary).filter(Beneficiary.beneficiary_id == ben_id).first():
        ben_id = f"BEN-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"

    new_ben = Beneficiary(
        beneficiary_id=ben_id,
        full_name=ben_in.full_name,
        age=ben_in.age,
        dob=ben_in.dob,
        contact_phone=ben_in.contact_phone,
        village=ben_in.village,
        sub_centre=ben_in.sub_centre,
        primary_health_centre=ben_in.primary_health_centre,
        assigned_asha_id=current_user.id if current_user.role == UserRole.ASHA else None,
        preferred_language=ben_in.preferred_language or "ta",
        consent_obtained=ben_in.consent_obtained,
        privacy_notice_acknowledged=ben_in.privacy_notice_acknowledged,
        is_draft=ben_in.is_draft,
        version_id=1
    )
    db.add(new_ben)
    db.flush()

    # Create associated pregnancy record
    prg_id = f"PRG-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"
    edd_date = calculate_edd(ben_in.lmp_date) if ben_in.lmp_date else None

    new_prg = PregnancyRecord(
        pregnancy_id=prg_id,
        beneficiary_id=new_ben.beneficiary_id,
        gravida=ben_in.gravida or 1,
        parity=ben_in.parity or 0,
        lmp_date=ben_in.lmp_date,
        edd_date=edd_date,
        is_edd_estimated=True,
        confirmation_date=ben_in.confirmation_date,
        registration_date=ben_in.registration_date or datetime.date.today(),
        status="ACTIVE",
        past_obstetric_history=ben_in.past_obstetric_history,
        known_medical_conditions=ben_in.known_medical_conditions,
        assigned_facility_id=ben_in.assigned_facility_id,
        high_risk_flag=False,
        version_id=1
    )
    db.add(new_prg)
    db.flush()

    # Automatically generate 4 ANC visits if LMP is available
    if ben_in.lmp_date:
        anc_schedule = generate_standard_anc_schedule(ben_in.lmp_date)
        today = datetime.date.today()
        for idx, item in enumerate(anc_schedule, 1):
            sched_date = item["scheduled_date"]
            if sched_date < today:
                status_val = "OVERDUE"
            elif sched_date <= today + datetime.timedelta(days=14):
                status_val = "DUE_SOON"
            else:
                status_val = "NOT_YET_DUE"

            anc_visit = ANCVisit(
                visit_uuid=f"ANC-{new_prg.pregnancy_id}-{idx}",
                pregnancy_id=new_prg.pregnancy_id,
                beneficiary_id=new_ben.beneficiary_id,
                anc_period=item["anc_period"],
                scheduled_date=sched_date,
                status=status_val,
                recorded_by_user_id=current_user.id,
                sync_status="SYNCHRONIZED"
            )
            db.add(anc_visit)

    # Evaluate any initial high-risk flags based on age or obstetric history
    initial_flags = evaluate_clinical_rules(
        age=ben_in.age,
        past_obstetric_history=ben_in.past_obstetric_history,
        known_medical_conditions=ben_in.known_medical_conditions
    )
    if initial_flags:
        new_prg.high_risk_flag = True
        for flag in initial_flags:
            rf = RiskFactor(
                risk_uuid=f"RISK-{uuid.uuid4().hex[:8].upper()}",
                pregnancy_id=new_prg.pregnancy_id,
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
    db.refresh(new_ben)

    log_audit(
        db,
        action="CREATE_BENEFICIARY",
        user=current_user,
        target_entity="beneficiary",
        target_id=new_ben.beneficiary_id,
        details=f"Registered beneficiary {new_ben.full_name} in village {new_ben.village}"
    )

    return {
        "message": "Beneficiary registered successfully",
        "beneficiary": new_ben.to_dict(),
        "pregnancy": new_prg.to_dict()
    }

@router.get("")
def list_beneficiaries(
    village: Optional[str] = None,
    high_risk: Optional[bool] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Beneficiary).filter(Beneficiary.is_active == True)

    # Filter by user role and assignment if field worker
    if current_user.role == UserRole.ASHA and current_user.village:
        query = query.filter(Beneficiary.village == current_user.village)
    elif current_user.role == UserRole.ANM and current_user.sub_centre:
        query = query.filter(Beneficiary.sub_centre == current_user.sub_centre)

    if village:
        query = query.filter(Beneficiary.village.ilike(f"%{village}%"))
    if search:
        query = query.filter(
            (Beneficiary.full_name.ilike(f"%{search}%")) |
            (Beneficiary.beneficiary_id.ilike(f"%{search}%")) |
            (Beneficiary.contact_phone.ilike(f"%{search}%"))
        )

    beneficiaries = query.order_by(Beneficiary.id.desc()).all()
    results = []
    for b in beneficiaries:
        b_dict = b.to_dict()
        # Attach latest active pregnancy
        active_prg = db.query(PregnancyRecord).filter(
            PregnancyRecord.beneficiary_id == b.beneficiary_id
        ).order_by(PregnancyRecord.id.desc()).first()

        if active_prg:
            if status and active_prg.status != status:
                continue
            if high_risk is not None and active_prg.high_risk_flag != high_risk:
                continue
            b_dict["active_pregnancy"] = active_prg.to_dict()
        elif high_risk is True:
            continue
        results.append(b_dict)

    log_audit(db, action="VIEW_BENEFICIARIES_LIST", user=current_user, details=f"Retrieved {len(results)} records")
    return results

@router.get("/{beneficiary_id}")
def get_beneficiary_details(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    prg = db.query(PregnancyRecord).filter(PregnancyRecord.beneficiary_id == beneficiary_id).order_by(PregnancyRecord.id.desc()).first()
    anc_visits = []
    pnc_visits = []
    risk_factors = []
    referrals = []

    if prg:
        anc_visits = [v.to_dict() for v in db.query(ANCVisit).filter(ANCVisit.pregnancy_id == prg.pregnancy_id).order_by(ANCVisit.scheduled_date.asc()).all()]
        pnc_visits = [v.to_dict() for v in db.query(PNCVisit).filter(PNCVisit.pregnancy_id == prg.pregnancy_id).order_by(PNCVisit.scheduled_date.asc()).all()]
        risk_factors = [r.to_dict() for r in db.query(RiskFactor).filter(RiskFactor.pregnancy_id == prg.pregnancy_id).all()]
        referrals = [r.to_dict() for r in db.query(Referral).filter(Referral.pregnancy_id == prg.pregnancy_id).all()]

    home_visits = [h.to_dict() for h in db.query(HomeVisit).filter(HomeVisit.beneficiary_id == beneficiary_id).order_by(HomeVisit.visit_date.desc()).all()]

    log_audit(db, action="VIEW_BENEFICIARY", user=current_user, target_entity="beneficiary", target_id=beneficiary_id)

    return {
        "beneficiary": ben.to_dict(),
        "pregnancy": prg.to_dict() if prg else None,
        "anc_visits": anc_visits,
        "pnc_visits": pnc_visits,
        "home_visits": home_visits,
        "risk_factors": risk_factors,
        "referrals": referrals
    }

@router.put("/{beneficiary_id}")
def update_beneficiary(
    beneficiary_id: str,
    ben_update: BeneficiaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    update_data = ben_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(ben, field, val)
    ben.version_id += 1

    db.commit()
    db.refresh(ben)

    log_audit(db, action="UPDATE_BENEFICIARY", user=current_user, target_entity="beneficiary", target_id=beneficiary_id, details=str(update_data))
    return ben.to_dict()

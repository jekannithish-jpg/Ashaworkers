import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import PNCVisit
from ..schemas.clinical import PNCVisitCreate
from ..services.auth_service import get_current_user, require_role, log_audit
from ..services.clinical_rules import generate_standard_pnc_schedule

router = APIRouter(prefix="/api/pnc", tags=["Postnatal Care (PNC) Tracking"])

@router.get("/due-list")
def get_pnc_due_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.date.today()
    query = db.query(PNCVisit).join(PregnancyRecord, PNCVisit.pregnancy_id == PregnancyRecord.pregnancy_id)\
                              .join(Beneficiary, PNCVisit.beneficiary_id == Beneficiary.beneficiary_id)

    if current_user.role == UserRole.ASHA and current_user.village:
        query = query.filter(Beneficiary.village == current_user.village)

    visits = query.order_by(PNCVisit.scheduled_date.asc()).all()
    results = []
    for v in visits:
        calc_status = v.status
        if v.status not in ("COMPLETED", "DEFERRED"):
            if v.scheduled_date < today:
                calc_status = "OVERDUE"
            elif v.scheduled_date <= today + datetime.timedelta(days=3):
                calc_status = "DUE_SOON"
            else:
                calc_status = "NOT_YET_DUE"

        v_dict = v.to_dict()
        v_dict["calculated_status"] = calc_status
        ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == v.beneficiary_id).first()
        v_dict["beneficiary_name"] = ben.full_name if ben else "Unknown"
        v_dict["village"] = ben.village if ben else "Unknown"
        v_dict["contact_phone"] = ben.contact_phone if ben else None
        results.append(v_dict)

    return results

@router.post("/record-visit")
def record_pnc_visit(
    visit_data: PNCVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    v_uuid = visit_data.pnc_uuid or f"PNC-{uuid.uuid4().hex[:8].upper()}"
    pnc = db.query(PNCVisit).filter(PNCVisit.pnc_uuid == v_uuid).first()

    if not pnc:
        pnc = PNCVisit(
            pnc_uuid=v_uuid,
            pregnancy_id=visit_data.pregnancy_id,
            beneficiary_id=visit_data.beneficiary_id,
            pnc_interval=visit_data.pnc_interval,
            delivery_date=visit_data.delivery_date,
            delivery_facility=visit_data.delivery_facility,
            scheduled_date=visit_data.scheduled_date,
            actual_visit_date=visit_data.actual_visit_date or datetime.date.today(),
            status="COMPLETED",
            maternal_assessment_status=visit_data.maternal_assessment_status,
            newborn_follow_up_status=visit_data.newborn_follow_up_status,
            feeding_counselling_provided=visit_data.feeding_counselling_provided,
            danger_signs_reported=visit_data.danger_signs_reported,
            referral_initiated=visit_data.referral_initiated,
            recorded_by_user_id=current_user.id
        )
        db.add(pnc)
    else:
        pnc.actual_visit_date = visit_data.actual_visit_date or datetime.date.today()
        pnc.status = "COMPLETED"
        pnc.maternal_assessment_status = visit_data.maternal_assessment_status
        pnc.newborn_follow_up_status = visit_data.newborn_follow_up_status
        pnc.feeding_counselling_provided = visit_data.feeding_counselling_provided
        pnc.danger_signs_reported = visit_data.danger_signs_reported
        pnc.referral_initiated = visit_data.referral_initiated
        pnc.recorded_by_user_id = current_user.id

    db.commit()
    db.refresh(pnc)

    log_audit(
        db,
        action="RECORD_PNC_VISIT",
        user=current_user,
        target_entity="pnc_visit",
        target_id=pnc.pnc_uuid,
        details=f"Documented {pnc.pnc_interval} for beneficiary {pnc.beneficiary_id}"
    )

    return {
        "message": "PNC visit recorded successfully",
        "visit": pnc.to_dict()
    }


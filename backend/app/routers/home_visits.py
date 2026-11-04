import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import HomeVisit
from ..schemas.clinical import HomeVisitCreate
from ..services.auth_service import get_current_user, require_role, log_audit

router = APIRouter(prefix="/api/home-visits", tags=["Home Visit Management"])

@router.post("", status_code=status.HTTP_201_CREATED)
def record_home_visit(
    visit_in: HomeVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    prg_id = visit_in.pregnancy_id
    if not prg_id and visit_in.beneficiary_id:
        prg = db.query(PregnancyRecord).filter(
            PregnancyRecord.beneficiary_id == visit_in.beneficiary_id,
            PregnancyRecord.status == "ACTIVE"
        ).first()
        if prg:
            prg_id = prg.pregnancy_id

    v_uuid = visit_in.visit_uuid or f"HV-{uuid.uuid4().hex[:8].upper()}"
    new_hv = HomeVisit(
        visit_uuid=v_uuid,
        pregnancy_id=prg_id,
        beneficiary_id=visit_in.beneficiary_id,
        visit_date=visit_in.visit_date,
        assigned_worker_id=current_user.id,
        visit_purpose=visit_in.visit_purpose,
        is_completed=visit_in.is_completed,
        observations=visit_in.observations,
        counselling_topics=visit_in.counselling_topics,
        follow_up_tasks=visit_in.follow_up_tasks,
        referral_initiated=visit_in.referral_initiated,
        next_visit_date=visit_in.next_visit_date,
        notes=visit_in.notes,
        is_draft=visit_in.is_draft,
        latitude=visit_in.latitude,
        longitude=visit_in.longitude,
        gps_accuracy=visit_in.gps_accuracy,
        survey_type=visit_in.survey_type or "ROUTINE_HOME_VISIT",
        survey_data=visit_in.survey_data,
        sync_status="SYNCHRONIZED"
    )
    db.add(new_hv)
    db.commit()
    db.refresh(new_hv)

    gps_info = f" (GPS: {new_hv.latitude:.4f}, {new_hv.longitude:.4f})" if new_hv.latitude and new_hv.longitude else ""
    log_audit(
        db,
        action="RECORD_HOME_VISIT",
        user=current_user,
        target_entity="home_visit",
        target_id=new_hv.visit_uuid,
        details=f"Home visit recorded for {new_hv.beneficiary_id}. Purpose: {new_hv.visit_purpose}{gps_info}"
    )

    return {
        "message": "Home visit recorded successfully",
        "home_visit": new_hv.to_dict()
    }

@router.get("")
def list_home_visits(
    beneficiary_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(HomeVisit).order_by(HomeVisit.visit_date.desc())
    if beneficiary_id:
        query = query.filter(HomeVisit.beneficiary_id == beneficiary_id)

    if current_user.role == UserRole.ASHA:
        query = query.filter(HomeVisit.assigned_worker_id == current_user.id)

    visits = query.limit(50).all()
    results = []
    for v in visits:
        v_dict = v.to_dict()
        ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == v.beneficiary_id).first()
        v_dict["beneficiary_name"] = ben.full_name if ben else "Unknown"
        results.append(v_dict)

    return results


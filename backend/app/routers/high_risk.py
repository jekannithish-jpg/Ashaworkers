import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import RiskFactor, ClinicalRule
from ..schemas.clinical import RiskFactorCreate, RiskFactorReview
from ..services.auth_service import get_current_user, require_role, log_audit

router = APIRouter(prefix="/api/high-risk", tags=["High-Risk Pregnancy (HRP) Tracking"])

@router.get("")
def list_high_risk_cases(
    status_filter: Optional[str] = None, # RULE_FLAGGED, CONFIRMED_HIGH_RISK, RESOLVED
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(RiskFactor).join(PregnancyRecord, RiskFactor.pregnancy_id == PregnancyRecord.pregnancy_id)\
                                .join(Beneficiary, PregnancyRecord.beneficiary_id == Beneficiary.beneficiary_id)

    if current_user.role == UserRole.ASHA and current_user.village:
        query = query.filter(Beneficiary.village == current_user.village)

    if status_filter:
        query = query.filter(RiskFactor.status == status_filter)

    risk_factors = query.order_by(RiskFactor.created_at.desc()).all()
    results = []
    for rf in risk_factors:
        r_dict = rf.to_dict()
        prg = db.query(PregnancyRecord).filter(PregnancyRecord.pregnancy_id == rf.pregnancy_id).first()
        ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == prg.beneficiary_id).first() if prg else None
        rule = db.query(ClinicalRule).filter(ClinicalRule.rule_code == rf.rule_code).first() if rf.rule_code else None

        r_dict["beneficiary_name"] = ben.full_name if ben else "Unknown"
        r_dict["beneficiary_id"] = ben.beneficiary_id if ben else "Unknown"
        r_dict["village"] = ben.village if ben else "Unknown"
        r_dict["contact_phone"] = ben.contact_phone if ben else None
        r_dict["rule_details"] = rule.to_dict() if rule else None
        results.append(r_dict)

    return results

@router.post("/flag", status_code=status.HTTP_201_CREATED)
def flag_high_risk_condition(
    risk_in: RiskFactorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    prg = db.query(PregnancyRecord).filter(PregnancyRecord.pregnancy_id == risk_in.pregnancy_id).first()
    if not prg:
        raise HTTPException(status_code=404, detail="Pregnancy record not found")

    r_uuid = risk_in.risk_uuid or f"RISK-{uuid.uuid4().hex[:8].upper()}"
    new_rf = RiskFactor(
        risk_uuid=r_uuid,
        pregnancy_id=risk_in.pregnancy_id,
        rule_code=risk_in.rule_code,
        risk_title=risk_in.risk_title,
        risk_detail=risk_in.risk_detail,
        severity=risk_in.severity,
        status="REPORTED" if current_user.role == UserRole.ASHA else "ASSESSMENT_PENDING",
        requires_professional_review=True,
        recorded_by_user_id=current_user.id,
        follow_up_due_date=risk_in.follow_up_due_date
    )
    prg.high_risk_flag = True
    db.add(new_rf)
    db.commit()
    db.refresh(new_rf)

    log_audit(
        db,
        action="FLAG_HIGH_RISK",
        user=current_user,
        target_entity="risk_factor",
        target_id=new_rf.risk_uuid,
        details=f"Flagged risk: {new_rf.risk_title} for pregnancy {new_rf.pregnancy_id}"
    )

    return {
        "message": "High-risk condition flagged successfully",
        "risk_factor": new_rf.to_dict()
    }

@router.post("/{risk_uuid}/review")
def review_high_risk_condition(
    risk_uuid: str,
    review_data: RiskFactorReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    rf = db.query(RiskFactor).filter(RiskFactor.risk_uuid == risk_uuid).first()
    if not rf:
        raise HTTPException(status_code=404, detail="Risk factor record not found")

    rf.status = review_data.status
    rf.clinical_plan = review_data.clinical_plan
    rf.confirmed_by_doctor_id = current_user.id
    if review_data.follow_up_due_date:
        rf.follow_up_due_date = review_data.follow_up_due_date
    rf.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(rf)

    log_audit(
        db,
        action="REVIEW_HIGH_RISK",
        user=current_user,
        target_entity="risk_factor",
        target_id=rf.risk_uuid,
        details=f"Professional review updated status to {rf.status}"
    )

    return {
        "message": "Clinical review recorded successfully",
        "risk_factor": rf.to_dict()
    }


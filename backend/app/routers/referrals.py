import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import DangerSign, Referral, HealthFacility
from ..schemas.clinical import ReferralCreate, ReferralOutcomeUpdate
from ..services.auth_service import get_current_user, require_role, log_audit

router = APIRouter(prefix="/api/referrals", tags=["Danger Signs & Referrals"])

@router.get("/danger-signs")
def get_danger_signs_catalog(db: Session = Depends(get_db)):
    signs = db.query(DangerSign).all()
    return [s.to_dict() for s in signs]

@router.get("/facilities")
def get_facilities(db: Session = Depends(get_db)):
    facilities = db.query(HealthFacility).all()
    return [f.to_dict() for f in facilities]

@router.post("/initiate", status_code=status.HTTP_201_CREATED)
def initiate_referral(
    ref_in: ReferralCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ASHA, UserRole.ANM, UserRole.MEDICAL_OFFICER]))
):
    prg = db.query(PregnancyRecord).filter(PregnancyRecord.pregnancy_id == ref_in.pregnancy_id).first()
    if not prg:
        raise HTTPException(status_code=404, detail="Pregnancy record not found")

    r_uuid = ref_in.referral_uuid or f"REF-{uuid.uuid4().hex[:8].upper()}"
    booking_code = f"EMG-{datetime.datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:4].upper()}"
    new_ref = Referral(
        referral_uuid=r_uuid,
        pregnancy_id=ref_in.pregnancy_id,
        beneficiary_id=ref_in.beneficiary_id,
        danger_sign_code=ref_in.danger_sign_code,
        reason=ref_in.reason,
        urgency=ref_in.urgency,
        referring_user_id=current_user.id,
        destination_facility_id=ref_in.destination_facility_id,
        transport_mode=ref_in.transport_mode or "EMERGENCY_AMBULANCE_108",
        referral_initiated_at=datetime.datetime.utcnow(),
        facility_acknowledged=False,
        outcome_status="PENDING",
        is_resolved=False
    )
    prg.high_risk_flag = True
    db.add(new_ref)
    db.commit()
    db.refresh(new_ref)

    fac = db.query(HealthFacility).filter(HealthFacility.id == new_ref.destination_facility_id).first()
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == new_ref.beneficiary_id).first()

    sms_text = (
        f"🚨 108 EMERGENCY OBSTETRIC REFERRAL\n"
        f"Dispatch Code: {booking_code}\n"
        f"Patient: {ben.full_name if ben else new_ref.beneficiary_id} ({ben.village if ben else 'Village'})\n"
        f"Phone: {ben.contact_phone if ben else 'N/A'}\n"
        f"Danger Sign: {new_ref.danger_sign_code or 'Acute Complication'}\n"
        f"Destination: {fac.facility_name if fac else 'PHC'}\n"
        f"ASHA: {current_user.full_name} ({current_user.phone_number or ''})"
    )

    log_audit(
        db,
        action="EMERGENCY_REFERRAL",
        user=current_user,
        target_entity="referral",
        target_id=new_ref.referral_uuid,
        details=f"Urgent referral initiated for {new_ref.beneficiary_id}. Booking Code: {booking_code}, Destination: {fac.facility_name if fac else ''}"
    )

    return {
        "message": "Referral initiated successfully",
        "emergency_booking_code": booking_code,
        "sms_notification_text": sms_text,
        "emergency_instruction": "Place mother in left lateral position. Call 108 immediately if critical transport is required. Accompany patient with MCP card.",
        "referral": new_ref.to_dict()
    }

@router.post("/{referral_uuid}/send-sms")
def dispatch_referral_sms(
    referral_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = db.query(Referral).filter(Referral.referral_uuid == referral_uuid).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == ref.beneficiary_id).first()
    fac = db.query(HealthFacility).filter(HealthFacility.id == ref.destination_facility_id).first()
    
    code = f"EMG-{ref.referral_uuid[-6:]}"
    sms_text = (
        f"108 ALERT: OBSTETRIC EMERGENCY REFERRAL\n"
        f"Code: {code}\n"
        f"Patient: {ben.full_name if ben else ref.beneficiary_id} ({ben.village if ben else ''})\n"
        f"Contact: {ben.contact_phone if ben else 'N/A'}\n"
        f"Facility: {fac.facility_name if fac else 'Nearest Hospital'}\n"
        f"Reason: {ref.reason}\n"
        f"ASHA: {current_user.full_name} ({current_user.phone_number or ''})"
    )
    
    log_audit(
        db,
        action="SMS_DISPATCHED",
        user=current_user,
        target_entity="referral",
        target_id=ref.referral_uuid,
        details=f"Simulated SMS alert dispatched to 108 Dispatch & Medical Officer for {ref.beneficiary_id}"
    )
    
    return {
        "status": "SENT_TO_GATEWAY",
        "message": "Emergency SMS dispatched to 108 ambulance dispatch and receiving hospital desk.",
        "sms_text": sms_text,
        "emergency_code": code,
        "destination_facility": fac.facility_name if fac else "District Hospital"
    }

@router.get("/emergency-info")
def get_emergency_info(
    db: Session = Depends(get_db)
):
    facilities = db.query(HealthFacility).all()
    contacts = [
        {"name": "108 Emergency Ambulance", "number": "108", "type": "Ambulance", "is_toll_free": True},
        {"name": "102 Janani Shishu Suraksha (JSSK)", "number": "102", "type": "Maternal Transport", "is_toll_free": True},
        {"name": "104 Health Information Helpline", "number": "104", "type": "Medical Advice", "is_toll_free": True},
        {"name": "1098 Childline India", "number": "1098", "type": "Child Support", "is_toll_free": True},
        {"name": "181 Women Helpline", "number": "181", "type": "Women Safety", "is_toll_free": True},
    ]
    return {
        "emergency_contacts": contacts,
        "facilities": [f.to_dict() for f in facilities]
    }

@router.get("")
def list_referrals(
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Referral).join(PregnancyRecord, Referral.pregnancy_id == PregnancyRecord.pregnancy_id)\
                              .join(Beneficiary, PregnancyRecord.beneficiary_id == Beneficiary.beneficiary_id)

    if current_user.role == UserRole.ASHA and current_user.village:
        query = query.filter(Beneficiary.village == current_user.village)

    if resolved is not None:
        query = query.filter(Referral.is_resolved == resolved)

    referrals = query.order_by(Referral.referral_initiated_at.desc()).all()
    results = []
    for r in referrals:
        r_dict = r.to_dict()
        prg = db.query(PregnancyRecord).filter(PregnancyRecord.pregnancy_id == r.pregnancy_id).first()
        ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == prg.beneficiary_id).first() if prg else None
        fac = db.query(HealthFacility).filter(HealthFacility.id == r.destination_facility_id).first()
        user = db.query(User).filter(User.id == r.referring_user_id).first()

        r_dict["beneficiary_name"] = ben.full_name if ben else "Unknown"
        r_dict["village"] = ben.village if ben else "Unknown"
        r_dict["facility_name"] = fac.facility_name if fac else "Unknown Facility"
        r_dict["facility_phone"] = fac.emergency_phone_1 if fac else "108"
        r_dict["referrer_name"] = user.full_name if user else "Staff"
        results.append(r_dict)

    return results

@router.put("/{referral_uuid}/outcome")
def update_referral_outcome(
    referral_uuid: str,
    outcome: ReferralOutcomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ANM, UserRole.MEDICAL_OFFICER, UserRole.SUPERVISOR]))
):
    ref = db.query(Referral).filter(Referral.referral_uuid == referral_uuid).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Referral record not found")

    ref.outcome_status = outcome.outcome_status
    ref.outcome_notes = outcome.outcome_notes
    ref.is_resolved = outcome.is_resolved
    if outcome.facility_acknowledged is not None:
        ref.facility_acknowledged = outcome.facility_acknowledged
        ref.acknowledgement_time = datetime.datetime.utcnow()

    db.commit()
    db.refresh(ref)

    log_audit(
        db,
        action="UPDATE_REFERRAL_OUTCOME",
        user=current_user,
        target_entity="referral",
        target_id=ref.referral_uuid,
        details=f"Outcome updated: {ref.outcome_status}, Resolved: {ref.is_resolved}"
    )

    return {
        "message": "Referral outcome documented successfully",
        "referral": ref.to_dict()
    }


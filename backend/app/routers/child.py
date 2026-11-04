import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary
from ..models.child import ChildRecord, ChildImmunization, ChildGrowth
from ..schemas.child import ChildCreate, ImmunizationLog, GrowthLog, ChildProfileOut
from ..services.auth_service import get_current_user, log_audit

router = APIRouter(prefix="/api/children", tags=["Child Health & Immunization Tracking"])

# Standard National Immunization Schedule (NIS - India MoHFW)
STANDARD_VACCINES = [
    # At Birth
    {"code": "BCG", "name": "BCG (Bacillus Calmette–Guérin)", "age_label": "At Birth", "days_offset": 0},
    {"code": "OPV_0", "name": "OPV 0 (Oral Polio Vaccine birth dose)", "age_label": "At Birth", "days_offset": 0},
    {"code": "HEP_B_0", "name": "Hepatitis B (Birth dose within 24h)", "age_label": "At Birth", "days_offset": 0},
    # 6 Weeks (42 days)
    {"code": "OPV_1", "name": "OPV 1 (Oral Polio Vaccine dose 1)", "age_label": "6 Weeks", "days_offset": 42},
    {"code": "PENTA_1", "name": "Pentavalent 1 (DPT + Hep B + Hib)", "age_label": "6 Weeks", "days_offset": 42},
    {"code": "ROTA_1", "name": "Rotavirus 1", "age_label": "6 Weeks", "days_offset": 42},
    {"code": "IPV_1", "name": "Fractional IPV 1", "age_label": "6 Weeks", "days_offset": 42},
    {"code": "PCV_1", "name": "PCV 1 (Pneumococcal Conjugate)", "age_label": "6 Weeks", "days_offset": 42},
    # 10 Weeks (70 days)
    {"code": "OPV_2", "name": "OPV 2 (Oral Polio Vaccine dose 2)", "age_label": "10 Weeks", "days_offset": 70},
    {"code": "PENTA_2", "name": "Pentavalent 2 (DPT + Hep B + Hib)", "age_label": "10 Weeks", "days_offset": 70},
    {"code": "ROTA_2", "name": "Rotavirus 2", "age_label": "10 Weeks", "days_offset": 70},
    # 14 Weeks (98 days)
    {"code": "OPV_3", "name": "OPV 3 (Oral Polio Vaccine dose 3)", "age_label": "14 Weeks", "days_offset": 98},
    {"code": "PENTA_3", "name": "Pentavalent 3 (DPT + Hep B + Hib)", "age_label": "14 Weeks", "days_offset": 98},
    {"code": "ROTA_3", "name": "Rotavirus 3", "age_label": "14 Weeks", "days_offset": 98},
    {"code": "IPV_2", "name": "Fractional IPV 2", "age_label": "14 Weeks", "days_offset": 98},
    {"code": "PCV_2", "name": "PCV 2 (Pneumococcal Conjugate)", "age_label": "14 Weeks", "days_offset": 98},
    # 9-12 Months (270 days)
    {"code": "MR_1", "name": "MR 1 (Measles-Rubella dose 1)", "age_label": "9-12 Months", "days_offset": 270},
    {"code": "JE_1", "name": "JE 1 (Japanese Encephalitis)", "age_label": "9-12 Months", "days_offset": 270},
    {"code": "PCV_BOOSTER", "name": "PCV Booster", "age_label": "9 Months", "days_offset": 270},
    {"code": "VIT_A_1", "name": "Vitamin A (1st Dose 1 lakh IU)", "age_label": "9 Months", "days_offset": 270},
    # 16-24 Months (480 days)
    {"code": "MR_2", "name": "MR 2 (Measles-Rubella dose 2)", "age_label": "16-24 Months", "days_offset": 480},
    {"code": "DPT_BOOSTER_1", "name": "DPT 1st Booster", "age_label": "16-24 Months", "days_offset": 480},
    {"code": "OPV_BOOSTER", "name": "OPV Booster", "age_label": "16-24 Months", "days_offset": 480},
    {"code": "VIT_A_2", "name": "Vitamin A (2nd Dose 2 lakh IU)", "age_label": "16 Months", "days_offset": 480},
]

@router.get("")
def list_children(
    village: Optional[str] = None,
    mother_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(ChildRecord)
    if mother_id:
        q = q.filter(ChildRecord.mother_beneficiary_id == mother_id)
    if village:
        q = q.filter(ChildRecord.village == village)
    elif current_user.role == UserRole.ASHA and current_user.village:
        q = q.filter(ChildRecord.village == current_user.village)
    
    children = q.order_by(ChildRecord.dob.desc()).all()
    results = []
    for c in children:
        cd = c.to_dict()
        # count pending immunizations
        pending_imms = db.query(ChildImmunization).filter(
            ChildImmunization.child_id == c.child_id,
            ChildImmunization.status.in_(["DUE", "OVERDUE"])
        ).count()
        completed_imms = db.query(ChildImmunization).filter(
            ChildImmunization.child_id == c.child_id,
            ChildImmunization.status == "COMPLETED"
        ).count()
        cd["pending_immunizations_count"] = pending_imms
        cd["completed_immunizations_count"] = completed_imms
        
        # latest growth
        latest_growth = db.query(ChildGrowth).filter(
            ChildGrowth.child_id == c.child_id
        ).order_by(ChildGrowth.measurement_date.desc()).first()
        cd["latest_growth"] = latest_growth.to_dict() if latest_growth else None
        results.append(cd)
        
    return results

@router.get("/{child_id}", response_model=ChildProfileOut)
def get_child_profile(
    child_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    child = db.query(ChildRecord).filter(ChildRecord.child_id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child record not found")
    
    mother = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == child.mother_beneficiary_id).first()
    
    # Update due/overdue status based on today's date
    today = datetime.date.today()
    imms = db.query(ChildImmunization).filter(ChildImmunization.child_id == child_id).order_by(ChildImmunization.scheduled_date.asc()).all()
    for imm in imms:
        if imm.status != "COMPLETED":
            if imm.scheduled_date < today:
                imm.status = "OVERDUE"
            elif imm.scheduled_date <= today + datetime.timedelta(days=7):
                imm.status = "DUE"
    db.commit()
    
    growth = db.query(ChildGrowth).filter(ChildGrowth.child_id == child_id).order_by(ChildGrowth.measurement_date.desc()).all()
    
    return ChildProfileOut(
        child=child.to_dict(),
        mother=mother.to_dict() if mother else None,
        immunizations=[i.to_dict() for i in imms],
        growth_history=[g.to_dict() for g in growth]
    )

@router.post("")
def register_child(
    child_in: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mother = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == child_in.mother_beneficiary_id).first()
    if not mother:
        raise HTTPException(status_code=404, detail="Mother beneficiary not found")
    
    # Generate unique Child ID
    count = db.query(ChildRecord).count() + 1
    child_id = f"CHD-{datetime.date.today().year}-{count:04d}"
    
    child = ChildRecord(
        child_id=child_id,
        mother_beneficiary_id=child_in.mother_beneficiary_id,
        child_name=child_in.child_name,
        gender=child_in.gender,
        dob=child_in.dob,
        birth_weight_kg=child_in.birth_weight_kg,
        delivery_place=child_in.delivery_place or "PHC",
        delivery_type=child_in.delivery_type or "NORMAL",
        blood_group=child_in.blood_group,
        assigned_asha_id=current_user.id if current_user.role == UserRole.ASHA else mother.assigned_asha_id,
        village=child_in.village or mother.village,
        status="HEALTHY"
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    
    # Auto-generate National Immunization Schedule records
    today = datetime.date.today()
    for v in STANDARD_VACCINES:
        sched_date = child_in.dob + datetime.timedelta(days=v["days_offset"])
        status_val = "DUE"
        if sched_date < today:
            status_val = "OVERDUE"
        
        imm = ChildImmunization(
            record_uuid=f"IMM-{child_id}-{v['code']}",
            child_id=child_id,
            vaccine_code=v["code"],
            vaccine_name=v["name"],
            target_age_label=v["age_label"],
            scheduled_date=sched_date,
            status=status_val
        )
        db.add(imm)
    
    # Record initial birth weight growth record if provided
    if child_in.birth_weight_kg:
        growth_stat = "NORMAL_GREEN"
        if child_in.birth_weight_kg < 2.0:
            growth_stat = "SAM_SEVERE_RED" # Low birth weight (<2.0kg)
        elif child_in.birth_weight_kg < 2.5:
            growth_stat = "MAM_MODERATE_YELLOW" # Borderline low birth weight (<2.5kg)
            
        growth = ChildGrowth(
            growth_uuid=f"GRW-{child_id}-BIRTH",
            child_id=child_id,
            measurement_date=child_in.dob,
            age_months=0,
            weight_kg=child_in.birth_weight_kg,
            growth_status=growth_stat,
            action_taken="Birth weight logged at delivery",
            recorded_by_user_id=current_user.id
        )
        db.add(growth)
        
    db.commit()
    log_audit(db, action="CHILD_REGISTERED", user=current_user, target_entity="child", target_id=child_id, details=f"Registered child {child.child_name} for mother {mother.full_name}")
    
    return {"status": "SUCCESS", "message": "Child registered and immunization schedule initialized", "child": child.to_dict()}

@router.post("/immunize")
def record_immunization(
    log_in: ImmunizationLog,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    imm = db.query(ChildImmunization).filter(
        ChildImmunization.child_id == log_in.child_id,
        ChildImmunization.vaccine_code == log_in.vaccine_code
    ).first()
    
    if not imm:
        # Create ad-hoc
        imm = ChildImmunization(
            record_uuid=f"IMM-{log_in.child_id}-{log_in.vaccine_code}-{int(datetime.datetime.utcnow().timestamp())}",
            child_id=log_in.child_id,
            vaccine_code=log_in.vaccine_code,
            vaccine_name=log_in.vaccine_code,
            target_age_label="Routine",
            scheduled_date=log_in.administered_date
        )
        db.add(imm)
    
    imm.administered_date = log_in.administered_date
    imm.batch_no = log_in.batch_no
    imm.status = "COMPLETED"
    imm.administered_by_user_id = current_user.id
    imm.adverse_reaction = log_in.adverse_reaction
    imm.notes = log_in.notes
    
    db.commit()
    db.refresh(imm)
    log_audit(db, action="VACCINATION_ADMINISTERED", user=current_user, target_entity="child_immunization", target_id=imm.record_uuid, details=f"Vaccinated {imm.vaccine_name}")
    
    return {"status": "SUCCESS", "message": f"{imm.vaccine_name} administered successfully", "immunization": imm.to_dict()}

@router.post("/growth")
def record_growth(
    grow_in: GrowthLog,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Determine WHO Growth Standard Malnutrition Status
    # Standard child growth benchmarks (simplified clinical rule for rural ASHA triage)
    # Expected weight approx: 3kg at birth, 6kg at 4mo, 8kg at 9mo, 10kg at 1yr, 12kg at 2yr
    age = grow_in.age_months
    wt = grow_in.weight_kg
    muac = grow_in.muac_cm
    
    status_val = "NORMAL_GREEN"
    action = grow_in.action_taken or "Routine nutritional counselling given"
    
    # MUAC criteria for 6-59 months
    if muac is not None and age >= 6:
        if muac < 11.5:
            status_val = "SAM_SEVERE_RED" # Severe Acute Malnutrition
            action = "URGENT: Refer to Nutrition Rehabilitation Centre (NRC) & start therapeutic food"
        elif muac < 12.5:
            status_val = "MAM_MODERATE_YELLOW" # Moderate Acute Malnutrition
            action = "Targeted supplementary feeding & weekly home weight monitoring"
    else:
        # Age-weight thresholds
        if age <= 6 and wt < (2.5 + (age * 0.4)):
            status_val = "MAM_MODERATE_YELLOW"
        elif age > 6 and wt < (4.5 + (age * 0.25)):
            status_val = "SAM_SEVERE_RED"
            action = "Underweight: Refer to PHC Medical Officer for growth faltering assessment"
        elif age > 6 and wt < (5.5 + (age * 0.3)):
            status_val = "MAM_MODERATE_YELLOW"
            
    growth_uuid = f"GRW-{grow_in.child_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    growth = ChildGrowth(
        growth_uuid=growth_uuid,
        child_id=grow_in.child_id,
        measurement_date=grow_in.measurement_date or datetime.date.today(),
        age_months=grow_in.age_months,
        weight_kg=grow_in.weight_kg,
        height_cm=grow_in.height_cm,
        muac_cm=grow_in.muac_cm,
        growth_status=status_val,
        action_taken=action,
        recorded_by_user_id=current_user.id
    )
    db.add(growth)
    
    # Update child status
    child = db.query(ChildRecord).filter(ChildRecord.child_id == grow_in.child_id).first()
    if child:
        if status_val == "SAM_SEVERE_RED":
            child.status = "HIGH_RISK"
        elif status_val == "MAM_MODERATE_YELLOW" and child.status != "HIGH_RISK":
            child.status = "UNDERWEIGHT"
            
    db.commit()
    db.refresh(growth)
    
    log_audit(db, action="GROWTH_RECORDED", user=current_user, target_entity="child_growth", target_id=growth_uuid, details=f"Growth entry for child {grow_in.child_id}: {wt}kg, status={status_val}")
    
    return {"status": "SUCCESS", "message": "Growth metrics recorded", "growth": growth.to_dict()}


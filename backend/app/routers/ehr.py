import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary
from ..models.ehr import MedicalHistory, Diagnosis, Medicine, LabReport
from ..schemas.ehr import MedicalHistoryCreate, DiagnosisCreate, MedicineCreate, LabReportCreate, EHRSummaryOut
from ..services.auth_service import get_current_user, log_audit

router = APIRouter(prefix="/api/ehr", tags=["Electronic Health Records (EHR)"])

@router.get("/{beneficiary_id}", response_model=EHRSummaryOut)
def get_beneficiary_ehr(
    beneficiary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail=f"Beneficiary {beneficiary_id} not found")
    
    # 1. Medical History
    history = db.query(MedicalHistory).filter(MedicalHistory.beneficiary_id == beneficiary_id).first()
    
    # 2. Diagnoses
    diagnoses = db.query(Diagnosis).filter(Diagnosis.beneficiary_id == beneficiary_id).order_by(Diagnosis.diagnosis_date.desc()).all()
    
    # 3. Medicines
    medicines = db.query(Medicine).filter(Medicine.beneficiary_id == beneficiary_id).order_by(Medicine.prescribed_date.desc()).all()
    
    # 4. Lab Reports
    lab_reports = db.query(LabReport).filter(LabReport.beneficiary_id == beneficiary_id).order_by(LabReport.sample_date.desc()).all()
    
    return EHRSummaryOut(
        beneficiary_id=beneficiary_id,
        history=history.to_dict() if history else None,
        diagnoses=[d.to_dict() for d in diagnoses],
        medicines=[m.to_dict() for m in medicines],
        lab_reports=[l.to_dict() for l in lab_reports]
    )

@router.post("/history")
def update_medical_history(
    hist_in: MedicalHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == hist_in.beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    hist = db.query(MedicalHistory).filter(MedicalHistory.beneficiary_id == hist_in.beneficiary_id).first()
    if not hist:
        hist = MedicalHistory(beneficiary_id=hist_in.beneficiary_id)
        db.add(hist)
    
    if hist_in.blood_group is not None:
        hist.blood_group = hist_in.blood_group
    if hist_in.rh_factor is not None:
        hist.rh_factor = hist_in.rh_factor
    if hist_in.allergies is not None:
        hist.allergies = hist_in.allergies
    if hist_in.chronic_conditions is not None:
        hist.chronic_conditions = hist_in.chronic_conditions
    if hist_in.past_surgeries is not None:
        hist.past_surgeries = hist_in.past_surgeries
    if hist_in.past_obstetric_complications is not None:
        hist.past_obstetric_complications = hist_in.past_obstetric_complications
    if hist_in.family_medical_history is not None:
        hist.family_medical_history = hist_in.family_medical_history
    if hist_in.general_notes is not None:
        hist.general_notes = hist_in.general_notes
    
    hist.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(hist)
    
    log_audit(db, action="EHR_HISTORY_UPDATE", user=current_user, target_entity="beneficiary", target_id=ben.beneficiary_id, details="Updated medical/obstetric history")
    return {"status": "SUCCESS", "message": "Medical history updated", "history": hist.to_dict()}

@router.post("/diagnosis")
def add_diagnosis(
    diag_in: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == diag_in.beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    diag_uuid = f"DX-{datetime.datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    diag = Diagnosis(
        diagnosis_uuid=diag_uuid,
        beneficiary_id=diag_in.beneficiary_id,
        diagnosis_code=diag_in.diagnosis_code or "CLIN-OBS",
        diagnosis_name=diag_in.diagnosis_name,
        severity=diag_in.severity or "MODERATE",
        status=diag_in.status or "ACTIVE",
        diagnosed_by_user_id=current_user.id,
        diagnosed_by_name=current_user.full_name,
        diagnosis_date=diag_in.diagnosis_date or datetime.date.today(),
        clinical_notes=diag_in.clinical_notes
    )
    db.add(diag)
    db.commit()
    db.refresh(diag)
    
    log_audit(db, action="EHR_DIAGNOSIS_ADDED", user=current_user, target_entity="diagnosis", target_id=diag_uuid, details=f"Diagnosis: {diag.diagnosis_name}")
    return {"status": "SUCCESS", "message": "Diagnosis recorded in EHR", "diagnosis": diag.to_dict()}

@router.post("/medicine")
def add_medicine(
    med_in: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == med_in.beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    med_uuid = f"RX-{datetime.datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    med = Medicine(
        medicine_uuid=med_uuid,
        beneficiary_id=med_in.beneficiary_id,
        medicine_name=med_in.medicine_name,
        dosage=med_in.dosage,
        frequency=med_in.frequency,
        duration_days=med_in.duration_days or 30,
        prescribed_by_user_id=current_user.id,
        prescribed_date=datetime.date.today(),
        dispensed_status=med_in.dispensed_status or "DISPENSED",
        stock_source=med_in.stock_source or "ASHA_KIT",
        instructions=med_in.instructions
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    
    log_audit(db, action="EHR_MEDICINE_DISPENSED", user=current_user, target_entity="medicine", target_id=med_uuid, details=f"Dispensed {med.medicine_name} ({med.dosage})")
    return {"status": "SUCCESS", "message": "Medicine dispensed and logged", "medicine": med.to_dict()}

@router.post("/lab-report")
def add_lab_report(
    lab_in: LabReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == lab_in.beneficiary_id).first()
    if not ben:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    
    lab_uuid = f"LAB-{datetime.datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    report = LabReport(
        report_uuid=lab_uuid,
        beneficiary_id=lab_in.beneficiary_id,
        test_name=lab_in.test_name,
        test_category=lab_in.test_category or "ROUTINE_ANC",
        sample_date=lab_in.sample_date or datetime.date.today(),
        result_value=lab_in.result_value,
        unit=lab_in.unit,
        reference_range=lab_in.reference_range,
        status=lab_in.status or "NORMAL",
        conducted_at_facility=lab_in.conducted_at_facility or current_user.sub_centre or "Vadipatti PHC Lab",
        technician_notes=lab_in.technician_notes
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    log_audit(db, action="EHR_LAB_REPORT_ADDED", user=current_user, target_entity="lab_report", target_id=lab_uuid, details=f"Lab test: {report.test_name} = {report.result_value}")
    return {"status": "SUCCESS", "message": "Lab report recorded in EHR", "lab_report": report.to_dict()}


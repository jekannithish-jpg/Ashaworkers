from typing import Optional, List
import datetime
from pydantic import BaseModel

class MedicalHistoryCreate(BaseModel):
    beneficiary_id: str
    blood_group: Optional[str] = None
    rh_factor: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    past_surgeries: Optional[str] = None
    past_obstetric_complications: Optional[str] = None
    family_medical_history: Optional[str] = None
    general_notes: Optional[str] = None

class DiagnosisCreate(BaseModel):
    beneficiary_id: str
    diagnosis_name: str
    diagnosis_code: Optional[str] = None
    severity: Optional[str] = "MODERATE"
    status: Optional[str] = "ACTIVE"
    diagnosis_date: Optional[datetime.date] = None
    clinical_notes: Optional[str] = None

class MedicineCreate(BaseModel):
    beneficiary_id: str
    medicine_name: str
    dosage: str
    frequency: str = "OD"
    duration_days: Optional[int] = 30
    dispensed_status: Optional[str] = "DISPENSED"
    stock_source: Optional[str] = "ASHA_KIT"
    instructions: Optional[str] = None

class LabReportCreate(BaseModel):
    beneficiary_id: str
    test_name: str
    test_category: Optional[str] = "ROUTINE_ANC"
    sample_date: Optional[datetime.date] = None
    result_value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = "NORMAL"
    conducted_at_facility: Optional[str] = None
    technician_notes: Optional[str] = None

class EHRSummaryOut(BaseModel):
    beneficiary_id: str
    history: Optional[dict] = None
    diagnoses: List[dict] = []
    medicines: List[dict] = []
    lab_reports: List[dict] = []


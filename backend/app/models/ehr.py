import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from ..database import Base

class MedicalHistory(Base):
    __tablename__ = "medical_histories"

    id = Column(Integer, primary_key=True, index=True)
    beneficiary_id = Column(String(64), ForeignKey("beneficiaries.beneficiary_id"), unique=True, nullable=False, index=True)
    blood_group = Column(String(10), nullable=True) # e.g. B+, O+, AB-
    rh_factor = Column(String(10), nullable=True)  # POSITIVE, NEGATIVE
    allergies = Column(Text, nullable=True)         # Known drug or food allergies
    chronic_conditions = Column(Text, nullable=True) # HTN, Diabetes, Asthma, Epilepsy, Thyroid
    past_surgeries = Column(Text, nullable=True)
    past_obstetric_complications = Column(Text, nullable=True) # Prior abortion, stillbirth, C-section
    family_medical_history = Column(Text, nullable=True) # Twins, genetic conditions
    general_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "beneficiary_id": self.beneficiary_id,
            "blood_group": self.blood_group,
            "rh_factor": self.rh_factor,
            "allergies": self.allergies,
            "chronic_conditions": self.chronic_conditions,
            "past_surgeries": self.past_surgeries,
            "past_obstetric_complications": self.past_obstetric_complications,
            "family_medical_history": self.family_medical_history,
            "general_notes": self.general_notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    diagnosis_uuid = Column(String(64), unique=True, index=True, nullable=False)
    beneficiary_id = Column(String(64), ForeignKey("beneficiaries.beneficiary_id"), nullable=False, index=True)
    diagnosis_code = Column(String(64), nullable=True) # e.g. ICD-10 or clinical rule code
    diagnosis_name = Column(String(200), nullable=False)
    severity = Column(String(32), default="MODERATE") # MILD, MODERATE, SEVERE, CRITICAL
    status = Column(String(32), default="ACTIVE")     # ACTIVE, RESOLVED, CHRONIC
    diagnosed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    diagnosed_by_name = Column(String(128), nullable=True)
    diagnosis_date = Column(Date, nullable=False, default=datetime.date.today)
    clinical_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "diagnosis_uuid": self.diagnosis_uuid,
            "beneficiary_id": self.beneficiary_id,
            "diagnosis_code": self.diagnosis_code,
            "diagnosis_name": self.diagnosis_name,
            "severity": self.severity,
            "status": self.status,
            "diagnosed_by_user_id": self.diagnosed_by_user_id,
            "diagnosed_by_name": self.diagnosed_by_name,
            "diagnosis_date": self.diagnosis_date.isoformat() if self.diagnosis_date else None,
            "clinical_notes": self.clinical_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    medicine_uuid = Column(String(64), unique=True, index=True, nullable=False)
    beneficiary_id = Column(String(64), ForeignKey("beneficiaries.beneficiary_id"), nullable=False, index=True)
    medicine_name = Column(String(150), nullable=False) # IFA, Calcium, Albendazole, Amoxicillin, Paracetamol
    dosage = Column(String(64), nullable=False)         # e.g. "100mg elemental Iron + 500mcg Folic Acid"
    frequency = Column(String(32), nullable=False)      # Once Daily (OD), Twice Daily (BD), Three Times (TDS)
    duration_days = Column(Integer, default=30)
    prescribed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    prescribed_date = Column(Date, default=datetime.date.today)
    dispensed_status = Column(String(32), default="DISPENSED") # DISPENSED, PENDING, TAKEN_REGULARLY, ADVERSE_EFFECT
    stock_source = Column(String(64), default="ASHA_KIT")     # ASHA_KIT, SUB_CENTRE, PHC_DISPENSARY
    instructions = Column(Text, nullable=True)                 # e.g. Take after meals with lime water; avoid tea
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_uuid": self.medicine_uuid,
            "beneficiary_id": self.beneficiary_id,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "duration_days": self.duration_days,
            "prescribed_by_user_id": self.prescribed_by_user_id,
            "prescribed_date": self.prescribed_date.isoformat() if self.prescribed_date else None,
            "dispensed_status": self.dispensed_status,
            "stock_source": self.stock_source,
            "instructions": self.instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uuid = Column(String(64), unique=True, index=True, nullable=False)
    beneficiary_id = Column(String(64), ForeignKey("beneficiaries.beneficiary_id"), nullable=False, index=True)
    test_name = Column(String(128), nullable=False)     # Hemoglobin (Hb), Fasting Blood Sugar, Urine Albumin, HIV, Syphilis, USG
    test_category = Column(String(64), default="ROUTINE_ANC") # ROUTINE_ANC, BLOOD, URINE, SEROLOGY, RADIOLOGY
    sample_date = Column(Date, default=datetime.date.today)
    result_value = Column(String(64), nullable=False)   # "9.2 g/dL", "Negative", "Trace", "120 mg/dL", "Normal Single IUP"
    unit = Column(String(32), nullable=True)            # g/dL, mg/dL, +, -
    reference_range = Column(String(64), nullable=True) # "11.0 - 15.0 g/dL"
    status = Column(String(32), default="NORMAL")       # NORMAL, ABNORMAL, CRITICAL
    conducted_at_facility = Column(String(128), nullable=True) # Alanganallur SC, Vadipatti PHC Lab
    technician_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "report_uuid": self.report_uuid,
            "beneficiary_id": self.beneficiary_id,
            "test_name": self.test_name,
            "test_category": self.test_category,
            "sample_date": self.sample_date.isoformat() if self.sample_date else None,
            "result_value": self.result_value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "status": self.status,
            "conducted_at_facility": self.conducted_at_facility,
            "technician_notes": self.technician_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


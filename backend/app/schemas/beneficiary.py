from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field

class BeneficiaryCreate(BaseModel):
    beneficiary_id: Optional[str] = None # Will auto-generate BEN-YYYY-XXXX if not provided
    full_name: str = Field(..., min_length=2, max_length=128)
    age: int = Field(..., ge=12, le=60)
    dob: Optional[date] = None
    contact_phone: Optional[str] = None
    village: str = Field(..., min_length=2)
    sub_centre: str = Field(..., min_length=2)
    primary_health_centre: Optional[str] = "Vadipatti PHC"
    preferred_language: Optional[str] = "ta"
    consent_obtained: bool = True
    privacy_notice_acknowledged: bool = True
    is_draft: bool = False
    
    # Pregnancy registration details (optional at initial intake if draft)
    gravida: Optional[int] = 1
    parity: Optional[int] = 0
    lmp_date: Optional[date] = None
    confirmation_date: Optional[date] = None
    registration_date: Optional[date] = None
    past_obstetric_history: Optional[str] = None
    known_medical_conditions: Optional[str] = None
    assigned_facility_id: Optional[int] = None

class BeneficiaryUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    dob: Optional[date] = None
    contact_phone: Optional[str] = None
    village: Optional[str] = None
    sub_centre: Optional[str] = None
    primary_health_centre: Optional[str] = None
    preferred_language: Optional[str] = None
    is_active: Optional[bool] = None

class PregnancyRecordCreate(BaseModel):
    beneficiary_id: str
    gravida: int = 1
    parity: int = 0
    lmp_date: Optional[date] = None
    edd_date: Optional[date] = None
    is_edd_estimated: bool = True
    confirmation_date: Optional[date] = None
    registration_date: date = Field(default_factory=date.today)
    past_obstetric_history: Optional[str] = None
    known_medical_conditions: Optional[str] = None
    assigned_facility_id: Optional[int] = None

class DuplicateCheckRequest(BaseModel):
    full_name: str
    village: str
    contact_phone: Optional[str] = None
    age: Optional[int] = None

class DuplicateCheckResponse(BaseModel):
    is_possible_duplicate: bool
    matches: List[dict]


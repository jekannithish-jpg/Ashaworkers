from typing import Optional, List
import datetime
from pydantic import BaseModel

class ChildCreate(BaseModel):
    mother_beneficiary_id: str
    child_name: str
    gender: str # MALE, FEMALE, OTHER
    dob: datetime.date
    birth_weight_kg: Optional[float] = None
    delivery_place: Optional[str] = "PHC"
    delivery_type: Optional[str] = "NORMAL"
    blood_group: Optional[str] = None
    village: Optional[str] = None

class ImmunizationLog(BaseModel):
    child_id: str
    vaccine_code: str
    administered_date: datetime.date
    batch_no: Optional[str] = None
    adverse_reaction: Optional[str] = None
    notes: Optional[str] = None

class GrowthLog(BaseModel):
    child_id: str
    measurement_date: Optional[datetime.date] = None
    age_months: int
    weight_kg: float
    height_cm: Optional[float] = None
    muac_cm: Optional[float] = None
    action_taken: Optional[str] = None

class ChildProfileOut(BaseModel):
    child: dict
    mother: Optional[dict] = None
    immunizations: List[dict] = []
    growth_history: List[dict] = []


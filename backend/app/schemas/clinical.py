from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field

class ANCVisitCreate(BaseModel):
    visit_uuid: Optional[str] = None
    pregnancy_id: str
    beneficiary_id: str
    anc_period: str # ANC-1, ANC-2, ANC-3, ANC-4, ANC-SPECIAL
    scheduled_date: date
    actual_visit_date: Optional[date] = None
    status: Optional[str] = "NOT_YET_DUE"
    gestational_age_weeks: Optional[int] = None
    weight_kg: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    hemoglobin_g_dl: Optional[float] = None
    urine_albumin: Optional[str] = "NOT_DONE"
    urine_sugar: Optional[str] = "NOT_DONE"
    ultrasound_status: Optional[str] = None
    ifa_tablets_issued: Optional[int] = 0
    calcium_tablets_issued: Optional[int] = 0
    tt_td_dose: Optional[str] = "NONE"
    counselling_topics: Optional[str] = None
    deferral_reason: Optional[str] = None
    clinical_notes: Optional[str] = None

class ANCVisitUpdate(BaseModel):
    actual_visit_date: Optional[date] = None
    status: Optional[str] = None
    gestational_age_weeks: Optional[int] = None
    weight_kg: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    hemoglobin_g_dl: Optional[float] = None
    urine_albumin: Optional[str] = None
    urine_sugar: Optional[str] = None
    ultrasound_status: Optional[str] = None
    ifa_tablets_issued: Optional[int] = None
    calcium_tablets_issued: Optional[int] = None
    tt_td_dose: Optional[str] = None
    counselling_topics: Optional[str] = None
    deferral_reason: Optional[str] = None
    clinical_notes: Optional[str] = None

class RiskFactorCreate(BaseModel):
    risk_uuid: Optional[str] = None
    pregnancy_id: str
    rule_code: Optional[str] = None
    risk_title: str
    risk_detail: Optional[str] = None
    severity: str = "HIGH" # MODERATE, HIGH, EMERGENCY
    status: str = "REPORTED"
    requires_professional_review: bool = True
    follow_up_due_date: Optional[date] = None
    clinical_plan: Optional[str] = None

class RiskFactorReview(BaseModel):
    status: str # CONFIRMED_HIGH_RISK, FOLLOW_UP_COMPLETED, RESOLVED
    clinical_plan: str
    follow_up_due_date: Optional[date] = None

class ReferralCreate(BaseModel):
    referral_uuid: Optional[str] = None
    pregnancy_id: str
    beneficiary_id: str
    danger_sign_code: Optional[str] = None
    reason: str
    urgency: str = "CRITICAL_108" # CRITICAL_108, HIGH_PRIORITY_102, ROUTINE
    destination_facility_id: int
    transport_mode: Optional[str] = "EMERGENCY_AMBULANCE_108"

class ReferralOutcomeUpdate(BaseModel):
    facility_acknowledged: Optional[bool] = None
    outcome_status: str # PENDING, ADMITTED, TREATED_DISCHARGED, ESCALATED_TERTIARY, LOST_TO_FOLLOWUP
    outcome_notes: str
    is_resolved: bool = True

class PNCVisitCreate(BaseModel):
    pnc_uuid: Optional[str] = None
    pregnancy_id: str
    beneficiary_id: str
    pnc_interval: str # DAY_1, DAY_3, DAY_7, DAY_14, DAY_21, DAY_28, DAY_42
    delivery_date: Optional[date] = None
    delivery_facility: Optional[str] = None
    scheduled_date: date
    actual_visit_date: Optional[date] = None
    status: Optional[str] = "NOT_YET_DUE"
    maternal_assessment_status: Optional[str] = None
    newborn_follow_up_status: Optional[str] = None
    feeding_counselling_provided: bool = True
    danger_signs_reported: Optional[str] = None
    referral_initiated: bool = False

class HomeVisitCreate(BaseModel):
    visit_uuid: Optional[str] = None
    pregnancy_id: Optional[str] = None
    beneficiary_id: str
    visit_date: date
    visit_purpose: str
    is_completed: bool = False
    observations: Optional[str] = None
    counselling_topics: Optional[str] = None
    follow_up_tasks: Optional[str] = None
    referral_initiated: bool = False
    next_visit_date: Optional[date] = None
    notes: Optional[str] = None
    is_draft: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy: Optional[float] = None
    survey_type: Optional[str] = "ROUTINE_HOME_VISIT"
    survey_data: Optional[str] = None


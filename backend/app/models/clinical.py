import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from ..database import Base

class HealthFacility(Base):
    __tablename__ = "health_facilities"

    id = Column(Integer, primary_key=True, index=True)
    facility_code = Column(String(64), unique=True, nullable=False)
    facility_name = Column(String(128), nullable=False)
    facility_type = Column(String(64), nullable=False) # SUB_CENTRE, PHC, CHC, FRU, SDH, DHH
    district = Column(String(100), nullable=False)
    block = Column(String(100), nullable=False)
    emergency_phone_1 = Column(String(20), nullable=False)
    emergency_phone_2 = Column(String(20), nullable=True)
    is_frusc = Column(Boolean, default=False)
    has_c_section = Column(Boolean, default=False)
    has_blood_bank = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "facility_code": self.facility_code,
            "facility_name": self.facility_name,
            "facility_type": self.facility_type,
            "district": self.district,
            "block": self.block,
            "emergency_phone_1": self.emergency_phone_1,
            "emergency_phone_2": self.emergency_phone_2,
            "is_frusc": self.is_frusc,
            "has_c_section": self.has_c_section,
            "has_blood_bank": self.has_blood_bank,
        }

class ANCVisit(Base):
    __tablename__ = "anc_visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_uuid = Column(String(64), unique=True, index=True, nullable=False)
    pregnancy_id = Column(String(64), ForeignKey("pregnancy_records.pregnancy_id"), nullable=False, index=True)
    beneficiary_id = Column(String(64), nullable=False, index=True)
    anc_period = Column(String(20), nullable=False) # ANC-1, ANC-2, ANC-3, ANC-4, ANC-SPECIAL
    scheduled_date = Column(Date, nullable=False)
    actual_visit_date = Column(Date, nullable=True)
    status = Column(String(32), nullable=False, default="NOT_YET_DUE")
    # Statuses: NOT_YET_DUE, DUE_SOON, DUE, COMPLETED, OVERDUE, DEFERRED, UNKNOWN
    gestational_age_weeks = Column(Integer, nullable=True)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    weight_kg = Column(Float, nullable=True)
    bp_systolic = Column(Integer, nullable=True)
    bp_diastolic = Column(Integer, nullable=True)
    hemoglobin_g_dl = Column(Float, nullable=True)
    urine_albumin = Column(String(32), default="NOT_DONE") # NIL, TRACE, PRESENT, NOT_DONE
    urine_sugar = Column(String(32), default="NOT_DONE")   # NIL, PRESENT, NOT_DONE
    ultrasound_status = Column(String(64), nullable=True)
    ifa_tablets_issued = Column(Integer, default=0)
    calcium_tablets_issued = Column(Integer, default=0)
    tt_td_dose = Column(String(32), default="NONE") # NONE, TD_1, TD_2, TD_BOOSTER
    counselling_topics = Column(Text, nullable=True)
    deferral_reason = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    sync_status = Column(String(32), default="SYNCHRONIZED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    version_id = Column(Integer, default=1)

    pregnancy = relationship("PregnancyRecord", back_populates="anc_visits")

    def to_dict(self):
        return {
            "id": self.id,
            "visit_uuid": self.visit_uuid,
            "pregnancy_id": self.pregnancy_id,
            "beneficiary_id": self.beneficiary_id,
            "anc_period": self.anc_period,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "actual_visit_date": self.actual_visit_date.isoformat() if self.actual_visit_date else None,
            "status": self.status,
            "gestational_age_weeks": self.gestational_age_weeks,
            "recorded_by_user_id": self.recorded_by_user_id,
            "weight_kg": self.weight_kg,
            "bp_systolic": self.bp_systolic,
            "bp_diastolic": self.bp_diastolic,
            "hemoglobin_g_dl": self.hemoglobin_g_dl,
            "urine_albumin": self.urine_albumin,
            "urine_sugar": self.urine_sugar,
            "ultrasound_status": self.ultrasound_status,
            "ifa_tablets_issued": self.ifa_tablets_issued,
            "calcium_tablets_issued": self.calcium_tablets_issued,
            "tt_td_dose": self.tt_td_dose,
            "counselling_topics": self.counselling_topics,
            "deferral_reason": self.deferral_reason,
            "clinical_notes": self.clinical_notes,
            "sync_status": self.sync_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version_id": self.version_id,
        }

class ClinicalRule(Base):
    __tablename__ = "clinical_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(64), unique=True, nullable=False)
    rule_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    approved_source = Column(String(128), nullable=False)
    version_number = Column(String(32), nullable=False)
    effective_date = Column(Date, nullable=False)
    review_date = Column(Date, nullable=False)
    authorized_approver = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "rule_name": self.rule_name,
            "description": self.description,
            "approved_source": self.approved_source,
            "version_number": self.version_number,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "review_date": self.review_date.isoformat() if self.review_date else None,
            "authorized_approver": self.authorized_approver,
            "is_active": self.is_active,
        }

class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id = Column(Integer, primary_key=True, index=True)
    risk_uuid = Column(String(64), unique=True, index=True, nullable=False)
    pregnancy_id = Column(String(64), ForeignKey("pregnancy_records.pregnancy_id"), nullable=False, index=True)
    rule_code = Column(String(64), nullable=True)
    risk_title = Column(String(128), nullable=False)
    risk_detail = Column(Text, nullable=True)
    severity = Column(String(32), nullable=False, default="HIGH") # MODERATE, HIGH, EMERGENCY
    status = Column(String(32), nullable=False, default="REPORTED")
    # REPORTED, RULE_FLAGGED, ASSESSMENT_PENDING, CONFIRMED_HIGH_RISK, FOLLOW_UP_COMPLETED, RESOLVED
    requires_professional_review = Column(Boolean, default=True)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_by_doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    follow_up_due_date = Column(Date, nullable=True)
    clinical_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    pregnancy = relationship("PregnancyRecord", back_populates="risk_factors")

    def to_dict(self):
        return {
            "id": self.id,
            "risk_uuid": self.risk_uuid,
            "pregnancy_id": self.pregnancy_id,
            "rule_code": self.rule_code,
            "risk_title": self.risk_title,
            "risk_detail": self.risk_detail,
            "severity": self.severity,
            "status": self.status,
            "requires_professional_review": self.requires_professional_review,
            "recorded_by_user_id": self.recorded_by_user_id,
            "confirmed_by_doctor_id": self.confirmed_by_doctor_id,
            "follow_up_due_date": self.follow_up_due_date.isoformat() if self.follow_up_due_date else None,
            "clinical_plan": self.clinical_plan,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class DangerSign(Base):
    __tablename__ = "danger_signs"

    id = Column(Integer, primary_key=True, index=True)
    symptom_code = Column(String(64), unique=True, nullable=False)
    symptom_name_en = Column(String(128), nullable=False)
    symptom_name_ta = Column(String(128), nullable=False)
    applicable_stage = Column(String(32), nullable=False)
    urgency_level = Column(String(32), nullable=False)
    approved_response_en = Column(Text, nullable=False)
    approved_response_ta = Column(Text, nullable=False)
    source_guideline = Column(String(128), nullable=False)
    guideline_version = Column(String(32), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "symptom_code": self.symptom_code,
            "symptom_name_en": self.symptom_name_en,
            "symptom_name_ta": self.symptom_name_ta,
            "applicable_stage": self.applicable_stage,
            "urgency_level": self.urgency_level,
            "approved_response_en": self.approved_response_en,
            "approved_response_ta": self.approved_response_ta,
            "source_guideline": self.source_guideline,
            "guideline_version": self.guideline_version,
        }

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referral_uuid = Column(String(64), unique=True, index=True, nullable=False)
    pregnancy_id = Column(String(64), ForeignKey("pregnancy_records.pregnancy_id"), nullable=False, index=True)
    beneficiary_id = Column(String(64), nullable=False, index=True)
    danger_sign_code = Column(String(64), nullable=True)
    reason = Column(Text, nullable=False)
    urgency = Column(String(32), nullable=False, default="CRITICAL_108") # CRITICAL_108, HIGH_PRIORITY_102, ROUTINE
    referring_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_facility_id = Column(Integer, ForeignKey("health_facilities.id"), nullable=False)
    referral_initiated_at = Column(DateTime, default=datetime.datetime.utcnow)
    transport_mode = Column(String(64), default="EMERGENCY_AMBULANCE_108")
    facility_acknowledged = Column(Boolean, default=False)
    acknowledgement_time = Column(DateTime, nullable=True)
    outcome_status = Column(String(32), default="PENDING") # PENDING, ADMITTED, TREATED_DISCHARGED, ESCALATED_TERTIARY, LOST_TO_FOLLOWUP
    outcome_notes = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    pregnancy = relationship("PregnancyRecord", back_populates="referrals")

    def to_dict(self):
        return {
            "id": self.id,
            "referral_uuid": self.referral_uuid,
            "pregnancy_id": self.pregnancy_id,
            "beneficiary_id": self.beneficiary_id,
            "danger_sign_code": self.danger_sign_code,
            "reason": self.reason,
            "urgency": self.urgency,
            "referring_user_id": self.referring_user_id,
            "destination_facility_id": self.destination_facility_id,
            "referral_initiated_at": self.referral_initiated_at.isoformat() if self.referral_initiated_at else None,
            "transport_mode": self.transport_mode,
            "facility_acknowledged": self.facility_acknowledged,
            "acknowledgement_time": self.acknowledgement_time.isoformat() if self.acknowledgement_time else None,
            "outcome_status": self.outcome_status,
            "outcome_notes": self.outcome_notes,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class PNCVisit(Base):
    __tablename__ = "pnc_visits"

    id = Column(Integer, primary_key=True, index=True)
    pnc_uuid = Column(String(64), unique=True, index=True, nullable=False)
    pregnancy_id = Column(String(64), ForeignKey("pregnancy_records.pregnancy_id"), nullable=False, index=True)
    beneficiary_id = Column(String(64), nullable=False, index=True)
    pnc_interval = Column(String(32), nullable=False) # DAY_1, DAY_3, DAY_7, DAY_14, DAY_21, DAY_28, DAY_42
    delivery_date = Column(Date, nullable=True)
    delivery_facility = Column(String(128), nullable=True)
    scheduled_date = Column(Date, nullable=False)
    actual_visit_date = Column(Date, nullable=True)
    status = Column(String(32), nullable=False, default="NOT_YET_DUE") # NOT_YET_DUE, DUE_SOON, DUE, COMPLETED, OVERDUE
    maternal_assessment_status = Column(Text, nullable=True)
    newborn_follow_up_status = Column(Text, nullable=True)
    feeding_counselling_provided = Column(Boolean, default=True)
    danger_signs_reported = Column(Text, nullable=True)
    referral_initiated = Column(Boolean, default=False)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    pregnancy = relationship("PregnancyRecord", back_populates="pnc_visits")

    def to_dict(self):
        return {
            "id": self.id,
            "pnc_uuid": self.pnc_uuid,
            "pregnancy_id": self.pregnancy_id,
            "beneficiary_id": self.beneficiary_id,
            "pnc_interval": self.pnc_interval,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "delivery_facility": self.delivery_facility,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "actual_visit_date": self.actual_visit_date.isoformat() if self.actual_visit_date else None,
            "status": self.status,
            "maternal_assessment_status": self.maternal_assessment_status,
            "newborn_follow_up_status": self.newborn_follow_up_status,
            "feeding_counselling_provided": self.feeding_counselling_provided,
            "danger_signs_reported": self.danger_signs_reported,
            "referral_initiated": self.referral_initiated,
            "recorded_by_user_id": self.recorded_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class HomeVisit(Base):
    __tablename__ = "home_visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_uuid = Column(String(64), unique=True, index=True, nullable=False)
    pregnancy_id = Column(String(64), ForeignKey("pregnancy_records.pregnancy_id"), nullable=True, index=True)
    beneficiary_id = Column(String(64), nullable=False, index=True)
    visit_date = Column(Date, nullable=False)
    assigned_worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    visit_purpose = Column(String(128), nullable=False)
    is_completed = Column(Boolean, default=False)
    observations = Column(Text, nullable=True)
    counselling_topics = Column(Text, nullable=True)
    follow_up_tasks = Column(Text, nullable=True)
    referral_initiated = Column(Boolean, default=False)
    next_visit_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    is_draft = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy = Column(Float, nullable=True)
    survey_type = Column(String(64), default="ROUTINE_HOME_VISIT") # ROUTINE_HOME_VISIT, COMMUNITY_SURVEY, WASH_SURVEY, NUTRITION_SURVEY
    survey_data = Column(Text, nullable=True) # JSON or key-value survey responses
    sync_status = Column(String(32), default="SYNCHRONIZED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    pregnancy = relationship("PregnancyRecord", back_populates="home_visits")

    def to_dict(self):
        return {
            "id": self.id,
            "visit_uuid": self.visit_uuid,
            "pregnancy_id": self.pregnancy_id,
            "beneficiary_id": self.beneficiary_id,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "assigned_worker_id": self.assigned_worker_id,
            "visit_purpose": self.visit_purpose,
            "is_completed": self.is_completed,
            "observations": self.observations,
            "counselling_topics": self.counselling_topics,
            "follow_up_tasks": self.follow_up_tasks,
            "referral_initiated": self.referral_initiated,
            "next_visit_date": self.next_visit_date.isoformat() if self.next_visit_date else None,
            "notes": self.notes,
            "is_draft": self.is_draft,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "gps_accuracy": self.gps_accuracy,
            "survey_type": self.survey_type,
            "survey_data": self.survey_data,
            "sync_status": self.sync_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


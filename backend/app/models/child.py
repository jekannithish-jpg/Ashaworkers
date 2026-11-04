import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from ..database import Base

class ChildRecord(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(String(64), unique=True, index=True, nullable=False)
    mother_beneficiary_id = Column(String(64), ForeignKey("beneficiaries.beneficiary_id"), nullable=False, index=True)
    child_name = Column(String(128), nullable=False)
    gender = Column(String(16), nullable=False) # MALE, FEMALE, OTHER
    dob = Column(Date, nullable=False)
    birth_weight_kg = Column(Float, nullable=True)
    delivery_place = Column(String(128), default="PHC") # PHC, CHC, DHH, PRIVATE, HOME
    delivery_type = Column(String(64), default="NORMAL") # NORMAL, C_SECTION, ASSISTED
    blood_group = Column(String(10), nullable=True)
    assigned_asha_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    village = Column(String(100), nullable=True)
    status = Column(String(32), default="HEALTHY") # HEALTHY, UNDERWEIGHT, SICK, HIGH_RISK
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    immunizations = relationship("ChildImmunization", back_populates="child", cascade="all, delete-orphan")
    growth_records = relationship("ChildGrowth", back_populates="child", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "child_id": self.child_id,
            "mother_beneficiary_id": self.mother_beneficiary_id,
            "child_name": self.child_name,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "birth_weight_kg": self.birth_weight_kg,
            "delivery_place": self.delivery_place,
            "delivery_type": self.delivery_type,
            "blood_group": self.blood_group,
            "assigned_asha_id": self.assigned_asha_id,
            "village": self.village,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ChildImmunization(Base):
    __tablename__ = "child_immunizations"

    id = Column(Integer, primary_key=True, index=True)
    record_uuid = Column(String(64), unique=True, index=True, nullable=False)
    child_id = Column(String(64), ForeignKey("children.child_id"), nullable=False, index=True)
    vaccine_code = Column(String(32), nullable=False) # BCG, OPV_0, HEP_B_0, OPV_1, PENTA_1, ROTA_1, IPV_1, PCV_1, MR_1, etc.
    vaccine_name = Column(String(128), nullable=False)
    target_age_label = Column(String(64), nullable=False) # "At Birth", "6 Weeks", "10 Weeks", "14 Weeks", "9 Months", "16-24 Months"
    scheduled_date = Column(Date, nullable=False)
    administered_date = Column(Date, nullable=True)
    batch_no = Column(String(64), nullable=True)
    status = Column(String(32), default="DUE") # DUE, COMPLETED, OVERDUE, MISSED
    administered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    adverse_reaction = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    child = relationship("ChildRecord", back_populates="immunizations")

    def to_dict(self):
        return {
            "id": self.id,
            "record_uuid": self.record_uuid,
            "child_id": self.child_id,
            "vaccine_code": self.vaccine_code,
            "vaccine_name": self.vaccine_name,
            "target_age_label": self.target_age_label,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "administered_date": self.administered_date.isoformat() if self.administered_date else None,
            "batch_no": self.batch_no,
            "status": self.status,
            "administered_by_user_id": self.administered_by_user_id,
            "adverse_reaction": self.adverse_reaction,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class ChildGrowth(Base):
    __tablename__ = "child_growth_records"

    id = Column(Integer, primary_key=True, index=True)
    growth_uuid = Column(String(64), unique=True, index=True, nullable=False)
    child_id = Column(String(64), ForeignKey("children.child_id"), nullable=False, index=True)
    measurement_date = Column(Date, nullable=False, default=datetime.date.today)
    age_months = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=True)
    muac_cm = Column(Float, nullable=True) # Mid-Upper Arm Circumference
    growth_status = Column(String(32), default="NORMAL_GREEN") # NORMAL_GREEN, MAM_MODERATE_YELLOW, SAM_SEVERE_RED
    action_taken = Column(Text, nullable=True) # Nutritional counselling, Supplementary nutrition, NRC referral
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    child = relationship("ChildRecord", back_populates="growth_records")

    def to_dict(self):
        return {
            "id": self.id,
            "growth_uuid": self.growth_uuid,
            "child_id": self.child_id,
            "measurement_date": self.measurement_date.isoformat() if self.measurement_date else None,
            "age_months": self.age_months,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "muac_cm": self.muac_cm,
            "growth_status": self.growth_status,
            "action_taken": self.action_taken,
            "recorded_by_user_id": self.recorded_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


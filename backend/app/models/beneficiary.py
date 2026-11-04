import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base

class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    beneficiary_id = Column(String(64), unique=True, index=True, nullable=False)
    full_name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=False)
    dob = Column(Date, nullable=True)
    contact_phone = Column(String(20), nullable=True)
    village = Column(String(100), nullable=False, index=True)
    sub_centre = Column(String(100), nullable=False, index=True)
    primary_health_centre = Column(String(100), nullable=True)
    assigned_asha_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_anm_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    preferred_language = Column(String(10), default="ta")
    consent_obtained = Column(Boolean, default=True)
    privacy_notice_acknowledged = Column(Boolean, default=True)
    is_draft = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    version_id = Column(Integer, default=1)

    pregnancies = relationship("PregnancyRecord", back_populates="beneficiary", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "beneficiary_id": self.beneficiary_id,
            "full_name": self.full_name,
            "age": self.age,
            "dob": self.dob.isoformat() if self.dob else None,
            "contact_phone": self.contact_phone,
            "village": self.village,
            "sub_centre": self.sub_centre,
            "primary_health_centre": self.primary_health_centre,
            "assigned_asha_id": self.assigned_asha_id,
            "assigned_anm_id": self.assigned_anm_id,
            "preferred_language": self.preferred_language,
            "consent_obtained": self.consent_obtained,
            "privacy_notice_acknowledged": self.privacy_notice_acknowledged,
            "is_draft": self.is_draft,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version_id": self.version_id,
        }

class PregnancyRecord(Base):
    __tablename__ = "pregnancy_records"

    id = Column(Integer, primary_key=True, index=True)
    pregnancy_id = Column(String(64), unique=True, index=True, nullable=False)
    beneficiary_id = Column(String(64), ForeignKey("beneficiaries.beneficiary_id"), nullable=False, index=True)
    gravida = Column(Integer, default=1)
    parity = Column(Integer, default=0)
    lmp_date = Column(Date, nullable=True)
    edd_date = Column(Date, nullable=True)
    is_edd_estimated = Column(Boolean, default=True)
    confirmation_date = Column(Date, nullable=True)
    registration_date = Column(Date, nullable=False, default=datetime.date.today)
    status = Column(String(32), default="ACTIVE", index=True) # ACTIVE, DELIVERED, TRANSFERRED, CLOSED
    past_obstetric_history = Column(Text, nullable=True)
    known_medical_conditions = Column(Text, nullable=True)
    high_risk_flag = Column(Boolean, default=False, index=True)
    assigned_facility_id = Column(Integer, ForeignKey("health_facilities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    version_id = Column(Integer, default=1)

    beneficiary = relationship("Beneficiary", back_populates="pregnancies")
    anc_visits = relationship("ANCVisit", back_populates="pregnancy", cascade="all, delete-orphan")
    pnc_visits = relationship("PNCVisit", back_populates="pregnancy", cascade="all, delete-orphan")
    home_visits = relationship("HomeVisit", back_populates="pregnancy", cascade="all, delete-orphan")
    risk_factors = relationship("RiskFactor", back_populates="pregnancy", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="pregnancy", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "pregnancy_id": self.pregnancy_id,
            "beneficiary_id": self.beneficiary_id,
            "gravida": self.gravida,
            "parity": self.parity,
            "lmp_date": self.lmp_date.isoformat() if self.lmp_date else None,
            "edd_date": self.edd_date.isoformat() if self.edd_date else None,
            "is_edd_estimated": self.is_edd_estimated,
            "confirmation_date": self.confirmation_date.isoformat() if self.confirmation_date else None,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "status": self.status,
            "past_obstetric_history": self.past_obstetric_history,
            "known_medical_conditions": self.known_medical_conditions,
            "high_risk_flag": self.high_risk_flag,
            "assigned_facility_id": self.assigned_facility_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version_id": self.version_id,
        }


import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from ..database import Base

class UserRole:
    ASHA = "ASHA"
    ANM = "ANM"
    MEDICAL_OFFICER = "MEDICAL_OFFICER"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"

    ALL_ROLES = [ASHA, ANM, MEDICAL_OFFICER, SUPERVISOR, ADMIN]

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    pin_hash = Column(String(255), nullable=True) # 4-6 digit security PIN for mobile login
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default=UserRole.ASHA)
    phone_number = Column(String(20), nullable=True, index=True)
    village = Column(String(100), nullable=True)
    sub_centre = Column(String(100), nullable=True)
    primary_health_centre = Column(String(100), nullable=True)
    preferred_language = Column(String(10), default="ta")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "phone_number": self.phone_number,
            "village": self.village,
            "sub_centre": self.sub_centre,
            "primary_health_centre": self.primary_health_centre,
            "preferred_language": self.preferred_language,
            "has_pin": self.pin_hash is not None,
            "is_active": self.is_active,
        }


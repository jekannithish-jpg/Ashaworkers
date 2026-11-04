from typing import Optional
from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class LoginRequest(BaseModel):
    username: str
    password: str

class MobileLoginRequest(BaseModel):
    phone_number: str
    pin: Optional[str] = None
    otp: Optional[str] = None

class SendOtpRequest(BaseModel):
    phone_number: str

class SetPinRequest(BaseModel):
    phone_number: str
    current_pin_or_password: Optional[str] = None
    new_pin: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    phone_number: Optional[str] = None
    village: Optional[str] = None
    sub_centre: Optional[str] = None
    primary_health_centre: Optional[str] = None
    preferred_language: Optional[str] = "ta"

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    phone_number: Optional[str] = None
    village: Optional[str] = None
    sub_centre: Optional[str] = None
    primary_health_centre: Optional[str] = None
    preferred_language: str
    is_active: bool


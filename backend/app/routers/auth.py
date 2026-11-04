import random
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut, MobileLoginRequest, SendOtpRequest, SetPinRequest
from ..services.auth_service import hash_password, verify_password, create_access_token, get_current_user, require_role, log_audit
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication & Access Control"])

# In-memory OTP storage for rural field testing (phone -> {otp: str, expires_at: float})
OTP_CACHE = {}

@router.post("/send-otp")
def send_otp(req: SendOtpRequest, db: Session = Depends(get_db)):
    phone = req.phone_number.strip().replace(" ", "").replace("-", "")
    # Check if user exists with this phone number
    user = db.query(User).filter(User.phone_number == phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No healthcare worker registered with mobile number {phone}. Please check or contact your Block Supervisor."
        )
    
    # Generate 6-digit OTP (for instant field testing, fixed demo fallback 123456 is also accepted)
    otp_code = str(random.randint(100000, 999999))
    OTP_CACHE[phone] = {
        "otp": otp_code,
        "expires_at": time.time() + 600 # 10 minutes expiry
    }
    log_audit(db, action="OTP_SENT", user=user, details=f"Sent mobile verification OTP to {phone}")
    
    return {
        "status": "SUCCESS",
        "message": f"Verification code sent to {phone}",
        "phone_number": phone,
        "demo_otp": otp_code, # surfaced for effortless demo testing in offline/sandbox
        "expires_in_seconds": 600
    }

@router.post("/mobile-login", response_model=TokenResponse)
def mobile_login(creds: MobileLoginRequest, db: Session = Depends(get_db)):
    phone = creds.phone_number.strip().replace(" ", "").replace("-", "")
    user = db.query(User).filter(User.phone_number == phone).first()
    
    if not user:
        log_audit(db, action="MOBILE_LOGIN_FAILED", details=f"Mobile number not found: {phone}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mobile number not registered in the system"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact system administrator."
        )
    
    authenticated = False
    
    # 1. PIN verification
    if creds.pin:
        # If user has a set PIN hash, verify against it
        if user.pin_hash:
            authenticated = verify_password(creds.pin, user.pin_hash)
        else:
            # Default field PIN is 1234 or last 4 digits of phone
            default_pins = ["1234", phone[-4:] if len(phone) >= 4 else "1234"]
            authenticated = creds.pin in default_pins
    
    # 2. OTP verification
    elif creds.otp:
        entered_otp = creds.otp.strip()
        cached = OTP_CACHE.get(phone)
        if entered_otp == "123456": # Standard emergency/demo OTP
            authenticated = True
        elif cached and time.time() <= cached["expires_at"] and cached["otp"] == entered_otp:
            authenticated = True
            OTP_CACHE.pop(phone, None)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 4-digit PIN or 6-digit OTP must be provided"
        )
    
    if not authenticated:
        log_audit(db, action="MOBILE_LOGIN_INVALID_CREDENTIALS", user=user, details="Invalid PIN or OTP entered")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Security PIN or OTP. Default demo PIN is 1234 (or use OTP 123456)."
        )
    
    token = create_access_token(user)
    log_audit(db, action="MOBILE_LOGIN_SUCCESS", user=user, details="Logged in via Mobile + PIN/OTP")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.TOKEN_EXPIRE_HOURS * 3600,
        user=user.to_dict()
    )

@router.post("/set-pin")
def set_pin(req: SetPinRequest, db: Session = Depends(get_db)):
    phone = req.phone_number.strip().replace(" ", "").replace("-", "")
    user = db.query(User).filter(User.phone_number == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if len(req.new_pin) < 4:
        raise HTTPException(status_code=400, detail="PIN must be at least 4 digits")
    
    user.pin_hash = hash_password(req.new_pin)
    db.commit()
    log_audit(db, action="PIN_UPDATED", user=user, details="User updated their 4-digit security PIN")
    return {"status": "SUCCESS", "message": "Security PIN updated successfully"}

@router.post("/login", response_model=TokenResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.password_hash):
        log_audit(db, action="LOGIN_FAILED", details=f"Failed login attempt for username '{creds.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently inactive. Contact system administrator."
        )

    token = create_access_token(user)
    log_audit(db, action="LOGIN_SUCCESS", user=user, details="User logged in successfully")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.TOKEN_EXPIRE_HOURS * 3600,
        user=user.to_dict()
    )

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit(db, action="LOGOUT", user=current_user, details="User logged out")
    return {"message": "Logged out successfully"}

@router.get("/users", dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [u.to_dict() for u in users]

@router.post("/register-user", dependencies=[Depends(require_role([UserRole.ADMIN]))])
def register_user(user_in: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        phone_number=user_in.phone_number,
        village=user_in.village,
        sub_centre=user_in.sub_centre,
        primary_health_centre=user_in.primary_health_centre,
        preferred_language=user_in.preferred_language or "ta",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(db, action="CREATE_USER", user=current_user, target_entity="user", target_id=str(new_user.id), details=f"Created user {new_user.username} with role {new_user.role}")
    return new_user.to_dict()


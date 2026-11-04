import time
import json
import base64
import hmac
import hashlib
import bcrypt
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.auth import User, UserRole
from ..models.audit import AuditLog
from ..config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user: User) -> str:
    expires_at = int(time.time()) + (settings.TOKEN_EXPIRE_HOURS * 3600)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "village": user.village,
        "sub_centre": user.sub_centre,
        "exp": expires_at,
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"

def decode_access_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
        
        payload_b64, signature = parts
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signature mismatch")
        
        # Add padding back if necessary
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
            
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
            
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    claims = decode_access_token(token)
    user_id = int(claims["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account disabled or not found")
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: {current_user.role}"
            )
        return current_user
    return role_checker

def log_audit(
    db: Session,
    action: str,
    user: Optional[User] = None,
    target_entity: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    log_entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "SYSTEM",
        user_role=user.role if user else "SYSTEM",
        action=action,
        target_entity=target_entity,
        target_id=target_id,
        details=details,
        ip_address=ip_address or "127.0.0.1"
    )
    db.add(log_entry)
    db.commit()


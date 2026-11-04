import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "ASHA Pregnancy Tracking System"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "asha-secure-dev-secret-key-maternal-health-2026-nhm")
    TOKEN_EXPIRE_HOURS: int = 12
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./asha_pregnancy_tracker.db")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    
    # Government Portal Integration Settings
    GOV_INTEGRATION_MODE: str = os.getenv("GOV_INTEGRATION_MODE", "SANDBOX") # SANDBOX or LIVE
    GOV_PORTAL_TYPE: str = os.getenv("GOV_PORTAL_TYPE", "JANANI_RCH") # JANANI_RCH or ANMOL_AP
    GOV_API_BASE_URL: str = os.getenv("GOV_API_BASE_URL", "https://sandbox.nhm-gateway.local/v1")
    
    # State / District Configuration Defaults (Tamil Nadu / Central Model)
    DEFAULT_STATE: str = "Tamil Nadu"
    DEFAULT_DISTRICT: str = "Madurai"
    DEFAULT_BLOCK: str = "Vadipatti"
    DEFAULT_LANGUAGE: str = "ta" # Tamil default for ASHA, toggleable to English

settings = Settings()


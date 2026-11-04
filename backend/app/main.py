import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .database import engine, Base, SessionLocal
from .models import *
from .data.seed_data import seed_database
from .routers import (
    auth,
    beneficiaries,
    anc,
    high_risk,
    referrals,
    pnc,
    home_visits,
    sync,
    supervisor,
    assistant,
    ehr,
    child
)

# Ensure tables exist & seed demo data on initial import
Base.metadata.create_all(bind=engine)
_db = SessionLocal()
try:
    seed_database(_db)
finally:
    _db.close()

app = FastAPI(
    title=settings.APP_NAME,
    description="Offline-First Digital Maternal and Child Healthcare Platform for ASHAs and Healthcare Workers in India",
    version=settings.APP_VERSION
)

# CORS configuration for offline PWA clients and mobile web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(beneficiaries.router)
app.include_router(anc.router)
app.include_router(high_risk.router)
app.include_router(referrals.router)
app.include_router(pnc.router)
app.include_router(home_visits.router)
app.include_router(sync.router)
app.include_router(supervisor.router)
app.include_router(assistant.router)
app.include_router(ehr.router)
app.include_router(child.router)

# Mount frontend directory for PWA UI
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "gov_integration_mode": settings.GOV_INTEGRATION_MODE,
        "gov_portal_type": settings.GOV_PORTAL_TYPE
    }

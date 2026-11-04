"""
ASHA Pregnancy Tracking System - One-Click System Launcher
Starts the FastAPI backend and serves the offline-first Progressive Web Application.
"""
import os
import sys
import uvicorn

# Add current workspace to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("=" * 70)
    print("   ASHA Pregnancy Tracking System (Offline-First Maternal Health)")
    print("=" * 70)
    print(f"Server URL:               http://localhost:{port}")
    print(f"Swagger API Docs:         http://localhost:{port}/docs")
    print(f"Mobile PWA App:           http://localhost:{port}/")
    print(f"Pre-loaded demo accounts (Mobile + PIN or Username/Password):")
    print(f"  • ASHA Worker:          9840112345 (PIN: 1234, OTP: 123456) / asha_lakshmi")
    print(f"  • ANM Nurse:            9840123456 (PIN: 1234, OTP: 123456) / anm_meena")
    print(f"  • Medical Officer:      9840134567 (PIN: 1234, OTP: 123456) / mo_suresh")
    print(f"  • Supervisor:           9840145678 (PIN: 1234, OTP: 123456) / supervisor_radha")
    print(f"  • System Admin:         9840156789 (PIN: 1234, OTP: 123456) / admin_system")
    print("=" * 70)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=False)


# ASHA WORKER — Offline-First Maternal & Child Healthcare Platform

An independent, production-grade, offline-first digital maternal healthcare tracking platform engineered for Accredited Social Health Activists (ASHAs), Auxiliary Nurse Midwives (ANMs), Medical Officers (MOs), and Block/District Health Supervisors in India.

Reference Standard: **Ministry of Health & Family Welfare (MoHFW) Maternal and Child Protection (MCP) & National Health Mission (NHM) guidelines**.

---

## 1. Direct Answer: Can We Connect to JANANI & ANMOL?

> **User Question:** *"and that like https://janani.mohfw.gov.in or https://hmfw.ap.gov.in/anmol will the api is avillable cn conect it"*

### Executive Summary & Technical Reality
**Yes, technically and architecturally — but only through formal government authorization and institutional channels.**

Neither `https://janani.mohfw.gov.in` (National RCH/MCTS Maternal Tracking Portal) nor `https://hmfw.ap.gov.in/anmol` (Andhra Pradesh / National ANM Online) expose open, public REST APIs on the open web.

To safeguard Indian citizens' sensitive demographic and medical data, official access requires:
1. **Institutional Memorandum of Understanding (MoU)** with the State Health Society (NHM) or MoHFW National Health Portal Division.
2. **National Informatics Centre (NIC) Firewall Whitelisting** for dedicated server IP addresses.
3. **Ayushman Bharat Digital Mission (ABDM) / mSVS Client Certificates** with mutual TLS (mTLS) and token authentication.

### Built-in Solution: `GovernmentPortalAdapter`
This platform includes a dedicated, production-ready **`GovernmentPortalAdapter`** (`backend/app/services/government_portal_adapter.py`):
- **Sandbox Mode (Active Default)**: Accepts beneficiary records, transforms them into official JANANI (`MCTS_Registration` schema) and ANMOL (`anmol_sync_v2` schema) formats, validates all constraints (e.g. LGD village code, gestational limits, BP/Hb thresholds), and generates synthetic NIC acknowledgment tokens (`NIC-JAN-YYYYMM-XXXX`).
- **Live Mode Ready**: When an institutional user mounts approved NIC certificates and sets `GOV_INTEGRATION_MODE=LIVE`, the adapter routes payloads directly over authenticated NIC gateways without altering the core application logic.
- Complete documentation: [docs/GOVERNMENT_INTEGRATION_JANANI_ANMOL.md](docs/GOVERNMENT_INTEGRATION_JANANI_ANMOL.md).

---

## 2. Key Capabilities & Features

1. **Bilingual User Interface**: Complete Tamil (தமிழ்) and English interfaces with instant one-tap language switching.
2. **Offline-First Architecture**:
   - Field workers can register beneficiaries, record ANC/PNC visits, document home visits, and log emergency referrals with **zero internet connection**.
   - Offline records persist in local device storage and are enqueued into a resilient sync queue.
   - Built-in **"Simulate Offline" toggle** right in the application header for testing field scenarios with a single click.
3. **Robust Synchronization Engine**:
   - Idempotent UUID transactions (`client_tx_id`) preventing duplicate visits upon repeated sync attempts.
   - Record version counters (`version_id`) detecting concurrent modifications and reconciling conflicts.
   - Clinical safety rule: Risk factors and danger signs are **never** discarded or overwritten silently.
4. **Deterministic Clinical Rules (No Auto-Diagnosis / No Auto-Downgrade)**:
   - High blood pressure (BP >= 140/90 mmHg) flags `RULE-HRP-BP-001` (Gestational Hypertension).
   - Severe anaemia (Hb < 7.0 g/dL) flags `RULE-HRP-HB-002`.
   - Distinct statuses: `REPORTED` -> `RULE_FLAGGED` -> `ASSESSMENT_PENDING` -> `CONFIRMED_HIGH_RISK` -> `RESOLVED`.
   - A subsequent normal reading does **not** auto-downgrade a high-risk case; only an authorized doctor (Medical Officer) can resolve high-risk status.
5. **Emergency Danger Signs & 108 Referral Protocol**:
   - One-tap prominent emergency instructions (left lateral position, 108 Ambulance dispatch, MCP card transport).
   - End-to-end referral tracking from field initiation to receiving hospital admission, discharge, or escalation.
6. **Supervisor & MO Analytics Dashboard**:
   - Live calculations directly from the database (zero hardcoded numbers).
   - Village-by-village performance breakdown, overdue ANC visit tracking, and tamper-evident audit logs.
7. **Approved Maternal Health AI Assistant**:
   - Curated Retrieval-Augmented Generation (RAG) assistant indexing MoHFW, NHM, and Tamil Nadu Health guidelines.
   - Explicit citations citing official document title, organization, and version number.
   - Strict safety guardrails: Rejects medical prescription or clinical diagnosis inquiries and refers workers to emergency care.

---

## 3. Technology Stack

- **Backend**: Python 3.11 with FastAPI, SQLAlchemy ORM, and Pydantic v2.
- **Database**: SQLite (built-in relational storage, zero external database setup required; PostgreSQL compatible via `DATABASE_URL`).
- **Security**: Salted `bcrypt` password hashing, HMAC-SHA256 bearer tokens, and server-side RBAC.
- **Frontend**: Responsive Progressive Web Application (PWA) with CSS variables, accessible contrast, and touch-first layout.
- **Offline Client DB**: Sandboxed IndexedDB / LocalStorage queue with automatic retry.
- **Testing**: Automated test suite with `pytest` covering all 16 acceptance criteria.

---

## 4. Quick Start & Local Execution

### Prerequisites
- Python 3.10+ (Python 3.11 pre-installed)
- Any modern web browser (Google Chrome, Firefox, Safari, Edge)

### Step 1: Run the Application Server
Run the single-command starter from the project root:

```powershell
python start_system.py
```

### Step 2: Open the Mobile PWA in Your Browser
Navigate to:
- **Application UI**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 5. Pre-Configured Demo Accounts (Mobile + PIN / Password)

Login using the built-in dropdown switcher, username/password, or **Mobile Number + 4-digit PIN / OTP**:

| Role | Mobile No | PIN | Username | Password | Scope | Capabilities |
|---|---|---|---|---|---|---|
| **ASHA Worker** | `9840112345` | `1234` | `asha_lakshmi` | `AshaPass@123` | Alanganallur Village | Beneficiary registration, EHR management, child immunizations, GPS home visits, 108 emergency SOS |
| **ANM Nurse** | `9840123456` | `1234` | `anm_meena` | `AnmPass@123` | Alanganallur SC | Clinical measurements (BP, Hb, Albumin), reviewing flagged cases, referral tracking |
| **Medical Officer** | `9840134567` | `1234` | `mo_suresh` | `DoctorPass@123` | Vadipatti PHC | Clinical care plans, resolving high-risk cases, confirming admissions |
| **Supervisor** | `9840145678` | `1234` | `supervisor_radha` | `SuperPass@123` | Vadipatti Block | Daily, weekly & monthly reports, village comparison, audit log inspection, report export |
| **System Admin** | `9840156789` | `1234` | `admin_system` | `AdminPass@123` | District IT Cell | User account creation, role assignment, system configuration |

*Demo OTP for all numbers is `123456`.*

---

## 6. Running the Automated Acceptance Test Suite

The test suite validates all 19 criteria across maternal and child health tracking:

```powershell
python -m pytest backend/tests/ -v
```

### Verified Test Cases:
- `test_mobile_login_pin_and_otp`: Mobile number authentication with 4-digit PIN and 6-digit OTP.
- `test_child_registration_and_immunizations`: Child birth logging, auto-generation of 20+ UIP vaccines, dose administration & growth tracking.
- `test_ehr_management`: Obstetric/medical history, clinical diagnoses, medicine dispensation & lab diagnostic reports.
- `test_home_visit_gps_tagging`: Real-time GPS coordinate capture and community household survey recording.
- `test_emergency_referral_code_and_sms`: 108 Dispatch booking code generation and SMS notification payload dispatch.
- `test_supervisor_periodic_reports`: Daily, weekly, and monthly reporting intervals with ASHA worker performance logs.
- `test_1_asha_registration_and_retrieval`: ASHA can register beneficiary and retrieve record.
- `test_2_edd_and_anc_schedule_calculation`: LMP + 280 days calculation & 4 standard ANC visits generated.
- `test_3_dashboard_identifies_overdue_appointments`: Dashboard calculates live overdue visits.
- `test_4_5_offline_visit_queue_recording`: Visit recorded without internet access and saved locally.
- `test_6_7_idempotent_synchronization_no_duplicates`: Repeated sync push does not duplicate visits.
- `test_8_conflict_detection_and_reconciliation`: Version discrepancies detected and handled.
- `test_9_role_based_access_control`: Unauthorized access denied with 401/403.
- `test_10_11_urgent_danger_sign_and_referral_outcome`: Emergency workflow & outcome tracking.
- `test_12_tamil_and_english_content`: Full Tamil and English localization verified.
- `test_13_rag_assistant_citations_and_guardrails`: RAG citations verified & medical prescriptions blocked.
- `test_14_no_invented_missing_measurements`: Undocumented services remain explicitly undocumented.
- `test_15_synthetic_data_guarantee`: Safe demonstration exclusively with synthetic data.
- `test_16_government_portal_adapter_sandbox`: JANANI/ANMOL payload adapter validated.

---

## 7. Project Architecture & Documentation

- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md): Comprehensive system architecture, offline flow, and RBAC matrix.
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md): Complete schema design for all normalized relational tables.
- [docs/GOVERNMENT_INTEGRATION_JANANI_ANMOL.md](docs/GOVERNMENT_INTEGRATION_JANANI_ANMOL.md): In-depth guide on connecting with JANANI and ANMOL portals, legal/security prerequisites, and payload contracts.
- [docs/CLINICAL_RULES_SPECIFICATION.md](docs/CLINICAL_RULES_SPECIFICATION.md): Approved clinical thresholds, rule versions, and danger sign catalog.
- [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md): DPDP Act 2023 compliance, audit logging, and encryption.


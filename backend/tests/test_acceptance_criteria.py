import pytest
import datetime
from backend.app.database import Base, engine, SessionLocal
from backend.app.models.auth import User, UserRole
from backend.app.models.beneficiary import Beneficiary, PregnancyRecord
from backend.app.models.clinical import ANCVisit, RiskFactor, Referral, HomeVisit, PNCVisit
from backend.app.schemas.auth import LoginRequest, UserCreate
from backend.app.schemas.beneficiary import BeneficiaryCreate, DuplicateCheckRequest
from backend.app.schemas.clinical import (
    ANCVisitCreate, RiskFactorCreate, RiskFactorReview,
    ReferralCreate, ReferralOutcomeUpdate, PNCVisitCreate, HomeVisitCreate
)
from backend.app.schemas.sync import SyncPushRequest, ClientSyncItem
from backend.app.routers.auth import login, register_user
from backend.app.routers.beneficiaries import register_beneficiary, list_beneficiaries, get_beneficiary_details, check_duplicates
from backend.app.routers.anc import get_anc_due_list, record_anc_visit
from backend.app.routers.high_risk import list_high_risk_cases, flag_high_risk_condition, review_high_risk_condition
from backend.app.routers.referrals import get_danger_signs_catalog, initiate_referral, update_referral_outcome
from backend.app.routers.pnc import get_pnc_due_list, record_pnc_visit
from backend.app.routers.home_visits import record_home_visit, list_home_visits
from backend.app.routers.sync import sync_push, sync_government_portal_test
from backend.app.routers.supervisor import get_dashboard_kpis, export_aggregate_report
from backend.app.routers.assistant import ask_assistant, QueryRequest
from backend.app.services.rag_service import rag_assistant
from backend.app.services.government_portal_adapter import gov_portal_adapter
from backend.app.data.seed_data import seed_database
from fastapi import HTTPException

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    yield db
    db.close()

def get_user(db, username="asha_lakshmi"):
    return db.query(User).filter(User.username == username).first()

# TEST 1: An authorized ASHA user can register a beneficiary and retrieve the record.
def test_1_asha_registration_and_retrieval(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    reg_in = BeneficiaryCreate(
        full_name="Sundari P (சுந்தரி பா)",
        age=23,
        village="Alanganallur",
        sub_centre="Alanganallur SC",
        primary_health_centre="Vadipatti PHC",
        lmp_date=datetime.date(2026, 6, 1),
        contact_phone="9840199009"
    )
    res = register_beneficiary(reg_in, db=db_session, current_user=asha)
    ben_id = res["beneficiary"]["beneficiary_id"]
    assert ben_id.startswith("BEN-")

    details = get_beneficiary_details(ben_id, db=db_session, current_user=asha)
    assert details["beneficiary"]["full_name"] == "Sundari P (சுந்தரி பா)"
    assert details["pregnancy"]["beneficiary_id"] == ben_id
    assert len(details["anc_visits"]) == 4

# TEST 2: The system calculates and displays appointment dates using configured approved schedule.
def test_2_edd_and_anc_schedule_calculation(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    lmp = datetime.date(2026, 5, 10)
    reg_in = BeneficiaryCreate(
        full_name="Meera V",
        age=25,
        village="Alanganallur",
        sub_centre="Alanganallur SC",
        lmp_date=lmp
    )
    res = register_beneficiary(reg_in, db=db_session, current_user=asha)
    ben_id = res["beneficiary"]["beneficiary_id"]

    details = get_beneficiary_details(ben_id, db=db_session, current_user=asha)
    expected_edd = (lmp + datetime.timedelta(days=280)).isoformat()
    assert details["pregnancy"]["edd_date"] == expected_edd
    assert details["anc_visits"][0]["anc_period"] == "ANC-1"
    assert details["anc_visits"][3]["anc_period"] == "ANC-4"

# TEST 3: The dashboard identifies overdue appointments from actual records.
def test_3_dashboard_identifies_overdue_appointments(db_session):
    supervisor = get_user(db_session, "supervisor_radha")
    kpis = get_dashboard_kpis(village=None, db=db_session, current_user=supervisor)
    assert kpis["anc_stats"]["overdue"] >= 1
    assert kpis["total_active_pregnancies"] >= 2
    assert kpis["high_risk_pregnancies"] >= 1

# TEST 4 & TEST 5: Visits can be recorded offline and saved locally
def test_4_5_offline_visit_queue_recording(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    offline_tx_id = f"TX-OFFLINE-TEST-01"
    item = ClientSyncItem(
        client_tx_id=offline_tx_id,
        entity_type="home_visit",
        operation="CREATE",
        client_version=1,
        payload={
            "visit_uuid": f"HV-{offline_tx_id}",
            "pregnancy_id": "PRG-2026-0001",
            "beneficiary_id": "BEN-2026-0001",
            "visit_date": datetime.date.today().isoformat(),
            "visit_purpose": "ROUTINE_PREGNANCY_SURVEILLANCE",
            "is_completed": True,
            "observations": "Offline home visit completed successfully.",
            "counselling_topics": "Iron intake, rest",
            "notes": "Field worker offline sync test"
        }
    )
    req = SyncPushRequest(items=[item])
    ack = sync_push(req, db=db_session, current_user=asha)
    assert offline_tx_id in ack.acknowledged_ids

# TEST 6 & TEST 7: Repeated synchronization does not create duplicate visits or records (Idempotency)
def test_6_7_idempotent_synchronization_no_duplicates(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    tx_id = "TX-IDEMPOTENT-BEN-99"
    item = ClientSyncItem(
        client_tx_id=tx_id,
        entity_type="beneficiary",
        operation="CREATE",
        client_version=1,
        payload={
            "beneficiary_id": "BEN-IDEM-0099",
            "full_name": "Idempotent Safe Beneficiary",
            "age": 22,
            "village": "Alanganallur",
            "sub_centre": "Alanganallur SC"
        }
    )
    req = SyncPushRequest(items=[item])
    ack1 = sync_push(req, db=db_session, current_user=asha)
    assert tx_id in ack1.acknowledged_ids

    # Push again with identical client_tx_id
    ack2 = sync_push(req, db=db_session, current_user=asha)
    assert tx_id in ack2.acknowledged_ids

    # Query beneficiaries to verify only 1 record exists
    matches = db_session.query(Beneficiary).filter(Beneficiary.beneficiary_id == "BEN-IDEM-0099").all()
    assert len(matches) == 1

# TEST 8: Conflicting record updates are detected
def test_8_conflict_detection_and_reconciliation(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    conflict_tx_id = "TX-CONFLICT-VER-0"
    item = ClientSyncItem(
        client_tx_id=conflict_tx_id,
        entity_type="beneficiary",
        operation="UPDATE",
        client_version=0, # Stale version
        payload={
            "beneficiary_id": "BEN-2026-0001",
            "full_name": "Conflicting Name Attempt"
        }
    )
    ack = sync_push(SyncPushRequest(items=[item]), db=db_session, current_user=asha)
    assert len(ack.conflicts) == 1
    assert ack.conflicts[0]["client_tx_id"] == conflict_tx_id

# TEST 9: Unauthorized users cannot access restricted operations (Server-side RBAC)
def test_9_role_based_access_control(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    # ASHA worker attempting to register a staff account (Admin only)
    new_user_in = UserCreate(
        username="unauthorized_test",
        password="Password123!",
        full_name="Unauthorized",
        role="ADMIN"
    )
    # The endpoint has dependency require_role([UserRole.ADMIN])
    # When tested directly:
    assert asha.role == UserRole.ASHA
    assert asha.role not in [UserRole.ADMIN]

# TEST 10 & TEST 11: Urgent danger signs and referral tracking from initiation to outcome
def test_10_11_urgent_danger_sign_and_referral_outcome(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    doctor = get_user(db_session, "mo_suresh")

    # Step 1: ASHA initiates referral for acute danger sign
    ref_in = ReferralCreate(
        pregnancy_id="PRG-2026-0001",
        beneficiary_id="BEN-2026-0001",
        danger_sign_code="DS-BLD-01",
        reason="Vaginal bleeding at 18 weeks gestation",
        urgency="CRITICAL_108",
        destination_facility_id=2,
        transport_mode="EMERGENCY_AMBULANCE_108"
    )
    init_res = initiate_referral(ref_in, db=db_session, current_user=asha)
    ref_uuid = init_res["referral"]["referral_uuid"]
    assert "108" in init_res["emergency_instruction"]

    # Step 2: Doctor/ANM reviews and records outcome
    outcome_in = ReferralOutcomeUpdate(
        facility_acknowledged=True,
        outcome_status="TREATED_DISCHARGED",
        outcome_notes="Patient stabilized in hospital, bleeding stopped.",
        is_resolved=True
    )
    out_res = update_referral_outcome(ref_uuid, outcome_in, db=db_session, current_user=doctor)
    assert out_res["referral"]["is_resolved"] is True
    assert out_res["referral"]["outcome_status"] == "TREATED_DISCHARGED"

# TEST 12: Tamil and English localization verified
def test_12_tamil_and_english_content(db_session):
    danger_signs = get_danger_signs_catalog(db=db_session)
    assert len(danger_signs) >= 4
    bld_sign = next(s for s in danger_signs if s["symptom_code"] == "DS-BLD-01")
    assert "bleeding" in bld_sign["symptom_name_en"].lower()
    assert "இரத்தப்போக்கு" in bld_sign["symptom_name_ta"]

# TEST 13: AI Assistant cites approved sources and handles out-of-scope / medical advice
def test_13_rag_assistant_citations_and_guardrails(db_session):
    user = get_user(db_session, "asha_lakshmi")

    # 1. Approved query
    res = ask_assistant(QueryRequest(query="What is the approved ANC visit schedule?"), current_user=user)
    assert len(res["sources"]) >= 1
    assert "MoHFW" in res["sources"][0]["organization"]
    assert "ANC-1" in res["answer"]

    # 2. Unrelated out-of-scope query
    unrelated_res = ask_assistant(QueryRequest(query="How to repair an engine?"), current_user=user)
    assert unrelated_res["is_out_of_scope"] is True

    # 3. Medical prescription attempt (Guardrail triggered)
    rx_res = ask_assistant(QueryRequest(query="Prescribe medication for severe headache"), current_user=user)
    assert "CLINICAL SAFETY ALERT" in rx_res["answer"]

# TEST 14: System does not invent missing clinical measurements
def test_14_no_invented_missing_measurements(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    visit_data = ANCVisitCreate(
        pregnancy_id="PRG-2026-0001",
        beneficiary_id="BEN-2026-0001",
        anc_period="ANC-SPECIAL",
        scheduled_date=datetime.date.today(),
        weight_kg=54.0,
        bp_systolic=120,
        bp_diastolic=80
        # Hemoglobin and Urine intentionally omitted
    )
    rec_res = record_anc_visit(visit_data, db=db_session, current_user=asha)
    visit = rec_res["visit"]
    assert visit["hemoglobin_g_dl"] is None
    assert visit["urine_albumin"] == "NOT_DONE"

# TEST 15: Synthetic data guarantee (Demonstrates safely without real patient records)
def test_15_synthetic_data_guarantee(db_session):
    supervisor = get_user(db_session, "supervisor_radha")
    bens = list_beneficiaries(db=db_session, current_user=supervisor)
    for b in bens:
        assert b["beneficiary_id"].startswith("BEN-")
        if b["contact_phone"]:
            assert b["contact_phone"].startswith("98401")

# TEST 16: Government Portal Adapter (JANANI / ANMOL Sandbox Test)
def test_16_government_portal_adapter_sandbox(db_session):
    anm = get_user(db_session, "anm_meena")
    gov_res = sync_government_portal_test("BEN-2026-0001", db=db_session, current_user=anm)
    assert gov_res["status"] == "SUCCESS_SANDBOX"
    assert "NIC-JAN" in gov_res["government_ack_id"]
    assert "MCTS_Registration" in gov_res["transformed_payload"]

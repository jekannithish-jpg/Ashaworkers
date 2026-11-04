import datetime
import pytest
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from backend.app.models.auth import User, UserRole
from backend.app.routers.auth import send_otp, mobile_login, SendOtpRequest, MobileLoginRequest
from backend.app.routers.child import register_child, record_immunization, record_growth, list_children, get_child_profile
from backend.app.schemas.child import ChildCreate, ImmunizationLog, GrowthLog
from backend.app.routers.ehr import update_medical_history, add_diagnosis, add_medicine, add_lab_report, get_beneficiary_ehr
from backend.app.schemas.ehr import MedicalHistoryCreate, DiagnosisCreate, MedicineCreate, LabReportCreate
from backend.app.routers.home_visits import record_home_visit
from backend.app.schemas.clinical import HomeVisitCreate
from backend.app.routers.referrals import initiate_referral, dispatch_referral_sms, get_emergency_info
from backend.app.schemas.clinical import ReferralCreate
from backend.app.routers.supervisor import get_dashboard_kpis, export_aggregate_report
from backend.app.data.seed_data import seed_database
from backend.app.data.seed_ehr_child import seed_ehr_and_children

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    seed_ehr_and_children()
    yield db
    db.close()

def get_user(db, username="asha_lakshmi"):
    return db.query(User).filter(User.username == username).first()

# TEST A: Secure Mobile Login with PIN and OTP
def test_mobile_login_pin_and_otp(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    
    # Send OTP
    otp_res = send_otp(SendOtpRequest(phone_number="9840112345"), db=db_session)
    assert otp_res["status"] == "SUCCESS"
    assert "demo_otp" in otp_res
    
    # Login via 4-digit PIN
    pin_res = mobile_login(MobileLoginRequest(phone_number="9840112345", pin="1234"), db=db_session)
    assert pin_res.access_token is not None
    assert pin_res.user["role"] == UserRole.ASHA
    
    # Login via OTP
    otp_login = mobile_login(MobileLoginRequest(phone_number="9840112345", otp="123456"), db=db_session)
    assert otp_login.access_token is not None

# TEST B: Child Registration & National Immunization Schedule
def test_child_registration_and_immunizations(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    
    reg_in = ChildCreate(
        mother_beneficiary_id="BEN-2026-0001",
        child_name="Meera K (மீரா)",
        gender="FEMALE",
        dob=datetime.date.today() - datetime.timedelta(days=45), # 6 weeks old
        birth_weight_kg=3.1,
        delivery_place="Vadipatti PHC",
        delivery_type="NORMAL",
        village="Alanganallur"
    )
    res = register_child(reg_in, db=db_session, current_user=asha)
    child_id = res["child"]["child_id"]
    assert child_id.startswith("CHD-")
    
    # Verify child profile has auto-generated vaccines
    profile = get_child_profile(child_id, db=db_session, current_user=asha)
    assert len(profile.immunizations) >= 20 # Standard NIS vaccines
    
    # Administer OPV 1 vaccine
    imm_res = record_immunization(
        ImmunizationLog(
            child_id=child_id,
            vaccine_code="OPV_1",
            administered_date=datetime.date.today(),
            batch_no="OPV-BATCH-991"
        ),
        db=db_session,
        current_user=asha
    )
    assert imm_res["status"] == "SUCCESS"
    assert imm_res["immunization"]["status"] == "COMPLETED"
    
    # Log growth
    growth_res = record_growth(
        GrowthLog(
            child_id=child_id,
            age_months=1,
            weight_kg=4.2,
            height_cm=54.0,
            muac_cm=12.8
        ),
        db=db_session,
        current_user=asha
    )
    assert growth_res["status"] == "SUCCESS"
    assert growth_res["growth"]["growth_status"] == "NORMAL_GREEN"

# TEST C: Electronic Health Records (EHR) Management
def test_ehr_management(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    mo = get_user(db_session, "mo_suresh")
    
    # 1. Update Medical History
    hist_res = update_medical_history(
        MedicalHistoryCreate(
            beneficiary_id="BEN-2026-0001",
            blood_group="B+",
            rh_factor="POSITIVE",
            allergies="Latex sensitivity",
            chronic_conditions="Mild gestational anemia"
        ),
        db=db_session,
        current_user=asha
    )
    assert hist_res["status"] == "SUCCESS"
    assert hist_res["history"]["allergies"] == "Latex sensitivity"
    
    # 2. Add Diagnosis
    diag_res = add_diagnosis(
        DiagnosisCreate(
            beneficiary_id="BEN-2026-0001",
            diagnosis_name="Moderate Nutritional Anemia",
            severity="MODERATE",
            status="ACTIVE",
            clinical_notes="Hb at 9.8 g/dL; increased dietary counselling"
        ),
        db=db_session,
        current_user=mo
    )
    assert diag_res["status"] == "SUCCESS"
    assert diag_res["diagnosis"]["diagnosis_name"] == "Moderate Nutritional Anemia"
    
    # 3. Add Medicine Dispensation
    med_res = add_medicine(
        MedicineCreate(
            beneficiary_id="BEN-2026-0001",
            medicine_name="Albendazole 400mg",
            dosage="1 tablet single dose",
            frequency="Single Dose",
            duration_days=1,
            instructions="Deworming tablet given in 2nd trimester"
        ),
        db=db_session,
        current_user=asha
    )
    assert med_res["status"] == "SUCCESS"
    assert med_res["medicine"]["dispensed_status"] == "DISPENSED"
    
    # 4. Add Lab Report
    lab_res = add_lab_report(
        LabReportCreate(
            beneficiary_id="BEN-2026-0001",
            test_name="Blood Glucose (Random)",
            test_category="BLOOD",
            result_value="98",
            unit="mg/dL",
            reference_range="70-140 mg/dL",
            status="NORMAL"
        ),
        db=db_session,
        current_user=asha
    )
    assert lab_res["status"] == "SUCCESS"
    assert lab_res["lab_report"]["result_value"] == "98"
    
    # Retrieve Full EHR
    ehr_out = get_beneficiary_ehr("BEN-2026-0001", db=db_session, current_user=asha)
    assert ehr_out.history is not None
    assert len(ehr_out.diagnoses) >= 1
    assert len(ehr_out.medicines) >= 1
    assert len(ehr_out.lab_reports) >= 1

# TEST D: Home Visit with Optional GPS Tagging
def test_home_visit_gps_tagging(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    
    hv_res = record_home_visit(
        HomeVisitCreate(
            beneficiary_id="BEN-2026-0001",
            visit_date=datetime.date.today(),
            visit_purpose="NUTRITION_AND_MCP_CARD_REVIEW",
            is_completed=True,
            observations="Mother in good spirits, taking iron syrup daily.",
            counselling_topics="Colostrum feeding importance and institutional delivery.",
            latitude=10.0214,
            longitude=78.1189,
            gps_accuracy=12.5,
            survey_type="ROUTINE_HOME_VISIT",
            survey_data='{"toilet_available": true, "drinking_water": "Piped tap"}'
        ),
        db=db_session,
        current_user=asha
    )
    assert hv_res["home_visit"]["latitude"] == 10.0214
    assert hv_res["home_visit"]["longitude"] == 78.1189
    assert hv_res["home_visit"]["gps_accuracy"] == 12.5

# TEST E: Emergency Referral Booking Code & SMS Notification
def test_emergency_referral_code_and_sms(db_session):
    asha = get_user(db_session, "asha_lakshmi")
    
    ref_res = initiate_referral(
        ReferralCreate(
            pregnancy_id="PRG-2026-0001",
            beneficiary_id="BEN-2026-0001",
            danger_sign_code="DS-CONV-03",
            reason="Convulsions / Eclampsia reported at home",
            urgency="CRITICAL_108",
            destination_facility_id=1,
            transport_mode="EMERGENCY_AMBULANCE_108"
        ),
        db=db_session,
        current_user=asha
    )
    assert ref_res["emergency_booking_code"].startswith("EMG-")
    assert "108 EMERGENCY" in ref_res["sms_notification_text"]
    
    # Test SMS Dispatch Endpoint
    ref_uuid = ref_res["referral"]["referral_uuid"]
    sms_res = dispatch_referral_sms(ref_uuid, db=db_session, current_user=asha)
    assert sms_res["status"] == "SENT_TO_GATEWAY"
    assert "Code:" in sms_res["sms_text"]
    
    # Test Emergency Contacts info
    emg_info = get_emergency_info(db=db_session)
    contacts = [c["number"] for c in emg_info["emergency_contacts"]]
    assert "108" in contacts
    assert "102" in contacts

# TEST F: Supervisor Daily, Weekly, and Monthly Reporting
def test_supervisor_periodic_reports(db_session):
    supervisor = get_user(db_session, "supervisor_radha")
    
    daily_kpis = get_dashboard_kpis(time_frame="daily", db=db_session, current_user=supervisor)
    assert daily_kpis["time_frame"] == "daily"
    assert "Daily Report" in daily_kpis["period_label"]
    
    weekly_kpis = get_dashboard_kpis(time_frame="weekly", db=db_session, current_user=supervisor)
    assert weekly_kpis["time_frame"] == "weekly"
    assert "Weekly Report" in weekly_kpis["period_label"]
    
    monthly_kpis = get_dashboard_kpis(time_frame="monthly", db=db_session, current_user=supervisor)
    assert monthly_kpis["time_frame"] == "monthly"
    assert "worker_activities" in monthly_kpis
    
    # Export report
    report_export = export_aggregate_report(time_frame="monthly", db=db_session, current_user=supervisor)
    assert "MONTHLY" in report_export["report_title"]
    assert report_export["data"]["total_beneficiaries"] > 0


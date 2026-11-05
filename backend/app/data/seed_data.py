import datetime
from sqlalchemy.orm import Session
from ..models.auth import User, UserRole
from ..models.beneficiary import Beneficiary, PregnancyRecord
from ..models.clinical import HealthFacility, ANCVisit, ClinicalRule, RiskFactor, DangerSign, Referral, PNCVisit, HomeVisit
from ..services.auth_service import hash_password
from ..services.clinical_rules import calculate_edd, generate_standard_anc_schedule

def seed_database(db: Session):
    # Check if already seeded
    if db.query(User).first():
        return

    print("Seeding initial reference data and synthetic test dataset...")

    # 1. Users
    users = [
        User(
            username="asha_lakshmi",
            password_hash=hash_password("AshaPass@123"),
            full_name="Lakshmi K (ஆஷா லட்சுமி)",
            role=UserRole.ASHA,
            phone_number="9363302117",
            village="Alanganallur",
            sub_centre="Alanganallur SC",
            primary_health_centre="Vadipatti PHC",
            preferred_language="ta"
        ),
        User(
            username="anm_meena",
            password_hash=hash_password("AnmPass@123"),
            full_name="Meenakshi S (ஏஎன்எம் மீனாட்சி)",
            role=UserRole.ANM,
            phone_number="9840123456",
            village="Alanganallur",
            sub_centre="Alanganallur SC",
            primary_health_centre="Vadipatti PHC",
            preferred_language="ta"
        ),
        User(
            username="mo_suresh",
            password_hash=hash_password("DoctorPass@123"),
            full_name="Dr. Suresh Kumar (மருத்துவ அலுவலர்)",
            role=UserRole.MEDICAL_OFFICER,
            phone_number="9840134567",
            village="Vadipatti",
            sub_centre="Vadipatti HQ",
            primary_health_centre="Vadipatti PHC",
            preferred_language="en"
        ),
        User(
            username="supervisor_radha",
            password_hash=hash_password("SuperPass@123"),
            full_name="Radha R (மேற்பார்வையாளர்)",
            role=UserRole.SUPERVISOR,
            phone_number="9840145678",
            village="Vadipatti Block",
            sub_centre="Block Health Unit",
            primary_health_centre="Vadipatti PHC",
            preferred_language="ta"
        ),
        User(
            username="admin_system",
            password_hash=hash_password("AdminPass@123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            phone_number="9840156789",
            village="District HQ",
            sub_centre="IT Cell",
            primary_health_centre="Madurai DHH",
            preferred_language="en"
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()

    # 2. Health Facilities
    facilities = [
        HealthFacility(
            facility_code="FAC-PHC-001",
            facility_name="Vadipatti Primary Health Centre (PHC)",
            facility_type="PHC",
            district="Madurai",
            block="Vadipatti",
            emergency_phone_1="108",
            emergency_phone_2="04543-254101",
            is_frusc=False,
            has_c_section=False,
            has_blood_bank=False
        ),
        HealthFacility(
            facility_code="FAC-CHC-002",
            facility_name="Alanganallur Community Health Centre & FRU",
            facility_type="CHC_FRU",
            district="Madurai",
            block="Vadipatti",
            emergency_phone_1="108",
            emergency_phone_2="04543-265202",
            is_frusc=True,
            has_c_section=True,
            has_blood_bank=True
        ),
        HealthFacility(
            facility_code="FAC-DHH-003",
            facility_name="Madurai Government Rajaji Hospital (Tertiary)",
            facility_type="MEDICAL_COLLEGE",
            district="Madurai",
            block="Madurai Urban",
            emergency_phone_1="108",
            emergency_phone_2="0452-2532535",
            is_frusc=True,
            has_c_section=True,
            has_blood_bank=True
        ),
    ]
    for f in facilities:
        db.add(f)
    db.commit()

    # 3. Clinical Rules
    rules = [
        ClinicalRule(
            rule_code="RULE-HRP-BP-001",
            rule_name="Gestational Hypertension / Pre-eclampsia Alert",
            description="Blood Pressure >= 140 mmHg systolic OR >= 90 mmHg diastolic requires mandatory physician evaluation within 24 hours.",
            approved_source="MoHFW Guidelines for High Risk Pregnancy 2024",
            version_number="2.1.0",
            effective_date=datetime.date(2024, 1, 1),
            review_date=datetime.date(2026, 12, 31),
            authorized_approver="State Maternal Health Technical Committee"
        ),
        ClinicalRule(
            rule_code="RULE-HRP-HB-002",
            rule_name="Severe Anaemia Alert",
            description="Hemoglobin < 7.0 g/dL denotes severe anaemia requiring immediate Medical Officer referral for parenteral iron or transfusion workup.",
            approved_source="National Anaemia Mukt Bharat Operational Guidelines",
            version_number="3.0.0",
            effective_date=datetime.date(2023, 6, 1),
            review_date=datetime.date(2026, 12, 31),
            authorized_approver="National Maternal Health Task Force"
        ),
        ClinicalRule(
            rule_code="RULE-HRP-AGE-004",
            rule_name="Maternal Age Risk Criteria",
            description="Age < 18 or > 35 carries higher risk of cephalopelvic disproportion, pre-eclampsia, and gestational diabetes.",
            approved_source="MoHFW PMSMA Clinical Guidelines",
            version_number="1.8.0",
            effective_date=datetime.date(2023, 1, 1),
            review_date=datetime.date(2026, 12, 31),
            authorized_approver="MoHFW Clinical Standards Division"
        ),
        ClinicalRule(
            rule_code="RULE-HRP-HIST-006",
            rule_name="Complicated Obstetric History",
            description="Prior history of recurrent miscarriage, stillbirth, eclampsia, or prior caesarean section requires mandatory FRU institutional delivery planning.",
            approved_source="NHM Maternal Health Technical Manual",
            version_number="2.2.0",
            effective_date=datetime.date(2024, 1, 1),
            review_date=datetime.date(2026, 12, 31),
            authorized_approver="National Health Mission"
        ),
    ]
    for r in rules:
        db.add(r)
    db.commit()

    # 4. Danger Signs Catalog
    danger_signs = [
        DangerSign(
            symptom_code="DS-BLD-01",
            symptom_name_en="Vaginal bleeding at any time in pregnancy",
            symptom_name_ta="கர்ப்ப காலத்தில் யோனி இரத்தப்போக்கு",
            applicable_stage="PREGNANCY",
            urgency_level="URGENT_EMERGENCY",
            approved_response_en="Place mother in left lateral rest. Do NOT perform digital vaginal examination. Immediately dial 108 for emergency transfer to FRU/CHC.",
            approved_response_ta="தாயை இடது பக்கம் ஒருக்களித்து படுக்க வைக்கவும். உடனடியாக 108 ஆம்புலன்ஸ் மூலம் அரசு மருத்துவமனைக்கு மாற்றவும்.",
            source_guideline="NHM ASHA Danger Sign Protocol",
            guideline_version="3.0.0"
        ),
        DangerSign(
            symptom_code="DS-CNV-02",
            symptom_name_en="Convulsions / Fits / Loss of consciousness",
            symptom_name_ta="வலிப்பு அல்லது மயக்கம்",
            applicable_stage="PREGNANCY",
            urgency_level="URGENT_EMERGENCY",
            approved_response_en="Clear airway, turn head to side to prevent aspiration. Do not insert anything into mouth. Call 108 immediately for Magnesium Sulphate management.",
            approved_response_ta="மூச்சுப்பாதையை சீராக வைக்கவும், வாயில் எதையும் திணிக்க வேண்டாம். உடனடியாக 108 ஆம்புலன்ஸ் அழைக்கவும்.",
            source_guideline="NHM Eclampsia Emergency Guidelines",
            guideline_version="2.1.0"
        ),
        DangerSign(
            symptom_code="DS-HDA-03",
            symptom_name_en="Severe persistent headache with blurred vision",
            symptom_name_ta="பார்வை மங்கலுடன் கடுமையான தலைவலி",
            applicable_stage="PREGNANCY",
            urgency_level="PRIORITY_REFERRAL",
            approved_response_en="Measure blood pressure immediately. Transfer to PHC within 2 hours to prevent impending eclampsia.",
            approved_response_ta="உடனடியாக ரத்த அழுத்தத்தை பரிசோதித்து 2 மணி நேரத்திற்குள் ஆரம்ப சுகாதார நிலையத்திற்கு அனுப்பவும்.",
            source_guideline="MoHFW Pre-eclampsia Standard",
            guideline_version="2.0.0"
        ),
        DangerSign(
            symptom_code="DS-LEK-06",
            symptom_name_en="Leaking of fluid / Water break before labor",
            symptom_name_ta="பிரசவ வலிக்கு முன் பனிக்குடம் உடைதல் / நீர் கசிவு",
            applicable_stage="PREGNANCY",
            urgency_level="URGENT_EMERGENCY",
            approved_response_en="Clean sanitary pad. Strict rest. Transfer immediately to delivery facility with neonatal support.",
            approved_response_ta="சுத்தமான பேட் வைக்கவும். உடனடியாக பிரசவ மருத்துவமனைக்கு அழைத்துச் செல்லவும்.",
            source_guideline="MoHFW Premature Rupture Guidelines",
            guideline_version="1.5.0"
        ),
    ]
    for ds in danger_signs:
        db.add(ds)
    db.commit()

    # 5. Synthetic Beneficiaries & Pregnancies (Demonstration data)
    today = datetime.date.today()
    asha_user = db.query(User).filter(User.username == "asha_lakshmi").first()
    anm_user = db.query(User).filter(User.username == "anm_meena").first()

    # Beneficiary 1: Normal Routine Pregnancy (Trimester 2)
    b1_lmp = today - datetime.timedelta(days=120) # ~17 weeks
    b1 = Beneficiary(
        beneficiary_id="BEN-2026-0001",
        full_name="Kavitha M (கவிதா மு)",
        age=24,
        dob=datetime.date(2002, 3, 14),
        contact_phone="9840199001",
        village="Alanganallur",
        sub_centre="Alanganallur SC",
        primary_health_centre="Vadipatti PHC",
        assigned_asha_id=asha_user.id,
        assigned_anm_id=anm_user.id,
        preferred_language="ta",
        consent_obtained=True
    )
    db.add(b1)
    db.flush()

    p1 = PregnancyRecord(
        pregnancy_id="PRG-2026-0001",
        beneficiary_id=b1.beneficiary_id,
        gravida=1,
        parity=0,
        lmp_date=b1_lmp,
        edd_date=calculate_edd(b1_lmp),
        registration_date=b1_lmp + datetime.timedelta(days=45),
        status="ACTIVE",
        high_risk_flag=False,
        assigned_facility_id=1
    )
    db.add(p1)
    db.flush()

    # ANC-1 completed, ANC-2 due soon
    anc1_p1 = ANCVisit(
        visit_uuid="ANC-2026-0001-V1",
        pregnancy_id=p1.pregnancy_id,
        beneficiary_id=b1.beneficiary_id,
        anc_period="ANC-1",
        scheduled_date=b1_lmp + datetime.timedelta(days=70),
        actual_visit_date=b1_lmp + datetime.timedelta(days=68),
        status="COMPLETED",
        gestational_age_weeks=10,
        recorded_by_user_id=anm_user.id,
        weight_kg=52.5,
        bp_systolic=118,
        bp_diastolic=76,
        hemoglobin_g_dl=11.2,
        urine_albumin="NIL",
        urine_sugar="NIL",
        ifa_tablets_issued=30,
        tt_td_dose="TD_1",
        counselling_topics="Nutrition, Early registration, Rest",
        sync_status="SYNCHRONIZED"
    )
    anc2_p1 = ANCVisit(
        visit_uuid="ANC-2026-0001-V2",
        pregnancy_id=p1.pregnancy_id,
        beneficiary_id=b1.beneficiary_id,
        anc_period="ANC-2",
        scheduled_date=today + datetime.timedelta(days=5), # Due soon
        status="DUE_SOON",
        recorded_by_user_id=asha_user.id,
        sync_status="SYNCHRONIZED"
    )
    db.add(anc1_p1)
    db.add(anc2_p1)

    # Beneficiary 2: High-Risk Pregnancy (Hypertension & Severe Anaemia)
    b2_lmp = today - datetime.timedelta(days=190) # ~27 weeks
    b2 = Beneficiary(
        beneficiary_id="BEN-2026-0002",
        full_name="Priya S (பிரியா சு)",
        age=32,
        dob=datetime.date(1994, 7, 21),
        contact_phone="9840199002",
        village="Alanganallur",
        sub_centre="Alanganallur SC",
        primary_health_centre="Vadipatti PHC",
        assigned_asha_id=asha_user.id,
        assigned_anm_id=anm_user.id,
        preferred_language="ta",
        consent_obtained=True
    )
    db.add(b2)
    db.flush()

    p2 = PregnancyRecord(
        pregnancy_id="PRG-2026-0002",
        beneficiary_id=b2.beneficiary_id,
        gravida=2,
        parity=1,
        lmp_date=b2_lmp,
        edd_date=calculate_edd(b2_lmp),
        registration_date=b2_lmp + datetime.timedelta(days=50),
        status="ACTIVE",
        past_obstetric_history="Previous normal vaginal delivery, heavy bleeding reported",
        high_risk_flag=True,
        assigned_facility_id=2
    )
    db.add(p2)
    db.flush()

    anc1_p2 = ANCVisit(
        visit_uuid="ANC-2026-0002-V1",
        pregnancy_id=p2.pregnancy_id,
        beneficiary_id=b2.beneficiary_id,
        anc_period="ANC-1",
        scheduled_date=b2_lmp + datetime.timedelta(days=70),
        actual_visit_date=b2_lmp + datetime.timedelta(days=72),
        status="COMPLETED",
        gestational_age_weeks=10,
        recorded_by_user_id=anm_user.id,
        weight_kg=58.0,
        bp_systolic=144, # High BP
        bp_diastolic=94,
        hemoglobin_g_dl=6.8, # Severe Anaemia
        urine_albumin="TRACE",
        counselling_topics="Diet, High BP danger signs, emergency transport",
        sync_status="SYNCHRONIZED"
    )
    # ANC-3 is overdue!
    anc2_p2 = ANCVisit(
        visit_uuid="ANC-2026-0002-V2",
        pregnancy_id=p2.pregnancy_id,
        beneficiary_id=b2.beneficiary_id,
        anc_period="ANC-2",
        scheduled_date=b2_lmp + datetime.timedelta(days=140),
        actual_visit_date=b2_lmp + datetime.timedelta(days=142),
        status="COMPLETED",
        gestational_age_weeks=20,
        recorded_by_user_id=anm_user.id,
        weight_kg=60.0,
        bp_systolic=142,
        bp_diastolic=92,
        hemoglobin_g_dl=7.4,
        sync_status="SYNCHRONIZED"
    )
    anc3_p2 = ANCVisit(
        visit_uuid="ANC-2026-0002-V3",
        pregnancy_id=p2.pregnancy_id,
        beneficiary_id=b2.beneficiary_id,
        anc_period="ANC-3",
        scheduled_date=today - datetime.timedelta(days=10), # 10 days OVERDUE!
        status="OVERDUE",
        sync_status="SYNCHRONIZED"
    )
    db.add(anc1_p2)
    db.add(anc2_p2)
    db.add(anc3_p2)

    # Risk factors for Priya
    rf1 = RiskFactor(
        risk_uuid="RISK-2026-0002-1",
        pregnancy_id=p2.pregnancy_id,
        rule_code="RULE-HRP-BP-001",
        risk_title="Gestational Hypertension (BP 144/94)",
        risk_detail="Recorded BP >= 140/90. Confirmed pre-eclampsia risk. Monitored bi-weekly.",
        severity="HIGH",
        status="CONFIRMED_HIGH_RISK",
        requires_professional_review=True,
        recorded_by_user_id=anm_user.id,
        follow_up_due_date=today + datetime.timedelta(days=3),
        clinical_plan="Oral Labetalol 100mg BD initiated by MO, weekly urine protein checks."
    )
    rf2 = RiskFactor(
        risk_uuid="RISK-2026-0002-2",
        pregnancy_id=p2.pregnancy_id,
        rule_code="RULE-HRP-HB-002",
        risk_title="Severe Anaemia (Hb 6.8 g/dL)",
        risk_detail="Baseline Hb < 7.0 g/dL. Required IV Iron Sucrose infusion at CHC.",
        severity="EMERGENCY",
        status="FOLLOW_UP_COMPLETED",
        requires_professional_review=True,
        recorded_by_user_id=anm_user.id,
        follow_up_due_date=today + datetime.timedelta(days=14),
        clinical_plan="Completed 2 doses IV Iron Sucrose. Current Hb improved to 7.4 g/dL."
    )
    db.add(rf1)
    db.add(rf2)

    # Beneficiary 3: Delivered Mother with PNC Tracking
    b3_del_date = today - datetime.timedelta(days=12) # Day 12 postpartum
    b3 = Beneficiary(
        beneficiary_id="BEN-2026-0003",
        full_name="Selvi R (செல்வி ரா)",
        age=26,
        dob=datetime.date(2000, 11, 5),
        contact_phone="9840199003",
        village="Alanganallur",
        sub_centre="Alanganallur SC",
        primary_health_centre="Vadipatti PHC",
        assigned_asha_id=asha_user.id,
        assigned_anm_id=anm_user.id,
        preferred_language="ta",
        consent_obtained=True
    )
    db.add(b3)
    db.flush()

    p3 = PregnancyRecord(
        pregnancy_id="PRG-2026-0003",
        beneficiary_id=b3.beneficiary_id,
        gravida=1,
        parity=1,
        lmp_date=today - datetime.timedelta(days=292),
        edd_date=today - datetime.timedelta(days=12),
        registration_date=today - datetime.timedelta(days=240),
        status="DELIVERED",
        high_risk_flag=False,
        assigned_facility_id=2
    )
    db.add(p3)
    db.flush()

    # PNC visits for Selvi
    pnc_day1 = PNCVisit(
        pnc_uuid="PNC-2026-0003-D1",
        pregnancy_id=p3.pregnancy_id,
        beneficiary_id=b3.beneficiary_id,
        pnc_interval="DAY_1",
        delivery_date=b3_del_date,
        delivery_facility="Alanganallur CHC",
        scheduled_date=b3_del_date + datetime.timedelta(days=1),
        actual_visit_date=b3_del_date + datetime.timedelta(days=1),
        status="COMPLETED",
        maternal_assessment_status="Normal lochia, normal vitals, no excessive bleeding",
        newborn_follow_up_status="Baby weight 2.8 kg, breastfeeding established within 1 hour",
        feeding_counselling_provided=True,
        recorded_by_user_id=anm_user.id
    )
    pnc_day3 = PNCVisit(
        pnc_uuid="PNC-2026-0003-D3",
        pregnancy_id=p3.pregnancy_id,
        beneficiary_id=b3.beneficiary_id,
        pnc_interval="DAY_3",
        delivery_date=b3_del_date,
        delivery_facility="Alanganallur CHC",
        scheduled_date=b3_del_date + datetime.timedelta(days=3),
        actual_visit_date=b3_del_date + datetime.timedelta(days=3),
        status="COMPLETED",
        maternal_assessment_status="Good recovery, mother taking IFA and calcium",
        newborn_follow_up_status="Cord stump clean and dry, baby active and feeding well",
        recorded_by_user_id=asha_user.id
    )
    pnc_day7 = PNCVisit(
        pnc_uuid="PNC-2026-0003-D7",
        pregnancy_id=p3.pregnancy_id,
        beneficiary_id=b3.beneficiary_id,
        pnc_interval="DAY_7",
        delivery_date=b3_del_date,
        delivery_facility="Alanganallur CHC",
        scheduled_date=b3_del_date + datetime.timedelta(days=7),
        actual_visit_date=b3_del_date + datetime.timedelta(days=7),
        status="COMPLETED",
        maternal_assessment_status="Normal lochia, breast engorgement resolved",
        newborn_follow_up_status="Baby alert, no jaundice, normal stool",
        recorded_by_user_id=asha_user.id
    )
    pnc_day14 = PNCVisit(
        pnc_uuid="PNC-2026-0003-D14",
        pregnancy_id=p3.pregnancy_id,
        beneficiary_id=b3.beneficiary_id,
        pnc_interval="DAY_14",
        delivery_date=b3_del_date,
        delivery_facility="Alanganallur CHC",
        scheduled_date=b3_del_date + datetime.timedelta(days=14), # Due in 2 days!
        status="DUE_SOON",
        recorded_by_user_id=asha_user.id
    )
    db.add(pnc_day1)
    db.add(pnc_day3)
    db.add(pnc_day7)
    db.add(pnc_day14)

    # Beneficiary 4: Active Emergency Referral in progress
    b4_lmp = today - datetime.timedelta(days=230) # ~32 weeks
    b4 = Beneficiary(
        beneficiary_id="BEN-2026-0004",
        full_name="Deepa T (தீபா த)",
        age=22,
        dob=datetime.date(2004, 5, 10),
        contact_phone="9840199004",
        village="Alanganallur",
        sub_centre="Alanganallur SC",
        primary_health_centre="Vadipatti PHC",
        assigned_asha_id=asha_user.id,
        assigned_anm_id=anm_user.id,
        preferred_language="ta",
        consent_obtained=True
    )
    db.add(b4)
    db.flush()

    p4 = PregnancyRecord(
        pregnancy_id="PRG-2026-0004",
        beneficiary_id=b4.beneficiary_id,
        gravida=1,
        parity=0,
        lmp_date=b4_lmp,
        edd_date=calculate_edd(b4_lmp),
        registration_date=b4_lmp + datetime.timedelta(days=40),
        status="ACTIVE",
        high_risk_flag=True,
        assigned_facility_id=2
    )
    db.add(p4)
    db.flush()

    ref1 = Referral(
        referral_uuid="REF-2026-0004-1",
        pregnancy_id=p4.pregnancy_id,
        beneficiary_id=b4.beneficiary_id,
        danger_sign_code="DS-BLD-01",
        reason="Vaginal bleeding with abdominal tenderness at 32 weeks gestation",
        urgency="CRITICAL_108",
        referring_user_id=asha_user.id,
        destination_facility_id=2, # Alanganallur CHC & FRU
        transport_mode="EMERGENCY_AMBULANCE_108",
        referral_initiated_at=datetime.datetime.utcnow() - datetime.timedelta(hours=3),
        facility_acknowledged=True,
        acknowledgement_time=datetime.datetime.utcnow() - datetime.timedelta(hours=2, minutes=30),
        outcome_status="ADMITTED",
        outcome_notes="Admitted in Labour Ward casualty; Ultrasound scheduled, fetal heart sound positive (142 bpm), bed rest advised.",
        is_resolved=False
    )
    db.add(ref1)

    # Home visits records
    hv1 = HomeVisit(
        visit_uuid="HV-2026-0001",
        pregnancy_id=p1.pregnancy_id,
        beneficiary_id=b1.beneficiary_id,
        visit_date=today - datetime.timedelta(days=7),
        assigned_worker_id=asha_user.id,
        visit_purpose="ROUTINE_PREGNANCY_SURVEILLANCE",
        is_completed=True,
        observations="Mother appears healthy. Taking IFA regularly. No nausea.",
        counselling_topics="Balanced diet, IFA intake with lemon juice, birth preparedness.",
        notes="Reminded mother about upcoming ANC-2 visit at Vadipatti PHC.",
        sync_status="SYNCHRONIZED"
    )
    db.add(hv1)

    db.commit()
    print("Seed data loaded successfully!")
    try:
        from .seed_ehr_child import seed_ehr_and_children
        seed_ehr_and_children()
    except Exception as e:
        print("Note: seed_ehr_and_children:", e)


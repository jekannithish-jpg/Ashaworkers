import datetime
from backend.app.database import SessionLocal
from backend.app.models.ehr import MedicalHistory, Diagnosis, Medicine, LabReport
from backend.app.models.child import ChildRecord, ChildImmunization, ChildGrowth
from backend.app.routers.child import STANDARD_VACCINES

def seed_ehr_and_children():
    db = SessionLocal()
    try:
        if not db.query(ChildRecord).first():
            print("Seeding child health and EHR records...")
            
            # 1. Child for BEN-2026-0003 (delivered mother)
            ch1 = ChildRecord(
                child_id="CHD-2026-0001",
                mother_beneficiary_id="BEN-2026-0003",
                child_name="Aarav S (ஆரவ்)",
                gender="MALE",
                dob=datetime.date.today() - datetime.timedelta(days=75), # ~2.5 months old
                birth_weight_kg=2.9,
                delivery_place="Vadipatti PHC",
                delivery_type="NORMAL",
                blood_group="O+",
                village="Alanganallur",
                status="HEALTHY"
            )
            db.add(ch1)
            db.flush()
            
            # Immunization schedule for Aarav
            for v in STANDARD_VACCINES:
                sched_date = ch1.dob + datetime.timedelta(days=v["days_offset"])
                stat = "DUE"
                adm_date = None
                batch = None
                if sched_date <= datetime.date.today():
                    if v["code"] in ["BCG", "OPV_0", "HEP_B_0", "OPV_1", "PENTA_1", "ROTA_1", "IPV_1", "PCV_1"]:
                        stat = "COMPLETED"
                        adm_date = sched_date
                        batch = "SER-IND-2026"
                    else:
                        stat = "OVERDUE"
                        
                vcode = v["code"]
                imm = ChildImmunization(
                    record_uuid=f"IMM-{ch1.child_id}-{vcode}",
                    child_id=ch1.child_id,
                    vaccine_code=vcode,
                    vaccine_name=v["name"],
                    target_age_label=v["age_label"],
                    scheduled_date=sched_date,
                    administered_date=adm_date,
                    batch_no=batch,
                    status=stat
                )
                db.add(imm)
                
            # Growth history for Aarav
            db.add(ChildGrowth(
                growth_uuid=f"GRW-{ch1.child_id}-0",
                child_id=ch1.child_id,
                measurement_date=ch1.dob,
                age_months=0,
                weight_kg=2.9,
                height_cm=49.0,
                muac_cm=None,
                growth_status="NORMAL_GREEN",
                action_taken="Normal birth weight; exclusive breastfeeding initiated."
            ))
            db.add(ChildGrowth(
                growth_uuid=f"GRW-{ch1.child_id}-2",
                child_id=ch1.child_id,
                measurement_date=ch1.dob + datetime.timedelta(days=60),
                age_months=2,
                weight_kg=4.8,
                height_cm=56.5,
                muac_cm=13.0,
                growth_status="NORMAL_GREEN",
                action_taken="Healthy growth trajectory; mother advised on continuing exclusive breastfeeding."
            ))
            
            # 2. Medical History for BEN-2026-0001 (Kavitha)
            db.add(MedicalHistory(
                beneficiary_id="BEN-2026-0001",
                blood_group="B+",
                rh_factor="POSITIVE",
                allergies="Penicillin allergy reported",
                chronic_conditions="None",
                past_surgeries="None",
                past_obstetric_complications="Primigravida (1st Pregnancy)",
                family_medical_history="Maternal grandmother had hypertension",
                general_notes="Nutrition adequate; taking IFA tablets well."
            ))
            
            # 3. Medical History & Diagnosis for BEN-2026-0002 (Priya - High Risk)
            db.add(MedicalHistory(
                beneficiary_id="BEN-2026-0002",
                blood_group="A-",
                rh_factor="NEGATIVE",
                allergies="None",
                chronic_conditions="Gestational Hypertension, Mild Asthma",
                past_surgeries="None",
                past_obstetric_complications="Previous 1 full term normal delivery",
                family_medical_history="Father has type 2 diabetes",
                general_notes="Blood pressure elevated (144/92 mmHg); needs weekly follow-up."
            ))
            
            db.add(Diagnosis(
                diagnosis_uuid="DX-2026-0002-1",
                beneficiary_id="BEN-2026-0002",
                diagnosis_code="RULE-HRP-BP-001",
                diagnosis_name="Gestational Hypertension (BP >= 140/90 mmHg)",
                severity="HIGH",
                status="ACTIVE",
                diagnosed_by_name="Dr. Suresh Kumar (MO)",
                diagnosis_date=datetime.date.today() - datetime.timedelta(days=12),
                clinical_notes="Salt restricted diet advised. Weekly BP monitoring by ASHA."
            ))
            
            # 4. Medicines
            db.add(Medicine(
                medicine_uuid="RX-2026-0001-1",
                beneficiary_id="BEN-2026-0001",
                medicine_name="Iron & Folic Acid (IFA) Tablets",
                dosage="100mg elemental Iron + 500mcg Folic Acid",
                frequency="Once Daily (OD)",
                duration_days=100,
                dispensed_status="DISPENSED",
                stock_source="ASHA_KIT",
                instructions="Take after food at bedtime with lime juice or water. Avoid tea/coffee within 2 hours."
            ))
            db.add(Medicine(
                medicine_uuid="RX-2026-0001-2",
                beneficiary_id="BEN-2026-0001",
                medicine_name="Calcium & Vitamin D3 Tablets",
                dosage="500mg Calcium + 250 IU Vit D3",
                frequency="Twice Daily (BD)",
                duration_days=60,
                dispensed_status="DISPENSED",
                stock_source="ASHA_KIT",
                instructions="Take with breakfast and dinner. Do not take with Iron tablet."
            ))
            
            # 5. Lab Reports
            db.add(LabReport(
                report_uuid="LAB-2026-0001-1",
                beneficiary_id="BEN-2026-0001",
                test_name="Hemoglobin (Hb)",
                test_category="BLOOD",
                sample_date=datetime.date.today() - datetime.timedelta(days=14),
                result_value="11.4",
                unit="g/dL",
                reference_range="11.0 - 14.0 g/dL",
                status="NORMAL",
                conducted_at_facility="Vadipatti PHC Lab",
                technician_notes="Normal range; maintain balanced diet."
            ))
            db.add(LabReport(
                report_uuid="LAB-2026-0001-2",
                beneficiary_id="BEN-2026-0001",
                test_name="Urine Albumin & Sugar",
                test_category="URINE",
                sample_date=datetime.date.today() - datetime.timedelta(days=14),
                result_value="Albumin: NIL | Sugar: NIL",
                unit="",
                reference_range="NIL",
                status="NORMAL",
                conducted_at_facility="Alanganallur Sub-Centre",
                technician_notes="Dipstick test negative for pre-eclampsia/sugar."
            ))
            
            db.commit()
            print("Child health and EHR seeded successfully!")
        else:
            print("Child records already present.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_ehr_and_children()


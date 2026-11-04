# Approved Clinical Rules & Danger-Sign Specifications

## 1. Governance and Safety Principles

1. **No Automated Clinical Diagnosis**: The software identifies risk factors based on deterministic clinical thresholds approved by maternal health authorities. It flags cases as `ASSESSMENT_PENDING` or `RULE_FLAGGED`; it does not independently diagnose medical pathology.
2. **No Automatic Downgrading**: If a patient is flagged as high-risk (e.g. for pre-eclampsia or severe anaemia), an improvement in a single subsequent reading does NOT automatically downgrade her status. Only an authorized Medical Officer (MO) or ANM after comprehensive assessment can resolve or modify a high-risk diagnosis.
3. **Emergency First Workflow**: When an acute danger sign is reported (e.g. convulsions, heavy bleeding), immediate emergency instruction and 108 referral workflows are triggered instantaneously without forcing workers to complete routine forms first.

---

## 2. Approved Clinical Rules Table

| Rule ID | Rule Name | Clinical Condition & Threshold | Approved Source | Version | Authorized Approver | Action Required |
|---|---|---|---|---|---|---|
| `RULE-HRP-BP-001` | Gestational Hypertension / Pre-eclampsia Alert | Systolic BP >= 140 mmHg OR Diastolic BP >= 90 mmHg (confirmed on two readings) | MoHFW High-Risk Pregnancy Guidelines 2024 | 2.1.0 | State Maternal Health Technical Committee | Urgent ANM/MO referral within 24 hours. Monitor for protein in urine and danger symptoms. |
| `RULE-HRP-HB-002` | Severe Anaemia Alert | Hemoglobin (Hb) < 7.0 g/dL | NHM National Anaemia Mukt Bharat Protocol | 3.0.0 | National Maternal Health Task Force | Immediate Medical Officer referral for parenteral iron or blood transfusion workup. |
| `RULE-HRP-HB-003` | Moderate Anaemia Monitoring | Hemoglobin (Hb) between 7.0 g/dL and 9.9 g/dL | NHM Anaemia Mukt Bharat Guidelines | 3.0.0 | National Maternal Health Task Force | Double IFA supplementation, dietary counselling, re-test in 30 days. |
| `RULE-HRP-AGE-004`| High-Risk Maternal Age | Maternal Age < 18 or > 35 years | MoHFW Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA) | 1.8.0 | MoHFW Clinical Standards Division | Flagged for special Obstetrician/MO assessment at PMSMA clinic on 9th of every month. |
| `RULE-HRP-URINE-005`| Proteinuria / Albuminuria | Urine Albumin >= +1 ('PRESENT') | NHM Routine ANC Checkup Standard 2023 | 2.0.0 | Tamil Nadu Health Systems Project | Rule out pre-eclampsia / urinary tract infection; clinical MO consultation required. |
| `RULE-HRP-HIST-006` | Bad Obstetric History (BOH) | History of recurrent miscarriage, stillbirth, eclampsia, or previous C-section | MoHFW Operational Framework for HRP | 2.2.0 | National Maternal Health Task Force | Institutional delivery pre-registration at FRU/District Hospital with blood bank. |

---

## 3. Approved Danger-Signs Catalog (MoHFW & Tamil Nadu Health Guidelines)

| Sign Code | Danger Sign (English) | Danger Sign (Tamil) | Urgency Level | Immediate Action Protocol | Emergency Transport |
|---|---|---|---|---|---|
| `DS-BLD-01` | Vaginal bleeding at any time in pregnancy | கர்ப்ப காலத்தில் யோனி இரத்தப்போக்கு | **URGENT EMERGENCY** | Place mother in left lateral rest, do NOT perform vaginal examination, immediately arrange emergency transport to First Referral Unit (FRU) / CHC. | 108 Ambulance Call Immediately |
| `DS-CNV-02` | Convulsions / Fits / Loss of consciousness | வலிப்பு அல்லது மயக்கம் | **URGENT EMERGENCY** | Keep airway clear, turn mother to side, do not restrain forcefully, urgent MO transfer for MgSO4 administration. | 108 Ambulance Call Immediately |
| `DS-HDA-03` | Severe persistent headache with blurred vision | பார்வை மங்கலுடன் கடுமையான தலைவலி | **PRIORITY REFERRAL** | Check BP immediately, refer to nearest PHC/CHC within 2 hours to prevent eclampsia. | 108 / 102 Janani Express |
| `DS-FVR-04` | High fever (> 101°F) with chills or foul discharge | அதிக காய்ச்சல் மற்றும் துர்நாற்றமுள்ள திரவப்போக்கு | **PRIORITY REFERRAL** | Hydration, immediate referral to PHC for infection and sepsis management. | 102 Janani Express / PHC vehicle |
| `DS-LAB-05` | Severe abdominal pain / rigid abdomen | கடுமையான வயிற்று வலி | **URGENT EMERGENCY** | Urgent evaluation for abruption or rupture at FRU. | 108 Ambulance |
| `DS-LEK-06` | Leaking of amniotic fluid before labor | பிரசவ வலிக்கு முன் பனிக்குடம் உடைதல் / நீர் கசிவு | **URGENT EMERGENCY** | Clean perineal pad, transfer to institutional delivery facility immediately. | 108 Ambulance |
| `DS-FET-07` | Reduced or absent fetal movements | குழந்தையின் அசைவு குறைதல் அல்லது இல்லாமை | **PRIORITY REFERRAL** | Ask mother to count kicks after meal; urgent Doppler/USG at PHC if <10 kicks in 2 hours. | 102 / Local transport |
| `DS-BRT-08` | Severe shortness of breath at rest | ஓய்வில் இருக்கும் போது கடுமையான மூச்சுத் திணறல் | **URGENT EMERGENCY** | Rule out pulmonary oedema / peripartum cardiomyopathy; immediate oxygen and FRU transfer. | 108 Ambulance |


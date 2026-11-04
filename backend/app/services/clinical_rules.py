import datetime
from typing import List, Dict, Any, Optional

def calculate_edd(lmp_date: Optional[datetime.date]) -> Optional[datetime.date]:
    """Calculate Estimated Date of Delivery (EDD = LMP + 280 days) according to standard obstetric protocol."""
    if not lmp_date:
        return None
    return lmp_date + datetime.timedelta(days=280)

def calculate_gestational_age_weeks(lmp_date: Optional[datetime.date], as_of: Optional[datetime.date] = None) -> Optional[int]:
    """Calculates completed gestational weeks from reliable LMP date."""
    if not lmp_date:
        return None
    as_of = as_of or datetime.date.today()
    days = (as_of - lmp_date).days
    if days < 0:
        return 0
    return days // 7

def generate_standard_anc_schedule(lmp_date: datetime.date) -> List[Dict[str, Any]]:
    """Generates standard 4-visit ANC schedule based on MoHFW/NHM guidelines."""
    schedule = [
        {
            "anc_period": "ANC-1",
            "scheduled_date": lmp_date + datetime.timedelta(days=70), # ~10 weeks (within 1st trimester)
            "target_window": "Registration & 1st Trimester (up to 12 weeks)"
        },
        {
            "anc_period": "ANC-2",
            "scheduled_date": lmp_date + datetime.timedelta(days=140), # 20 weeks (14-26 weeks)
            "target_window": "2nd Trimester (14 to 26 weeks)"
        },
        {
            "anc_period": "ANC-3",
            "scheduled_date": lmp_date + datetime.timedelta(days=210), # 30 weeks (28-34 weeks)
            "target_window": "3rd Trimester (28 to 34 weeks)"
        },
        {
            "anc_period": "ANC-4",
            "scheduled_date": lmp_date + datetime.timedelta(days=252), # 36 weeks (36 to 40 weeks)
            "target_window": "Pre-delivery Assessment (36+ weeks)"
        }
    ]
    return schedule

def generate_standard_pnc_schedule(delivery_date: datetime.date) -> List[Dict[str, Any]]:
    """Generates 7 standard Postnatal Care visits for institutional/home deliveries (NHM protocol)."""
    intervals = [
        ("DAY_1", 1, "Within 24 hours of delivery"),
        ("DAY_3", 3, "Day 3 Postpartum Check"),
        ("DAY_7", 7, "Day 7 Postpartum Check"),
        ("DAY_14", 14, "Day 14 Postpartum Check"),
        ("DAY_21", 21, "Day 21 Postpartum Check"),
        ("DAY_28", 28, "Day 28 Postpartum Check"),
        ("DAY_42", 42, "Day 42 (6 weeks) Final PNC & Family Planning"),
    ]
    schedule = []
    for code, days, desc in intervals:
        schedule.append({
            "pnc_interval": code,
            "scheduled_date": delivery_date + datetime.timedelta(days=days),
            "description": desc
        })
    return schedule

def evaluate_clinical_rules(
    age: Optional[int] = None,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    hemoglobin_g_dl: Optional[float] = None,
    urine_albumin: Optional[str] = None,
    past_obstetric_history: Optional[str] = None,
    known_medical_conditions: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates clinical measurements against approved MoHFW/NHM clinical rules.
    Returns list of identified risk flags.
    Never auto-diagnoses; flags as RULE_FLAGGED with specific clinical rule ID.
    """
    flags = []

    # Rule 1: Gestational Hypertension / Pre-eclampsia Alert
    if bp_systolic is not None and bp_diastolic is not None:
        if bp_systolic >= 140 or bp_diastolic >= 90:
            flags.append({
                "rule_code": "RULE-HRP-BP-001",
                "risk_title": "Elevated Blood Pressure (>=140/90 mmHg)",
                "risk_detail": f"Recorded BP is {bp_systolic}/{bp_diastolic} mmHg. Potential gestational hypertension / pre-eclampsia risk. Professional evaluation required within 24 hours.",
                "severity": "HIGH",
                "status": "RULE_FLAGGED",
                "requires_professional_review": True
            })

    # Rule 2: Severe Anaemia Alert
    if hemoglobin_g_dl is not None:
        if hemoglobin_g_dl < 7.0:
            flags.append({
                "rule_code": "RULE-HRP-HB-002",
                "risk_title": "Severe Anaemia (Hb < 7.0 g/dL)",
                "risk_detail": f"Recorded Hb is {hemoglobin_g_dl} g/dL. Critical maternal and fetal oxygenation risk. Urgent referral to Medical Officer / FRU required.",
                "severity": "EMERGENCY",
                "status": "RULE_FLAGGED",
                "requires_professional_review": True
            })
        elif 7.0 <= hemoglobin_g_dl < 10.0:
            flags.append({
                "rule_code": "RULE-HRP-HB-003",
                "risk_title": "Moderate Anaemia (Hb 7.0 - 9.9 g/dL)",
                "risk_detail": f"Recorded Hb is {hemoglobin_g_dl} g/dL. Requires therapeutic double IFA regimen, nutritional counselling, and 30-day review.",
                "severity": "MODERATE",
                "status": "RULE_FLAGGED",
                "requires_professional_review": True
            })

    # Rule 3: High-Risk Age
    if age is not None:
        if age < 18:
            flags.append({
                "rule_code": "RULE-HRP-AGE-004",
                "risk_title": "Adolescent Pregnancy (Age < 18)",
                "risk_detail": f"Beneficiary age is {age} years. Higher physiological risk of cephalopelvic disproportion and pre-eclampsia.",
                "severity": "HIGH",
                "status": "RULE_FLAGGED",
                "requires_professional_review": True
            })
        elif age >= 35:
            flags.append({
                "rule_code": "RULE-HRP-AGE-004",
                "risk_title": "Advanced Maternal Age (Age >= 35)",
                "risk_detail": f"Beneficiary age is {age} years. Increased incidence of gestational diabetes and chromosomal anomalies.",
                "severity": "MODERATE",
                "status": "RULE_FLAGGED",
                "requires_professional_review": True
            })

    # Rule 4: Proteinuria
    if urine_albumin in ("TRACE", "PRESENT"):
        flags.append({
            "rule_code": "RULE-HRP-URINE-005",
            "risk_title": f"Proteinuria Detected ({urine_albumin})",
            "risk_detail": f"Urine Albumin test showed '{urine_albumin}'. Investigate for pre-eclampsia or urinary tract infection.",
            "severity": "HIGH",
            "status": "RULE_FLAGGED",
            "requires_professional_review": True
        })

    # Rule 5: Bad Obstetric History
    if past_obstetric_history:
        p_hist = past_obstetric_history.lower()
        keywords = ["miscarriage", "abortion", "stillbirth", "eclampsia", "c-section", "caesarean", "preterm", "bleeding", "iud"]
        if any(kw in p_hist for kw in keywords):
            flags.append({
                "rule_code": "RULE-HRP-HIST-006",
                "risk_title": "History of Complicated Pregnancy / BOH",
                "risk_detail": f"Prior obstetric history notes: {past_obstetric_history}. Mandatory institutional delivery planning at FRU.",
                "severity": "HIGH",
                "status": "RULE_FLAGGED",
                "requires_professional_review": True
            })

    return flags


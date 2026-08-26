# Pharmacist-facing medicine reference information.
# Display/counselling only — NOT used by the risk algorithm or ML models.

MEDICINE_INFO = {
    "Omeprazole": {
        "indication": "Used to reduce stomach acid, including reflux and acid-related conditions.",
        "common_side_effects": "Headache, abdominal discomfort, nausea, diarrhoea or constipation.",
        "change_factors": "Symptom control, treatment step-down, tolerability, duration of therapy and relevant interactions.",
        "increase_risks": "Higher exposure may increase adverse effects.",
        "decrease_risks": "Symptoms may recur or rebound acid symptoms may occur.",
        "monitoring": "Review ongoing treatment need and clinical response.",
        "important_interactions": "Check current interaction information where relevant.",
        "pregnancy_breastfeeding": "Check current clinical guidance where relevant.",
        "counselling": "Explain how to take the medicine and when symptoms should be reviewed.",
        "reference_source": "Pharmacist feedback; verify against current BNF/product information.",
        "high_risk_flag": 0,
        "dispensing_warning": "",
    },

    "Warfarin": {
        "indication": "Anticoagulant used to prevent or treat blood clots.",
        "common_side_effects": "Bleeding and bruising.",
        "change_factors": "INR, bleeding/clotting events, diet, acute illness, liver function and interacting medicines.",
        "increase_risks": "Excess anticoagulation may increase serious bleeding risk.",
        "decrease_risks": "Insufficient anticoagulation may increase thrombosis risk.",
        "monitoring": "INR monitoring is important.",
        "important_interactions": "Many clinically important medicine and dietary interactions.",
        "pregnancy_breastfeeding": "Requires specific clinical review.",
        "counselling": "Discuss bleeding precautions and anticoagulant monitoring.",
        "reference_source": "Pharmacist feedback; verify against current BNF/MHRA/product information.",
        "high_risk_flag": 1,
        "dispensing_warning": "HIGH-RISK MEDICINE: Confirm prescription, INR monitoring, interactions and patient-specific factors have been reviewed before dispensing.",
    },

    "Phenytoin": {
        "indication": "Used for treatment and prevention of certain seizures.",
        "common_side_effects": "Dizziness, nystagmus, ataxia and confusion.",
        "change_factors": "Serum concentration, seizure control, interactions, protein binding and nonlinear pharmacokinetics.",
        "increase_risks": "Small dose increases can sometimes cause disproportionate increases in exposure and toxicity.",
        "decrease_risks": "Dose reduction may increase breakthrough seizure risk.",
        "monitoring": "Serum phenytoin concentration and clinical response may require review.",
        "important_interactions": "Many clinically important enzyme-mediated interactions.",
        "pregnancy_breastfeeding": "Pregnancy or breastfeeding requires specific clinical review.",
        "counselling": "Discuss adherence, toxicity symptoms and specialist advice before treatment changes.",
        "reference_source": "Pharmacist feedback; verify against current BNF/MHRA/product information.",
        "high_risk_flag": 1,
        "dispensing_warning": "ADDITIONAL CLINICAL REVIEW: Confirm monitoring, interactions and pregnancy/breastfeeding considerations where applicable before dispensing.",
    },
}


DEFAULT_MEDICINE_INFO = {
    "indication": "",
    "common_side_effects": "",
    "change_factors": "",
    "increase_risks": "",
    "decrease_risks": "",
    "monitoring": "",
    "important_interactions": "",
    "pregnancy_breastfeeding": "",
    "counselling": "",
    "reference_source": "",
    "high_risk_flag": 0,
    "dispensing_warning": "",
}


def get_medicine_info(drug_name):
    return MEDICINE_INFO.get(drug_name, DEFAULT_MEDICINE_INFO)
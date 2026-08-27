# Pharmacist-facing medicine reference information.
# Display/counselling only — NOT used by the risk algorithm or ML models.
#
# Content is intentionally concise for the prototype UI.
# Clinical information should be verified against current BNF,
# NHS guidance and product information before real-world use.


def medicine(
    indication,
    common_side_effects,
    counselling,
    monitoring="",
    change_factors="",
    increase_risks="",
    decrease_risks="",
    important_interactions="",
    pregnancy_breastfeeding="",
    high_risk_flag=0,
    dispensing_warning="",
):
    return {
        "indication": indication,
        "common_side_effects": common_side_effects,
        "change_factors": change_factors,
        "increase_risks": increase_risks,
        "decrease_risks": decrease_risks,
        "monitoring": monitoring,
        "important_interactions": important_interactions,
        "pregnancy_breastfeeding": pregnancy_breastfeeding,
        "counselling": counselling,
        "reference_source": (
            "Pharmacist-facing summary; verify against current "
            "BNF/NHS/product information."
        ),
        "high_risk_flag": high_risk_flag,
        "dispensing_warning": dispensing_warning,
    }


MEDICINE_INFO = {

    # ---------------------------------------------------------
    # 1. AMLODIPINE
    # ---------------------------------------------------------
    "Amlodipine": medicine(
        indication=(
            "Used to treat high blood pressure and help prevent angina."
        ),
        common_side_effects=(
            "Headache, dizziness, flushing and ankle swelling."
        ),
        counselling=(
            "Take regularly as prescribed. Report troublesome swelling "
            "or persistent dizziness."
        ),
        monitoring=(
            "Review blood pressure, symptoms and adverse effects."
        ),
        change_factors=(
            "Blood-pressure control, angina symptoms, oedema, "
            "tolerability and interacting medicines."
        ),
    ),

    # ---------------------------------------------------------
    # 2. APIXABAN
    # ---------------------------------------------------------
    "Apixaban": medicine(
        indication=(
            "Anticoagulant used to prevent and treat blood clots "
            "and reduce stroke risk in some patients with atrial fibrillation."
        ),
        common_side_effects=(
            "Bleeding, bruising, anaemia and nausea."
        ),
        counselling=(
            "Take exactly as prescribed and report unusual or prolonged "
            "bleeding. Do not stop treatment without medical advice."
        ),
        monitoring=(
            "Review bleeding risk, renal function and concurrent medicines."
        ),
        change_factors=(
            "Bleeding risk, renal function, age, weight, interacting "
            "medicines and indication."
        ),
        important_interactions=(
            "Check for medicines that increase bleeding or alter "
            "apixaban exposure."
        ),
    ),

    # ---------------------------------------------------------
    # 3. ATORVASTATIN
    # ---------------------------------------------------------
    "Atorvastatin": medicine(
        indication=(
            "Used to lower cholesterol and reduce the risk of heart "
            "attack and stroke."
        ),
        common_side_effects=(
            "Headache, nausea, digestive symptoms and muscle aches."
        ),
        counselling=(
            "Take regularly as prescribed and report unexplained "
            "muscle pain, weakness or tenderness."
        ),
        monitoring=(
            "Review lipid response and relevant liver or muscle symptoms."
        ),
        change_factors=(
            "Cholesterol targets, cardiovascular risk, muscle symptoms, "
            "liver function and interactions."
        ),
    ),

    # ---------------------------------------------------------
    # 4. BISOPROLOL
    # ---------------------------------------------------------
    "Bisoprolol": medicine(
        indication=(
            "Used for high blood pressure, angina and some cases of "
            "heart failure."
        ),
        common_side_effects=(
            "Tiredness, dizziness, headache, cold hands or feet, "
            "and low blood pressure."
        ),
        counselling=(
            "Take regularly as prescribed and do not stop suddenly "
            "without medical advice."
        ),
        monitoring=(
            "Monitor blood pressure, heart rate and clinical response."
        ),
        change_factors=(
            "Heart rate, blood pressure, heart-failure symptoms and "
            "tolerability."
        ),
    ),

    # ---------------------------------------------------------
    # 5. DIGOXIN
    # ---------------------------------------------------------
    "Digoxin": medicine(
        indication=(
            "Used for some abnormal heart rhythms including atrial "
            "fibrillation and for selected patients with heart failure."
        ),
        common_side_effects=(
            "Dizziness, nausea, vomiting, diarrhoea and visual changes."
        ),
        counselling=(
            "Take consistently and seek advice if nausea, confusion, "
            "visual disturbance or unusual heartbeat occurs."
        ),
        monitoring=(
            "Renal function, electrolytes and digoxin concentration "
            "may require monitoring."
        ),
        change_factors=(
            "Renal function, serum concentration, heart rate, "
            "electrolytes and interacting medicines."
        ),
        important_interactions=(
            "Several medicines can alter digoxin concentration or "
            "increase arrhythmia risk."
        ),
    ),

    # ---------------------------------------------------------
    # 6. FUROSEMIDE
    # ---------------------------------------------------------
    "Furosemide": medicine(
        indication=(
            "Diuretic used to reduce excess fluid and sometimes to "
            "treat high blood pressure."
        ),
        common_side_effects=(
            "Increased urination, thirst, dizziness, headache and dehydration."
        ),
        counselling=(
            "Take as directed and be aware of increased urination. "
            "Seek advice if significant dehydration or dizziness occurs."
        ),
        monitoring=(
            "Monitor renal function, electrolytes, fluid status and "
            "blood pressure where appropriate."
        ),
        change_factors=(
            "Fluid status, blood pressure, renal function, electrolytes "
            "and clinical response."
        ),
    ),

    # ---------------------------------------------------------
    # 7. INSULIN GLARGINE
    # ---------------------------------------------------------
    "Insulin Glargine": medicine(
        indication=(
            "Long-acting insulin used to control blood glucose in diabetes."
        ),
        common_side_effects=(
            "Low blood glucose, injection-site reactions and weight gain."
        ),
        counselling=(
            "Use exactly as prescribed, monitor blood glucose and know "
            "how to recognise and manage hypoglycaemia."
        ),
        monitoring=(
            "Monitor blood glucose and review insulin requirements "
            "during illness or significant routine changes."
        ),
        change_factors=(
            "Blood-glucose control, diet, illness, renal function, "
            "activity and hypoglycaemia."
        ),
        increase_risks=(
            "Excess insulin may cause hypoglycaemia."
        ),
        decrease_risks=(
            "Insufficient insulin may cause hyperglycaemia."
        ),
    ),

    # ---------------------------------------------------------
    # 8. LEVOTHYROXINE
    # ---------------------------------------------------------
    "Levothyroxine": medicine(
        indication=(
            "Used to replace thyroid hormone in people with an "
            "underactive thyroid."
        ),
        common_side_effects=(
            "Side effects usually occur when the dose is too high and may "
            "include palpitations, sweating, tremor or restlessness."
        ),
        counselling=(
            "Take consistently in the same way each day and separate it "
            "from medicines or supplements that interfere with absorption "
            "when advised."
        ),
        monitoring=(
            "Thyroid function tests such as TSH are used to guide treatment."
        ),
        change_factors=(
            "TSH and thyroid hormone results, symptoms, pregnancy, "
            "weight and absorption interactions."
        ),
        important_interactions=(
            "Calcium, iron and some medicines can reduce absorption."
        ),
    ),

    # ---------------------------------------------------------
    # 9. LITHIUM
    # ---------------------------------------------------------
    "Lithium": medicine(
        indication=(
            "Used to treat and prevent episodes of bipolar disorder "
            "and some other mood disorders."
        ),
        common_side_effects=(
            "Tremor, thirst, increased urination, nausea and diarrhoea."
        ),
        counselling=(
            "Maintain consistent fluid and salt intake and seek urgent "
            "advice for possible toxicity symptoms."
        ),
        monitoring=(
            "Lithium concentration, renal function and thyroid function "
            "require regular monitoring."
        ),
        change_factors=(
            "Serum lithium concentration, renal function, hydration, "
            "sodium balance, symptoms and interacting medicines."
        ),
        increase_risks=(
            "Excess exposure can cause lithium toxicity."
        ),
        decrease_risks=(
            "Insufficient exposure may lead to loss of mood control."
        ),
        important_interactions=(
            "NSAIDs, ACE inhibitors and some diuretics can increase "
            "lithium concentrations."
        ),
    ),

    # ---------------------------------------------------------
    # 10. METFORMIN
    # ---------------------------------------------------------
    "Metformin": medicine(
        indication=(
            "Used to improve blood-glucose control in type 2 diabetes."
        ),
        common_side_effects=(
            "Nausea, diarrhoea, stomach discomfort and reduced appetite."
        ),
        counselling=(
            "Take with or after food when advised to reduce stomach "
            "side effects and follow the prescribed formulation and dose."
        ),
        monitoring=(
            "Review glucose control and renal function."
        ),
        change_factors=(
            "Blood-glucose control, gastrointestinal tolerability, "
            "renal function and formulation."
        ),
        increase_risks=(
            "Higher doses may increase gastrointestinal adverse effects."
        ),
        decrease_risks=(
            "Dose reduction may reduce glucose-lowering effect."
        ),
    ),

    # ---------------------------------------------------------
    # 11. OMEPRAZOLE
    # ---------------------------------------------------------
    "Omeprazole": medicine(
        indication=(
            "Used to reduce stomach acid, including reflux and "
            "acid-related conditions."
        ),
        common_side_effects=(
            "Headache, abdominal discomfort, nausea, diarrhoea "
            "or constipation."
        ),
        counselling=(
            "Explain how to take the medicine and when persistent "
            "or recurrent symptoms should be reviewed."
        ),
        monitoring=(
            "Review ongoing treatment need and clinical response."
        ),
        change_factors=(
            "Symptom control, treatment step-down, tolerability, "
            "duration of therapy and relevant interactions."
        ),
        increase_risks=(
            "Higher exposure may increase adverse effects."
        ),
        decrease_risks=(
            "Symptoms may recur or rebound acid symptoms may occur."
        ),
    ),

    # ---------------------------------------------------------
    # 12. PHENYTOIN
    # ---------------------------------------------------------
    "Phenytoin": medicine(
        indication=(
            "Used for treatment and prevention of certain seizures."
        ),
        common_side_effects=(
            "Dizziness, nystagmus, ataxia and confusion."
        ),
        counselling=(
            "Discuss adherence, toxicity symptoms and specialist advice "
            "before treatment changes."
        ),
        monitoring=(
            "Serum phenytoin concentration and clinical response may "
            "require review."
        ),
        change_factors=(
            "Serum concentration, seizure control, interactions, "
            "protein binding and nonlinear pharmacokinetics."
        ),
        increase_risks=(
            "Small dose increases can sometimes cause disproportionate "
            "increases in exposure and toxicity."
        ),
        decrease_risks=(
            "Dose reduction may increase breakthrough seizure risk."
        ),
        important_interactions=(
            "Many clinically important enzyme-mediated interactions."
        ),
        pregnancy_breastfeeding=(
            "Pregnancy or breastfeeding requires specific clinical review."
        ),
        high_risk_flag=1,
        dispensing_warning=(
            "ADDITIONAL CLINICAL REVIEW: Confirm monitoring, interactions "
            "and pregnancy/breastfeeding considerations where applicable "
            "before dispensing."
        ),
    ),

    # ---------------------------------------------------------
    # 13. PREDNISOLONE
    # ---------------------------------------------------------
    "Prednisolone": medicine(
        indication=(
            "Corticosteroid used to reduce inflammation and suppress "
            "immune responses in a range of conditions."
        ),
        common_side_effects=(
            "Indigestion, difficulty sleeping, mood changes and "
            "increased appetite."
        ),
        counselling=(
            "Take exactly as prescribed, usually with food. Long courses "
            "should not normally be stopped suddenly without medical advice."
        ),
        monitoring=(
            "Longer treatment may require monitoring of blood pressure, "
            "glucose and other corticosteroid adverse effects."
        ),
        change_factors=(
            "Disease activity, duration of treatment, response and "
            "corticosteroid adverse effects."
        ),
    ),

    # ---------------------------------------------------------
    # 14. RAMIPRIL
    # ---------------------------------------------------------
    "Ramipril": medicine(
        indication=(
            "Used for high blood pressure, heart failure and to reduce "
            "cardiovascular or kidney risk in selected patients."
        ),
        common_side_effects=(
            "Dizziness, headache, dry cough and gastrointestinal symptoms."
        ),
        counselling=(
            "Take regularly and seek advice for severe dizziness, "
            "swelling or persistent troublesome cough."
        ),
        monitoring=(
            "Blood pressure, kidney function and potassium commonly "
            "require review."
        ),
        change_factors=(
            "Blood pressure, renal function, potassium, cough, "
            "heart-failure response and hypotension."
        ),
        increase_risks=(
            "Higher exposure may increase hypotension, hyperkalaemia "
            "or renal impairment."
        ),
    ),

    # ---------------------------------------------------------
    # 15. SALBUTAMOL
    # ---------------------------------------------------------
    "Salbutamol": medicine(
        indication=(
            "Reliever medicine used to quickly ease wheezing and "
            "breathlessness caused by conditions such as asthma."
        ),
        common_side_effects=(
            "Tremor, headache, faster heartbeat and muscle cramps."
        ),
        counselling=(
            "Ensure correct inhaler technique and seek clinical review "
            "if the reliever is needed more often than expected."
        ),
        monitoring=(
            "Review symptom control, inhaler technique and frequency of use."
        ),
        change_factors=(
            "Symptom control, frequency of reliever use and treatment response."
        ),
    ),

    # ---------------------------------------------------------
    # 16. SERTRALINE
    # ---------------------------------------------------------
    "Sertraline": medicine(
        indication=(
            "Used to treat depression and certain anxiety-related disorders."
        ),
        common_side_effects=(
            "Nausea, headache, dizziness, sleep disturbance and diarrhoea."
        ),
        counselling=(
            "Take regularly as prescribed. Benefits may take several weeks "
            "and treatment should not be stopped suddenly without advice."
        ),
        monitoring=(
            "Review treatment response, adverse effects and changes in mood."
        ),
        change_factors=(
            "Treatment response, adverse effects, mental-health symptoms "
            "and interacting medicines."
        ),
        increase_risks=(
            "Higher doses may increase adverse effects."
        ),
        decrease_risks=(
            "Dose reduction may reduce treatment response or cause "
            "discontinuation symptoms if changed too quickly."
        ),
    ),

    # ---------------------------------------------------------
    # 17. VITAMIN D
    # ---------------------------------------------------------
    "Vitamin D": medicine(
        indication=(
            "Used to prevent or treat vitamin D deficiency and support "
            "normal bone and muscle health."
        ),
        common_side_effects=(
            "Usually well tolerated at prescribed doses; excessive doses "
            "can raise calcium levels."
        ),
        counselling=(
            "Take the prescribed dose and avoid taking additional "
            "high-dose vitamin D unless advised."
        ),
        monitoring=(
            "Calcium or vitamin D levels may be monitored in selected patients."
        ),
        change_factors=(
            "Vitamin D status, calcium levels, treatment phase and "
            "clinical response."
        ),
    ),

    # ---------------------------------------------------------
    # 18. WARFARIN
    # ---------------------------------------------------------
    "Warfarin": medicine(
        indication=(
            "Anticoagulant used to prevent or treat blood clots."
        ),
        common_side_effects=(
            "Bleeding and bruising."
        ),
        counselling=(
            "Discuss bleeding precautions, anticoagulant monitoring "
            "and the importance of taking the prescribed dose."
        ),
        monitoring=(
            "INR monitoring is important."
        ),
        change_factors=(
            "INR, bleeding or clotting events, diet, acute illness, "
            "liver function and interacting medicines."
        ),
        increase_risks=(
            "Excess anticoagulation may increase serious bleeding risk."
        ),
        decrease_risks=(
            "Insufficient anticoagulation may increase thrombosis risk."
        ),
        important_interactions=(
            "Many clinically important medicine and dietary interactions."
        ),
        pregnancy_breastfeeding=(
            "Requires specific clinical review."
        ),
        high_risk_flag=1,
        dispensing_warning=(
            "HIGH-RISK MEDICINE: Confirm prescription, INR monitoring, "
            "interactions and patient-specific factors have been reviewed "
            "before dispensing."
        ),
    ),
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
    if not drug_name:
        return DEFAULT_MEDICINE_INFO.copy()

    # Exact match first
    if drug_name in MEDICINE_INFO:
        return MEDICINE_INFO[drug_name].copy()

    # Case-insensitive fallback
    normalized = drug_name.strip().lower()

    for medicine_name, info in MEDICINE_INFO.items():
        if medicine_name.lower() == normalized:
            return info.copy()

    return DEFAULT_MEDICINE_INFO.copy()
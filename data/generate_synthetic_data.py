# Part of the data pipeline -- the first step, makes patients.csv and
# medications.csv that everything downstream builds on.
"""
Generates the synthetic patient/prescription dataset.

A few design choices worth knowing about:
- Drugs are grouped by therapeutic_class (Anticoagulant, ACE inhibitor,
  SSRI, etc.) rather than sitting in one flat list.
- Each patient also gets a handful of concurrent_medications, shown
  alongside the alert for context and summarised as polypharmacy_count.
- Risk isn't one flat rule for every drug -- each drug is flagged
  narrow_therapeutic_index (NTI) or not. NTI drugs (warfarin, digoxin,
  levothyroxine, insulin, lithium) have a much smaller gap between an
  effective and a harmful dose, so the risk thresholds scale with that
  rather than using one fixed percentage for everything.
- drug_changed only means the active ingredient changed.
  formulation_changed is its own flag for immediate- vs
  extended-release swaps of the same drug (this does matter clinically).
  manufacturer_changed is tracked as a control feature on purpose --
  it's a packaging/brand swap, not a formula change, and it's meant to
  show up as not mattering once eda.py looks at it, rather than that
  just being an assumption.
"""

import csv
import os
import random
import sys
import uuid
from datetime import date, timedelta

random.seed(42)

# Resolve the import path from this file's own location rather than the
# current working directory, so it works whether you run this from
# inside data/ or from the repo root. comparison_engine.py doesn't touch
# `random` or do any file I/O on import, so importing it here can't
# affect the random.seed(42) sequence above.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
from comparison_engine import classify_risk  # noqa: E402

# --- Reference drug data -----------------------------------------------
# Each drug: name, therapeutic_class, narrow_therapeutic_index (NTI),
# available formulations (>1 means a formulation-change scenario is
# possible), typical doses (mg), route, associated condition.
# Each drug's "routes" list is ordered [primary route, ...alternates]. Almost
# every drug here only has one real-world route -- a tablet doesn't have a
# subcutaneous form. The two exceptions (Digoxin, Furosemide) genuinely do
# have a well-established IV/IM form alongside the oral one, so those are
# the only drugs a route_change scenario can actually produce. "unit" is
# the correct clinical dose unit for that drug -- most are mg, but a few
# (insulin, levothyroxine, salbutamol, vitamin D) are not, and using mg for
# those would be clinically wrong regardless of the numeric value.
DRUGS = [
    {"name": "Warfarin", "class": "Anticoagulant", "nti": True,
     "formulations": ["Standard"], "doses": [1, 2, 3, 5, 10], "unit": "mg",
     "routes": ["Oral"], "condition": "Atrial fibrillation"},
    {"name": "Apixaban", "class": "Anticoagulant", "nti": True,
     "formulations": ["Standard"], "doses": [2.5, 5], "unit": "mg",
     "routes": ["Oral"], "condition": "Atrial fibrillation"},
    {"name": "Digoxin", "class": "Cardiac glycoside", "nti": True,
     "formulations": ["Standard"], "doses": [0.0625, 0.125, 0.25], "unit": "mg",
     # IV only -- intramuscular digoxin is painful and associated with
     # muscle necrosis, and isn't modelled here.
     "routes": ["Oral", "Intravenous"], "condition": "Heart failure"},
    {"name": "Levothyroxine", "class": "Thyroid hormone", "nti": True,
     "formulations": ["Standard"], "doses": [25, 50, 75, 100, 125], "unit": "micrograms",
     "routes": ["Oral"], "condition": "Hypothyroidism"},
    {"name": "Insulin Glargine", "class": "Insulin", "nti": True,
     "formulations": ["Standard"], "doses": [10, 20, 30, 40], "unit": "units",
     "routes": ["Subcutaneous"], "condition": "Type 1 diabetes"},
    {"name": "Lithium", "class": "Mood stabiliser", "nti": True,
     "formulations": ["Standard-release", "Prolonged-release"], "doses": [200, 400, 600, 800], "unit": "mg",
     "routes": ["Oral"], "condition": "Bipolar disorder"},

    {"name": "Metformin", "class": "Biguanide (antidiabetic)", "nti": False,
     "formulations": ["Standard-release", "Prolonged-release"], "doses": [500, 850, 1000], "unit": "mg",
     "routes": ["Oral"], "condition": "Type 2 diabetes"},
    {"name": "Amlodipine", "class": "Calcium channel blocker", "nti": False,
     "formulations": ["Standard"], "doses": [5, 10], "unit": "mg",
     "routes": ["Oral"], "condition": "Hypertension"},
    {"name": "Ramipril", "class": "ACE inhibitor", "nti": False,
     "formulations": ["Standard"], "doses": [1.25, 2.5, 5, 10], "unit": "mg",
     "routes": ["Oral"], "condition": "Hypertension"},
    {"name": "Bisoprolol", "class": "Beta-blocker", "nti": False,
     "formulations": ["Standard"], "doses": [1.25, 2.5, 5, 10], "unit": "mg",
     "routes": ["Oral"], "condition": "Heart failure"},
    {"name": "Atorvastatin", "class": "Statin", "nti": False,
     "formulations": ["Standard"], "doses": [10, 20, 40, 80], "unit": "mg",
     "routes": ["Oral"], "condition": "Hyperlipidaemia"},
    # 100 micrograms/actuation is the real UK salbutamol MDI strength; there
    # is no 200-micrograms/actuation product. Modelling "2 actuations" as a
    # dose would need a separate actuation-count field this project doesn't
    # have -- delivered-dose frequency is out of scope, so only the one
    # real product strength is represented.
    {"name": "Salbutamol", "class": "Beta-2 agonist (bronchodilator)", "nti": False,
     "formulations": ["Standard"], "doses": [100], "unit": "micrograms/actuation",
     "routes": ["Inhaled"], "condition": "Asthma"},
    {"name": "Omeprazole", "class": "Proton pump inhibitor", "nti": False,
     "formulations": ["Gastro-resistant"], "doses": [10, 20, 40], "unit": "mg",
     "routes": ["Oral"], "condition": "GORD"},
    {"name": "Sertraline", "class": "SSRI (antidepressant)", "nti": False,
     "formulations": ["Standard"], "doses": [50, 100, 150], "unit": "mg",
     "routes": ["Oral"], "condition": "Depression"},
    {"name": "Furosemide", "class": "Loop diuretic", "nti": False,
     "formulations": ["Standard"], "doses": [20, 40, 80], "unit": "mg",
     # Kept to Oral/IV for this prototype -- IM furosemide exists but isn't
     # modelled here, matching the same scope decision made for Digoxin.
     "routes": ["Oral", "Intravenous"], "condition": "Heart failure"},
    {"name": "Vitamin D", "class": "Supplement", "nti": False,
     "formulations": ["Standard"], "doses": [400, 800, 1000], "unit": "IU",
     "routes": ["Oral"], "condition": "Vitamin D deficiency"},
    {"name": "Prednisolone", "class": "Corticosteroid", "nti": False,
     "formulations": ["Standard"], "doses": [5, 10, 20, 40], "unit": "mg",
     "routes": ["Oral"], "condition": "COPD exacerbation"},
]

MANUFACTURERS = ["Accord Healthcare", "Teva", "Mylan", "Sandoz", "Wockhardt", "Actavis"]
ALLERGIES = ["Penicillin", "None recorded", "Sulphonamides", "NSAIDs", "None recorded", "None recorded"]
GP_NAMES = ["Dr A. Okafor", "Dr S. Patel", "Dr J. McAllister", "Dr R. Chowdhury", "Dr E. Novak", "Dr F. Bianchi"]

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
               "William", "Elizabeth", "David", "Susan", "Richard", "Jessica", "Joseph", "Sarah",
               "Thomas", "Karen", "Charles", "Nancy", "Aisha", "Mohammed", "Priya", "Wei", "Fatima", "Liam"]
LAST_NAMES = ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies",
              "Robinson", "Wright", "Thompson", "Evans", "Walker", "White", "Roberts", "Green",
              "Hall", "Wood", "Khan", "Patel", "Singh", "Ahmed", "Kelly", "Baker"]


def random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def gen_patients(n):
    patients = []
    for _ in range(n):
        pid = str(uuid.uuid4())[:8]
        dob = random_date(date(1935, 1, 1), date(2008, 12, 31))
        patients.append({
            "patient_id": pid,
            "first_name": random.choice(FIRST_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "date_of_birth": dob.isoformat(),
            "allergy": random.choice(ALLERGIES),
            "gp_name": random.choice(GP_NAMES),
        })
    return patients


def pick_concurrent_medications(index_drug, k):
    """Picks k other drugs (not the index drug) this patient is also
    taking, purely for context -- doesn't feed into the risk rule."""
    pool = [d for d in DRUGS if d["name"] != index_drug["name"]]
    k = min(k, len(pool))
    return random.sample(pool, k)


def make_prescription_pair(patient, drug):
    prev_dose = random.choice(drug["doses"])
    prev_formulation = random.choice(drug["formulations"])
    prev_manufacturer = random.choice(MANUFACTURERS)
    prev_start = random_date(date(2025, 1, 1), date(2026, 4, 1))

    # A drug switch is only ever plausible onto another drug used for the
    # SAME condition (e.g. Warfarin <-> Apixaban, both for atrial
    # fibrillation) -- never onto an unrelated drug just because none
    # exists for this condition. 10 of the 17 drugs here are the only drug
    # listed for their condition, so "drug_switch" simply isn't offered as
    # a possible scenario for those -- no invented substitute, no no-op
    # placeholder pretending a switch happened.
    same_condition_alts = [d for d in DRUGS if d["condition"] == drug["condition"] and d["name"] != drug["name"]]
    change_type_weights = [
        ("none", 12), ("dose_increase", 13), ("dose_decrease_small", 13), ("dose_decrease_large", 13),
        ("drug_switch", 15), ("formulation_switch", 13), ("manufacturer_switch_only", 11), ("route_change", 10),
    ]
    if not same_condition_alts:
        change_type_weights = [(ct, w) for ct, w in change_type_weights if ct != "drug_switch"]
    options, weights = zip(*change_type_weights)
    change_type = random.choices(options, weights=weights, k=1)[0]

    prev_route = drug["routes"][0]

    cur_dose = prev_dose
    cur_formulation = prev_formulation
    cur_manufacturer = prev_manufacturer
    cur_route = prev_route
    cur_drug = drug

    if change_type == "dose_increase":
        higher = [d for d in drug["doses"] if d > prev_dose]
        cur_dose = random.choice(higher) if higher else prev_dose
        cur_manufacturer = random.choice(MANUFACTURERS)
    elif change_type == "dose_decrease_small":
        lower = [d for d in drug["doses"] if 0 < prev_dose - d and (prev_dose - d) / prev_dose < 0.5]
        cur_dose = random.choice(lower) if lower else prev_dose
        cur_manufacturer = random.choice(MANUFACTURERS)
    elif change_type == "dose_decrease_large":
        lower = [d for d in drug["doses"] if d < prev_dose and (prev_dose - d) / prev_dose >= 0.5]
        cur_dose = random.choice(lower) if lower else (drug["doses"][0] if drug["doses"][0] < prev_dose else prev_dose)
        cur_manufacturer = random.choice(MANUFACTURERS)
    elif change_type == "drug_switch":
        # same_condition_alts is guaranteed non-empty here -- "drug_switch"
        # was excluded from change_type_weights above whenever it's empty.
        cur_drug = random.choice(same_condition_alts)
        cur_dose = random.choice(cur_drug["doses"])
        cur_formulation = random.choice(cur_drug["formulations"])
        cur_route = cur_drug["routes"][0]
        cur_manufacturer = random.choice(MANUFACTURERS)
    elif change_type == "formulation_switch":
        alt_forms = [f for f in drug["formulations"] if f != prev_formulation]
        if alt_forms:
            cur_formulation = random.choice(alt_forms)
        cur_manufacturer = random.choice(MANUFACTURERS)
    elif change_type == "manufacturer_switch_only":
        alt_mfrs = [m for m in MANUFACTURERS if m != prev_manufacturer]
        cur_manufacturer = random.choice(alt_mfrs) if alt_mfrs else prev_manufacturer
    elif change_type == "route_change":
        # Only meaningful for a drug with more than one real route (Digoxin,
        # Furosemide -- both genuinely available as oral and IV/IM). For a
        # single-route drug there's no valid alternate route to switch to,
        # so this scenario is a no-op for it, same as dose_increase falling
        # back to prev_dose when there's no higher dose available.
        alt_routes = [r for r in drug["routes"] if r != prev_route]
        if alt_routes:
            cur_route = random.choice(alt_routes)

    cur_start = prev_start + timedelta(days=random.randint(14, 120))

    # --- Derive ACTUAL features from real before/after values ---------
    drug_changed = cur_drug["name"] != drug["name"]
    formulation_changed = (not drug_changed) and (cur_formulation != prev_formulation)
    manufacturer_changed = cur_manufacturer != prev_manufacturer
    route_changed = cur_route != prev_route
    dose_changed = cur_dose != prev_dose
    # A percentage only makes sense between two doses of the SAME drug --
    # across a drug switch the numbers may not even share a unit (e.g. IU
    # vs mg), so no percentage is computed there at all.
    dose_pct_change = 0.0
    if not drug_changed and prev_dose:
        dose_pct_change = (prev_dose - cur_dose) / prev_dose
    narrow_therapeutic_index = drug["nti"] or (drug_changed and cur_drug["nti"])

    concurrent = pick_concurrent_medications(drug, random.choice([0, 1, 1, 2, 2, 3]))
    polypharmacy_count = len(concurrent)

    # uses the same classify_risk() the live app calls, so the generator
    # and the app can't quietly end up with different rules
    risk_label = classify_risk(
        drug_changed=drug_changed,
        formulation_changed=formulation_changed,
        dose_changed=dose_changed,
        dose_change_pct=dose_pct_change,
        route_changed=route_changed,
        narrow_therapeutic_index=narrow_therapeutic_index,
    )

    return {
        "patient_id": patient["patient_id"],
        "condition": drug["condition"],
        "previous_drug": drug["name"],
        "previous_class": drug["class"],
        "previous_dose_mg": prev_dose,
        "previous_dose_unit": drug["unit"],
        "previous_formulation": prev_formulation,
        "previous_manufacturer": prev_manufacturer,
        "previous_route": prev_route,
        "previous_start_date": prev_start.isoformat(),
        "previous_prescriber": patient["gp_name"],
        "current_drug": cur_drug["name"],
        "current_class": cur_drug["class"],
        "current_dose_mg": cur_dose,
        "current_dose_unit": cur_drug["unit"],
        "current_formulation": cur_formulation,
        "current_manufacturer": cur_manufacturer,
        "current_route": cur_route,
        "current_start_date": cur_start.isoformat(),
        "current_prescriber": patient["gp_name"],
        "change_type_label": change_type,
        "drug_changed": drug_changed,
        "formulation_changed": formulation_changed,
        "manufacturer_changed": manufacturer_changed,
        "route_changed": route_changed,
        "dose_changed": dose_changed,
        "dose_change_pct": round(dose_pct_change, 3),
        "narrow_therapeutic_index": narrow_therapeutic_index,
        "concurrent_medications": "; ".join(d["name"] for d in concurrent),
        "polypharmacy_count": polypharmacy_count,
        "risk_label": risk_label,
    }


def main(per_class=150, out_dir="."):
    """Keeps sampling until each risk class has exactly `per_class` rows,
    so the dataset comes out balanced by construction rather than by luck."""
    targets = {"NONE": per_class, "LOW": per_class, "MEDIUM": per_class, "HIGH": per_class}
    counts = {k: 0 for k in targets}
    patients, rows = [], []
    attempts, max_attempts = 0, per_class * 4 * 400

    while any(counts[k] < targets[k] for k in targets) and attempts < max_attempts:
        attempts += 1
        p = gen_patients(1)[0]
        drug = random.choice(DRUGS)
        pair = make_prescription_pair(p, drug)
        label = pair["risk_label"]

        if counts.get(label, 0) >= targets.get(label, 0):
            continue

        counts[label] += 1
        pair["first_name"] = p["first_name"]
        pair["last_name"] = p["last_name"]
        pair["date_of_birth"] = p["date_of_birth"]
        pair["allergy"] = p["allergy"]
        patients.append(p)
        rows.append(pair)

    if attempts >= max_attempts:
        print(f"WARNING: hit max_attempts with counts={counts} (target {per_class} each)")

    combined = list(zip(patients, rows))
    random.shuffle(combined)
    patients, rows = zip(*combined)
    patients, rows = list(patients), list(rows)

    patients_path = f"{out_dir}/patients.csv"
    with open(patients_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(patients[0].keys()))
        w.writeheader()
        w.writerows(patients)

    meds_path = f"{out_dir}/medications.csv"
    with open(meds_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Generated {len(patients)} patients -> {patients_path}")
    print(f"Generated {len(rows)} prescription pairs -> {meds_path}")
    print(f"Class balance: {counts}")
    print(f"Drugs: {len(DRUGS)} across {len(set(d['class'] for d in DRUGS))} therapeutic classes, "
          f"{sum(1 for d in DRUGS if d['nti'])} narrow-therapeutic-index")


if __name__ == "__main__":
    main()

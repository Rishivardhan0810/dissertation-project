# Automated tests -- run with: pytest backend/tests -v
"""Comparison-engine correctness (formulation/NTI logic included) plus
dataset integrity: balance, missing values, train/test leakage."""
import collections
import os
import sys
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
DATA_DIR = os.path.join(HERE, "..", "..", "data")

from comparison_engine import Prescription, compare_prescriptions  # noqa: E402

# ---------------------------------------------------------------------
# Comparison engine unit tests
# ---------------------------------------------------------------------

def test_no_change_detected():
    prev = Prescription("Metformin", 500, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Metformin", 500, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p1", prev, cur)
    assert report.change_types == []
    assert not report.drug_changed
    assert not report.dose_changed

def test_drug_switch_detected():
    prev = Prescription("Warfarin", 5, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Apixaban", 5, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p2", prev, cur)
    assert report.drug_changed
    assert "drug" in report.change_types

def test_large_dose_reduction_percentage():
    prev = Prescription("Furosemide", 80, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Furosemide", 20, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p3", prev, cur)
    assert report.dose_changed
    assert report.dose_change_pct == pytest.approx(0.75, abs=0.001)

def test_route_change_detected():
    prev = Prescription("Insulin Glargine", 20, "Standard", "Teva", "Subcutaneous", "2026-01-01", "Dr A")
    cur = Prescription("Insulin Glargine", 20, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p4", prev, cur)
    assert report.route_changed
    assert not report.drug_changed
    assert not report.dose_changed

def test_formulation_change_detected_not_confused_with_drug_change():
    """Immediate-release -> extended-release of the SAME drug should be
    formulation_changed, not drug_changed."""
    prev = Prescription("Metformin", 500, "Immediate-release", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Metformin", 500, "Extended-release", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p5", prev, cur)
    assert report.formulation_changed
    assert not report.drug_changed

def test_manufacturer_only_change_not_flagged_as_a_meaningful_change():
    """A brand/generic-maker swap of the identical formula should NOT
    appear in change_types -- this is the 'focus on formula, not
    packaging' behaviour, tested directly."""
    prev = Prescription("Atorvastatin", 20, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Atorvastatin", 20, "Standard", "Accord Healthcare", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p6", prev, cur)
    assert report.manufacturer_changed
    assert report.change_types == []  # tracked, but not a risk-relevant change

def test_narrow_therapeutic_index_flagged_correctly():
    """Warfarin is a known narrow-therapeutic-index drug; Vitamin D is not."""
    prev = Prescription("Warfarin", 5, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Warfarin", 3, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p7", prev, cur)
    assert report.narrow_therapeutic_index

    prev2 = Prescription("Vitamin D", 800, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur2 = Prescription("Vitamin D", 400, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report2 = compare_prescriptions("p8", prev2, cur2)
    assert not report2.narrow_therapeutic_index

def test_nti_detection_is_case_insensitive():
    """The shared NTI matcher must not depend on exact capitalisation --
    real-world drug names won't always arrive capitalised like the
    synthetic generator's reference table."""
    prev = Prescription("warfarin", 5, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("WARFARIN", 3, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p9", prev, cur)
    assert report.narrow_therapeutic_index

def test_nti_detection_rejects_false_substring_match():
    """A plain 'Insulin' entry shouldn't be flagged NTI just because
    'insulin' is a substring of 'Insulin Glargine'."""
    prev = Prescription("Insulin", 10, "Standard", "Teva", "Subcutaneous", "2026-01-01", "Dr A")
    cur = Prescription("Insulin", 12, "Standard", "Teva", "Subcutaneous", "2026-02-01", "Dr A")
    report = compare_prescriptions("p10", prev, cur)
    assert not report.narrow_therapeutic_index

def test_comparison_engine_and_real_data_adapter_share_one_nti_function():
    """Both call sites should resolve to the same function object, not two
    copies that happen to agree today but could drift apart later."""
    from comparison_engine import is_narrow_therapeutic_index as engine_fn
    sys.path.insert(0, os.path.join(DATA_DIR, "real_synthea"))
    import adapt_real_synthea
    assert adapt_real_synthea.is_narrow_therapeutic_index is engine_fn

def test_drug_switch_risk_scales_with_nti_not_uniformly_high():
    """A drug switch shouldn't score the same regardless of whether an
    NTI drug is involved -- guards against an earlier bug where every
    switch scored HIGH no matter what."""
    import pandas as pd
    raw_path = os.path.join(DATA_DIR, "medications.csv")
    if not os.path.exists(raw_path):
        pytest.skip("medications.csv not generated -- run data/generate_synthetic_data.py first")
    df = pd.read_csv(raw_path)
    switches = df[df["drug_changed"] == True]  # noqa: E712
    nti_labels = set(switches[switches["narrow_therapeutic_index"] == True]["risk_label"])  # noqa: E712
    non_nti_labels = set(switches[switches["narrow_therapeutic_index"] == False]["risk_label"])  # noqa: E712
    assert len(switches) > 0, "No drug switches were generated -- can't test this"
    assert nti_labels != non_nti_labels or (nti_labels == set() or non_nti_labels == set()), (
        f"Drug switches score identically regardless of NTI status: "
        f"NTI switches -> {nti_labels}, non-NTI switches -> {non_nti_labels}. "
        f"Risk must scale by pharmacology, not just by whether a switch happened."
    )

# ---------------------------------------------------------------------
# Dose-percentage handling: only meaningful for a same-drug comparison
# ---------------------------------------------------------------------

def test_same_drug_dose_percentage_still_calculated():
    """Digoxin 0.125mg -> 0.25mg is a same-drug, same-unit comparison, so
    the 100% increase should still be computed and reported."""
    prev = Prescription("Digoxin", 0.125, "Standard", "Teva", "Oral", "2026-01-01", "Dr A")
    cur = Prescription("Digoxin", 0.25, "Standard", "Teva", "Oral", "2026-02-01", "Dr A")
    report = compare_prescriptions("p11", prev, cur)
    assert report.dose_change_pct == pytest.approx(-1.0, abs=0.001)
    assert "100%" in report.magnitude_summary
    assert "increased" in report.magnitude_summary

def test_different_drug_dose_percentage_is_suppressed():
    """A drug switch shouldn't report a dose percentage at all -- Vitamin D
    (IU) to Furosemide (mg) is not a meaningful numeric comparison, even
    though the two dose_mg values differ a lot."""
    prev = Prescription("Vitamin D", 1000, "Standard", "Teva", "Oral", "2026-01-01", "Dr A", dose_unit="IU")
    cur = Prescription("Furosemide", 80, "Standard", "Teva", "Oral", "2026-02-01", "Dr A", dose_unit="mg")
    report = compare_prescriptions("p12", prev, cur)
    assert report.dose_change_pct == 0.0
    assert "%" not in report.magnitude_summary
    assert "1000 IU" in report.magnitude_summary
    assert "80mg" in report.magnitude_summary
    assert report.drug_changed

def test_dose_percentage_suppressed_when_units_differ_for_the_same_drug_name():
    """Defensive case: even if the drug name is unchanged, a percentage
    should only be computed when the unit is also the same -- guards
    against malformed/inconsistent data, not just drug switches."""
    prev = Prescription("Test Drug", 100, "Standard", "Teva", "Oral", "2026-01-01", "Dr A", dose_unit="micrograms")
    cur = Prescription("Test Drug", 100, "Standard", "Teva", "Oral", "2026-02-01", "Dr A", dose_unit="mg")
    report = compare_prescriptions("p13", prev, cur)
    assert report.dose_change_pct == 0.0

# ---------------------------------------------------------------------
# Dataset integrity tests (run after generate_synthetic_data.py + preprocess.py)
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def raw_data():
    path = os.path.join(DATA_DIR, "medications.csv")
    if not os.path.exists(path):
        pytest.skip("medications.csv not generated -- run data/generate_synthetic_data.py first")
    return pd.read_csv(path)

@pytest.fixture(scope="module")
def train_test():
    train_path = os.path.join(DATA_DIR, "train.csv")
    test_path = os.path.join(DATA_DIR, "test.csv")
    if not (os.path.exists(train_path) and os.path.exists(test_path)):
        pytest.skip("train.csv/test.csv not built -- run data/preprocess.py first")
    return pd.read_csv(train_path), pd.read_csv(test_path)

def test_no_missing_values(raw_data):
    # concurrent_medications is legitimately empty for patients with zero
    # concurrent medications (polypharmacy_count == 0) -- an empty string
    # in the CSV reads back as NaN in pandas, which is expected, not a
    # data quality problem. Every other column must have no nulls.
    other_cols = [c for c in raw_data.columns if c != "concurrent_medications"]
    assert raw_data[other_cols].isnull().sum().sum() == 0
    zero_polypharmacy = raw_data[raw_data["polypharmacy_count"] == 0]
    assert raw_data["concurrent_medications"].isnull().sum() == len(zero_polypharmacy), (
        "concurrent_medications is blank for rows other than polypharmacy_count == 0"
    )

def test_class_balance_within_tolerance(raw_data):
    counts = raw_data["risk_label"].value_counts()
    ratio = counts.max() / counts.min()
    assert ratio <= 1.5, f"Classes are imbalanced: {counts.to_dict()} (ratio {ratio:.2f})"

def test_all_four_classes_present(raw_data):
    assert set(raw_data["risk_label"].unique()) == {"NONE", "LOW", "MEDIUM", "HIGH"}

def test_at_least_two_therapeutic_classes_and_one_nti_drug_present(raw_data):
    """Sanity check that the drug reference table actually made it into
    the generated data, not just the code."""
    assert raw_data["previous_class"].nunique() >= 2
    assert raw_data["narrow_therapeutic_index"].any()

def test_manufacturer_changes_exist_but_dont_drive_risk_alone(raw_data):
    """Manufacturer-only swaps should actually exist in the data, and
    should score NONE rather than a false alarm."""
    mfr_only = raw_data[
        raw_data["manufacturer_changed"]
        & ~raw_data["drug_changed"] & ~raw_data["formulation_changed"]
        & ~raw_data["dose_changed"] & ~raw_data["route_changed"]
    ]
    assert len(mfr_only) > 0, "No manufacturer-only change pairs were generated"
    assert (mfr_only["risk_label"] == "NONE").all()

# ---------------------------------------------------------------------
# Medication reference data: routes/formulations/units must be
# drug-specific and clinically plausible, not generic across every drug
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def drug_reference():
    """Imports the actual generator reference table (not a hand-copied
    duplicate of it), so these tests check the real source of truth."""
    sys.path.insert(0, DATA_DIR)
    import generate_synthetic_data as gen
    return {d["name"]: d for d in gen.DRUGS}

def test_no_impossible_route_for_any_drug(raw_data, drug_reference):
    """A drug should never appear with a route it doesn't actually have --
    e.g. Apixaban/Metformin/Levothyroxine etc. are oral-only and must
    never show up as Subcutaneous, Inhaled, etc."""
    for _, row in raw_data.iterrows():
        prev_ref = drug_reference[row["previous_drug"]]
        assert row["previous_route"] in prev_ref["routes"], (
            f"{row['previous_drug']} generated with route {row['previous_route']!r}, "
            f"but its only valid routes are {prev_ref['routes']}"
        )
        cur_ref = drug_reference[row["current_drug"]]
        assert row["current_route"] in cur_ref["routes"], (
            f"{row['current_drug']} generated with route {row['current_route']!r}, "
            f"but its only valid routes are {cur_ref['routes']}"
        )

def test_furosemide_extended_release_no_longer_generated(raw_data):
    furosemide_rows = raw_data[
        (raw_data["previous_drug"] == "Furosemide") | (raw_data["current_drug"] == "Furosemide")
    ]
    assert not (furosemide_rows["previous_formulation"] == "Extended-release").any()
    assert not (furosemide_rows["current_formulation"] == "Extended-release").any()
    assert not (furosemide_rows["previous_formulation"] == "Immediate-release").any()

def test_insulin_glargine_uses_units_not_mg(raw_data):
    rows = raw_data[raw_data["previous_drug"] == "Insulin Glargine"]
    assert len(rows) > 0, "No Insulin Glargine rows generated"
    assert (rows["previous_dose_unit"] == "units").all()

def test_levothyroxine_uses_micrograms_not_mg(raw_data):
    rows = raw_data[raw_data["previous_drug"] == "Levothyroxine"]
    assert len(rows) > 0, "No Levothyroxine rows generated"
    assert (rows["previous_dose_unit"] == "micrograms").all()

def test_vitamin_d_uses_iu_not_mg(raw_data):
    rows = raw_data[raw_data["previous_drug"] == "Vitamin D"]
    assert len(rows) > 0, "No Vitamin D rows generated"
    assert (rows["previous_dose_unit"] == "IU").all()

def test_dose_change_pct_is_zero_whenever_drug_changed(raw_data):
    """The generator-side fix for the same issue comparison_engine.py
    fixes: a drug switch should never carry a nonzero dose_change_pct."""
    switches = raw_data[raw_data["drug_changed"] == True]  # noqa: E712
    assert len(switches) > 0
    assert (switches["dose_change_pct"] == 0.0).all()

def test_drug_switches_only_occur_within_same_condition(raw_data, drug_reference):
    """A drug switch must never cross into an unrelated condition -- no
    more 'Vitamin D -> Furosemide'-style substitutions."""
    switches = raw_data[raw_data["drug_changed"] == True]  # noqa: E712
    assert len(switches) > 0, "No drug switches were generated at all"
    for _, row in switches.iterrows():
        prev_condition = drug_reference[row["previous_drug"]]["condition"]
        cur_condition = drug_reference[row["current_drug"]]["condition"]
        assert prev_condition == cur_condition, (
            f"Drug switch crossed conditions: {row['previous_drug']} ({prev_condition}) -> "
            f"{row['current_drug']} ({cur_condition})"
        )

def test_single_drug_conditions_never_generate_a_drug_switch(raw_data, drug_reference):
    """Conditions with only one drug in the reference table (e.g. Vitamin D
    deficiency, Type 1 diabetes) have no valid same-condition alternative,
    so a drug_switch should never be generated for them at all -- not even
    onto an unrelated drug."""
    condition_drug_counts = collections.Counter(d["condition"] for d in drug_reference.values())
    single_drug_conditions = {c for c, n in condition_drug_counts.items() if n == 1}
    assert len(single_drug_conditions) > 0, "Expected at least one single-drug condition in the reference table"

    switches = raw_data[raw_data["drug_changed"] == True]  # noqa: E712
    for _, row in switches.iterrows():
        prev_condition = drug_reference[row["previous_drug"]]["condition"]
        assert prev_condition not in single_drug_conditions, (
            f"{row['previous_drug']} ({prev_condition}) has no same-condition alternative, "
            f"but a drug switch was generated for it anyway -> {row['current_drug']}"
        )

def test_digoxin_never_uses_generic_injection_or_intramuscular(raw_data):
    digoxin_rows = raw_data[(raw_data["previous_drug"] == "Digoxin") | (raw_data["current_drug"] == "Digoxin")]
    assert len(digoxin_rows) > 0, "No Digoxin rows generated"
    for col in ("previous_route", "current_route"):
        assert not (digoxin_rows[col] == "Injection").any(), f"Digoxin generated with generic 'Injection' in {col}"
        assert not (digoxin_rows[col] == "Intramuscular").any(), f"Digoxin generated with 'Intramuscular' in {col}"

def test_furosemide_uses_only_oral_or_intravenous(raw_data):
    prev_routes = raw_data.loc[raw_data["previous_drug"] == "Furosemide", "previous_route"]
    cur_routes = raw_data.loc[raw_data["current_drug"] == "Furosemide", "current_route"]
    assert len(prev_routes) + len(cur_routes) > 0, "No Furosemide rows generated"
    used_routes = set(prev_routes.unique()) | set(cur_routes.unique())
    assert used_routes <= {"Oral", "Intravenous"}, f"Furosemide used an unexpected route: {used_routes}"

def test_salbutamol_dose_unit_and_value_are_coherent(raw_data):
    """Salbutamol should only ever appear as the one real product strength
    (100 micrograms/actuation) -- no invented 200-micrograms/actuation
    strength."""
    rows = raw_data[raw_data["previous_drug"] == "Salbutamol"]
    assert len(rows) > 0, "No Salbutamol rows generated"
    assert (rows["previous_dose_unit"] == "micrograms/actuation").all()
    assert (rows["previous_dose_mg"] == 100).all()

def test_no_patient_overlap_between_train_and_test(train_test):
    train_df, test_df = train_test
    overlap = set(train_df["patient_id"]) & set(test_df["patient_id"])
    assert not overlap, f"{len(overlap)} patients leaked across train/test"

def test_all_classes_present_in_both_splits(train_test):
    train_df, test_df = train_test
    assert set(train_df["risk_label"].unique()) == {"NONE", "LOW", "MEDIUM", "HIGH"}
    assert set(test_df["risk_label"].unique()) == {"NONE", "LOW", "MEDIUM", "HIGH"}

def test_no_class_missing_or_tiny_in_either_split(train_test):
    """Every class needs a reasonable minimum count in both train and test."""
    train_df, test_df = train_test
    for split_name, df in [("train", train_df), ("test", test_df)]:
        counts = df["risk_label"].value_counts()
        assert counts.min() >= 10, f"{split_name} split has a near-empty class: {counts.to_dict()}"

# ---------------------------------------------------------------------
# Real Synthea external validation set (optional -- only if present)
# ---------------------------------------------------------------------

def test_real_synthea_adapter_output_well_formed():
    real_path = os.path.join(DATA_DIR, "real_synthea", "real_test.csv")
    if not os.path.exists(real_path):
        pytest.skip("real_test.csv not built -- run data/real_synthea/adapt_real_synthea.py first")
    df = pd.read_csv(real_path)
    assert len(df) > 0
    assert df["risk_label"].isin(["NONE", "LOW", "MEDIUM", "HIGH"]).all()
    assert df["dose_change_pct"].notna().all()

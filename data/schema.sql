-- Part of the data pipeline -- defines every table and view in
-- pharmacy.db. load_to_db.py runs this file to build the database.
--
-- The schema is intentionally simple for the MSc prototype.
-- The medicine-information fields provide pharmacist-facing clinical
-- context and are NOT inputs to the automated risk-classification model.


-- ================================================================
-- PATIENTS
-- ================================================================

CREATE TABLE IF NOT EXISTS patients (

    patient_id             TEXT PRIMARY KEY,

    first_name             TEXT NOT NULL,

    last_name              TEXT NOT NULL,

    date_of_birth          TEXT NOT NULL,

    condition              TEXT,

    allergy                TEXT,

    gp_name                TEXT,

    concurrent_medications TEXT,

    polypharmacy_count     INTEGER DEFAULT 0

);


-- ================================================================
-- PRESCRIPTIONS
-- ================================================================

CREATE TABLE IF NOT EXISTS prescriptions (

    prescription_id INTEGER PRIMARY KEY,

    patient_id TEXT NOT NULL
        REFERENCES patients(patient_id),

    drug_name TEXT NOT NULL,

    drug_class TEXT,


    -- ------------------------------------------------------------
    -- PHARMACIST-FACING MEDICINE INFORMATION
    -- ------------------------------------------------------------
    --
    -- These fields provide clinical context and counselling
    -- information.
    --
    -- IMPORTANT:
    -- They are NOT used by the Random Forest, text model or
    -- deterministic prescription-change risk classifier.

    indication TEXT,

    common_side_effects TEXT,

    change_factors TEXT,

    increase_risks TEXT,

    decrease_risks TEXT,

    monitoring TEXT,

    important_interactions TEXT,

    pregnancy_breastfeeding TEXT,

    counselling TEXT,

    reference_source TEXT,


    -- ------------------------------------------------------------
    -- MEDICINE-SPECIFIC SAFETY REVIEW
    -- ------------------------------------------------------------
    --
    -- Separate from prescription-change risk.
    --
    -- Example:
    -- Warfarin or phenytoin may require an additional pharmacist
    -- review even when the prescription itself has not changed.

    high_risk_flag INTEGER NOT NULL DEFAULT 0,

    dispensing_warning TEXT,


    -- ------------------------------------------------------------
    -- PRESCRIPTION INFORMATION
    -- ------------------------------------------------------------

    dose_mg REAL NOT NULL,

    dose_unit TEXT NOT NULL DEFAULT 'mg',

    formulation TEXT NOT NULL,

    manufacturer TEXT,

    route TEXT NOT NULL,

    start_date TEXT NOT NULL,

    prescriber TEXT,

    is_current INTEGER NOT NULL DEFAULT 0

);


-- ================================================================
-- ACKNOWLEDGEMENTS
-- ================================================================

CREATE TABLE IF NOT EXISTS acknowledgements (

    ack_id INTEGER PRIMARY KEY,

    patient_id TEXT NOT NULL
        REFERENCES patients(patient_id),

    pharmacist_name TEXT NOT NULL,

    ack_timestamp TEXT NOT NULL,

    risk_level TEXT NOT NULL

);


-- ================================================================
-- DISPENSING RECORDS
-- ================================================================
--
-- Kept separate from acknowledgements because a normal prescription
-- may be dispensed without a prescription-change alert.

CREATE TABLE IF NOT EXISTS dispenses (

    dispense_id INTEGER PRIMARY KEY,

    patient_id TEXT NOT NULL
        REFERENCES patients(patient_id),

    ack_id INTEGER
        REFERENCES acknowledgements(ack_id),

    pharmacist_name TEXT NOT NULL,

    drug_name TEXT NOT NULL,

    dose_mg REAL NOT NULL,

    dispense_timestamp TEXT NOT NULL

);


-- ================================================================
-- INDEXES
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_prescriptions_patient
ON prescriptions(patient_id);

CREATE INDEX IF NOT EXISTS idx_dispenses_patient
ON dispenses(patient_id);


-- ================================================================
-- ACTIVITY LOG VIEW
-- ================================================================
--
-- Combines acknowledgement and dispensing activity into one readable
-- audit view.

CREATE VIEW IF NOT EXISTS activity_log AS

SELECT

    'Acknowledged alert' AS action,

    p.first_name || ' ' || p.last_name AS patient_name,

    a.pharmacist_name,

    NULL AS drug_name,

    NULL AS dose_mg,

    a.risk_level,

    a.ack_timestamp AS happened_at

FROM acknowledgements a

JOIN patients p
    ON p.patient_id = a.patient_id


UNION ALL


SELECT

    'Dispensed' AS action,

    p.first_name || ' ' || p.last_name AS patient_name,

    d.pharmacist_name,

    d.drug_name,

    d.dose_mg,

    NULL AS risk_level,

    d.dispense_timestamp AS happened_at

FROM dispenses d

JOIN patients p
    ON p.patient_id = d.patient_id


ORDER BY happened_at DESC;
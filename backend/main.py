# Part of the backend -- the FastAPI app itself. Ties together the
# database, the comparison engine, and the two comparison models.
"""
Patient lookup, prescription comparison, risk scoring (rule + Random
Forest + text model), acknowledgement/dispense logging, and the audit
endpoints. This is what the React frontend talks to.
"""

import os
import sqlite3
from datetime import datetime, timezone

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from comparison_engine import (
    Prescription,
    compare_prescriptions,
    natural_language_description,
    classify_risk,
)


# ---------------------------------------------------------------------
# FILE LOCATIONS
# ---------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    HERE,
    "..",
    "data",
    "pharmacy.db",
)

RF_MODEL_PATH = os.path.join(
    HERE,
    "risk_models",
    "rf_model.joblib",
)

TEXT_MODEL_PATH = os.path.join(
    HERE,
    "risk_models",
    "text_model.joblib",
)


# ---------------------------------------------------------------------
# PRESCRIPTION FIELDS USED BY THE COMPARISON ENGINE
# ---------------------------------------------------------------------
#
# IMPORTANT:
# Medicine-information fields such as indication, monitoring,
# counselling and dispensing warnings are deliberately NOT included.
#
# They are pharmacist-facing reference information only and do not
# influence the deterministic rule or either ML model.

RX_FIELDS = (
    "drug_name",
    "dose_mg",
    "dose_unit",
    "formulation",
    "manufacturer",
    "route",
    "start_date",
    "prescriber",
)


# ---------------------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------------------

app = FastAPI(
    title="Prescription Comparison Alert API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# LOAD SAVED ML MODELS
# ---------------------------------------------------------------------

rf_model = (
    joblib.load(RF_MODEL_PATH)
    if os.path.exists(RF_MODEL_PATH)
    else None
)

text_model = (
    joblib.load(TEXT_MODEL_PATH)
    if os.path.exists(TEXT_MODEL_PATH)
    else None
)


# ---------------------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------------------

def get_conn():
    """
    Open a fresh SQLite connection.

    sqlite3.Row allows rows to behave similarly to dictionaries.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ---------------------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------------------

class LookupRequest(BaseModel):
    patient_id: str
    date_of_birth: str


class AckRequest(BaseModel):
    patient_id: str
    pharmacist_name: str
    risk_level: str


class DispenseRequest(BaseModel):
    patient_id: str
    pharmacist_name: str
    drug_name: str
    dose_mg: float


# ---------------------------------------------------------------------
# MEDICINE INFORMATION HELPER
# ---------------------------------------------------------------------

def build_medicine_information(row):
    """
    Build the pharmacist-facing medicine-information object.

    These values are display/counselling information only.
    They do not influence risk classification.
    """

    if not row:
        return None

    return {
        "drug_name": row.get(
            "drug_name",
            "",
        ),

        "indication": row.get(
            "indication",
            "",
        ),

        "common_side_effects": row.get(
            "common_side_effects",
            "",
        ),

        "change_factors": row.get(
            "change_factors",
            "",
        ),

        "increase_risks": row.get(
            "increase_risks",
            "",
        ),

        "decrease_risks": row.get(
            "decrease_risks",
            "",
        ),

        "monitoring": row.get(
            "monitoring",
            "",
        ),

        "important_interactions": row.get(
            "important_interactions",
            "",
        ),

        "pregnancy_breastfeeding": row.get(
            "pregnancy_breastfeeding",
            "",
        ),

        "counselling": row.get(
            "counselling",
            "",
        ),

        "reference_source": row.get(
            "reference_source",
            "",
        ),

        "high_risk_flag": bool(
            row.get(
                "high_risk_flag",
                0,
            )
        ),

        "dispensing_warning": row.get(
            "dispensing_warning",
            "",
        ),
    }


# ---------------------------------------------------------------------
# PATIENT LOOKUP
# ---------------------------------------------------------------------

@app.post("/api/lookup")
def lookup_patient(req: LookupRequest):
    """
    Look up a patient using Patient ID and date of birth.

    Both values must match the same patient record.
    """

    conn = get_conn()

    row = conn.execute(
        """
        SELECT *
        FROM patients
        WHERE patient_id = ?
          AND date_of_birth = ?
        """,
        (
            req.patient_id,
            req.date_of_birth,
        ),
    ).fetchone()

    if not row:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="No matching patient record found.",
        )

    patient = dict(row)

    # Retrieve every prescription for the patient, oldest first.
    rx_rows = conn.execute(
        """
        SELECT *
        FROM prescriptions
        WHERE patient_id = ?
        ORDER BY start_date ASC
        """,
        (
            patient["patient_id"],
        ),
    ).fetchall()

    conn.close()

    prescriptions = [
        dict(r)
        for r in rx_rows
    ]


    # -----------------------------------------------------------------
    # NO PRESCRIPTIONS
    # -----------------------------------------------------------------

    if len(prescriptions) == 0:

        return {
            "patient": patient,
            "prescriptions": [],
            "alert": None,
            "medicine_information": None,
            "status": "no_prescriptions",
            "status_message":
                "No prescription available for this patient.",
        }


    # -----------------------------------------------------------------
    # FIRST PRESCRIPTION
    # -----------------------------------------------------------------

    if len(prescriptions) == 1:

        current_rx = prescriptions[0]

        return {
            "patient": patient,
            "prescriptions": prescriptions,
            "alert": None,

            "medicine_information":
                build_medicine_information(
                    current_rx
                ),

            "status":
                "first_prescription",

            "status_message": (
                "Automated prescription-change comparison cannot be "
                "performed because no previous prescription is available. "
                "Pharmacist review of the medication, dose and formulation "
                "is required before dispensing."
            ),
        }


    # -----------------------------------------------------------------
    # PREVIOUS VS CURRENT PRESCRIPTION
    # -----------------------------------------------------------------

    previous_row = prescriptions[-2]
    current_row = prescriptions[-1]


    # Only RX_FIELDS are supplied to Prescription.
    #
    # Pharmacist-facing medicine information is therefore completely
    # separate from the comparison/risk pipeline.

    previous = Prescription(
        **{
            key: previous_row[key]
            for key in RX_FIELDS
        }
    )

    current = Prescription(
        **{
            key: current_row[key]
            for key in RX_FIELDS
        }
    )


    # -----------------------------------------------------------------
    # PRESCRIPTION COMPARISON
    # -----------------------------------------------------------------

    report = compare_prescriptions(
        patient["patient_id"],
        previous,
        current,
    )


    sentence = natural_language_description(
        report,

        patient.get(
            "condition",
            "",
        ),

        patient.get(
            "allergy",
            "",
        ),

        patient.get(
            "concurrent_medications",
            "",
        ),
    )


    # -----------------------------------------------------------------
    # RISK CLASSIFICATION
    # -----------------------------------------------------------------

    alert = None


    if report.change_types:

        # Random Forest receives only the six structured comparison
        # features used throughout the project.

        rf_features = pd.DataFrame(
            [
                {
                    "drug_changed":
                        int(
                            report.drug_changed
                        ),

                    "formulation_changed":
                        int(
                            report.formulation_changed
                        ),

                    "dose_changed":
                        int(
                            report.dose_changed
                        ),

                    "dose_change_pct_abs":
                        abs(
                            report.dose_change_pct
                        ),

                    "route_changed":
                        int(
                            report.route_changed
                        ),

                    "narrow_therapeutic_index":
                        int(
                            report.narrow_therapeutic_index
                        ),
                }
            ]
        )


        # -------------------------------------------------------------
        # RANDOM FOREST
        # -------------------------------------------------------------

        if rf_model is not None:

            rf_risk = rf_model.predict(
                rf_features
            )[0]

        else:

            rf_risk = "UNKNOWN"


        # -------------------------------------------------------------
        # TEXT MODEL
        # -------------------------------------------------------------

        if text_model is not None:

            text_risk = text_model.predict(
                [sentence]
            )[0]

        else:

            text_risk = "UNKNOWN"


        # -------------------------------------------------------------
        # DETERMINISTIC PRIMARY RISK RULE
        # -------------------------------------------------------------

        rule_risk = classify_risk(

            drug_changed=
                report.drug_changed,

            formulation_changed=
                report.formulation_changed,

            dose_changed=
                report.dose_changed,

            dose_change_pct=
                report.dose_change_pct,

            route_changed=
                report.route_changed,

            narrow_therapeutic_index=
                report.narrow_therapeutic_index,
        )


        # The deterministic rule controls the live alert.
        #
        # Random Forest and text-model predictions remain secondary
        # comparison signals only.

        final_risk = rule_risk


        # -------------------------------------------------------------
        # ALERT RESPONSE
        # -------------------------------------------------------------

        alert = {

            "change_types":
                report.change_types,

            "summary":
                report.magnitude_summary,

            "natural_language":
                sentence,

            "previous":
                report.previous,

            "current":
                report.current,

            "narrow_therapeutic_index":
                report.narrow_therapeutic_index,

            "manufacturer_changed":
                report.manufacturer_changed,

            "risk_rule":
                rule_risk,

            "risk_random_forest":
                rf_risk,

            "risk_text_model":
                text_risk,

            "risk_final":
                final_risk,

            "gp_name":
                patient.get(
                    "gp_name",
                    "",
                ),


            # ---------------------------------------------------------
            # BASIC CURRENT-MEDICINE COUNSELLING INFORMATION
            # ---------------------------------------------------------
            #
            # Kept here for backwards compatibility with the existing
            # frontend AlertPanel.
            #
            # Full medicine information is also returned separately in
            # medicine_information below.

            "indication":
                current_row.get(
                    "indication",
                    "",
                ),

            "common_side_effects":
                current_row.get(
                    "common_side_effects",
                    "",
                ),
        }


    # -----------------------------------------------------------------
    # NORMAL LOOKUP RESPONSE
    # -----------------------------------------------------------------

    return {

        "patient":
            patient,

        "prescriptions":
            prescriptions,

        "alert":
            alert,

        "medicine_information":
            build_medicine_information(
                current_row
            ),

        "status":
            "normal",

        "status_message":
            None,
    }


# ---------------------------------------------------------------------
# ACKNOWLEDGEMENT
# ---------------------------------------------------------------------

@app.post("/api/acknowledge")
def acknowledge(req: AckRequest):
    """
    Record that a pharmacist reviewed an alert or first prescription.
    """

    conn = get_conn()

    conn.execute(
        """
        INSERT INTO acknowledgements (
            patient_id,
            pharmacist_name,
            ack_timestamp,
            risk_level
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            req.patient_id,

            req.pharmacist_name,

            datetime.now(
                timezone.utc
            ).isoformat(),

            req.risk_level,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "status": "acknowledged"
    }


# ---------------------------------------------------------------------
# DISPENSING
# ---------------------------------------------------------------------

@app.post("/api/dispense")
def dispense(req: DispenseRequest):
    """
    Record an actual dispensing transaction.

    If an acknowledgement exists, the dispense is linked to the most
    recent acknowledgement for that patient.
    """

    conn = get_conn()


    ack_row = conn.execute(
        """
        SELECT ack_id
        FROM acknowledgements
        WHERE patient_id = ?
        ORDER BY ack_id DESC
        LIMIT 1
        """,
        (
            req.patient_id,
        ),
    ).fetchone()


    ack_id = (
        ack_row["ack_id"]
        if ack_row
        else None
    )


    conn.execute(
        """
        INSERT INTO dispenses (
            patient_id,
            ack_id,
            pharmacist_name,
            drug_name,
            dose_mg,
            dispense_timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            req.patient_id,

            ack_id,

            req.pharmacist_name,

            req.drug_name,

            req.dose_mg,

            datetime.now(
                timezone.utc
            ).isoformat(),
        ),
    )


    conn.commit()
    conn.close()


    return {
        "status": "dispensed"
    }


# ---------------------------------------------------------------------
# AUDIT SUMMARY
# ---------------------------------------------------------------------

@app.get("/api/audit/summary")
def audit_summary():
    """
    Return aggregate information for the Audit & Safety dashboard.
    """

    conn = get_conn()


    total_dispenses = conn.execute(
        """
        SELECT COUNT(*)
        FROM dispenses
        """
    ).fetchone()[0]


    total_acknowledgements = conn.execute(
        """
        SELECT COUNT(*)
        FROM acknowledgements
        """
    ).fetchone()[0]


    first_prescription_reviews = conn.execute(
        """
        SELECT COUNT(*)
        FROM acknowledgements
        WHERE risk_level = 'FIRST_PRESCRIPTION_REVIEW'
        """
    ).fetchone()[0]


    acknowledged_risk_counts = {
        "NONE": 0,
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
    }


    rows = conn.execute(
        """
        SELECT
            risk_level,
            COUNT(*) AS n
        FROM acknowledgements
        WHERE risk_level IN (
            'NONE',
            'LOW',
            'MEDIUM',
            'HIGH'
        )
        GROUP BY risk_level
        """
    ).fetchall()


    conn.close()


    for row in rows:

        acknowledged_risk_counts[
            row["risk_level"]
        ] = row["n"]


    return {

        "total_dispenses":
            total_dispenses,

        "total_acknowledgements":
            total_acknowledgements,

        "first_prescription_reviews":
            first_prescription_reviews,

        "acknowledged_risk_counts":
            acknowledged_risk_counts,
    }


# ---------------------------------------------------------------------
# AUDIT ACTIVITY
# ---------------------------------------------------------------------

@app.get("/api/audit/activity")
def audit_activity(limit: int = 50):
    """
    Return recent acknowledgement and dispensing events.

    Patient ID is deliberately used instead of patient name in this
    oversight view.
    """

    if limit <= 0:

        raise HTTPException(
            status_code=400,
            detail="limit must be a positive integer",
        )


    limit = min(
        limit,
        500,
    )


    conn = get_conn()


    rows = conn.execute(
        """
        SELECT
            'Acknowledged' AS action,
            patient_id,
            pharmacist_name,
            NULL AS drug_name,
            NULL AS dose_mg,
            risk_level,
            ack_timestamp AS happened_at

        FROM acknowledgements

        UNION ALL

        SELECT
            'Dispensed' AS action,
            patient_id,
            pharmacist_name,
            drug_name,
            dose_mg,
            NULL AS risk_level,
            dispense_timestamp AS happened_at

        FROM dispenses

        ORDER BY happened_at DESC

        LIMIT ?
        """,
        (
            limit,
        ),
    ).fetchall()


    conn.close()


    return {

        "events": [
            dict(r)
            for r in rows
        ]
    }


# ---------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------

@app.get("/api/health")
def health():
    """
    Confirm that the backend is running and show whether the two saved
    comparison models loaded successfully.
    """

    return {

        "status":
            "ok",

        "rf_model_loaded":
            rf_model is not None,

        "text_model_loaded":
            text_model is not None,
    }
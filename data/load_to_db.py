# Part of the data pipeline -- builds pharmacy.db.
# Loads patients.csv and medications.csv into SQLite using schema.sql.
#
# Pharmacist-facing medicine information is stored separately in
# medicine_reference.py to keep this loader simple and maintainable.

import csv
import os
import sqlite3

from medicine_reference import get_medicine_info


HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "pharmacy.db")


# ---------------------------------------------------------------------
# INSERT PRESCRIPTION
# ---------------------------------------------------------------------

def insert_prescription(
    conn,
    patient_id,
    drug_name,
    drug_class,
    dose_mg,
    dose_unit,
    formulation,
    manufacturer,
    route,
    start_date,
    prescriber,
    is_current,
):
    """
    Insert a prescription together with pharmacist-facing medicine
    reference information.

    Medicine reference fields are display/counselling information only.
    They are not ML features and do not affect risk classification.
    """

    info = get_medicine_info(drug_name)

    conn.execute(
        """
        INSERT INTO prescriptions (
            patient_id,
            drug_name,
            drug_class,

            indication,
            common_side_effects,
            change_factors,
            increase_risks,
            decrease_risks,
            monitoring,
            important_interactions,
            pregnancy_breastfeeding,
            counselling,
            reference_source,

            high_risk_flag,
            dispensing_warning,

            dose_mg,
            dose_unit,
            formulation,
            manufacturer,
            route,
            start_date,
            prescriber,
            is_current
        )
        VALUES (
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            patient_id,
            drug_name,
            drug_class,

            info.get("indication", ""),
            info.get("common_side_effects", ""),
            info.get("change_factors", ""),
            info.get("increase_risks", ""),
            info.get("decrease_risks", ""),
            info.get("monitoring", ""),
            info.get("important_interactions", ""),
            info.get("pregnancy_breastfeeding", ""),
            info.get("counselling", ""),
            info.get("reference_source", ""),

            int(info.get("high_risk_flag", 0)),
            info.get("dispensing_warning", ""),

            float(dose_mg),
            dose_unit,
            formulation,
            manufacturer,
            route,
            start_date,
            prescriber,
            int(is_current),
        ),
    )


# ---------------------------------------------------------------------
# MAIN DATABASE BUILD
# ---------------------------------------------------------------------

def main():

    # Rebuilding the database removes existing prototype audit logs.
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    # -------------------------------------------------------------
    # CREATE DATABASE TABLES
    # -------------------------------------------------------------

    schema_path = os.path.join(HERE, "schema.sql")

    with open(schema_path, encoding="utf-8") as f:
        conn.executescript(f.read())


    # -------------------------------------------------------------
    # BUILD PATIENT MEDICATION CONTEXT
    # -------------------------------------------------------------

    med_context = {}

    medications_path = os.path.join(
        HERE,
        "medications.csv",
    )

    with open(
        medications_path,
        encoding="utf-8",
        newline="",
    ) as f:

        for row in csv.DictReader(f):

            pid = row["patient_id"]

            if pid not in med_context:

                med_context[pid] = {
                    "condition":
                        row.get("condition", ""),

                    "concurrent_medications":
                        row.get(
                            "concurrent_medications",
                            "",
                        ),

                    "polypharmacy_count":
                        row.get(
                            "polypharmacy_count",
                            0,
                        ),
                }


    # -------------------------------------------------------------
    # LOAD PATIENTS
    # -------------------------------------------------------------

    patients_path = os.path.join(
        HERE,
        "patients.csv",
    )

    with open(
        patients_path,
        encoding="utf-8",
        newline="",
    ) as f:

        for row in csv.DictReader(f):

            ctx = med_context.get(
                row["patient_id"],
                {},
            )

            conn.execute(
                """
                INSERT INTO patients (
                    patient_id,
                    first_name,
                    last_name,
                    date_of_birth,
                    condition,
                    allergy,
                    gp_name,
                    concurrent_medications,
                    polypharmacy_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["patient_id"],
                    row["first_name"],
                    row["last_name"],
                    row["date_of_birth"],

                    ctx.get(
                        "condition",
                        "",
                    ),

                    row.get(
                        "allergy",
                        "",
                    ),

                    row.get(
                        "gp_name",
                        "",
                    ),

                    ctx.get(
                        "concurrent_medications",
                        "",
                    ),

                    int(
                        ctx.get(
                            "polypharmacy_count",
                            0,
                        )
                        or 0
                    ),
                ),
            )


    # -------------------------------------------------------------
    # LOAD PREVIOUS AND CURRENT PRESCRIPTIONS
    # -------------------------------------------------------------

    with open(
        medications_path,
        encoding="utf-8",
        newline="",
    ) as f:

        for row in csv.DictReader(f):

            pid = row["patient_id"]

            # Previous prescription
            insert_prescription(
                conn=conn,
                patient_id=pid,

                drug_name=
                    row["previous_drug"],

                drug_class=
                    row["previous_class"],

                dose_mg=
                    row["previous_dose_mg"],

                dose_unit=
                    row["previous_dose_unit"],

                formulation=
                    row["previous_formulation"],

                manufacturer=
                    row["previous_manufacturer"],

                route=
                    row["previous_route"],

                start_date=
                    row["previous_start_date"],

                prescriber=
                    row["previous_prescriber"],

                is_current=0,
            )

            # Current prescription
            insert_prescription(
                conn=conn,
                patient_id=pid,

                drug_name=
                    row["current_drug"],

                drug_class=
                    row["current_class"],

                dose_mg=
                    row["current_dose_mg"],

                dose_unit=
                    row["current_dose_unit"],

                formulation=
                    row["current_formulation"],

                manufacturer=
                    row["current_manufacturer"],

                route=
                    row["current_route"],

                start_date=
                    row["current_start_date"],

                prescriber=
                    row["current_prescriber"],

                is_current=1,
            )


    # -------------------------------------------------------------
    # OPTIONAL FIRST-PRESCRIPTION DEMO PATIENT
    # -------------------------------------------------------------

    demo_path = os.path.join(
        HERE,
        "demo_patient.csv",
    )

    if os.path.exists(demo_path):

        with open(
            demo_path,
            encoding="utf-8",
            newline="",
        ) as f:

            for row in csv.DictReader(f):

                conn.execute(
                    """
                    INSERT INTO patients (
                        patient_id,
                        first_name,
                        last_name,
                        date_of_birth,
                        condition,
                        allergy,
                        gp_name,
                        concurrent_medications,
                        polypharmacy_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["patient_id"],
                        row["first_name"],
                        row["last_name"],
                        row["date_of_birth"],

                        row.get(
                            "condition",
                            "",
                        ),

                        row.get(
                            "allergy",
                            "",
                        ),

                        row.get(
                            "gp_name",
                            "",
                        ),

                        row.get(
                            "concurrent_medications",
                            "",
                        ),

                        int(
                            row.get(
                                "polypharmacy_count",
                                0,
                            )
                            or 0
                        ),
                    ),
                )

                insert_prescription(
                    conn=conn,

                    patient_id=
                        row["patient_id"],

                    drug_name=
                        row["drug_name"],

                    drug_class=
                        row["drug_class"],

                    dose_mg=
                        row["dose_mg"],

                    dose_unit=
                        row["dose_unit"],

                    formulation=
                        row["formulation"],

                    manufacturer=
                        row["manufacturer"],

                    route=
                        row["route"],

                    start_date=
                        row["start_date"],

                    prescriber=
                        row["prescriber"],

                    is_current=1,
                )

        print(
            f"Loaded 1 demo patient "
            f"(first-prescription case) from {demo_path}"
        )

    else:

        print(
            "Demo first-prescription fixture "
            "not found; skipping."
        )


    # -------------------------------------------------------------
    # SAVE DATABASE
    # -------------------------------------------------------------

    conn.commit()


    # -------------------------------------------------------------
    # BASIC VALIDATION
    # -------------------------------------------------------------

    n_patients = conn.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    n_prescriptions = conn.execute(
        "SELECT COUNT(*) FROM prescriptions"
    ).fetchone()[0]

    n_high_risk = conn.execute(
        """
        SELECT COUNT(*)
        FROM prescriptions
        WHERE high_risk_flag = 1
        """
    ).fetchone()[0]


    print(
        f"Loaded {n_patients} patients "
        f"and {n_prescriptions} prescriptions "
        f"into {DB_PATH}"
    )

    print(
        f"High-risk medicine prescription "
        f"records: {n_high_risk}"
    )


    conn.close()


if __name__ == "__main__":
    main()
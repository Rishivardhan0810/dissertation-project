import { useState } from "react";
import AlertPanel from "./AlertPanel";

function formatDose(value, unit) {
  return !unit || unit === "mg"
    ? `${value}mg`
    : `${value} ${unit}`;
}

function fmtDate(iso) {
  if (!iso) return "—";

  const d = new Date(iso);

  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function RecordScreen({
  data,
  apiBase,
  onBack,
}) {
  const {
    patient,
    prescriptions,
    alert,
    status,
    status_message,
    medicine_information,
  } = data;

  const [acknowledged, setAcknowledged] = useState(false);
  const [ackBusy, setAckBusy] = useState(false);
  const [pharmacistName, setPharmacistName] = useState("");
  const [dispenseBusy, setDispenseBusy] = useState(false);
  const [dispensed, setDispensed] = useState(false);
  const [medicineSafetyReviewed, setMedicineSafetyReviewed] =
    useState(false);

  const isNoPrescriptions =
    status === "no_prescriptions";

  const isFirstPrescription =
    status === "first_prescription";

  const current =
    prescriptions.length > 0
      ? prescriptions[prescriptions.length - 1]
      : null;

  const medicineInfo = {
    indication:
      medicine_information?.indication ||
      current?.indication ||
      "",

    common_side_effects:
      medicine_information?.common_side_effects ||
      current?.common_side_effects ||
      "",

    counselling:
      medicine_information?.counselling ||
      current?.counselling ||
      "",

    high_risk_flag: Boolean(
      medicine_information?.high_risk_flag ||
        current?.high_risk_flag
    ),

    dispensing_warning:
      medicine_information?.dispensing_warning ||
      current?.dispensing_warning ||
      "",
  };

  const concurrentMedsList = (
    patient.concurrent_medications || ""
  )
    .split(";")
    .map((m) => m.trim())
    .filter(Boolean);

  const changeReviewRequired =
    Boolean(alert) || isFirstPrescription;

  const changeReviewComplete =
    !changeReviewRequired || acknowledged;

  const medicineSafetyComplete =
    !medicineInfo.high_risk_flag ||
    medicineSafetyReviewed;

  const dispenseLocked =
    isNoPrescriptions ||
    !changeReviewComplete ||
    !medicineSafetyComplete;

  const needsInlineDispenseName =
    !alert &&
    !isFirstPrescription &&
    !isNoPrescriptions;

  async function handleAcknowledge() {
    if (!pharmacistName.trim()) return;

    setAckBusy(true);

    try {
      const res = await fetch(
        `${apiBase}/api/acknowledge`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            patient_id: patient.patient_id,
            pharmacist_name: pharmacistName.trim(),
            risk_level: alert.risk_final,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(
          "Acknowledgement could not be logged."
        );
      }

      setAcknowledged(true);
    } catch (error) {
      console.error(error);
    } finally {
      setAckBusy(false);
    }
  }

  async function handleAcknowledgeFirstPrescription() {
    if (!pharmacistName.trim()) return;

    setAckBusy(true);

    try {
      const res = await fetch(
        `${apiBase}/api/acknowledge`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            patient_id: patient.patient_id,
            pharmacist_name: pharmacistName.trim(),
            risk_level: "FIRST_PRESCRIPTION_REVIEW",
          }),
        }
      );

      if (!res.ok) {
        throw new Error(
          "First-prescription review could not be logged."
        );
      }

      setAcknowledged(true);
    } catch (error) {
      console.error(error);
    } finally {
      setAckBusy(false);
    }
  }

  async function handleDispense() {
    if (
      !pharmacistName.trim() ||
      !current ||
      dispenseLocked
    ) {
      return;
    }

    setDispenseBusy(true);

    try {
      const res = await fetch(
        `${apiBase}/api/dispense`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            patient_id: patient.patient_id,
            pharmacist_name: pharmacistName.trim(),
            drug_name: current.drug_name,
            dose_mg: current.dose_mg,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(
          "Dispensing transaction could not be logged."
        );
      }

      setDispensed(true);
    } catch (error) {
      console.error(error);
    } finally {
      setDispenseBusy(false);
    }
  }

  return (
    <div className="record-wrap">

      {/* BACK BUTTON */}

      <div className="record-toolbar">
        <button
          className="btn btn-ghost"
          onClick={onBack}
        >
          &larr; New search
        </button>
      </div>

      {/* PATIENT BANNER - FULL WIDTH */}

      <section className="patient-banner">
        <div>
          <h1>
            {patient.first_name}{" "}
            {patient.last_name}
          </h1>

          <p className="patient-meta">
            DOB {fmtDate(patient.date_of_birth)}
            {" · "}
            Patient ID {patient.patient_id}
            {" · "}
            GP {patient.gp_name}
          </p>
        </div>

        <div className="patient-tags">

          <span className="tag">
            Condition:{" "}
            {patient.condition || "—"}
          </span>

          <span
            className={`tag ${
              patient.allergy &&
              patient.allergy !== "None recorded"
                ? "tag-warn"
                : ""
            }`}
          >
            Allergy:{" "}
            {patient.allergy || "—"}
          </span>

          {patient.polypharmacy_count > 0 && (
            <span className="tag">
              Also on{" "}
              {patient.polypharmacy_count}{" "}
              other medication
              {patient.polypharmacy_count > 1
                ? "s"
                : ""}
            </span>
          )}

        </div>
      </section>

      {/* MAIN + SIDEBAR */}

      <div className="record-content-layout">

        {/* ==============================
            LEFT - MAIN CLINICAL WORKFLOW
            ============================== */}

        <div className="record-main-column">

          {/* CONCURRENT MEDICATIONS */}

          <section className="concurrent-meds-panel">
            <h2>Concurrent medications</h2>

            {concurrentMedsList.length > 0 ? (
              <ul className="concurrent-meds-list">
                {concurrentMedsList.map((med) => (
                  <li key={med}>{med}</li>
                ))}
              </ul>
            ) : (
              <p className="concurrent-meds-empty">
                No concurrent medications recorded.
              </p>
            )}

            <p className="concurrent-meds-note">
              Drug–drug interaction checking is not
              automated in this prototype. Pharmacist
              clinical review is required.
            </p>
          </section>

          {/* PRESCRIPTION CHANGE ALERT */}

          {alert && (
            <AlertPanel
              alert={alert}
              concurrentMedications={
                patient.concurrent_medications
              }
              acknowledged={acknowledged}
              ackBusy={ackBusy}
              pharmacistName={pharmacistName}
              setPharmacistName={setPharmacistName}
              onAcknowledge={handleAcknowledge}
            />
          )}

          {/* FIRST PRESCRIPTION */}

          {isFirstPrescription &&
            !acknowledged && (
              <section
                className="first-rx-panel"
                role="alert"
              >
                <p className="first-rx-title">
                  First prescription &mdash; no
                  previous record available
                </p>

                <p className="first-rx-explain">
                  {status_message}
                </p>

                <div className="alert-ack-row">

                  <label className="field field-inline">
                    <span>Your name</span>

                    <input
                      value={pharmacistName}
                      onChange={(e) =>
                        setPharmacistName(
                          e.target.value
                        )
                      }
                      placeholder="Pharmacist name"
                    />
                  </label>

                  <button
                    className="btn btn-acknowledge"
                    disabled={
                      !pharmacistName.trim() ||
                      ackBusy
                    }
                    onClick={
                      handleAcknowledgeFirstPrescription
                    }
                  >
                    {ackBusy
                      ? "Logging…"
                      : "First prescription reviewed"}
                  </button>

                </div>
              </section>
            )}

          {isFirstPrescription &&
            acknowledged && (
              <section className="first-rx-resolved">

                <span
                  className="alert-resolved-icon"
                  aria-hidden="true"
                >
                  &#10003;
                </span>

                <div>
                  <p className="alert-resolved-title">
                    First prescription reviewed
                  </p>

                  <p className="alert-resolved-sub">
                    Logged for {pharmacistName}
                    {" · "}
                    Dispense is now unlocked.
                  </p>
                </div>

              </section>
            )}

          {/* NO PRESCRIPTIONS */}

          {isNoPrescriptions && (
            <section className="no-rx-panel">
              {status_message}
            </section>
          )}

          {/* PRESCRIPTION DETAILS */}

          {current && (
            <section className="rx-panel">

              <h2>Current EPS prescription</h2>

              <div style={{ overflowX: "auto" }}>
                <table className="rx-table">
                  <thead>
                    <tr>
                      <th>Drug</th>
                      <th>Class</th>
                      <th>Dose</th>
                      <th>Formulation</th>
                      <th>Route</th>
                      <th>Manufacturer</th>
                      <th>Start date</th>
                    </tr>
                  </thead>

                  <tbody>
                    <tr>
                      <td>{current.drug_name}</td>
                      <td>{current.drug_class}</td>

                      <td>
                        {formatDose(
                          current.dose_mg,
                          current.dose_unit
                        )}
                      </td>

                      <td>{current.formulation}</td>
                      <td>{current.route}</td>
                      <td>{current.manufacturer}</td>

                      <td>
                        {fmtDate(current.start_date)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h2 className="rx-history-heading">
                Prescription history
              </h2>

              <div style={{ overflowX: "auto" }}>
                <table className="rx-table rx-table-history">

                  <thead>
                    <tr>
                      <th>Drug</th>
                      <th>Class</th>
                      <th>Dose</th>
                      <th>Formulation</th>
                      <th>Route</th>
                      <th>Manufacturer</th>
                      <th>Start date</th>
                    </tr>
                  </thead>

                  <tbody>
                    {[...prescriptions]
                      .reverse()
                      .map((rx) => (
                        <tr
                          key={rx.prescription_id}
                          className={
                            rx.is_current
                              ? "row-current"
                              : ""
                          }
                        >
                          <td>{rx.drug_name}</td>
                          <td>{rx.drug_class}</td>

                          <td>
                            {formatDose(
                              rx.dose_mg,
                              rx.dose_unit
                            )}
                          </td>

                          <td>{rx.formulation}</td>
                          <td>{rx.route}</td>
                          <td>{rx.manufacturer}</td>

                          <td>
                            {fmtDate(rx.start_date)}
                            {rx.is_current
                              ? " (current)"
                              : ""}
                          </td>
                        </tr>
                      ))}
                  </tbody>

                </table>
              </div>

            </section>
          )}

          {/* HIGH-RISK MEDICINE CHECK
              Remains in main workflow near Dispense */}

          {medicineInfo.high_risk_flag && (
            <section
              role="alert"
              style={{
                background: "#fff4e5",
                border: "1px solid #e5a23c",
                borderRadius: "10px",
                padding: "16px 18px",
              }}
            >
              <strong>
                Additional medicine safety check
              </strong>

              <p
                style={{
                  margin: "8px 0 12px",
                  fontSize: "13.5px",
                  lineHeight: "1.5",
                }}
              >
                {medicineInfo.dispensing_warning ||
                  "Additional pharmacist review is required before dispensing this medicine."}
              </p>

              {!medicineSafetyReviewed ? (
                <button
                  type="button"
                  className="btn btn-acknowledge"
                  onClick={() =>
                    setMedicineSafetyReviewed(true)
                  }
                >
                  Safety check completed
                </button>
              ) : (
                <p
                  style={{
                    margin: 0,
                    fontWeight: "600",
                    color: "#146c4d",
                  }}
                >
                  &#10003; Safety check completed
                </p>
              )}
            </section>
          )}

          {/* DISPENSE */}

          {!isNoPrescriptions && (
            <section className="dispense-panel">

              {dispensed ? (
                <p className="dispense-confirm">
                  <span aria-hidden="true">
                    &#10003;
                  </span>

                  {" "}
                  Dispensed by{" "}
                  {pharmacistName.trim()}
                  {" · "}
                  {current.drug_name}
                  {" "}
                  {formatDose(
                    current.dose_mg,
                    current.dose_unit
                  )}
                  {" logged for "}
                  {patient.first_name}
                  {" "}
                  {patient.last_name}.
                </p>
              ) : (
                <>

                  {needsInlineDispenseName && (
                    <label className="field field-inline">
                      <span>
                        Pharmacist name
                      </span>

                      <input
                        value={pharmacistName}
                        onChange={(e) =>
                          setPharmacistName(
                            e.target.value
                          )
                        }
                        placeholder="Pharmacist name"
                      />
                    </label>
                  )}

                  <button
                    className="btn btn-dispense"
                    disabled={
                      dispenseLocked ||
                      !pharmacistName.trim() ||
                      dispenseBusy
                    }
                    title={
                      !changeReviewComplete
                        ? "Review and acknowledge the prescription change first"
                        : !medicineSafetyComplete
                        ? "Complete the medicine safety check first"
                        : !pharmacistName.trim()
                        ? "Enter pharmacist name"
                        : ""
                    }
                    onClick={handleDispense}
                  >
                    {dispenseLocked
                      ? "Dispense (review required)"
                      : dispenseBusy
                      ? "Logging…"
                      : "Dispense"}
                  </button>

                </>
              )}

              <p className="dispense-hint">
                Barcode scan on collection verifies
                that the medicine box matches the
                current prescription. Prescription
                changes are reviewed above.
              </p>

            </section>
          )}

        </div>

        {/* ==============================
            RIGHT - MEDICINE SIDEBAR
            ============================== */}

        {current && (
          <aside className="medicine-sidebar">

            <p className="medicine-sidebar-label">
              Medicine information
            </p>

            <h2>{current.drug_name}</h2>

            {medicineInfo.indication && (
              <div className="medicine-sidebar-item">
                <strong>Used for</strong>

                <p>
                  {medicineInfo.indication}
                </p>
              </div>
            )}

            {medicineInfo.common_side_effects && (
              <div className="medicine-sidebar-item">
                <strong>
                  Common side effects
                </strong>

                <p>
                  {
                    medicineInfo.common_side_effects
                  }
                </p>
              </div>
            )}

            {medicineInfo.counselling && (
              <div className="medicine-sidebar-item">
                <strong>
                  Patient counselling
                </strong>

                <p>
                  {medicineInfo.counselling}
                </p>
              </div>
            )}

            <p className="medicine-sidebar-note">
              Reference information to support
              pharmacist counselling. Clinical
              judgement remains with the pharmacist.
            </p>

          </aside>
        )}

      </div>

    </div>
  );
}
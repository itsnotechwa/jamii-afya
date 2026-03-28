// src/pages/NewClaim.jsx
import { useState, useEffect } from "react";
import { useClaims } from "../hooks/useClaims";           
import { submitClaim } from "../api/claims";              
import Spinner from "../components/LoadingSpinner";
import { useAuth } from "../hooks/useAuth";        
import { getHospitals } from "../api/hospitals";  
import { useNavigate } from "react-router-dom";     

// ──────────────────────────────────────────────────────────────────────
// NEW CLAIM PAGE
// ──────────────────────────────────────────────────────────────────────
export default function NewClaimPage() {
  const navigate = useNavigate();
  const [snack, setSnack] = useState({ msg: "", type: "" });
  const showSnack = (msg, type) => setSnack({ msg, type });
  /* -------------------------------------------------
    we keep the claim‑list hook so we can
    refresh the home‑page after a successful submit.
   ------------------------------------------------- */
  const { refetch: refetchClaims } = useClaims();   

  // Form state
  const [form, setForm] = useState({ hospital: "", amount: "", desc: "" });
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [errors, setErrors] = useState({});

  // Renamed to avoid colliding with the `loading` flag that could come
  // from `useClaims` (if you ever decide to keep it here).
  const [submitting, setSubmitting] = useState(false);

  // Validation
  const validate = () => {
    const e = {};
    if (!form.hospital) e.hospital = "Select a hospital";
    if (
      !form.amount ||
      isNaN(form.amount) ||
      Number(form.amount) < 1000
    )
      e.amount = "Enter a valid amount (min KES 1,000)";
    if (!file) e.file = "Attach a hospital bill";
    return e;
  };

  // Get Approved hospitals data
  const [hospitals, setHospitals] = useState([]);

  useEffect(() => {
    getHospitals().then(setHospitals).catch(() => {});
  }, []);

  // -----------------------------------------------------------------
  // Real submit handler – async, calls the API, shows spinner,
  // handles success / error, then resets UI.
  // -----------------------------------------------------------------
  const submit = async () => {
    const e = validate();
    if (Object.keys(e).length) {
      setErrors(e);
      return;
    }

    setSubmitting(true);
    setErrors({}); // clear previous UI errors

    try {
      // Prepare payload for the API (match the shape expected in claims.js)
      const payload = {
        hospital: form.hospital,
        amount:   Number(form.amount),   // API expects a number, not a string
        desc:     form.desc,
        file,                           // the File object selected by the user
      };

      // ----‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑‑-
      // Call the back‑end. The function throws on non‑2xx, so we
      // catch the error in the `catch` block below.
      // ---------------------------------------------------------
      await submitClaim(payload);

      // Success UI
      showSnack(
        `Claim #${Math.floor(Math.random() * 1000)} submitted! You’ll be notified when verified.`,
        "success"
      );

      // If you keep the list hook, refresh the home‑page data
      refetchClaims?.();

      // Move the user to the history page (or wherever you like)
      navigate("/history");
    } catch (err) {
      // Show the error returned by the back‑end or a generic fallback
      showSnack(err.message || "Failed to submit claim. Please try again.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  // -----------------------------------------------------------------
  // File handling (drag‑and‑drop or click‑to‑browse)
  // -----------------------------------------------------------------
  const handleFile = (f) => {
    if (f && (f.type === "application/pdf" || f.type.startsWith("image/"))) {
      setFile(f);
      setErrors((e) => ({ ...e, file: "" }));
    }
  };

  // -----------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Request Emergency Assistance</div>
          <div className="page-subtitle">
            Submit a verified claim to receive community support
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 600 }}>
        <div className="card" style={{ padding: 28 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* ---------- Hospital selector ---------- */}
            <div className="field">
              <label>Hospital *</label>
              <select
                className={`field-input ${errors.hospital ? "error" : ""}`}
                value={form.hospital}
                onChange={(e) =>
                  setForm({ ...form, hospital: e.target.value })
                }
              >
                <option value="">Select hospital…</option>
                {hospitals.map((h) => (
                  <option key={h.id} value={h.name}>
                    {h.name}
                  </option>
                ))}
              </select>
              {errors.hospital && (
                <span className="field-error">{errors.hospital}</span>
              )}
            </div>

            {/* ---------- Amount ---------- */}
            <div className="field">
              <label>Amount Required (KES) *</label>
              <div
                className={`field-prefix ${errors.amount ? "error" : ""}`}
                style={errors.amount ? { borderColor: "var(--red)" } : {}}
              >
                <span className="prefix-label">KES</span>
                <input
                  className="prefix-input"
                  type="number"
                  placeholder="e.g. 80000"
                  value={form.amount}
                  onChange={(e) =>
                    setForm({ ...form, amount: e.target.value })
                  }
                  min="1000"
                />
              </div>
              {errors.amount && (
                <span className="field-error">{errors.amount}</span>
              )}
            </div>

            {/* ---------- Description (optional) ---------- */}
            <div className="field">
              <label>Case Description (optional)</label>
              <textarea
                className="field-input"
                rows={3}
                placeholder="Brief description of the medical emergency…"
                value={form.desc}
                onChange={(e) =>
                  setForm({ ...form, desc: e.target.value })
                }
                style={{ resize: "vertical" }}
              />
            </div>

            {/* ---------- Bill upload ---------- */}
            <div className="field">
              <label>Hospital Bill (PDF or image) *</label>
              {file ? (
                <div className="file-preview">
                  <span style={{ fontSize: "1.2rem" }}>📄</span>
                  <span className="file-name">{file.name}</span>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setFile(null)}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div
                  className={`upload-zone ${drag ? "dragover" : ""}`}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDrag(true);
                  }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDrag(false);
                    handleFile(e.dataTransfer.files[0]);
                  }}
                  onClick={() =>
                    document.getElementById("bill-upload").click()
                  }
                >
                  <div style={{ fontSize: "2rem", marginBottom: 8 }}>📁</div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>
                    Drag &amp; drop your bill here
                  </div>
                  <div
                    style={{
                      fontSize: ".82rem",
                      color: "var(--ink-muted)",
                    }}
                  >
                    or click to browse · PDF or image
                  </div>
                  <input
                    id="bill-upload"
                    type="file"
                    accept=".pdf,image/*"
                    style={{ display: "none" }}
                    onChange={(e) => handleFile(e.target.files[0])}
                  />
                </div>
              )}
              {errors.file && (
                <span className="field-error">{errors.file}</span>
              )}
            </div>

            {/* ---------- Submit button ---------- */}
            <button
              className="btn btn-primary btn-full btn-lg"
              onClick={submit}
              disabled={submitting}
              style={{ marginTop: 4 }}
            >
              {submitting ? (
                <>
                  <Spinner /> Submitting Claim…
                </>
              ) : (
                "Submit Claim"
              )}
            </button>

            {/* ---------- Helper text ---------- */}
            <p
              style={{
                fontSize: ".78rem",
                color: "var(--ink-muted)",
                textAlign: "center",
              }}
            >
              Claims are reviewed by the group administrator and two community
              members. You'll receive an SMS confirmation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// src/pages/NewClaim.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useClaims } from "../hooks/useClaims";
import { submitClaim } from "../api/emergencies";
import { getHospitals } from "../api/hospitals";
import { useSnack } from "../context/SnackContext";
import Spinner from "../components/LoadingSpinner";

export default function NewClaimPage() {
  const navigate    = useNavigate();
  const showSnack   = useSnack();                          // from Layout context
  const { refetch: refetchClaims } = useClaims();

  const [form,       setForm]       = useState({ hospital: "", amount: "", desc: "" });
  const [file,       setFile]       = useState(null);
  const [drag,       setDrag]       = useState(false);
  const [errors,     setErrors]     = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [hospitals,  setHospitals]  = useState([]);

  useEffect(() => {
    getHospitals().then(setHospitals).catch(() => {});
  }, []);

  const validate = () => {
    const e = {};
    if (!form.hospital) e.hospital = "Select a hospital";
    if (!form.amount || isNaN(form.amount) || Number(form.amount) < 1000)
      e.amount = "Enter a valid amount (min KES 1,000)";
    if (!file) e.file = "Attach a hospital bill";
    return e;
  };

  const submit = async () => {
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }

    setSubmitting(true);
    setErrors({});

    try {
      await submitClaim({
        hospital: form.hospital,
        amount:   Number(form.amount),
        desc:     form.desc,
        file,
      });

      showSnack("Claim submitted! You'll be notified when verified.", "success");
      refetchClaims?.();
      navigate("/history");
    } catch (err) {
      showSnack(err.message || "Failed to submit claim. Please try again.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleFile = (f) => {
    if (f && (f.type === "application/pdf" || f.type.startsWith("image/"))) {
      setFile(f);
      setErrors((e) => ({ ...e, file: "" }));
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Request Emergency Assistance</div>
          <div className="page-subtitle">Submit a verified claim to receive community support</div>
        </div>
      </div>

      <div style={{ maxWidth: 600 }}>
        <div className="card" style={{ padding: 28 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* Hospital */}
            <div className="field">
              <label htmlFor="hospital-select">Hospital *</label>
              <select
                id="hospital-select"
                className={`field-input ${errors.hospital ? "error" : ""}`}
                value={form.hospital}
                onChange={(e) => setForm({ ...form, hospital: e.target.value })}
                aria-required="true"
                aria-describedby={errors.hospital ? "hospital-err" : undefined}
              >
                <option value="">Select hospital…</option>
                {hospitals.map((h) => (
                  <option key={h.id} value={h.name}>{h.name}</option>
                ))}
              </select>
              {errors.hospital && (
                <span id="hospital-err" className="field-error" role="alert">{errors.hospital}</span>
              )}
            </div>

            {/* Amount */}
            <div className="field">
              <label htmlFor="amount-input">Amount Required (KES) *</label>
              <div
                className={`field-prefix ${errors.amount ? "error" : ""}`}
                style={errors.amount ? { borderColor: "var(--red)" } : {}}
              >
                <span className="prefix-label">KES</span>
                <input
                  id="amount-input"
                  className="prefix-input"
                  type="number"
                  placeholder="e.g. 80000"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                  min="1000"
                  aria-required="true"
                  aria-describedby={errors.amount ? "amount-err" : undefined}
                />
              </div>
              {errors.amount && (
                <span id="amount-err" className="field-error" role="alert">{errors.amount}</span>
              )}
            </div>

            {/* Description */}
            <div className="field">
              <label htmlFor="desc-input">Case Description (optional)</label>
              <textarea
                id="desc-input"
                className="field-input"
                rows={3}
                placeholder="Brief description of the medical emergency…"
                value={form.desc}
                onChange={(e) => setForm({ ...form, desc: e.target.value })}
                style={{ resize: "vertical" }}
              />
            </div>

            {/* File upload */}
            <div className="field">
              <label>Hospital Bill (PDF or image) *</label>
              {file ? (
                <div className="file-preview">
                  <span style={{ fontSize: "1.2rem" }}>📄</span>
                  <span className="file-name">{file.name}</span>
                  <button className="btn btn-ghost btn-sm" onClick={() => setFile(null)}>
                    Remove
                  </button>
                </div>
              ) : (
                <div
                  className={`upload-zone ${drag ? "dragover" : ""}`}
                  role="button"
                  tabIndex={0}
                  aria-label="Upload hospital bill — click or drag a PDF or image"
                  onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={(e) => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0]); }}
                  onClick={() => document.getElementById("bill-upload").click()}
                  onKeyDown={(e) => e.key === "Enter" && document.getElementById("bill-upload").click()}
                >
                  <div style={{ fontSize: "2rem", marginBottom: 8 }}>📁</div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>Drag &amp; drop your bill here</div>
                  <div style={{ fontSize: ".82rem", color: "var(--ink-muted)" }}>
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
                <span className="field-error" role="alert">{errors.file}</span>
              )}
            </div>

            {/* Submit */}
            <button
              className="btn btn-primary btn-full btn-lg"
              onClick={submit}
              disabled={submitting}
              style={{ marginTop: 4 }}
            >
              {submitting ? <><Spinner /> Submitting Claim…</> : "Submit Claim"}
            </button>

            <p style={{ fontSize: ".78rem", color: "var(--ink-muted)", textAlign: "center" }}>
              Claims are reviewed by the group administrator and two community members.
              You'll receive an SMS confirmation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
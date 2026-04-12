// src/pages/Home.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useClaims } from "../hooks/useClaims";
import { fmt, pct } from "../helpers";              
import StatusChip from "../components/StatusChip";
import ProgressBar from "../components/ProgressBar";
import Snackbar from "../components/SnackBar";
import LoadingSpinner from "../components/LoadingSpinner";

export default function HomePage() {
  /* ----------  Hook ------------------------------------------------- */
  const { claims, loading, error, refetch } = useClaims();

  const navigate = useNavigate();
  /* ----------------------------------------------------------------- */

  const [snack, setSnack]       = useState({ msg: "", type: "" });

  /* ----------  Loading UI ------------------------------------------ */
  if (loading) {
    return (
      <div
        className="page"
        style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}
      >
        <LoadingSpinner dark />
      </div>
    );
  }

  /* ----------  Error UI -------------------------------------------- */
  if (error) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-title">Could not load claims</div>
          <div className="empty-state-sub">{error}</div>
          <button
            className="btn btn-outline"
            style={{ marginTop: 16 }}
            onClick={refetch}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  /* ----------  Empty‑state when there are zero claims -------------- */
  if (claims.length === 0) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">🩺</div>
          <div className="empty-state-title">No active emergencies yet</div>
          <div className="empty-state-sub">
            Be the first to submit a claim or check back later.
          </div>
          <button
            className="btn btn-primary"
            style={{ marginTop: 16 }}
            onClick={() => navigate("/claims/new")}
          >
            + Submit a Claim
          </button>
        </div>
      </div>
    );
  }

  /* ----------  Main UI ------------------------------------------- */
  return (
    <div className="page">
      {/* ---------- Banner ---------------------------------------- */}
      <div className="banner">
        <div>
          <div
            className="banner-text"
            style={{ fontWeight: 700, marginBottom: 2 }}
          >
            Active Medical Emergencies
          </div>
          {/* use the live data, not a static constant */}
          <div style={{ fontSize: ".82rem", opacity: 0.85 }}>
            {claims.filter((c) => c.status === "approved").length} cases need
            your help today
          </div>
        </div>
        <button
          className="banner-cta"
          onClick={() => navigate("/claims/new")}
        >
          + Submit a Claim →
        </button>
      </div>

      {/* ---------- Stats row -------------------------------------- */}
      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-label">Total Needed</div>
          <div className="stat-value blue">
            {fmt(claims.reduce((s, c) => s + c.amount, 0))}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Raised Today</div>
          <div className="stat-value green">
            {fmt(claims.reduce((s, c) => s + c.funded, 0))}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Active Claims</div>
          <div className="stat-value orange">
            {claims.filter((c) => c.status === "approved").length}
          </div>
        </div>

        <div className="stat-card" title="Active emergencies with some funds approved toward the goal">
          <div className="stat-label">Receiving funds</div>
          <div className="stat-value">
            {claims.filter((c) => (Number(c.funded) || 0) > 0).length}
          </div>
        </div>
      </div>

      {/* ---------- Page header ------------------------------------ */}
      <div className="page-header">
        <div>
          <div className="page-title">Active Claims</div>
          <div className="page-subtitle">
            Verified by Jamii-Afya administrators
          </div>
        </div>
      </div>

      {/* ---------- Claims grid ------------------------------------ */}
      <div className="claims-grid">
        {claims.map((claim) => {
          const p = pct(claim.funded, claim.amount);
          return (
            <div key={claim.id} className="card claim-card">
              <div className="claim-card-inner">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: 8,
                  }}
                >
                  <div className="claim-hospital">{claim.hospital}</div>
                  <div style={{ display: "flex", gap: 6 }}>
                    {claim.urgent && <StatusChip status="urgent" />}
                    <StatusChip status={claim.status} />
                  </div>
                </div>

                <div className="claim-amount">{fmt(claim.amount)}</div>
                <div className="claim-desc">{claim.desc}</div>

                <ProgressBar value={p} urgent={claim.urgent} />

                <div
                  style={{
                    fontSize: ".8rem",
                    color: "var(--ink-muted)",
                    marginTop: 8,
                  }}
                >
                  {fmt(claim.funded)} raised ·{" "}
                  {fmt(claim.amount - claim.funded)} to go
                </div>
              </div>

              <div className="claim-actions">
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => navigate(`/claims/${claim.id}`)}
                >
                  View Details
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* ---------- Snackbar for toast messages -------------------- */}
      <Snackbar
        msg={snack.msg}
        type={snack.type}
        onClose={() => setSnack({ msg: "", type: "" })}
      />
    </div>
  );
}

// src/pages/ClaimDetail.jsx
import { useParams, useNavigate } from "react-router-dom";
import { useClaimDetail } from "../hooks/useClaims";
import { fmt, pct, absoluteApiUrl } from "../helpers";
import StatusChip      from "../components/StatusChip";
import ProgressBar     from "../components/ProgressBar";
import CircularProgress from "../components/CircularProgress";
import LoadingSpinner  from "../components/LoadingSpinner";

export default function ClaimDetail() {
  const { claimId }  = useParams();
  const navigate     = useNavigate();
  const { claim, loading, error, refetch } = useClaimDetail(claimId);

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="page" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <LoadingSpinner dark />
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (error || !claim) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-title">Could not load claim</div>
          <div className="empty-state-sub">{error ?? "Claim not found."}</div>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", marginTop: 16 }}>
            <button className="btn btn-ghost" onClick={() => navigate("/")}>← Home</button>
            <button className="btn btn-outline" onClick={refetch}>Retry</button>
          </div>
        </div>
      </div>
    );
  }

  const p = pct(claim.funded, claim.amount);

  // ── Main ───────────────────────────────────────────────────────────────────
  return (
    <div className="page" style={{ paddingBottom: 90 }}>
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <span className="breadcrumb-link" onClick={() => navigate("/")}>Home</span>
        <span className="breadcrumb-sep">›</span>
        <span>{claim.hospital}</span>
        <span className="breadcrumb-sep">›</span>
        <span>Claim #{claim.id}</span>
      </div>

      {/* Header */}
      <div className="detail-header">
        <div>
          <div className="detail-title">{claim.hospital}</div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <StatusChip status={claim.status} />
            {claim.urgent && <StatusChip status="urgent" />}
          </div>
        </div>
        <CircularProgress value={p} />
      </div>

      {/* Two-column grid */}
      <div className="detail-grid">
        {/* Left column */}
        <div>
          {/* Amounts card */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div style={{ padding: "20px 20px 16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
                <div>
                  <div style={{ fontSize: ".8rem", color: "var(--ink-muted)", marginBottom: 4 }}>Total Required</div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", color: "var(--ink)" }}>
                    {fmt(claim.amount)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: ".8rem", color: "var(--ink-muted)", marginBottom: 4 }}>Funded So Far</div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", color: "var(--green)" }}>
                    {fmt(claim.funded)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: ".8rem", color: "var(--ink-muted)", marginBottom: 4 }}>Remaining</div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", color: "var(--orange)" }}>
                    {fmt(claim.amount - claim.funded)}
                  </div>
                </div>
              </div>
              <ProgressBar value={p} urgent={claim.urgent} />
            </div>
          </div>

          {/* Case description card */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div style={{ padding: 20 }}>
              <div style={{ fontWeight: 700, marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
                <span>📋</span> Case Description
              </div>
              <p style={{ fontSize: ".9rem", color: "var(--ink-secondary)", lineHeight: 1.7 }}>
                {claim.desc}
              </p>
              <div style={{ marginTop: 14, padding: "10px 14px", background: "var(--surface-2)", borderRadius: "var(--radius-sm)", fontSize: ".82rem", color: "var(--ink-muted)", lineHeight: 1.5 }}>
                {claim.paybill ? (
                  <>
                    Chama collection (paybill / till):{' '}
                    <strong style={{ color: "var(--ink)" }}>{claim.paybill}</strong>
                    {' '}· Set by your group admin for manual M-Pesa payments.
                  </>
                ) : (
                  <>
                    No group paybill is configured for this case. Pool funding uses your{' '}
                    <strong style={{ color: "var(--ink)" }}>monthly chama contribution</strong> (M-Pesa STK from History or the banner), not per-claim crowdfunding on this screen.
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="pdf-mock">
              <div style={{ fontSize: "2.5rem" }}>📄</div>
              <div style={{ fontWeight: 600, fontSize: ".9rem" }}>Hospital Bill</div>
              <div style={{ fontSize: ".8rem", color: "var(--ink-muted)", textAlign: "center" }}>
                PDF document attached<br />Verified by Jamii-Afya
              </div>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={!claim.documents?.length}
                onClick={() => {
                  const u = absoluteApiUrl(claim.documents[0]?.file);
                  if (u) window.open(u, '_blank', 'noopener,noreferrer');
                }}
              >
                {claim.documents?.length ? 'View bill document' : 'No bill uploaded'}
              </button>
            </div>
          </div>


        </div>
      </div>

      <div className="sticky-donate">
        <button className="btn btn-ghost" onClick={() => navigate("/")}>← Back</button>
      </div>
    </div>
  );
}
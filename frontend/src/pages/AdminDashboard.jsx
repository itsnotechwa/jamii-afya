import { useState } from "react";
import { useAdmin } from "../hooks/useAdmin";
import { fmt, absoluteApiUrl } from "../helpers";
import ConfirmModal from "../components/ConfirmModal";
import LoadingSpinner from "../components/LoadingSpinner";
import { useSnack } from "../context/SnackContext";


// ------ ADMIN PAGE ----------
export default function AdminPage() {
  const { pending, loading, error, actionId, approve, refetch } = useAdmin(); 
  const showSnack = useSnack();

  const [confirming, setConfirming] = useState(null);
  const [viewPdf, setViewPdf] = useState(null);

  const handleApprove = async () => {
    try {
      await approve(confirming);
      showSnack(`Request approved. ${fmt(confirming.amount)} is being sent to ${confirming.member}.`);
    } catch {
      showSnack("Approval failed. Please try again.", "error");
    } finally {
      setConfirming(null);
    }
  };

  // -------- Loading ---------
  if (loading) {
    return (
        <div className="page" style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <LoadingSpinner dark />
      </div>
    );
  }

  // --------- Error ----------
  if (error) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-title">Could not load pending claims</div>
          <div className="empty-state-sub">{error}</div>
          <button className="btn btn-outline" style={{ marginTop: 16 }} onClick={refetch}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  // -----Main-----
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Admin Dashboard</div>
          <div className="page-subtitle">Pending claims awaiting verification</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="chip chip-pending">
            <span className="chip-dot" />{pending.length} pending
          </span>
        </div>
      </div>

      {/* ------- Table -------*/}
      {pending.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <div className="empty-state-title">All caught up!</div>
          <div className="empty-state-sub">No pending claims at this time.</div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Claim ID</th>
                <th>Hospital</th>
                <th>Patient</th>
                <th>Amount</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((c) => (
                <tr key={c.id}>
                  <td><span style={{ fontWeight: 700, color: "var(--blue)" }}>#{c.id}</span></td>
                  <td style={{ fontWeight: 600 }}>{c.hospital}</td>
                  <td style={{ color: "var(--ink-secondary)" }}>{c.patient}</td>
                  <td style={{ fontFamily: "var(--font-display)", fontSize: "1rem" }}>{fmt(c.amount)}</td>
                  <td><span style={{ color: "var(--ink-muted)", fontSize: ".82rem" }}>{c.submitted_ago}</span></td>
                  <td>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => setViewPdf(c)}>View Bill</button>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setConfirming(c)}
                        disabled={actionId === c.id}
                      >
                        {actionId === c.id ? <><LoadingSpinner /> Processing…</> : "Approve →"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {confirming && (
        <ConfirmModal
          title={`Approve Claim #${confirming.id}`}
          message={`Approving this request will release ${fmt(confirming.amount)} 
          from the group till to ${confirming.member} via M-Pesa.`
          }
          onConfirm={handleApprove}
          onClose={() => setConfirming(null)}
          loading={actionId === confirming?.id}
        />
      )}

      {viewPdf && (
        <div className="modal-backdrop" onClick={() => setViewPdf(null)}>
          <div className="modal" style={{ maxWidth: 480 }}>
            <div className="modal-header">
              <div className="modal-title">Bill – {viewPdf.hospital} #{viewPdf.id}</div>
              <button className="modal-close" onClick={() => setViewPdf(null)}>✕</button>
            </div>
            <div className="pdf-mock" style={{ height: 320 }}>
              <div style={{ fontSize: "3rem" }}>📄</div>
              <div style={{ fontWeight: 600 }}>Hospital Bill Document</div>
              <div style={{ fontSize: ".82rem", color: "var(--ink-muted)", textAlign: "center" }}>
                Claim #{viewPdf.id} · {viewPdf.patient}<br />Amount: {fmt(viewPdf.amount)}
              </div>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={!viewPdf.documents?.length}
                onClick={() => {
                  const u = absoluteApiUrl(viewPdf.documents[0]?.file);
                  if (u) window.open(u, '_blank', 'noopener,noreferrer');
                }}
              >
                {viewPdf.documents?.length ? 'Open bill document' : 'No document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

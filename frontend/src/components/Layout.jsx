// src/components/Layout.jsx
import { useState, useCallback, useEffect } from "react";
import { getSchedule, getMyContributions } from "../api/contributions";
import ContributeModal from "./ModalContribute";
import { fmt } from "../helpers";
import Navbar from './NavBar';
import Snackbar from './SnackBar';
import { SnackContext } from '../context/SnackContext';

export default function Layout({ children }) {
  const [snack,    setSnack]    = useState({ msg: "", type: "" });
  const [overdue,  setOverdue]  = useState(false);
  const [schedule, setSchedule] = useState(null);
  const [showContribute, setShowContribute] = useState(false);

  const showSnack = useCallback(
    (msg, type = "success") => setSnack({ msg, type }),
    []
  );

  useEffect(() => {
    // Check if the current user has an unpaid contribution past the deadline
    Promise.all([getSchedule(), getMyContributions()])
      .then(([sched, contribs]) => {
        setSchedule(sched);
        const hasOverdue = contribs.some(c => c.status === "overdue");
        setOverdue(hasOverdue);
      })
      .catch(() => {}); // silent — don't block the app if this fails
  }, []);

  return (
    <SnackContext.Provider value={showSnack}>
      <div className="app-shell">
        <Navbar />

        {/* Overdue contribution banner — persists until paid */}
        {overdue && (
          <div style={{
            background: "var(--red)",
            color: "#fff",
            padding: "12px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 16,
            fontSize: "var(--text-sm)",
            fontWeight: 600,
          }}>
            <span>
              ⚠️ Your {schedule?.period} contribution of{" "}
              {fmt(schedule?.amount)} is overdue.
            </span>
            <button
              className="btn btn-xs"
              style={{ background: "#fff", color: "var(--red)", fontWeight: 700 }}
              onClick={() => setShowContribute(true)}
            >
              Pay Now
            </button>
          </div>
        )}

        <main style={{ flex: 1 }}>
          {children}
        </main>
      </div>

      {showContribute && (
        <ContributeModal
          schedule={schedule}
          onClose={() => {
            setShowContribute(false);
            // Re-check overdue status after payment
            getMyContributions()
              .then(contribs => setOverdue(contribs.some(c => c.status === "overdue")))
              .catch(() => {});
          }}
        />
      )}

      <Snackbar
        msg={snack.msg}
        type={snack.type}
        onClose={() => setSnack({ msg: "", type: "" })}
      />
    </SnackContext.Provider>
  );
}
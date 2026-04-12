// src/components/Layout.jsx
import { useState, useCallback, useEffect } from "react";
import { getSchedule, getMyContributions } from "../api/contributions";
import ContributeModal from "./ModalContribute";
import { fmt } from "../helpers";
import Navbar from './NavBar';
import Snackbar from './SnackBar';
import { SnackContext } from '../context/SnackContext';
import { ContributionPayContext } from '../context/ContributionPayContext';
import { needsContributionPayment } from '../utils/contributionPay';

export default function Layout({ children }) {
  const [snack,    setSnack]    = useState({ msg: "", type: "" });
  const [showPayBanner, setShowPayBanner] = useState(false);
  const [schedule, setSchedule] = useState(null);
  const [showContribute, setShowContribute] = useState(false);

  const showSnack = useCallback(
    (msg, type = "success") => setSnack({ msg, type }),
    []
  );

  useEffect(() => {
    Promise.all([getSchedule(), getMyContributions()])
      .then(([sched, contribs]) => {
        setSchedule(sched);
        setShowPayBanner(needsContributionPayment(sched, contribs));
      })
      .catch(() => {}); // silent — no group / API error: hide banner
  }, []);

  return (
    <SnackContext.Provider value={showSnack}>
      <ContributionPayContext.Provider value={{ openPayModal: () => setShowContribute(true) }}>
        <div className="app-shell">
          <Navbar />

          {/* Chama contribution — M-Pesa STK (opens ModalContribute) */}
          {showPayBanner && (
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
                ⚠️ Your {schedule?.period} contribution ({fmt(schedule?.amount)}) — pay with M-Pesa to stay current.
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
              Promise.all([getSchedule(), getMyContributions()])
                .then(([sched, contribs]) => {
                  setSchedule(sched);
                  setShowPayBanner(needsContributionPayment(sched, contribs));
                })
                .catch(() => {});
            }}
          />
        )}

        <Snackbar
          msg={snack.msg}
          type={snack.type}
          onClose={() => setSnack({ msg: "", type: "" })}
        />
      </ContributionPayContext.Provider>
    </SnackContext.Provider>
  );
}
// src/hooks/useAdmin.js
// ─────────────────────────────────────────────────────────────────────────────
// Admin dashboard state: pending claims list + approve / reject mutations.
// Optimistically removes approved/rejected claims from local state so
// the UI responds instantly without a full refetch.
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useEffect, useCallback } from "react";
import { useAuth } from "./useAuth";
import { getClaims, approveClaim, rejectClaim } from "../api/emergencies";

export function useAdmin() {
  const { token } = useAuth();
  const [pending,  setPending]  = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);
  const [actionId, setActionId] = useState(null); // claim being processed

  // ── Fetch pending claims ───────────────────────────────────────────────────
  // Backend should filter to status=pending when role=admin.
  // Alternatively use /api/claims/?status=pending
  const fetchPending = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const all = await getClaims();
      setPending(all.filter((c) => c.status === "pending"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchPending(); }, [fetchPending]);

  // ── Approve ────────────────────────────────────────────────────────────────
  const approve = useCallback(async (claim) => {
    setActionId(claim.id);
    try {
      await approveClaim(claim.id);
      // Optimistic remove — don't wait for a refetch
      setPending((prev) => prev.filter((c) => c.id !== claim.id));
    } catch (err) {
      setError(err.message);
      throw err; // let the modal surface it
    } finally {
      setActionId(null);
    }
  }, [token]);

  // ── Reject ─────────────────────────────────────────────────────────────────
  const reject = useCallback(async (claim, reason = "") => {
    setActionId(claim.id);
    try {
      await rejectClaim(claim.id, reason);
      setPending((prev) => prev.filter((c) => c.id !== claim.id));
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setActionId(null);
    }
  }, [token]);

  return {
    pending,
    loading,
    error,
    actionId,       // which claim is mid-request (for loading state on buttons)
    approve,
    reject,
    refetch: fetchPending,
  };
}
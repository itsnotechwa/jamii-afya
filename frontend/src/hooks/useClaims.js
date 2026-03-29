// src/hooks/useClaims.js
// ─────────────────────────────────────────────────────────────────────────────
// Manages fetching + caching claims list and single claim detail.
// Components call this — they never call the API layer directly.
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useEffect, useCallback } from "react";
import { useAuth } from "./useAuth";
import { getClaims, getClaim } from "../api/emergencies";

// ── Claims list ───────────────────────────────────────────────────────────────
export function useClaims() {
  const { token } = useAuth();
  const [claims,  setClaims]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const fetchClaims = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getClaims(token);
      setClaims(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchClaims(); }, [fetchClaims]);

  return { claims, loading, error, refetch: fetchClaims };
}

// ── Single claim detail ───────────────────────────────────────────────────────
export function useClaimDetail(claimId) {
  const { token } = useAuth();
  const [claim,   setClaim]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const fetchClaim = useCallback(async () => {
    if (!claimId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getClaim(claimId, token);
      setClaim(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [claimId, token]);

  useEffect(() => { fetchClaim(); }, [fetchClaim]);

  return { claim, loading, error, refetch: fetchClaim };
}
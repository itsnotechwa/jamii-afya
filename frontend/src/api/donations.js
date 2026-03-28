// src/api/donations.js
// ─────────────────────────────────────────────────────────────────────────────
// M-Pesa STK Push + donation history.
//
// Expected backend routes:
//   POST /api/donations/stk-push/     → triggers Safaricom STK push
//   GET  /api/donations/              → current user's donation history
//   GET  /api/donations/claim/{id}/   → donations for a specific claim
//
// M-Pesa STK flow:
//   1. Frontend POSTs { claim_id, amount, phone }
//   2. Backend calls Safaricom Daraja API → Safaricom pushes prompt to phone
//   3. Backend returns { checkout_request_id, message }
//   4. Frontend polls /api/donations/stk-status/{checkout_request_id}/
//      until status is "completed" | "failed" | "cancelled"
//
// Poll interval: 3s, max 10 attempts (30s timeout — Safaricom prompt expires).
// ─────────────────────────────────────────────────────────────────────────────
import api from "./axios";

// ── Initiate STK push ─────────────────────────────────────────────────────────
// phone: "0712345678" or "254712345678" — normalise on backend
export const initiateStkPush = (claimId, amount, phone) =>
  api.post("/api/donations/stk-push/", { claim_id: claimId, amount, phone })
  .then(r=>r.data);

// ── Poll for STK result ───────────────────────────────────────────────────────
// Returns { status: "pending" | "completed" | "failed" | "cancelled", ... }
export const getStkStatus = (checkoutRequestId) =>
  api.get(`/api/donations/stk-status/${checkoutRequestId}/`).then(r => r.data);

/**
 * Polls getStkStatus until terminal state or timeout.
 * Returns the final status object.
 * Throws if timed out or if status is "failed"/"cancelled".
 *
 * @param {string} checkoutRequestId
 * @param {string} token
 * @param {{ intervalMs?: number, maxAttempts?: number }} opts
 */
export async function pollStkStatus(
  checkoutRequestId,
  { intervalMs = 3000, maxAttempts = 10 } = {}
) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise((r) => setTimeout(r, intervalMs));

    const result = await getStkStatus(checkoutRequestId);

    if (result.status === "completed") return result;
    if (result.status === "failed")    throw new Error("Payment failed. Please try again.");
    if (result.status === "cancelled") throw new Error("Payment was cancelled.");
    // "pending" → keep polling
  }

  throw new Error("Payment timed out. Check your M-Pesa messages and try again.");
}

// ── Donation history ──────────────────────────────────────────────────────────
export const getMyDonations = () =>
  api.get("/api/donations/").then(r => r.data);

export const getClaimDonations = (claimId) =>
  api.get(`/api/donations/claim/${claimId}/`).then(r => r.data);
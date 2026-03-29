// src/api/claims.js
// ─────────────────────────────────────────────────────────────────────────────
// All Claims endpoints. Mirrors your FastAPI/Django router.
//
// Expected backend routes:
//   GET    /api/claims/              → list (approved + pending for admin)
//   GET    /api/claims/{id}/         → single claim with donations[]
//   POST   /api/claims/              → submit new claim (multipart, has file)
//   PATCH  /api/claims/{id}/approve/ → admin approve
//   PATCH  /api/claims/{id}/reject/  → admin reject
// 
import api from './axios'

const mapEmergency = (e) => ({
  id: e.id,
  hospital: e.group,
  amount: e.amount_requested,
  funded: e.amount_approved ?? 0,
  desc: e.description,
  status: e.status,
  urgent: e.status === 'pending' && !e.amount_approved,
  patient: e.claimant_name,
  donations: [],
});


// List 
// Returns all claims the current user can see.
// Donors: approved only. Admins: everything (backend enforces via role on JWT).
export const getClaims = () =>
  api.get("/api/emergencies/").then(r => r.data).map(mapEmergency);

// Single claim (with donations) 
export const getClaim = (id) =>
  api.get(`/api/emergencies/${id}/`).then(r => r.data);

// Submit new claim (has file upload — multipart, NOT JSON) 
// `data` shape: { hospital: string, amount: number, desc: string, file: File }
export async function submitClaim(data) {
  const form = new FormData();
  form.append("hospital", data.hospital);
  form.append("amount",   data.amount);
  form.append("desc",     data.desc ?? "");
  form.append("bill",     data.file);
  // axios handles auth header via interceptor — no manual token needed
  const { data: res } = await api.post('/api/emergencies/', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res;
}
// Admin: approve 
// Backend should trigger the M-Pesa B2C payout after persisting the approval.
export const approveClaim = (id) =>
  api.patch(`/api/emergencies/${id}/vote/`, {}).then(r => r.data);

// Admin: reject 
export const rejectClaim = (id, reason) =>
  api.patch(`/api/emergencies/${id}/vote/`, { reason }).then(r => r.data);
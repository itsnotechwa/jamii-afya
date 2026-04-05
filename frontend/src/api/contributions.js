// src/api/contributions.js
import api from './axios';

/** Daraja and our API mix PascalCase and snake_case for checkout ids. */
export function normalizeCheckoutRequestId(data) {
  if (!data || typeof data !== 'object') return '';
  return (
    data.checkout_request_id ||
    data.CheckoutRequestID ||
    ''
  );
}

/** Map POST /recheck/ response to pollContributionStatus shape. */
export function mapRecheckToPollShape(payload) {
  const { status, contribution_status, result_code, mpesa_receipt } = payload;
  if (contribution_status === 'confirmed' || status === 'success') {
    return { status: 'completed', mpesa_ref: mpesa_receipt || '' };
  }
  if (status === 'failed') {
    const rc = String(result_code || '');
    if (rc === '1032') return { status: 'cancelled' };
    return { status: 'failed' };
  }
  return { status: 'pending' };
}

/**
 * Load contribution schedule for the current user (primary group).
 * @returns {Promise<{ group_id: number, group_name: string, amount: number, period: string, next_due: string, paybill: string }>}
 */
export async function getSchedule() {
  const { data } = await api.get('/api/contributions/schedule/');
  return data;
}

/**
 * Initiate STK push. Uses schedule to fill group_id and period when omitted.
 */
export async function initiateContributionPush(amount, _phoneUnused, opts = {}) {
  let { groupId, period } = opts;
  if (groupId == null || !period) {
    const sched = await getSchedule();
    groupId = groupId ?? sched.group_id;
    period = period ?? sched.period;
  }
  const { data } = await api.post('/api/contributions/initiate/', {
    group_id: groupId,
    amount,
    period,
  });
  const checkout_request_id = normalizeCheckoutRequestId(data);
  const rc = data && String(data.ResponseCode ?? '');
  if (!checkout_request_id || rc !== '0') {
    const msg =
      (data && (data.CustomerMessage || data.ResponseDescription || data.detail)) ||
      'Could not start M-Pesa payment. Please try again.';
    throw new Error(msg);
  }
  return { ...data, checkout_request_id };
}

export async function getContributionStkStatus(checkoutRequestId) {
  const { data } = await api.post('/api/contributions/recheck/', {
    checkout_request_id: checkoutRequestId,
  });
  return mapRecheckToPollShape(data);
}

export async function pollContributionStatus(
  checkoutRequestId,
  { intervalMs = 3000, maxAttempts = 10 } = {},
) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise((r) => setTimeout(r, intervalMs));
    const result = await getContributionStkStatus(checkoutRequestId);
    if (result.status === 'completed') return result;
    if (result.status === 'failed') throw new Error('Payment failed. Please try again.');
    if (result.status === 'cancelled') throw new Error('Payment was cancelled.');
  }
  throw new Error('Payment timed out. Check your M-Pesa messages and try again.');
}

export async function getMyContributions() {
  const { data } = await api.get('/api/contributions/');
  const raw = Array.isArray(data) ? data : data.results ?? [];
  return raw.map((c) => ({
    id: c.id,
    amount: parseFloat(c.amount ?? 0),
    period: c.period ?? '',
    status: c.status ?? 'pending',
    hospital: c.group_name ?? 'Pool Fund',
    date: c.created_at ? new Date(c.created_at).toLocaleDateString('en-KE') : '',
    mpesa_ref: c.mpesa_ref ?? null,
  }));
}

/**
 * Admin: re-prompt unpaid members (same as send_reminder).
 * @param {{ groupId: number, period: string }} params
 */
export async function repromptContribution({ groupId, period }) {
  const { data } = await api.post('/api/contributions/reprompt/', {
    group_id: groupId,
    period,
  });
  return data;
}

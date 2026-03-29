import api from './axios';

// Trigger M-Pesa STK push for a contribution
export const initiateContributionPush = (amount, phone) =>
  api.post('/api/contributions/initiate/', { 
    group_id: 1, 
    amount, 
    phone, 
    period: new Date().toISOString().slice(0,7),
  }).then(r => r.data);

// Poll for STK result — same pattern as old donations
export const getContributionStkStatus = (checkoutRequestId) =>
  api.get(`/api/contributions/stk-status/${checkoutRequestId}/`).then(r => r.data);

export async function pollContributionStatus(
  checkoutRequestId,
  { intervalMs = 3000, maxAttempts = 10 } = {}
) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise((r) => setTimeout(r, intervalMs));
    const result = await getContributionStkStatus(checkoutRequestId);
    if (result.status === 'completed') return result;
    if (result.status === 'failed')    throw new Error('Payment failed. Please try again.');
    if (result.status === 'cancelled') throw new Error('Payment was cancelled.');
  }
  throw new Error('Payment timed out. Check your M-Pesa messages and try again.');
}

// Current user's contribution history
export const getMyContributions = () =>
  api.get('/api/contributions/').then(r => r.data);

// Current contribution schedule set by admin
export const getSchedule = () =>
  api.get('/api/contributions/schedule/').then(r => r.data);

// Re-prompt — user manually triggers reminder to themselves
export const repromptContribution = () =>
  api.post('/api/contributions/reprompt/').then(r => r.data);
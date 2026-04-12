/**
 * Shared rule for when the chama M-Pesa contribution modal should be offered.
 * Backend statuses: pending | confirmed | failed (no "overdue").
 */
function sameGroupId(a, b) {
  if (a == null || b == null) return false;
  return Number(a) === Number(b);
}

function samePeriod(a, b) {
  return String(a ?? '').trim() === String(b ?? '').trim();
}

export function needsContributionPayment(schedule, contribs) {
  if (schedule?.group_id == null || !schedule?.period) return false;
  const row = contribs.find(
    (c) => sameGroupId(c.group_id, schedule.group_id) && samePeriod(c.period, schedule.period),
  );
  if (!row) return true;
  return row.status === 'pending' || row.status === 'failed';
}

// src/api/emergencies.js
import api from './axios';

const mapEmergency = (e) => ({
  id: e.id,
  hospital:
    typeof e.group === 'object' ? e.group?.name : e.group ?? e.hospital ?? 'Unknown Hospital',
  amount: parseFloat(e.amount_requested ?? e.amount ?? 0),
  funded: parseFloat(e.amount_approved ?? e.funded ?? 0),
  desc: e.description ?? e.desc ?? '',
  status: e.status ?? 'pending',
  urgent: e.status === 'pending' && !e.amount_approved,
  patient: e.claimant_name ?? e.patient ?? 'Anonymous',
  documents: Array.isArray(e.documents) ? e.documents : [],
  paybill: (e.paybill != null && e.paybill !== '') ? String(e.paybill).trim() : '',
});

export async function getClaims() {
  const { data } = await api.get('/api/emergencies/');
  const raw = Array.isArray(data) ? data : data.results ?? [];
  return raw.map(mapEmergency);
}

export async function getClaim(id) {
  const { data } = await api.get(`/api/emergencies/${id}/`);
  return mapEmergency(data);
}

/**
 * Create emergency then attach bill document (backend expects `file` on upload_document).
 */
export async function submitClaim(data) {
  const hospitalLine = data.hospital ? `Hospital: ${data.hospital}` : '';
  const description = [hospitalLine, data.desc || ''].filter(Boolean).join('\n\n');

  const { data: created } = await api.post('/api/emergencies/', {
    group: data.group,
    emergency_type: data.emergency_type ?? 'other',
    description,
    amount_requested: data.amount,
    payout_phone: data.payout_phone,
  });

  if (data.file) {
    const doc = new FormData();
    doc.append('file', data.file);
    doc.append('label', data.label || 'Hospital bill');
    await api.post(`/api/emergencies/${created.id}/upload_document/`, doc, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  return created;
}

export async function approveClaim(id) {
  const { data } = await api.post(`/api/emergencies/${id}/vote/`, { decision: 'approve' });
  return data;
}

export async function rejectClaim(id, reason = '') {
  const { data } = await api.post(`/api/emergencies/${id}/vote/`, {
    decision: 'reject',
    note: reason,
  });
  return data;
}

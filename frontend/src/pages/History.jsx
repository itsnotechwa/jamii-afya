// src/pages/History.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fmt, pct } from '../helpers';
import { useClaims } from '../hooks/useClaims';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusChip from '../components/StatusChip';
import ProgressBar from '../components/ProgressBar';
import { useMyContributions } from '../hooks/useMyContributions';
import { useContributionPay } from '../context/ContributionPayContext';
import { useSnack } from '../context/SnackContext';
import { needsContributionPayment } from '../utils/contributionPay';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { openPayModal } = useContributionPay();
  const showSnack = useSnack();
  const [tab, setTab] = useState('claims');

  const {
    claims: myClaims,
    loading: claimsLoading,
    error:   claimsError,
    refetch: refetchClaims,
  } = useClaims();

  // Hook now correctly exposes `contributions` and `schedule`
  const {
    contributions,
    schedule,
    loading: contribLoading,
    error:   contribError,
    refetch: refetchContribs,
  } = useMyContributions();

  const isLoading = claimsLoading || contribLoading;
  const pageError = claimsError || contribError;

  if (isLoading) {
    return (
      <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
        <LoadingSpinner dark />
      </div>
    );
  }

  if (pageError) {
    return (
      <div className="page">
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-title">Could not load history</div>
          <div className="empty-state-sub">{pageError}</div>
          <button
            className="btn btn-outline"
            style={{ marginTop: 16 }}
            onClick={() => { refetchClaims(); refetchContribs(); }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalContributed = contributions.reduce((s, c) => s + (c.amount ?? 0), 0);
  const showContributionPay = needsContributionPayment(schedule, contributions);

  const copyClaimLink = (claimId) => {
    const path = `/claims/${claimId}`;
    const url = `${window.location.origin}${path}`;
    navigator.clipboard.writeText(url).then(
      () => showSnack('Link copied — share it to rally support.'),
      () => showSnack('Could not copy link.', 'error'),
    );
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">My Activity</div>
          <div className="page-subtitle">Your claims and contribution history</div>
        </div>
      </div>

      {/* Stat row */}
      <div className="stat-row" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-label">My Claims</div>
          <div className="stat-value blue">{myClaims.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Contributed</div>
          <div className="stat-value green">{fmt(totalContributed)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Contributions Made</div>
          <div className="stat-value orange">{contributions.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Next Due</div>
          <div className="stat-value blue" style={{ fontSize: '1rem' }}>
            {schedule?.next_due ?? '—'}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 24, maxWidth: 320 }}>
        <button
          className={`tab-btn ${tab === 'claims' ? 'active' : ''}`}
          onClick={() => setTab('claims')}
        >
          My Claims
        </button>
        <button
          className={`tab-btn ${tab === 'contributions' ? 'active' : ''}`}
          onClick={() => setTab('contributions')}
        >
          My Contributions
        </button>
      </div>

      {/* ── Claims tab ── */}
      {tab === 'claims' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {myClaims.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-title">No claims yet</div>
              <div className="empty-state-sub">Claims you submit will appear here.</div>
              <button
                className="btn btn-primary"
                style={{ marginTop: 16 }}
                onClick={() => navigate('/claims/new')}
              >
                + Submit a Claim
              </button>
            </div>
          ) : (
            myClaims.map((d) => {
              const p = pct(d.funded, d.amount);
              return (
                <div key={d.id} className="card">
                  <div style={{ padding: '18px 20px' }}>
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      alignItems: 'flex-start', marginBottom: 10,
                      flexWrap: 'wrap', gap: 8,
                    }}>
                      <div>
                        <div style={{ fontWeight: 700, marginBottom: 2 }}>{d.hospital}</div>
                        <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', color: 'var(--blue)' }}>
                          {fmt(d.amount)}
                        </div>
                      </div>
                      <StatusChip status={d.status} />
                    </div>
                    <ProgressBar value={p} />
                    <div style={{ fontSize: '.8rem', color: 'var(--ink-muted)', marginTop: 8 }}>
                      {fmt(d.funded)} of {fmt(d.amount)} raised
                    </div>
                  </div>
                  <div style={{
                    padding: '10px 20px', borderTop: '1px solid var(--border)',
                    background: 'var(--surface-2)', display: 'flex', gap: 8,
                  }}>
                    <button className="btn btn-outline btn-sm" onClick={() => navigate(`/claims/${d.id}`)}>
                      View Details
                    </button>
                    {d.status !== 'funded' && (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => copyClaimLink(d.id)}
                      >
                        Copy link
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* ── Contributions tab ── */}
      {tab === 'contributions' && (
        <div className="card">
          {showContributionPay && (
            <div style={{
              padding: '14px 20px',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 12,
              justifyContent: 'space-between',
            }}>
              <span style={{ fontSize: '.88rem', color: 'var(--ink-secondary)' }}>
                Monthly chama contribution ({schedule?.period}) — pay with M-Pesa STK.
              </span>
              <button type="button" className="btn btn-primary btn-sm" onClick={openPayModal}>
                Pay with M-Pesa
              </button>
            </div>
          )}
          {contributions.length === 0 ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--ink-muted)', fontSize: '.88rem' }}>
              No contributions yet.
            </div>
          ) : (
            <div style={{ padding: '0 20px' }}>
              {contributions.map((c) => (
                <div key={c.id} className="timeline-item">
                  <div className="timeline-icon green">💙</div>
                  <div className="timeline-body">
                    <div className="timeline-main">
                      {c.period} ·{' '}
                      <span style={{ color: 'var(--green)', fontFamily: 'var(--font-display)' }}>
                        {fmt(c.amount)}
                      </span>
                    </div>
                    <div className="timeline-meta">
                      {c.date}{c.mpesa_ref ? ` · Ref: ${c.mpesa_ref}` : ''}
                    </div>
                  </div>
                  <span className={`chip ${c.status === 'confirmed' ? 'chip-funded' : 'chip-pending'}`}>
                    {c.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
import { useState, useEffect } from 'react';
import { getProfile, updateProfile } from '../api/auth';
import { useSnack } from '../context/SnackContext';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ProfilePage() {
  const showSnack = useSnack();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [phoneDisplay, setPhoneDisplay] = useState('');
  const [verified, setVerifiedLabel] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr('');
      try {
        const p = await getProfile();
        if (cancelled || !p) return;
        setFirstName(p.first_name || '');
        setLastName(p.last_name || '');
        setEmail(p.email || '');
        setNationalId(p.national_id || '');
        setPhoneDisplay(String(p.phone_number ?? ''));
        setVerifiedLabel(Boolean(p.is_verified));
      } catch (e) {
        if (!cancelled) setErr(e.message || 'Could not load profile.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setErr('');
    try {
      const nid = nationalId.replace(/\s/g, '');
      await updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        ...(nid ? { national_id: nid } : { national_id: null }),
      });
      showSnack('Profile saved.');
    } catch (e) {
      setErr(e.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
        <LoadingSpinner dark />
      </div>
    );
  }

  return (
    <div className="page" style={{ maxWidth: 480, margin: '0 auto' }}>
      <div className="page-header">
        <div>
          <div className="page-title">Your profile</div>
          <div className="page-subtitle">Name, email, and ID — phone is set at registration</div>
        </div>
      </div>

      <div className="card" style={{ padding: 24 }}>
        <div className="field" style={{ marginBottom: 14 }}>
          <label>Phone number</label>
          <input className="prefix-input" style={{ width: '100%', opacity: 0.85 }} value={phoneDisplay} readOnly disabled />
        </div>
        <div style={{ fontSize: '.8rem', color: verified ? 'var(--green)' : 'var(--orange)', marginBottom: 16 }}>
          {verified ? '✓ Phone verified' : 'Phone not verified — complete verification when prompted after sign-in.'}
        </div>

        <div className="field" style={{ marginBottom: 14 }}>
          <label htmlFor="pf-first">First name</label>
          <input
            id="pf-first"
            className="prefix-input"
            style={{ width: '100%' }}
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
        </div>
        <div className="field" style={{ marginBottom: 14 }}>
          <label htmlFor="pf-last">Last name</label>
          <input
            id="pf-last"
            className="prefix-input"
            style={{ width: '100%' }}
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>
        <div className="field" style={{ marginBottom: 14 }}>
          <label htmlFor="pf-email">Email</label>
          <input
            id="pf-email"
            type="email"
            className="prefix-input"
            style={{ width: '100%' }}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field" style={{ marginBottom: 20 }}>
          <label htmlFor="pf-nid">National ID</label>
          <input
            id="pf-nid"
            className="prefix-input"
            style={{ width: '100%' }}
            value={nationalId}
            onChange={(e) => setNationalId(e.target.value)}
          />
        </div>

        {err && <p className="field-error" role="alert" style={{ marginBottom: 12 }}>{err}</p>}

        <button type="button" className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <><LoadingSpinner /> Saving…</> : 'Save changes'}
        </button>
      </div>
    </div>
  );
}

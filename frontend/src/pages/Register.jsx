import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerAccount } from '../api/auth';
import Spinner from '../components/LoadingSpinner';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const handleSubmit = async () => {
    setErr('');
    if (phone.replace(/\s/g, '').length < 9) {
      setErr('Enter a valid Kenyan phone number (9 digits after +254).');
      return;
    }
    if (password.length < 8) {
      setErr('Password must be at least 8 characters.');
      return;
    }
    if (password !== password2) {
      setErr('Passwords do not match.');
      return;
    }
    if (!firstName.trim() || !lastName.trim()) {
      setErr('First and last name are required.');
      return;
    }

    const payload = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      phone_number: `+254${phone.replace(/\D/g, '')}`,
      email: email.trim() || '',
      password,
      password2,
    };
    const nid = nationalId.replace(/\s/g, '');
    if (nid) payload.national_id = nid;

    setLoading(true);
    try {
      await registerAccount(payload);
      navigate('/login?registered=1', { replace: true });
    } catch (e) {
      setErr(e.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="login-shell">
      <div className="login-card" style={{ maxWidth: 420 }}>
        <div className="login-logo">
          <div className="login-logo-mark">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="white" aria-hidden="true">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <div>
            <div className="login-title">Create account</div>
            <div className="login-sub">Join Jamii Afya — verify your phone after sign-in</div>
          </div>
        </div>

        <div className="field" style={{ marginBottom: 12 }}>
          <label htmlFor="reg-first">First name</label>
          <input
            id="reg-first"
            className="prefix-input"
            style={{ width: '100%' }}
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="given-name"
          />
        </div>
        <div className="field" style={{ marginBottom: 12 }}>
          <label htmlFor="reg-last">Last name</label>
          <input
            id="reg-last"
            className="prefix-input"
            style={{ width: '100%' }}
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="family-name"
          />
        </div>

        <div className="field" style={{ marginBottom: 12 }}>
          <label htmlFor="reg-phone">Phone</label>
          <div className="field-prefix">
            <span className="prefix-label">+254</span>
            <input
              id="reg-phone"
              className="prefix-input"
              type="tel"
              placeholder="712 345 678"
              value={phone}
              onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
              onKeyDown={onKeyDown}
              maxLength={9}
              autoComplete="tel"
            />
          </div>
        </div>

        <div className="field" style={{ marginBottom: 12 }}>
          <label htmlFor="reg-nid">National ID (optional)</label>
          <input
            id="reg-nid"
            className="prefix-input"
            style={{ width: '100%' }}
            value={nationalId}
            onChange={(e) => setNationalId(e.target.value)}
            onKeyDown={onKeyDown}
          />
        </div>

        <div className="field" style={{ marginBottom: 12 }}>
          <label htmlFor="reg-email">Email</label>
          <input
            id="reg-email"
            className="prefix-input"
            style={{ width: '100%' }}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="email"
          />
        </div>

        <div className="field" style={{ marginBottom: 12 }}>
          <label htmlFor="reg-pw">Password</label>
          <input
            id="reg-pw"
            className="prefix-input"
            style={{ width: '100%' }}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="new-password"
          />
        </div>

        <div className="field" style={{ marginBottom: 16 }}>
          <label htmlFor="reg-pw2">Confirm password</label>
          <input
            id="reg-pw2"
            className="prefix-input"
            style={{ width: '100%' }}
            type="password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="new-password"
          />
        </div>

        {err && (
          <span className="field-error" role="alert" style={{ display: 'block', marginBottom: 14, textAlign: 'center' }}>
            {err}
          </span>
        )}

        <button type="button" className="btn btn-primary btn-full btn-lg" onClick={handleSubmit} disabled={loading}>
          {loading ? <><Spinner /> Creating account…</> : 'Create account'}
        </button>

        <p style={{ fontSize: '.85rem', color: 'var(--ink-muted)', textAlign: 'center', marginTop: 16 }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

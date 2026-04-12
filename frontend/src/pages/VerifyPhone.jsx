import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { sendPhoneOtp, verifyPhoneOtp } from '../api/auth';
import { useAuth } from '../hooks/useAuth';
import Spinner from '../components/LoadingSpinner';

export default function VerifyPhonePage() {
  const { setVerified } = useAuth();
  const location = useLocation();

  const [code, setCode] = useState('');
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  const handleSend = async () => {
    setErr('');
    setMsg('');
    setSending(true);
    try {
      const data = await sendPhoneOtp();
      setMsg(data?.detail || 'Check your phone for the code.');
    } catch (e) {
      setErr(e.message);
    } finally {
      setSending(false);
    }
  };

  const handleVerify = async () => {
    setErr('');
    setMsg('');
    const digits = code.replace(/\D/g, '');
    if (digits.length !== 6) {
      setErr('Enter the full 6-digit code from your SMS.');
      return;
    }
    setVerifying(true);
    try {
      await verifyPhoneOtp(digits);
      setVerified(true);
      // PrivateRoute redirects off /verify-phone using location.state.from (same as login flow).
    } catch (e) {
      setErr(e.message);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 440, margin: '0 auto', paddingTop: 24 }}>
      <div className="card" style={{ padding: 24 }}>
        <h1 className="page-title" style={{ fontSize: '1.35rem', marginBottom: 8 }}>Verify your phone</h1>
        <p style={{ fontSize: '.88rem', color: 'var(--ink-secondary)', marginBottom: 20, lineHeight: 1.5 }}>
          We send a one-time code to the number on your account. You need a verified phone to use payouts and notifications.
        </p>

        <button
          type="button"
          className="btn btn-outline btn-full"
          style={{ marginBottom: 20 }}
          onClick={handleSend}
          disabled={sending}
        >
          {sending ? <><Spinner /> Sending…</> : 'Send verification code'}
        </button>

        <div className="field" style={{ marginBottom: 16 }}>
          <label htmlFor="otp-code">6-digit code</label>
          <input
            id="otp-code"
            className="prefix-input"
            style={{ width: '100%', letterSpacing: '0.2em', fontSize: '1.1rem' }}
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          />
        </div>

        {msg && (
          <p style={{ fontSize: '.85rem', color: 'var(--green)', marginBottom: 12 }}>{msg}</p>
        )}
        {err && (
          <p className="field-error" role="alert" style={{ marginBottom: 12 }}>{err}</p>
        )}

        <button
          type="button"
          className="btn btn-primary btn-full"
          onClick={handleVerify}
          disabled={verifying}
        >
          {verifying ? <><Spinner /> Verifying…</> : 'Verify & continue'}
        </button>
      </div>
    </div>
  );
}

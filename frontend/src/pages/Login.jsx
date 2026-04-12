// src/pages/Login.jsx
import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Spinner from "../components/LoadingSpinner";

export default function LoginPage() {
  const { login }  = useAuth();
  const navigate   = useNavigate();
  const location   = useLocation();
  const from       = location.state?.from?.pathname ?? "/";
  const [searchParams] = useSearchParams();

  const [phone,    setPhone]    = useState("");
  const [notice,  setNotice]   = useState("");

  useEffect(() => {
    if (searchParams.get("registered") === "1") {
      setNotice("Account created. Sign in, then verify your phone with the code we SMS.");
    } else {
      setNotice("");
    }
  }, [searchParams]);
  const [password, setPassword] = useState("");
  const [showPw,   setShowPw]   = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [err,      setErr]      = useState("");

  const handleSubmit = async () => {
    if (phone.replace(/\s/g, "").length < 9) {
      setErr("Enter a valid Kenyan number"); return;
    }
    if (!password) {
      setErr("Enter your password"); return;
    }

    setErr(""); setLoading(true);
    try {
      await login("+254" + phone, password);
      navigate(from, { replace: true });
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Allow submit on Enter key from either field
  const onKeyDown = (e) => { if (e.key === "Enter") handleSubmit(); };

  return (
    <div className="login-shell">
      <div className="login-card">

        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-mark">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="white" aria-hidden="true">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <div>
            <div className="login-title">Jamii Afya</div>
            <div className="login-sub">Fast, transparent aid for Kenyans</div>
          </div>
        </div>

        {/* Phone */}
        <div className="field" style={{ marginBottom: 16 }}>
          <label htmlFor="phone-input">Phone Number</label>
          <div className="field-prefix">
            <span className="prefix-label">+254</span>
            <input
              id="phone-input"
              className="prefix-input"
              type="tel"
              placeholder="712 345 678"
              value={phone}
              onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))}
              onKeyDown={onKeyDown}
              maxLength={9}
              autoComplete="tel"
              aria-required="true"
            />
          </div>
        </div>

        {/* Password */}
        <div className="field" style={{ marginBottom: 20 }}>
          <label htmlFor="password-input">Password</label>
          <div className="field-prefix" style={{ position: "relative" }}>
            <input
              id="password-input"
              className="prefix-input"
              style={{ paddingRight: 44 }}
              type={showPw ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={onKeyDown}
              autoComplete="current-password"
              aria-required="true"
            />
            {/* Show / hide toggle */}
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              aria-label={showPw ? "Hide password" : "Show password"}
              style={{
                position: "absolute", right: 10, top: "50%",
                transform: "translateY(-50%)",
                background: "none", border: "none",
                cursor: "pointer", color: "var(--ink-muted)",
                fontSize: ".8rem", padding: "4px 6px",
              }}
            >
              {showPw ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        {notice && (
          <p style={{ fontSize: ".85rem", color: "var(--green)", textAlign: "center", marginBottom: 12 }}>
            {notice}
          </p>
        )}

        {/* Error */}
        {err && (
          <span
            className="field-error"
            role="alert"
            style={{ display: "block", marginBottom: 14, textAlign: "center" }}
          >
            {err}
          </span>
        )}

        {/* Submit */}
        <button
          className="btn btn-primary btn-full btn-lg"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? <><Spinner /> Signing in…</> : "Sign In"}
        </button>

        <p style={{ fontSize: ".85rem", color: "var(--ink-muted)", textAlign: "center", marginTop: 14 }}>
          New here? <Link to="/register">Create an account</Link>
        </p>

        {/* Demo hint */}
        <p style={{ fontSize: ".78rem", color: "var(--ink-muted)", textAlign: "center", marginTop: 10 }}>
          Demo — Admin: <strong>+254700000000</strong> / <strong>123456</strong>
          &nbsp;·&nbsp;
          Member: <strong>+254712345678</strong> / <strong>123456</strong>
        </p>
      </div>
    </div>
  );
}
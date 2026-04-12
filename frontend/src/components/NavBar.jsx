// src/components/NavBar.jsx
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Navbar() {
  const navigate     = useNavigate();
  const { pathname } = useLocation();
  const { role, isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  if (!isAuthenticated) return null;

  // Helper - Roles that can use the 'New Claim' button
  const canCreateClaim = ["admin", "member"].includes(role);

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div
        className="navbar-logo"
        onClick={() => navigate("/")}
        style={{ cursor: "pointer" }}
        role="link"
        aria-label="Go to home"
      >
        <div className="logo-pulse">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="white" aria-hidden="true">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </div>
        Jamii-Afya
      </div>

      <div className="navbar-actions">
        <button
          className={`nav-btn ${pathname === "/" ? "active" : ""}`}
          aria-current={pathname === "/" ? "page" : undefined}
          onClick={() => navigate("/")}
        >
          🏠 Home
        </button>

        { canCreateClaim && (
          <button
          className={`nav-btn ${pathname === "/claims/new" ? "active" : ""}`}
          aria-current={pathname === "/claims/new" ? "page" : undefined}
          onClick={() => navigate("/claims/new")}
        >
          + New Claim
        </button>
        )}

        <button
          className={`nav-btn ${pathname === "/history" ? "active" : ""}`}
          aria-current={pathname === "/history" ? "page" : undefined}
          onClick={() => navigate("/history")}
        >
          History
        </button>

        <button
          className={`nav-btn ${pathname === "/profile" ? "active" : ""}`}
          aria-current={pathname === "/profile" ? "page" : undefined}
          onClick={() => navigate("/profile")}
        >
          Profile
        </button>

        {role === "admin" && (
          <button
            className={`nav-btn ${pathname === "/admin" ? "active" : ""}`}
            aria-current={pathname === "/admin" ? "page" : undefined}
            onClick={() => navigate("/admin")}
          >
            Admin
          </button>
        )}

        <button className="nav-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}
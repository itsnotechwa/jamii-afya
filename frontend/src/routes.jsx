import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import LoadingSpinner from './components/LoadingSpinner';

import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyPhone from './pages/VerifyPhone';
import Profile from './pages/Profile';
import ClaimDetail from './pages/ClaimDetail';
import NewClaim from './pages/NewClaim';
import AdminDashboard from './pages/AdminDashboard';
import History from './pages/History';

/**
 * @param {{ allowedRoles?: string[], skipPhoneVerification?: boolean, children: React.ReactNode }} props
 */
function PrivateRoute({ allowedRoles, skipPhoneVerification, children }) {
  const { isAuthenticated, role, isVerified, authReady } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!authReady) {
    return (
      <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
        <LoadingSpinner dark />
      </div>
    );
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />;
  }

  if (!skipPhoneVerification && isVerified === false && location.pathname !== '/verify-phone') {
    return <Navigate to="/verify-phone" replace state={{ from: location }} />;
  }

  if (location.pathname === '/verify-phone' && isVerified === true) {
    const from = location.state?.from;
    if (from?.pathname) {
      return (
        <Navigate
          replace
          to={{
            pathname: from.pathname,
            search: from.search ?? '',
            hash: from.hash ?? '',
          }}
          state={from.state}
        />
      );
    }
    return <Navigate to="/" replace />;
  }

  // No shell/nav during phone verification (like /login) — avoids Profile → /profile → bounce back here.
  if (location.pathname === '/verify-phone') {
    return children;
  }

  return <Layout>{children}</Layout>;
}

function PublicOnlyRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/" replace /> : children;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <Register />
          </PublicOnlyRoute>
        }
      />

      <Route
        path="/verify-phone"
        element={
          <PrivateRoute skipPhoneVerification>
            <VerifyPhone />
          </PrivateRoute>
        }
      />

      <Route
        path="/"
        element={
          <PrivateRoute>
            <Home />
          </PrivateRoute>
        }
      />

      <Route
        path="/claims/:claimId"
        element={
          <PrivateRoute>
            <ClaimDetail />
          </PrivateRoute>
        }
      />

      <Route
        path="/claims/new"
        element={
          <PrivateRoute allowedRoles={['member', 'admin']}>
            <NewClaim />
          </PrivateRoute>
        }
      />

      <Route
        path="/history"
        element={
          <PrivateRoute>
            <History />
          </PrivateRoute>
        }
      />

      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        }
      />

      <Route
        path="/admin"
        element={
          <PrivateRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </PrivateRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

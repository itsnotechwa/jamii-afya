import React, { createContext, useReducer, useEffect, useCallback, useState } from 'react';
import { loginWithPassword, clearAuthStorage, getProfile } from '../api/auth';

const initialState = {
  token: localStorage.getItem('token') || null,
  role: localStorage.getItem('role') || null,
  userId: localStorage.getItem('userId') ? Number(localStorage.getItem('userId')) : null,
  isVerified:
    localStorage.getItem('isVerified') === '1'
      ? true
      : localStorage.getItem('isVerified') === '0'
        ? false
        : null,
};

function authReducer(state, action) {
  switch (action.type) {
    case 'SET_USER':
      return {
        ...state,
        token: action.token,
        role: action.role,
        userId: action.userId,
        isVerified: action.isVerified,
      };
    case 'SET_VERIFIED':
      return { ...state, isVerified: action.isVerified };
    case 'CLEAR':
      return { token: null, role: null, userId: null, isVerified: null };
    default:
      return state;
  }
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const [authReady, setAuthReady] = useState(!initialState.token);

  useEffect(() => {
    if (state.token) {
      localStorage.setItem('token', state.token);
      localStorage.setItem('role', state.role);
      localStorage.setItem('userId', String(state.userId));
      if (state.isVerified === true) localStorage.setItem('isVerified', '1');
      else if (state.isVerified === false) localStorage.setItem('isVerified', '0');
    } else {
      clearAuthStorage();
    }
  }, [state.token, state.role, state.userId, state.isVerified]);

  useEffect(() => {
    if (!state.token) {
      setAuthReady(true);
      return;
    }
    let cancelled = false;
    setAuthReady(false);
    (async () => {
      try {
        const p = await getProfile();
        if (!cancelled && p) {
          dispatch({ type: 'SET_VERIFIED', isVerified: Boolean(p.is_verified) });
        }
      } catch {
        /* 401 etc. — axios interceptor may redirect; still unblock UI */
      } finally {
        if (!cancelled) setAuthReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [state.token]);

  async function login(phone, password) {
    const data = await loginWithPassword(phone, password);
    dispatch({
      type: 'SET_USER',
      token: data.token,
      role: data.role,
      userId: data.id,
      isVerified: data.isVerified,
    });
    return data;
  }

  const setVerified = useCallback((value) => {
    dispatch({ type: 'SET_VERIFIED', isVerified: value });
    localStorage.setItem('isVerified', value ? '1' : '0');
  }, []);

  function logout() {
    dispatch({ type: 'CLEAR' });
  }

  const value = {
    token: state.token,
    role: state.role,
    userId: state.userId,
    isVerified: state.isVerified,
    isAuthenticated: Boolean(state.token),
    authReady,
    login,
    logout,
    setVerified,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

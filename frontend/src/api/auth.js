/**
 * auth.js
 * Returns { token, role, id }; caller stores these in AuthContext.
 */

import api from './axios';

const ALLOW_DEMO_LOGIN = import.meta.env.VITE_ALLOW_DEMO_LOGIN === 'true';

async function loginViaApi(phone, password) {
  const { data } = await api.post('/api/auth/login/', {
    identifier: phone,
    password,
  });
  if (!data || typeof data !== 'object') {
    throw new Error('Unexpected login response from server.');
  }
  const token = data.token || data.access;
  if (!token) {
    throw new Error(data.detail || 'Login did not return a token.');
  }
  const user = data.user;
  if (!user || user.id == null || Number.isNaN(Number(user.id))) {
    throw new Error(data.detail || 'Login did not return user information.');
  }
  const role = user.is_staff ? 'admin' : 'member';
  localStorage.setItem('token', token);
  localStorage.setItem('role', role);
  const id = Number(user.id);
  localStorage.setItem('userId', String(id));
  return { token, role, id };
}

/**
 * Login and retrieve JWT + role.
 * @param {string} phone  E.164 e.g. "+254712345678" (sent as `identifier` to the API)
 * @param {string} password
 * @returns {Promise<{ token: string, role: 'member'|'admin', id: number }>}
 */
export async function loginWithPassword(phone, password) {
  if (ALLOW_DEMO_LOGIN) {
    try {
      return await loginViaApi(phone, password);
    } catch (error) {
      console.warn('Backend login failed, using demo fallback:', error.message);
      const mockToken =
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkRlbW8gVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
      const mockRole = phone === '+254700000000' ? 'admin' : 'member';
      const mockId = 1;
      localStorage.setItem('token', mockToken);
      localStorage.setItem('role', mockRole);
      localStorage.setItem('userId', String(mockId));
      return { token: mockToken, role: mockRole, id: mockId };
    }
  } else {
    return loginViaApi(phone, password);
  }
}

/**
 * Clear all auth artefacts from localStorage.
 * AuthContext.logout() should call this before clearing its own state.
 */
export function clearAuthStorage() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('userId');
}

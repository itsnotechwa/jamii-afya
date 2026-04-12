/**
 * auth.js — login, register, profile, OTP verification.
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
  const id = Number(user.id);
  const isVerified = Boolean(user.is_verified);
  localStorage.setItem('token', token);
  localStorage.setItem('role', role);
  localStorage.setItem('userId', String(id));
  localStorage.setItem('isVerified', isVerified ? '1' : '0');
  return { token, role, id, isVerified };
}

/**
 * Login and retrieve JWT + role.
 * @returns {Promise<{ token: string, role: 'member'|'admin', id: number, isVerified: boolean }>}
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
      localStorage.setItem('isVerified', '1');
      return { token: mockToken, role: mockRole, id: mockId, isVerified: true };
    }
  }
  return loginViaApi(phone, password);
}

export async function registerAccount(payload) {
  const { data } = await api.post('/api/auth/register/', payload);
  return data;
}

export async function getProfile() {
  const { data } = await api.get('/api/auth/profile/');
  return data;
}

export async function updateProfile(payload) {
  const { data } = await api.patch('/api/auth/profile/', payload);
  return data;
}

export async function sendPhoneOtp() {
  const { data } = await api.post('/api/auth/verify/send/', {});
  return data;
}

export async function verifyPhoneOtp(code) {
  const { data } = await api.post('/api/auth/verify/confirm/', { code: String(code).trim() });
  return data;
}

export { clearAuthStorage } from './authStorage';

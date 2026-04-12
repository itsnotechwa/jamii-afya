import axios from 'axios';
import { clearAuthStorage } from './authStorage';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT ──────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error),
);

/** Flatten Django REST Framework validation payloads (detail, non_field_errors, field errors). */
function drfErrorMessage(data) {
  if (data == null || typeof data !== 'object') return null;
  const { detail, message, non_field_errors: nfe } = data;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length) return detail.map(String).join(' ');
  if (typeof message === 'string' && message.trim()) return message;
  if (Array.isArray(nfe) && nfe.length) return nfe.map(String).join(' ');
  for (const key of Object.keys(data)) {
    if (key === 'detail' || key === 'message') continue;
    const v = data[key];
    if (Array.isArray(v) && v.length) return `${key}: ${v.map(String).join(' ')}`;
    if (typeof v === 'string' && v.trim()) return `${key}: ${v}`;
  }
  return null;
}

// ── Response interceptor: normalise errors ───────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthStorage();
      // Full navigation remounts the app; AuthContext re-initializes from cleared storage.
      window.location.href = '/login';
    }
    const data = error.response?.data;
    const message =
      drfErrorMessage(data) ||
      error.message ||
      'An unexpected error occurred.';
    return Promise.reject(new Error(message));
  },
);

export default api;
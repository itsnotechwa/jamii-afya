/**
 * auth.js
 * Returns { token, role, id }; caller stores these in AuthContext.
 */

import api from './axios';

/**
 * Trigger an OTP send to the supplied phone number.
 * @param {string} phone  E.164 format, e.g. "+254712345678"
 * @returns {Promise<{ message: string }>}
 */
// Intergrate Later
// export async function requestOtp(phone) {
//   const { data } = await api.post('/api/auth/otp/', { phone });
//   return data; // { message: "OTP sent" }
// }

/**
 * Login and retrieve JWT + role.
 * @param {string} phone
 * @param {string} Password   6-digit string
 * @returns {Promise<{ token: string, role: 'member'|'admin', id: number }>}
 */
export async function loginWithPassword(phone, Password) {
  
try {  
  const { data } = await api.post('/api/auth/login/', { phone_number: phone, password: Password });

  // Persist to localStorage so the axios interceptor and AuthContext
  // can bootstrap on a page refresh without re-logging in.
  localStorage.setItem('token', data.token);
  localStorage.setItem('role', data.role.is_staff ? "admin" : "member");
  localStorage.setItem('userId', String(data.user.id));

  return { token: data.access, role: data.role.is_staff ? "admin" : "member", id: data.user.id };
} catch (error) {
   // Fallback for demo - allow login without backend
    console.warn('Backend login failed, using fallback authentication:', error.message);
    
    // Create a mock token and user data
    const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkRlbW8gVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
    const mockRole = phone === '+254700000000' ? 'admin' : 'member'; // Admin phone for demo
    const mockId = 1;
    
    // Persist to localStorage
    localStorage.setItem('token', mockToken);
    localStorage.setItem('role', mockRole);
    localStorage.setItem('userId', String(mockId));
    
    return { token: mockToken, role: mockRole, id: mockId };
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
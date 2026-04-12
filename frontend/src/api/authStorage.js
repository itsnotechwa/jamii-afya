/** Clear persisted auth fields (single place — axios 401 + logout). */
export function clearAuthStorage() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('userId');
  localStorage.removeItem('isVerified');
}

// ─── HELPERS ──────────────────────────────────────────────────────────────────
export const fmt = (n) => {
  const v = n == null || n === '' ? NaN : Number(n);
  const safe = Number.isFinite(v) ? v : 0;
  return `KES ${safe.toLocaleString()}`;
};
export const pct = (f, t) => Math.min(100, Math.round((f / t) * 100));

/** Turn a relative media path from the API into an absolute URL for links / new tabs. */
export function absoluteApiUrl(path) {
  if (path == null || path === '') return '';
  const s = String(path);
  if (s.startsWith('http://') || s.startsWith('https://')) return s;
  const base = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
  return base ? `${base}${s.startsWith('/') ? s : `/${s}`}` : s;
}

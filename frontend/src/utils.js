// Shared helper utilities
export const API_BASE = '';  // Uses Vite proxy → localhost:8000

function parseDate(dateValue) {
  if (!dateValue) return null;
  const value = dateValue instanceof Date ? dateValue.toISOString() : String(dateValue);
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`);
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

export function timeSince(dateStr) {
  if (!dateStr) return '—';
  const secs = Math.max(0, Math.floor((Date.now() - parseDate(dateStr).getTime()) / 1000));
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  return parseDate(dateStr).toLocaleString();
}

export function severityClass(sev) {
  switch ((sev || '').toUpperCase()) {
    case 'CRITICAL': return 'badge-critical';
    case 'HIGH': return 'badge-high';
    case 'MEDIUM': return 'badge-medium';
    default: return 'badge-low';
  }
}

export function statusClass(status) {
  switch ((status || '').toUpperCase()) {
    case 'OPEN': return 'badge-status-open';
    case 'INVESTIGATING': return 'badge-status-investigating';
    case 'MITIGATED': return 'badge-status-mitigated';
    case 'RESOLVED': return 'badge-status-resolved';
    default: return 'badge-status-open';
  }
}

export function logClass(line) {
  const l = line.toLowerCase();
  if (l.includes('error') || l.includes('fatal')) return 'log-line-error';
  if (l.includes('warn')) return 'log-line-warn';
  if (l.includes('info')) return 'log-line-info';
  return 'log-line-ok';
}

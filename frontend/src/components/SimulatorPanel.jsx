import { useState } from 'react';
import { apiFetch } from '../utils';

const INCIDENT_TYPES = [
  { key: 'high_cpu', label: '⚡ High CPU' },
  { key: 'memory_leak', label: '💧 Memory Leak' },
  { key: 'db_timeout', label: '🗄️ DB Timeout' },
  { key: 'http_5xx', label: '🔥 HTTP 5xx Spike' },
  { key: 'slow_query', label: '🐌 Slow Query' },
  { key: 'bad_deployment', label: '💥 Bad Deployment' },
];

const SERVICES = ['api-gateway', 'auth-service', 'payment-service', 'order-service', 'user-service'];
const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export default function SimulatorPanel({ onCreated, onDemoPart1, onDemoPart2 }) {
  const [selectedType, setSelectedType] = useState('high_cpu');
  const [service, setService] = useState('');
  const [severity, setSeverity] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState('');

  const simulate = async () => {
    setLoading(true);
    try {
      const body = { incident_type: selectedType };
      if (service) body.service = service;
      if (severity) body.severity = severity;
      const inc = await apiFetch('/api/incidents/simulate', { method: 'POST', body: JSON.stringify(body) });
      onCreated?.(inc, `Incident ${inc.id} created (${selectedType.replace('_', ' ')})`);
    } catch (e) {
      onCreated?.(null, null, e.message);
    } finally {
      setLoading(false);
    }
  };

  const demoPart = async (part) => {
    setDemoLoading(part);
    try {
      const endpoint = part === '1' ? '/api/simulation/demo-part1' : '/api/simulation/demo-part2';
      const inc = await apiFetch(endpoint, { method: 'POST' });
      if (part === '1') onDemoPart1?.(inc);
      else onDemoPart2?.(inc);
    } catch (e) {
      onCreated?.(null, null, e.message);
    } finally {
      setDemoLoading('');
    }
  };

  return (
    <div className="simulator-panel">
      <div className="panel-title">
        <span>🎛️</span> Incident Simulator
      </div>

      {/* Demo Flow Buttons */}
      <div className="demo-bar" style={{ marginBottom: 14 }}>
        <strong>🎯 Demo Flow:</strong>
        <span>Run the full Hindsight learning loop</span>
        <button type="button" className="btn btn-primary btn-sm" onClick={() => demoPart('1')} disabled={demoLoading === '1'}>
          {demoLoading === '1' ? <span className="spinner" /> : null} Demo Part 1 (IR-001)
        </button>
        <button type="button" className="btn btn-hindsight btn-sm" onClick={() => demoPart('2')} disabled={demoLoading === '2'}>
          {demoLoading === '2' ? <span className="spinner" /> : null} Demo Part 2 (IR-002)
        </button>
      </div>

      <div className="panel-title" style={{ marginBottom: 8 }}>
        <span>⚙️</span> Custom Simulation
      </div>
      <div className="incident-type-grid">
        {INCIDENT_TYPES.map(t => (
          <button
            type="button"
            key={t.key}
            className={`incident-type-btn${selectedType === t.key ? ' selected' : ''}`}
            onClick={() => setSelectedType(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
        <div className="form-group">
          <label className="form-label">Service (optional)</label>
          <select className="form-control" value={service} onChange={e => setService(e.target.value)}>
            <option value="">Auto-detect</option>
            {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Override Severity</label>
          <select className="form-control" value={severity} onChange={e => setSeverity(e.target.value)}>
            <option value="">Default</option>
            {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <button type="button" className="btn btn-primary w-full" onClick={simulate} disabled={loading}>
        {loading ? <span className="spinner" /> : '⚡'}
        {loading ? ' Simulating...' : ' Simulate Incident'}
      </button>
    </div>
  );
}

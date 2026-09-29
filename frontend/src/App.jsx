import { useEffect, useState, useCallback } from 'react';
import './index.css';
import './App.css';
import { apiFetch, formatDateTime, timeSince } from './utils';
import { useToast, useInterval } from './hooks';
import SimulatorPanel from './components/SimulatorPanel';
import IncidentList from './components/IncidentList';
import IncidentDetail from './components/IncidentDetail';
import MemoryLibrary from './components/MemoryLibrary';
import RunbooksPage from './components/RunbooksPage';
import LearningLoopModal from './components/LearningLoopModal';
import AICore from './components/AICore';

// ─── Topbar Status Pill ──────────────────────────────────────────
function StatusPill({ label, connected, loading }) {
  if (loading) return <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>...</span>;
  return (
    <span className={`status-pill ${connected ? 'connected' : 'disconnected'}`}>
      <span className="dot" />
      {label}: {connected ? '●' : '○'} {connected ? 'Connected' : 'Offline'}
    </span>
  );
}

// ─── Dashboard Stats ─────────────────────────────────────────────
function DashboardStats({ incidents, activeSeverity, onSeveritySelect }) {
  const counts = incidents.reduce((acc, inc) => {
    acc[inc.severity] = (acc[inc.severity] || 0) + 1;
    acc[inc.status] = (acc[inc.status] || 0) + 1;
    return acc;
  }, {});

  const active = incidents.filter(incident => ['OPEN', 'INVESTIGATING', 'MITIGATED'].includes(incident.status)).length;
  const stats = [
    { label: 'Active incidents', value: active, note: 'Require attention', color: 'var(--critical)', filter: '' },
    { label: 'Total tracked', value: incidents.length, note: 'Across this workspace', color: 'var(--text-primary)', filter: '' },
    { label: 'Resolved', value: counts['RESOLVED'] || 0, note: 'Closed incidents', color: 'var(--hindsight)', filter: '' },
  ];

  return (
    <div className="stats-row reference-stats">
      {stats.map(s => (
        <div key={s.label} className="stat-card" style={{ borderLeftColor: s.color }}>
          <div className="stat-info">
            <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
            <div className="stat-label">{s.label}</div>
            <div className="stat-note">{s.note}</div>
          </div>
        </div>
      ))}
      <div className="severity-filter-strip">
        <span>Severity</span>
        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(severity => (
          <button key={severity} className={`severity-filter-chip ${severity.toLowerCase()}${activeSeverity === severity ? ' active' : ''}`} onClick={() => onSeveritySelect(activeSeverity === severity ? '' : severity)}>
            {severity}
            <b>{counts[severity] || 0}</b>
          </button>
        ))}
      </div>
    </div>
  );
}

function TelemetryRibbon({ incidents, syncState }) {
  const active = incidents.filter(incident => ['OPEN', 'INVESTIGATING'].includes(incident.status)).length;
  const critical = incidents.filter(incident => incident.severity === 'CRITICAL').length;
  const resolved = incidents.filter(incident => incident.status === 'RESOLVED').length;
  const signals = [
    { label: 'Active signals', value: active, tone: active ? 'amber' : 'green' },
    { label: 'Critical watch', value: critical, tone: critical ? 'red' : 'green' },
    { label: 'Resolved today', value: resolved, tone: 'cyan' },
  ];

  return (
    <div className="telemetry-ribbon" aria-label="Incident telemetry summary">
      <span className="telemetry-label"><span className={`signal-pulse ${syncState}`} /> TELEMETRY STREAM</span>
      {signals.map(signal => (
        <span key={signal.label} className="telemetry-signal">
          <span className={`signal-bar ${signal.tone}`}><i /><i /><i /><i /></span>
          <b>{signal.value}</b> {signal.label}
        </span>
      ))}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────
export default function App() {
  const { push: toast, Toast } = useToast();
  const [page, setPage] = useState('dashboard'); // dashboard | memory | runbooks
  const [incidents, setIncidents] = useState([]);
  const [allIncidents, setAllIncidents] = useState([]);
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [syncState, setSyncState] = useState('syncing');
  const [lastSync, setLastSync] = useState(null);
  const [syncError, setSyncError] = useState('');
  const [searching, setSearching] = useState(false);
  const [recentlyUpdatedId, setRecentlyUpdatedId] = useState(null);
  const [selectedInc, setSelectedInc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hindsightStatus, setHindsightStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [showLoop, setShowLoop] = useState(false);
  const [showSimulator, setShowSimulator] = useState(true);

  const loadIncidents = useCallback(async ({ silent = false, searchValue = search, severityValue = severityFilter, statusValue = statusFilter } = {}) => {
    if (!silent) setSearching(true);
    setSyncState('syncing');
    try {
      const params = new URLSearchParams();
      if (searchValue.trim()) params.set('search', searchValue.trim());
      if (severityValue) params.set('severity', severityValue);
      if (statusValue) params.set('status', statusValue);
      const [data, summary] = await Promise.all([
        apiFetch(`/api/incidents${params.toString() ? `?${params}` : ''}`),
        apiFetch('/api/incidents'),
      ]);
      setIncidents(previous => {
        const changed = data.find(item => {
          const oldItem = previous.find(previousItem => previousItem.id === item.id);
          return oldItem && oldItem.updated_at !== item.updated_at;
        });
        if (changed) {
          setRecentlyUpdatedId(changed.id);
          window.setTimeout(() => setRecentlyUpdatedId(current => current === changed.id ? null : current), 2400);
        }
        return data;
      });
      setAllIncidents(summary);
      setLastSync(new Date());
      setSyncError('');
      setSyncState('live');
      setSelectedInc(previous => previous ? data.find(item => item.id === previous.id) || previous : previous);
    } catch (e) {
      setSyncState('error');
      setSyncError(e.message);
      if (!silent) toast(`Failed to load incidents: ${e.message}`, 'error');
    } finally {
      setLoading(false);
      setSearching(false);
    }
  }, [search, severityFilter, statusFilter, toast]);

  const loadStatus = useCallback(async () => {
    try {
      const s = await apiFetch('/api/memory/status');
      setHindsightStatus(s);
    } catch {
      setHindsightStatus({ connected: false });
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => loadIncidents(), 350);
    return () => clearTimeout(timer);
  }, [search, severityFilter, statusFilter]);

  useInterval(() => { if (page === 'dashboard') loadIncidents({ silent: true }); }, 20000);

  const aiState = selectedInc
    ? (selectedInc.severity === 'CRITICAL' ? 'critical' : analysisStateFor(selectedInc))
    : (hindsightStatus?.connected ? 'recalling' : 'monitoring');

  function analysisStateFor(incident) {
    return ['INVESTIGATING'].includes(incident.status) ? 'analyzing' : 'monitoring';
  }

  const handleIncidentCreated = (inc, msg, errMsg) => {
    if (errMsg) { toast(errMsg, 'error'); return; }
    toast(msg || `Incident ${inc.id} created`, 'success');
    loadIncidents({ silent: true });
    setSelectedInc(inc);
  };

  const handleDemoPart1 = (inc) => {
    toast(`🎯 Demo Part 1: ${inc.id} created — investigate now to see empty Hindsight`, 'info');
    loadIncidents({ silent: true });
    setSelectedInc(inc);
  };

  const handleDemoPart2 = (inc) => {
    toast(`🎯 Demo Part 2: ${inc.id} created — investigate to see Hindsight recall IR-001!`, 'hindsight');
    loadIncidents({ silent: true });
    setSelectedInc(inc);
  };

  const fetchSampleAlert = async () => {
    try {
      const sample = await apiFetch('/api/incidents/simulate', {
        method: 'POST',
        body: JSON.stringify({ incident_type: 'http_5xx' }),
      });
      handleIncidentCreated(sample, `Sample alert ${sample.id} fetched`);
    } catch (e) {
      toast(`Sample alert failed: ${e.message}`, 'error');
    }
  };

  const resetDemo = async () => {
    if (!confirm('Reset all incidents and demo data? This cannot be undone.')) return;
    try {
      await apiFetch('/api/simulation/reset', { method: 'POST' });
      setIncidents([]);
      setAllIncidents([]);
      setSelectedInc(null);
      toast('Demo reset complete — ready for fresh run', 'info');
    } catch (e) {
      toast(`Reset failed: ${e.message}`, 'error');
    }
  };

  return (
    <div className="app-layout">
      {/* ── Topbar ─────────────────────────────────────── */}
      <header className="topbar">
        <a className="topbar-brand" href="#" onClick={e => { e.preventDefault(); setPage('dashboard'); setSelectedInc(null); }}>
          <div className="brand-icon">🛡️</div>
          <span>Incident Response Agent</span>
        </a>

        <nav className="topbar-nav">
          <button className={`nav-btn${page === 'dashboard' ? ' active' : ''}`} onClick={() => setPage('dashboard')}>
            🏠 Dashboard
          </button>
          <button className={`nav-btn${page === 'memory' ? ' active' : ''}`} onClick={() => setPage('memory')}>
            🧠 Memory Library
          </button>
          <button className={`nav-btn${page === 'runbooks' ? ' active' : ''}`} onClick={() => setPage('runbooks')}>
            📖 Runbooks
          </button>
        </nav>

        <div className="topbar-right">
          <button
            className="btn btn-hindsight btn-sm"
            onClick={() => setShowLoop(true)}
            style={{ marginRight: 4 }}
          >
            🎯 Demo Flow
          </button>
          <StatusPill
            label="Hindsight"
            connected={hindsightStatus?.connected}
            loading={statusLoading}
          />
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────── */}
      <main className="main-content">
        {page === 'memory' && <MemoryLibrary toast={{ push: toast }} />}
        {page === 'runbooks' && <RunbooksPage toast={{ push: toast }} />}

        {page === 'dashboard' && (
          <>
            <div className="command-strip reference-hero">
              <div>
                <span className="eyebrow">OPERATIONS / INCIDENTS</span>
                <h1>Response overview</h1>
                <p>Triage service events and coordinate a response.</p>
                <div className="sync-status">
                  <span className={`sync-dot ${syncState}`} />
                  {syncState === 'syncing' ? 'SYNCING' : syncState === 'error' ? 'CONNECTION ISSUE' : 'LIVE'}
                  <span>{lastSync ? `Updated ${formatDateTime(lastSync)}` : 'Waiting for backend'}</span>
                </div>
              </div>
              <div className="reference-actions">
                <button className="btn btn-ghost" onClick={() => loadIncidents()}>↻ Refresh</button>
                <button className="btn btn-ghost" onClick={fetchSampleAlert}>ϟ Fetch sample alert</button>
                <button className="btn btn-primary" onClick={() => setShowSimulator(true)}>＋ New incident</button>
              </div>
            </div>
            <DashboardStats incidents={allIncidents} activeSeverity={severityFilter} onSeveritySelect={setSeverityFilter} />

            <div className="dashboard-grid">
              {/* Left Sidebar */}
              <div className="triage-card">
                <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.6px', color: 'var(--text-secondary)', flex: 1 }}>
                    Triage queue
                  </h3>
                  <button className="btn btn-ghost btn-sm" onClick={() => loadIncidents()}>↻</button>
                  <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }} onClick={resetDemo}>🗑️ Reset</button>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setShowSimulator(s => !s)}
                  >
                    {showSimulator ? '▲ Hide Simulator' : '▼ Simulator'}
                  </button>
                </div>

                <div className="incident-controls">
                  <div className="triage-heading">
                    <div><span className="eyebrow">TRIAGE QUEUE</span><h2>Incidents <b>{incidents.length}</b></h2></div>
                    <div className="status-tabs">
                      {[['', 'All'], ['OPEN', 'Active'], ['RESOLVED', 'Resolved']].map(([value, label]) => (
                        <button key={label} className={statusFilter === value ? 'active' : ''} onClick={() => setStatusFilter(value)}>{label}</button>
                      ))}
                    </div>
                  </div>
                  <input
                    className="form-control"
                    value={search}
                    onChange={event => setSearch(event.target.value)}
                    placeholder="⌕ Search incidents, services, root causes..."
                    aria-label="Search incidents"
                  />
                  {severityFilter && (
                    <div className="active-filter">
                      Showing {severityFilter} incidents
                      <button type="button" onClick={() => setSeverityFilter('')}>Clear</button>
                    </div>
                  )}
                  {syncError && (
                    <div className="sync-error">
                      Unable to connect to Incident Service. <button type="button" onClick={() => loadIncidents()}>Retry</button>
                    </div>
                  )}
                </div>

                {showSimulator && (
                  <SimulatorPanel
                    onCreated={handleIncidentCreated}
                    onDemoPart1={handleDemoPart1}
                    onDemoPart2={handleDemoPart2}
                  />
                )}

                {loading || searching ? (
                  <div className="loading-overlay" style={{ padding: 24 }}>
                    <div className="spinner" />
                    <span>Loading incidents...</span>
                  </div>
                ) : (
                  <IncidentList
                    incidents={incidents}
                    selectedId={selectedInc?.id}
                    recentlyUpdatedId={recentlyUpdatedId}
                    onSelect={inc => setSelectedInc(inc)}
                  />
                )}
              </div>

              {/* Main Detail Panel */}
              <div>
                {selectedInc ? (
                  <IncidentDetail
                    key={selectedInc.id}
                    incident={selectedInc}
                    onRefresh={loadIncidents}
                    onClose={() => setSelectedInc(null)}
                    toast={{ push: toast }}
                  />
                ) : (
                  <div className="card" style={{ textAlign: 'center', padding: 64 }}>
                    <div style={{ fontSize: 56, marginBottom: 16 }}>🛡️</div>
                    <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 12, letterSpacing: '-0.3px' }}>
                      Select an incident to begin
                    </h2>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: 480, margin: '0 auto 24px' }}>
                      AI-powered incident investigation with long-term operational memory.
                      The agent recalls past incidents, correlates symptoms, and generates
                      historical recommendations via{' '}
                      <span style={{ color: 'var(--hindsight)', fontWeight: 700 }}>Hindsight</span>.
                    </p>

                    <div style={{
                      display: 'flex', gap: 16, justifyContent: 'center',
                      flexWrap: 'wrap', marginBottom: 32,
                    }}>
                      {[
                        { icon: '🔍', label: 'Hindsight Recall', desc: 'Queries past incident memory' },
                        { icon: '🤖', label: 'AI Investigation', desc: 'LLM-powered root cause analysis' },
                        { icon: '✅', label: 'Human Approval', desc: 'Operator reviews before action' },
                        { icon: '🧠', label: 'Learn & Retain', desc: 'Postmortems stored in Hindsight' },
                      ].map(f => (
                        <div key={f.label} style={{
                          background: 'var(--bg-elevated)',
                          border: '1px solid var(--border)',
                          borderRadius: 10,
                          padding: '16px 20px',
                          textAlign: 'left',
                          width: 200,
                        }}>
                          <div style={{ fontSize: 24, marginBottom: 6 }}>{f.icon}</div>
                          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{f.label}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{f.desc}</div>
                        </div>
                      ))}
                    </div>

                    <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                      <button className="btn btn-hindsight btn-lg" onClick={() => setShowLoop(true)}>
                        🎯 View Demo Flow
                      </button>
                      <button className="btn btn-primary btn-lg" onClick={() => setShowSimulator(true)}>
                        ⚡ Create Incident
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>

      {showLoop && <LearningLoopModal onClose={() => setShowLoop(false)} />}
      <Toast />
    </div>
  );
}

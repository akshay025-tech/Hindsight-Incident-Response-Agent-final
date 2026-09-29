import { useEffect, useState } from 'react';
import { apiFetch, timeSince } from '../utils';

export default function MemoryLibrary({ toast }) {
  const [library, setLibrary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [lib, stat] = await Promise.all([
          apiFetch('/api/memory/library'),
          apiFetch('/api/memory/status'),
        ]);
        setLibrary(lib);
        setStatus(stat);
      } catch (e) {
        toast?.push(`Memory library load failed: ${e.message}`, 'error');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const recall = async () => {
    const query = prompt('Recall query (e.g. "api-gateway memory leak resolution"):');
    if (!query) return;
    try {
      const result = await apiFetch(`/api/memory/recall?query=${encodeURIComponent(query)}`);
      if (result.memories?.length) {
        alert(`Found ${result.count} memories:\n\n` + result.memories.map(m => m.text.slice(0, 200)).join('\n\n---\n\n'));
      } else {
        alert('No relevant memories found for this query.');
      }
    } catch (e) {
      toast?.push(`Recall failed: ${e.message}`, 'error');
    }
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="spinner" style={{ width: 32, height: 32 }} />
        <span>Loading memory library...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Status Header */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px', color: 'var(--text-primary)', marginBottom: 4 }}>
              🧠 Hindsight Memory Library
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Operational knowledge retained from past incident postmortems
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-hindsight btn-sm" onClick={recall}>
              🔍 Recall Query
            </button>
          </div>
        </div>
        <hr className="divider" />
        <div style={{ display: 'flex', gap: 20 }}>
          <div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Status</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: status?.connected ? 'var(--success)' : 'var(--warning)',
                display: 'inline-block',
              }} />
              <span style={{ fontSize: 13, color: status?.connected ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>
                {status?.connected ? 'Hindsight Cloud Connected' : 'Local Memory Bank Active'}
              </span>
            </div>
          </div>
          <div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Bank ID</span>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, fontFamily: 'var(--mono)' }}>
              {status?.bank_id || library?.bank_id || 'incident-response-team'}
            </div>
          </div>
          <div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Memories</span>
            <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--hindsight)', marginTop: 2, fontFamily: 'var(--mono)' }}>
              {library?.count ?? 0}
            </div>
          </div>
        </div>
      </div>

      {/* Memory Cards */}
      {!library?.memories?.length ? (
        <div className="empty-state">
          <div className="empty-icon">🧠</div>
          <p>No memories retained yet.<br />Resolve an incident and generate a postmortem to seed Hindsight memory.</p>
        </div>
      ) : (
        <div className="memory-library-grid">
          {library.memories.map((mem, i) => (
            <div key={mem.id || i} className="memory-lib-card">
              <div className="memory-lib-id">
                🧠 {mem.incident_id}
                {mem.retained_in_hindsight && (
                  <span style={{
                    marginLeft: 'auto',
                    fontSize: 10,
                    padding: '2px 7px',
                    background: 'var(--hindsight-subtle)',
                    border: '1px solid rgba(167,139,250,0.25)',
                    borderRadius: 10,
                    color: 'var(--hindsight)',
                    fontWeight: 700,
                  }}>
                    RETAINED
                  </span>
                )}
              </div>

              <div className="memory-lib-item">
                <div className="memory-lib-key">Root Cause</div>
                <div className="memory-lib-val" style={{ color: 'var(--critical)', fontWeight: 600 }}>
                  {mem.root_cause}
                </div>
              </div>

              <div className="memory-lib-item">
                <div className="memory-lib-key">Resolution</div>
                <div className="memory-lib-val">{mem.resolution}</div>
              </div>

              <div className="memory-lib-item">
                <div className="memory-lib-key">Runbook</div>
                <div className="memory-lib-val" style={{ color: 'var(--hindsight)' }}>
                  📖 {mem.runbook}
                </div>
              </div>

              {mem.impact && (
                <div className="memory-lib-item">
                  <div className="memory-lib-key">Impact</div>
                  <div className="memory-lib-val">{mem.impact}</div>
                </div>
              )}

              {mem.lessons_learned?.length > 0 && (
                <div className="memory-lib-item">
                  <div className="memory-lib-key">Lesson</div>
                  <div className="memory-lib-val">{mem.lessons_learned[0]}</div>
                </div>
              )}

              <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-muted)' }}>
                📅 {mem.timestamp ? new Date(mem.timestamp).toLocaleDateString() : 'N/A'} ·{' '}
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>
                  ✅ {mem.outcome}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

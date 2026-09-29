import { useEffect, useState } from 'react';
import { apiFetch } from '../utils';

export default function RunbooksPage({ toast }) {
  const [runbooks, setRunbooks] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/runbooks')
      .then(data => { setRunbooks(data); if (data.length) setSelected(data[0]); })
      .catch(e => toast?.push(`Failed to load runbooks: ${e.message}`, 'error'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 32, height: 32 }} /><span>Loading runbooks...</span></div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20, alignItems: 'start' }}>
      {/* List */}
      <div className="card">
        <div className="card-header">
          <span>📖</span>
          <h3 className="card-title">Runbooks</h3>
        </div>
        {runbooks.map(rb => (
          <button
            key={rb.id}
            className={`incident-row${selected?.id === rb.id ? ' selected' : ''}`}
            style={{ marginBottom: 6 }}
            onClick={() => setSelected(rb)}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>{rb.name}</div>
              <span style={{
                fontSize: 10, padding: '2px 7px',
                background: rb.risk === 'high' ? 'var(--danger-subtle)' : rb.risk === 'low' ? 'var(--success-subtle)' : 'var(--warning-subtle)',
                color: rb.risk === 'high' ? 'var(--danger)' : rb.risk === 'low' ? 'var(--success)' : 'var(--warning)',
                borderRadius: 4, fontWeight: 700, textTransform: 'uppercase',
              }}>
                {rb.risk} risk
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Detail */}
      {selected && (
        <div className="card">
          <h2 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>{selected.name}</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6 }}>{selected.description}</p>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
            {selected.applicable_services?.map(s => (
              <span key={s} style={{ fontSize: 11, padding: '3px 9px', background: 'var(--accent-subtle)', border: '1px solid rgba(251,113,133,0.2)', borderRadius: 4, color: 'var(--accent-hover)', fontFamily: 'var(--mono)' }}>
                {s}
              </span>
            ))}
          </div>

          <div className="postmortem-section">
            <div className="pm-section-title">🔬 Diagnostic Steps</div>
            <ol style={{ listStyle: 'decimal', paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {selected.diagnostic_steps?.map((step, i) => (
                <li key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="postmortem-section">
            <div className="pm-section-title">🔧 Remediation Steps</div>
            <ol style={{ listStyle: 'decimal', paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {selected.remediation_steps?.map((step, i) => (
                <li key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  <code style={{ fontFamily: 'var(--mono)', fontSize: 11, background: 'var(--bg-input)', padding: '1px 5px', borderRadius: 3, color: '#60a5fa' }}>
                    {step}
                  </code>
                </li>
              ))}
            </ol>
          </div>

          <div className="postmortem-section">
            <div className="pm-section-title">✅ Success Criteria</div>
            <ul className="pm-list">
              {selected.success_criteria?.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>

          {selected.rollback && (
            <div className="postmortem-section">
              <div className="pm-section-title" style={{ color: 'var(--warning)' }}>⚠️ Rollback Procedure</div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{selected.rollback}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

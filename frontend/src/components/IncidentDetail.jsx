import { useState } from 'react';
import { apiFetch, severityClass, statusClass, logClass, formatDateTime, timeSince } from '../utils';

function MetricsGrid({ metrics }) {
  if (!metrics || !Object.keys(metrics).length) return null;
  return (
    <div className="metrics-grid">
      {Object.entries(metrics).map(([k, v]) => (
        <div key={k} className="metric-chip">
          <div className="metric-chip-value">
            {typeof v === 'number' && k.includes('percent') ? `${v}%` : v}
          </div>
          <div className="metric-chip-label">{k.replace(/_/g, ' ')}</div>
        </div>
      ))}
    </div>
  );
}

function HindsightMemoryPanel({ analysis }) {
  if (!analysis) return null;
  const { historical_memory_found, historical_memories, reflect_insight } = analysis;

  if (!historical_memory_found || !historical_memories?.length) {
    return (
      <div className="hindsight-panel">
        <div className="panel-title">🧠 HINDSIGHT MEMORY</div>
        <div style={{ fontSize: 13, color: 'var(--warning)', padding: '12px 0' }}>
          🟡 No relevant historical memory found — this is a first-occurrence incident.
        </div>
      </div>
    );
  }

  return (
    <div className="hindsight-panel">
      <div className="hindsight-header">
        <div className="panel-title">🧠 HINDSIGHT MEMORY</div>
        <span className="hindsight-found-label">
          🔍 {historical_memories.length} historical {historical_memories.length === 1 ? 'memory' : 'memories'} recalled
        </span>
      </div>
      {reflect_insight && (
        <div style={{
          background: 'var(--hindsight-subtle)',
          border: '1px solid rgba(94,234,212,0.2)',
          borderRadius: 6,
          padding: '10px 12px',
          fontSize: 12,
          color: 'var(--text-secondary)',
          marginBottom: 10,
          lineHeight: 1.6,
        }}>
          <span style={{ color: 'var(--hindsight)', fontWeight: 700, display: 'block', marginBottom: 4 }}>
            💡 Hindsight Reflection
          </span>
          {reflect_insight}
        </div>
      )}
      {historical_memories.map((m, i) => (
        <div key={i} className="memory-card">
          <p>{m.text}</p>
        </div>
      ))}
    </div>
  );
}

function HypothesesPanel({ hypotheses }) {
  if (!hypotheses?.length) return null;
  return (
    <div className="panel">
      <div className="panel-title">🔬 LIKELY ROOT CAUSES</div>
      {hypotheses.map((h, i) => (
        <div key={i} className="hypothesis-card">
          <div className="hyp-header">
            <span className="hyp-cause">{h.cause}</span>
            <span style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 12,
              background: 'var(--accent-subtle)',
              color: 'var(--accent-hover)',
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
            }}>
              {h.category || 'unknown'}
            </span>
          </div>
          <div className="confidence-bar-wrap">
            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{ width: `${Math.round(h.confidence * 100)}%` }}
              />
            </div>
            <span className="confidence-pct">{Math.round(h.confidence * 100)}%</span>
          </div>
          {h.evidence?.length > 0 && (
            <ul className="hyp-evidence">
              {h.evidence.slice(0, 4).map((ev, j) => (
                <li key={j}>{typeof ev === 'string' ? ev : JSON.stringify(ev)}</li>
              ))}
            </ul>
          )}
          {h.reasoning && (
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, lineHeight: 1.5 }}>
              {h.reasoning}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function RecommendationsPanel({ analysis, onApprove, onReject, approvalLoading, approved }) {
  if (!analysis?.recommended_actions?.length) return null;
  const recs = analysis.recommended_actions;
  const primary = recs[0];

  return (
    <div className="panel">
      <div className="panel-title">🎯 RECOMMENDED ACTION</div>
      {approved && (
        <div style={{
          background: 'var(--success-subtle)',
          border: '1px solid rgba(16,185,129,0.3)',
          borderRadius: 6,
          padding: '10px 12px',
          fontSize: 13,
          color: 'var(--success)',
          marginBottom: 12,
          fontWeight: 600,
        }}>
          ✅ Action approved by operator — remediation in progress (simulated)
        </div>
      )}
      {recs.map((rec, i) => (
        <div key={i} className="rec-card" style={{ borderColor: i === 0 ? 'rgba(251,113,133,0.5)' : 'rgba(251,113,133,0.2)' }}>
          <div className="rec-action">{i === 0 ? '⭐ ' : `${i + 1}. `}{rec.action}</div>
          {rec.reason && <div className="rec-reason">{rec.reason}</div>}
          <div className="rec-meta">
            {rec.runbook && (
              <div className="rec-meta-item">
                <span className="rec-meta-label">Runbook</span>
                <span className="rec-meta-value" style={{ color: 'var(--hindsight)' }}>📖 {rec.runbook}</span>
              </div>
            )}
            {rec.historical_support && (
              <div className="rec-meta-item">
                <span className="rec-meta-label">Historical Support</span>
                <span className="rec-meta-value" style={{ color: 'var(--hindsight)' }}>
                  🧠 Supported by {rec.historical_support}
                </span>
              </div>
            )}
            {rec.risk && (
              <div className="rec-meta-item">
                <span className="rec-meta-label">Risk Level</span>
                <span className="rec-meta-value" style={{
                  color: rec.risk === 'high' ? 'var(--danger)' : rec.risk === 'low' ? 'var(--success)' : 'var(--warning)',
                  fontWeight: 600,
                }}>
                  {rec.risk?.toUpperCase()}
                </span>
              </div>
            )}
            {rec.expected_outcome && (
              <div className="rec-meta-item" style={{ gridColumn: 'span 2' }}>
                <span className="rec-meta-label">Expected Outcome</span>
                <span className="rec-meta-value">{rec.expected_outcome}</span>
              </div>
            )}
          </div>
          {i === 0 && !approved && (
            <div className="approval-bar">
              <button
                className="btn btn-success"
                style={{ flex: 1 }}
                onClick={onApprove}
                disabled={approvalLoading}
              >
                {approvalLoading ? <span className="spinner" /> : '✅'} APPROVE
              </button>
              <button
                className="btn btn-danger"
                style={{ flex: 1 }}
                onClick={onReject}
                disabled={approvalLoading}
              >
                ❌ REJECT
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function PostmortemPanel({ incident, postmortem, onGeneratePostmortem, onDownloadPostmortem, pmLoading }) {
  const canGenerate = ['MITIGATED', 'RESOLVED'].includes(incident?.status);

  if (!postmortem && !canGenerate) {
    return (
      <div className="panel">
        <div className="panel-title">📋 POSTMORTEM</div>
        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Postmortem will be available after incident is mitigated or resolved.
        </p>
      </div>
    );
  }

  if (!postmortem) {
    return (
      <div className="panel">
        <div className="panel-title">📋 POSTMORTEM</div>
        <button
          className="btn btn-hindsight w-full"
          onClick={onGeneratePostmortem}
          disabled={pmLoading}
        >
          {pmLoading ? <span className="spinner" /> : '🧠'}
          {pmLoading ? ' Generating & Retaining...' : ' Generate Postmortem & Save to Hindsight'}
        </button>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-title">
        📋 POSTMORTEM
        {postmortem.retained_in_hindsight && (
          <span style={{
            marginLeft: 'auto',
            fontSize: 11,
            fontWeight: 700,
            color: 'var(--hindsight)',
            background: 'var(--hindsight-subtle)',
            padding: '2px 8px',
            borderRadius: 12,
            border: '1px solid rgba(94,234,212,0.25)',
          }}>
            🧠 Retained in Hindsight
          </span>
        )}
      </div>

      <button className="btn btn-hindsight btn-sm" onClick={onDownloadPostmortem} style={{ marginBottom: 12 }}>
        ⇩ Download Postmortem PDF
      </button>

      <div className="postmortem-section">
        <div className="pm-section-title">Summary</div>
        <div className="pm-section-body">{postmortem.incident_summary}</div>
      </div>

      <div className="postmortem-section">
        <div className="pm-section-title">Root Cause</div>
        <div className="pm-section-body" style={{ color: 'var(--critical)', fontWeight: 600 }}>
          {postmortem.root_cause}
        </div>
      </div>

      <div className="postmortem-section">
        <div className="pm-section-title">Resolution</div>
        <div className="pm-section-body">{postmortem.resolution}</div>
      </div>

      {postmortem.runbook_used && (
        <div className="postmortem-section">
          <div className="pm-section-title">Runbook Used</div>
          <div className="pm-section-body" style={{ color: 'var(--hindsight)' }}>
            📖 {postmortem.runbook_used}
          </div>
        </div>
      )}

      {postmortem.timeline?.length > 0 && (
        <div className="postmortem-section">
          <div className="pm-section-title">Timeline</div>
          <div className="timeline">
            {postmortem.timeline.map((t, i) => (
              <div key={i} className="timeline-item">
                <div className="timeline-dot">⏱</div>
                <div className="timeline-content">
                  <div className="timeline-ts">{t.timestamp}</div>
                  <div className="timeline-event">{t.event}</div>
                  {t.actor && <div className="timeline-actor">{t.actor}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {postmortem.lessons_learned?.length > 0 && (
        <div className="postmortem-section">
          <div className="pm-section-title">Lessons Learned</div>
          <ul className="pm-list">
            {postmortem.lessons_learned.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </div>
      )}

      {postmortem.follow_up_actions?.length > 0 && (
        <div className="postmortem-section">
          <div className="pm-section-title">Follow-up Actions</div>
          <ul className="pm-list">
            {postmortem.follow_up_actions.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      {postmortem.retained_in_hindsight && (
        <div style={{
          background: 'var(--hindsight-subtle)',
          border: '1px solid rgba(94,234,212,0.3)',
          borderRadius: 8,
          padding: '12px 14px',
          marginTop: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--hindsight)',
        }}>
          🧠 Incident knowledge retained in Hindsight. Future similar incidents will benefit from this learning.
        </div>
      )}
    </div>
  );
}

export default function IncidentDetail({
  incident,
  onRefresh,
  onClose,
  toast,
}) {
  const [analysis, setAnalysis] = useState(null);
  const [postmortem, setPostmortem] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [approved, setApproved] = useState(false);
  const [pmLoading, setPmLoading] = useState(false);
  const [inc, setInc] = useState(incident);

  const refresh = async () => {
    try {
      const updated = await apiFetch(`/api/incidents/${inc.id}`);
      setInc(updated);
      onRefresh?.();
    } catch {}
  };

  const analyze = async () => {
    setAnalyzing(true);
    try {
      const result = await apiFetch(`/api/agents/analyze/${inc.id}`, { method: 'POST' });
      setAnalysis(result);
      await refresh();
      toast.push(`AI investigation complete for ${inc.id}`, 'success');
      if (result.historical_memory_found) {
        toast.push(`🧠 Historical memory recalled! Found ${result.historical_memories?.length} relevant incidents`, 'hindsight');
      }
    } catch (e) {
      toast.push(`Analysis failed: ${e.message}`, 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const approve = async () => {
    setApprovalLoading(true);
    try {
      await apiFetch(`/api/incidents/${inc.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ decision: 'approve', operator_comment: 'Approved from Incident Command Center' }),
      });
      setApproved(true);
      await refresh();
      toast.push(`Remediation approved for ${inc.id}`, 'success');
    } catch (e) {
      toast.push(`Approval failed: ${e.message}`, 'error');
    } finally {
      setApprovalLoading(false);
    }
  };

  const reject = async () => {
    setApprovalLoading(true);
    try {
      await apiFetch(`/api/incidents/${inc.id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ decision: 'reject', operator_comment: 'Rejected by operator' }),
      });
      await refresh();
      toast.push(`Recommendation rejected for ${inc.id}`, 'info');
    } catch (e) {
      toast.push(`Rejection failed: ${e.message}`, 'error');
    } finally {
      setApprovalLoading(false);
    }
  };

  const generatePostmortem = async () => {
    setPmLoading(true);
    try {
      const pm = await apiFetch(`/api/postmortems/${inc.id}`, {
        method: 'POST',
        body: JSON.stringify({ operator_feedback: 'Incident resolved successfully.' }),
      });
      setPostmortem(pm);
      await refresh();
      toast.push(`Postmortem generated for ${inc.id}`, 'success');
      if (pm.retained_in_hindsight) {
        toast.push('🧠 Incident knowledge retained in Hindsight!', 'hindsight');
      }
    } catch (e) {
      toast.push(`Postmortem failed: ${e.message}`, 'error');
    } finally {
      setPmLoading(false);
    }
  };

  const downloadPostmortem = async () => {
    try {
      const response = await fetch(`/api/postmortems/${inc.id}/download`);
      if (!response.ok) throw new Error('Unable to generate report');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `postmortem-${inc.id}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
      toast.push('Postmortem PDF downloaded', 'success');
    } catch (e) {
      toast.push(`Postmortem download failed: ${e.message}`, 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Header */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span className={`badge ${severityClass(inc.severity)}`}>{inc.severity}</span>
              <span className={`badge ${statusClass(inc.status)}`}>{inc.status}</span>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 700, color: 'var(--accent-hover)' }}>
                {inc.id}
              </span>
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6, letterSpacing: '-0.3px' }}>
              {inc.title}
            </h2>
            <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
              <span>🖥️ {inc.service}</span>
              {inc.deployment?.version && <span>📦 {inc.deployment.version}</span>}
            </div>
            <div className="incident-timestamps">
              <span><b>Detected</b> {formatDateTime(inc.created_at)}</span>
              <span><b>Last updated</b> {formatDateTime(inc.updated_at)}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost btn-sm" onClick={refresh}>↻ Refresh</button>
            <button className="btn btn-ghost btn-sm" onClick={onClose}>✕ Close</button>
          </div>
        </div>

        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{inc.description}</p>

        {inc.symptoms?.length > 0 && (
          <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {inc.symptoms.map((s, i) => (
              <span key={i} style={{
                fontSize: 11,
                padding: '3px 8px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 4,
                color: 'var(--text-secondary)',
              }}>
                {s}
              </span>
            ))}
          </div>
        )}

        <MetricsGrid metrics={inc.metrics} />

        {inc.logs?.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="pm-section-title" style={{ marginBottom: 6 }}>Recent Logs</div>
            <div className="log-block">
              {inc.logs.map((l, i) => (
                <div key={i} className={logClass(l)}>{l}</div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: 14 }}>
          <button
            className="btn btn-primary w-full"
            onClick={analyze}
            disabled={analyzing}
          >
            {analyzing ? <span className="spinner" /> : '🤖'}
            {analyzing ? ' AI Investigating...' : analysis ? ' Re-Analyze' : ' Start AI Investigation'}
          </button>
          {analyzing && (
            <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
              Querying Hindsight memory bank · Generating hypotheses · Matching runbooks...
            </p>
          )}
        </div>
      </div>

      {analysis && (
        <>
          {/* AI Summary */}
          <div className="card card-sm">
            <div className="panel-title">🤖 AI INVESTIGATION SUMMARY</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {analysis.summary}
            </p>
            {analysis.confidence_score > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10 }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Overall Confidence</span>
                <div style={{ flex: 1, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.round(analysis.confidence_score * 100)}%`,
                    background: 'linear-gradient(90deg, var(--accent), var(--hindsight))',
                    borderRadius: 2,
                    transition: 'width 0.6s',
                  }} />
                </div>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--accent-hover)' }}>
                  {Math.round(analysis.confidence_score * 100)}%
                </span>
              </div>
            )}
          </div>

          <HindsightMemoryPanel analysis={analysis} />
          <HypothesesPanel hypotheses={analysis.hypotheses} />

          {analysis.recommended_runbooks?.length > 0 && (
            <div className="panel">
              <div className="panel-title">📖 MATCHED RUNBOOKS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {analysis.recommended_runbooks.map((rb, i) => (
                  <span key={i} style={{
                    padding: '5px 12px',
                    background: 'var(--hindsight-subtle)',
                    border: '1px solid rgba(94,234,212,0.25)',
                    borderRadius: 20,
                    fontSize: 12,
                    color: 'var(--hindsight)',
                    fontWeight: 600,
                  }}>
                    📖 {rb}
                  </span>
                ))}
              </div>
            </div>
          )}

          <RecommendationsPanel
            analysis={analysis}
            onApprove={approve}
            onReject={reject}
            approvalLoading={approvalLoading}
            approved={approved}
          />

          <PostmortemPanel
            incident={inc}
            postmortem={postmortem}
            onGeneratePostmortem={generatePostmortem}
            onDownloadPostmortem={downloadPostmortem}
            pmLoading={pmLoading}
          />
        </>
      )}
    </div>
  );
}

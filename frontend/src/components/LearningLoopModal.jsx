/**
 * LearningLoopModal — shows the critical Hindsight learning loop flow
 * Demo Part 1 → Postmortem → Retain → Demo Part 2 → Recall → Historical Recommendation
 */
export default function LearningLoopModal({ onClose }) {
  const steps = [
    { icon: '⚡', label: 'IR-001 (High CPU)', sub: 'First incident — no historical memory', phase: 'DEMO PART 1', color: 'var(--warning)' },
    { icon: '🤖', label: 'AI Investigation', sub: 'Hindsight returns empty — first occurrence', phase: 'ANALYZE', color: 'var(--accent-hover)' },
    { icon: '✅', label: 'Operator Approves Rollback', sub: 'Human-in-the-loop approval', phase: 'APPROVE', color: 'var(--success)' },
    { icon: '📋', label: 'Postmortem Generated', sub: 'Root cause: Deployment memory leak', phase: 'POSTMORTEM', color: 'var(--text-primary)' },
    { icon: '🧠', label: 'Retained in Hindsight', sub: 'Knowledge permanently stored in memory bank', phase: 'RETAIN', color: 'var(--hindsight)' },
    { icon: '⚡', label: 'IR-002 (High CPU — Similar)', sub: 'Second incident — same service, same pattern', phase: 'DEMO PART 2', color: 'var(--warning)' },
    { icon: '🔍', label: 'Hindsight Recalls IR-001', sub: '3 historical memories returned instantly', phase: 'RECALL', color: 'var(--hindsight)' },
    { icon: '🎯', label: 'Historical Recommendation', sub: 'Rollback — backed by IR-001 precedent', phase: 'RECOMMEND', color: 'var(--accent-hover)' },
    { icon: '🚀', label: 'Faster Resolution', sub: 'Agent learned from history — MTTR cut dramatically', phase: 'RESULT', color: 'var(--success)' },
  ];

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
    }}>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-bright)',
        borderRadius: 'var(--radius-lg)',
        padding: 32,
        maxWidth: 640,
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
              🧠 Hindsight Learning Loop
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              The core hackathon demonstration flow
            </p>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕ Close</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {steps.map((step, i) => (
            <div key={i} style={{ display: 'flex', gap: 16, position: 'relative' }}>
              {/* Vertical line */}
              {i < steps.length - 1 && (
                <div style={{
                  position: 'absolute', left: 19, top: 40, bottom: -4,
                  width: 2,
                  background: i === 4 ? 'linear-gradient(to bottom, var(--hindsight), var(--accent))' : 'var(--border)',
                }} />
              )}
              <div style={{
                width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18,
                  background: step.color === 'var(--hindsight)' ? 'var(--hindsight-subtle)' : 'var(--accent-subtle)',
                border: `2px solid ${step.color}`,
                color: step.color,
                position: 'relative', zIndex: 1,
              }}>
                {step.icon}
              </div>
              <div style={{ flex: 1, paddingBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontSize: 9, fontWeight: 800, padding: '2px 7px',
                    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                    borderRadius: 4, color: 'var(--text-muted)',
                    textTransform: 'uppercase', letterSpacing: '0.6px',
                  }}>{step.phase}</span>
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: step.color, marginTop: 4 }}>{step.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{step.sub}</div>
              </div>
            </div>
          ))}
        </div>

        <div style={{
          background: 'var(--hindsight-subtle)',
          border: '1px solid rgba(94,234,212,0.3)',
          borderRadius: 8,
          padding: '14px 16px',
          marginTop: 8,
          fontSize: 13,
          color: 'var(--hindsight)',
          fontWeight: 600,
        }}>
          🎯 This is the main hackathon demonstration — the agent learns from IR-001 and uses that knowledge to resolve IR-002 faster.
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={onClose}>
            Start Demo →
          </button>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';

const CORE_STATES = {
  monitoring: { label: 'Monitoring', tone: 'normal', detail: 'Watching live incident telemetry' },
  analyzing: { label: 'Analyzing', tone: 'analyzing', detail: 'Correlating evidence and hypotheses' },
  recalling: { label: 'Recalling Memory', tone: 'recalling', detail: 'Searching Hindsight operational memory' },
  learning: { label: 'Learning', tone: 'learning', detail: 'Capturing postmortem knowledge' },
  critical: { label: 'Critical Alert', tone: 'critical', detail: 'A critical incident needs attention' },
};

export default function AICore({ state = 'monitoring' }) {
  const current = CORE_STATES[state] || CORE_STATES.monitoring;
  const [expanded, setExpanded] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const handlePointerMove = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 14;
    const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * -10;
    setTilt({ x: y, y: x });
  };

  return (
    <button
      type="button"
      className={`ai-core ai-core-${current.tone}${expanded ? ' expanded' : ''}`}
      style={{ '--core-tilt-x': `${tilt.x}deg`, '--core-tilt-y': `${tilt.y}deg` }}
      aria-label={`AI Core: ${current.label}`}
      aria-expanded={expanded}
      onClick={() => setExpanded(value => !value)}
      onPointerMove={handlePointerMove}
      onPointerLeave={() => setTilt({ x: 0, y: 0 })}
    >
      <span className="ai-core-stage">
        <span className="ai-core-orbit ai-core-orbit-one" />
        <span className="ai-core-orbit ai-core-orbit-two" />
        <span className="ai-core-orbit ai-core-orbit-three" />
        <span className="ai-core-node ai-core-node-one" />
        <span className="ai-core-node ai-core-node-two" />
        <span className="ai-core-node ai-core-node-three" />
        <span className="ai-core-orb"><span>AI</span></span>
      </span>
      <div className="ai-core-copy">
        <span className="ai-core-kicker">AI CORE</span>
        <strong>{current.label}</strong>
        <span className="ai-core-hint">{expanded ? 'Click to collapse' : 'Inspect core'}</span>
      </div>
      {expanded && <span className="ai-core-detail">{current.detail}</span>}
    </button>
  );
}

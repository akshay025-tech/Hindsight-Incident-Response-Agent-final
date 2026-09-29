import { formatDateTime, timeSince, severityClass, statusClass } from '../utils';

export default function IncidentList({ incidents, selectedId, recentlyUpdatedId, onSelect }) {
  if (!incidents.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📋</div>
        <p>No incidents yet. Use the simulator to create one.</p>
      </div>
    );
  }

  return (
    <div className="incident-list">
      {incidents.map(inc => (
        <button
          key={inc.id}
          className={`incident-row incident-row-${(inc.severity || 'low').toLowerCase()}${selectedId === inc.id ? ' selected' : ''}${recentlyUpdatedId === inc.id ? ' recently-updated' : ''}`}
          onClick={() => onSelect(inc)}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3, flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className={`badge ${severityClass(inc.severity)}`}>{inc.severity}</span>
              <span className={`badge ${statusClass(inc.status)}`}>{inc.status}</span>
            </div>
            <span className="incident-title" style={{ marginTop: 2 }}>{inc.title}</span>
            <span className="incident-service">{inc.service}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 700, color: 'var(--accent-hover)' }}>
              {inc.id}
            </span>
            <span className="incident-time" title={`Detected ${formatDateTime(inc.created_at)}\nUpdated ${formatDateTime(inc.updated_at)}`}>
              Detected {formatDateTime(inc.created_at)}
            </span>
            <span className="incident-time">Updated {timeSince(inc.updated_at)}</span>
            {recentlyUpdatedId === inc.id && <span className="updated-marker">● UPDATED</span>}
          </div>
        </button>
      ))}
    </div>
  );
}

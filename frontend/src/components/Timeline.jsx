import React from 'react';

/**
 * Vertical Incident Timeline Component
 * Chronological sequence of telemetry changes, log alerts, metric spikes, and span delays.
 * Filterable by selected service; highlights items linked to root cause.
 */
export default function Timeline({ timeline, selectedService, onInspectEvidence, topCandidateEvidenceIds = [] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="card-empty-state">
        <p>No timeline records for this window.</p>
      </div>
    );
  }

  // Filter if service is selected in topology graph
  const filteredTimeline = selectedService
    ? timeline.filter((item) => item.service?.toLowerCase() === selectedService.toLowerCase())
    : timeline;

  const getKindBadge = (kind) => {
    switch (kind) {
      case 'change':
        return { label: 'CHANGE', color: '#ec4899', icon: '⚡' };
      case 'metric':
        return { label: 'METRIC', color: '#06b6d4', icon: '📈' };
      case 'log':
        return { label: 'LOG', color: '#f59e0b', icon: '📝' };
      case 'trace':
        return { label: 'TRACE', color: '#8b5cf6', icon: '⏱️' };
      default:
        return { label: 'ANOMALY', color: '#ef4444', icon: '🚨' };
    }
  };

  return (
    <div className="timeline-container">
      <div className="timeline-header">
        <div>
          <h3 className="section-title">Correlated Incident Sequence</h3>
          <p className="section-subtitle">
            Time-ordered telemetry timeline linking multi-modal signals to candidate hypotheses.
          </p>
        </div>
        <span className="timeline-count-badge">
          {filteredTimeline.length} Event{filteredTimeline.length > 1 ? 's' : ''}
          {selectedService && ` on ${selectedService}`}
        </span>
      </div>

      <div className="timeline-stream">
        {filteredTimeline.map((item, idx) => {
          const kindInfo = getKindBadge(item.kind);
          const hasEvidence = item.evidence_ids && item.evidence_ids.length > 0;
          const firstEid = hasEvidence ? item.evidence_ids[0] : null;
          const isLinkedToTop = item.evidence_ids?.some((eid) => topCandidateEvidenceIds.includes(eid));

          // Format UTC time (HH:MM:SS)
          const timeFormatted = item.ts ? item.ts.substring(11, 19) : '--:--:--';

          return (
            <div
              key={idx}
              className={`timeline-entry ${isLinkedToTop ? 'linked-to-top-cause' : ''}`}
            >
              {/* Timeline Left Timestamp & Dot */}
              <div className="timeline-time-col">
                <span className="time-badge">{timeFormatted}</span>
                <div
                  className="timeline-node-dot"
                  style={{ borderColor: kindInfo.color, backgroundColor: isLinkedToTop ? kindInfo.color : '#0f172a' }}
                >
                  <span className="dot-icon">{kindInfo.icon}</span>
                </div>
              </div>

              {/* Timeline Event Content Box */}
              <div className="timeline-content-card">
                <div className="timeline-meta-row">
                  <div className="badges-group">
                    <span
                      className="kind-pill"
                      style={{ color: kindInfo.color, backgroundColor: `${kindInfo.color}1a` }}
                    >
                      {kindInfo.label}
                    </span>
                    <span className="service-pill">{item.service}</span>
                    {isLinkedToTop && (
                      <span className="root-cause-link-badge">★ Root Cause Link</span>
                    )}
                  </div>

                  {hasEvidence && (
                    <button
                      className="btn-inspect-link"
                      onClick={() => onInspectEvidence(firstEid, item.service)}
                      title={`Inspect telemetry #${firstEid}`}
                    >
                      Inspect #{firstEid} ↗
                    </button>
                  )}
                </div>

                <p className="timeline-summary-text">{item.summary}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

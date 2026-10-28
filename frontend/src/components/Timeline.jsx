import React, { useState } from 'react';

/**
 * User-Friendly Incident Timeline Component
 * Presents multi-modal telemetry events in an elegant, human-readable enterprise feed.
 */
export default function Timeline({
  timeline = [],
  selectedService,
  onInspectEvidence,
  topCandidateEvidenceIds = [],
}) {
  const [filterType, setFilterType] = useState('all');

  if (!timeline || timeline.length === 0) {
    return (
      <div className="timeline-empty-card">
        <span className="empty-icon">🕒</span>
        <h4>No Incident Events</h4>
        <p>No telemetry events detected for this time window.</p>
      </div>
    );
  }

  // Friendly service label mapper
  const formatServiceName = (srv) => {
    if (!srv) return 'System';
    const names = {
      payment: 'Payment Service',
      checkout: 'Checkout Service',
      frontend: 'Frontend Gateway',
      cart: 'Cart Service',
      user: 'User Profile Service',
      db: 'Database Cluster',
      catalogue: 'Catalog Service',
      orders: 'Order Service',
    };
    return names[srv.toLowerCase()] || `${srv.charAt(0).toUpperCase() + srv.slice(1)} Service`;
  };

  const serviceIcons = {
    payment: '🗄️',
    checkout: '🛒',
    frontend: '💻',
    cart: '🛍️',
    user: '👤',
    db: '💾',
  };

  // Human-friendly signal kinds
  const getKindDetails = (kind) => {
    switch (kind?.toLowerCase()) {
      case 'change':
        return {
          label: 'Config Change',
          color: '#b83280',
          bg: '#fdf2f8',
          border: '#fbcfe8',
          icon: '⚡',
        };
      case 'metric':
        return {
          label: 'Metric Anomaly',
          color: '#2b6cb0',
          bg: '#ebf8ff',
          border: '#bee3f8',
          icon: '📈',
        };
      case 'log':
        return {
          label: 'Log Warning',
          color: '#c05621',
          bg: '#fffaf0',
          border: '#fbd38d',
          icon: '📝',
        };
      case 'trace':
        return {
          label: 'Trace Latency',
          color: '#6b46c1',
          bg: '#faf5ff',
          border: '#e9d8fd',
          icon: '⏱️',
        };
      default:
        return {
          label: 'System Alert',
          color: '#c53030',
          bg: '#fff5f5',
          border: '#fed7d7',
          icon: '🚨',
        };
    }
  };

  // Clean human-friendly summary text (clean up raw code syntax)
  const formatSummary = (raw) => {
    if (!raw) return '';
    return raw
      .replace(/log:([a-zA-Z0-9_]+)/g, 'log alert ($1)')
      .replace(/pool_size\s*50\s*->\s*5/g, 'connection pool reduced from 50 to 5')
      .replace(/error_rate\s*spike/gi, 'Error rate spike')
      .replace(/within\s*5000ms/gi, 'timeout limit of 5.0 seconds');
  };

  // Filter items
  const filteredTimeline = timeline.filter((item) => {
    if (selectedService && item.service?.toLowerCase() !== selectedService.toLowerCase()) {
      return false;
    }
    if (filterType !== 'all' && item.kind?.toLowerCase() !== filterType) {
      return false;
    }
    return true;
  });

  return (
    <div className="timeline-container-card">
      {/* Header Bar */}
      <div className="timeline-header-bar">
        <div className="timeline-title-group">
          <div className="timeline-header-icon-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div>
            <h3 className="timeline-heading">Correlated Incident Sequence</h3>
            <p className="timeline-subheading">
              Chronological feed of configuration changes, error logs, and performance anomalies.
            </p>
          </div>
        </div>

        {/* Filter Badges & Event Count */}
        <div className="timeline-actions-wrap">
          <div className="timeline-type-filters">
            <button
              className={`filter-chip ${filterType === 'all' ? 'active' : ''}`}
              onClick={() => setFilterType('all')}
            >
              All Events ({timeline.length})
            </button>
            <button
              className={`filter-chip ${filterType === 'change' ? 'active' : ''}`}
              onClick={() => setFilterType('change')}
            >
              Changes
            </button>
            <button
              className={`filter-chip ${filterType === 'log' ? 'active' : ''}`}
              onClick={() => setFilterType('log')}
            >
              Logs
            </button>
            <button
              className={`filter-chip ${filterType === 'metric' ? 'active' : ''}`}
              onClick={() => setFilterType('metric')}
            >
              Metrics
            </button>
          </div>

          {selectedService && (
            <div className="filtered-service-pill">
              <span>Filtered by: <strong>{formatServiceName(selectedService)}</strong></span>
            </div>
          )}
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="timeline-stream-wrapper">
        <div className="timeline-vertical-spine"></div>

        <div className="timeline-events-list">
          {filteredTimeline.map((item, idx) => {
            const kindDetails = getKindDetails(item.kind);
            const hasEvidence = item.evidence_ids && item.evidence_ids.length > 0;
            const firstEid = hasEvidence ? item.evidence_ids[0] : null;
            const isRootLink = item.evidence_ids?.some((eid) =>
              topCandidateEvidenceIds.includes(eid)
            );
            const timeStr = item.ts ? item.ts.substring(11, 19) + ' UTC' : '--:--:--';
            const srvIcon = serviceIcons[item.service?.toLowerCase()] || '🖥️';

            return (
              <div
                key={`timeline-item-${idx}`}
                className={`timeline-row-item ${isRootLink ? 'is-root-cause' : ''}`}
              >
                {/* Time & Dot Node */}
                <div className="timeline-node-column">
                  <div className="timeline-time-text">{timeStr}</div>
                  <div
                    className="timeline-icon-node"
                    style={{
                      borderColor: kindDetails.color,
                      backgroundColor: isRootLink ? kindDetails.color : '#ffffff',
                      color: isRootLink ? '#ffffff' : kindDetails.color,
                    }}
                    title={kindDetails.label}
                  >
                    <span>{kindDetails.icon}</span>
                  </div>
                </div>

                {/* Event Card Content */}
                <div className={`timeline-card-box ${isRootLink ? 'highlight-root' : ''}`}>
                  <div className="timeline-card-topbar">
                    <div className="badges-cluster">
                      {/* Kind Pill */}
                      <span
                        className="badge-kind-pill"
                        style={{
                          color: kindDetails.color,
                          backgroundColor: kindDetails.bg,
                          border: `1px solid ${kindDetails.border}`,
                        }}
                      >
                        {kindDetails.icon} {kindDetails.label}
                      </span>

                      {/* Service Tag */}
                      <span className="badge-service-pill">
                        {srvIcon} {formatServiceName(item.service)}
                      </span>

                      {/* Root Cause Link Tag */}
                      {isRootLink && (
                        <span className="badge-root-link">
                          ★ Root Cause Evidence
                        </span>
                      )}
                    </div>

                    {/* Friendly Evidence Inspection Button */}
                    {hasEvidence && (
                      <div className="evidence-btn-wrap">
                        <button
                          type="button"
                          className="btn-inspect-evidence-clean"
                          onClick={() => onInspectEvidence(firstEid, item.service)}
                          title="Open verified raw telemetry proof"
                        >
                          <span className="btn-icon">🔍</span>
                          <span>View Evidence</span>
                        </button>
                        <span className="evidence-ref-pill">Ref: {firstEid}</span>
                      </div>
                    )}
                  </div>

                  {/* Summary Text */}
                  <div className="timeline-event-summary">
                    <p className="event-summary-text">{formatSummary(item.summary)}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

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
        <span className="material-symbols-outlined empty-icon">schedule</span>
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

  // Google Material Symbols for services
  const serviceIcons = {
    payment: 'credit_card',
    checkout: 'shopping_cart',
    frontend: 'desktop_windows',
    cart: 'shopping_bag',
    user: 'person',
    db: 'database',
    catalogue: 'inventory_2',
    orders: 'receipt_long',
  };

  // Human-friendly signal kinds with Google Material Symbols
  const getKindDetails = (kind) => {
    switch (kind?.toLowerCase()) {
      case 'change':
        return {
          label: 'Config Change',
          color: '#d946ef',
          bg: '#fdf4ff',
          border: '#f0abfc',
          icon: 'bolt',
        };
      case 'metric':
        return {
          label: 'Metric Anomaly',
          color: '#2563eb',
          bg: '#eff6ff',
          border: '#93c5fd',
          icon: 'trending_up',
        };
      case 'log':
        return {
          label: 'Log Warning',
          color: '#d97706',
          bg: '#fffbeb',
          border: '#fde68a',
          icon: 'receipt_long',
        };
      case 'trace':
        return {
          label: 'Trace Latency',
          color: '#7c3aed',
          bg: '#f5f3ff',
          border: '#c4b5fd',
          icon: 'speed',
        };
      default:
        return {
          label: 'System Alert',
          color: '#dc2626',
          bg: '#fef2f2',
          border: '#fca5a5',
          icon: 'warning',
        };
    }
  };

  // Clean human-friendly summary text
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
    <div className="timeline-container-card division-timeline-card">
      {/* Header Bar */}
      <div className="timeline-header-bar">
        <div className="timeline-title-group">
          <div className="timeline-header-icon-badge division-header-icon-box">
            <span className="material-symbols-outlined">timeline</span>
          </div>
          <div>
            <div className="division-pretitle-tag">CHRONOLOGICAL EVENT FEED</div>
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
              <span className="material-symbols-outlined sym-icon-xs">view_list</span>
              All ({timeline.length})
            </button>
            <button
              className={`filter-chip ${filterType === 'change' ? 'active' : ''}`}
              onClick={() => setFilterType('change')}
            >
              <span className="material-symbols-outlined sym-icon-xs">bolt</span>
              Changes
            </button>
            <button
              className={`filter-chip ${filterType === 'log' ? 'active' : ''}`}
              onClick={() => setFilterType('log')}
            >
              <span className="material-symbols-outlined sym-icon-xs">receipt_long</span>
              Logs
            </button>
            <button
              className={`filter-chip ${filterType === 'metric' ? 'active' : ''}`}
              onClick={() => setFilterType('metric')}
            >
              <span className="material-symbols-outlined sym-icon-xs">trending_up</span>
              Metrics
            </button>
          </div>

          {selectedService && (
            <div className="filtered-service-pill">
              <span className="material-symbols-outlined sym-icon-xs">filter_alt</span>
              <span>Filtered: <strong>{formatServiceName(selectedService)}</strong></span>
            </div>
          )}
        </div>
      </div>

      {/* Timeline Stream with Distinct Sub-Division Cards */}
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
            const srvIcon = serviceIcons[item.service?.toLowerCase()] || 'dns';

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
                    <span className="material-symbols-outlined sym-icon-sm">{kindDetails.icon}</span>
                  </div>
                </div>

                {/* Event Card Content with Multi-Layer Border and Shadow */}
                <div className={`timeline-card-box ${isRootLink ? 'highlight-root' : ''} kind-${item.kind?.toLowerCase() || 'default'}`}>
                  <div className="timeline-card-topbar">
                    <div className="badges-cluster">
                      {/* Kind Pill */}
                      <span
                        className="badge-kind-pill"
                        style={{
                          color: kindDetails.color,
                          backgroundColor: kindDetails.bg,
                          border: `1.5px solid ${kindDetails.border}`,
                        }}
                      >
                        <span className="material-symbols-outlined sym-icon-xs">{kindDetails.icon}</span>
                        {kindDetails.label}
                      </span>

                      {/* Service Tag */}
                      <span className="badge-service-pill">
                        <span className="material-symbols-outlined sym-icon-xs">{srvIcon}</span>
                        {formatServiceName(item.service)}
                      </span>

                      {/* Root Cause Link Tag */}
                      {isRootLink && (
                        <span className="badge-root-link">
                          <span className="material-symbols-outlined sym-icon-xs">stars</span>
                          Root Cause Evidence
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
                          <span className="material-symbols-outlined sym-icon-xs">search</span>
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

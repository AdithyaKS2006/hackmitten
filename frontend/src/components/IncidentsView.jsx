import React, { useState } from 'react';

export default function IncidentsView({
  scenarios = [],
  selectedScenario,
  onSelectScenario,
  onNavigateToConsole,
}) {
  const [filter, setFilter] = useState('all');

  const incidentDetails = {
    mock: {
      category: 'cascade',
      severity: 'Critical',
      affected: ['payment', 'checkout', 'frontend'],
      rootCause: 'Database connection pool starved following config change (50 -> 5).',
      duration: '45 mins',
      status: 'Active Incident',
      signals: [
        { icon: 'bolt', text: 'Config Change' },
        { icon: 'receipt_long', text: 'Log Alert' },
        { icon: 'trending_up', text: 'Metric Spike' },
      ],
    },
    syn_1: {
      category: 'resource',
      severity: 'Critical',
      affected: ['payment', 'checkout'],
      rootCause: 'Payment service connection pool starvation under traffic spike.',
      duration: '32 mins',
      status: 'Active Incident',
      signals: [
        { icon: 'bolt', text: 'Config Change' },
        { icon: 'receipt_long', text: 'Log Alert' },
      ],
    },
    syn_2: {
      category: 'regression',
      severity: 'High',
      affected: ['cart', 'frontend'],
      rootCause: 'NullPointer exception introduced in release deploy v2.',
      duration: '18 mins',
      status: 'Investigating',
      signals: [
        { icon: 'bolt', text: 'Deploy Event' },
        { icon: 'emergency', text: 'Crash Logs' },
      ],
    },
    syn_3: {
      category: 'database',
      severity: 'High',
      affected: ['db', 'checkout', 'payment'],
      rootCause: 'Row lock contention saturation in core database without deployment.',
      duration: '25 mins',
      status: 'Investigating',
      signals: [
        { icon: 'trending_up', text: 'Latency Metric' },
        { icon: 'timer', text: 'Lock Spans' },
      ],
    },
    syn_4: {
      category: 'memory',
      severity: 'Medium',
      affected: ['checkout'],
      rootCause: 'JVM heap exhaustion with misleading concurrent frontend release.',
      duration: '50 mins',
      status: 'Investigating',
      signals: [
        { icon: 'trending_up', text: 'Memory Leak' },
        { icon: 'bolt', text: 'Red Herring Deploy' },
      ],
    },
    syn_5: {
      category: 'external',
      severity: 'Warning',
      affected: ['checkout', 'payment'],
      rootCause: 'Third-party payment gateway outage; safely guarded under Rule 5.',
      duration: '60 mins',
      status: 'External Outage (Guarded)',
      signals: [
        { icon: 'timer', text: 'Gateway Timeout' },
        { icon: 'shield', text: 'Refusal Guard' },
      ],
    },
  };

  const filteredScenarios = scenarios.filter((sc) => {
    if (filter === 'all') return true;
    const details = incidentDetails[sc.id] || {};
    if (filter === 'critical') return details.severity === 'Critical';
    if (filter === 'external') return details.category === 'external';
    if (filter === 'code') return details.category === 'regression';
    return true;
  });

  return (
    <div className="incidents-page-container">
      {/* Top Banner */}
      <div className="incidents-header-card">
        <div className="incidents-header-info">
          <div className="incidents-pretitle">INCIDENT MANAGEMENT CONSOLE</div>
          <h2 className="incidents-title">Active & Historical Microservice Incidents</h2>
          <p className="incidents-subtitle">
            Catalog of multi-modal failure scenarios evaluated against automated root cause attribution models.
          </p>
        </div>

        {/* Filter Chips */}
        <div className="incidents-filters-bar">
          <button
            className={`incident-filter-chip ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Incidents ({scenarios.length})
          </button>
          <button
            className={`incident-filter-chip ${filter === 'critical' ? 'active' : ''}`}
            onClick={() => setFilter('critical')}
          >
            Critical Cascades
          </button>
          <button
            className={`incident-filter-chip ${filter === 'code' ? 'active' : ''}`}
            onClick={() => setFilter('code')}
          >
            Deploy Regressions
          </button>
          <button
            className={`incident-filter-chip ${filter === 'external' ? 'active' : ''}`}
            onClick={() => setFilter('external')}
          >
            External Outages
          </button>
        </div>
      </div>

      {/* Incidents Grid */}
      <div className="incidents-cards-grid">
        {filteredScenarios.map((sc) => {
          const meta = incidentDetails[sc.id] || {
            severity: 'Medium',
            affected: ['service'],
            rootCause: 'Telemetry anomaly detected.',
            duration: '30 mins',
            status: 'Investigating',
            signals: [{ icon: 'trending_up', text: 'Anomaly' }],
          };

          const isSelected = selectedScenario === sc.id;
          const isCritical = meta.severity === 'Critical';
          const isExternal = meta.category === 'external';

          return (
            <div
              key={sc.id}
              className={`incident-card-item ${isSelected ? 'selected' : ''} ${isCritical ? 'critical-border' : ''}`}
            >
              <div className="incident-card-header">
                <div className="incident-badge-row">
                  <span
                    className={`severity-badge ${isCritical ? 'sev-crit' : isExternal ? 'sev-guard' : 'sev-high'}`}
                  >
                    {meta.severity.toUpperCase()}
                  </span>
                  <span className="incident-id-pill">ID: {sc.id}</span>
                </div>
                <span className="incident-duration-text">
                  <span className="material-symbols-outlined sym-icon-xs">timer</span>
                  {meta.duration}
                </span>
              </div>

              <h3 className="incident-card-title">{sc.name || sc.id}</h3>
              <p className="incident-card-summary">{meta.rootCause}</p>

              {/* Signals and Affected Services */}
              <div className="incident-meta-details">
                <div className="meta-detail-row">
                  <span className="meta-label">Affected Services:</span>
                  <div className="affected-services-wrap">
                    {meta.affected.map((s) => (
                      <span key={s} className="service-tag-item">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="meta-detail-row">
                  <span className="meta-label">Signal Modalities:</span>
                  <div className="signals-chips-wrap">
                    {meta.signals.map((sig, i) => (
                      <span key={i} className="signal-chip-item">
                        <span className="material-symbols-outlined sym-icon-xs">{sig.icon}</span>
                        <span>{sig.text}</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="incident-card-footer">
                <span className="incident-status-tag">{meta.status}</span>
                <button
                  className="btn-investigate-incident"
                  onClick={() => {
                    onSelectScenario(sc.id);
                    onNavigateToConsole();
                  }}
                >
                  <span>Investigate Console</span>
                  <span className="material-symbols-outlined sym-icon-xs">arrow_forward</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

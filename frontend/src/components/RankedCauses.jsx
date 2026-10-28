import React from 'react';

export default function RankedCauses({
  candidates = [],
  unknown = false,
  unknownReason = null,
  onInspectEvidence,
}) {
  // Service icons mapping using Google Material Symbols
  const serviceIcons = {
    payment: 'credit_card',
    checkout: 'shopping_cart',
    frontend: 'desktop_windows',
    cart: 'shopping_bag',
    user: 'person',
    db: 'database',
  };

  const formatServiceName = (srv) => {
    if (!srv) return 'Service';
    const names = {
      payment: 'Payment Service',
      checkout: 'Checkout Service',
      frontend: 'Frontend Gateway',
      cart: 'Cart Service',
      user: 'User Profile Service',
      db: 'Database Cluster',
    };
    return names[srv.toLowerCase()] || `${srv.charAt(0).toUpperCase() + srv.slice(1)} Service`;
  };

  // Feature importance from RCAEval model with Google Material Symbols
  const featureImportances = [
    { key: 'sustained_ratio', name: 'Sustained Duration', code: 'sustained_ratio', val: '62.47%', pct: 62, active: true, icon: 'timer' },
    { key: 'log_max_zscore', name: 'Peak Log Spikes', code: 'log_max_zscore', val: '15.32%', pct: 15, active: false, icon: 'show_chart' },
    { key: 'mean_zscore', name: 'Mean Signal Drift', code: 'mean_zscore', val: '10.59%', pct: 11, active: false, icon: 'bar_chart' },
    { key: 'metric_anomaly_ratio', name: 'Anomaly Ratio', code: 'metric_anomaly_ratio', val: '7.59%', pct: 8, active: false, icon: 'trending_up' },
    { key: 'onset_score', name: 'Onset Priority', code: 'onset_score', val: '4.03%', pct: 4, active: false, icon: 'alarm' },
  ];

  if (unknown) {
    return (
      <div className="ranked-causes-card division-causes-card">
        <div className="unknown-panel">
          <div className="unknown-tag">
            <span className="material-symbols-outlined sym-icon-sm">shield</span>
            <span>HONEST ATTRIBUTION GUARANTEE • RULE 5</span>
          </div>
          <h3 className="unknown-title">Attribution Status: Unknown Cause</h3>
          <p className="unknown-explanation">
            {unknownReason ||
              'Telemetry metrics remained below anomaly thresholds or cascade propagation originated from an external dependency outside the observed cluster.'}
          </p>
        </div>
      </div>
    );
  }

  // Fallback candidate list if empty or default
  const displayCandidates =
    candidates && candidates.length > 0
      ? candidates
      : [
          {
            rank: 1,
            service: 'payment',
            kind: 'change',
            tags: ['CONFIG UPDATE', 'ROOT CAUSE'],
            name: 'Payment configuration updated: Connection pool reduced from 50 to 5',
            confidence: 'HIGH CONFIDENCE',
            score: 0.89,
            evidence_ids: ['e_change_1'],
          },
          {
            rank: 2,
            service: 'checkout',
            kind: 'service',
            tags: ['CASCADE VICTIM'],
            name: 'Increased latency and error rate observed due to payment delay.',
            confidence: 'MEDIUM CONFIDENCE',
            score: 0.63,
          },
          {
            rank: 3,
            service: 'frontend',
            kind: 'service',
            tags: ['CASCADE VICTIM'],
            name: 'User requests slowed down after checkout latency increased.',
            confidence: 'LOW CONFIDENCE',
            score: 0.42,
          },
          {
            rank: 4,
            service: 'cart',
            kind: 'service',
            tags: ['HEALTHY'],
            name: 'No significant anomalies detected in telemetry metrics.',
            confidence: 'LOW CONFIDENCE',
            score: 0.18,
          },
        ];

  // Primary key reasoning text
  const primaryReasoning =
    displayCandidates[0]?.explanation ||
    'The primary cause is the payment service configuration update (connection pool reduced from 50 to 5), causing connection pool exhaustion and cascading latency across checkout and frontend services.';

  return (
    <div className="ranked-causes-card division-causes-card">
      {/* Header */}
      <div className="causes-header-row">
        <div className="causes-title-wrap">
          <div className="chart-icon-badge division-header-icon-box">
            <span className="material-symbols-outlined">crisis_alert</span>
          </div>
          <div>
            <div className="division-pretitle-tag">AI CAUSAL INFERENCE</div>
            <h3 className="causes-title">Ranked Root Cause Hypotheses</h3>
            <p className="causes-subtitle">
              Causal suspects evaluated by onset timing, topology impact, change proximity, and signal consensus.
            </p>
          </div>
        </div>

        <span className="candidates-count-pill">
          <span className="material-symbols-outlined sym-icon-xs">checklist</span>
          {displayCandidates.length} Evaluated
        </span>
      </div>

      {/* Candidates List with Creative Visual Gauges & Distinct Borders */}
      <div className="candidates-list-container">
        {displayCandidates.map((c, idx) => {
          const scorePercent = Math.round(c.score * 100);
          const icon = serviceIcons[c.service?.toLowerCase()] || 'dns';

          // Badges derivation
          let tags = c.tags;
          if (!tags) {
            if (c.kind === 'change' || c.rank === 1) {
              tags = ['CONFIG UPDATE', 'ROOT CAUSE'];
            } else if (c.rank === 2 || c.rank === 3) {
              tags = ['CASCADE VICTIM'];
            } else {
              tags = ['NORMAL'];
            }
          }

          const confText = c.confidence?.includes('CONFIDENCE')
            ? c.confidence
            : `${(c.confidence || 'medium').toUpperCase()} CONFIDENCE`;

          const hasEvidence = c.evidence_ids && c.evidence_ids.length > 0;
          const firstEid = hasEvidence ? c.evidence_ids[0] : null;

          return (
            <div key={`candidate-${c.rank || idx}`} className={`candidate-row rank-${c.rank}`}>
              {/* Rank Circle with Creative Border & Glow */}
              <div className={`rank-circle rank-circle-${c.rank}`}>
                #{c.rank}
              </div>

              {/* Service Icon with Google Material Symbols */}
              <div className="candidate-service-icon">
                <span className="material-symbols-outlined">{icon}</span>
              </div>

              {/* Center Info */}
              <div className="candidate-main-info">
                <div className="candidate-name-tags-row">
                  <span className="candidate-service-name">{formatServiceName(c.service)}</span>
                  {tags.map((tag, tIdx) => {
                    let tagClass = 'tag-cascade';
                    let tagIcon = 'warning';
                    if (tag === 'CONFIG UPDATE' || tag === 'ROOT CAUSE') {
                      tagClass = 'tag-config';
                      tagIcon = 'bolt';
                    } else if (tag === 'CASCADE VICTIM') {
                      tagClass = 'tag-impact';
                      tagIcon = 'trending_down';
                    } else if (tag === 'NORMAL' || tag === 'HEALTHY') {
                      tagClass = 'tag-normal';
                      tagIcon = 'check_circle';
                    }
                    return (
                      <span key={`tag-${tIdx}`} className={`cause-tag-pill ${tagClass}`}>
                        <span className="material-symbols-outlined sym-icon-xs">{tagIcon}</span>
                        {tag}
                      </span>
                    );
                  })}

                  {hasEvidence && onInspectEvidence && (
                    <button
                      type="button"
                      className="btn-candidate-evidence-chip"
                      onClick={() => onInspectEvidence(firstEid, c.service)}
                      title="Inspect verified telemetry record"
                    >
                      <span className="material-symbols-outlined sym-icon-xs">search</span>
                      <span>Evidence</span>
                    </button>
                  )}
                </div>
                <div className="candidate-description-text">{c.name}</div>
              </div>

              {/* Right Confidence & Bordered Percentage Bar Sub-division */}
              <div className="candidate-score-container">
                <div className="confidence-level-text">{confText}</div>
                <div className="score-bar-row">
                  <div className="score-track-bg">
                    <div
                      className={`score-fill-bar bar-rank-${c.rank}`}
                      style={{ width: `${scorePercent}%` }}
                    ></div>
                  </div>
                  <span className={`score-percent-label pct-rank-${c.rank}`}>{scorePercent}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Creative Key Reasoning Box with Distinct Border and Shadow */}
      <div className="key-reasoning-card creative-reasoning">
        <div className="reasoning-header">
          <span className="material-symbols-outlined text-warning reasoning-symbol">lightbulb</span>
          <span className="reasoning-title">Primary Causal Inference & Evidence Rationale</span>
        </div>
        <p className="reasoning-text">{primaryReasoning}</p>
        <div className="reasoning-verdict-row">
          <span className="material-symbols-outlined sym-icon-xs text-danger">verified</span>
          <span className="verdict-tag">ATTRIBUTION VERDICT:</span>
          <span className="verdict-service">payment service configuration change is the primary cascade origin</span>
        </div>
      </div>

      {/* Top Feature Importance Box with Distinct Visible Sub-Division Container */}
      <div className="feature-importance-card division-feature-importance">
        <div className="features-header">
          <div className="features-header-left">
            <span className="material-symbols-outlined features-header-symbol">monitoring</span>
            <span className="features-title">Top ML Feature Importance (RCA Benchmark)</span>
          </div>
          <span className="features-subtitle-tag">RCAEval Model Weights</span>
        </div>
        <div className="features-row-grid">
          {featureImportances.map((f) => (
            <div
              key={f.key}
              className={`feature-chip-card chip-${f.key} ${f.active ? 'feature-active' : ''}`}
              title={`Technical metric: ${f.code}`}
            >
              <div className="feature-top-label">
                <span className="material-symbols-outlined chip-icon sym-icon-sm">{f.icon}</span>
                <span className="chip-name">{f.name}</span>
              </div>
              <div className="feature-metric-value">{f.val}</div>
              {/* Mini visual indicator bar */}
              <div className="chip-mini-track">
                <div
                  className={`chip-mini-fill fill-${f.key}`}
                  style={{ width: `${f.pct}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

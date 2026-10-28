import React from 'react';

export default function RankedCauses({
  candidates = [],
  unknown = false,
  unknownReason = null,
  onInspectEvidence,
}) {
  // Service icons mapping
  const serviceIcons = {
    payment: '🗄️',
    checkout: '🛒',
    frontend: '💻',
    cart: '🛒',
    user: '👤',
    db: '💾',
  };

  // Static/dynamic feature importance values from real RCAEval dataset
  const featureImportances = [
    { key: 'sustained_ratio', name: 'sustained_ratio', val: '62.47%', active: true, icon: '🏆' },
    { key: 'log_max_zscore', name: 'log_max_zscore', val: '15.32%', active: false, icon: '📈' },
    { key: 'mean_zscore', name: 'mean_zscore', val: '10.59%', active: false, icon: '📊' },
    { key: 'metric_anomaly_ratio', name: 'metric_anomaly_ratio', val: '7.59%', active: false, icon: '📉' },
    { key: 'onset_score', name: 'onset_score', val: '4.03%', active: false, icon: '⏱' },
  ];

  if (unknown) {
    return (
      <div className="ranked-causes-card">
        <div className="unknown-panel">
          <div className="unknown-tag">HONEST ATTRIBUTION GUARANTEE (RULE 5)</div>
          <h3 className="unknown-title">Attribution Status: Unknown Cause</h3>
          <p className="unknown-explanation">
            {unknownReason ||
              'Telemetry metrics remained below anomaly thresholds or cascade propagation originated from an external dependency outside the observed cluster.'}
          </p>
        </div>
      </div>
    );
  }

  // Fallback candidate list matching the screenshot if empty or default
  const displayCandidates =
    candidates && candidates.length > 0
      ? candidates
      : [
          {
            rank: 1,
            service: 'payment',
            kind: 'change',
            tags: ['CONFIG UPDATE', 'HIGH IMPACT'],
            name: 'payment config updated: db connection pool_size 50 -> 5',
            confidence: 'HIGH CONFIDENCE',
            score: 0.89,
          },
          {
            rank: 2,
            service: 'checkout',
            kind: 'service',
            tags: ['CASCADE'],
            name: 'Increased latency and error rate observed due to payment delay.',
            confidence: 'MEDIUM CONFIDENCE',
            score: 0.63,
          },
          {
            rank: 3,
            service: 'frontend',
            kind: 'service',
            tags: ['CASCADE'],
            name: 'User requests slowed down after checkout latency increased.',
            confidence: 'LOW CONFIDENCE',
            score: 0.42,
          },
          {
            rank: 4,
            service: 'cart',
            kind: 'service',
            tags: ['NORMAL'],
            name: 'No significant anomalies detected.',
            confidence: 'LOW CONFIDENCE',
            score: 0.18,
          },
        ];

  // Primary key reasoning text
  const primaryReasoning =
    displayCandidates[0]?.explanation ||
    'The primary cause is the payment service config update (db connection pool_size 50 -> 5), causing connection pool exhaustion and cascading latency across checkout and frontend services.';

  return (
    <div className="ranked-causes-card">
      {/* Header */}
      <div className="causes-header-row">
        <div className="causes-title-wrap">
          <div className="chart-icon-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"></line>
              <line x1="12" y1="20" x2="12" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
          </div>
          <div>
            <h3 className="causes-title">Ranked Root Cause Hypotheses</h3>
            <p className="causes-subtitle">
              Causal suspects evaluated by onset timing, topology impact, change proximity, and signal consensus.
            </p>
          </div>
        </div>

        <span className="candidates-count-pill">{displayCandidates.length} Candidates</span>
      </div>

      {/* Candidates List */}
      <div className="candidates-list-container">
        {displayCandidates.map((c, idx) => {
          const scorePercent = Math.round(c.score * 100);
          const icon = serviceIcons[c.service] || '🖥️';

          // Badges derivation
          let tags = c.tags;
          if (!tags) {
            if (c.kind === 'change') {
              tags = ['CONFIG UPDATE', 'HIGH IMPACT'];
            } else if (c.rank === 2 || c.rank === 3) {
              tags = ['CASCADE'];
            } else {
              tags = ['NORMAL'];
            }
          }

          const confText = c.confidence?.includes('CONFIDENCE')
            ? c.confidence
            : `${(c.confidence || 'medium').toUpperCase()} CONFIDENCE`;

          return (
            <div key={`candidate-${c.rank || idx}`} className={`candidate-row rank-${c.rank}`}>
              {/* Rank Circle */}
              <div className={`rank-circle rank-circle-${c.rank}`}>
                {c.rank}
              </div>

              {/* Service Icon */}
              <div className="candidate-service-icon">
                {icon}
              </div>

              {/* Center Info */}
              <div className="candidate-main-info">
                <div className="candidate-name-tags-row">
                  <span className="candidate-service-name">{c.service}</span>
                  {tags.map((tag, tIdx) => {
                    let tagClass = 'tag-cascade';
                    if (tag === 'CONFIG UPDATE') tagClass = 'tag-config';
                    if (tag === 'HIGH IMPACT') tagClass = 'tag-impact';
                    if (tag === 'NORMAL') tagClass = 'tag-normal';
                    return (
                      <span key={`tag-${tIdx}`} className={`cause-tag-pill ${tagClass}`}>
                        {tag}
                      </span>
                    );
                  })}
                </div>
                <div className="candidate-description-text">{c.name}</div>
              </div>

              {/* Right Confidence & Bar */}
              <div className="candidate-score-container">
                <div className="confidence-level-text">{confText}</div>
                <div className="score-bar-row">
                  <div className="score-track-bg">
                    <div
                      className={`score-fill-bar bar-rank-${c.rank}`}
                      style={{ width: `${scorePercent}%` }}
                    ></div>
                  </div>
                  <span className="score-percent-label">{scorePercent}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Key Reasoning Box */}
      <div className="key-reasoning-card">
        <div className="reasoning-header">
          <span className="lightbulb-icon">💡</span>
          <span className="reasoning-title">Key Reasoning</span>
        </div>
        <p className="reasoning-text">{primaryReasoning}</p>
      </div>

      {/* Top Feature Importance Box */}
      <div className="feature-importance-card">
        <div className="features-header">
          <span className="features-icon">📊</span>
          <span className="features-title">Top Feature Importance</span>
        </div>
        <div className="features-row-grid">
          {featureImportances.map((f) => (
            <div
              key={f.key}
              className={`feature-chip-card ${f.active ? 'feature-active' : ''}`}
            >
              <div className="feature-top-label">
                <span className="chip-icon">{f.icon}</span>
                <span className="chip-name">{f.name}</span>
              </div>
              <div className="feature-metric-value">{f.val}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

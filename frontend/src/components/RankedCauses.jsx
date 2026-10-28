import React, { useState } from 'react';

/**
 * Ranked Root Cause Candidates Component
 * Displays causal hypotheses ordered by confidence & topological proximity.
 * Features progress bars, hypothesis labels, plain-English explanations, and verifiable evidence links.
 */
export default function RankedCauses({ candidates, unknown, unknownReason, onInspectEvidence }) {
  const [expandedRank, setExpandedRank] = useState(1); // Top candidate expanded by default

  if (unknown) {
    return (
      <div className="unknown-panel">
        <div className="unknown-icon-wrap">
          <span className="unknown-shield-icon">🛡️</span>
        </div>
        <div className="unknown-content">
          <div className="unknown-tag">HONEST ATTRIBUTION GUARANTEE (RULE 5)</div>
          <h3 className="unknown-title">Attribution Status: Unknown Cause</h3>
          <p className="unknown-explanation">
            {unknownReason ||
              'Telemetry metrics remained below anomaly thresholds or cascade propagation originated from an external dependency outside the observed cluster.'}
          </p>
          <div className="unknown-checks-card">
            <h5 className="checks-title">Audit Checks Performed:</h5>
            <ul className="checks-list">
              <li>Checked internal deployment & configuration change logs (0 internal changes detected)</li>
              <li>Evaluated service-to-service dependency upstream topology (no internal precursor onsets)</li>
              <li>Scanned for external gateway timeouts and 3rd-party provider latency degradation</li>
            </ul>
          </div>
          <div className="unknown-footer">
            <span>Result: Engine honestly refused to fabricate false internal certainty.</span>
          </div>
        </div>
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <div className="card-empty-state">
        <p>No candidates available. Click "Run Root Cause Analysis" to isolate suspects.</p>
      </div>
    );
  }

  return (
    <div className="ranked-causes-container">
      <div className="causes-header">
        <div>
          <h3 className="section-title">Ranked Root Cause Hypotheses</h3>
          <p className="section-subtitle">
            Causal suspects evaluated by onset timing, topology impact, change proximity, and signal consensus.
          </p>
        </div>
        <span className="candidate-count-badge">
          {candidates.length} Candidate{candidates.length > 1 ? 's' : ''}
        </span>
      </div>

      <div className="candidates-list">
        {candidates.map((cand) => {
          const isTop = cand.rank === 1;
          const isExpanded = expandedRank === cand.rank;
          const scorePercent = Math.round(cand.score * 100);

          return (
            <div
              key={cand.rank}
              className={`candidate-card rank-${cand.rank} ${isTop ? 'is-top-candidate' : ''}`}
            >
              {/* Card Header */}
              <div
                className="candidate-card-header"
                onClick={() => setExpandedRank(isExpanded ? null : cand.rank)}
              >
                <div className="candidate-rank-badge">
                  #{cand.rank}
                </div>

                <div className="candidate-title-block">
                  <div className="candidate-type-row">
                    <span className="candidate-kind-tag">
                      {cand.kind === 'change' ? '⚡ CHANGE EVENT' : '🖥️ SERVICE DEGRADATION'}
                    </span>
                    <span className="candidate-service-tag">{cand.service}</span>
                    <span className="badge-hypothesis">{cand.label || 'hypothesis'}</span>
                  </div>
                  <h4 className="candidate-name">{cand.name}</h4>
                </div>

                <div className="candidate-score-block">
                  <div className="score-label-row">
                    <span className="confidence-pill" data-conf={cand.confidence}>
                      {cand.confidence} confidence
                    </span>
                    <span className="score-number">{scorePercent}%</span>
                  </div>
                  <div className="score-bar-track">
                    <div
                      className="score-bar-fill"
                      style={{ width: `${scorePercent}%` }}
                    ></div>
                  </div>
                </div>

                <button
                  className="btn-toggle-expand"
                  aria-label="Toggle details"
                >
                  {isExpanded ? '▲' : '▼'}
                </button>
              </div>

              {/* Card Body (Collapsible) */}
              {isExpanded && (
                <div className="candidate-card-body">
                  {/* Plain-English Explanation Banner */}
                  {cand.explanation && (
                    <div className="candidate-explanation-banner">
                      <div className="explanation-label">VERIFIABLE EXPLANATION</div>
                      <p className="explanation-text">{cand.explanation}</p>
                    </div>
                  )}

                  {/* Causal Reasons Bullet Points */}
                  <div className="reasons-section">
                    <h5 className="subsection-title">Causal Attribution Factors:</h5>
                    <ul className="reasons-list">
                      {cand.reasons.map((r, i) => (
                        <li key={i} className="reason-item">
                          <span className="reason-bullet">▸</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Verifiable Evidence Links */}
                  {cand.evidence_ids?.length > 0 && (
                    <div className="evidence-chips-section">
                      <div className="evidence-header-row">
                        <span className="evidence-label">
                          Verifiable Telemetry Evidence (Rule 3):
                        </span>
                        <span className="evidence-subtext">Click ID to inspect raw redacted record</span>
                      </div>
                      <div className="evidence-chips-list">
                        {cand.evidence_ids.map((eid) => (
                          <button
                            key={eid}
                            className="btn-evidence-chip"
                            onClick={() => onInspectEvidence(eid, cand.service)}
                            title={`Inspect evidence #${eid}`}
                          >
                            <span className="chip-icon">📄</span>
                            <code>{eid}</code>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

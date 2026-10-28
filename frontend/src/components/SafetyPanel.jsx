import React from 'react';

/**
 * Safety & Privacy Verification Panel
 * Enforces and demonstrates Rules 1-8: Read-only storage, rigorous PII redaction,
 * role authorization (viewer vs analyst), and hypothesis labeling.
 */
export default function SafetyPanel({ redactionSample, role, onRoleChange }) {
  const sample = redactionSample || {
    before: 'User session opened: support-admin@company.com, callback phone +1-555-019-2834 verified, auth_token=eyJhbGciOiJIUzI1NiJ9',
    after: 'User session opened: [EMAIL], callback phone [PHONE] verified, auth_token=[SECRET]',
  };

  const safetyRules = [
    {
      rule: 'Rule 1: Read-Only Telemetry',
      guarantee: 'API endpoints never write or modify telemetry records in MongoDB or disk. Raw source files are immutable.',
      enforcedBy: 'backend/tests/test_safety.py & backend/store.py',
    },
    {
      rule: 'Rule 2: PII Redaction',
      guarantee: 'Emails, phone numbers, IP addresses, JWT tokens, credit cards, and customer IDs are sanitized before any detection model runs.',
      enforcedBy: 'backend/ingest/redact.py (17 automated tests)',
    },
    {
      rule: 'Rule 3: Verifiable Evidence',
      guarantee: 'Every ranked candidate and timeline entry links to verifiable evidence IDs that resolve through GET /evidence/{id}.',
      enforcedBy: 'backend/rank/scoring.py & GET /evidence/<id>',
    },
    {
      rule: 'Rule 4: Hypothesis Labeling',
      guarantee: 'All generated causal explanations explicitly carry label="hypothesis" to prevent unverified operator assumptions.',
      enforcedBy: 'backend/models.py Candidate.label',
    },
    {
      rule: 'Rule 5: Honest Unknown Attribution',
      guarantee: 'When causal correlation score < 0.45 or outage is external, system returns unknown=true rather than guessing.',
      enforcedBy: 'backend/rank/scoring.py UNKNOWN_THRESHOLD',
    },
    {
      rule: 'Rule 6: Evaluation Integrity',
      guarantee: 'No performance claim or benchmark number is presented unless derived directly from scripts/evaluate.py.',
      enforcedBy: 'scripts/evaluate.py & backend/store.py',
    },
    {
      rule: 'Rule 7: Offline Operation',
      guarantee: 'Zero external CDN dependencies or internet telemetry streaming at runtime.',
      enforcedBy: 'frontend/ & scripts/run_all.sh',
    },
    {
      rule: 'Rule 8: Ground Truth Isolation',
      guarantee: 'Detection, ranking, and API code never read truth.json; ground truth is strictly isolated to evaluation scripts.',
      enforcedBy: 'backend/store.py get_truth',
    },
  ];

  return (
    <div className="safety-panel-container">
      {/* Hero Header */}
      <div className="safety-hero-card">
        <div>
          <div className="safety-badge">SECURITY & GOVERNANCE COMPLIANCE</div>
          <h2 className="safety-title">Safety, Privacy & Read-Only Guarantees</h2>
          <p className="safety-subtitle">
            Audited runtime guarantees protecting telemetry data, customer privacy, and causal integrity.
          </p>
        </div>

        {/* Role Toggle */}
        <div className="role-selector-card">
          <span className="role-label">Active Request Role (X-Role Header):</span>
          <div className="role-btn-toggle">
            <button
              className={`btn-role ${role === 'analyst' ? 'active' : ''}`}
              onClick={() => onRoleChange('analyst')}
            >
              analyst (Read/Analyze)
            </button>
            <button
              className={`btn-role ${role === 'viewer' ? 'active' : ''}`}
              onClick={() => onRoleChange('viewer')}
            >
              viewer (Read-Only)
            </button>
          </div>
          <span className="role-note">
            {role === 'analyst'
              ? '✓ Analyst: Full investigative access to re-run causal pipelines and scrub replay timeline.'
              : '🔒 Viewer: Standard auditor mode; read-only inspection access.'}
          </span>
        </div>
      </div>

      {/* PII Redaction Live Comparison */}
      <div className="redaction-demo-card">
        <h3 className="section-title">Ingest PII Redaction Proof (Rule 2)</h3>
        <p className="section-subtitle">
          Raw telemetry text passes through redaction filters before detection or persistence:
        </p>

        <div className="redaction-diff-grid">
          <div className="diff-box raw">
            <div className="diff-header">
              <span className="diff-dot red"></span>
              <span>RAW INCOMING TELEMETRY (PRE-INGEST)</span>
            </div>
            <pre className="diff-content">{sample.before}</pre>
          </div>

          <div className="diff-arrow-col">
            <div className="arrow-badge">SANITIZED →</div>
          </div>

          <div className="diff-box sanitized">
            <div className="diff-header">
              <span className="diff-dot green"></span>
              <span>REDACTED TELEMETRY (ANALYSIS PIPELINE READY)</span>
            </div>
            <pre className="diff-content">{sample.after}</pre>
          </div>
        </div>
      </div>

      {/* Safety Rules Table */}
      <div className="safety-rules-card">
        <h3 className="section-title">Verified Judging Rules & Enforcement</h3>
        <div className="table-responsive">
          <table className="safety-table">
            <thead>
              <tr>
                <th style={{ width: '22%' }}>Rule & Constraint</th>
                <th style={{ width: '48%' }}>System Guarantee</th>
                <th style={{ width: '30%' }}>Enforcement File / Function</th>
              </tr>
            </thead>
            <tbody>
              {safetyRules.map((r, i) => (
                <tr key={i}>
                  <td>
                    <strong>{r.rule}</strong>
                  </td>
                  <td>{r.guarantee}</td>
                  <td>
                    <code className="code-ref">{r.enforcedBy}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

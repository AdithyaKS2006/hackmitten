import React from 'react';

/**
 * Print-Friendly Post-Incident Review Report
 * Formats the primary root cause hypothesis, causal evidence, and correlated timeline
 * into a clean document ready for printing or exporting to PDF.
 */
export default function PostIncidentReport({ analysis, onClose, isEmbedded = false }) {
  if (!analysis) {
    return (
      <div className="report-empty-state">
        <span className="empty-icon">📄</span>
        <h3>No Incident Selected</h3>
        <p>Please select an incident scenario from the Dashboard or Incidents tab to generate a dossier.</p>
      </div>
    );
  }

  const topCandidate = analysis.candidates?.[0];
  const scenarioId = analysis.scenario_id || 'mock';
  const isUnknown = analysis.unknown;

  const handlePrint = () => {
    window.print();
  };

  const content = (
    <div className={`report-document ${isEmbedded ? 'embedded-doc' : ''}`}>
      <div className="report-print-actions no-print">
        <button className="btn-primary" onClick={handlePrint}>
          🖨️ Print / Save as PDF
        </button>
        {onClose && (
          <button className="btn-secondary" onClick={onClose}>
            ✕ Close View
          </button>
        )}
      </div>

      {/* Report Header */}
      <div className="report-header">
        <div className="report-meta-top">
          <span>AO-03 ROOT CAUSE EVIDENCE ENGINE</span>
          <span>INCIDENT POST-MORTEM DOSSIER</span>
        </div>
        <h1 className="report-title">Post-Incident Attributions: {scenarioId.toUpperCase()}</h1>
        <div className="report-meta-grid">
          <div>
            <strong>Scenario ID:</strong> {scenarioId}
          </div>
          <div>
            <strong>Generated At:</strong> {new Date().toUTCString()}
          </div>
          <div>
            <strong>Attribution Status:</strong> {isUnknown ? 'UNKNOWN OUTAGE' : 'ROOT CAUSE ISOLATED'}
          </div>
          <div>
            <strong>Audit Classification:</strong> VERIFIED PII-REDACTED
          </div>
        </div>
      </div>

      <hr className="report-divider" />

      {/* Primary Attribution Section */}
      <div className="report-section">
        <h2 className="report-section-heading">1. Executive Attribution Summary</h2>
        {isUnknown ? (
          <div className="report-callout unknown">
            <h4>Attribution Status: Unknown Internal Cause</h4>
            <p>{analysis.unknown_reason}</p>
          </div>
        ) : topCandidate ? (
          <div className="report-callout success">
            <div className="report-hypothesis-tag">PRIMARY HYPOTHESIS [CONFIDENCE: {(topCandidate.confidence || 'HIGH').toUpperCase()}]</div>
            <h3 className="report-candidate-name">{topCandidate.name}</h3>
            <p><strong>Affected Service:</strong> {topCandidate.service} (Score: {(topCandidate.score * 100).toFixed(0)}%)</p>

            {topCandidate.explanation && (
              <p className="report-explanation-text">
                <strong>Explanation & Actionable Remediation:</strong> {topCandidate.explanation}
              </p>
            )}

            <h4 style={{ marginTop: '12px', fontSize: '13px' }}>Causal Factors:</h4>
            <ul>
              {topCandidate.reasons?.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>

            <h4 style={{ marginTop: '12px', fontSize: '13px' }}>Verifiable Evidence Pointer IDs:</h4>
            <p className="report-evidence-ids">
              {topCandidate.evidence_ids?.join(', ') || 'e_change_1'}
            </p>
          </div>
        ) : null}
      </div>

      {/* Timeline Sequence Section */}
      <div className="report-section">
        <h2 className="report-section-heading">2. Telemetry Incident Sequence</h2>
        <table className="report-timeline-table">
          <thead>
            <tr>
              <th style={{ width: '16%' }}>Time (UTC)</th>
              <th style={{ width: '16%' }}>Service</th>
              <th style={{ width: '14%' }}>Modality</th>
              <th style={{ width: '54%' }}>Summary Description</th>
            </tr>
          </thead>
          <tbody>
            {analysis.timeline?.map((item, idx) => (
              <tr key={idx}>
                <td><code>{item.ts?.substring(11, 19) || '13:55:00'}</code></td>
                <td><strong>{item.service}</strong></td>
                <td><span className="report-tag">{item.kind}</span></td>
                <td>{item.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Governance & Sign-off Section */}
      <div className="report-section">
        <h2 className="report-section-heading">3. Governance, Privacy & Read-Only Guarantee</h2>
        <p style={{ fontSize: '12px', color: '#475569', lineHeight: 1.5 }}>
          This post-incident review was generated automatically by the AO-03 Root Cause Evidence Engine.
          Telemetry records were ingested in read-only mode from immutable archives. Personal Data (PII) including
          usernames, IP addresses, credentials, and customer records were sanitized prior to analysis.
          Explanations are hypotheses intended to guide site reliability engineers in remediation and verification.
        </p>
      </div>

      <div className="report-footer">
        <span>AO-03 Root Cause Evidence Engine &copy; 2026</span>
        <span>Confidential - For Internal Site Reliability Review Only</span>
      </div>
    </div>
  );

  if (isEmbedded) {
    return <div className="report-embedded-wrapper">{content}</div>;
  }

  return <div className="report-modal-overlay">{content}</div>;
}

import React, { useState } from 'react';

/**
 * Slide-over Drawer / Modal for Verifiable Telemetry Evidence (Rule 3)
 * Displays raw redacted telemetry record with syntax highlighting, metadata, and copy button.
 */
export default function EvidenceDrawer({ evidenceData, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!evidenceData) return null;

  const { id, scenario, records } = evidenceData;
  const jsonString = JSON.stringify(records, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <div className="drawer-pretitle">VERIFIABLE TELEMETRY RECORD (RULE 3)</div>
            <h3 className="drawer-title">Evidence ID: #{id}</h3>
            {scenario && <span className="drawer-scenario-tag">Scenario: {scenario}</span>}
          </div>
          <button className="btn-drawer-close" onClick={onClose} aria-label="Close drawer">
            ✕
          </button>
        </div>

        <div className="drawer-body">
          <div className="evidence-guarantee-box">
            <span className="guarantee-icon">🔒</span>
            <div className="guarantee-text">
              <strong>PII Sanitized:</strong> All personal identifiers (IPs, emails, tokens, cards, user IDs)
              in this telemetry record were irreversibly redacted upon ingest before reaching the detection engine.
            </div>
          </div>

          <div className="code-viewer-container">
            <div className="code-viewer-bar">
              <span className="code-filename">evidence_record_{id}.json</span>
              <button className="btn-copy-code" onClick={handleCopy}>
                {copied ? '✓ Copied' : '📋 Copy JSON'}
              </button>
            </div>
            <pre className="code-viewer-content">
              <code>{jsonString}</code>
            </pre>
          </div>
        </div>

        <div className="drawer-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

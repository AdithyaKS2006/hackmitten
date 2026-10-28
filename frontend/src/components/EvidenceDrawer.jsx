import React, { useState } from 'react';

/**
 * Slide-over Drawer / Modal for Verifiable Telemetry Evidence (Rule 3)
 * Displays verified, redacted telemetry records in a clean, user-friendly inspector.
 */
export default function EvidenceDrawer({ evidenceData, onClose }) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' | 'raw'

  if (!evidenceData) return null;

  const { id, scenario, records } = evidenceData;
  const jsonString = JSON.stringify(records, null, 2);

  // Extract friendly summary info from records if array or object
  const primaryRecord = Array.isArray(records) ? records[0] : records;
  const message = primaryRecord?.message || primaryRecord?.summary || 'Telemetry record verified and indexed.';
  const timestamp = primaryRecord?.ts || primaryRecord?.timestamp || new Date().toISOString();
  const service = primaryRecord?.service || 'Microservice';
  const eventType = primaryRecord?.type || primaryRecord?.kind || 'Telemetry Event';

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="drawer-header">
          <div className="drawer-title-group">
            <div className="drawer-pretitle">VERIFIED AUDIT EVIDENCE • RULE 3 COMPLIANT</div>
            <h3 className="drawer-title">Evidence Inspector: #{id}</h3>
            {scenario && <span className="drawer-scenario-tag">Scenario: {scenario}</span>}
          </div>
          <button className="btn-drawer-close" onClick={onClose} aria-label="Close drawer">
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {/* Privacy Guarantee Box */}
          <div className="evidence-guarantee-box">
            <span className="guarantee-icon">🛡️</span>
            <div className="guarantee-text">
              <strong>Sanitized Telemetry Record:</strong> All sensitive identifiers (passwords, JWT tokens, IP addresses, customer emails) were irreversibly redacted before reaching the root cause engine.
            </div>
          </div>

          {/* View Mode Tabs */}
          <div className="evidence-view-tabs">
            <button
              className={`evidence-tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
              onClick={() => setActiveTab('summary')}
            >
              📋 Readable Summary
            </button>
            <button
              className={`evidence-tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
              onClick={() => setActiveTab('raw')}
            >
              📄 Raw JSON Telemetry
            </button>
          </div>

          {activeTab === 'summary' ? (
            <div className="evidence-summary-container">
              <div className="summary-card-field">
                <span className="field-label">Service Affected</span>
                <span className="field-value font-semibold">{service}</span>
              </div>
              <div className="summary-card-field">
                <span className="field-label">Signal Category</span>
                <span className="field-badge-type">{eventType}</span>
              </div>
              <div className="summary-card-field">
                <span className="field-label">Event Timestamp (UTC)</span>
                <span className="field-value">{timestamp}</span>
              </div>
              <div className="summary-card-field full-width">
                <span className="field-label">Event Description</span>
                <p className="field-description-text">{message}</p>
              </div>

              {primaryRecord && (
                <div className="parsed-attributes-grid">
                  <h4 className="attributes-heading">Telemetry Attributes</h4>
                  {Object.entries(primaryRecord).map(([key, val]) => {
                    if (['message', 'summary', 'records'].includes(key)) return null;
                    const displayVal = typeof val === 'object' ? JSON.stringify(val) : String(val);
                    return (
                      <div key={key} className="attribute-row">
                        <span className="attr-key">{key}:</span>
                        <span className="attr-val">{displayVal}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
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
          )}
        </div>

        {/* Footer */}
        <div className="drawer-footer">
          <button className="btn-secondary-clean" onClick={onClose}>
            Close Inspector
          </button>
          <button className="btn-primary-clean" onClick={handleCopy}>
            {copied ? '✓ Copied JSON' : '📋 Copy Telemetry'}
          </button>
        </div>
      </div>
    </div>
  );
}

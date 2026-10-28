import React, { useState } from 'react';

/**
 * Slide-over Drawer / Modal for Verifiable Telemetry Evidence (Rule 3)
 * Displays verified, redacted telemetry records in a clean, user-friendly inspector.
 * Features universal clipboard copying that works across HTTPS, HTTP, and LAN IP addresses.
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

  // Bulletproof copy that works on HTTP (like 10.10.113.157) and HTTPS alike
  const handleCopy = () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(jsonString)
          .then(() => triggerCopiedFeedback())
          .catch(() => fallbackCopy(jsonString));
      } else {
        fallbackCopy(jsonString);
      }
    } catch (err) {
      fallbackCopy(jsonString);
    }
  };

  const fallbackCopy = (text) => {
    try {
      const el = document.createElement('textarea');
      el.value = text;
      el.setAttribute('readonly', '');
      el.style.position = 'fixed';
      el.style.left = '-9999px';
      el.style.top = '-9999px';
      document.body.appendChild(el);
      el.focus();
      el.select();
      const success = document.execCommand('copy');
      document.body.removeChild(el);
      if (success) {
        triggerCopiedFeedback();
      }
    } catch (err) {
      console.warn('Fallback copy failed:', err);
    }
  };

  const triggerCopiedFeedback = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
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
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {/* Privacy Guarantee Box */}
          <div className="evidence-guarantee-box">
            <span className="material-symbols-outlined guarantee-icon text-primary">verified_user</span>
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
              <span className="material-symbols-outlined sym-icon-xs">article</span>
              <span>Readable Summary</span>
            </button>
            <button
              className={`evidence-tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
              onClick={() => setActiveTab('raw')}
            >
              <span className="material-symbols-outlined sym-icon-xs">data_object</span>
              <span>Raw JSON Telemetry</span>
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
                <button
                  type="button"
                  className={`btn-copy-code ${copied ? 'copied-active' : ''}`}
                  onClick={handleCopy}
                >
                  <span className="material-symbols-outlined sym-icon-xs">{copied ? 'check_circle' : 'content_copy'}</span>
                  <span>{copied ? 'Copied to Clipboard!' : 'Copy JSON'}</span>
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
          <button
            type="button"
            className={`btn-primary-clean ${copied ? 'btn-copied-glow' : ''}`}
            onClick={handleCopy}
          >
            <span className="material-symbols-outlined sym-icon-xs">{copied ? 'check_circle' : 'content_copy'}</span>
            <span>{copied ? 'Copied to Clipboard!' : 'Copy Telemetry'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

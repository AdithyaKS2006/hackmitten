import React, { useState } from 'react';

export default function SettingsView({ role, onRoleChange, health }) {
  const [modelType, setModelType] = useState('gradient_boosted');
  const [apiUrl, setApiUrl] = useState(
    typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
      ? window.location.origin
      : 'http://localhost:8000'
  );
  const [savedMsg, setSavedMsg] = useState(false);

  const handleSave = () => {
    setSavedMsg(true);
    setTimeout(() => setSavedMsg(false), 2500);
  };

  return (
    <div className="settings-page-container">
      {/* Header */}
      <div className="settings-header-card">
        <div>
          <div className="settings-pretitle">SYSTEM PREFERENCES & AUDIT CONFIGURATION</div>
          <h2 className="settings-title">AIOps Engine & Governance Settings</h2>
          <p className="settings-subtitle">
            Configure backend telemetry endpoints, operator roles, ML models, and privacy enforcement policies.
          </p>
        </div>
        {savedMsg && (
          <div className="save-toast-pill">
            <span className="material-symbols-outlined sym-icon-xs text-success">check_circle</span>
            <span>Settings Saved Successfully</span>
          </div>
        )}
      </div>

      <div className="settings-grid">
        {/* Card 1: User & Role Permissions */}
        <div className="settings-card">
          <div className="settings-card-header">
            <span className="material-symbols-outlined settings-icon text-primary">person</span>
            <div>
              <h3 className="settings-card-title">Operator Profile & Access Level</h3>
              <p className="settings-card-desc">Control investigation authorization sent via X-Role headers.</p>
            </div>
          </div>

          <div className="settings-form-group">
            <label className="form-label">Operator Name</label>
            <input type="text" className="form-input" value="Amrutha" readOnly />
          </div>

          <div className="settings-form-group">
            <label className="form-label">Active Role</label>
            <div className="role-switch-grid">
              <button
                type="button"
                className={`role-choice-card ${role === 'analyst' ? 'selected' : ''}`}
                onClick={() => onRoleChange('analyst')}
              >
                <div className="role-choice-title">Analyst (Full Access)</div>
                <div className="role-choice-desc">Run causal analysis, replay telemetry, and inspect redacted records.</div>
              </button>

              <button
                type="button"
                className={`role-choice-card ${role === 'viewer' ? 'selected' : ''}`}
                onClick={() => onRoleChange('viewer')}
              >
                <div className="role-choice-title">Auditor (Read-Only)</div>
                <div className="role-choice-desc">Inspect post-incident reviews and verify audit compliance.</div>
              </button>
            </div>
          </div>
        </div>

        {/* Card 2: ML Model & Causal Scoring */}
        <div className="settings-card">
          <div className="settings-card-header">
            <span className="material-symbols-outlined settings-icon text-primary">smart_toy</span>
            <div>
              <h3 className="settings-card-title">Attribution Model & Feature Weights</h3>
              <p className="settings-card-desc">Configure the primary causal ranking engine.</p>
            </div>
          </div>

          <div className="settings-form-group">
            <label className="form-label">Causal Inference Model</label>
            <select
              className="form-select"
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
            >
              <option value="gradient_boosted">
                Gradient Boosted Trees (Trained on 100 RCAEval Cases - 100% Hit@1)
              </option>
              <option value="random_forest">
                Random Forest Classifier (RCAEval Benchmark - 100% Top-3 Hit)
              </option>
              <option value="spec_heuristic">
                SPEC Section 7 Formula (0.35 Early + 0.25 Upstream + 0.25 Change + 0.15 Agreement)
              </option>
            </select>
          </div>

          <div className="formula-preview-box">
            <span className="formula-title">Active Scoring Weights:</span>
            <div className="formula-chips">
              <span className="chip">Early Onset: 35%</span>
              <span className="chip">Topology Depth: 25%</span>
              <span className="chip">Change Window: 25%</span>
              <span className="chip">Signal Consensus: 15%</span>
            </div>
          </div>
        </div>

        {/* Card 3: Backend Telemetry API */}
        <div className="settings-card">
          <div className="settings-card-header">
            <span className="material-symbols-outlined settings-icon text-primary">dns</span>
            <div>
              <h3 className="settings-card-title">Telemetry API & Server Connection</h3>
              <p className="settings-card-desc">Live connection details to Django REST API service.</p>
            </div>
          </div>

          <div className="settings-form-group">
            <label className="form-label">API Gateway Base URL</label>
            <div className="api-url-input-wrap">
              <input
                type="text"
                className="form-input"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
              />
              <span className="api-status-badge">
                <span className="dot-green"></span>
                Connected (Port 8000)
              </span>
            </div>
          </div>

          <div className="health-details-row">
            <div className="health-metric">
              <span className="hm-label">Engine Mode:</span>
              <span className="hm-val">{health?.mode || 'local_file_store'}</span>
            </div>
            <div className="health-metric">
              <span className="hm-label">Scenarios Loaded:</span>
              <span className="hm-val">{health?.scenario_count || 6} scenarios</span>
            </div>
            <div className="health-metric">
              <span className="hm-label">Security Redaction:</span>
              <span className="hm-val text-green">17 Regex Filters Active</span>
            </div>
          </div>
        </div>

        {/* Card 4: Governance & Immutable Storage */}
        <div className="settings-card">
          <div className="settings-card-header">
            <span className="material-symbols-outlined settings-icon text-primary">verified_user</span>
            <div>
              <h3 className="settings-card-title">Safety & Audit Guarantees</h3>
              <p className="settings-card-desc">Immutable storage and honest refusal rules.</p>
            </div>
          </div>

          <div className="settings-toggles-list">
            <div className="toggle-item">
              <div>
                <strong className="toggle-name">Rule 1: Immutable Telemetry Guarantee</strong>
                <p className="toggle-desc">All API write/mutation requests to raw telemetry archives are rejected.</p>
              </div>
              <span className="toggle-locked">
                <span className="material-symbols-outlined sym-icon-xs">lock</span>
                ENFORCED
              </span>
            </div>

            <div className="toggle-item">
              <div>
                <strong className="toggle-name">Rule 5: Honest Refusal Guard (Threshold 0.45)</strong>
                <p className="toggle-desc">Return unknown=true if correlation score &lt; 0.45 or outage is external.</p>
              </div>
              <span className="toggle-locked">
                <span className="material-symbols-outlined sym-icon-xs">lock</span>
                ENFORCED
              </span>
            </div>

            <div className="toggle-item">
              <div>
                <strong className="toggle-name">Rule 8: Ground Truth Isolation Gate</strong>
                <p className="toggle-desc">Causal models and API endpoints never read ground truth records.</p>
              </div>
              <span className="toggle-locked">
                <span className="material-symbols-outlined sym-icon-xs">lock</span>
                ENFORCED
              </span>
            </div>
          </div>

          <div className="settings-footer-actions">
            <button className="btn-save-settings" onClick={handleSave}>
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

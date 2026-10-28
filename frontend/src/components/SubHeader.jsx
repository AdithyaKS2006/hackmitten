import React from 'react';

export default function SubHeader({
  role,
  onRoleChange,
  health,
  isMockMode,
  onOpenReport,
  analysisReady,
}) {
  return (
    <div className="sub-header-bar techinova-hero-banner">
      {/* Title & Description with Neural Radar Icon */}
      <div className="sub-header-left">
        <div className="engine-icon-badge techinova-radar-badge">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" strokeDasharray="3 3"></circle>
            <circle cx="12" cy="12" r="6"></circle>
            <circle cx="12" cy="12" r="2" fill="#b47836"></circle>
            <line x1="12" y1="2" x2="12" y2="4"></line>
            <line x1="12" y1="20" x2="12" y2="22"></line>
            <line x1="2" y1="12" x2="4" y2="12"></line>
            <line x1="20" y1="12" x2="22" y2="12"></line>
          </svg>
          <div className="radar-pulse-ring"></div>
        </div>
        <div>
          <div className="engine-pretitle">TECHINOVA AIOps ENGINE • CAUSAL REASONING</div>
          <h1 className="engine-title">Root Cause Evidence Engine</h1>
          <p className="engine-description">
            Live multi-modal telemetry correlation isolating microservice failure chains with mathematical attribution proof.
          </p>
        </div>
      </div>

      {/* Action Badges & Options */}
      <div className="sub-header-right">
        {/* Read-only Storage pill */}
        <div className="pill-btn pill-neutral" title="Rule 1: Historical telemetry archives are strictly immutable">
          <span className="pill-icon">🔒</span>
          <span>Read-Only Storage</span>
        </div>

        {/* Role Selector Dropdown */}
        <div className="role-selector-pill">
          <span className="role-prefix">Role:</span>
          <select
            className="role-dropdown-native"
            value={role}
            onChange={(e) => onRoleChange && onRoleChange(e.target.value)}
          >
            <option value="analyst">Analyst (Full Access)</option>
            <option value="viewer">Auditor (Read-Only)</option>
          </select>
        </div>

        {/* API Online Badge */}
        <div className="pill-btn pill-success">
          <span className="dot-pulse-green"></span>
          <span>API Connected (Cluster Ready)</span>
        </div>

        {/* View Report Button */}
        <button
          type="button"
          className="btn-view-report"
          onClick={onOpenReport}
          title="Open printable post-incident review dossier"
        >
          <span className="btn-icon">📄</span>
          <span>View Report</span>
        </button>
      </div>
    </div>
  );
}

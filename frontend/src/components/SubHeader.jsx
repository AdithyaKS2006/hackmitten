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
    <div className="sub-header-bar">
      {/* Title & Description with Network Icon */}
      <div className="sub-header-left">
        <div className="engine-icon-badge">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="18" cy="5" r="3"></circle>
            <circle cx="6" cy="12" r="3"></circle>
            <circle cx="18" cy="19" r="3"></circle>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
          </svg>
        </div>
        <div>
          <h1 className="engine-title">Root Cause Evidence Engine</h1>
          <p className="engine-description">
            Analyze microservice incidents using ML and telemetry data to find the most likely root cause.
          </p>
        </div>
      </div>

      {/* Action Badges & Options */}
      <div className="sub-header-right">
        {/* Read-only Storage pill */}
        <div className="pill-btn pill-neutral">
          <span className="pill-icon">📁</span>
          <span>Read-only Storage</span>
        </div>

        {/* Role Selector Dropdown */}
        <div className="role-selector-pill">
          <span className="role-prefix">Role:</span>
          <select
            className="role-dropdown-native"
            value={role}
            onChange={(e) => onRoleChange && onRoleChange(e.target.value)}
          >
            <option value="analyst">Analyst (Full)</option>
            <option value="viewer">Viewer (Read)</option>
          </select>
        </div>

        {/* API Online Badge */}
        <div className="pill-btn pill-success">
          <span className="dot-pulse-green"></span>
          <span>API Online ({health?.mode || 'file'})</span>
        </div>

        {/* View Report Button */}
        <button
          className="btn-view-report"
          onClick={onOpenReport}
          title="Open printable post-incident review report"
        >
          <span className="btn-icon">📄</span>
          <span>View Report</span>
        </button>
      </div>
    </div>
  );
}

import React from 'react';

/**
 * Main Navigation & Header Component
 * Houses top-level branding, active scenario switcher, role authorization selector,
 * system status pill, and primary tab navigation.
 */
export default function Header({
  scenarios,
  selectedScenario,
  onSelectScenario,
  role,
  onRoleChange,
  activeTab,
  onTabChange,
  health,
  isMockMode,
  onOpenReport,
  analysisReady,
}) {
  return (
    <header className="main-header">
      {/* Top Banner Row */}
      <div className="header-top-row">
        <div className="brand-group">
          <div className="brand-logo-badge">
            <span className="brand-icon">⚡</span>
            <span>AO-03 ENGINE</span>
          </div>
          <div>
            <h1 className="header-app-title">Root Cause Evidence Engine</h1>
            <p className="header-tagline">
              Automated causal attribution & verifiable evidence extraction for microservices incidents
            </p>
          </div>
        </div>

        {/* Global Status Pills & Role Controls */}
        <div className="header-controls-group">
          {/* Read-Only Safety Pill */}
          <div className="pill-badge pill-readonly" title="Rule 1: Read-only storage guarantee">
            <span className="dot dot-blue"></span>
            <span>READ-ONLY STORAGE</span>
          </div>

          {/* Role Authorization Pill */}
          <div className="role-dropdown-wrap">
            <label htmlFor="role-select" className="role-dropdown-label">Role:</label>
            <select
              id="role-select"
              className="role-select-box"
              value={role}
              onChange={(e) => onRoleChange(e.target.value)}
              title="Select request authorization role (X-Role header)"
            >
              <option value="analyst">analyst (Full)</option>
              <option value="viewer">viewer (Read)</option>
            </select>
          </div>

          {/* Backend Online / Mock Pill */}
          {isMockMode ? (
            <div className="pill-badge pill-mock" title="Running in offline local mock fallback mode">
              <span className="dot dot-amber"></span>
              <span>Offline Mock Mode</span>
            </div>
          ) : (
            <div className="pill-badge pill-online" title="Django API Online">
              <span className="dot dot-green"></span>
              <span>API Online ({health?.mode || 'Ready'})</span>
            </div>
          )}

          {/* Post-Incident Report Trigger */}
          {analysisReady && (
            <button
              className="btn-report-export"
              onClick={onOpenReport}
              title="Open printable post-incident review dossier"
            >
              📄 Post-Incident Report
            </button>
          )}
        </div>
      </div>

      {/* Navigation & Scenario Selector Bar */}
      <div className="header-nav-bar">
        {/* Scenario Selector */}
        <div className="scenario-selector-wrap">
          <label htmlFor="scenario-select" className="scenario-label">Incident Scenario:</label>
          <select
            id="scenario-select"
            className="scenario-select-box"
            value={selectedScenario}
            onChange={(e) => onSelectScenario(e.target.value)}
          >
            {scenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name || sc.id} ({sc.id})
              </option>
            ))}
          </select>
        </div>

        {/* Main Tabs */}
        <nav className="header-tabs-nav" aria-label="Investigation views">
          <button
            className={`tab-btn ${activeTab === 'investigation' ? 'active' : ''}`}
            onClick={() => onTabChange('investigation')}
          >
            🔍 Investigation Console
          </button>
          <button
            className={`tab-btn ${activeTab === 'evaluation' ? 'active' : ''}`}
            onClick={() => onTabChange('evaluation')}
          >
            📊 Benchmark Evaluation
          </button>
          <button
            className={`tab-btn ${activeTab === 'safety' ? 'active' : ''}`}
            onClick={() => onTabChange('safety')}
          >
            🛡️ Safety & Governance
          </button>
        </nav>
      </div>
    </header>
  );
}

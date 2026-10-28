import React from 'react';

export default function ActionBar({
  scenarios = [],
  selectedScenario,
  onSelectScenario,
  activeTab,
  onTabChange,
}) {
  const tabs = [
    { id: 'investigation', label: 'Investigation Console', icon: '🔍' },
    { id: 'evaluation', label: 'Benchmark Evaluation', icon: '📊' },
    { id: 'safety', label: 'Safety & Governance', icon: '🛡️' },
  ];

  return (
    <div className="action-bar-row">
      {/* Scenario Selector Dropdown */}
      <div className="scenario-select-container">
        <span className="scenario-field-label">Incident Scenario:</span>
        <div className="scenario-select-wrapper">
          <span className="scenario-db-icon">🗄️</span>
          <select
            className="scenario-select-dropdown"
            value={selectedScenario}
            onChange={(e) => onSelectScenario(e.target.value)}
          >
            {scenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name || sc.id} ({sc.id})
              </option>
            ))}
          </select>
          <span className="select-arrow">▾</span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="nav-tabs-bar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`action-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

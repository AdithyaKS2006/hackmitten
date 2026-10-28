import React from 'react';

export default function Sidebar({ currentNav = 'dashboard', onNavChange }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', tag: 'Core' },
    { id: 'incidents', label: 'Incidents', icon: 'warning', tag: '6' },
    { id: 'servicemap', label: 'Service Map', icon: 'account_tree', tag: 'Topo' },
    { id: 'reports', label: 'Reports', icon: 'description', tag: 'Audit' },
    { id: 'settings', label: 'Settings', icon: 'settings', tag: 'Config' },
  ];

  return (
    <aside className="app-sidebar">
      {/* Brand Logo & Name: TechInova */}
      <div className="sidebar-brand">
        <div className="brand-cube-icon techinova-logo-wrap">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Hexagonal Server Frame */}
            <path
              d="M16 2L29 9.5V22.5L16 30L3 22.5V9.5L16 2Z"
              stroke="#b47836"
              strokeWidth="2.2"
              fill="#faf4ec"
            />
            {/* TechInova Stylized 'T' & Network Core */}
            <path
              d="M10 10H22M16 10V22"
              stroke="#8c5221"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            {/* Interconnected Server Nodes */}
            <circle cx="10" cy="10" r="2.2" fill="#b47836" />
            <circle cx="22" cy="10" r="2.2" fill="#b47836" />
            <circle cx="16" cy="22" r="2.5" fill="#22a06b" />
            <circle cx="16" cy="10" r="1.8" fill="#ffffff" />
          </svg>
        </div>
        <div className="brand-text">
          <h2 className="brand-title">TechInova</h2>
          <span className="brand-subtitle">AIOps Incident Intelligence</span>
        </div>
      </div>

      {/* Nav Menu with Distinct Light Borders and Google Material Symbols */}
      <nav className="sidebar-nav">
        <span className="sidebar-section-label">PLATFORM NAVIGATION</span>
        {navItems.map((item) => {
          const isActive = currentNav === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-item-btn ${isActive ? 'active' : ''}`}
              onClick={() => onNavChange && onNavChange(item.id)}
              title={`Switch to ${item.label}`}
            >
              <div className="nav-item-left">
                <span className="material-symbols-outlined nav-item-icon">{item.icon}</span>
                <span className="nav-item-label">{item.label}</span>
              </div>
              <span className={`nav-item-pill ${isActive ? 'active-pill' : ''}`}>
                {item.tag}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Standard Enterprise Cluster Health Indicator */}
      <div className="sidebar-footer-card enterprise-health-card">
        <div className="system-status-header">
          <div className="status-badge-live">
            <span className="pulse-dot-beacon"></span>
            <span className="status-state-text">Cluster Operational</span>
          </div>
          <span className="system-version-pill">v2.4 Live</span>
        </div>

        <div className="system-metrics-mini-list">
          <div className="system-metric-line">
            <span className="s-metric-label">Monitored Services</span>
            <span className="s-metric-val">6 of 6 Active</span>
          </div>
          <div className="system-metric-line">
            <span className="s-metric-label">AI Engine</span>
            <span className="s-metric-val badge-ml">RCA ML Ready</span>
          </div>
          <div className="system-metric-line">
            <span className="s-metric-label">Telemetry Latency</span>
            <span className="s-metric-val">12ms • P99 Normal</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

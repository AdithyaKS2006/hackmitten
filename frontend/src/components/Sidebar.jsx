import React from 'react';

export default function Sidebar({ currentNav = 'dashboard', onNavChange }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠', tag: 'Core' },
    { id: 'incidents', label: 'Incidents', icon: '⚠️', tag: '6' },
    { id: 'servicemap', label: 'Service Map', icon: '🔗', tag: 'Topo' },
    { id: 'reports', label: 'Reports', icon: '📄', tag: 'Audit' },
    { id: 'settings', label: 'Settings', icon: '⚙️', tag: 'Config' },
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

      {/* Nav Menu with Light Borders and Distinct Action Buttons */}
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
                <span className="nav-item-icon">{item.icon}</span>
                <span className="nav-item-label">{item.label}</span>
              </div>
              <span className={`nav-item-pill ${isActive ? 'active-pill' : ''}`}>
                {item.tag}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Health Badge - Replaced technical raw API URL with user-friendly cluster health */}
      <div className="sidebar-footer-card">
        <div className="status-indicator-row">
          <span className="status-dot-green"></span>
          <span className="status-text-bold">Cluster Health: Healthy</span>
        </div>
        <div className="status-subtext">6 Services Monitored • Live ML Inference</div>
      </div>
    </aside>
  );
}

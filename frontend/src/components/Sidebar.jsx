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
      {/* Brand Logo & Name */}
      <div className="sidebar-brand">
        <div className="brand-cube-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" fill="#f6ece0" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
        </div>
        <div className="brand-text">
          <h2 className="brand-title">Hackmitten</h2>
          <span className="brand-subtitle">AIOps Root Cause Analysis</span>
        </div>
      </div>

      {/* Nav Menu with Light Borders and Distinct Action Buttons */}
      <nav className="sidebar-nav">
        <span className="sidebar-section-label">MAIN NAVIGATION</span>
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

      {/* Bottom Online Status Badge */}
      <div className="sidebar-footer-card">
        <div className="status-indicator-row">
          <span className="status-dot-green"></span>
          <span className="status-text-bold">System Online</span>
        </div>
        <div className="status-timestamp">API: http://localhost:8000</div>
      </div>
    </aside>
  );
}

import React, { useState, useEffect, useRef } from 'react';

export default function TopNav({
  onSearch,
  role = 'analyst',
  onRoleChange,
  onNavigate,
  onSelectScenario,
  onSelectService,
}) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [unreadCount, setUnreadCount] = useState(4);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);

  const notifRef = useRef(null);
  const accountRef = useRef(null);
  const searchRef = useRef(null);

  // Search catalog index using Google Material Symbols
  const searchCatalog = [
    { type: 'Service', icon: 'credit_card', title: 'payment', subtitle: 'Root Cause • Python Django • Port 8000', action: () => { if (onSelectService) onSelectService('payment'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Service', icon: 'shopping_cart', title: 'checkout', subtitle: 'Cascade Victim • Go gRPC • High Latency', action: () => { if (onSelectService) onSelectService('checkout'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Service', icon: 'desktop_windows', title: 'frontend', subtitle: 'Cascade Victim • Node.js Express Gateway', action: () => { if (onSelectService) onSelectService('frontend'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Service', icon: 'shopping_bag', title: 'cart', subtitle: 'Healthy Service • Java Spring Boot', action: () => { if (onSelectService) onSelectService('cart'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Service', icon: 'person', title: 'user', subtitle: 'Healthy Service • Go Profile Service', action: () => { if (onSelectService) onSelectService('user'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Service', icon: 'database', title: 'db', subtitle: 'PostgreSQL Relational Cluster', action: () => { if (onSelectService) onSelectService('db'); if (onNavigate) onNavigate('dashboard'); } },

    { type: 'Scenario', icon: 'bolt', title: 'Payment DB Pool Exhaustion Cascade', subtitle: 'Scenario: mock • Database thread pool starved', action: () => { if (onSelectScenario) onSelectScenario('mock'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Scenario', icon: 'warning', title: 'Payment DB Connection Pool Starvation', subtitle: 'Scenario: syn_1 • Configuration change 50 -> 5', action: () => { if (onSelectScenario) onSelectScenario('syn_1'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Scenario', icon: 'bug_report', title: 'Cart Service NullPointer Release Regression', subtitle: 'Scenario: syn_2 • Deployment failure v2', action: () => { if (onSelectScenario) onSelectScenario('syn_2'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Scenario', icon: 'lock', title: 'Database Lock Saturation (No Change)', subtitle: 'Scenario: syn_3 • Row lock contention', action: () => { if (onSelectScenario) onSelectScenario('syn_3'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Scenario', icon: 'trending_up', title: 'Checkout Memory Leak with Red Herring', subtitle: 'Scenario: syn_4 • Heap exhaustion', action: () => { if (onSelectScenario) onSelectScenario('syn_4'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Scenario', icon: 'shield', title: 'External Payment Gateway Outage', subtitle: 'Scenario: syn_5 • Honest Unknown Refusal Guard', action: () => { if (onSelectScenario) onSelectScenario('syn_5'); if (onNavigate) onNavigate('dashboard'); } },

    { type: 'Telemetry Signal', icon: 'search_check', title: 'Connection Pool Exhausted Logs', subtitle: 'Failed to obtain DB connection within 5000ms', action: () => { if (onSelectService) onSelectService('payment'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Telemetry Signal', icon: 'show_chart', title: 'P99 Latency Spike > 1800ms', subtitle: 'Cross-service cascade from checkout to frontend', action: () => { if (onSelectService) onSelectService('checkout'); if (onNavigate) onNavigate('dashboard'); } },
    { type: 'Telemetry Signal', icon: 'verified_user', title: 'PII Redacted Telemetry Records', subtitle: 'Verified sanitization of credentials and IP addresses', action: () => { if (onNavigate) onNavigate('settings'); } },
  ];

  const filteredSearchResults = searchCatalog.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.subtitle.toLowerCase().includes(q) ||
      item.type.toLowerCase().includes(q)
    );
  });

  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'critical',
      icon: 'crisis_alert',
      title: 'Payment Connection Pool Starved',
      desc: 'db connection pool_size 50 -> 5 caused thread exhaustion on payment service.',
      time: '13:58:15 UTC',
      unread: true,
      service: 'payment',
    },
    {
      id: 2,
      type: 'warning',
      icon: 'warning',
      title: 'Checkout Latency Cascade',
      desc: 'Downstream HTTP transactions queued. P99 latency reached 1820ms.',
      time: '13:58:40 UTC',
      unread: true,
      service: 'checkout',
    },
    {
      id: 3,
      type: 'change',
      icon: 'bolt',
      title: 'Configuration Change Deployed',
      desc: 'Database connection parameters modified on payment cluster.',
      time: '13:55:00 UTC',
      unread: true,
      service: 'payment',
    },
    {
      id: 4,
      type: 'security',
      icon: 'verified_user',
      title: 'PII Sanitization Verified',
      desc: 'All customer credentials and IP addresses sanitized before model inference.',
      time: '13:50:00 UTC',
      unread: true,
      service: 'ingest',
    },
  ]);

  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
      if (accountRef.current && !accountRef.current.contains(e.target)) {
        setShowAccountMenu(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSearchDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    setUnreadCount(0);
  };

  const handleNotificationClick = (n) => {
    setNotifications((prev) =>
      prev.map((item) => (item.id === n.id ? { ...item, unread: false } : item))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
    setShowNotifications(false);
    if (onNavigate) onNavigate('dashboard');
  };

  const handleSearchResultClick = (item) => {
    item.action();
    setShowSearchDropdown(false);
    setSearchQuery('');
  };

  return (
    <header className="top-navbar">
      {/* Interactive Global Search Bar */}
      <div className="search-bar-container" ref={searchRef}>
        <span className="search-icon">
          <span className="material-symbols-outlined">search</span>
        </span>
        <input
          type="text"
          className="search-input"
          placeholder="Search services, incident scenarios or telemetry signals..."
          value={searchQuery}
          onFocus={() => setShowSearchDropdown(true)}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setShowSearchDropdown(true);
            if (onSearch) onSearch(e.target.value);
          }}
        />

        {searchQuery ? (
          <button
            type="button"
            className="search-clear-btn"
            onClick={() => {
              setSearchQuery('');
              if (onSearch) onSearch('');
            }}
          >
            <span className="material-symbols-outlined sym-icon-xs">close</span>
          </button>
        ) : (
          <span className="search-shortcut-pill">Ctrl+K</span>
        )}

        {/* Live Search Results Dropdown */}
        {showSearchDropdown && (
          <div className="search-results-dropdown">
            <div className="search-results-header">
              <span>Quick Navigation & Telemetry Index</span>
              <span className="search-count-badge">{filteredSearchResults.length} matches</span>
            </div>

            <div className="search-results-list">
              {filteredSearchResults.length > 0 ? (
                filteredSearchResults.map((res, idx) => (
                  <div
                    key={idx}
                    className="search-result-item"
                    onClick={() => handleSearchResultClick(res)}
                  >
                    <span className="search-item-icon">
                      <span className="material-symbols-outlined">{res.icon}</span>
                    </span>
                    <div className="search-item-text">
                      <div className="search-item-title-row">
                        <strong className="search-item-title">{res.title}</strong>
                        <span className="search-item-type">{res.type}</span>
                      </div>
                      <span className="search-item-subtitle">{res.subtitle}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="search-empty-state">
                  <span>No matches found for "{searchQuery}". Try "payment", "cascade", or "pool".</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Controls: Notifications & User Profile */}
      <div className="top-nav-right">
        {/* Notification Bell with Badge & Dropdown */}
        <div className="top-nav-dropdown-wrapper" ref={notifRef}>
          <button
            type="button"
            className={`icon-btn-round ${showNotifications ? 'active' : ''}`}
            title="Notifications & Incident Alerts"
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowAccountMenu(false);
              setShowSearchDropdown(false);
            }}
          >
            <span className="material-symbols-outlined">notifications</span>
            {unreadCount > 0 && (
              <span className="notification-badge-number">{unreadCount}</span>
            )}
          </button>

          {/* Interactive Notifications Panel */}
          {showNotifications && (
            <div className="dropdown-panel-menu notifications-dropdown-panel">
              <div className="dropdown-panel-header">
                <div className="d-flex align-center gap-6">
                  <span className="panel-title">System Alerts & Notifications</span>
                  {unreadCount > 0 && (
                    <span className="panel-count-tag">{unreadCount} new</span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button className="btn-text-action" onClick={markAllRead}>
                    Mark all read
                  </button>
                )}
              </div>

              <div className="notifications-list-scroll">
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`notification-item-card ${n.unread ? 'unread' : ''}`}
                    onClick={() => handleNotificationClick(n)}
                  >
                    <span className="notif-icon">
                      <span className="material-symbols-outlined sym-icon-sm">{n.icon}</span>
                    </span>
                    <div className="notif-body">
                      <div className="notif-title-row">
                        <strong className="notif-title">{n.title}</strong>
                        <span className="notif-time">{n.time}</span>
                      </div>
                      <p className="notif-desc">{n.desc}</p>
                      <div className="notif-meta-tags">
                        <span className="notif-service-pill">{n.service}</span>
                        {n.unread && <span className="notif-unread-dot"></span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="dropdown-panel-footer">
                <button
                  className="btn-footer-link"
                  onClick={() => {
                    setShowNotifications(false);
                    if (onNavigate) onNavigate('dashboard');
                  }}
                >
                  View Incident Investigation Timeline →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Profile / Account Menu: TechInova */}
        <div className="top-nav-dropdown-wrapper" ref={accountRef}>
          <div
            className={`user-profile-badge ${showAccountMenu ? 'active' : ''}`}
            onClick={() => {
              setShowAccountMenu(!showAccountMenu);
              setShowNotifications(false);
              setShowSearchDropdown(false);
            }}
          >
            <div className="user-avatar-circle">A</div>
            <div className="user-meta-name-col">
              <span className="user-name">Amrutha</span>
              <span className="user-role-label">{role === 'analyst' ? 'Analyst' : 'Auditor'}</span>
            </div>
            <span className="material-symbols-outlined dropdown-caret">arrow_drop_down</span>
          </div>

          {/* Interactive Account Dropdown Panel */}
          {showAccountMenu && (
            <div className="dropdown-panel-menu account-dropdown-panel">
              {/* User Header */}
              <div className="account-panel-user-header">
                <div className="large-avatar-circle">A</div>
                <div className="user-full-details">
                  <h4 className="account-user-name">Amrutha</h4>
                  <span className="account-user-email">Lead SRE & Incident Commander</span>
                  <span className="account-team-badge">TechInova SRE Team</span>
                </div>
              </div>

              {/* Role Switcher Section */}
              <div className="account-section">
                <span className="account-section-label">Switch Active Permission Role:</span>
                <div className="role-options-list">
                  <div
                    className={`role-option-item ${role === 'analyst' ? 'active-role' : ''}`}
                    onClick={() => {
                      if (onRoleChange) onRoleChange('analyst');
                    }}
                  >
                    <div>
                      <strong className="role-opt-name">Analyst (Full Access)</strong>
                      <span className="role-opt-desc">Full telemetry analysis, replay & evidence inspector</span>
                    </div>
                    {role === 'analyst' && <span className="material-symbols-outlined sym-icon-xs text-primary">check</span>}
                  </div>

                  <div
                    className={`role-option-item ${role === 'viewer' ? 'active-role' : ''}`}
                    onClick={() => {
                      if (onRoleChange) onRoleChange('viewer');
                    }}
                  >
                    <div>
                      <strong className="role-opt-name">Auditor (Read-Only)</strong>
                      <span className="role-opt-desc">Inspect post-mortem dossiers and governance audit</span>
                    </div>
                    {role === 'viewer' && <span className="material-symbols-outlined sym-icon-xs text-primary">check</span>}
                  </div>
                </div>
              </div>

              {/* Navigation Options */}
              <div className="account-section">
                <span className="account-section-label">Quick Links:</span>
                <div className="account-links-list">
                  <button
                    className="account-link-btn"
                    onClick={() => {
                      setShowAccountMenu(false);
                      if (onNavigate) onNavigate('dashboard');
                    }}
                  >
                    <span className="material-symbols-outlined sym-icon-sm">dashboard</span>
                    <span>Investigation Dashboard</span>
                  </button>
                  <button
                    className="account-link-btn"
                    onClick={() => {
                      setShowAccountMenu(false);
                      if (onNavigate) onNavigate('incidents');
                    }}
                  >
                    <span className="material-symbols-outlined sym-icon-sm">warning</span>
                    <span>Incident Catalog</span>
                  </button>
                  <button
                    className="account-link-btn"
                    onClick={() => {
                      setShowAccountMenu(false);
                      if (onNavigate) onNavigate('reports');
                    }}
                  >
                    <span className="material-symbols-outlined sym-icon-sm">description</span>
                    <span>Post-Incident Reports</span>
                  </button>
                  <button
                    className="account-link-btn"
                    onClick={() => {
                      setShowAccountMenu(false);
                      if (onNavigate) onNavigate('settings');
                    }}
                  >
                    <span className="material-symbols-outlined sym-icon-sm">settings</span>
                    <span>System Settings</span>
                  </button>
                </div>
              </div>

              {/* Session Status & Logout */}
              <div className="account-panel-footer">
                <div className="session-status-text">
                  <span className="dot-green"></span>
                  <span>Session: Active (TechInova Cluster)</span>
                </div>
                <button
                  className="btn-account-logout"
                  onClick={() => {
                    alert('Session verified for operator Amrutha.');
                    setShowAccountMenu(false);
                  }}
                >
                  Reset Session
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

import React from 'react';

export default function TopNav({ onSearch }) {
  return (
    <header className="top-navbar">
      {/* Search Input Bar */}
      <div className="search-bar-container">
        <span className="search-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8a8074" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </span>
        <input
          type="text"
          className="search-input"
          placeholder="Search service, incident or keyword..."
          onChange={(e) => onSearch && onSearch(e.target.value)}
        />
      </div>

      {/* Right Controls: Notifications & User Profile */}
      <div className="top-nav-right">
        {/* Notification Bell */}
        <button className="icon-btn-round" title="Notifications">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5a5247" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          <span className="notification-dot-red"></span>
        </button>

        {/* User Profile Avatar */}
        <div className="user-profile-badge">
          <div className="user-avatar-circle">A</div>
          <span className="user-name">Amrutha</span>
          <span className="dropdown-caret">▾</span>
        </div>
      </div>
    </header>
  );
}

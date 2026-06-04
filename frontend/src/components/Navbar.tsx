import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <nav className="navbar glass-card">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/dashboard" className="brand-logo">
            <span className="gradient-text">GnuCash SaaS</span>
          </Link>
        </div>
        
        <div className="navbar-links">
          <Link 
            to="/dashboard" 
            className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/files" 
            className={`nav-link ${location.pathname === '/files' ? 'active' : ''}`}
          >
            Files
          </Link>
        </div>

        <div className="navbar-user">
          <span className="user-email">{user?.email}</span>
          <button onClick={logout} className="btn btn-secondary btn-sm">
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}


import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/dashboard" className="brand-logo">
            <span className="text-gradient">GnuCash SaaS</span>
          </Link>
        </div>
        
        <div className="navbar-links">
          <Link 
            to="/dashboard" 
            className={location.pathname === '/dashboard' ? 'active' : ''}
          >
            Dashboard
          </Link>
          <Link 
            to="/files" 
            className={location.pathname === '/files' ? 'active' : ''}
          >
            Files
          </Link>
        </div>

        <div className="navbar-right">
          <span className="navbar-email">{user?.email}</span>
          <button onClick={logout} className="btn btn-secondary btn-sm">
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

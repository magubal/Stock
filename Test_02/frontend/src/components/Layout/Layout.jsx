import React, { useState, useRef, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { TrendingUp, BarChart3, Activity, Bitcoin, Zap, FileText, Lightbulb, ChevronDown } from 'lucide-react';
import './Layout.css';

const Layout = () => {
  const [monitorOpen, setMonitorOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setMonitorOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const monitorLinks = [
    { to: '/liquidity-stress', icon: Activity, label: '유동성 스트레스', color: '#f97316' },
    { to: '/crypto-trends', icon: Bitcoin, label: '크립토 동향', color: '#a855f7' },
    { to: '/intelligence', icon: Zap, label: 'Intelligence Board', color: '#3b82f6' },
    { to: '/disclosures', icon: FileText, label: '공시 모니터', color: '#22c55e' },
  ];

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-inner">
          <NavLink to="/" className="app-logo">
            <div className="logo-icon">
              <TrendingUp size={22} />
            </div>
            <span>Stock Research <span className="highlight">ONE</span></span>
          </NavLink>

          <nav className="app-nav">
            <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <BarChart3 size={16} />
              <span>Dashboard</span>
            </NavLink>

            <div className="nav-dropdown" ref={dropdownRef}>
              <button
                className={`nav-link dropdown-trigger ${['/liquidity-stress', '/crypto-trends', '/intelligence', '/disclosures'].some(p => location.pathname === p) ? 'active' : ''}`}
                onClick={() => setMonitorOpen(!monitorOpen)}
              >
                <Activity size={16} />
                <span>모니터링</span>
                <ChevronDown size={14} className={`chevron ${monitorOpen ? 'open' : ''}`} />
              </button>
              {monitorOpen && (
                <div className="dropdown-menu">
                  {monitorLinks.map(({ to, icon: Icon, label, color }) => (
                    <NavLink
                      key={to}
                      to={to}
                      className={({ isActive }) => `dropdown-item ${isActive ? 'active' : ''}`}
                      onClick={() => setMonitorOpen(false)}
                    >
                      <Icon size={16} style={{ color }} />
                      <span>{label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>

            <NavLink to="/ideas" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Lightbulb size={16} />
              <span>아이디어</span>
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

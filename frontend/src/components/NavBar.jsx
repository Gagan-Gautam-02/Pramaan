import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, LayoutDashboard, Clock, LogOut, User } from 'lucide-react'

export default function NavBar() {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <nav style={{
      borderBottom: '1px solid var(--border)',
      background: 'rgba(8,12,20,0.8)',
      backdropFilter: 'blur(20px)',
      position: 'sticky', top: 0, zIndex: 100,
    }}>
      <div className="container" style={{
        display: 'flex', alignItems: 'center',
        height: 60, gap: '1.5rem',
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none' }}>
          <div style={{
            width: 32, height: 32,
            background: 'linear-gradient(135deg, #4f8ef7, #7c3aed)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <ShieldCheck size={18} color="#fff" />
          </div>
          <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
            DeepSafe
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: 'flex', gap: '0.25rem', flex: 1 }}>
          {[
            { to: '/', icon: <LayoutDashboard size={15} />, label: 'Dashboard' },
            { to: '/history', icon: <Clock size={15} />, label: 'History' },
          ].map(link => (
            <Link
              key={link.to}
              to={link.to}
              id={`nav-${link.label.toLowerCase()}`}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.4rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.88rem', fontWeight: 500,
                color: pathname === link.to ? 'var(--brand)' : 'var(--text-secondary)',
                background: pathname === link.to ? 'rgba(79,142,247,0.1)' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.15s',
              }}
            >
              {link.icon} {link.label}
            </Link>
          ))}
        </div>

        {/* User */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {user && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              color: 'var(--text-secondary)', fontSize: '0.85rem',
            }}>
              <User size={14} />
              <span>{user.username}</span>
            </div>
          )}
          <button
            id="nav-logout"
            onClick={handleLogout}
            className="btn btn-ghost"
            style={{ padding: '0.4rem 0.75rem', fontSize: '0.82rem' }}
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}

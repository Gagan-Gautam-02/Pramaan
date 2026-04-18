import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function Login() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'register') {
        await register(username, password)
        await login(username, password)
      } else {
        await login(username, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Check credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page" style={{ justifyContent: 'center', alignItems: 'center', padding: '2rem' }}>
      <div className="bg-animated" />

      {/* Logo */}
      <div className="fade-in" style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.7rem', marginBottom: '0.75rem' }}>
          <div style={{
            width: 48, height: 48,
            background: 'linear-gradient(135deg, #4f8ef7, #7c3aed)',
            borderRadius: 14,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 24px rgba(79,142,247,0.4)',
          }}>
            <ShieldCheck size={26} color="#fff" />
          </div>
          <h1 className="glow-text" style={{ fontSize: '2.2rem', margin: 0 }}>DeepSafe</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Enterprise-grade deepfake detection
        </p>
      </div>

      {/* Card */}
      <div className="glass fade-in" style={{
        width: '100%', maxWidth: 420, padding: '2.5rem',
        animationDelay: '0.1s',
      }}>
        {/* Tabs */}
        <div style={{
          display: 'flex', background: 'var(--bg-700)',
          borderRadius: 'var(--radius-sm)', padding: 4, marginBottom: '2rem',
        }}>
          {['login', 'register'].map(m => (
            <button
              key={m}
              id={`tab-${m}`}
              onClick={() => { setMode(m); setError('') }}
              style={{
                flex: 1, padding: '0.55rem', border: 'none',
                borderRadius: 'var(--radius-sm)',
                background: mode === m ? 'var(--brand)' : 'transparent',
                color: mode === m ? '#fff' : 'var(--text-secondary)',
                fontFamily: 'var(--font-sans)',
                fontWeight: 600, fontSize: '0.88rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                textTransform: 'capitalize',
              }}
            >
              {m === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          {/* Username */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label className="label" htmlFor="login-username">Username</label>
            <input
              id="login-username"
              className="input"
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>

          {/* Password */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label className="label" htmlFor="login-password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-password"
                className="input"
                type={showPwd ? 'text' : 'password'}
                placeholder="Enter password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                style={{ paddingRight: '2.8rem' }}
              />
              <button
                type="button"
                onClick={() => setShowPwd(v => !v)}
                style={{
                  position: 'absolute', right: 12, top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none', border: 'none',
                  color: 'var(--text-muted)', cursor: 'pointer',
                  display: 'flex',
                }}
                aria-label="Toggle password visibility"
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              background: 'rgba(255,77,77,0.1)',
              border: '1px solid rgba(255,77,77,0.3)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.65rem 0.9rem',
              marginBottom: '1.25rem',
              fontSize: '0.88rem',
              color: 'var(--danger)',
            }}>
              <AlertCircle size={15} />
              {error}
            </div>
          )}

          <button
            id="auth-submit"
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '0.75rem' }}
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <p style={{
          textAlign: 'center', marginTop: '1.5rem',
          fontSize: '0.83rem', color: 'var(--text-muted)',
        }}>
          Demo: register any username/password to get started
        </p>
      </div>
    </div>
  )
}

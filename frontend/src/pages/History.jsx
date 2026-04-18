import { useState, useEffect } from 'react'
import NavBar from '../components/NavBar'
import { useAuth } from '../context/AuthContext'
import { Clock, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'

function HistoryRow({ item, idx }) {
  const [open, setOpen] = useState(false)
  const isF = item.verdict === 'fake'

  return (
    <div
      className="glass"
      style={{ padding: 0, overflow: 'hidden', transition: 'all 0.2s' }}
    >
      <button
        id={`history-row-${idx}`}
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: '1rem',
          padding: '1rem 1.25rem',
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-primary)', textAlign: 'left',
        }}
      >
        {/* Verdict dot */}
        <div style={{
          width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
          background: isF ? 'var(--danger)' : 'var(--safe)',
          boxShadow: `0 0 8px ${isF ? 'var(--danger)' : 'var(--safe)'}`,
        }} />

        <div style={{ flex: 1, display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <span className={`badge ${isF ? 'badge-fake' : 'badge-real'}`}>
            {item.verdict.toUpperCase()}
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            {item.media_type}
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            {item.ensemble_method}
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '0.88rem', color: 'var(--brand)',
          }}>
            {(item.confidence * 100).toFixed(1)}% conf
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginLeft: 'auto' }}>
            {new Date(item.timestamp + 'Z').toLocaleString()}
          </span>
        </div>
        {open ? <ChevronUp size={16} color="var(--text-muted)" /> : <ChevronDown size={16} color="var(--text-muted)" />}
      </button>

      {open && (
        <div style={{ padding: '0 1.25rem 1.25rem', borderTop: '1px solid var(--border)' }}>
          <div style={{ paddingTop: '1rem' }}>
            <div className="label" style={{ marginBottom: '0.75rem' }}>Model Results</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {Object.entries(item.model_results || {}).map(([name, r]) => (
                <div key={name} style={{
                  display: 'flex', alignItems: 'center', gap: '1rem',
                  background: 'var(--bg-700)', borderRadius: 'var(--radius-sm)',
                  padding: '0.6rem 0.9rem',
                }}>
                  <span style={{ flex: 1, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{name}</span>
                  <span className={`badge ${r.label === 'fake' ? 'badge-fake' : 'badge-real'}`} style={{ fontSize: '0.75rem' }}>
                    {r.label}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--brand)', minWidth: 50, textAlign: 'right' }}>
                    {(r.probability * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function History() {
  const { authAxios } = useAuth()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    authAxios().get('/history')
      .then(res => setHistory(res.data))
      .catch(err => setError(err.response?.data?.detail || 'Failed to load history'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="bg-animated" />
      <NavBar />

      <main className="container" style={{ flex: 1, paddingTop: '2rem', paddingBottom: '3rem' }}>
        <div className="fade-in" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Clock size={24} color="var(--brand)" />
          <h2>Analysis History</h2>
        </div>

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
            <span className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
          </div>
        )}

        {error && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            background: 'rgba(255,77,77,0.1)', border: '1px solid rgba(255,77,77,0.3)',
            borderRadius: 'var(--radius-sm)', padding: '1rem 1.25rem',
            color: 'var(--danger)',
          }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {!loading && !error && history.length === 0 && (
          <div className="glass" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No analysis history yet. Run your first detection on the dashboard!
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {history.map((item, idx) => (
            <HistoryRow key={item.id} item={item} idx={idx} />
          ))}
        </div>
      </main>
    </div>
  )
}

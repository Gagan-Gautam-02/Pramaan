import { ShieldX, ShieldCheck, ShieldAlert } from 'lucide-react'

export default function ResultCard({ result }) {
  const isFake = result.verdict === 'fake'
  const isUnknown = result.verdict === 'unknown'
  const confidence = Math.round(result.confidence_in_verdict * 100)
  const score = Math.round(result.ensemble_score_is_fake * 100)

  const color = isFake ? 'var(--danger)' : isUnknown ? 'var(--accent-yellow)' : 'var(--safe)'
  const glow = isFake ? 'var(--danger-glow)' : isUnknown ? 'rgba(251,191,36,0.2)' : 'var(--safe-glow)'
  const Icon = isFake ? ShieldX : isUnknown ? ShieldAlert : ShieldCheck

  return (
    <div
      id="result-card"
      className="glass"
      style={{
        padding: '2rem',
        border: `1px solid ${color}44`,
        background: `${glow}`,
        textAlign: 'center',
      }}
    >
      {/* Icon */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 64, height: 64, borderRadius: '50%',
        background: `${glow}`,
        border: `2px solid ${color}55`,
        marginBottom: '1rem',
        boxShadow: `0 0 24px ${glow}`,
      }}>
        <Icon size={30} color={color} />
      </div>

      {/* Verdict */}
      <div style={{
        fontSize: '2.5rem', fontWeight: 800,
        color: color, letterSpacing: '-0.03em',
        marginBottom: '0.25rem',
        textShadow: `0 0 20px ${glow}`,
      }}>
        {result.verdict.toUpperCase()}
      </div>

      <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        {isFake
          ? 'This media appears to be AI-generated or manipulated.'
          : 'This media appears to be authentic.'}
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
        {[
          { label: 'Ensemble Score', value: `${score}%`, sub: 'P(fake)' },
          { label: 'Confidence', value: `${confidence}%`, sub: 'in verdict' },
          { label: 'Method', value: result.ensemble_method_used, sub: 'fusion' },
        ].map(stat => (
          <div key={stat.label} style={{
            background: 'var(--bg-700)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.75rem',
          }}>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '1.3rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
            }}>{stat.value}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {stat.sub}
            </div>
          </div>
        ))}
      </div>

      {/* Score bar */}
      <div style={{ marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Real</span>
          <span>Fake</span>
        </div>
        <div className="progress-track">
          <div
            className={`progress-fill ${isFake ? 'progress-fake' : 'progress-real'}`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    </div>
  )
}

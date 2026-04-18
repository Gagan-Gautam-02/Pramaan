import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'

export default function ModelBreakdown({ result }) {
  const entries = Object.entries(result.model_results || {})
  if (!entries.length) return null

  const chartData = entries.map(([name, r]) => ({
    model: name.replace(/_/g, ' ').replace('deepfakedetection', '').replace('universalfakedetect', 'UnivFake').trim(),
    score: Math.round((r.probability || 0) * 100),
  }))

  return (
    <div id="model-breakdown" className="glass" style={{ padding: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
        Model Breakdown
      </h3>

      {/* Per-model bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {entries.map(([name, r]) => {
          const pct = Math.round((r.probability || 0) * 100)
          const isFake = r.label === 'fake'
          return (
            <div key={name}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                marginBottom: '0.35rem', fontSize: '0.85rem',
              }}>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {name.replace(/_/g, ' ')}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className={`badge ${isFake ? 'badge-fake' : 'badge-real'}`} style={{ fontSize: '0.72rem' }}>
                    {r.label}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-primary)', minWidth: 42, textAlign: 'right' }}>
                    {pct}%
                  </span>
                </div>
              </div>
              <div className="progress-track" style={{ height: 6 }}>
                <div
                  className={`progress-fill ${isFake ? 'progress-fake' : 'progress-real'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      {/* Radar chart */}
      {chartData.length >= 3 && (
        <div style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData}>
              <PolarGrid stroke="rgba(99,179,237,0.1)" />
              <PolarAngleAxis dataKey="model" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Radar
                name="P(fake)"
                dataKey="score"
                stroke="#4f8ef7"
                fill="#4f8ef7"
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Tooltip
                contentStyle={{ background: 'var(--bg-700)', border: '1px solid var(--border)', borderRadius: 8 }}
                labelStyle={{ color: 'var(--text-secondary)' }}
                itemStyle={{ color: 'var(--brand)' }}
                formatter={(v) => [`${v}%`, 'P(fake)']}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

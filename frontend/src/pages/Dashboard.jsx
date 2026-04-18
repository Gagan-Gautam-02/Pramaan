import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import NavBar from '../components/NavBar'
import ResultCard from '../components/ResultCard'
import ModelBreakdown from '../components/ModelBreakdown'
import { useAuth } from '../context/AuthContext'
import {
  Upload, Image as ImageIcon, Film, Music,
  Zap, ChevronDown, Info,
} from 'lucide-react'

const MEDIA_TYPES = [
  { value: 'image', label: 'Image', icon: <ImageIcon size={15} />, accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp'] } },
  { value: 'video', label: 'Video', icon: <Film size={15} />, accept: { 'video/*': ['.mp4', '.avi', '.mov', '.mkv'] } },
  { value: 'audio', label: 'Audio', icon: <Music size={15} />, accept: { 'audio/*': ['.wav', '.mp3', '.flac', '.ogg'] } },
]

const ENSEMBLE_METHODS = [
  { value: 'voting', label: 'Voting', desc: 'Majority vote across models' },
  { value: 'average', label: 'Average', desc: 'Mean probability score' },
  { value: 'stacking', label: 'Stacking', desc: 'Trained meta-learner' },
]

export default function Dashboard() {
  const { token, API } = useAuth()
  const [mediaType, setMediaType] = useState('image')
  const [ensembleMethod, setEnsembleMethod] = useState('voting')
  const [threshold, setThreshold] = useState(0.5)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const currentType = MEDIA_TYPES.find(t => t.value === mediaType)

  const onDrop = useCallback((accepted) => {
    if (!accepted.length) return
    const f = accepted[0]
    setFile(f)
    setResult(null)
    setError('')
    if (f.type.startsWith('image/')) {
      const url = URL.createObjectURL(f)
      setPreview(url)
    } else {
      setPreview(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: currentType.accept,
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  })

  async function handleAnalyze() {
    if (!file) { setError('Please select a file first.'); return }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('ensemble_method', ensembleMethod)
      form.append('threshold', threshold)

      const headers = { Authorization: `Bearer ${token}` }
      const res = await axios.post(`${API}/detect`, form, { headers })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed. Is the gateway running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="bg-animated" />
      <NavBar />

      <main className="container" style={{ flex: 1, paddingTop: '2rem', paddingBottom: '3rem' }}>
        {/* Hero */}
        <div className="fade-in" style={{ marginBottom: '2.5rem' }}>
          <h1>
            Detect Deepfakes{' '}
            <span className="glow-text">Instantly</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '1.05rem' }}>
            Upload an image, video, or audio file and our ensemble of AI models will analyze it.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', alignItems: 'start' }}>
          {/* Left: Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Media type selector */}
            <div className="glass fade-in" style={{ padding: '1.5rem', animationDelay: '0.05s' }}>
              <label className="label">Media Type</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {MEDIA_TYPES.map(t => (
                  <button
                    key={t.value}
                    id={`media-type-${t.value}`}
                    onClick={() => { setMediaType(t.value); setFile(null); setPreview(null); setResult(null) }}
                    className="btn"
                    style={{
                      flex: 1,
                      background: mediaType === t.value
                        ? 'linear-gradient(135deg,var(--brand),#7c3aed)'
                        : 'var(--bg-700)',
                      color: mediaType === t.value ? '#fff' : 'var(--text-secondary)',
                      border: `1px solid ${mediaType === t.value ? 'transparent' : 'var(--border)'}`,
                      fontSize: '0.85rem',
                      padding: '0.55rem 0.75rem',
                    }}
                  >
                    {t.icon} {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Ensemble method */}
            <div className="glass fade-in" style={{ padding: '1.5rem', animationDelay: '0.1s' }}>
              <label className="label">Ensemble Method</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {ENSEMBLE_METHODS.map(m => (
                  <button
                    key={m.value}
                    id={`ensemble-${m.value}`}
                    onClick={() => setEnsembleMethod(m.value)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '0.75rem 1rem',
                      background: ensembleMethod === m.value ? 'rgba(79,142,247,0.1)' : 'var(--bg-700)',
                      border: `1px solid ${ensembleMethod === m.value ? 'var(--brand)' : 'var(--border)'}`,
                      borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      color: 'var(--text-primary)',
                    }}
                  >
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.label}</div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{m.desc}</div>
                    </div>
                    {ensembleMethod === m.value && (
                      <div style={{
                        width: 8, height: 8, borderRadius: '50%',
                        background: 'var(--brand)',
                        boxShadow: '0 0 8px var(--brand)',
                      }} />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Threshold */}
            <div className="glass fade-in" style={{ padding: '1.5rem', animationDelay: '0.15s' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <label className="label" style={{ margin: 0 }}>Detection Threshold</label>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: '0.88rem',
                  color: 'var(--brand)', fontWeight: 600,
                }}>
                  {threshold.toFixed(2)}
                </span>
              </div>
              <input
                id="threshold-slider"
                type="range" min={0} max={1} step={0.01}
                value={threshold}
                onChange={e => setThreshold(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--brand)', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.3rem' }}>
                <span>More sensitive</span>
                <span>Less sensitive</span>
              </div>
            </div>
          </div>

          {/* Right: Upload + Result */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Dropzone */}
            <div
              {...getRootProps()}
              id="file-dropzone"
              className="glass fade-in"
              style={{
                padding: '2.5rem',
                textAlign: 'center',
                cursor: 'pointer',
                border: `2px dashed ${isDragActive ? 'var(--brand)' : 'var(--border)'}`,
                background: isDragActive ? 'rgba(79,142,247,0.05)' : 'var(--surface)',
                transition: 'all 0.2s',
                animationDelay: '0.05s',
                minHeight: 220,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem',
              }}
            >
              <input {...getInputProps()} id="file-input" />
              {preview ? (
                <img
                  src={preview}
                  alt="Preview"
                  style={{ maxHeight: 160, maxWidth: '100%', borderRadius: 'var(--radius-md)', objectFit: 'contain' }}
                />
              ) : (
                <div style={{
                  width: 64, height: 64,
                  background: 'var(--bg-600)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Upload size={28} color="var(--brand)" />
                </div>
              )}
              {file ? (
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{file.name}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    {(file.size / 1024).toFixed(1)} KB — click to change
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontWeight: 600 }}>
                    {isDragActive ? 'Drop it!' : 'Drag & drop or click to upload'}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.3rem' }}>
                    {currentType.label} files up to 50 MB
                  </div>
                </div>
              )}
            </div>

            {/* Analyze button */}
            <button
              id="analyze-btn"
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '0.85rem', fontSize: '1rem' }}
              onClick={handleAnalyze}
              disabled={loading || !file}
            >
              {loading ? (
                <><span className="spinner" /> Analyzing…</>
              ) : (
                <><Zap size={18} /> Analyze Media</>
              )}
            </button>

            {/* Error */}
            {error && (
              <div style={{
                background: 'rgba(255,77,77,0.1)',
                border: '1px solid rgba(255,77,77,0.3)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.9rem 1rem',
                color: 'var(--danger)',
                fontSize: '0.88rem',
              }}>
                {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <ResultCard result={result} />
                <ModelBreakdown result={result} />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

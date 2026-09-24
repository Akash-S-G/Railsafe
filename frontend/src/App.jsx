import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

const LEVEL_COLOR = {
  CRITICAL: 'text-red-400 border-red-800',
  HIGH: 'text-orange-400 border-orange-800',
  MEDIUM: 'text-yellow-400 border-yellow-800',
  LOW: 'text-emerald-400 border-emerald-800',
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState({ inspected: 0, normal: 0, suspicious: 0, high_risk: 0, critical: 0 })
  const [assets, setAssets] = useState([])
  const [past, setPast] = useState([])
  const [pending, setPending] = useState([])   // [{file, url}] selected images
  const [batch, setBatch] = useState([])       // results of last run
  const [processing, setProcessing] = useState(false)
  const [chainage, setChainage] = useState('124320')
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef(null)

  const refresh = () => {
    axios.get(`${API}/queue`).then(r => Array.isArray(r.data) && setAssets(r.data)).catch(() => {})
    axios.get(`${API}/stats`).then(r => setStats(r.data)).catch(() => {})
    axios.get(`${API}/inspections`).then(r => Array.isArray(r.data) && setPast(r.data)).catch(() => {})
  }

  useEffect(() => {
    axios.get(`${API}/health`).then(r => setHealth(r.data)).catch(() => setHealth({ status: 'offline' }))
    refresh()
  }, [])

  const addFiles = (fileList) => {
    const arr = Array.from(fileList || []).filter(f => f.type.startsWith('image/'))
    setPending(p => [...p, ...arr.map(f => ({ file: f, url: URL.createObjectURL(f) }))])
  }

  const removePending = (i) => setPending(p => p.filter((_, j) => j !== i))

  const runBatch = async () => {
    if (!pending.length || processing) return
    setProcessing(true); setBatch([])
    const fd = new FormData()
    pending.forEach(p => fd.append('files', p.file))
    fd.append('chainage', chainage || '124320')
    fd.append('track', 'UP')
    fd.append('line', 'LINE-01')
    try {
      const r = await axios.post(`${API}/inspections`, fd)
      setBatch(Array.isArray(r.data) ? r.data : [r.data])
      refresh()
    } catch (e) {
      alert('Inspection failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setProcessing(false)
    }
  }

  const kpis = [
    ['Inspected', stats.inspected], ['Normal', stats.normal], ['Suspicious', stats.suspicious],
    ['High Risk', stats.high_risk], ['Critical', stats.critical],
  ]

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold tracking-tight">RAILSAFE <span className="text-zinc-500 font-normal">Railway Infrastructure Health</span></h1>
        <span className={`text-xs px-2 py-1 rounded ${health?.status === 'ok' ? 'bg-emerald-900 text-emerald-200' : 'bg-zinc-800 text-zinc-400'}`}>
          API {health?.status || 'checking...'} {health?.version || ''} {health?.temporal || ''}
        </span>
      </header>

      <main className="max-w-6xl mx-auto p-6 grid gap-6">
        {/* KPIs — live from /stats */}
        <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {kpis.map(([k, v]) => (
            <div key={k} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
              <div className="text-xs text-zinc-500">{k}</div>
              <div className="text-2xl font-mono">{v ?? 0}</div>
            </div>
          ))}
        </section>

        {/* Inspect — drag & drop, batch */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Inspect Images <span className="text-zinc-500 text-sm">YOLO → fusion → severity → risk (batch supported)</span></h2>

          <div
            data-testid="dropzone"
            onClick={() => fileRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={e => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files) }}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer text-sm transition-colors ${dragging ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300' : 'border-zinc-700 text-zinc-500 hover:border-zinc-500'}`}
          >
            {dragging ? 'Drop to add images' : 'Drag & drop images here, or click to browse — select multiple for batch prediction'}
          </div>
          <input ref={fileRef} type="file" accept="image/*" multiple className="hidden"
            data-testid="file-input" onChange={e => addFiles(e.target.files)} />

          {/* Selected tiles */}
          {pending.length > 0 && (
            <div className="mt-3">
              <div className="text-xs text-zinc-500 mb-2">{pending.length} image(s) selected</div>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="pending-tiles">
                {pending.map((p, i) => (
                  <div key={i} className="relative group">
                    <img src={p.url} alt={p.file.name} className="w-full h-24 object-cover rounded border border-zinc-700" />
                    <button onClick={(e) => { e.stopPropagation(); removePending(i) }}
                      className="absolute top-1 right-1 w-5 h-5 rounded-full bg-zinc-950/80 text-zinc-300 text-xs leading-none hover:bg-red-800">✕</button>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex gap-3 items-center">
                <label className="text-xs text-zinc-500">Chainage (m)
                  <input value={chainage} onChange={e => setChainage(e.target.value)} data-testid="chainage-input"
                    className="ml-2 w-28 bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm font-mono" />
                </label>
                <button onClick={runBatch} disabled={processing} data-testid="inspect-button"
                  className="px-4 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-sm font-semibold">
                  {processing ? 'Running...' : `Run Inspection (${pending.length})`}
                </button>
              </div>
            </div>
          )}

          {/* Batch result tiles */}
          {batch.length > 0 && (
            <div className="mt-4">
              <div className="text-xs text-zinc-500 mb-2">Results — {batch.length} inspected</div>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="batch-tiles">
                {batch.map((r, i) => (
                  <div key={i} className={`border rounded p-2 bg-zinc-950 ${LEVEL_COLOR[r.risk?.level] || 'border-zinc-700'}`}>
                    <img src={pending[i]?.url} alt="" className="w-full h-20 object-cover rounded" />
                    <div className="text-xs mt-1 font-mono">{r.known_defect?.type} {(r.known_defect?.confidence * 100).toFixed(0)}%</div>
                    <div className="text-xs font-mono">risk {r.risk?.risk} {r.risk?.level}</div>
                    <div className="text-[10px] text-zinc-500">{r.status} · {r.asset_id}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Past predictions — tiles from /inspections */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Past Predictions <span className="text-zinc-500 text-sm">{past.length} stored · newest first</span></h2>
          {past.length === 0 ? (
            <div className="text-sm text-zinc-500 py-4" data-testid="past-empty">No predictions yet — inspect some images above.</div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="past-tiles">
              {past.map(r => (
                <div key={r.image} data-testid="past-tile" className={`border rounded p-2 bg-zinc-950 ${LEVEL_COLOR[r.risk?.level] || 'border-zinc-700'}`}>
                  <img src={`${API}/image/${encodeURI(r.image)}`} alt="" loading="lazy"
                    className="w-full h-20 object-cover rounded" data-testid="past-img" />
                  <div className="text-xs mt-1 font-mono">{r.known_defect?.type} {r.known_defect ? `${(r.known_defect.confidence * 100).toFixed(0)}%` : ''}</div>
                  <div className="text-xs font-mono">risk {r.risk?.risk} {r.risk?.level}</div>
                  <div className="text-[10px] text-zinc-500 truncate" title={r.image}>{r.created_at} · {r.asset_id}</div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Queue — live from /queue */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Maintenance Queue <span className="text-zinc-500 text-sm">sorted by R = w1S+…</span></h2>
          {assets.length === 0 ? (
            <div className="text-sm text-zinc-500 py-4" data-testid="queue-empty">No inspections yet — upload an image above.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-zinc-500"><tr><th className="text-left py-1">#</th><th className="text-left">Asset</th><th className="text-left">Chainage</th><th className="text-left">Defect</th><th className="text-left">Risk</th><th className="text-left">Level</th></tr></thead>
              <tbody className="font-mono">
                {assets.map(a => (
                  <tr key={a.asset_id + a.image} className="border-t border-zinc-800">
                    <td className="py-2">{a.priority}</td>
                    <td>{a.asset_id}</td>
                    <td>{a.chainage_m}</td>
                    <td>{a.known_defect?.type}</td>
                    <td>{a.risk?.risk}</td>
                    <td className={a.risk?.level === 'CRITICAL' ? 'text-red-400' : a.risk?.level === 'HIGH' ? 'text-orange-400' : ''}>{a.risk?.level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="text-xs text-zinc-600">
          Frontend: React 18 + Vite 5 + Tailwind + Axios. API: POST /inspections (batch), GET /inspections, GET /image, GET /queue, GET /stats. Temporal gated.
        </section>
      </main>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function App() {
  const [health, setHealth] = useState(null)
  const [assets, setAssets] = useState([])
  const [stats, setStats] = useState({ inspected: 0, normal: 0, suspicious: 0, high_risk: 0, critical: 0 })
  const [result, setResult] = useState(null)
  const [processing, setProcessing] = useState(false)
  const [chainage, setChainage] = useState('124320')
  const fileRef = useRef(null)

  const refresh = () => {
    axios.get(`${API}/queue`).then(r => Array.isArray(r.data) && setAssets(r.data)).catch(() => {})
    axios.get(`${API}/stats`).then(r => setStats(r.data)).catch(() => {})
  }

  useEffect(() => {
    axios.get(`${API}/health`).then(r => setHealth(r.data)).catch(() => setHealth({ status: 'offline' }))
    refresh()
  }, [])

  const runInspection = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file) { alert('Select an image first'); return }
    setProcessing(true); setResult(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('chainage', chainage || '124320')
    fd.append('track', 'UP')
    fd.append('line', 'LINE-01')
    try {
      const r = await axios.post(`${API}/inspections`, fd)
      setResult(r.data)
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

        {/* Inspect — upload image, run pipeline */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Inspect Image <span className="text-zinc-500 text-sm">YOLO → fusion → severity → risk</span></h2>
          <div className="flex flex-wrap gap-3 items-center">
            <input ref={fileRef} type="file" accept="image/*" data-testid="file-input"
              className="text-sm file:mr-3 file:px-3 file:py-1 file:rounded file:border-0 file:bg-zinc-800 file:text-zinc-200" />
            <label className="text-xs text-zinc-500">Chainage (m)
              <input value={chainage} onChange={e => setChainage(e.target.value)} data-testid="chainage-input"
                className="ml-2 w-28 bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm font-mono" />
            </label>
            <button onClick={runInspection} disabled={processing} data-testid="inspect-button"
              className="px-4 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-sm font-semibold">
              {processing ? 'Running...' : 'Run Inspection'}
            </button>
          </div>

          {result && (
            <div className="mt-4 border border-zinc-700 rounded p-4 grid md:grid-cols-2 gap-4" data-testid="result-card">
              <div className="text-sm space-y-1">
                <div className="text-xs text-zinc-500">Asset {result.asset_id} · KM {result.chainage_m} · {result.line_id}/{result.track_id}</div>
                <div>Defect: <span className="font-mono">{result.known_defect.type}</span> ({(result.known_defect.confidence * 100).toFixed(1)}%)</div>
                <div>Anomaly (heuristic): <span className="font-mono">{result.anomaly}</span></div>
                <div>Status: <span className={`px-2 py-0.5 rounded text-xs ${result.status === 'KNOWN_DEFECT' ? 'bg-red-900 text-red-100' : result.status === 'UNKNOWN_ABNORMALITY' ? 'bg-yellow-900 text-yellow-100' : 'bg-emerald-900 text-emerald-100'}`}>{result.status}</span></div>
                <div>Severity: <span className="font-mono">{result.severity.severity}</span> {result.severity.level}</div>
                <div>Risk: <span className="font-mono">{result.risk.risk}</span>/100 {result.risk.level}</div>
                <div className="text-xs text-zinc-400">Recommendation: {result.risk.recommendation}</div>
              </div>
              <div className="text-xs font-mono text-zinc-500">
                Contributors — severity: {Object.entries(result.severity.contributors).map(([k, v]) => `${k} ${v}`).join(', ')}
                <br />risk: {Object.entries(result.risk.contributors).map(([k, v]) => `${k} ${v}`).join(', ')}
              </div>
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
          Frontend: React 18 + Vite 5 + Tailwind + Axios. API: POST /inspections, GET /queue, GET /stats (see docs/architecture/dashboard.md). Temporal gated.
        </section>
      </main>
    </div>
  )
}

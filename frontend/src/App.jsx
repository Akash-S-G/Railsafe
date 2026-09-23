import { useEffect, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function App() {
  const [health, setHealth] = useState(null)
  const [assets] = useState([
    { id: 'FASTENER-001821', km: '124+320', risk: 86, level: 'CRITICAL', anomaly: 0.82, trend: '↑ RAPID' },
    { id: 'RAIL-000341', km: '12.43', risk: 91, level: 'CRITICAL', anomaly: 0.91, trend: '→ STABLE' },
    { id: 'FISHPLATE-00012', km: '18.77', risk: 76, level: 'HIGH', anomaly: 0.71, trend: '↑ SLOW' },
  ])

  useEffect(() => {
    axios.get(`${API}/health`).then(r => setHealth(r.data)).catch(() => setHealth({ status: 'offline', version: 'v1' }))
  }, [])

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold tracking-tight">RAILSAFE <span className="text-zinc-500 font-normal">Railway Infrastructure Health</span></h1>
        <span className={`text-xs px-2 py-1 rounded ${health?.status==='ok' ? 'bg-emerald-900 text-emerald-200' : 'bg-zinc-800 text-zinc-400'}`}>
          API {health?.status || 'checking...'} {health?.version || ''} {health?.temporal || ''}
        </span>
      </header>

      <main className="max-w-6xl mx-auto p-6 grid gap-6">
        {/* KPIs */}
        <section className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            ['Inspected','12,450'],['Normal','11,930'],['Suspicious','382'],['High Risk','104'],['Critical','34']
          ].map(([k,v])=>(
            <div key={k} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
              <div className="text-xs text-zinc-500">{k}</div>
              <div className="text-2xl font-mono">{v}</div>
            </div>
          ))}
        </section>

        {/* Map placeholder */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 h-[340px] flex flex-col">
          <h2 className="font-semibold mb-2">Railway Map <span className="text-zinc-500 text-sm">Leaflet — risk-colored pins (LOW 🟢 MEDIUM 🟡 HIGH 🟠 CRITICAL 🔴)</span></h2>
          <div className="flex-1 border border-dashed border-zinc-700 rounded flex items-center justify-center text-zinc-500 text-sm">
            Leaflet map renders here — filter by risk / component / line+chainage. Backend GET /assets?line=&chainage_from=&chainage_to
          </div>
          <div className="mt-3 flex gap-2 text-xs">
            {assets.map(a=>(
              <span key={a.id} className={`px-2 py-1 rounded ${a.level==='CRITICAL'?'bg-red-900 text-red-100': a.level==='HIGH'?'bg-orange-900 text-orange-100':'bg-zinc-800'}`}>
                {a.id} KM{a.km} {a.risk}
              </span>
            ))}
          </div>
        </section>

        {/* Queue */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="font-semibold mb-3">Maintenance Queue <span className="text-zinc-500 text-sm">sorted by R = w1S+…</span></h2>
          <table className="w-full text-sm">
            <thead className="text-zinc-500"><tr><th className="text-left py-1">Priority</th><th className="text-left">Component</th><th className="text-left">KM</th><th className="text-left">Risk</th><th className="text-left">Level</th></tr></thead>
            <tbody className="font-mono">
              {assets.map((a,i)=>(
                <tr key={a.id} className="border-t border-zinc-800"><td className="py-2">{i+1}</td><td>{a.id}</td><td>{a.km}</td><td>{a.risk}</td><td>{a.level}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="mt-2 text-xs text-zinc-500">Backend: GET /assets?chainage_from=... Phase 8 PostGIS. Temporal gated.</div>
        </section>

        <section className="text-xs text-zinc-600">
          Frontend: React 18 + Vite 5 + Tailwind + Leaflet + Recharts + Axios. See docs/architecture/dashboard.md.
        </section>
      </main>
    </div>
  )
}

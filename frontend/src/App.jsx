import { useEffect, useMemo, useRef, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

const LEVEL_COLOR = {
  CRITICAL: 'text-red-400 border-red-800',
  HIGH: 'text-orange-400 border-orange-800',
  MEDIUM: 'text-yellow-400 border-yellow-800',
  LOW: 'text-emerald-400 border-emerald-800',
}

const NAV = [
  ['overview', 'Overview'],
  ['inspect', 'Inspect'],
  ['history', 'History'],
  ['assets', 'Assets'],
  ['queue', 'Queue'],
  ['analytics', 'Analytics'],
  ['system', 'System'],
]

const STAGE_LABEL = ['1 Input', '2 Detection', '3 Anomaly', '4 Fusion', '5 Severity', '6 Risk', '7 Asset']
const WORKFLOW = ['OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED']

// ---------- theme ----------
function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('railsafe-theme') || 'dark')
  useEffect(() => {
    localStorage.setItem('railsafe-theme', theme)
  }, [theme])
  const dark = theme === 'dark'
  const th = {
    dark,
    root: dark ? 'bg-zinc-950 text-zinc-100' : 'bg-zinc-100 text-zinc-900',
    header: dark ? 'border-zinc-800' : 'border-zinc-200 bg-white',
    card: dark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm',
    inner: dark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200',
    muted: dark ? 'text-zinc-500' : 'text-zinc-500',
    subtext: dark ? 'text-zinc-400' : 'text-zinc-600',
    input: dark ? 'bg-zinc-800 border-zinc-700 text-zinc-100' : 'bg-white border-zinc-300 text-zinc-900',
    sideActive: dark ? 'bg-emerald-900/60 text-emerald-200' : 'bg-emerald-100 text-emerald-900',
    sideIdle: dark ? 'text-zinc-400 hover:bg-zinc-900' : 'text-zinc-600 hover:bg-white',
    tableHead: dark ? 'text-zinc-500' : 'text-zinc-500',
    tableRow: dark ? 'border-zinc-800 hover:bg-zinc-900' : 'border-zinc-200 hover:bg-zinc-50',
  }
  return { theme, setTheme, th }
}

// ---------- small widgets ----------
function Bar({ v, max = 1, color = 'bg-emerald-500' }) {
  const pct = Math.max(0, Math.min(100, (v / max) * 100))
  return (
    <div className="h-1.5 rounded bg-zinc-800 overflow-hidden" style={{ background: 'rgba(127,127,127,.25)' }}>
      <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

function BBoxView({ src, result }) {
  const bbox = result?.bbox
  const isMock = !bbox || (bbox[0] === 0 && bbox[1] === 0)
  return (
    <div className="relative rounded overflow-hidden border border-zinc-700" data-testid="bbox-view">
      {src ? <img src={src} alt="" className="w-full h-44 object-cover" /> : <div className="w-full h-44 bg-zinc-800" />}
      <div className="absolute border-2 border-emerald-400 rounded" style={{ inset: '4%' }} data-testid="bbox-box">
        <span className="absolute -top-5 left-0 text-[10px] font-mono bg-emerald-500 text-zinc-950 px-1 rounded">
          {result?.component_type || 'rail'} {(result?.known_defect?.confidence * 100 || 0).toFixed(0)}%
        </span>
      </div>
      {isMock && <div className="absolute bottom-1 left-1 text-[10px] font-mono bg-zinc-950/80 px-1 rounded text-zinc-400">full-frame box (mock — RFDD det pending)</div>}
    </div>
  )
}

function HeatmapView({ src, result }) {
  const hm = result?.heatmap_path
  return (
    <div className="rounded overflow-hidden border border-zinc-700" data-testid="heatmap-view">
      {hm ? (
        <img src={`${API}/image/${encodeURI(hm)}`} alt="heatmap" className="w-full h-44 object-cover" />
      ) : (
        <div className="relative w-full h-44" title="RailSense heatmap placeholder">
          {src && <img src={src} alt="" className="absolute inset-0 w-full h-full object-cover opacity-60" />}
          <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at 50% 60%, rgba(239,68,68,.55), rgba(239,68,68,0) 60%)' }} />
          <div className="absolute bottom-1 left-1 text-[10px] font-mono bg-zinc-950/80 px-1 rounded text-zinc-400">
            heatmap unavailable — RailSense TF not wired (heuristic A={result?.anomaly ?? '?'})
          </div>
        </div>
      )}
    </div>
  )
}

function PipelineDetail({ result, imgSrc, onClose, th }) {
  if (!result) return null
  const sev = result.severity || {}
  const risk = result.risk || {}
  const sevC = sev.contributors || {}
  const riskC = risk.contributors || {}
  const fusionWhy = result.status === 'KNOWN_DEFECT'
    ? `known conf ${(result.known_defect?.confidence ?? 0).toFixed(2)} ≥ 0.5 → KNOWN_DEFECT`
    : result.status === 'UNKNOWN_ABNORMALITY'
      ? `known conf low, anomaly ${(result.anomaly ?? 0).toFixed(2)} ≥ 0.5 → UNKNOWN_ABNORMALITY`
      : `both below 0.5 → NORMAL`
  return (
    <section className={`${th.card} border border-emerald-800 rounded-lg p-4`} data-testid="pipeline-detail" id="pipeline">
      <div className="flex justify-between items-center mb-3">
        <h2 className="font-semibold">Pipeline stages <span className={`${th.muted} text-sm font-normal`}>{result.asset_id} · {result.status}</span></h2>
        <button onClick={onClose} className="text-xs px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200" data-testid="pipeline-close">Close ✕</button>
      </div>
      <div className="flex gap-1 mb-3 flex-wrap">
        {STAGE_LABEL.map(s => <span key={s} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">{s}</span>)}
      </div>
      <div className="grid md:grid-cols-3 gap-3 text-sm">
        <div className={`${th.inner} border rounded p-2`}>
          <div className={`text-xs ${th.muted} mb-1`}>2 · Detection (YOLO bbox)</div>
          <BBoxView src={imgSrc} result={result} />
          <div className="text-xs font-mono mt-1">{result.known_defect?.type} {(result.known_defect?.confidence != null) ? `${(result.known_defect.confidence * 100).toFixed(1)}%` : ''}</div>
          <div className={`text-[10px] ${th.muted} font-mono`}>bbox [{(result.bbox || []).join(', ')}]</div>
        </div>
        <div className={`${th.inner} border rounded p-2`}>
          <div className={`text-xs ${th.muted} mb-1`}>3 · Anomaly (RailSense)</div>
          <HeatmapView src={imgSrc} result={result} />
          <div className="text-xs font-mono mt-1">A = {result.anomaly ?? '—'}</div>
          <Bar v={result.anomaly || 0} color="bg-red-500" />
        </div>
        <div className={`${th.inner} border rounded p-2`}>
          <div className={`text-xs ${th.muted} mb-1`}>4 · Fusion</div>
          <div className="text-xs font-mono px-1.5 py-0.5 rounded inline-block bg-zinc-800 text-zinc-200" data-testid="fusion-status">{result.status}</div>
          <div className={`text-[11px] ${th.subtext} mt-1`}>{fusionWhy}</div>
          <div className={`text-xs ${th.muted} mt-2 mb-1`}>6 · Condition Ct=[A,D,S,L,Q]</div>
          <div className="text-[11px] font-mono">A={result.anomaly} D={result.known_defect?.type} S={sev.severity} L={result.chainage_m} Q={sev.level}</div>
        </div>
        <div className={`${th.inner} border rounded p-2`}>
          <div className={`text-xs ${th.muted} mb-1`}>5 · Severity S=w1D+w2A+w3G+w4C → {sev.severity} {sev.level}</div>
          {Object.entries(sevC).map(([k, v]) => (
            <div key={k} className="mb-1"><div className="flex justify-between text-[11px] font-mono"><span>{k}</span><span>{v}</span></div><Bar v={v} max={0.4} color="bg-orange-500" /></div>
          ))}
        </div>
        <div className={`${th.inner} border rounded p-2`}>
          <div className={`text-xs ${th.muted} mb-1`}>6 · Risk R → {risk.risk} {risk.level}</div>
          {Object.entries(riskC).map(([k, v]) => (
            <div key={k} className="mb-1"><div className="flex justify-between text-[11px] font-mono"><span>{k}</span><span>{v}</span></div><Bar v={v} max={40} color="bg-red-500" /></div>
          ))}
          <div className="text-[11px] text-emerald-500 mt-1">{risk.recommendation}</div>
        </div>
        <div className={`${th.inner} border rounded p-2`}>
          <div className={`text-xs ${th.muted} mb-1`}>7 · Asset + input</div>
          <div className="text-[11px] font-mono">asset {result.asset_id}</div>
          <div className="text-[11px] font-mono">chainage {result.chainage_m} · track {result.track_id} · line {result.line_id}</div>
          <div className="text-[11px] font-mono">priority {result.priority ?? '—'} · {result.created_at ?? ''}</div>
          <div className={`text-[10px] ${th.muted} mt-1`}>1 · Input image + GPS/chainage → chainage-window asset match (v1). Temporal gated.</div>
        </div>
      </div>
    </section>
  )
}

function DistBars({ title, entries, th }) {
  const max = Math.max(1, ...entries.map(([, v]) => v))
  return (
    <div className={`${th.card} border rounded-lg p-4`}>
      <h3 className="font-semibold text-sm mb-2">{title}</h3>
      {entries.length === 0 && <div className={`text-xs ${th.muted}`}>No data yet.</div>}
      {entries.map(([k, v]) => (
        <div key={k} className="mb-1.5">
          <div className="flex justify-between text-xs font-mono"><span>{k}</span><span>{v}</span></div>
          <Bar v={v} max={max} color="bg-emerald-500" />
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const { theme, setTheme, th } = useTheme()
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState({ inspected: 0, normal: 0, suspicious: 0, high_risk: 0, critical: 0 })
  const [assets, setAssets] = useState([])
  const [past, setPast] = useState([])
  const [pending, setPending] = useState([])
  const [batch, setBatch] = useState([])
  const [processing, setProcessing] = useState(false)
  const [chainage, setChainage] = useState('124320')
  const [track, setTrack] = useState('UP')
  const [line, setLine] = useState('LINE-01')
  const [dragging, setDragging] = useState(false)
  const [selected, setSelected] = useState(null)
  // monitoring ops
  const [qFilter, setQFilter] = useState('ALL')
  const [qSearch, setQSearch] = useState('')
  const [hDefect, setHDefect] = useState('ALL')
  const [hLevel, setHLevel] = useState('ALL')
  const [hSearch, setHSearch] = useState('')
  const [ops, setOps] = useState(() => { try { return JSON.parse(localStorage.getItem('railsafe-ops') || '{}') } catch { return {} } })
  const fileRef = useRef(null)

  const refresh = () => {
    axios.get(`${API}/queue`).then(r => Array.isArray(r.data) && setAssets(r.data)).catch(() => {})
    axios.get(`${API}/stats`).then(r => setStats(r.data)).catch(() => {})
    axios.get(`${API}/inspections`).then(r => Array.isArray(r.data) && setPast(r.data)).catch(() => {})
  }

  useEffect(() => {
    axios.get(`${API}/health`).then(r => setHealth(r.data)).catch(() => setHealth({ status: 'offline' }))
    refresh()
    const t = setInterval(refresh, 15000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => { localStorage.setItem('railsafe-ops', JSON.stringify(ops)) }, [ops])

  const addFiles = (fileList) => {
    const arr = Array.from(fileList || []).filter(f => f.type.startsWith('image/'))
    setPending(p => [...p, ...arr.map(f => ({ file: f, url: URL.createObjectURL(f) }))])
  }
  const removePending = (i) => setPending(p => p.filter((_, j) => j !== i))
  const clearPending = () => setPending([])

  const runBatch = async () => {
    if (!pending.length || processing) return
    setProcessing(true); setBatch([])
    const fd = new FormData()
    pending.forEach(p => fd.append('files', p.file))
    fd.append('chainage', chainage || '124320')
    fd.append('track', track || 'UP')
    fd.append('line', line || 'LINE-01')
    try {
      const r = await axios.post(`${API}/inspections`, fd)
      const arr = Array.isArray(r.data) ? r.data : [r.data]
      const withPrev = arr.map((x, i) => ({ ...x, _pendingUrl: pending[i]?.url }))
      setBatch(withPrev)
      setSelected(withPrev.length ? { result: withPrev[0], imgSrc: withPrev[0]._pendingUrl } : null)
      setPending([])
      refresh()
    } catch (e) {
      alert('Inspection failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setProcessing(false)
    }
  }

  const imgSrcOf = (r, i) => {
    if (r?._pendingUrl) return r._pendingUrl
    if (typeof i === 'number' && pending[i]?.url) return pending[i].url
    if (r?.image) return `${API}/image/${encodeURI(r.image)}`
    return null
  }
  const select = (r, i) => setSelected({ result: r, imgSrc: r?._pendingUrl || imgSrcOf(r, i) })
  const opKey = (r) => `${r.asset_id}__${r.image}`
  const getOp = (r) => ops[opKey(r)] || { status: 'OPEN', assignee: '' }
  const setOp = (r, patch) => setOps(o => ({ ...o, [opKey(r)]: { ...getOp(r), ...patch } }))

  const queueFiltered = useMemo(() => assets.filter(a => {
    if (qFilter !== 'ALL' && a.risk?.level !== qFilter) return false
    const op = getOp(a)
    if (qFilter === 'ALL' && false) return true
    if (['OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'].includes(qFilter) && op.status !== qFilter) return false
    if (qSearch && !(a.asset_id + (a.known_defect?.type || '') + (a.risk?.level || '')).toLowerCase().includes(qSearch.toLowerCase())) return false
    return true
  }), [assets, qFilter, qSearch, ops])

  const historyFiltered = useMemo(() => past.filter(r => {
    if (hDefect !== 'ALL' && r.known_defect?.type !== hDefect) return false
    if (hLevel !== 'ALL' && r.risk?.level !== hLevel) return false
    if (hSearch && !(r.asset_id + (r.known_defect?.type || '') + (r.image || '')).toLowerCase().includes(hSearch.toLowerCase())) return false
    return true
  }), [past, hDefect, hLevel, hSearch])

  const assetGroups = useMemo(() => {
    const m = new Map()
    for (const r of past) {
      const k = r.asset_id || 'UNKNOWN'
      if (!m.has(k)) m.set(k, { asset_id: k, count: 0, maxRisk: 0, level: 'LOW', last: '', defect: '', chainage: r.chainage_m, track: r.track_id, line: r.line_id })
      const g = m.get(k)
      g.count += 1
      if ((r.risk?.risk || 0) > g.maxRisk) { g.maxRisk = r.risk.risk; g.level = r.risk.level; g.defect = r.known_defect?.type }
      if ((r.created_at || '') > g.last) g.last = r.created_at
    }
    return [...m.values()].sort((a, b) => b.maxRisk - a.maxRisk)
  }, [past])

  const defectDist = useMemo(() => {
    const c = {}
    for (const r of past) { const k = r.known_defect?.type || 'Unknown'; c[k] = (c[k] || 0) + 1 }
    return Object.entries(c).sort((a, b) => b[1] - a[1])
  }, [past])
  const riskDist = useMemo(() => {
    const c = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
    for (const r of past) { const k = r.risk?.level; if (c[k] !== undefined) c[k] += 1 }
    return Object.entries(c)
  }, [past])

  const exportQueueCsv = () => {
    const rows = [['priority', 'asset_id', 'chainage_m', 'track', 'line', 'defect', 'risk', 'level', 'status', 'workflow', 'assignee', 'recommendation']]
    queueFiltered.forEach(a => {
      const op = getOp(a)
      rows.push([a.priority, a.asset_id, a.chainage_m, a.track_id, a.line_id, a.known_defect?.type, a.risk?.risk, a.risk?.level, a.status, op.status, op.assignee, a.risk?.recommendation])
    })
    const csv = rows.map(r => r.map(x => `"${String(x ?? '')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const el = document.createElement('a')
    el.href = url; el.download = 'railsafe-queue.csv'; el.click()
    URL.revokeObjectURL(url)
  }

  const kpis = [
    ['Inspected', stats.inspected], ['Normal', stats.normal], ['Suspicious', stats.suspicious],
    ['High Risk', stats.high_risk], ['Critical', stats.critical],
  ]
  const defectOptions = ['ALL', ...new Set(past.map(r => r.known_defect?.type).filter(Boolean))]

  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  return (
    <div className={`min-h-screen ${th.root}`}>
      <header className={`border-b ${th.header} px-4 py-3 flex flex-wrap gap-2 justify-between items-center sticky top-0 z-10 ${th.dark ? 'bg-zinc-950' : 'bg-white'}`}>
        <div>
          <h1 className="text-xl font-bold tracking-tight">RAILSAFE <span className={`${th.muted} font-normal text-sm`}>Railway Infrastructure Health · Defect Monitoring Console</span></h1>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-1 rounded ${health?.status === 'ok' ? 'bg-emerald-900 text-emerald-200' : 'bg-zinc-800 text-zinc-400'}`}>
            API {health?.status || 'checking...'} {health?.version || ''} {health?.temporal || ''}
          </span>
          <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} data-testid="theme-toggle"
            className={`text-xs px-3 py-1 rounded border ${th.dark ? 'border-zinc-700 hover:border-zinc-500' : 'border-zinc-300 hover:border-zinc-500'}`}>
            {theme === 'dark' ? '☀ Light theme' : '🌙 Dark theme'}
          </button>
          <button onClick={refresh} className="text-xs px-3 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white">↻ Refresh</button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto flex gap-6 px-4 py-6">
        {/* Sidebar */}
        <nav className="hidden md:flex flex-col gap-1 w-44 shrink-0 sticky top-20 self-start">
          {NAV.map(([id, label]) => (
            <button key={id} onClick={() => scrollTo(id)} className={`text-left text-sm px-3 py-2 rounded ${th.sideIdle} hover:opacity-100`}>
              {label}
            </button>
          ))}
          <div className={`mt-4 text-[11px] ${th.muted} px-3`}>Assets tracked<br /><span className="text-lg font-mono text-emerald-500">{assetGroups.length}</span></div>
          <div className={`text-[11px] ${th.muted} px-3`}>Queue depth<br /><span className="text-lg font-mono text-emerald-500">{assets.length}</span></div>
        </nav>

        <main className="flex-1 grid gap-6 min-w-0">
          {/* OVERVIEW */}
          <section id="overview" className="grid gap-4 scroll-mt-24">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {kpis.map(([k, v]) => (
                <div key={k} className={`${th.card} border rounded-lg p-4`}>
                  <div className={`text-xs ${th.muted}`}>{k}</div>
                  <div className="text-2xl font-mono">{v ?? 0}</div>
                </div>
              ))}
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              <DistBars title="Risk distribution (history)" entries={riskDist} th={th} />
              <DistBars title="Defects by type (history)" entries={defectDist} th={th} />
              <div className={`${th.card} border rounded-lg p-4`}>
                <h3 className="font-semibold text-sm mb-2">Operations</h3>
                <div className="grid gap-2 text-sm">
                  <button onClick={() => scrollTo('inspect')} className="px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-left">＋ New inspection (batch upload)</button>
                  <button onClick={() => scrollTo('queue')} className={`px-3 py-1.5 rounded border text-left ${th.dark ? 'border-zinc-700' : 'border-zinc-300'}`}>→ Triage maintenance queue ({assets.length})</button>
                  <button onClick={exportQueueCsv} className={`px-3 py-1.5 rounded border text-left ${th.dark ? 'border-zinc-700' : 'border-zinc-300'}`}>⤓ Export queue CSV</button>
                  <button onClick={() => scrollTo('assets')} className={`px-3 py-1.5 rounded border text-left ${th.dark ? 'border-zinc-700' : 'border-zinc-300'}`}>▦ Asset registry ({assetGroups.length} assets)</button>
                </div>
                <p className={`text-[11px] ${th.muted} mt-2`}>Temporal trends gated — single-inspection view until repeated-observation data exists.</p>
              </div>
            </div>
          </section>

          {/* INSPECT */}
          <section id="inspect" className={`${th.card} border rounded-lg p-4 scroll-mt-24`}>
            <h2 className="font-semibold mb-1">Inspect Images <span className={`${th.muted} text-sm`}>YOLO → fusion → severity → risk (batch supported)</span></h2>
            <p className={`text-xs ${th.muted} mb-3`}>Upload frames with chainage / track / line metadata. Each file becomes an observation linked to an asset.</p>
            <div
              data-testid="dropzone"
              onClick={() => fileRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={e => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files) }}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer text-sm transition-colors ${dragging ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300' : th.dark ? 'border-zinc-700 text-zinc-500 hover:border-zinc-500' : 'border-zinc-300 text-zinc-500 hover:border-zinc-500'}`}
            >
              {dragging ? 'Drop to add images' : 'Drag & drop images here, or click to browse — select multiple for batch prediction'}
            </div>
            <input ref={fileRef} type="file" accept="image/*" multiple className="hidden"
              data-testid="file-input" onChange={e => addFiles(e.target.files)} />

            {pending.length > 0 && (
              <div className="mt-3">
                <div className={`text-xs ${th.muted} mb-2`}>{pending.length} image(s) selected <button onClick={clearPending} className="underline ml-2">clear</button></div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="pending-tiles">
                  {pending.map((p, i) => (
                    <div key={i} className="relative group">
                      <img src={p.url} alt={p.file.name} className="w-full h-24 object-cover rounded border border-zinc-700" />
                      <button onClick={(e) => { e.stopPropagation(); removePending(i) }}
                        className="absolute top-1 right-1 w-5 h-5 rounded-full bg-zinc-950/80 text-zinc-300 text-xs leading-none hover:bg-red-800">✕</button>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex gap-3 items-center flex-wrap">
                  <label className={`text-xs ${th.muted}`}>Chainage (m)
                    <input value={chainage} onChange={e => setChainage(e.target.value)} data-testid="chainage-input"
                      className={`ml-2 w-28 border rounded px-2 py-1 text-sm font-mono ${th.input}`} />
                  </label>
                  <label className={`text-xs ${th.muted}`}>Track
                    <select value={track} onChange={e => setTrack(e.target.value)} className={`ml-2 border rounded px-2 py-1 text-sm ${th.input}`}>
                      <option>UP</option><option>DN</option><option>LOOP</option>
                    </select>
                  </label>
                  <label className={`text-xs ${th.muted}`}>Line
                    <select value={line} onChange={e => setLine(e.target.value)} className={`ml-2 border rounded px-2 py-1 text-sm ${th.input}`}>
                      <option>LINE-01</option><option>LINE-02</option><option>YARD</option>
                    </select>
                  </label>
                  <button onClick={runBatch} disabled={processing} data-testid="inspect-button"
                    className="px-4 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-sm font-semibold text-white">
                    {processing ? 'Running...' : `Run Inspection (${pending.length})`}
                  </button>
                </div>
              </div>
            )}

            {batch.length > 0 && (
              <div className="mt-4">
                <div className={`text-xs ${th.muted} mb-2`}>Results — {batch.length} inspected · click a tile for bbox / heatmap / severity / risk stages</div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="batch-tiles">
                  {batch.map((r, i) => (
                    <div key={i} onClick={() => select({ ...r, _pendingUrl: pending[i]?.url }, i)} className={`border rounded p-2 cursor-pointer hover:border-emerald-600 ${th.inner} ${LEVEL_COLOR[r.risk?.level] || 'border-zinc-700'}`}>
                      <img src={r._pendingUrl} alt="" className="w-full h-20 object-cover rounded" />
                      <div className="text-xs mt-1 font-mono">{r.known_defect?.type} {(r.known_defect?.confidence * 100).toFixed(0)}%</div>
                      <div className="text-xs font-mono">risk {r.risk?.risk} {r.risk?.level}</div>
                      <div className={`text-[10px] ${th.muted}`}>{r.status} · {r.asset_id}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          {selected && <PipelineDetail result={selected.result} imgSrc={selected.imgSrc} onClose={() => setSelected(null)} th={th} />}

          {/* HISTORY */}
          <section id="history" className={`${th.card} border rounded-lg p-4 scroll-mt-24`}>
            <div className="flex flex-wrap gap-2 justify-between items-center mb-3">
              <h2 className="font-semibold">Past Predictions <span className={`${th.muted} text-sm`}>{historyFiltered.length}/{past.length} stored · newest first · click tile for stages</span></h2>
              <div className="flex gap-2 text-xs">
                <select value={hDefect} onChange={e => setHDefect(e.target.value)} className={`border rounded px-2 py-1 ${th.input}`}>
                  {defectOptions.map(d => <option key={d}>{d}</option>)}
                </select>
                <select value={hLevel} onChange={e => setHLevel(e.target.value)} className={`border rounded px-2 py-1 ${th.input}`}>
                  {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(l => <option key={l}>{l}</option>)}
                </select>
                <input value={hSearch} onChange={e => setHSearch(e.target.value)} placeholder="search asset / file"
                  className={`border rounded px-2 py-1 w-40 ${th.input}`} />
              </div>
            </div>
            {historyFiltered.length === 0 ? (
              <div className={`text-sm ${th.muted} py-4`} data-testid="past-empty">No predictions yet — inspect some images above.</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="past-tiles">
                {historyFiltered.map(r => (
                  <div key={r.image} data-testid="past-tile" onClick={() => select(r)} className={`border rounded p-2 cursor-pointer hover:border-emerald-600 ${th.inner} ${LEVEL_COLOR[r.risk?.level] || 'border-zinc-700'}`}>
                    <img src={`${API}/image/${encodeURI(r.image)}`} alt="" loading="lazy"
                      className="w-full h-20 object-cover rounded" data-testid="past-img" />
                    <div className="text-xs mt-1 font-mono">{r.known_defect?.type} {r.known_defect ? `${(r.known_defect.confidence * 100).toFixed(0)}%` : ''}</div>
                    <div className="text-xs font-mono">risk {r.risk?.risk} {r.risk?.level}</div>
                    <div className={`text-[10px] ${th.muted} truncate`} title={r.image}>{r.created_at} · {r.asset_id}</div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* ASSETS */}
          <section id="assets" className={`${th.card} border rounded-lg p-4 scroll-mt-24`}>
            <h2 className="font-semibold mb-1">Asset Registry <span className={`${th.muted} text-sm`}>{assetGroups.length} components · grouped observations · worst-risk first</span></h2>
            <p className={`text-xs ${th.muted} mb-3`}>Component-centric view: each asset persists across inspections (chainage + track + line). Click an asset to filter history.</p>
            {assetGroups.length === 0 ? (
              <div className={`text-sm ${th.muted} py-4`}>No assets yet — upload inspections to populate the registry.</div>
            ) : (
              <table className="w-full text-sm">
                <thead className={th.tableHead}><tr><th className="text-left py-1">Asset</th><th className="text-left">Obs</th><th className="text-left">Worst defect</th><th className="text-left">Max risk</th><th className="text-left">Level</th><th className="text-left">Last seen</th></tr></thead>
                <tbody className="font-mono">
                  {assetGroups.map(g => (
                    <tr key={g.asset_id} onClick={() => { setHSearch(g.asset_id); scrollTo('history') }} className={`border-t cursor-pointer ${th.tableRow}`}>
                      <td className="py-2">{g.asset_id}</td>
                      <td>{g.count}</td>
                      <td>{g.defect}</td>
                      <td>{g.maxRisk}</td>
                      <td className={g.level === 'CRITICAL' ? 'text-red-500' : g.level === 'HIGH' ? 'text-orange-500' : ''}>{g.level}</td>
                      <td className="text-xs">{g.last.slice(0, 10)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          {/* QUEUE */}
          <section id="queue" className={`${th.card} border rounded-lg p-4 scroll-mt-24`}>
            <div className="flex flex-wrap gap-2 justify-between items-center mb-3">
              <h2 className="font-semibold">Maintenance Queue <span className={`${th.muted} text-sm`}>sorted by R · triage workflow · {queueFiltered.length}/{assets.length}</span></h2>
              <div className="flex gap-2 text-xs">
                <select value={qFilter} onChange={e => setQFilter(e.target.value)} className={`border rounded px-2 py-1 ${th.input}`}>
                  {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', ...WORKFLOW].map(f => <option key={f}>{f}</option>)}
                </select>
                <input value={qSearch} onChange={e => setQSearch(e.target.value)} placeholder="search asset / defect"
                  className={`border rounded px-2 py-1 w-40 ${th.input}`} />
                <button onClick={exportQueueCsv} className="px-3 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white">⤓ CSV</button>
              </div>
            </div>
            {queueFiltered.length === 0 ? (
              <div className={`text-sm ${th.muted} py-4`} data-testid="queue-empty">No inspections yet — upload an image above.</div>
            ) : (
              <table className="w-full text-sm">
                <thead className={th.tableHead}><tr><th className="text-left py-1">#</th><th className="text-left">Asset</th><th className="text-left">Chainage</th><th className="text-left">Defect</th><th className="text-left">Risk</th><th className="text-left">Level</th><th className="text-left">Workflow</th><th className="text-left">Assignee</th></tr></thead>
                <tbody className="font-mono">
                  {queueFiltered.map(a => {
                    const op = getOp(a)
                    return (
                      <tr key={a.asset_id + a.image} className={`border-t ${th.tableRow}`}>
                        <td className="py-2" onClick={() => select(a)}>{a.priority}</td>
                        <td onClick={() => select(a)} className="cursor-pointer">{a.asset_id}</td>
                        <td>{a.chainage_m}</td>
                        <td>{a.known_defect?.type}</td>
                        <td>{a.risk?.risk}</td>
                        <td className={a.risk?.level === 'CRITICAL' ? 'text-red-500' : a.risk?.level === 'HIGH' ? 'text-orange-500' : ''}>{a.risk?.level}</td>
                        <td>
                          <select value={op.status} onChange={e => setOp(a, { status: e.target.value })}
                            className={`border rounded px-1 py-0.5 text-xs ${th.input}`}>
                            {WORKFLOW.map(w => <option key={w}>{w}</option>)}
                          </select>
                        </td>
                        <td>
                          <input value={op.assignee} onChange={e => setOp(a, { assignee: e.target.value })} placeholder="crew"
                            className={`border rounded px-1 py-0.5 text-xs w-20 ${th.input}`} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
            <p className={`text-[11px] ${th.muted} mt-2`}>Workflow state stored locally (browser). Wire to backend `PATCH /queue` when multi-user dispatch is needed.</p>
          </section>

          {/* ANALYTICS */}
          <section id="analytics" className="grid md:grid-cols-2 gap-4 scroll-mt-24">
            <DistBars title="Analytics · defects by type" entries={defectDist} th={th} />
            <DistBars title="Analytics · observations by risk level" entries={riskDist} th={th} />
          </section>

          {/* SYSTEM */}
          <section id="system" className={`${th.card} border rounded-lg p-4 scroll-mt-24`}>
            <h2 className="font-semibold mb-2">System</h2>
            <div className="grid md:grid-cols-3 gap-3 text-xs font-mono">
              <div className={`${th.inner} border rounded p-2`}>API: {API}<br />health: {health?.status} {health?.version}<br />temporal: {health?.temporal}</div>
              <div className={`${th.inner} border rounded p-2`}>Model: YOLO-cls multiclass<br />Anomaly: RailSense (heuristic stand-in)<br />Severity/Risk: prototype weights</div>
              <div className={`${th.inner} border rounded p-2`}>Theme: {theme}<br />Endpoints: POST /inspections, GET /queue /stats /inspections /image<br />Storage: pipeline JSON + uploads</div>
            </div>
          </section>

          <section className={`text-xs ${th.muted}`}>
            RailSafe monitoring console: React 18 + Vite 5 + Tailwind + Axios. Temporal gated. Workflow state is local-only until backend dispatch lands.
          </section>
        </main>
      </div>
    </div>
  )
}

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../App.jsx'

// Mock axios: route by URL
vi.mock('axios', () => ({
  default: {
    get: vi.fn((url) => {
      if (url.includes('/stats')) return Promise.resolve({ data: { inspected: 3, normal: 0, suspicious: 0, known_defects: 3, high_risk: 2, critical: 1 } })
      if (url.includes('/queue')) return Promise.resolve({ data: [
        { asset_id: 'RAIL-13000-UP', chainage_m: 13000, known_defect: { type: 'Squats' }, risk: { risk: 69.9, level: 'HIGH' }, anomaly: 0.85, status: 'KNOWN_DEFECT', priority: 1, image: 'a.jpg' },
        { asset_id: 'RAIL-124320.0-UP', chainage_m: 124320, known_defect: { type: 'Flakings' }, risk: { risk: 58.5, level: 'HIGH' }, anomaly: 0.45, status: 'KNOWN_DEFECT', priority: 2, image: 'b.jpg' },
      ] })
      return Promise.resolve({ data: { status: 'ok', version: 'v1', temporal: 'gated' } })
    }),
    post: vi.fn(() => Promise.resolve({ data: {
      asset_id: 'RAIL-999001-UP', chainage_m: 999001, known_defect: { type: 'Squats', confidence: 0.99 },
      anomaly: 0.85, status: 'KNOWN_DEFECT',
      severity: { severity: 0.774, level: 'CRITICAL', contributors: { D: 0.24, A: 0.297, G: 0.046, C: 0.19 } },
      risk: { risk: 69.9, level: 'HIGH', recommendation: 'PRIORITY INSPECTION', contributors: { S: 31, C: 23.8, A: 6.2, L: 9 } },
    } })),
  },
}))

describe('RailSafe Dashboard (claims per docs/architecture/dashboard.md)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders header with Railway Infrastructure Health', async () => {
    render(<App />)
    expect(screen.getByText(/RAILSAFE/)).toBeInTheDocument()
    expect(screen.getByText(/Railway Infrastructure Health/)).toBeInTheDocument()
  })

  it('shows live KPI cards from /stats (not synthetic)', async () => {
    render(<App />)
    expect(screen.getByText('Inspected')).toBeInTheDocument()
    expect(screen.getByText('Critical')).toBeInTheDocument()
    expect(await screen.findByText('3')).toBeInTheDocument() // inspected count from mocked /stats
  })

  it('shows inspect panel with file input and Run Inspection button', () => {
    render(<App />)
    expect(screen.getByTestId('file-input')).toBeInTheDocument()
    expect(screen.getByTestId('inspect-button')).toBeInTheDocument()
    expect(screen.getByText(/Inspect Image/)).toBeInTheDocument()
  })

  it('shows live maintenance queue from /queue', async () => {
    render(<App />)
    expect(screen.getByText(/Maintenance Queue/)).toBeInTheDocument()
    expect(await screen.findByText(/RAIL-13000-UP/)).toBeInTheDocument()
    expect(screen.getByText(/Squats/)).toBeInTheDocument()
  })
})

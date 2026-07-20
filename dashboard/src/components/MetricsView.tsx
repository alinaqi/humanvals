import { useEffect, useState } from 'react'
import { api } from '../api'
import type { InterventionReport } from '../types'
import { InterventionChart } from './InterventionChart'

export function MetricsView() {
  const [report, setReport] = useState<InterventionReport | null>(null)

  useEffect(() => { api.intervention().then(setReport) }, [])

  if (!report) return <div className="empty">Loading…</div>
  if (report.n === 0) {
    return <div className="empty">No evaluations yet — metrics appear after the first review.</div>
  }

  return (
    <>
      <h2>Intervention rate over time</h2>
      <p style={{ color: 'var(--text-2)', maxWidth: 640 }}>
        Share of reviewed cases needing correction, in chronological buckets.
        A declining line means the agent is learning from operator guidance —
        this is the product’s success metric.
      </p>
      <div className="card">
        <InterventionChart series={report.series} />
      </div>
      <div className="tiles" style={{ marginTop: 12 }}>
        <div className="tile">
          <div className="label">Overall intervention rate</div>
          <div className="value">{(report.overall * 100).toFixed(0)}%</div>
        </div>
        <div className="tile">
          <div className="label">Evaluations</div>
          <div className="value">{report.n}</div>
        </div>
      </div>
    </>
  )
}

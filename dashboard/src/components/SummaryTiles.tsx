import type { Summary } from '../types'

export function SummaryTiles({ summary }: { summary: Summary }) {
  const pct = (summary.intervention_rate * 100).toFixed(0)
  return (
    <div className="tiles">
      <Tile label="Cases" value={String(summary.cases)} />
      <Tile label="Awaiting review" value={String(summary.unreviewed)} />
      <Tile label="Candidate guidelines" value={String(summary.guidelines.candidate ?? 0)} />
      <Tile label="Validated guidelines" value={String(summary.guidelines.validated ?? 0)} />
      <Tile label="Intervention rate" value={`${pct}%`} />
    </div>
  )
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="tile">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  )
}

import { useState } from 'react'

const W = 640
const H = 220
const PAD = { top: 16, right: 56, bottom: 28, left: 44 }

/** Single-series line: no legend needed (title names it); direct label on the
 * last point; recessive grid; hover tooltip on nearest bucket. */
export function InterventionChart({ series }: { series: number[] }) {
  const [hover, setHover] = useState<number | null>(null)
  const iw = W - PAD.left - PAD.right
  const ih = H - PAD.top - PAD.bottom
  const x = (i: number) =>
    PAD.left + (series.length === 1 ? iw / 2 : (i / (series.length - 1)) * iw)
  const y = (v: number) => PAD.top + (1 - v) * ih
  const points = series.map((v, i) => `${x(i)},${y(v)}`).join(' ')
  const last = series.length - 1

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - rect.left) / rect.width) * W - PAD.left
    const i = Math.round((px / iw) * (series.length - 1))
    setHover(i >= 0 && i < series.length ? i : null)
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto' }}
      role="img" aria-label="Intervention rate per chronological bucket"
      onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      {[0, 0.5, 1].map(v => (
        <g key={v}>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)}
            stroke="var(--border)" strokeWidth="1" />
          <text x={PAD.left - 8} y={y(v) + 4} textAnchor="end" fontSize="11"
            fill="var(--text-2)">{v * 100}%</text>
        </g>
      ))}
      <text x={PAD.left} y={H - 6} fontSize="11" fill="var(--text-2)">older</text>
      <text x={W - PAD.right} y={H - 6} textAnchor="end" fontSize="11"
        fill="var(--text-2)">recent</text>
      <polyline points={points} fill="none" stroke="var(--accent)" strokeWidth="2"
        strokeLinejoin="round" strokeLinecap="round" />
      {series.map((v, i) => (
        <circle key={i} cx={x(i)} cy={y(v)} r={hover === i ? 5 : 3.5}
          fill="var(--accent)" stroke="var(--surface)" strokeWidth="2" />
      ))}
      <text x={x(last) + 10} y={y(series[last]) + 4} fontSize="12" fontWeight="600"
        fill="var(--text)">{(series[last] * 100).toFixed(0)}%</text>
      {hover !== null && (
        <g>
          <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={H - PAD.bottom}
            stroke="var(--text-2)" strokeWidth="1" strokeDasharray="3 3" />
          <g transform={`translate(${Math.min(x(hover) + 8, W - 130)}, ${PAD.top})`}>
            <rect width="120" height="36" rx="6" fill="var(--surface)"
              stroke="var(--border)" />
            <text x="10" y="15" fontSize="11" fill="var(--text-2)">
              bucket {hover + 1} of {series.length}
            </text>
            <text x="10" y="29" fontSize="12" fontWeight="600" fill="var(--text)">
              {(series[hover] * 100).toFixed(0)}% corrected
            </text>
          </g>
        </g>
      )}
    </svg>
  )
}

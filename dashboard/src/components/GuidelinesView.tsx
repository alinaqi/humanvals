import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { Guideline } from '../types'

export function GuidelinesView() {
  const [guidelines, setGuidelines] = useState<Guideline[]>([])
  const [changes, setChanges] = useState<[string, string, string][] | null>(null)

  const load = useCallback(() => { api.guidelines().then(setGuidelines) }, [])
  useEffect(load, [load])

  const promote = async () => {
    const r = await api.runPromotions()
    setChanges(r.changes)
    load()
  }

  return (
    <>
      <p>
        <button className="btn" onClick={promote}>Run promotions</button>
        {changes && (
          <span style={{ marginLeft: 12, color: 'var(--text-2)' }}>
            {changes.length === 0 ? 'No changes — thresholds not met yet.'
              : changes.map(([id, from, to]) => `${id}: ${from} → ${to}`).join(' · ')}
          </span>
        )}
      </p>
      <table>
        <thead>
          <tr>
            <th>Guideline</th><th>Status</th><th>Intent</th>
            <th style={{ textAlign: 'right' }}>Evidence</th>
            <th style={{ textAlign: 'right' }}>Reinforced</th>
          </tr>
        </thead>
        <tbody>
          {guidelines.map(g => (
            <tr key={g.id}>
              <td>
                {g.text}
                {g.applies_when && (
                  <div style={{ color: 'var(--text-2)', fontSize: 12 }}>
                    applies when: {g.applies_when}
                  </div>
                )}
              </td>
              <td><span className={`chip ${g.status}`}>{g.status}</span></td>
              <td style={{ color: 'var(--text-2)', fontSize: 13 }}>
                {g.intent_text.slice(0, 60)}
              </td>
              <td className="num">{g.wins}/{g.exposures}</td>
              <td className="num">×{g.validation_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {guidelines.length === 0 && (
        <div className="empty">No guidelines yet — they appear as reviewers add feedback.</div>
      )}
    </>
  )
}

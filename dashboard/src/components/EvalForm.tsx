import { useEffect, useState } from 'react'
import { api } from '../api'
import type { EvaluationBody, Guideline } from '../types'

const DIMENSIONS = [
  ['intent_ok', 'Understood the intent?'],
  ['output_ok', 'Output correct?'],
  ['context_ok', 'Right context used?']
] as const

type DimKey = (typeof DIMENSIONS)[number][0]
type Resolution = EvaluationBody['resolution']

export function EvalForm(props: { caseId: string; agent: string; onSubmitted: () => void }) {
  const [dims, setDims] = useState<Record<DimKey, boolean>>(
    { intent_ok: true, output_ok: true, context_ok: true })
  const [guideline, setGuideline] = useState('')
  const [appliesWhen, setAppliesWhen] = useState('')
  const [reviewer, setReviewer] = useState('operator')
  const [conflicts, setConflicts] = useState<Guideline[]>([])
  const [resolution, setResolution] = useState<Resolution>('add')
  const [target, setTarget] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setConflicts([]); setResolution('add'); setTarget(null); setError('')
    if (guideline.trim().length < 8) return
    const t = setTimeout(() => {
      api.conflicts(guideline, props.agent).then(setConflicts).catch(() => {})
    }, 500)
    return () => clearTimeout(t)
  }, [guideline, props.agent])

  const submit = async () => {
    setBusy(true); setError('')
    try {
      await api.evaluate(props.caseId, {
        ...dims, reviewer, notes: '', guideline_text: guideline.trim(),
        applies_when: appliesWhen.trim(), resolution, target_guideline_id: target
      })
      setGuideline(''); setAppliesWhen('')
      props.onSubmitted()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <div className="dim-row">
        {DIMENSIONS.map(([key, q]) => (
          <div className="dim" key={key}>
            <span className="q">{q}</span>
            <span className="seg">
              <button className={dims[key] ? 'on-yes' : ''}
                onClick={() => setDims({ ...dims, [key]: true })}>Yes</button>
              <button className={!dims[key] ? 'on-no' : ''}
                onClick={() => setDims({ ...dims, [key]: false })}>No</button>
            </span>
          </div>
        ))}
      </div>
      <label className="field">Guideline for the future (optional)</label>
      <textarea value={guideline} placeholder="How should the agent handle this next time?"
        onChange={e => setGuideline(e.target.value)} />
      {conflicts.length > 0 && (
        <ConflictPanel conflicts={conflicts} resolution={resolution} target={target}
          onPick={(r, t) => { setResolution(r); setTarget(t) }} />
      )}
      {(resolution === 'scope_both' || guideline) && (
        <>
          <label className="field">Applies when {resolution === 'scope_both' ? '(required)' : '(optional)'}</label>
          <input type="text" value={appliesWhen} placeholder="e.g. enterprise customers only"
            onChange={e => setAppliesWhen(e.target.value)} />
        </>
      )}
      <label className="field">Reviewer</label>
      <input type="text" value={reviewer} onChange={e => setReviewer(e.target.value)} />
      {error && <p style={{ color: 'var(--critical)' }}>{error}</p>}
      <p>
        <button className="btn" disabled={busy} onClick={submit}>Submit evaluation</button>
      </p>
    </div>
  )
}

function ConflictPanel(props: {
  conflicts: Guideline[]
  resolution: Resolution
  target: string | null
  onPick: (r: Resolution, target: string | null) => void
}) {
  return (
    <div>
      {props.conflicts.map(c => (
        <div className="conflict" key={c.id}>
          <div>Similar guideline exists: “{c.text}”</div>
          <div className="meta">
            {c.status} · reinforced ×{c.validation_count}
            {c.applies_when && ` · applies when: ${c.applies_when}`}
          </div>
          <div className="resolution-row">
            {([['add', 'Add anyway'], ['reinforce', 'Reinforce existing'],
              ['override', 'Override it'], ['scope_both', 'Scope both']] as const)
              .map(([r, label]) => (
                <button key={r}
                  className={`btn ghost${props.resolution === r && (r === 'add' || props.target === c.id) ? ' selected' : ''}`}
                  style={props.resolution === r && (r === 'add' || props.target === c.id)
                    ? { borderColor: 'var(--accent)', color: 'var(--accent)' } : {}}
                  onClick={() => props.onPick(r, r === 'add' ? null : c.id)}>
                  {label}
                </button>
              ))}
          </div>
        </div>
      ))}
    </div>
  )
}

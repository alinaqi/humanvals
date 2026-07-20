import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { Case } from '../types'
import { EvalForm } from './EvalForm'

export function ReviewView({ onChanged }: { onChanged: () => void }) {
  const [cases, setCases] = useState<Case[]>([])
  const [selected, setSelected] = useState<Case | null>(null)
  const [unreviewedOnly, setUnreviewedOnly] = useState(true)
  const [toast, setToast] = useState('')

  const load = useCallback(() => {
    api.cases(unreviewedOnly).then(cs => {
      setCases(cs)
      setSelected(prev => cs.find(c => c.id === prev?.id) ?? cs[0] ?? null)
    })
  }, [unreviewedOnly])

  useEffect(load, [load])

  const submitted = () => {
    setToast('Evaluation saved')
    setTimeout(() => setToast(''), 2500)
    load()
    onChanged()
  }

  return (
    <div className="split">
      <div>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 10 }}>
          <input type="checkbox" checked={unreviewedOnly}
            onChange={e => setUnreviewedOnly(e.target.checked)} />
          Unreviewed only
        </label>
        <div className="list">
          {cases.map(c => (
            <button key={c.id} className={c.id === selected?.id ? 'selected' : ''}
              onClick={() => setSelected(c)}>
              <div>{c.input.slice(0, 80)}</div>
              <div className="meta">
                <span>{c.agent}</span>
                <span>{c.reviewed ? 'reviewed' : 'needs review'}</span>
                <span>{c.guidelines_injected.length} injected</span>
              </div>
            </button>
          ))}
          {cases.length === 0 && <div className="empty">No cases yet</div>}
        </div>
      </div>
      <div>
        {selected ? <CaseDetail case_={selected} onSubmitted={submitted} />
          : <div className="empty">Select a case</div>}
      </div>
      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}

function CaseDetail({ case_, onSubmitted }: { case_: Case; onSubmitted: () => void }) {
  const meta = case_.metadata as {
    thought_chain?: string[]
    tool_calls?: { name?: string }[]
    context?: string
  }
  return (
    <>
      <div className="card">
        <div className="kv">INPUT</div>
        <div className="io-block mono">{case_.input}</div>
        <div className="kv">OUTPUT</div>
        <div className="io-block mono">{case_.output}</div>
        {meta.thought_chain && meta.thought_chain.length > 0 && (
          <>
            <div className="kv">THOUGHT CHAIN</div>
            <div className="io-block mono">{meta.thought_chain.join('\n')}</div>
          </>
        )}
        {meta.tool_calls && meta.tool_calls.length > 0 && (
          <>
            <div className="kv">TOOL CALLS</div>
            <div className="io-block mono">
              {meta.tool_calls.map(t => t.name ?? '?').join(', ')}
            </div>
          </>
        )}
        <div className="kv">
          GUIDELINES INJECTED: {case_.guidelines_injected.length === 0
            ? 'none' : case_.guidelines_injected.join(', ')}
        </div>
      </div>
      <EvalForm caseId={case_.id} agent={case_.agent} onSubmitted={onSubmitted} />
    </>
  )
}

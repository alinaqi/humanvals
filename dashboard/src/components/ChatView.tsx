import { useRef, useState } from 'react'
import { api } from '../api'

interface Message {
  role: 'user' | 'assistant'
  text: string
  injected?: number
  model?: string
  caseId?: string
}

export function ChatView({ onChanged }: { onChanged: () => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  const send = async () => {
    const message = input.trim()
    if (!message || busy) return
    setBusy(true); setError('')
    setMessages(m => [...m, { role: 'user', text: message }])
    setInput('')
    try {
      const r = await api.chat(message)
      setMessages(m => [...m, {
        role: 'assistant', text: r.reply,
        injected: r.guideline_ids.length, model: r.model, caseId: r.case_id
      }])
      onChanged()
      endRef.current?.scrollIntoView({ behavior: 'smooth' })
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <p style={{ color: 'var(--text-2)' }}>
        This is a live support agent wired through humanvals: every reply fetches
        matching guidelines first, and every exchange becomes a case in the Review
        tab. Ask about a refund to see learned guidance kick in.
      </p>
      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <div>{m.text}</div>
            {m.role === 'assistant' && (
              <div className="bubble-meta">
                {m.injected === 0 ? 'no guidelines injected' :
                  `${m.injected} guideline${m.injected === 1 ? '' : 's'} injected`}
                {' · '}{m.model}{' · case '}{m.caseId} — review it in the Review tab
              </div>
            )}
          </div>
        ))}
        {messages.length === 0 && (
          <div className="empty">Try: “I want a refund for my order #123, it arrived broken”</div>
        )}
        <div ref={endRef} />
      </div>
      {error && <p style={{ color: 'var(--critical)' }}>{error}</p>}
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <input type="text" value={input} placeholder="Message the support agent…"
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') void send() }} />
        <button className="btn" disabled={busy || !input.trim()} onClick={send}>
          {busy ? '…' : 'Send'}
        </button>
      </div>
    </div>
  )
}

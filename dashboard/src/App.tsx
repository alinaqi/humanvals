import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { ChatView } from './components/ChatView'
import { GuidelinesView } from './components/GuidelinesView'
import { MetricsView } from './components/MetricsView'
import { ReviewView } from './components/ReviewView'
import { SummaryTiles } from './components/SummaryTiles'
import type { Summary } from './types'

const TABS = ['Chat', 'Review', 'Guidelines', 'Metrics'] as const
type Tab = (typeof TABS)[number]

export default function App() {
  const [tab, setTab] = useState<Tab>('Review')
  const [summary, setSummary] = useState<Summary | null>(null)

  const refresh = useCallback(() => {
    api.summary().then(setSummary).catch(() => setSummary(null))
  }, [])

  useEffect(refresh, [refresh])

  return (
    <>
      <div className="topbar">
        <h1>humanvals</h1>
        <span className="sub">human feedback → verified agent memory</span>
      </div>
      {summary && <SummaryTiles summary={summary} />}
      <nav className="tabs">
        {TABS.map(t => (
          <button key={t} className={t === tab ? 'active' : ''} onClick={() => setTab(t)}>
            {t}
            {t === 'Review' && summary && summary.unreviewed > 0
              ? ` (${summary.unreviewed})` : ''}
          </button>
        ))}
      </nav>
      {tab === 'Chat' && <ChatView onChanged={refresh} />}
      {tab === 'Review' && <ReviewView onChanged={refresh} />}
      {tab === 'Guidelines' && <GuidelinesView />}
      {tab === 'Metrics' && <MetricsView />}
    </>
  )
}

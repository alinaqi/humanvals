import type { Case, EvaluationBody, Guideline, InterventionReport, Summary } from './types'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json() as Promise<T>
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body)
  })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error((detail as { detail?: string }).detail ?? r.statusText)
  }
  return r.json() as Promise<T>
}

export const api = {
  summary: () => get<Summary>('/api/summary'),
  cases: (unreviewedOnly: boolean) =>
    get<Case[]>(`/api/cases?unreviewed_only=${unreviewedOnly}`),
  case: (id: string) => get<Case>(`/api/cases/${id}`),
  evaluate: (caseId: string, body: EvaluationBody) =>
    post<{ evaluation_id: string; guideline_id: string | null }>(
      `/api/cases/${caseId}/evaluate`, body),
  conflicts: (guidelineText: string, agent: string) =>
    post<Guideline[]>('/api/conflicts', { guideline_text: guidelineText, agent }),
  guidelines: () => get<Guideline[]>('/api/guidelines'),
  chat: (message: string) =>
    post<{ reply: string; case_id: string; guideline_ids: string[]; model: string }>(
      '/api/demo/chat', { message }),
  runPromotions: () => post<{ changes: [string, string, string][] }>('/api/promotions/run'),
  intervention: () => get<InterventionReport>('/api/metrics/intervention')
}

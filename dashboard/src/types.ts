export interface Case {
  id: string
  agent: string
  namespace: string
  input: string
  output: string
  metadata: Record<string, unknown>
  guidelines_injected: string[]
  created_at: number
  reviewed: boolean
}

export interface Guideline {
  id: string
  agent: string
  namespace: string
  intent_text: string
  text: string
  applies_when: string
  origin: string
  status: 'candidate' | 'validated' | 'superseded' | 'rejected'
  kind: 'heuristic' | 'policy'
  exposures: number
  wins: number
  validation_count: number
  superseded_by: string | null
  source_case_id: string | null
  created_at: number
  promoted_at: number | null
}

export interface Summary {
  cases: number
  unreviewed: number
  guidelines: Record<string, number>
  intervention_rate: number
}

export interface InterventionReport {
  overall: number
  series: number[]
  n: number
}

export interface EvaluationBody {
  intent_ok: boolean
  output_ok: boolean
  context_ok: boolean
  tool_ok: boolean
  expected_tool_call: string
  reviewer: string
  notes: string
  guideline_text: string
  applies_when: string
  guideline_kind: 'heuristic' | 'policy'
  resolution: 'add' | 'reinforce' | 'override' | 'scope_both'
  target_guideline_id: string | null
}

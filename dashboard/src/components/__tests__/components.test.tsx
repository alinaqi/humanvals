import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Summary } from '../../types'
import { EvalForm } from '../EvalForm'
import { InterventionChart } from '../InterventionChart'
import { SummaryTiles } from '../SummaryTiles'

describe('SummaryTiles', () => {
  it('renders all five tiles with values', () => {
    const summary: Summary = {
      cases: 12, unreviewed: 3,
      guidelines: { candidate: 2, validated: 1 },
      intervention_rate: 0.25
    }
    render(<SummaryTiles summary={summary} />)
    expect(screen.getByText('Cases')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText('Validated guidelines')).toBeInTheDocument()
  })
})

describe('EvalForm', () => {
  it('renders the four evaluation dimensions', () => {
    render(<EvalForm caseId="c1" agent="bot" onSubmitted={() => {}} />)
    expect(screen.getByText('Understood the intent?')).toBeInTheDocument()
    expect(screen.getByText('Output correct?')).toBeInTheDocument()
    expect(screen.getByText('Right context used?')).toBeInTheDocument()
    expect(screen.getByText('Guideline for the future (optional)')).toBeInTheDocument()
    expect(screen.getByText('Submit evaluation')).toBeInTheDocument()
  })
})

describe('InterventionChart', () => {
  it('direct-labels the latest bucket value', () => {
    render(<InterventionChart series={[1, 0.5, 0.2]} />)
    expect(screen.getByRole('img', { name: /intervention rate/i })).toBeInTheDocument()
    expect(screen.getByText('20%')).toBeInTheDocument()
  })
})

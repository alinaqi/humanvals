import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
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
  it('renders the evaluation dimensions and guideline field', () => {
    render(<EvalForm caseId="c1" agent="bot" onSubmitted={() => {}} />)
    expect(screen.getByText('Understood the intent?')).toBeInTheDocument()
    expect(screen.getByText('Output correct?')).toBeInTheDocument()
    expect(screen.getByText('Right context used?')).toBeInTheDocument()
    expect(screen.getByText('Right tool calls?')).toBeInTheDocument()
    expect(screen.getByText('Guideline for the future (optional)')).toBeInTheDocument()
    expect(screen.getByText('Submit evaluation')).toBeInTheDocument()
  })

  it('offers the policy toggle only once a guideline is typed', async () => {
    const { fireEvent } = await import('@testing-library/react')
    render(<EvalForm caseId="c1" agent="bot" onSubmitted={() => {}} />)
    expect(screen.queryByText(/Critical policy/)).toBeNull()
    fireEvent.change(
      screen.getByPlaceholderText('How should the agent handle this next time?'),
      { target: { value: 'Always confirm the order number' } })
    expect(screen.getByText(/Critical policy/)).toBeInTheDocument()
  })

  it('asks for the correct tool call only when tool dimension is No', async () => {
    const { fireEvent } = await import('@testing-library/react')
    render(<EvalForm caseId="c1" agent="bot" onSubmitted={() => {}} />)
    expect(screen.queryByText('What should the tool call have been?')).toBeNull()
    const toolSeg = screen.getByText('Right tool calls?').parentElement!
    fireEvent.click(toolSeg.querySelectorAll('button')[1])
    expect(screen.getByText('What should the tool call have been?')).toBeInTheDocument()
  })
})

describe('ChatView', () => {
  it('sends a message and shows the injection transparency line', async () => {
    const { fireEvent, waitFor } = await import('@testing-library/react')
    const { ChatView } = await import('../ChatView')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        reply: 'Refund on the way!', case_id: 'abc123',
        guideline_ids: ['g1'], model: 'glm-5.2'
      }), { status: 200 }))
    render(<ChatView onChanged={() => {}} />)
    fireEvent.change(screen.getByPlaceholderText('Message the support agent…'),
      { target: { value: 'refund my order' } })
    fireEvent.click(screen.getByText('Send'))
    await waitFor(() => {
      expect(screen.getByText('Refund on the way!')).toBeInTheDocument()
      expect(screen.getByText(/1 guideline injected/)).toBeInTheDocument()
    })
    fetchMock.mockRestore()
  })
})

describe('InterventionChart', () => {
  it('direct-labels the latest bucket value', () => {
    render(<InterventionChart series={[1, 0.5, 0.2]} />)
    expect(screen.getByRole('img', { name: /intervention rate/i })).toBeInTheDocument()
    expect(screen.getByText('20%')).toBeInTheDocument()
  })
})

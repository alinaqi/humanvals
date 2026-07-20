# CLAUDE.md

## Skills
Read and follow these skills before writing any code:
- .claude/skills/base/SKILL.md
- .claude/skills/security/SKILL.md
- .claude/skills/python/SKILL.md
- .claude/skills/typescript/SKILL.md
- .claude/skills/react-web/SKILL.md
- .claude/skills/llm-patterns/SKILL.md
- .claude/skills/session-management/SKILL.md

## Project Overview
HumanVals — human feedback → agent memory. A library that turns human operator
evaluations of agent outputs ("cases") into retrievable guidelines, injects them
into future agent runs with a strict budget, measures each guideline's impact via
exposure logging, and promotes verified guidelines to a permanent knowledge layer.
Builds on the Engram RFC (see docs/HumanVals_RFC.md).

## Tech Stack
- Library + API: Python 3.10+ (core is stdlib-only; FastAPI server is an extra)
- Dashboard: React + TypeScript (Vite)
- Storage: SQLite (pluggable Store protocol)
- Testing: pytest (backend), Vitest (dashboard)
- Deployment: Render (render.yaml)

## Key Commands
```bash
# Backend (uses uv)
uv sync --all-extras          # install
uv run pytest                 # tests
uv run pytest --cov=humanvals # coverage
uv run ruff check .           # lint
uv run mypy                   # types
uv run uvicorn humanvals.server.app:create_app --factory --reload  # API :8000

# Dashboard
cd dashboard && npm install && npm run dev   # dev server :5173
cd dashboard && npm test && npm run build

# Examples (run without API keys — fake/test models)
uv run python examples/pydantic_ai_agent.py
uv run python examples/langgraph_agent.py
uv run python examples/crewai_agent.py
```

## Architecture (one paragraph)
Agent calls `hv.guidelines(input)` → intent lookup returns budgeted guidelines →
agent appends them to its prompt → `hv.record_case(...)` logs input/output/metadata
**including which guidelines were injected** (exposure log — the backbone).
Humans evaluate cases on 4 dimensions (intent/output/context/guideline) via the
dashboard → evaluations update guideline validation stats → `hv.run_promotions()`
promotes/demotes via Wilson-bound policy. See docs/adr/ for all decisions.

## Documentation
- `docs/HumanVals_RFC.md` — the concept RFC (part of the alinaqi RFC series)
- `docs/adr/` — architecture decision records (create one for every significant decision)
- `docs/AGENT_GUIDE.md` + `llms.txt` — docs designed for AI agents integrating the library
- `_project_specs/` — specs, todos, session state

## Atomic Todos
Tracked in `_project_specs/todos/` (active/backlog/completed). Every todo has
validation criteria and test cases (see base skill).

## Session Management
State in `_project_specs/session/` (current-state.md, decisions.md,
code-landmarks.md, archive/). Update current-state.md after each completed todo
or ~15-20 tool calls; log decisions to decisions.md; ADR for anything architectural.

## Project-Specific Patterns
- TDD non-negotiable: failing test first, then implementation
- Core library has ZERO runtime dependencies — keep it that way
- Every generation path MUST write an exposure log (guidelines_injected)
- Precision over recall in retrieval: return nothing rather than something marginal
- Never delete guidelines: supersede (status + superseded_by) for auditability

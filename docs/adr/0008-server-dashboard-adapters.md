# 0008 — API Server, Dashboard, and Framework Examples

**Status:** accepted
**Date:** 2026-07-21

## Context
Operators need a review UI; devs need to see integration with real agent
frameworks. Neither may bloat the core.

## Decision
- **Server**: FastAPI app factory `humanvals.server.app:create_app`, thin REST
  over the library (no logic in routes): cases, evaluations (with conflict
  check + resolution), guidelines, promotion trigger, metrics. Serves the
  built dashboard as static files when present.
- **Dashboard**: React+TS+Vite in `dashboard/`, talks to the REST API. Three
  views: Review queue (case detail + 5-dimension form), Guidelines (lifecycle
  states + evidence), Metrics (intervention rate over time). Neat/simple:
  system font, one accent color, no UI framework dependency beyond React.
- **Frameworks**: NO adapters package — plain examples in `examples/` showing
  the two-call integration with pydantic-ai, CrewAI, LangGraph, each runnable
  without API keys via the framework's offline/fake model. Adapters would
  imply maintenance surface for three fast-moving APIs; the integration is two
  lines and doesn't need wrapping.

## Consequences
Core remains zero-dep; examples are documentation that executes. Dashboard has
no design-system dependency to keep visuals fully under our control.

# 0001 — Project Initialization & Tech Stack

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md

## Context
HumanVals is a developer library (human feedback → verified agent memory) that
must be trivially adoptable, plus a review UI for operators.

## Decision
- Python 3.10+ library, developed on 3.12 (uv-managed) — crewai/langgraph lag on 3.14.
- Packaging: hatchling, src/ layout. Public repo: github.com/alinaqi/humanvals.
- Review server: FastAPI (optional extra `humanvals[server]`).
- Dashboard: React + TypeScript + Vite (static build served by the API in prod).
- Storage: SQLite by default (ADR-0003).
- CI-quality gates: pytest (+coverage), ruff, mypy --strict, Vitest.

## Consequences
All later work follows this stack. Deployment target is Render (render.yaml),
pending API key; everything must run fully locally without keys.

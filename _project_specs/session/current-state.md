# Current Session State

*Last updated: 2026-07-21 ~02:00 (overnight autonomous build)*

## Active Task
Task 8: full validation + visual proof (demo seed, server, screenshots, report).

## Current Status
- **Phase**: validating
- **Progress**: core lib, server, dashboard, 3 framework examples, docs all done
- **Blocking Issues**: none. Render deploy waits for API key (morning).

## Completed this session
1. Project init (own git repo, uv py3.12, skills, CLAUDE.md)
2. HumanVals RFC (docs/HumanVals_RFC.md) + 8 ADRs; council-reviewed
   (kimi K2.6 8/8; srooter-routed opus 4/8 → amendments applied to
   ADR-0002/3/6/7 + RFC §6 limitations + Q5)
3. Core library TDD: 39 tests → 53 with server/examples; 98% cov; ruff+mypy strict clean
4. FastAPI server (humanvals.server.app:create_app) + React dashboard (Vite,
   3 views, validated palette, builds clean, vitest green)
5. Examples: pydantic-ai, langgraph, crewai — all run WITHOUT API keys;
   live_agent.py uses OpenAI-compatible gateway (srooter: glm-5.2 default)
6. Docs: README (public-grade), AGENT_GUIDE.md, llms.txt, LICENSE, CI, render.yaml

## Next Steps
1. scripts/seed_demo.py — demo data w/ live glm-5.2 outputs, declining intervention curve
2. Run server :8000, playwright screenshots → docs/assets/
3. Coverage + full gates run; proof artifact for the morning
4. git commit(s) + push to github.com/alinaqi/humanvals (empty public repo confirmed)

## Key Context to Preserve
- srooter gateway: env from ~/.srooter/active.env (OPENAI_BASE_URL/KEY);
  routes by its own policy — 'kimi-k3' request may serve glm-5.2/opus
- Parent dir is the 31app git repo — humanvals/.git is separate on purpose
- Promotion math: wilson_lower(5/5)=0.5655 → promote_threshold=0.55

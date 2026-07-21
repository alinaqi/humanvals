# Project Overview

## Vision
HumanVals: the missing measurement-and-promotion loop for agent memory.
Human operators review agent outputs as "cases", their feedback becomes
retrievable guidelines, every injection is exposure-logged, and only
guidelines with verified positive impact are promoted to permanent knowledge.

## Goals
- [ ] Dead-simple dev integration: two calls (`guidelines()`, `record_case()`)
- [ ] Zero-dependency core library (stdlib only)
- [ ] 5-dimension human evaluation (intent / output / context / tool / guideline)
- [ ] Write-time contradiction + duplicate detection with human override
- [ ] Exposure-logged impact measurement, Wilson-bound promotion policy
- [ ] Works with pydantic-ai, crewai, langgraph out of the box
- [ ] Neat, simple review dashboard (React)
- [ ] Docs designed for AI agents (llms.txt, AGENT_GUIDE.md)

## Non-Goals
- Not a vector DB / embedding store product (pluggable interface instead)
- Not RLHF / model fine-tuning ("finetuned-prompt" is prompt-space only)
- Not a general memory system — guidelines only (see Engram RFC for the rest)

## Success Metrics
- Cold start to first injected guideline < 10 lines of dev code
- Intervention rate per intent cluster declines as guidelines accumulate
- 80%+ test coverage; all three example agents run without API keys

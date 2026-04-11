# DevStack — Task Tracking

> **All implementation tasks are in PLAN.md §20 (Implementation Backlog).**
>
> §20 contains 60+ tasks across 6 phases, each with file paths, spec references, and acceptance criteria.
> Use GitHub Projects, Linear, or your team's preferred tracker to manage progress.
>
> Quick links:
> - Phase 0 — Foundation (state, ports, BaseAgent): PLAN.md line ~1730
> - Phase 0 — Harness Engineering (AGENTS.md, Makefile, ADRs, hooks): PLAN.md §22h
> - Phase 1 — Adapters (vault, LLM, WebSocket): PLAN.md line ~1746
> - Phase 2 — Agents & Skills (5 agents + prompts): PLAN.md line ~1766
> - Phase 3 — Infrastructure (Terraform, CI/CD): PLAN.md line ~1785
> - Phase 4 — Frontend Dashboard (Next.js, gates): PLAN.md line ~1802
> - Phase 5 — Observability (OTel, dashboards): PLAN.md line ~1815
> - Phase 6 — Legal & Compliance: PLAN.md line ~1828
>
> **New from Harness Engineering (§22):**
> - ✅ AGENTS.md created (AI agent entry point, ~80 lines)
> - ✅ Makefile created (standard entry points: setup, test, lint, dev, ci)
> - ✅ docs/decisions/ created (5 initial ADRs extracted from PLAN.md)
> - ✅ docs/architecture.md created (codebase map + dependency graph)
> - [ ] backend/hooks/pipeline.py — Pre/post agent execution hook pipeline (Squad pattern)
> - [ ] Custom ruff rules — PgBouncer session mode, RLS parameterization, Pydantic v2
> - [ ] Builder skill update — Agent-legibility requirements for generated apps
> - [ ] CI validation — AGENTS.md + Makefile existence checks in ci.yml

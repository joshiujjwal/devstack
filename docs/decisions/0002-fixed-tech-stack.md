# ADR-0002: Fixed Tech Stack in v1

**Status:** Accepted  
**Date:** 2025 (project inception)  
**Reference:** PLAN.md §6

## Context

The #1 cause of AI hallucination in code generation is framework choice ambiguity. "Should I use React or Vue? Express or FastAPI? AWS or Azure?" Each decision doubles prompt complexity and halves code quality. Additionally, a fixed stack enables compound learning — each project improves the skills for the SAME stack.

## Decision

Fix the entire tech stack for v1. No framework choices at runtime:

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 15 (TypeScript) | Most popular React framework; largest skill training corpus |
| Backend | Python 3.12 + FastAPI | Async + automatic OpenAPI docs + Pydantic validation |
| Database | PostgreSQL + PgBouncer | RLS support (critical for multi-tenancy) |
| Infra | Terraform + Azure | ACI for ephemeral sandboxes (unique capability) |
| CI/CD | GitHub Actions | Ubiquitous, well-documented |
| LLM routing | LiteLLM + ModelRouter | Model-agnostic, YAML-configured |

## Consequences

- **Positive:** Eliminates decision hallucination — agents never waste tokens choosing frameworks.
- **Positive:** Skill quality compounds across projects (same stack every time).
- **Positive:** Predictable infrastructure costs (Azure pricing is known upfront).
- **Negative:** Cannot serve users who need Vue, Django, AWS, etc. (out of scope for v1).
- **Negative:** Stack may become dated — requires periodic re-evaluation.

## Enforcement

- Agent skill files are optimized for exactly this stack
- Architect agent generates within these constraints (no alternatives proposed)

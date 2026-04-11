# AGENTS.md — DevStack Agency

## What this project is
An autonomous 5-agent AI dev agency: Idea → Deployed Azure web app in ~3 hours for <$25.
Pipeline: Analyst → Designer → Architect → Builder → Deployer, with 5 human approval gates.

## Quick commands (available after Phase 0 implementation)
> **Note:** These commands require the backend/frontend code from PLAN.md §20 Phase 0+.
> Until then, use them as reference for what the standard entry points will be.

- Setup: `make setup` (installs Python + Node deps)
- Test backend: `pytest backend/tests/ -v --tb=short`
- Test frontend: `npx vitest run --reporter=verbose`
- Lint: `make lint` (ruff + mypy + import-linter + SkillRegistry.validate_all)
- Run locally: `DEMO_MODE=true make run`
- Full check: `make ci` (lint + test + validate skills)

## Architecture (CRITICAL — never violate)
- **Hexagonal**: agents import ONLY from `core/ports.py`, never from `adapters/`
- **5 ports**: LLMPort, VaultPort, ToolPort, HumanPort, LoggingPort
- **Anti-hallucination contract**:
  - AH-1: All LLM calls use Pydantic structured schemas (no free-form text)
  - AH-2: Tool calls before facts (no fabricated claims)
  - AH-3: Code must execute in Docker sandbox before gate (not just validate)
  - AH-4: `original_requirement` is immutable (`frozen=True`)
- **PgBouncer**: session mode ONLY (transaction mode breaks RLS — see ADR-0003)
- **RLS**: parameterized `$1` queries ONLY (never f-strings for SET LOCAL)
- **Auth before RLS**: AuthMiddleware MUST run before RLSMiddleware

## Directory map
- `backend/core/` — Ports, state, base agent (THE core — read this first)
- `backend/agents/` — 5 pipeline agents (each extends BaseAgent)
- `backend/adapters/` — LLM, vault, human implementations (swappable)
- `backend/skills/` — Markdown skill files loaded into agent context (<2,000 tokens each)
- `backend/middleware/` — Auth → RLS middleware stack (order matters!)
- `backend/hooks/` — Pre/post agent execution hooks (budget, audit, PII) *(planned — §22e)*
- `frontend/` — Next.js 15 dashboard (gate approval UI, AMC screens)
- `infra/terraform/` — Azure infrastructure-as-code
- `.github/workflows/` — CI/CD pipelines
- `docs/decisions/` — Architecture Decision Records (ADRs)
- `docs/architecture.md` — Codebase map and dependency graph
- `reference/` — Research artifacts (model-agnostic architecture, prior plans)

## Key specs (progressive disclosure — start here, go deeper as needed)

**Level 1 — Architecture overview:**
- Codebase map: `docs/architecture.md` (directory structure + dependency graph)
- Visual guide: `EXPLAIN.md` (mermaid diagrams + architecture overview)

**Level 2 — Decision rationale:**
- `docs/decisions/0001-hexagonal-architecture.md` — Why ports & adapters
- `docs/decisions/0002-fixed-tech-stack.md` — Why the stack is fixed
- `docs/decisions/0003-pgbouncer-session-mode.md` — Why session mode (not transaction)
- `docs/decisions/0004-aci-not-aca-sandbox.md` — Why ACI for sandbox
- `docs/decisions/0005-tdd-red-green-mandatory.md` — Why TDD is enforced

**Level 3 — Full specs (PLAN.md sections):**
- §1c (~line 168): Hexagonal architecture, §8 (~line 780): BaseAgent contract
- §2 (~line 240): Agent roster + skill architecture
- §4 (~line 400): LangGraph orchestrator
- §6 (~line 500): Tech stack rationale, §7 (~line 600): HITL gates
- §1b (~line 108): Anti-hallucination contract
- §20 (~line 1784): Implementation backlog (60+ tasks, 6 phases)
- §22 (~line 1945): Harness engineering practices

**For developers building this project:** See `copilot-enhance.md` for Copilot agent definitions, skill files, session hooks, and IDE configuration.

## Tech stack (fixed, non-negotiable in v1)
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (TypeScript, TailwindCSS) |
| Backend | Python 3.12 + FastAPI + Pydantic v2 |
| Database | PostgreSQL + PgBouncer (session mode) + Redis (noeviction) |
| Infra | Terraform + Azure Container Apps |
| Sandbox | Azure Container Instances (NOT ACA — ACI supports Docker-in-Docker) |
| CI/CD | GitHub Actions |
| LLM routing | LiteLLM + ModelRouter (YAML-configured, model-agnostic) |
| Observability | OpenTelemetry + Azure App Insights |

## Custom lint rules (enforced in CI — cannot be bypassed)
- `import-linter`: agents/ cannot import adapters/
- `SkillRegistry.validate_all()`: skill files must be <2,000 tokens
- `mypy --strict`: no untyped code in backend/
- `ruff`: Python formatting + style
- Structural test: AuthMiddleware registered before RLSMiddleware

## Testing rules
- Red/green TDD mandatory: write failing test BEFORE implementation
- Backend: `pytest backend/tests/ -v --tb=short`
- Frontend: `npx vitest run --reporter=verbose`
- Integration tests use MockVault + MockHumanPort + MockLLM (no Azure needed)
- Test naming: `test_{feature}_{scenario}_{expected_result}`

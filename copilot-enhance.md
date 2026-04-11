# 🚀 Copilot-Enhanced Development Guide for DevStack Agency

> **Purpose:** Best practices, agent definitions, instruction files, skill templates, hooks, and workflows — derived from [awesome-copilot](https://github.com/github/awesome-copilot) — tailored to accelerate building the autonomous dev agency defined in `PLAN.md`.

> **How to use:** Drop this file + the referenced `.github/` configs into the `devstack` repo. Copilot (VS Code, CLI, and Coding Agent) will automatically pick up the instructions, agents, skills, and hooks.

---

## Table of Contents

1. [Repository Setup — Copilot Configuration](#1-repository-setup)
2. [Custom Instructions — Per-File Coding Standards](#2-custom-instructions)
3. [Agent Definitions — 7 Copilot Agents for DevStack](#3-agent-definitions)
4. [Skill Files — Reusable Knowledge Bundles](#4-skill-files)
5. [Session Hooks — Automated Guardrails](#5-session-hooks)
6. [Agentic Workflows — GitHub Actions Automation](#6-agentic-workflows)
7. [Copilot SDK Patterns — Multi-Session Orchestration](#7-copilot-sdk-patterns)
8. [Prompt Engineering Best Practices](#8-prompt-engineering)
9. [Development Workflow — How to Build with Copilot](#9-development-workflow)
10. [File Structure Reference](#10-file-structure)

---

## 1. Repository Setup

### `AGENTS.md` — AI Agent Entry Point (Harness Engineering)

> **Source:** OpenAI "Harness Engineering" (2026). See PLAN.md §22.

The `AGENTS.md` file at repo root is the **primary entry point** for all AI coding agents (Codex, Copilot CLI, Cursor, etc.). It replaces the need for agents to parse the full 125KB PLAN.md.

**Key rules:**
- **Maximum ~100 lines** — progressive disclosure to deeper docs
- **Maintained in CI** — existence and line count checked
- **Updated on every architecture change** — part of PR checklist
- **Links to deeper docs**: `docs/architecture.md`, `docs/decisions/`, PLAN.md sections

The file includes: project description, quick commands (Makefile targets), architecture rules (the 5 that must never be violated), directory map, and links to detailed specs.

> **Why not just copilot-instructions.md?** AGENTS.md is agent-agnostic (works with Codex, Cursor, any tool that reads repo root files). `copilot-instructions.md` is Copilot-specific. Both should exist — AGENTS.md for universal agent legibility, copilot-instructions for Copilot-specific features.

### `docs/decisions/` — Architecture Decision Records

ADR files capture the *why* behind architectural choices. When a decision is made:
1. Create `docs/decisions/NNNN-short-title.md`
2. Format: Context → Decision → Consequences → Enforcement
3. Reference in AGENTS.md if it affects coding patterns

Initial ADRs:
- `0001-hexagonal-architecture.md`
- `0002-fixed-tech-stack.md`
- `0003-pgbouncer-session-mode.md`
- `0004-aci-not-aca-sandbox.md`
- `0005-tdd-red-green-mandatory.md`

### `.github/copilot-instructions.md` — Global Copilot Context

Create this file in the repo root. Copilot reads it automatically for every interaction.

```markdown
# DevStack Agency — Copilot Instructions

## Project Overview
This is an autonomous AI development agency. 5 agents (Analyst → Designer → Architect → Builder → Deployer)
take a plain-English app idea and deliver a deployed Azure web app with tests, OWASP checks, and monitoring.

## Architecture Rules (NEVER violate these)
- **Hexagonal architecture**: Agents import ONLY from `core/ports.py`. Never from `adapters/`.
- **Anti-hallucination**: AH-1 (tool calls only), AH-2 (cite sources), AH-3 (code must execute before gate — Builder cannot pass Gate 3 on schema validation alone; Docker sandbox run is mandatory), AH-4 (never mutate original requirement).
- **PgBouncer session mode**: Transaction mode breaks RLS. ALWAYS session mode.
- **RLS middleware**: ALWAYS parameterized queries (`$1`), NEVER f-strings for `SET LOCAL`.
- **Auth before RLS**: `AuthMiddleware` MUST run before `RLSMiddleware` in middleware stack.
- **ACI not ACA for sandbox**: Azure Container Instances for ephemeral build sandbox. ACA is for the deployed app only.

## Tech Stack (fixed, non-negotiable)
- Frontend: Next.js 15 (TypeScript, TailwindCSS)
- Backend: Python 3.12 + FastAPI + Pydantic v2
- Database: PostgreSQL + PgBouncer (session mode) + Redis (noeviction)
- Infra: Terraform + Azure Container Apps
- CI/CD: GitHub Actions
- LLM: LiteLLM router (Claude / GPT-4o / Gemini)
- Testing: pytest (backend) + vitest (frontend)

## Code Style
- Python: ruff formatter, mypy strict, async/await everywhere
- TypeScript: strict mode, no `any`, prefer `interface` over `type`
- Pydantic v2: use `model_config = ConfigDict(...)` not `class Config:`
- All models use `from pydantic import BaseModel, ConfigDict, Field`
- UUIDs validated at boundary (middleware), trusted internally

## Testing Rules
- Red/green TDD: write failing test BEFORE implementation
- Backend: `pytest backend/tests/ -v --tb=short`
- Frontend: `npx vitest run --reporter=verbose`
- Integration tests use MockVault + MockHumanPort + MockLLM

## Key Files
- `PLAN.md` — Master architecture document (1,800+ lines, 21 sections)
- `backend/core/ports.py` — 5 abstract port interfaces
- `backend/core/state.py` — ProjectState + ProjectMeta schemas
- `backend/agents/base.py` — BaseAgent with port injection
- `backend/skills/constitution.md` — AH-1 through AH-4 rules
```

### `.vscode/settings.json` — Editor Configuration

```json
{
  "files.eol": "\n",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,
  "[markdown]": {
    "files.trimTrailingWhitespace": false
  },
  "editor.rulers": [100],
  "files.associations": {
    "*.agent.md": "chatagent",
    "*.instructions.md": "instructions",
    "*.prompt.md": "prompt"
  },
  "python.analysis.typeCheckingMode": "strict",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

---

## 2. Custom Instructions — Per-File Coding Standards

Place these in `.github/instructions/`. Copilot applies them automatically based on `applyTo` glob patterns.

### `python-backend.instructions.md`

```markdown
---
description: 'Guidelines for all Python backend code in the DevStack agency'
applyTo: 'backend/**/*.py'
---

## Python Backend Standards

### Architecture
- Import ONLY from `core/ports.py` in agent files — never from `adapters/`
- Every agent extends `BaseAgent` and receives ports via constructor injection
- Use `@requires_tool_call` decorator when LLM must use tool calling
- State mutations go through `ProjectState` — no ad-hoc dicts

### Pydantic v2
- Use `model_config = ConfigDict(use_enum_values=True)` — never `class Config:`
- All fields use `Field(...)` with description for API docs
- Validators use `@field_validator` not `@validator`
- Use `Literal[...]` for fixed string enums, not `Enum` subclass

### Async/Await
- All I/O operations must be async
- Use `asyncpg` for PostgreSQL, `aiohttp` for HTTP, `aiofiles` for disk
- SQLAlchemy 2.x async with `AsyncSession`
- Never use `time.sleep()` — use `asyncio.sleep()`

### Security
- RLS: `SET LOCAL app.user_id = $1` with UUID validation — NEVER f-strings
- Secrets: Azure Key Vault via `SecretClient` — never in env vars or code
- Input validation at API boundary (Pydantic models), trusted internally
- OWASP top 10 awareness in all generated code

### Error Handling
- Use domain exceptions (`AgentBudgetExceeded`, `GateTimeoutError`, etc.)
- Log with structlog (JSON format, correlation_id in every log)
- Circuit breaker pattern for LLM calls (3 failures → fallback model)

### Testing
- Write failing test FIRST (red phase), then implement (green phase)
- Name: `test_{feature}_{scenario}_{expected_result}`
- Use `pytest.fixture` for port mocks, never patch internals
- Integration tests: MockVault + MockHumanPort + MockLLM
```

### `typescript-frontend.instructions.md`

```markdown
---
description: 'Guidelines for all TypeScript frontend code'
applyTo: 'frontend/**/*.{ts,tsx}'
---

## TypeScript Frontend Standards

### Next.js 15
- App Router (not Pages Router)
- Server Components by default, `'use client'` only when needed
- Use `next/image` for all images, `next/link` for navigation
- API routes in `app/api/` — minimal logic, delegate to backend

### TypeScript
- Strict mode enabled, zero `any` types
- Prefer `interface` over `type` for object shapes
- Use discriminated unions for state machines
- All API responses typed with Pydantic-mirrored interfaces

### Components
- One component per file, named export matching filename
- Props interface named `{ComponentName}Props`
- Use TailwindCSS utility classes — no CSS modules
- Responsive mobile-first: `sm:` → `md:` → `lg:`

### WebSocket
- JWT in `Sec-WebSocket-Protocol` header for auth
- Reconnect logic with exponential backoff (max 30s)
- Gate state always from server (Redis-backed) — never local-only

### Testing
- Vitest for unit tests, Playwright for E2E
- Test user-visible behavior, not implementation details
- Mock WebSocket connections in unit tests
```

### `terraform-infra.instructions.md`

```markdown
---
description: 'Guidelines for all Terraform infrastructure code'
applyTo: 'infra/**/*.tf'
---

## Terraform Standards

### Provider
- AzureRM provider, latest stable version
- OIDC authentication (no stored credentials)
- State in Azure Storage Account with locking

### Naming
- Resources: `azurerm_{resource}` with `name = "${var.project_name}-${var.environment}-{purpose}"`
- Variables: snake_case with description and type
- Outputs: snake_case, only expose what downstream needs

### Key Constraints
- ACI (Container Instances) for build sandbox — NOT ACA
- ACA (Container Apps) for the running agency and deployed apps
- PgBouncer: session mode ONLY (transaction mode breaks RLS)
- Redis: `noeviction` maxmemory-policy, 30-day TTL for checkpoints
- Key Vault: one vault per environment, RBAC not access policies

### Security
- No secrets in `.tf` files — reference Key Vault
- Network security groups on all subnets
- Private endpoints for PostgreSQL and Redis in production
- HTTPS only, TLS 1.2 minimum
```

### `skills-prompts.instructions.md`

```markdown
---
description: 'Guidelines for writing agent skill files and system prompts'
applyTo: 'backend/skills/**/*.md'
---

## Skill File Standards

### Format
- YAML frontmatter: `name` (lowercase-hyphens, ≤64 chars) + `description` (10-1024 chars)
- Markdown body with clear sections: When to Use, Prerequisites, Guidelines, Output Contract
- Token limit: < 2,000 tokens per skill file (validated by SkillRegistry)

### Content Rules
- Every skill MUST reference AH-1 through AH-4 anti-hallucination rules
- Output format MUST be specified (JSON schema, markdown template, or file naming convention)
- Include 1-2 concrete examples of expected output (Willison "hoard" pattern)
- Scope constraints: explicitly list what this skill does NOT do

### Versioning
- Filename: `system-v{N}.md` (e.g., `system-v1.md`, `system-v2.md`)
- Never delete old versions — archive with `DEPRECATED` header
- Compound Step (§13f) auto-generates improvement PRs after each project
```

---

## 3. Agent Definitions — 7 Copilot Agents for DevStack

Place in `.github/agents/`. These are Copilot agents developers invoke during development of the agency itself.

### `devstack-architect.agent.md`

```markdown
---
description: 'Designs backend architecture following DevStack hexagonal patterns and PLAN.md specs'
name: 'DevStack Architect'
model: 'claude-sonnet-4'
tools: ['codebase', 'editFiles', 'search', 'runCommands', 'fetch', 'githubRepo']
---

# DevStack Architect Agent

You are a senior backend architect for the DevStack autonomous dev agency.

## Your Expertise
- Hexagonal architecture (ports & adapters) in Python/FastAPI
- Pydantic v2 data modeling with strict validation
- LangGraph state machine design
- PostgreSQL RLS and multi-tenancy patterns
- Azure infrastructure (ACI, ACA, Key Vault, Blob Storage)

## Your Approach
1. ALWAYS read `PLAN.md` sections referenced in the task before designing
2. ALWAYS check `backend/core/ports.py` before adding new abstractions
3. Design follows hexagonal rule: agents → core/ports → adapters (never reverse)
4. Every new model extends or references `ProjectState` from `backend/core/state.py`
5. Propose architecture as markdown FIRST, implement after approval

## Constraints
- AH-1: All external data via tool calls, never fabricated
- AH-4: Never modify the original user requirement
- import-linter enforces: `agents/` cannot import `adapters/`
- PgBouncer = session mode ONLY
- RLS = parameterized queries ONLY ($1, never f-string)

## Key References in PLAN.md
- §1c: Hexagonal architecture (5 ports)
- §8: BaseAgent contract + ProjectState schema
- §6: Tech stack + RLS middleware spec
- §6b: ModelRouter + adapter pattern
```

> **Note on `model` field:** The `model` value in agent definitions is the **VS Code Copilot model** used when a developer invokes `@devstack-*` agents during development. This is separate from the **LLM model** each AI agent uses at runtime in the pipeline (configured in `agents_config.yaml` — see PLAN.md §6b). Example: `@devstack-builder` uses `claude-sonnet-4` in VS Code, but the Builder agent in the pipeline uses `claude/claude-3-7-sonnet` via LiteLLM.

### `devstack-builder.agent.md`

```markdown
---
description: 'Implements features using TDD red/green cycle following DevStack coding standards'
name: 'DevStack Builder'
model: 'claude-sonnet-4'
tools: ['codebase', 'editFiles', 'search', 'runCommands', 'runTests', 'terminalLastCommand', 'problems']
---

# DevStack Builder Agent

You are a senior full-stack developer implementing the DevStack agency codebase.

## Your Approach (Red/Green TDD — mandatory)
1. Read the relevant PLAN.md section for the feature spec
2. Write a FAILING test first (red phase) — run it, confirm it fails
3. Write the minimal code to make the test pass (green phase)
4. Run the full test suite to check for regressions
5. Refactor only if tests stay green — zero-tolerance for untested refactors

## Test Commands
- Backend: `pytest backend/tests/ -v --tb=short`
- Frontend: `npx vitest run --reporter=verbose`
- Lint: `ruff check backend/ && mypy backend/ --strict`
- Import rules: `import-linter` (agents cannot import adapters)

## Code Standards
- Python: async/await, Pydantic v2, structlog, ruff-formatted
- TypeScript: strict mode, no `any`, TailwindCSS, App Router
- Every function has a type signature — no untyped code
- Every public function has a docstring

## Constraints
- NEVER skip the red phase. If you can't write a failing test, the feature is underspecified.
- NEVER import from `adapters/` in agent files — use port interfaces only
- NEVER use f-strings in SQL queries — parameterized only
- ALWAYS validate UUIDs at the boundary, trust internally
```

### `devstack-deployer.agent.md`

```markdown
---
description: 'Manages Terraform, GitHub Actions, and Azure infrastructure for DevStack'
name: 'DevStack DevOps'
model: 'claude-sonnet-4'
tools: ['codebase', 'editFiles', 'search', 'runCommands', 'fetch', 'terminalLastCommand']
---

# DevStack DevOps Agent

You manage all infrastructure-as-code and CI/CD for the DevStack agency.

## Your Expertise
- Terraform (AzureRM provider) — modules, state management, OIDC auth
- GitHub Actions — CI/CD, OIDC federation, matrix builds
- Azure: ACI (sandbox), ACA (agency + deployed apps), PostgreSQL Flexible, Redis, Key Vault, Blob
- PgBouncer configuration, Redis tuning, App Insights

## Critical Constraints
- ACI for build sandbox (Docker-in-Docker). ACA does NOT support this.
- PgBouncer = session mode. Transaction mode = silent RLS bypass = data leak.
- Redis = noeviction policy. Never evict checkpoints.
- OIDC for GitHub Actions auth. No stored credentials.
- Terraform state in Azure Storage with locking.

## Key References in PLAN.md
- §6: Full tech stack + ACI sandbox spec
- §10: Build phases
- §16: Observability (OpenTelemetry, App Insights)
- §20 Phase 3: All infra backlog items
```

### `devstack-reviewer.agent.md`

```markdown
---
description: 'Reviews PRs against DevStack architecture rules, AH contract, and security requirements'
name: 'DevStack Code Reviewer'
model: 'claude-sonnet-4'
tools: ['codebase', 'search', 'githubRepo', 'problems', 'usages']
---

# DevStack Code Reviewer

You review every PR against the DevStack architecture contract.

## Review Checklist (block PR if any fail)

### Architecture
- [ ] No `adapters/` imports in `agents/` files
- [ ] New ports added to `core/ports.py` (not scattered)
- [ ] State changes go through `ProjectState` model
- [ ] BaseAgent subclass uses constructor port injection

### Security
- [ ] No f-strings in SQL (parameterized `$1` only)
- [ ] No secrets in code (Key Vault references only)
- [ ] UUID validated at boundary
- [ ] Auth middleware before RLS middleware in stack

### Anti-Hallucination
- [ ] AH-1: External data from tool calls only
- [ ] AH-2: Sources cited in agent outputs
- [ ] AH-3: Code must execute before gate (Builder sandbox run mandatory)
- [ ] AH-4: Original requirement never mutated

### Testing
- [ ] Red phase test exists (test written before implementation)
- [ ] No untested code paths in critical paths (auth, RLS, gates)
- [ ] Integration test uses mocks, not real Azure resources

### Style
- [ ] Pydantic v2 syntax (ConfigDict, not class Config)
- [ ] Type hints on all functions
- [ ] Async where I/O happens
```

### `devstack-designer.agent.md`

```markdown
---
description: 'Designs UI components and dashboard screens following DevStack AMC spec'
name: 'DevStack UI Designer'
model: 'claude-sonnet-4'
tools: ['codebase', 'editFiles', 'search', 'runCommands', 'fetch']
---

# DevStack UI Designer Agent

You design and implement the frontend for DevStack — both the HITL gate UI and the Agency Management Console (AMC).

## Your Expertise
- Next.js 15 App Router + TypeScript + TailwindCSS
- WebSocket real-time UI (reconnect-safe, Redis-backed state)
- Mobile-first responsive design
- Non-technical user UX (Sam persona — see PLAN.md §0)

## Design Principles
- Plain English everywhere: "Building code" not "Builder agent stage 4"
- Costs in dollars, never tokens
- Gate approval is a checklist, not a code review
- Progressive disclosure: Sam sees simple summary; "View details" expands technical info
- Mobile: gates approvable from phone (full-screen modal, swipe-to-approve)

## Key References in PLAN.md
- §7: HITL gates + plain-language guide
- §21: AMC 7 screens, data models, WebSocket events, API endpoints
- §20 Phase 4: Frontend backlog items
```

### `devstack-planner.agent.md`

```markdown
---
description: 'Breaks down PLAN.md backlog items into implementable tasks with acceptance criteria'
name: 'DevStack Planner'
model: 'claude-sonnet-4'
tools: ['codebase', 'search', 'fetch', 'githubRepo']
---

# DevStack Planner Agent

You break down §20 Implementation Backlog items into actionable GitHub Issues with acceptance criteria.

## Your Approach
1. Read the backlog item in §20
2. Read the referenced spec section (e.g., "Spec: §8" → read §8 in PLAN.md)
3. Break into 1-3 GitHub Issues, each independently shippable
4. Each issue includes: description, acceptance criteria, test plan, files to create/modify
5. Tag with phase label (phase-0, phase-1, etc.) and role label (backend, frontend, devops)

## Issue Template
```
### What
[One paragraph describing what to build]

### Spec Reference
PLAN.md §[N] — [section name]

### Acceptance Criteria
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] Tests pass: `pytest backend/tests/unit/test_{feature}.py -v`

### Files
- Create: `backend/path/to/file.py`
- Modify: `backend/core/ports.py` (add new port if needed)

### Dependencies
- Requires: #{issue_number} (if any)
- Blocks: #{issue_number} (if any)
```

## Constraints
- Never combine multiple §20 items into one issue
- Every issue must have at least one test in acceptance criteria
- Phase 0 items have no dependencies — all can be parallel
```

### `devstack-analyst.agent.md`

```markdown
---
description: 'Reads PLAN.md and answers architecture questions with exact section references'
name: 'DevStack Analyst'
model: 'claude-sonnet-4'
tools: ['codebase', 'search', 'fetch']
---

# DevStack Analyst Agent

You are the walking encyclopedia of the DevStack PLAN.md. When anyone has a question about the architecture, you find the answer in the plan and cite the exact section.

## Your Approach
1. Search PLAN.md for the relevant section
2. Quote the relevant passage
3. Cite as "PLAN.md §N — [section name]"
4. If the question isn't answered in PLAN.md, say so explicitly — never fabricate

## Common Questions You Handle
- "Where is X specified?" → Section number + quote
- "What's the data model for Y?" → Schema from §8 or §21c
- "How does Z work?" → Explanation with section refs
- "Is X consistent with Y?" → Cross-reference check
- "What are the constraints on Z?" → List from relevant section

## Constraint
- AH-1: Never fabricate information. If PLAN.md doesn't cover it, say "Not specified in PLAN.md — this needs a design decision."
```

---

## 4. Skill Files — Reusable Knowledge Bundles

Place in `.github/skills/`. Each skill is a folder with `SKILL.md` + optional bundled assets.

### `devstack-hexagonal/SKILL.md`

```markdown
---
name: devstack-hexagonal
description: 'Hexagonal architecture patterns for the DevStack agency — port definitions, adapter wiring, and import rules'
---

# Hexagonal Architecture — DevStack Patterns

## When to Use This Skill
- Creating a new port interface
- Implementing a new adapter
- Wiring adapters to agents via dependency injection
- Checking import rules (agents → core/ports → adapters)

## The 5 Ports (core/ports.py)

| Port | Purpose | Methods |
|------|---------|---------|
| `LLMPort` | LLM inference | `structured_call(prompt, output_schema, **kwargs) -> T` |
| `VaultPort` | File storage | `save(namespace, key, content)`, `load(namespace, key)`, `save_binary(namespace, key, content, mime_type) -> str` |
| `ToolPort` | External tool execution | `call(tool_name, **kwargs) -> dict` |
| `HumanPort` | HITL gate approval | `ask(question, options, ...) -> str`, `notify(level, message) -> None` |
| `LoggingPort` | Telemetry | `log_event(event: AgentRunEvent)` |

## Adapter Wiring Pattern

```python
# In orchestrator.py — wire once at startup
from adapters.llm.router import ModelRouter
from adapters.vault.azure_blob import AzureBlobVault
from adapters.human.websocket import WebSocketHuman

llm = ModelRouter(config_path="agents_config.yaml")
vault = AzureBlobVault(connection_string=os.environ["AZURE_STORAGE_CONN"])
human = WebSocketHuman(redis=redis_client)

analyst = AnalystAgent(llm=llm, vault=vault, human=human, logger=logger)
```

## Import Rule (CI-Enforced)
```
# ✅ ALLOWED
from core.ports import LLMPort, VaultPort

# ❌ BLOCKED by import-linter
from adapters.llm.anthropic import AnthropicAdapter
```

## References
- PLAN.md §1c — Full hexagonal architecture spec
- PLAN.md §8 — BaseAgent contract
```

### `devstack-rls-security/SKILL.md`

```markdown
---
name: devstack-rls-security
description: 'Row-Level Security patterns for PostgreSQL multi-tenancy — middleware ordering, parameterized queries, PgBouncer session mode'
---

# RLS Security Patterns

## When to Use This Skill
- Writing or modifying RLS middleware
- Configuring PgBouncer
- Adding new database tables (all need RLS policies)
- Reviewing security of data access code

## Critical Rules (violating any = data leak)

### 1. Middleware Order
```python
# AuthMiddleware MUST run BEFORE RLSMiddleware
app.add_middleware(RLSMiddleware)    # runs second (inner)
app.add_middleware(AuthMiddleware)   # runs first (outer)
# FastAPI middleware runs in REVERSE order of add_middleware calls
```

### 2. Parameterized Queries Only
```python
# ✅ CORRECT — parameterized
validated = _validate_uuid(user_id)
await db.execute("SET LOCAL app.user_id = $1", validated)

# ❌ DANGEROUS — SQL injection via f-string
await db.execute(f"SET LOCAL app.user_id = '{user_id}'")
```

### 3. PgBouncer Session Mode
```ini
# pgbouncer.ini
pool_mode = session    # ✅ CORRECT
# pool_mode = transaction  # ❌ BREAKS RLS — resets SET LOCAL on connection return
```

## References
- PLAN.md §6 — Full RLS + middleware spec
- PLAN.md §15 — Known risks (RLS bypass listed)
```

### `devstack-tdd-redgreen/SKILL.md`

```markdown
---
name: devstack-tdd-redgreen
description: 'Red/green TDD workflow enforced by DevStack — write failing test first, then implement, vault the red phase log'
---

# TDD Red/Green Workflow

## When to Use This Skill
- Implementing any new feature
- Fixing any bug (write failing test that reproduces it first)
- Builder agent code generation

## The Mandatory Workflow

### Phase 1: RED (write failing test)
```bash
# Write the test
# Run it — it MUST fail
pytest backend/tests/unit/test_new_feature.py -v --tb=short
# Expected: FAILED (1 failure)
# Vault the red phase log
```

### Phase 2: GREEN (write minimal code)
```bash
# Implement the minimal code to pass
pytest backend/tests/unit/test_new_feature.py -v --tb=short
# Expected: PASSED (all green)
```

### Phase 3: REFACTOR (only if green)
```bash
# Refactor if needed — tests must stay green
pytest backend/tests/ -v --tb=short
# Expected: ALL PASSED (no regressions)
```

## Gate 3 Enforcement
- Red phase log is vaulted to `4_app/red_phase.txt`
- Gate 3 reviewer checks: "Did red phase exist before green phase?"
- If no red phase log → Gate 3 BLOCKS (automatic)

## References
- PLAN.md §4 — Core loop (red/green TDD)
- PLAN.md §7 — Gate 3 checklist
- Simon Willison — "Red/green TDD with agents"
```

---

## 5. Session Hooks — Automated Guardrails

Place `hooks.json` in `.github/hooks/`. These run automatically during Copilot coding agent sessions.

### `hooks.json`

```json
{
  "version": 1,
  "hooks": {
    "postToolUse": [
      {
        "type": "command",
        "bash": ".github/hooks/import-guard.sh",
        "cwd": ".",
        "timeoutSec": 10
      }
    ],
    "sessionEnd": [
      {
        "type": "command",
        "bash": ".github/hooks/session-summary.sh",
        "cwd": ".",
        "timeoutSec": 30
      },
      {
        "type": "command",
        "bash": ".github/hooks/license-check.sh",
        "cwd": ".",
        "env": {
          "LICENSE_MODE": "warn"
        },
        "timeoutSec": 15
      }
    ]
  }
}
```

### `import-guard.sh` — Hexagonal Architecture Enforcement

```bash
#!/bin/bash
# Runs after every file edit — catches import violations immediately
VIOLATIONS=$(grep -rn "from adapters\." backend/agents/ 2>/dev/null || true)
if [ -n "$VIOLATIONS" ]; then
  echo "❌ HEXAGONAL VIOLATION: agents/ cannot import from adapters/"
  echo "$VIOLATIONS"
  echo "Use core/ports.py interfaces instead."
  exit 1
fi
echo "✅ Import rules OK"
```

**PowerShell equivalent (`import-guard.ps1` — for Windows):**
```powershell
# Runs after every file edit — catches import violations immediately
$violations = Select-String -Path "backend\agents\*.py" -Pattern "from adapters\." -ErrorAction SilentlyContinue
if ($violations) {
    Write-Error "❌ HEXAGONAL VIOLATION: agents/ cannot import from adapters/"
    $violations | ForEach-Object { Write-Host $_.Line }
    Write-Host "Use core/ports.py interfaces instead."
    exit 1
}
Write-Host "✅ Import rules OK"
```

### `session-summary.sh`— Session Audit Trail

```bash
#!/bin/bash
# Runs at session end — logs what was changed
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || echo "no git")
TESTS_PASS=$(pytest backend/tests/ -q --tb=no 2>/dev/null && echo "PASS" || echo "FAIL")

echo "=== DevStack Session Summary ==="
echo "Time: $TIMESTAMP"
echo "Files changed: $CHANGED_FILES"
echo "Tests: $TESTS_PASS"
echo "================================"
```

**PowerShell equivalent (`session-summary.ps1`):**
```powershell
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$changed = git diff --name-only HEAD 2>$null
$testsResult = if (pytest backend/tests/ -q --tb=no 2>$null) { "PASS" } else { "FAIL" }
Write-Host "=== DevStack Session Summary ==="
Write-Host "Time: $timestamp"
Write-Host "Files changed: $changed"
Write-Host "Tests: $testsResult"
```

> **Cross-platform note:** Use `.sh` scripts on macOS/Linux/WSL and `.ps1` on Windows. Update `hooks.json` to point to the correct script for your platform. Alternatively, rewrite hooks as Python scripts (cross-platform) using `subprocess` for git/pytest calls.

### `license-check.sh`— Dependency License Compliance

```bash
#!/bin/bash
# Checks for copyleft licenses in new dependencies
BLOCKED="GPL-2.0,GPL-3.0,AGPL-3.0,SSPL-1.0"
NEW_DEPS=$(git diff HEAD -- requirements.txt package.json 2>/dev/null || true)
if [ -n "$NEW_DEPS" ]; then
  echo "New dependencies detected — checking licenses..."
  # Simplified check — full version uses pip-licenses / license-checker
  pip-licenses --format=json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
blocked = set('$BLOCKED'.split(','))
for pkg in data:
    if pkg.get('License') in blocked:
        print(f'❌ BLOCKED: {pkg[\"Name\"]} ({pkg[\"License\"]})')
        sys.exit(1)
print('✅ All licenses OK')
" 2>/dev/null || echo "⚠️ License check skipped (pip-licenses not installed)"
fi
```

---

### Agent Execution Hooks — Runtime Pipeline (Squad-Inspired)

> **Source:** [Squad framework](https://github.com/bradygaster/squad) `HookPipeline` pattern.

Beyond Copilot session hooks (above), the DevStack pipeline agents themselves execute through a hook pipeline. This provides governance **at runtime** without modifying agent code.

```python
# backend/hooks/pipeline.py — Pre/post agent execution hooks
from abc import ABC, abstractmethod
from backend.core.state import ProjectState
from backend.core.ports import LoggingPort

class HookAction:
    def __init__(self, action: str, reason: str = ""):
        self.action = action  # "allow" | "block" | "modify"
        self.reason = reason

class PreAgentHook(ABC):
    """Runs before each agent's run() method."""
    @abstractmethod
    async def check(self, agent_name: str, state: ProjectState) -> HookAction: ...

class PostAgentHook(ABC):
    """Runs after each agent's run() method."""
    @abstractmethod
    async def check(self, agent_name: str, state: ProjectState, result: ProjectState) -> HookAction: ...

# Built-in hooks (receive ports via constructor — same DI pattern as agents):
class BudgetGuard(PreAgentHook):
    """Block execution if token/USD budget exceeded."""
    async def check(self, agent_name, state):
        if state.meta.usd_spent >= state.meta.usd_budget:
            return HookAction("block", f"Budget exceeded: ${state.meta.usd_spent:.2f} >= ${state.meta.usd_budget:.2f}")
        return HookAction("allow")

class GateEnforcer(PreAgentHook):
    """Block agent if prior gate not approved."""
    GATE_MAP = {"designer": 0, "architect": 1, "builder": 2, "deployer": 3}
    async def check(self, agent_name, state):
        required_gate = self.GATE_MAP.get(agent_name)
        if required_gate is not None and not state.gate_approvals.get(required_gate):
            return HookAction("block", f"Gate {required_gate} not yet approved")
        return HookAction("allow")

class AuditLogger(PostAgentHook):
    """Log every agent invocation for audit trail. Uses LoggingPort (not direct I/O)."""
    def __init__(self, logging_port: LoggingPort):
        self.logging_port = logging_port

    async def check(self, agent_name, state, result):
        await self.logging_port.log("info", f"Agent {agent_name} completed", {
            "project_id": str(state.meta.project_id),
            "stage": state.stage,
            "tokens_used": state.meta.tokens_used,
            "usd_spent": state.meta.usd_spent,
        })
        return HookAction("allow")
```

**Hook pipeline runs in `BaseAgent.run()` wrapper** — individual agents don't know about hooks. This keeps agent code clean while enforcing governance, budget, and audit requirements.

> **Why not just use ports?** Ports provide capability abstraction (LLMPort, VaultPort). Hooks provide cross-cutting governance (budget, audit, gates). They're complementary patterns. Ports answer "how do I talk to an LLM?" Hooks answer "should this agent be allowed to run right now?"

---

## 6. Agentic Workflows — GitHub Actions Automation

Place in `.github/workflows/`. These are AI-powered GitHub Actions.

### `daily-agency-report.md` — Daily Status Report

```markdown
---
name: "Daily Agency Report"
description: "Generates a daily summary of pipeline runs, gate approvals, and cost spend"
on:
  schedule: daily on weekdays at 9am UTC
permissions:
  contents: read
  issues: write
safe-outputs:
  create-issue:
    title-prefix: "[daily-report] "
    labels: [report, agency]
---

## Daily Agency Report

Create a daily summary issue for the DevStack team.

## What to Include
- Projects started in last 24 hours (count + names)
- Projects completed (deployed to live)
- Projects failed (with error summary)
- Gates currently pending approval (highlight any > 24h old)
- Total LLM spend yesterday vs 7-day average
- Any infrastructure health alerts
- Top skill by usage this week
```

### `eval-nightly.md` — Nightly Eval Suite

```markdown
---
name: "Nightly Eval Run"
description: "Runs the agent eval suite and posts results as a PR comment"
on:
  schedule: daily at midnight UTC
permissions:
  contents: read
  pull-requests: write
safe-outputs:
  create-issue:
    title-prefix: "[eval] "
    labels: [eval, automated]
---

## Nightly Eval Suite

Run the full eval suite for all 5 agents and post results.

## Steps
1. Run `pytest backend/tests/evals/ -v --tb=short` for backend evals
2. Run `npx vitest run tests/evals/` for frontend evals
3. Compare scores against baseline in `tests/evals/baseline.json`
4. If any score dropped > 5% from baseline, create a GitHub Issue flagging regression
5. Post summary table: agent name, eval score, delta from baseline, pass/fail
```

---

## 7. Copilot SDK Patterns — Multi-Session Orchestration

Key patterns from the awesome-copilot cookbook for building the agency orchestrator.

> ⚠️ **Conceptual examples.** The SDK API below illustrates the *patterns* (fresh context per agent, parallel sessions, persisted sessions) — not the exact import paths or class names. The real GitHub Copilot SDK evolves rapidly; consult the [official SDK docs](https://github.com/features/copilot) for current API surface before implementing. The patterns themselves (Ralph Loop, multi-session, persist/resume) are stable regardless of API changes.

### Ralph Loop— Fresh Context Per Agent Iteration

The most relevant pattern for our 5-agent pipeline. Each agent gets a fresh session (prevents context degradation).

```python
# Pattern: Each agent runs in a fresh Copilot SDK session
# State shared via ProjectState in Redis/Blob (not in-context)

from copilot_sdk import CopilotClient, SessionConfig, MessageOptions
from pathlib import Path

async def run_agent_stage(agent_name: str, skill_path: str, project_state: dict):
    """Run one agent stage with fresh context."""
    client = CopilotClient()
    await client.start()

    session = await client.create_session(SessionConfig(
        model="claude-sonnet-4",
        working_directory=str(Path.cwd()),
        system_message={"content": Path(skill_path).read_text()},
    ))

    # Inject project state as context (not conversation history)
    prompt = f"""
    Project state: {json.dumps(project_state)}

    Execute the {agent_name} stage. Follow the skill instructions exactly.
    Write all outputs to the vault.
    """

    response = await session.send_and_wait(
        MessageOptions(prompt=prompt),
        timeout=600  # 10 min per agent
    )

    await session.destroy()  # Fresh context for next agent
    await client.stop()
    return response
```

### Multi-Session — Parallel Agent Execution

```python
# Pattern: Run independent agents in parallel sessions
async def run_parallel_agents(agents: list[tuple[str, str]], state: dict):
    client = CopilotClient()
    await client.start()

    sessions = []
    for agent_name, skill_path in agents:
        session = await client.create_session(SessionConfig(
            model="claude-sonnet-4",
            system_message={"content": Path(skill_path).read_text()},
        ))
        sessions.append((agent_name, session))

    # Run all in parallel
    tasks = [
        session.send_and_wait(MessageOptions(prompt=f"State: {json.dumps(state)}"))
        for _, session in sessions
    ]
    results = await asyncio.gather(*tasks)

    # Cleanup
    for _, session in sessions:
        await session.destroy()
    await client.stop()
    return dict(zip([name for name, _ in sessions], results))
```

### Persisted Sessions — Resume After Gate Approval

```python
# Pattern: Pause at gate, resume after human approval
async def pause_at_gate(project_id: str, gate_number: int, session: Session):
    """Save session state, wait for gate approval, then resume."""
    # Session state persisted to disk automatically
    session_id = f"project-{project_id}-gate-{gate_number}"
    await session.destroy()  # State saved

    # ... human approves gate via AMC dashboard ...

    # Resume with full context
    client = CopilotClient()
    await client.start()
    resumed = await client.resume_session(session_id)
    return resumed
```

---

## 8. Prompt Engineering Best Practices

Derived from awesome-copilot's 260+ agent definitions and 300+ skill files.

### Structure Every Prompt With

```markdown
## Role
[Who the agent is — 1-2 sentences]

## Context
[What the agent needs to know — project state, constraints, prior decisions]

## Task
[What to do — specific, measurable, verifiable]

## Output Contract
[Exact format of expected output — JSON schema, file paths, markdown template]

## Constraints
[What NOT to do — anti-hallucination rules, scope boundaries, forbidden patterns]

## Examples
[1-2 concrete examples of correct output — Willison "hoard" pattern]
```

### Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| "Be creative" | Non-deterministic output | Specify exact output format |
| "Do your best" | No acceptance criteria | List specific criteria |
| No examples | Agent guesses format | Include 1-2 worked examples |
| Monolithic prompt | Context window waste | Split into skill files (<2K tokens each) |
| "Consider everything" | Agent tries to boil ocean | Explicit scope: "ONLY these 3 things" |
| No constraints | Agent invents features | List what NOT to do |

### Deterministic Prompting (from PLAN.md §1b)

```markdown
## Anti-Hallucination Rules (inject into every skill)

AH-1: Every external fact MUST come from a tool call (file read, API, search).
      Never state facts from "training data."

AH-2: When citing a design decision, reference the PLAN.md section number.
      Example: "RLS is mandatory (PLAN.md §6)."

AH-3: Code must execute before Gate 3. Builder cannot pass on schema validation alone.
      Docker sandbox run with real test execution is mandatory.

AH-4: The original user requirement (from intake) is FROZEN.
      You may refine scope, but never change what the user asked for.
```

---

## 9. Development Workflow — How to Build with Copilot

### Daily Flow for a DevStack Developer

```
1. Pick a §20 backlog item → read the referenced PLAN.md section
2. Invoke @devstack-planner to break it into GitHub Issues
3. Start the issue → invoke @devstack-builder for TDD implementation
4. Open PR → @devstack-reviewer auto-reviews against architecture rules
5. Hooks run: import-guard (post-tool), license-check (session-end)
6. Merge → GitHub Actions CI validates (pytest, vitest, import-linter, ruff, mypy)
7. Nightly eval checks agent quality hasn't regressed
```

### Using Agents Effectively

| Task | Invoke | Why |
|---|---|---|
| "How does RLS work in our system?" | `@devstack-analyst` | Finds exact PLAN.md section + quotes |
| "Design the VaultPort adapter" | `@devstack-architect` | Follows hexagonal rules, references ports.py |
| "Implement ModelRouter" | `@devstack-builder` | TDD red/green, runs tests, validates imports |
| "Review this PR" | `@devstack-reviewer` | Checks AH contract, security, architecture |
| "Create Terraform for Redis" | `@devstack-deployer` | Knows ACI vs ACA, session mode, noeviction |
| "Build the gate approval UI" | `@devstack-designer` | Sam-first UX, plain English, mobile-responsive |
| "Break down Phase 1 into issues" | `@devstack-planner` | Creates GitHub Issues with acceptance criteria |

### RUG Pattern — Repeat Until Good

For complex multi-file features, use the RUG (Repeat Until Good) orchestration:

```
1. @devstack-planner decomposes the feature into tasks
2. For each task:
   a. @devstack-builder implements (work agent)
   b. @devstack-reviewer validates (validation agent)
   c. If review fails → @devstack-builder re-implements with review feedback
3. Final integration: run full test suite
4. PR opened with all changes
```

---

## 10. File Structure Reference

```
devstack/
├── .github/
│   ├── copilot-instructions.md       ← Global Copilot context (read by every interaction)
│   ├── agents/
│   │   ├── devstack-architect.agent.md
│   │   ├── devstack-builder.agent.md
│   │   ├── devstack-deployer.agent.md
│   │   ├── devstack-reviewer.agent.md
│   │   ├── devstack-designer.agent.md
│   │   ├── devstack-planner.agent.md
│   │   └── devstack-analyst.agent.md
│   ├── instructions/
│   │   ├── python-backend.instructions.md    ← Applied to backend/**/*.py
│   │   ├── typescript-frontend.instructions.md ← Applied to frontend/**/*.{ts,tsx}
│   │   ├── terraform-infra.instructions.md   ← Applied to infra/**/*.tf
│   │   └── skills-prompts.instructions.md    ← Applied to backend/skills/**/*.md
│   ├── skills/                               ← Copilot-specific skills (dev guidance)
│   │   ├── devstack-hexagonal/SKILL.md       ← For developers building the agency
│   │   ├── devstack-rls-security/SKILL.md
│   │   └── devstack-tdd-redgreen/SKILL.md
│   ├── hooks/
│   │   ├── hooks.json                        ← Hook event configuration
│   │   ├── import-guard.sh                   ← postToolUse: catch import violations
│   │   ├── session-summary.sh                ← sessionEnd: audit trail
│   │   └── license-check.sh                  ← sessionEnd: dependency compliance
│   └── workflows/
│       ├── ci.yml                            ← Standard CI (pytest, vitest, ruff, mypy)
│       ├── daily-agency-report.md            ← Agentic: daily status issue
│       └── eval-nightly.md                   ← Agentic: nightly eval suite
├── .vscode/
│   └── settings.json                         ← Editor config + Copilot file associations
├── PLAN.md                                   ← Master architecture (1,900+ lines, 22 sections)
├── AGENTS.md                                  ← AI agent entry point (Harness Engineering, ~80 lines)
├── Makefile                                   ← Standard commands (setup, test, lint, dev, ci)
├── copilot-enhance.md                        ← This file
├── docs/
│   ├── architecture.md                        ← Codebase map + dependency rules
│   └── decisions/                             ← Architecture Decision Records (ADRs)
│       ├── 0001-hexagonal-architecture.md
│       ├── 0002-fixed-tech-stack.md
│       ├── 0003-pgbouncer-session-mode.md
│       ├── 0004-aci-not-aca-sandbox.md
│       └── 0005-tdd-red-green-mandatory.md
├── backend/
│   ├── core/                                 ← Ports + state (hexagonal core)
│   ├── agents/                               ← Agent implementations
│   ├── adapters/                             ← Port implementations
│   ├── skills/                               ← Agent skill files (.md)
│   ├── hooks/                                ← Pre/post agent execution hooks (Squad pattern)
│   └── middleware/                            ← Auth + RLS
├── frontend/                                 ← Next.js 15 app
└── infra/                                    ← Terraform + configs
```

---

## Quick Reference Card

| What you need | Where to find it |
|---|---|
| **Agent entry point (for AI tools)** | `AGENTS.md` (~80 lines, read first) |
| Architecture spec | `PLAN.md` (22 sections, 1,900+ lines) |
| Architecture map | `docs/architecture.md` (directory + dependency graph) |
| Decision records | `docs/decisions/` (ADR files — why we chose what) |
| Harness engineering spec | `PLAN.md §22` (how we build with AI agents) |
| Global Copilot context | `.github/copilot-instructions.md` |
| Per-language coding rules | `.github/instructions/*.instructions.md` |
| Copilot agents (invoke with @) | `.github/agents/*.agent.md` |
| Reusable knowledge bundles | `.github/skills/*/SKILL.md` |
| Session guardrails | `.github/hooks/hooks.json` + scripts |
| Runtime agent hooks | `backend/hooks/pipeline.py` (Squad-inspired) |
| AI-powered GitHub Actions | `.github/workflows/*.md` (agentic) |
| Standard commands | `Makefile` (`setup`, `test`, `lint`, `dev`, `ci`) |
| Implementation backlog | `PLAN.md §20` (6 phases, all file paths) |
| AMC dashboard spec | `PLAN.md §21` (7 screens, API, WebSocket) |
| Security patterns | `.github/skills/devstack-rls-security/SKILL.md` |
| TDD workflow | `.github/skills/devstack-tdd-redgreen/SKILL.md` |

> **Two types of skills in this project:**
> - `.github/skills/` — **Copilot skills** for developers building the agency (IDE guidance, patterns, checklists)
> - `backend/skills/` — **Runtime agent skills** loaded by the 5 AI agents at runtime (system prompts, constitution, critique)
> These are different systems. `.github/skills/` follows the awesome-copilot SKILL.md format. `backend/skills/` follows the DevStack skill format (YAML frontmatter + markdown, <2K tokens, validated by SkillRegistry).

---

*Generated from [awesome-copilot](https://github.com/github/awesome-copilot) patterns, tailored for DevStack agency development. See PLAN.md for the full architecture spec.*

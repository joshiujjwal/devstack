# DevStack Agency — Architecture Map

> **Purpose:** High-level codebase map for AI coding agents and new contributors.  
> **Rule:** Keep this under 200 lines. Link to PLAN.md sections for deep details.

---

## System Overview

```
User Idea (plain English)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│            PRESENTATION LAYER                        │
│  FastAPI REST API + Next.js Dashboard + WebSocket    │
└───────────────────────┬─────────────────────────────┘
                        │ JSON / WebSocket events
┌───────────────────────▼─────────────────────────────┐
│            APPLICATION LAYER                         │
│  LangGraph Orchestrator + Gate Manager               │
│  Routes: Analyst → Designer → Architect → Builder    │
│          → Deployer (with gates between each)        │
└───────────────────────┬─────────────────────────────┘
                        │ ProjectState
┌───────────────────────▼─────────────────────────────┐
│            DOMAIN LAYER (core/)                      │
│  BaseAgent + 5 Port Interfaces + Skills + State      │
│  ┌─────────┬──────────┬─────────┬────────┬────────┐ │
│  │ LLMPort │VaultPort │ToolPort │HumanPt │LogPort │ │
│  └────┬────┴────┬─────┴────┬────┴───┬────┴───┬────┘ │
└───────┼─────────┼──────────┼────────┼────────┼──────┘
        │         │          │        │        │
┌───────▼─────────▼──────────▼────────▼────────▼──────┐
│            ADAPTER LAYER (swappable)                  │
│  Anthropic │ AzureBlob │ Docker  │ WebSkt │ OTel    │
│  OpenAI    │ MockVault │ Sandbox │ Mock   │ Prom    │
│  Gemini    │           │         │        │         │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

> **Note:** This shows the target structure from PLAN.md §20. Directories marked
> with *(planned)* don't exist yet — they're created during implementation phases.

```
devstack/
├── AGENTS.md              # AI agent entry point (read first)
├── PLAN.md                # Master spec (2,000+ lines, 22 sections)
├── EXPLAIN.md             # Visual architecture guide
├── Makefile               # Standard entry points
├── docs/
│   ├── architecture.md    # This file
│   └── decisions/         # Architecture Decision Records
│       ├── 0001-hexagonal-architecture.md
│       ├── 0002-fixed-tech-stack.md
│       ├── 0003-pgbouncer-session-mode.md
│       ├── 0004-aci-not-aca-sandbox.md
│       └── 0005-tdd-red-green-mandatory.md
├── backend/                           # (planned — Phase 0+)
│   ├── core/
│   │   ├── ports.py       # 5 abstract port interfaces (THE contract)
│   │   ├── state.py       # ProjectState + ProjectMeta + IntakeAnswers
│   │   └── __init__.py
│   ├── agents/
│   │   ├── base.py        # BaseAgent (port injection, budget, singleton)
│   │   ├── analyst.py     # Stage 1: intake + PRD
│   │   ├── designer.py    # Stage 2: mockups + flows
│   │   ├── architect.py   # Stage 3: data model + API contracts
│   │   ├── builder.py     # Stage 4: TDD code gen + sandbox
│   │   └── deployer.py    # Stage 5: Terraform + Azure deploy
│   ├── adapters/
│   │   ├── llm/           # Anthropic, OpenAI, Gemini, Mock adapters
│   │   ├── vault/         # AzureBlob, Mock vault
│   │   ├── human/         # WebSocket HITL, Mock auto-approve
│   │   └── logging/       # OTel, CopilotSDK adapters
│   ├── hooks/             # Pre/post agent execution hooks (planned — §22e)
│   ├── middleware/
│   │   ├── auth.py        # JWT validation (runs FIRST)
│   │   └── rls.py         # SET LOCAL app.user_id (runs SECOND)
│   ├── skills/            # Markdown skill files per agent
│   │   ├── constitution.md
│   │   ├── critique.md
│   │   ├── gate-checklists.md
│   │   ├── analyst/system-v1.md
│   │   ├── designer/system-v1.md
│   │   ├── architect/system-v1.md
│   │   ├── builder/system-v1.md
│   │   └── deployer/system-v1.md
│   ├── orchestrator.py    # LangGraph state machine
│   └── api/               # FastAPI routes + WebSocket handlers
├── frontend/              # Next.js 15 (TypeScript, TailwindCSS) (planned — Phase 4)
│   ├── app/               # App Router pages
│   └── components/        # Gate approval, pipeline status, cost display
├── infra/                             # (planned — Phase 3)
│   └── terraform/         # Azure IaC (ACA, ACI, PG, Redis, Key Vault)
├── .github/                           # (planned — Phase 3)
│   ├── workflows/         # CI, deploy, infra, eval
│   ├── agents/            # Copilot agent definitions (for development)
│   └── instructions/      # Per-file Copilot coding standards
└── reference/             # Research artifacts and archived plans
```

## Data Flow

```
User Idea → Analyst → [Gate 0] → Designer → [Gate 1] → Architect → [Gate 2]
         → Builder → [Gate 3] → Deployer → [Gate 4] → Live URL

State: ProjectState travels through the entire pipeline.
  - Hot state: Redis (24h TTL, real-time dashboard updates)
  - Cold state: Azure Blob (permanent, all artifacts archived)
  - Metadata: PostgreSQL (user/project records, LLM call logs)
```

## Dependency Rules

```
agents/    →  core/ports.py   (ONLY — enforced by import-linter)
adapters/  →  core/ports.py   (implements interfaces)
middleware/→  core/state.py   (reads ProjectState/user context)
skills/    →  standalone .md  (loaded by SkillRegistry, no code imports)
hooks/     →  core/ports.py   (uses ports for logging/budget checks)
```

**Violation of these rules will be caught in CI and block the PR.**

## Key Patterns

| Pattern | Where | Why |
|---------|-------|-----|
| Port injection | `BaseAgent.__init__(llm, vault, human, tools, logging)` | Testable, swappable |
| Structured output | `instructor` + Pydantic for all LLM calls | AH-1: no free-form text |
| Skill files | `backend/skills/**/*.md` | New capability = new file, not code |
| Circuit breaker | `ModelRouter` (3 failures → fallback model) | Cost protection |
| Gate idempotency | Server-side set, not counter | Double-approve safe |
| Progressive disclosure | AGENTS.md → docs/ → PLAN.md | Agent context efficiency |

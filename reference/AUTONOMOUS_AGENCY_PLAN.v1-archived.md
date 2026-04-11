# 🤖 Autonomous Full-Stack AI Development Agency
## From Idea → Deployed Web App — End-to-End Multi-Agent System

> **Document Version:** 2.0 | **Status:** Active  
> **Last Updated:** March 2026 — rewritten on first-principles (Willison, Karpathy, Anthropic, Harper Reed)  
> **Target Deployment:** Azure Container Apps  
> **Human Oversight:** Stage-gate approval at every phase  

---


## 1. First Principles

> **Why this section exists:** Every design decision in this document should trace back to one of these six principles. If it doesn''t, cut it.

| # | Principle | Source | What it means here |
|---|---|---|---|
| 1 | **Tests are the safety net** | Willison | No agent output is trusted without automated tests. TDD is mandatory for the Builder. No test = no ship. |
| 2 | **Prompts are programs** | Karpathy | System prompts are version-controlled, reviewed, and tested like code. Skill files are first-class artifacts. |
| 3 | **Skills over agents** | Anthropic | Don''t hardcode logic per agent. Load markdown skill files at runtime. New capability = new skill file, not new agent class. |
| 4 | **Human = board of directors** | Harper Reed | Agents report, propose, and ask. Humans direct, approve, and veto. Agents never act unilaterally on irreversible actions. |
| 5 | **Start minimal, earn complexity** | Karpathy | 5 agents in v1. No cross-project memory. No sub-agents. No parallel branching. Add only after v1 ships. |
| 6 | **Checkpointing everywhere** | Harper Reed | Save state at every HITL gate. Roll back is a feature, not an edge case. |

### The Vision (one sentence)
A user describes a web app in plain English; the agency builds and deploys it to Azure — pausing at every stage for human approval.

---

## 2. The Agent Roster (5 agents)

> **Why 5, not 10?** (Karpathy: "Start minimal.") The original 10-agent design added a Critic agent, a Liaison agent, a Security agent, a QA agent, and a Researcher as separate entities. Critic and Liaison are not agents — they are **patterns** (a skill file and an orchestrator feature respectively). Security and QA are Builder responsibilities enforced by skill files. Researcher is combined with Analyst.

| Agent | Combines (v1 original) | Primary Model | Fallback |
|---|---|---|---|
| **Analyst** | Researcher + PM | `claude/claude-3-7-sonnet` | `openai/gpt-4o` |
| **Designer** | UX/UI Designer | `google/gemini-2.5-pro` | `claude/claude-3-7-sonnet` |
| **Architect** | Solutions Architect | `claude/claude-3-7-sonnet` | `openai/gpt-4o` |
| **Builder** | Developer + QA + Security | `claude/claude-3-7-sonnet` | `openai/gpt-4.1` |
| **Deployer** | DevOps + Deployment | `openai/gpt-4.1` | `claude/claude-haiku` |

### What each agent owns

**Analyst** — Clarifies the idea, researches competitors, produces PRD + user stories. Owns `1_analysis/`.

**Designer** — Design system (`DESIGN.md`), user flow diagrams (Napkin AI), screen mockups (Stitch). Owns `2_design/`.

**Architect** — System design within the fixed stack. Produces `architecture.md`, `api_spec.yaml`, Terraform plan. Owns `3_architecture/`.

**Builder** — Code (TDD skill), Docker sandbox execution, security review (OWASP skill), GitHub commits. Owns `4_app/`.

**Deployer** — Dockerfiles, GitHub Actions, Terraform, Azure provisioning, staging → production. Owns `5_infra/`.

> **Critic** is `skills/critique.md` loaded by every agent — not a separate agent. Quality ownership stays with the producer. *(Anthropic)*  
> **Liaison** is the orchestrator rendering structured HITL templates — not a separate agent. A dedicated GPT-4o-mini Liaison is a waste of tokens and a failure point.

---

## 3. Skills-Based Architecture

> **Why skills?** (Anthropic) Hardcoded agent logic doesn''t scale. A skill file is a short markdown document (< 500 tokens) that any agent loads into its context on demand. New capability = new `.md` file. No code change required.

```
skills/
├── critique.md            ← ALL agents load this before returning output
├── tdd.md                 ← Builder: write tests before code
├── design-system.md       ← Designer: token conventions, shadcn/ui patterns
├── terraform.md           ← Deployer: Azure Terraform module patterns
├── security-checklist.md  ← Builder: OWASP Top 10 review checklist
└── api-contract.md        ← Architect: OpenAPI 3.1 conventions
```

### Skill file format (≤ 500 tokens each)

```
# [Skill Name]
**Purpose:** One sentence.
## Steps  (numbered list)
## Example  (1-2 concrete examples)
## Pitfalls  (bullet list)
```

### How agents load skills

```python
class BuilderAgent(BaseAgent):
    skills = ["critique.md", "tdd.md", "security-checklist.md"]

    def run(self, state: ProjectState) -> ProjectState:
        skill_context = self.load_skills()   # reads files, joins into context
        prompt = self.build_prompt(state, skill_context)
        ...
```

Skills live in `backend/skills/`. Loaded once per `run()` call. CI enforces token-count limits per file.

---

## 4. The Core Loop

> **Why this loop?** (Karpathy: "The Loopy Era") Every stage is the same structure. No elaborate branching. Linear pipeline with one feedback cycle per stage.

```
Plan → Generate → Test → Self-Critique (critique.md) → HITL Gate → next stage
  ↑                  |
  └── revise ────────┘  (max 3 iterations before escalating to human)
```

### Pipeline stages

```
Idea Input
  │
  ▼
[Analyst]  → problem_statement.md + PRD.md
  │  HITL Gate 0: "Does this match your vision?"
  ▼
[Designer] → DESIGN.md + wireframes/ + flows/
  │  HITL Gate 1: "Approve design direction?"
  ▼
[Architect] → architecture.md + api_spec.yaml + terraform plan
  │  HITL Gate 2: "Approve architecture?"
  ▼
[Builder]  → app/ (code + tests, Docker-verified)
  │  HITL Gate 3: "Review code summary + test results?"
  ▼
[Deployer] → infra/ + GitHub Actions + staging URL
  │  HITL Gate 4: "Approve production deploy?"
  ▼
  🎉 Live Azure URL
```

### Failure handling
- Any agent failure → retry up to 3× → escalate to human with plain-English failure report
- LangGraph checkpointing (Redis): pipeline resumes from last successful gate after failure
- Infinite loop guard: if Builder/Deployer cycles >3 times on same failure → halt and escalate

---

## 5. Memory: 2 Layers

> **Why only 2?** (Karpathy: "Context window = RAM — load only what''s needed.") The original plan had a third layer: a cross-project agency knowledge base. Cut for v1. It adds zero value until 100 projects have shipped.

| Layer | Technology | Scope | Contents |
|---|---|---|---|
| **Layer 1: Run state** | LangGraph + Pydantic + Redis | Ephemeral per run | Agent outputs, decisions, clarification requests, error log |
| **Layer 2: Project vault** | Markdown files (Azure Blob) | Persistent per project | All stage artifacts, approved versions, decision log |

**Layer 3 (cross-project knowledge base) is explicitly deferred to v2.** Do not build it now.

### Vault structure
```
/{user_id}/{project_id}/
├── 1_analysis/
│   └── PRD.md
├── 2_design/
│   ├── DESIGN.md
│   ├── wireframes/
│   └── flows/
├── 3_architecture/
│   ├── architecture.md
│   └── api_spec.yaml
├── 4_app/           ← mirrors GitHub repo
└── 5_infra/
    └── terraform/
```

---

## 6. Tech Stack

> **Why fixed?** Fewer decisions = fewer bugs = agents that know their target deeply. The Architect makes choices within this stack (DB engine, auth strategy, caching), not outside it.

### Agency Platform (what runs the agents)

| Layer | Technology |
|---|---|
| **Orchestration** | LangGraph (Python 3.12) — stateful graphs, HITL interrupts, Redis checkpointing |
| **Backend API** | FastAPI (Python 3.12) |
| **Frontend Dashboard** | Next.js 15 + TypeScript + Tailwind + shadcn/ui |
| **Real-time** | WebSockets (FastAPI ↔ Next.js) |
| **Database** | PostgreSQL (Azure Database for PostgreSQL) — RLS multi-tenancy, pgvector |
| **Cache / State** | Redis (Azure Cache for Redis) — LangGraph checkpoint store |
| **Code Sandbox** | Docker (Azure Container Instances) — isolated, ephemeral |
| **Secrets** | Azure Key Vault — never in code or env files |
| **Observability** | LangSmith + Azure Monitor |
| **Auth** | Clerk (frontend) + JWT (backend) |
| **Vault Storage** | Azure Blob Storage — project markdown artifacts |
| **LLM Router** | LiteLLM — multi-provider, cost tracking |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions |
| **Design Tools** | Gemini 2.5 Pro + Napkin AI + Google Stitch |

### What the Agency Builds (also fixed)

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15 + TypeScript + Tailwind + shadcn/ui |
| **Backend** | Python 3.12 + FastAPI |
| **IaC** | Terraform (Azure provider) — never Bicep, never ARM |
| **CI/CD** | GitHub Actions |
| **Container** | Docker + Azure Container Apps |
| **Repo** | GitHub (auto-created per project) |

### Multi-Tenancy (PostgreSQL RLS)

Single shared database. Every table carries `project_id` + `user_id`. Isolation enforced by Row-Level Security — not at the application layer.

```sql
CREATE TABLE projects (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id),
    name       TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY projects_isolation ON projects
    USING (user_id = current_setting(''app.user_id'')::UUID);
```

- Vault files → `/{user_id}/{project_id}/` in Azure Blob  
- LangGraph checkpoints → `thread_id = project_id` in Redis  
- GitHub repos → `{user_slug}-{project_slug}`  
- Azure resources → resource group `rg-{project_id}`  

---

## 7. Human-in-the-Loop Design

> **Why HITL at every gate?** (Willison: "Vibe coding is fast and irresponsible.") Agents over-produce complexity. Human judgment is the scoping mechanism.

### Approval UI (Chat Dashboard)

```
┌────────────────────────────────────────────────────────────┐
│ 🤖 Agency           [Project: TaskTracker]   [Gate 2 of 4] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📐 GATE 2 COMPLETE: Architecture Ready                    │
│  ─────────────────────────────────────────────────────    │
│  PostgreSQL + FastAPI + Next.js. Auth via Clerk.           │
│  Redis for session cache. No microservices (MVP).          │
│                                                            │
│  💰 Estimated cost so far: $0.34 | Stage budget: $2.00     │
│                                                            │
│  [📄 View architecture.md]  [📄 View api_spec.yaml]        │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │ ✅ Approve   │  │ ✏️ Give Notes  │  │ 🔄 Re-run Stage │ │
│  └──────────────┘  └───────────────┘  └─────────────────┘ │
│  Your message: ___________________________________________  │
└────────────────────────────────────────────────────────────┘
```

### Gate Rules
| Action | What happens |
|---|---|
| **Approve** | Pipeline advances. State checkpointed. |
| **Give Notes** | Feedback routed to owning agent; agent revises and re-submits. |
| **Re-run** | Stage restarts from checkpoint. Agent gets a clean attempt. |
| **Ask a question** | Orchestrator routes to owning agent; inline response in chat. |
| **Stop** | Project paused at checkpoint indefinitely. Resumable any time. |

### Agents ask humans too
Any agent can call `ask_human()` mid-task (not just at gates) when a decision has significant trade-offs. Dashboard shows it as a priority card. No agent makes irreversible infrastructure decisions without explicit human approval.

---

## 8. BaseAgent Contract

> **Why a shared contract?** (Principle 3 + Anthropic) The orchestrator never imports individual agents. It only knows names. Every agent is a class with the same interface, making the system trivially extensible.

```python
# backend/agents/base.py
from abc import ABC, abstractmethod
from backend.orchestrator.state import ProjectState

class BaseAgent(ABC):
    name: str           # e.g. "builder"
    stage: str          # pipeline stage, e.g. "build"
    model: str          # primary LiteLLM model string
    fallback_model: str
    skills: list[str]   # skill filenames to load into context

    def __init__(self, project_id: str): ...

    @abstractmethod
    def run(self, state: ProjectState) -> ProjectState:
        """Main entry. Must return updated state. Must NOT raise."""
        ...

    def ask_human(self, state, question: str, context: str,
                  options: list[str] = []) -> ProjectState:
        """Adds clarification request to state → triggers HITL interrupt."""
        ...

    def record_decision(self, state, question: str, chosen: str,
                        rationale: str, alternatives: list[str] = []) -> None:
        """Writes significant decisions to state + vault."""
        ...

    def emit(self, state, content: str) -> ProjectState:
        """Appends agent message to conversation log (shown in dashboard)."""
        ...

    def fail(self, state, error: str) -> ProjectState:
        """Records error. Orchestrator decides on retry. Never raises."""
        ...

    def load_skills(self) -> str:
        """Reads self.skills files and returns joined markdown context."""
        ...
```

### Consistency rules (enforced by CI)
1. Every agent declares `name`, `stage`, `model`, `fallback_model`, `skills`
2. `run()` signature is always `(self, state: ProjectState) -> ProjectState`
3. `run()` never raises — errors go to `self.fail()`
4. All LLM calls use `self.llm.structured_call()` with a Pydantic `output_schema`
5. Agents write artifacts to vault AND update state — not one or the other

### Agent registry (single source of truth)

```python
# backend/orchestrator/registry.py
AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "analyst":   AnalystAgent,
    "designer":  DesignerAgent,
    "architect": ArchitectAgent,
    "builder":   BuilderAgent,
    "deployer":  DeployerAgent,
}

# LangGraph node factory — orchestrator only calls this
def make_node(agent_name: str):
    def node_fn(state: ProjectState) -> ProjectState:
        agent = AGENT_REGISTRY[agent_name](state.meta.project_id)
        return agent.run(state)
    node_fn.__name__ = agent_name
    return node_fn
```

---

## 9. Cost Controls

> **Why from day 1?** (Harper Reed + Anthropic) Cost controls added in phase 5 are always too late. They need to be load-bearing architecture from the start.

| Control | Mechanism |
|---|---|
| **Per-stage token budget** | Hard limit in `ProjectState`. Agent must summarize + stop if exceeded. |
| **Budget exceeded → escalate** | Agent calls `ask_human()` with a cost summary and options to continue. |
| **Gate cost display** | Dashboard shows running cost estimate before each approval (see §7 UI). |
| **Project budget cap** | User sets a hard USD limit at project start. Pipeline halts if exceeded. |
| **Model routing** | LiteLLM routes to cheaper fallback if primary rate-limits (not just on error). |
| **Cost tracking per project** | Every LiteLLM call tagged with `project_id` + `agent_name` + `stage`. |

```python
# Enforced in BaseAgent.run() wrapper
if state.meta.tokens_used > state.meta.token_budget:
    return self.ask_human(state,
        question="Token budget exceeded. How do you want to proceed?",
        context=f"Used {state.meta.tokens_used} of {state.meta.token_budget} tokens.",
        options=["Extend budget by 50%", "Summarize and stop", "Abort stage"],
    )
```



> **Why 4 phases, not 6?** (Karpathy: "Start minimal.") The original plan had 6 phases including a cross-project knowledge base and a polish phase before the product was even deployed end-to-end. Phases are now ordered by value delivered.

### Phase 1 — Foundation + 5 Agents + Dashboard
- [ ] Monorepo setup (`agency-platform/`)
- [ ] LangGraph skeleton: 5 nodes, HITL interrupts, Redis checkpointing
- [ ] FastAPI backend + WebSocket streaming
- [ ] Next.js chat dashboard (gate UI, artifact viewer, cost display)
- [ ] LiteLLM router + all 5 agent stubs
- [ ] Skills system: file loading + CI token-count tests
- [ ] **Milestone:** Idea → Architecture with human approval gates (no real code gen yet)

### Phase 2 — Project Vault (File-Based Memory)
- [ ] Azure Blob vault with `/{user_id}/{project_id}/` namespace
- [ ] Vault read/write in all agents
- [ ] Artifact viewer in dashboard (renders markdown, YAML, HTML mockups)
- [ ] Decision log per project
- [ ] **Milestone:** Artifacts persist across sessions; projects are resumable

### Phase 3 — Azure Deployment End-to-End
- [ ] Builder Agent: Docker sandbox code execution (Azure Container Instances)
- [ ] TDD skill: Builder writes tests first, verifies they pass before HITL gate
- [ ] Deployer Agent: Terraform + GitHub Actions + Azure Container Apps
- [ ] Staging → production promotion flow
- [ ] **Milestone:** Full end-to-end: Idea → Live Azure URL

### Phase 4 — Cost Tracking + Multi-Project + Polish
- [ ] Cost dashboard (per-project spend, per-agent breakdown)
- [ ] Multi-project support per user
- [ ] Project history and replay from any checkpoint
- [ ] Agency''s own CI/CD + monitoring (dogfooding)
- [ ] **Milestone:** Production-ready; usable by others

---

## 11. Directory Structure

```
agency-platform/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── agents/
│   │   ├── base.py
│   │   ├── analyst.py
│   │   ├── designer.py
│   │   ├── architect.py
│   │   ├── builder.py
│   │   └── deployer.py
│   ├── skills/
│   │   ├── critique.md
│   │   ├── tdd.md
│   │   ├── design-system.md
│   │   ├── terraform.md
│   │   ├── security-checklist.md
│   │   └── api-contract.md
│   ├── orchestrator/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── registry.py
│   │   └── checkpointer.py
│   ├── tools/
│   │   ├── web_search.py
│   │   ├── code_executor.py
│   │   ├── github_api.py
│   │   ├── azure_api.py
│   │   └── vault.py
│   ├── llm/router.py
│   └── api/
│       ├── projects.py
│       ├── chat.py
│       └── approvals.py
├── frontend/
│   ├── app/projects/[id]/
│   └── components/
│       ├── ChatPanel.tsx
│       ├── ApprovalGate.tsx
│       ├── ArtifactViewer.tsx
│       ├── CostDisplay.tsx
│       └── PipelineProgress.tsx
├── infra/terraform/
└── .github/workflows/
    ├── ci.yml
    └── deploy.yml
```

---

## 12. What We Are NOT Building Yet

> *(Karpathy: "Start minimal, earn complexity.")* These are explicit deferrals, not forgotten features.

| Cut Item | Why deferred |
|---|---|
| **Cross-project knowledge base (Layer 3 memory)** | Needs 100+ projects to be useful. Premature optimization. |
| **Parallel sub-agents** (Frontend ∥ Backend ∥ DB) | Adds coordination complexity before the linear path is proven. |
| **Perplexity Sonar / real-time web search** | Tavily is sufficient for v1. Adds another API dependency. |
| **SWE-agent-style iterative bug-fix loops** | Builder''s TDD loop + max-3-retry guard covers 90% of cases. |
| **Voice input on dashboard** | Nice-to-have. Text is sufficient for v1 and easier to test. |

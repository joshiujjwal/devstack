# 🤖 Autonomous Full-Stack Dev Agency
## Idea → Deployed Web App, end-to-end

> **Version:** 2.0 — First-principles rewrite  
> **Grounded in:** Willison (agentic engineering), Karpathy (Software 3.0), Anthropic (skills > agents), Harper Reed (human = board)  
> **Original archived:** `AUTONOMOUS_AGENCY_PLAN.v1-archived.md`  

---

## 📋 TL;DR — Read This First (2-minute orientation)

> **What this document is:** A complete, self-contained blueprint for an autonomous 5-agent AI development agency. It takes a plain-English app idea and delivers a live Azure-deployed web app — with tests, OWASP checks, and a full audit trail — for under $25.

### What gets built
A pipeline of **5 AI agents** (Analyst → Designer → Architect → Builder → Deployer) orchestrated by LangGraph, with **5 human approval gates** at key decision points. Every agent writes to a shared **ProjectState** object (Redis hot + Azure Blob cold). Every generated app ships with OpenTelemetry, Azure App Insights, and RLS-enforced multi-tenancy.

### Fixed tech stack (non-negotiable in v1)
| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (TypeScript) |
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL + PgBouncer (session mode) + Redis |
| Infra-as-Code | Terraform + Azure Container Apps |
| CI/CD | GitHub Actions |
| Design tools | Google Gemini (brief) + Napkin AI (flows) + Google Stitch (mockups) |
| LLM routing | LiteLLM + ModelRouter (model-agnostic, YAML-configured) |

### How to read this document by role

| You are… | Read these sections first |
|---|---|
| **Product owner / Sam** | §0 (what it does, pricing), §7 (your 5 approval gates), §19 (business model) |
| **Backend engineer** | §1b (AH contract), §1c (hexagonal arch), §8 (BaseAgent), §6 (tech stack + RLS), §20 (implementation backlog) |
| **Frontend engineer** | §7 (gate UI + WebSocket spec), §16 (observability dashboards), §20 Phase 4 |
| **DevOps / Infra** | §6 (ACI sandbox spec), §10 (build phases), §11 (directory structure), §20 Phase 3 |
| **Designer** | §2 (Designer agent), §6 (Napkin/Stitch I/O spec), §7 Gate 1 (mockup approval) |
| **Investor / stakeholder** | §0 (persona + metrics), §18 (legal/compliance), §19 (unit economics + GTM) |
| **Legal / compliance** | §18 (full pre-launch checklist), §15f (business risks), §6 (data residency) |
| **Agency admin / team lead** | TL;DR → §21 (AMC screens + API), §16 (observability), §17 (Copilot SDK analytics), §20 Phase 4b |

### Key design decisions (and why)
| Decision | Why |
|---|---|
| **Skills over bespoke agents** | Skill markdown files are versionable, testable, and swappable without code changes (Anthropic pattern) |
| **Fixed stack in v1** | Eliminates a whole class of hallucination ("what framework should I use?"). Stack is a solved problem; app logic is not. |
| **ACI not ACA for sandbox** | ACA does not support Docker-in-Docker. ACI ephemeral containers are the only Azure option for isolated code execution. |
| **PgBouncer session mode** | Transaction mode resets `SET LOCAL app.user_id` on connection return → silent RLS bypass → data leak. Session mode is mandatory. |
| **5 HITL gates** | "Human = board of directors." Agents propose; humans approve. Gates 0, 1, 4 are intuitive for non-technical users. Gates 2-3 have plain-language guides (§7). |
| **Red/green TDD enforced** | Builder writes failing tests BEFORE writing code. Red-phase log is vaulted. Passing without red phase is a Gate 3 blocker. |
| **Hexagonal architecture** | Agents import only from `core/ports.py`. Adapters (Anthropic, Azure, etc.) are swappable without touching agent logic. |

### What this system does NOT do (v1)
Mobile apps · Existing codebase modifications · Shopify / WordPress plugins · ML pipelines · CLI tools · Real-time WebSocket-heavy apps · Multi-cloud (Azure only in v1)

---

## 0. Product North Star

**Primary user persona — "Sam"** (compliance-conscious founder or internal product owner):
> Sam is a **founder or product manager at a funded startup or SMB** who needs a web app built to a professional standard — not a throwaway prototype. Sam may be non-technical but has a budget ($50-500/mo), a clear idea, and stakeholders to satisfy. Sam values **guardrails, audit trails, and predictable quality** over raw speed. Sam would otherwise hire a freelancer ($5-15k) or a dev agency ($20-50k). This system delivers the same outcome in an afternoon for under $25.

**Secondary persona — "Alex":** A developer who wants to skip boilerplate and ship side projects 10× faster with professional defaults already in place.

**What Sam is NOT:** A solo founder who wants Bolt.new speed (idea → live in 10 min). For that use case, Bolt.new, Lovable.dev, and Vercel v0 are better choices. This system trades speed for correctness, compliance, and audit trail.

**Value proposition:** *Turn a plain-English app idea into a production-ready, Azure-deployed web app — with a full audit trail, architecture review, and TDD-verified code — in one afternoon, for under $25.*

**When HITL gates help Sam (not hinder):**
- Gate 0: Catches scope creep before any work starts ($0 cost to catch here)
- Gate 1: Sam sees mockups before code is written — easy to change direction
- Gate 4: Sam has a staging URL to share with stakeholders before going live
- Gates 2-3: Shown in plain language (see below); Sam's job is budget approval, not technical review

**Agency success metrics (v1 targets):**
| Metric | Target |
|---|---|
| Idea → deployed URL (happy path) | < 3 hours |
| First-pass gate approval rate (no revision needed) | > 65% |
| Project completion rate (Gate 0 → Gate 4) | > 70% |
| "App does what I described" (user-reported) | > 80% |
| Cost per project (LLM + Azure) | < $25 |

**Pricing (v1):** LLM costs passed through at cost + 20%. User pays Azure resources directly (shown pre-Gate 0). First project free on Railway (demo mode, no Azure account needed). No subscription. No seat fee.

**Post-deployment model:** Revisions are incremental pipeline re-runs. Patch cost = ~$5-10 (single-stage re-run, not full rebuild). Dependency updates shipped monthly as automated PRs from agency (Phase 2+).

**Competitive position:** Not competing with Bolt.new on speed. Competing with hiring a freelancer on cost ($20 vs $5,000) and with dev agencies on turnaround (1 day vs 4 weeks). Moat = audit trail + HITL gates + production-ready defaults that freelancers often skip.

**Onboarding (v1 sketch):** Landing page → "Try it free" → OAuth (GitHub login) → Demo project auto-starts ("Build me a task tracker for 3 people") → user watches pipeline run → at Gate 0, prompted to approve their own idea → learns the flow before spending money.

---

## 1. First Principles

> *"These govern every design decision. If something in this plan violates one, the plan is wrong."*

| # | Principle | Source |
|---|---|---|
| 1 | **Tests are the safety net.** No test = no trust. Agents break things silently. | Willison |
| 2 | **Prompts are programs.** Version and test system prompts like code. | Karpathy |
| 3 | **Skills over agents.** Load markdown skill files into a universal agent instead of building bespoke agents for everything. | Anthropic |
| 4 | **Human = board of directors.** Agents report, propose, and ask. Humans approve and redirect. | Harper Reed |
| 5 | **Start minimal, earn complexity.** 5 agents in v1. Add more only when v1 is shipped and validated. | Karpathy |
| 6 | **Checkpointing everywhere.** Save state at every gate. Roll back is a feature, not an afterthought. | Harper Reed |

---

## 1b. Anti-Hallucination Contract

> **Why here?** Hallucination is not a prompt quality problem — it's an architecture problem. These 4 rules are enforced by code, not by asking the model nicely.

| # | Rule | Mechanism | Impact |
|---|---|---|---|
| **AH-1** | **All LLM calls use structured schemas.** No agent returns free-form text. | `instructor` + Pydantic models for every `structured_call()`. Validator rejects and auto-retries with error feedback (×3). | 70-80% error reduction |
| **AH-2** | **Tool use before answer.** No agent may state a fact without grounding it in a real tool call. | `tool_choice="required"` (OpenAI) / `tool_runner` loop (Anthropic). Analyst must call `web_search` before claiming any competitor or market fact. | 60-70% error reduction |
| **AH-3** | **Code must execute before gate.** Builder cannot pass Gate 3 on schema validation alone. | Docker sandbox execution: tests must pass, actual stderr fed back to model on retry. TDD forces tests written first. | 80-95% for code |
| **AH-4** | **`original_requirement` is immutable.** Summarisation checkpoints may not rewrite it. | Pinned field in `ProjectState` with `frozen=True`. Context window trim never touches it. All agents re-read it at the top of every `run()`. | Prevents context drift |

```python
# AH-1: enforced in BaseAgent — every LLM call
result = self.llm.structured_call(
    prompt=prompt,
    output_schema=AnalystOutput,  # Pydantic — rejects on validation failure
    max_retries=3,                # error message fed back to model on each retry
)

# AH-2: Analyst must call web_search BEFORE generating PRD claims
@requires_tool_call("web_search")   # decorator raises if no tool called first
def run(self, state: ProjectState) -> ProjectState: ...

# AH-4: original_requirement never drifts
class ProjectMeta(BaseModel, frozen=True):
    project_id: UUID
    user_id: UUID
    original_requirement: str          # AH-4: never summarised away
    token_budget: int = 200_000        # hard limit per project
    tokens_used: int = 0
    usd_budget: float = 50.0           # user's stated max spend
    usd_spent: float = 0.0
    created_at: datetime
    monthly_infra_estimate: float = 0.0  # updated by Architect at Gate 2

class ProjectState(BaseModel):
    meta: ProjectMeta
    intake: IntakeAnswers | None = None
    stage: Literal["intake","analyst","designer","architect","builder","deployer","done","failed"]
    artifacts: dict[str, str] = {}     # vault_key -> vault_path (e.g. "prd" -> "1_analysis/prd.md")
    decisions: list[dict] = []         # [{question, chosen, rationale, agent, timestamp}]
    errors: list[str] = []             # non-raising error log; downstream agents read this
    status: Literal["ok","degraded","failed"] = "ok"
    gate_approvals: dict[int, bool] = {}   # gate_number -> approved

    model_config = ConfigDict(use_enum_values=True)
```

> **Engineer note:** `run()` signals failure via `state.errors.append(msg); state.status = "failed"; return state` — never raises. Downstream agents check `state.status` before proceeding.

**`CONSTITUTION.md`** — a new skill file loaded by every agent's `critique.md` step:
```
1. All claims must cite a tool call result, vault file, or be marked assumption=true.
2. Do not invent API signatures or library versions not confirmed by execution.
3. If unsure, raise ask_human() rather than guessing.
4. Code must pass type checking + sandbox execution — not just look correct.
```

---

## 1c. Clean Architecture (Hexagonal / Ports & Adapters)

> **Why hexagonal?** Agents must be testable without calling real LLMs, deployable to any cloud, and swappable between providers. This is only possible if agents depend on *abstractions* (ports), not *implementations* (Anthropic SDK, Azure SDK).

```
┌──────────────────────────────────────────────────────────────┐
│          PRESENTATION  (FastAPI + Next.js + WebSocket)       │
└────────────────────────┬─────────────────────────────────────┘
                         │ JSON / WebSocket
┌────────────────────────▼─────────────────────────────────────┐
│          APPLICATION   (LangGraph orchestrator + registry)   │
└────────────────────────┬─────────────────────────────────────┘
                         │ ProjectState
┌────────────────────────▼─────────────────────────────────────┐
│          DOMAIN        (BaseAgent + Skills + State)          │
│                                                              │
│  Agents depend ONLY on these 5 ports (abstractions):        │
│  LLMPort · VaultPort · ToolPort · HumanPort · LoggingPort   │
└──┬───────────┬───────────┬──────────┬───────────┬───────────┘
   │           │           │          │           │
┌──▼──┐    ┌──▼──┐    ┌───▼──┐   ┌──▼──┐    ┌──▼──────┐
│Anthro│    │Azure│    │Docker│   │WebSk│    │LangSmith│
│ pic  │    │Blob │    │Exec  │   │ et  │    │ / Prom  │
│ LLM  │    │Vault│    │Tools │   │HITL │    │ etheus  │
└──────┘    └─────┘    └──────┘   └─────┘    └─────────┘
     ADAPTERS (concrete, swappable, never imported by agents)
```

**SOLID rules for the codebase (enforced by CI linting):**

| Principle | Rule | Enforcement |
|---|---|---|
| **S** — Single Responsibility | Each agent owns one stage. Each skill file owns one capability. Each adapter owns one provider. | File-level lint: no agent imports another agent |
| **O** — Open/Closed | New skill = new `.md` file. `SkillRegistry` auto-discovers all `.md` files in `skills/`. No existing code modified. | CI: `SkillRegistry.validate_all()` runs on every PR |
| **L** — Liskov Substitution | Any `LLMPort` impl can replace any other. `AnthropicLLM`, `OpenAILLM`, `MockLLM` all honour the same contract. | mypy strict mode on all adapters |
| **I** — Interface Segregation | `BaseAgent` only requires `run()`, `emit()`, `fail()`. `HITLCapable` and `DecisionRecorder` are opt-in mixins. | Abstract base classes; no unused abstract methods |
| **D** — Dependency Inversion | Agents import `from core.ports import LLMPort` — never `from anthropic import Anthropic`. | CI: `import-linter` forbids `agents/` from importing `adapters/` |

```python
# core/ports.py — the 5 port interfaces every agent depends on
class LLMPort(ABC):
    async def structured_call(self, prompt: str, output_schema: type[T], ...) -> T: ...
    async def get_cost(self, prompt_tokens: int, completion_tokens: int) -> float: ...

class VaultPort(ABC):
    async def save(self, namespace: str, key: str, content: str | bytes) -> None: ...
    async def load(self, namespace: str, key: str) -> str | bytes: ...
    async def save_binary(self, namespace: str, key: str, content: bytes, mime_type: str) -> str: ...  # returns URL

class ToolPort(ABC):
    async def call(self, tool_name: str, **kwargs) -> dict: ...
    def available_tools(self) -> list[dict]: ...

class HumanPort(ABC):
    async def ask(self, question: str, options: list[str], ...) -> str: ...
    async def notify(self, level: str, message: str) -> None: ...

# WebSocketHumanAdapter security requirements:
# 1. Connection: JWT token in `Sec-WebSocket-Protocol` header, validated at upgrade
# 2. Routing: connection scoped to user_id + project_id — user A cannot receive user B's gate events
# 3. Reconnect: gate state persisted in Redis; reconnection restores pending gate question
# 4. Timeout: unanswered gates auto-expire after 24h with `awaiting_human=False, pipeline_errors+=["Gate N timed out"]`
# 5. Double-advance: gate approval is idempotent (server-side set, not counter)

class LoggingPort(ABC):
    async def log(self, level: str, message: str, metadata: dict = None) -> None: ...
```

**Testing benefit:** `MockLLM() + MockVault() + MockHuman()` → full agent unit tests with zero real API calls, zero Azure dependency.

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

**Designer toolchain I/O (concrete spec):**
| Step | Input | Output | Vault path |
|---|---|---|---|
| Gemini 2.5 Pro → `DESIGN.md` | PRD + intake aesthetic choice | Markdown design system: colors (hex), fonts, spacing scale, component list, screen list | `2_design/design_system.md` |
| Napkin AI API → diagrams | User flow text from `DESIGN.md` (pipe-delimited steps) | **SVG files** (Napkin returns `image/svg+xml`). One SVG per user flow. | `2_design/flows/*.svg` |
| Google Stitch → mockups | `DESIGN.md` + screen list with descriptions | **HTML+CSS mockup** per screen (Stitch returns self-contained HTML). Rendered by `ArtifactViewer.tsx` via iframe. | `2_design/mockups/*.html` |

**Fallback if Napkin AI is down:** Designer generates ASCII flow diagram in `DESIGN.md` and logs `state.errors.append("napkin_unavailable: text flow used")`. Does NOT fail the stage.

**Brand input (new IntakeAnswers field):** `brand_assets_url: str | None = None`. User pastes URL of existing site or uploads brand guide PDF (stored as blob). Designer agent calls `web_fetch(brand_assets_url)` to extract dominant colors via CSS/meta tags.

**Gate 1 artifact format:** `ArtifactViewer.tsx` renders `.html` mockups in sandboxed `<iframe>` (no JS execution). SVG diagrams shown as inline images. No Figma account required.

**Architect** — System design within the fixed stack. Produces `architecture.md`, `api_spec.yaml`, Terraform plan. Owns `3_architecture/`.

**Builder** — Code (TDD skill), Docker sandbox execution, security review (OWASP skill), GitHub commits. Owns `4_app/`.

**Deployer** — Dockerfiles, GitHub Actions, Terraform, Azure provisioning, staging → production. Owns `5_infra/`.

> **Critic** is `skills/critique.md` loaded by every agent — not a separate agent. Quality ownership stays with the producer. *(Anthropic)*  
> **Liaison** is the orchestrator rendering structured HITL templates — not a separate agent. A dedicated GPT-4o-mini Liaison is a waste of tokens and a failure point.

---

## 2b. Idea Intake Protocol

> **Why?** Every downstream hallucination traces to ambiguity at intake. These questions eliminate agent guessing before any work starts. Grounded in: Shape Up, Working Backwards, The Mom Test, YC application, RICE scoring.

> **⚠️ Stack constraint (shown to user at top of intake):** *"This system builds web apps (Next.js frontend + Python/FastAPI backend) deployed to Azure. It does NOT support: mobile apps, Shopify plugins, data pipelines, CLI tools, or Vercel deployments. If your project requires these, stop here."*

**Mandatory — 5 questions, ~2 minutes. Gate 0 blocks if any are missing.**  
**Contextual — 10 additional questions surfaced by Analyst interactively if needed.**

| # | Category | Question | Type | Hallucination it prevents |
|---|---|---|---|---|
| **Q1** | Problem | What is the core problem? (automate / centralise / replace / enable) | Choice | Building the wrong thing entirely |
| **Q2** | User | Who uses it? (just me / team / customers / public) | Choice | Over-engineered auth, wrong data model |
| **Q3** | Flow | Happy path in ≤5 numbered steps | Freeform | 30 screens instead of 3 |
| **Q4** | Compliance | Any compliance needs? (none / HIPAA / PCI / GDPR) | Multi-choice | Non-compliant stack shipped |
| **Q5** | Budget | Monthly hosting budget? (<$50 / <$500 / unlimited) | Choice | Wrong infra tier, surprise bills |

**Contextual (Analyst asks these interactively only if relevant):**

| # | Category | Question |
|---|---|---|
| C1 | Success | How will you measure success? (3 metrics max) |
| C2 | Workflow | Describe one painful workflow today |
| C3 | Scope | What is one workflow you do NOT want automated? |
| C4 | Data | What data must the app store? (users / items / history / files) |
| C5 | Integration | One primary integration? (email / Slack / Google / GitHub / Stripe / none) |
| C6 | Timeline | Launch timeline? (ASAP / 1-2 weeks / 1 month / no deadline) |
| C7 | Existing | Existing systems or APIs to connect? Credentials available? |
| C8 | Failure | What would make this not worth shipping? |
| C9 | Design | Aesthetic direction? (minimal / modern / match existing brand) |
| C10 | Access | How will users access it? (public URL / invite / login / internal) |

**Build-vs-Buy gate:** Before Gate 0, Analyst runs `web_search` for existing SaaS solutions. If a well-maintained tool solves >80% of stated needs at <$100/mo, it surfaces a recommendation: *"Notion + Zapier already does this. Should we continue building?"* The human decides; Analyst does NOT decide.

**Output of intake → `1_analysis/intake_summary.json`** (structured, machine-readable). Analyst uses this as its sole authoritative source. Any field not answered is an explicit `null`, not guessed.

```python
class IntakeAnswers(BaseModel):   # NOT frozen — filled progressively during intake conversation
    # Locked to model_fields_set at Gate 0 checkpoint; frozen after human approves
    core_problem: str | None = None          # Filled during intake conversation
    user_type: str | None = None
    happy_path_steps: str | None = None
    compliance: str | None = None
    monthly_budget: str | None = None
    # Contextual — may be None if not asked
    success_metrics: list[str] | None = None
    data_entities: list[str] | None = None
    primary_integration: str | None = None
    deploy_model: Literal["public","invite","login","internal"] | None = None
    brand_assets_url: str | None = None      # C9: URL to existing site or uploaded brand guide
    existing_system_url: str | None = None   # C7: URL/description of existing system to integrate

> **Mandatory fields constant:**
> ```python
> MANDATORY_FIELDS = ["core_problem", "user_type", "happy_path_steps", "compliance", "monthly_budget"]
> ```
> **Progressive filling:** During intake, the Analyst fills these fields one by one. At Gate 0, a validator checks all 5 mandatory fields are non-None: `assert all(getattr(intake, f) is not None for f in MANDATORY_FIELDS)`. Gate 0 blocks if any mandatory field is still None.

If Analyst finds contradictions (e.g., "ASAP timeline" + "5 integrations"), it calls `ask_human()` with the specific conflict — it does not silently resolve it.

---

## 3. Skills-Based Architecture

> (Anthropic) A skill file is a short markdown document (< 500 tokens) loaded into an agent's context on demand. New capability = new `.md` file, not a new agent class.

> Skills evolve over time through the **Compound Step** (see §13f) — every project that ships automatically opens a PR to improve the skill file used. Over 10+ projects, skill quality compounds.

```
skills/
├── critique.md            ← ALL agents — structured self-eval (see §9b reflection prompt)
├── constitution.md        ← ALL agents — 4 anti-hallucination principles (see §1b)
├── tdd.md                 ← Builder — write tests before code
├── design-system.md       ← Designer — token conventions, shadcn/ui patterns
├── terraform.md           ← Deployer — Azure Terraform module patterns
├── security-checklist.md  ← Builder — OWASP Top 10 review
├── api-contract.md        ← Architect — OpenAPI 3.1 conventions
├── prompt-style.md        ← ALL agents — portability rules (avoid vendor idioms, see §6b)
└── gate-checklists.md     ← ALL agents — YES/NO/DEFER questions per gate (see §7)
```

Skill format: `# Name | **Purpose** | ## Steps | ## Example (working code) | ## Pitfalls` (≤ 500 tokens each).

> **(Willison: Hoard pattern)** Every skill file must include a **working code example** — not pseudocode, not prose, actual runnable code that has been validated. Agents can recombine proven working examples to solve new problems. We only ever need to figure out a pattern once; the skill file is its permanent home. When an agent discovers a new pattern that works, it files a PR adding it to `skills/`. This is the compound step.

```python
class BuilderAgent(BaseAgent):
    skills = ["critique.md", "tdd.md", "security-checklist.md"]
    def run(self, state):
        prompt = self.build_prompt(state, self.load_skills())  # skills → context
        ...
```

Skills live in `backend/skills/`. CI enforces token-count limits per file.

**`AGENTS.md`** — the project's machine-readable configuration for tools like Claude Code, Codex, and Devin. Placed at repo root. Contains: agent registry table (name → module path), skill-to-agent mapping, tool allowlists per agent, and environment variable requirements. External coding tools read this file to understand the agency's structure before making changes.

---

## 4. The Core Loop

> (Karpathy: "The Loopy Era") Every stage is the same pattern. No branching. One feedback cycle per stage.

```
Intake (15 Qs) → Plan → [RED: write tests, confirm they fail] → [GREEN: implement until tests pass] → Reflect → (loop up to 3×) → HITL Gate → next stage
                   ↑         ↑          ↑        ↑
              Pydantic    tool_use   CONSTITUTION  Docker sandbox
              schema      before     .md check    execution
              (AH-1)      answer     (AH-2+3)     (AH-3)
                          (AH-2)
```

> **Red/green TDD (Willison):** Builder first writes tests and **confirms they fail** (red phase) before writing any implementation code. A test that passes before the implementation exists is a broken test. The shorthand `"use red/green TDD"` is understood by every major model. Builder must attach the red-phase test output (failing tests log) to the vault before writing implementation code.

**Test runner commands (Builder must use these exactly):**
| Layer | Run command | Output file |
|---|---|---|
| Python backend | `pytest backend/tests/ -v --tb=short 2>&1` | `/workspace/test_output.txt` |
| TypeScript frontend | `npx vitest run --reporter=verbose 2>&1` | `/workspace/test_output.txt` |
| Both | Backend first, then frontend; both must pass | Concatenated to single output |

**Red-phase vault contract:**
- Builder saves failing test output BEFORE any implementation: `vault.save(project_id, "4_app/red_phase.txt", failing_output)`
- `state.artifacts["red_phase_log"] = "4_app/red_phase.txt"` 
- Gate 3 check "sandbox run log attached" verifies this key exists in `state.artifacts`

> **Plan:** Agent reads `intake_summary.json` + vault artifacts. Output schema is a Pydantic model — not free text. Agent cannot proceed to Generate until schema validates.

> **Generate:** `tool_choice="required"` — Analyst calls `web_search`, Architect calls `read_file("api_spec.yaml")`, Builder calls `run_tests()`. No tool call = no answer. *(AH-2)*

> **Reflect:** Agent runs `CONSTITUTION.md` check — 4 principles, each answered Y/N with evidence. Any N → retry loop, not HITL gate. Free-form "review yourself" is replaced by structured boolean checklist. *(AH-3)*

> **Test:** Builder executes code in Docker sandbox. Real stderr fed back as retry context. Gate 3 is blocked until all tests pass in sandbox. *(AH-3)*

> **Within each stage, the agent runs its internal loop autonomously (up to 3 iterations). The human sees the STAGE result, not every iteration. *(Karpathy: "Review results in the morning.")*

> **At HITL Gate 3 (code review), the dashboard shows an actual GitHub PR diff, not a text summary. Human reviews code like a senior engineer. *(No Priors / Simon Last)*

```
Idea → [Intake: 15 Qs] → [Analyst]   → PRD.md          → Gate 0 ✅
                        → [Designer]  → DESIGN.md        → Gate 1 ✅
                        → [Architect] → architecture.md  → Gate 2 ✅
                        → [Builder]   → app/ + tests     → Gate 3 ✅ (PR diff shown)
                        → [Deployer]  → infra/ + staging → Gate 4 ✅ → 🎉 Live Azure URL
```

**Failure:** Any agent failure → retry ×3 → escalate to human. LangGraph checkpointing means pipeline always resumes from the last successful gate.

---

## 5. Memory: 2 Layers

> (Karpathy: "Context window = RAM — load only what's needed.") Layer 3 (cross-project knowledge base) is explicitly cut for v1. Zero value until 100 projects have shipped.

| Layer | Technology | Scope | Contents |
|---|---|---|---|
| **1 — Run state** | LangGraph + Pydantic + Redis | Ephemeral per run | Agent outputs, decisions, clarifications, error log |
| **2 — Project vault** | Markdown files (Azure Blob) | Persistent per project | Stage artifacts, approved versions, decision log |

Vault namespace: `/{user_id}/{project_id}/1_analysis/` … `5_infra/`

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

> **Redis config requirement:** Eviction policy must be `noeviction` (never evict checkpoints under memory pressure — pipeline errors explicitly instead). Checkpoint TTL: 30 days (expired projects cleaned up by weekly maintenance job). Azure Cache for Redis tier: **Basic C1** (1GB) for MVP; upgrade to Standard C1 (1GB + replica) for production.

**Redis memory pressure handling:**
- **Alert at 80%:** Azure Monitor alert fires when Redis memory > 800MB (Basic C1 = 1GB). Operator notified via PagerDuty.
- **Alert at 95%:** Pipeline intake paused — `POST /api/v1/agency/projects` returns `503 Service Unavailable` with message "Agency at capacity, try again in 1 hour."
- **Checkpoint write failure:** If `REDIS_OOM` error on checkpoint save, the current stage retries once after 60s (stale checkpoints may have expired). If retry fails, stage fails with `state.errors += ["Redis OOM — checkpoint write failed"]` and Gate shows the error. Pipeline does NOT proceed without a saved checkpoint.
- **Emergency runbook:** Scale Redis to C2 (2.5GB) via Terraform apply. Or manually: `redis-cli --scan --pattern "checkpoint:*" | head -100 | xargs redis-cli DEL` to purge oldest checkpoints.

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
    USING (user_id = current_setting('app.user_id')::UUID);
```

**⚠️ RLS requires `SET LOCAL` per transaction — FastAPI middleware is mandatory:**

```python
# FastAPI middleware stack order (MUST be registered in this order in main.py):
# 1. AuthMiddleware      → validates JWT, sets request.state.user_id (UUID)
# 2. RLSMiddleware       → reads request.state.user_id, sets PostgreSQL session variable
# DB: db = request.app.state.db  (AsyncEngine from SQLAlchemy, set at startup in lifespan())
# Library: SQLAlchemy 2.x async with asyncpg driver

# backend/middleware/rls.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RLSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = request.state.user_id   # set by JWT auth middleware upstream
        async with db.transaction():
            import uuid as _uuid
            _validated = str(_uuid.UUID(str(user_id)))  # raises ValueError if not a valid UUID
            await db.execute("SET LOCAL app.user_id = $1", _validated)
            # Never f-string interpolate user_id — validated UUID + parameterized query prevents injection
            response = await call_next(request)
        return response
```

> **Without this middleware, `current_setting('app.user_id')` returns empty string, RLS policy evaluates False, and ALL rows are hidden (silent data loss) or ALL rows are returned (data leak depending on policy direction).** Both are production failures. RLS middleware must have its own integration test.

> **⚠️ PgBouncer requirement:** If PgBouncer is used for connection pooling, it MUST be configured in **session mode** (`pool_mode = session`). In transaction mode, `SET LOCAL` is reset when the connection returns to the pool — RLS policy then evaluates against an empty user_id, silently hiding all rows (data loss) or showing all rows (data leak depending on policy direction). Session mode is required. Azure Database for PostgreSQL Flexible Server supports direct connections without PgBouncer as a simpler v1 alternative (max_connections=~100 sufficient for MVP scale).

- Vault files → `/{user_id}/{project_id}/` in Azure Blob (per-user SAS tokens, not shared connection string)
- LangGraph checkpoints → `thread_id = project_id` in Redis  
- GitHub repos → `{user_slug}-{project_slug}` (collision-check before create) | Azure resources → `rg-{project_id}`  

**Docker sandbox — Azure Container Instances (ACI), NOT ACA (Engineer + DevOps fix):**

> ⚠️ Azure Container Apps does NOT support Docker-in-Docker (no privileged mode, no socket access). Builder invokes **separate ephemeral ACI instances** per sandbox run via Azure SDK. This is the only correct approach.

**Code injection into sandbox:**
```python
# Builder creates a tar archive of generated code and streams it into a fresh ACI instance
# Flow: zip code → upload to Azure Blob → ACI mounts blob as volume at /workspace
# ACI env: WORKSPACE=/workspace, timeout=120s, no network egress
```

**Output retrieval:**
```python
# ACI writes test output to /workspace/test_output.txt + /workspace/exit_code.txt
# Builder polls ACI status → on completion, downloads output file from Blob
# stdout/stderr captured by ACI and available via Azure SDK ACI log API as fallback
```

**Phase toggle (build vs verify):**
- **Build phase**: ACI with outbound network allowed (npm install / pip install from allowlist)
- **Verify phase**: Same container, `--restart=Never`, network policy `deny-all` via ACI subnet NSG
- Builder runs 2 ACI calls per iteration: (1) build+install, (2) verify execution

**Resource spec:** 1 vCPU, 1GB RAM, 120s timeout, auto-deleted on completion (ACI `--restart=Never`)
**Cost:** ~$0.10-0.30 per Builder stage (3-5 sandbox runs × ~$0.05/run)
**ACI auth:** Agency Managed Identity with `Contributor` role on ACI resource group
**Cleanup:** ACI instance auto-deletes on `--restart=Never` + `terminationGracePeriodSeconds: 0`

**`model_registry.yml` write protection:**
- File is Git-tracked; agents have **read-only** access at runtime (loaded once at startup)
- No runtime code path writes to it — agents cannot self-upgrade models
- Evolution System (§13, Phase 4+) proposes model changes as GitHub PRs, merged only by human

### 6b. Model-Agnostic Design

> **Why model-agnostic?** Models improve monthly. Claude 4, GPT-5, Gemini 3 will all outperform today's models on specific tasks. The agency must swap models via config change, not code change.

**`backend/llm/model_registry.yml`** — single source of truth for all models:

```yaml
models:
  claude_sonnet:
    name: "claude-3-7-sonnet-20250219"
    status: production        # production | staging | deprecated
    primary_tasks: [analyst, architect, builder]
    fallback: gpt_4o
    cost_per_mtok: 0.003
    capabilities: [structured_output, tool_use, vision]
    benchmark_score: 0.89
    last_benchmarked: "2026-03-01"

  gemini_25_pro:
    name: "google/gemini-2.5-pro"
    status: production
    primary_tasks: [designer]
    fallback: claude_sonnet
    capabilities: [structured_output, tool_use, vision, image_generation]

  gpt_4o:
    name: "openai/gpt-4o"
    status: fallback
    primary_tasks: []
    capabilities: [structured_output, tool_use]

  # New model dropped by provider → add here + set status: staging → run benchmarks
```

**`ModelRouter`** — `LLMPort` implementation that reads the registry at startup:

```python
class ModelRouter(LLMPort):
    """Reads model_registry.yml. Agents call self.llm.structured_call() — no provider knowledge."""
    def __init__(self, registry_path: str, task: str):
        registry = yaml.safe_load(open(registry_path))
        model_key = self._find_primary(registry, task)  # finds status=production for this task
        self.primary = self._build_adapter(registry["models"][model_key])
        self.fallback = self._build_adapter(registry["models"][registry["models"][model_key]["fallback"]])

    async def structured_call(self, prompt, output_schema, **kwargs):
        try: return await self.primary.structured_call(prompt, output_schema, **kwargs)
        except (RateLimitError, ProviderError): return await self.fallback.structured_call(...)

    def _build_adapter(self, cfg) -> LLMPort:
        # Returns AnthropicLLMAdapter, OpenAILLMAdapter, or GeminiLLMAdapter
        # based on cfg["name"] prefix — agents never see this
        ...
```

# Correct matching + caching pattern (fixes Engineer findings #6, #7):

_registry_cache: dict | None = None  # module-level singleton cache

class ModelRouter(LLMPort):
    def __init__(self, registry_path: str, task: str):
        global _registry_cache
        if _registry_cache is None:
            with open(registry_path) as f:
                _registry_cache = yaml.safe_load(f)
        self._registry = _registry_cache
        self._task = task
        self._adapter = self._build_adapter(self._find_primary())

    def _find_primary(self) -> dict:
        candidates = [
            m for m in self._registry["models"].values()
            if self._task in m.get("primary_tasks", [])   # string 'in' list — exact match
            and m.get("status") == "active"
        ]
        if not candidates:
            raise ValueError(f"No active model for task '{self._task}'. Check model_registry.yml.")
        return max(candidates, key=lambda m: m.get("benchmark_score", 0))  # highest score wins

    def _build_adapter(self, cfg: dict):
        name = cfg["name"]
        if name.startswith("claude"):    return AnthropicAdapter(cfg)
        elif name.startswith("gpt"):     return OpenAIAdapter(cfg)
        elif name.startswith("gemini"):  return GeminiAdapter(cfg)
        else: raise ValueError(f"Unknown model prefix in registry: {name}")

**Prompt portability rules** (enforced by `skills/prompt-style.md`):
- Use generic section headers (`## Task`, `## Context`, `## Output`) — not Anthropic XML tags
- Never use provider-specific syntax (no `<claude_thinking>`, no OpenAI `{{}}` templates)
- Test every system prompt against ≥2 providers in CI before merge

---

## 7. Human-in-the-Loop Design

> (Willison: "Vibe coding is fast and irresponsible.") Agents over-produce complexity. Human judgment at every gate is the scoping mechanism.

> **Gate Queue in the AMC:** All open gates across all projects are surfaced in the Agency Management Console Gate Queue (§21, Screen 3). Sam receives a browser notification + optional email when a gate opens. The gate badge count in the AMC nav always shows total pending approvals.

### Gate Checklist Model

**Approve is disabled until all critical questions are answered YES or DEFER.** DEFER = "I accept this risk and will address it post-launch." Items marked DEFER are logged to the project vault as known technical debt.

Each gate has **4 critical questions** (full text in `skills/gate-checklists.md`). Previous 7-question lists are reduced — all 7 remain in the skill file as guidance, but only 4 are gate-blocking:

| Gate | After | 4 Critical Questions (approval blocks on these) |
|---|---|---|
| **Gate 0** | Analyst | Problem specific & measurable? Users named? Scope bounded with explicit out-of-scope? Budget-to-infra feasibility confirmed? |
| **Gate 1** | Designer | Design solves stated user problem? Every MVP feature has a screen? Edge cases (errors/empty states) shown? Mobile layout considered? |
| **Gate 2** | Architect | Data model complete + all relations defined? Auth/authz mechanism explicit? Estimated infra cost within stated budget? `terraform validate` dry-run passed? |
| **Gate 3** | Builder | App boots in Docker sandbox — **sandbox run log attached to vault** (not claimed, proven)? Tests verify behaviour (not just coverage)? No hardcoded secrets? OWASP checklist passed? **PR description reviewed by human** (not just LLM-generated text)? |
| **Gate 4** | Deployer | Staging stable for 1h+? Rollback procedure documented? DB migrations reversible? Monitoring active and alert routing confirmed? |

> **Anti-pattern to avoid (Willison):** Never advance Gate 3 on code you haven't personally run. The sandbox run log is the evidence. Reviewing the PR description (which agents auto-generate convincingly) is your responsibility — rude to ask a reviewer to read text you haven't validated.

### Plain-Language Gate Guide (for non-technical users)

Gate 1 and Gate 4 are self-explanatory (look at mockups; check if app works). Gates 2 and 3 need translation:

**Gate 2 — Architecture Review (what Sam actually checks):**
> You are NOT reviewing technical diagrams. You are answering 3 simple questions:
> 1. 💰 **"The estimated monthly Azure cost is $X. Is that within my budget?"** — If yes, approve. If no, click "Give Notes" and say your budget.
> 2. 📋 **"Does the list of features match what I asked for?"** — The architecture doc lists every feature. Scan the list. If something is missing or wrong, say so.
> 3. 🔐 **"Does the login/access model match my needs?"** — "Public URL", "invite only", "login required", or "internal only". Check this matches your intake answer.
> Everything else (data model, RLS, API contracts) is the Architect's job — trust it unless the cost or features are wrong.

**Gate 3 — Code Review (what Sam actually checks):**
> You are NOT reviewing Python or TypeScript code. You are checking one thing:
> 1. 🧪 **"Did all the automated tests pass?"** — The gate shows a test summary. Green = all pass. Red = there are failures. If red, click "Re-run Stage" and wait. Do not approve a red test run.
> The GitHub PR link is for your developer (if you have one) to review. If you don't have a developer, approving with all tests green is sufficient.

### Approval UI

```
┌────────────────────────────────────────────────────────────────┐
│ 🤖 Agency           [Project: TaskTracker]   [Gate 2 of 5]     │
├────────────────────────────────────────────────────────────────┤
│  📐 GATE 2 COMPLETE: Architecture Ready                        │
│  PostgreSQL + FastAPI + Next.js. Auth via Clerk.               │
│  💰 Estimated cost so far: $0.34 | Est. monthly infra: $45     │
│  ⏱️  Time elapsed: 22 min | Est. remaining: ~40 min            │
│  [📄 architecture.md]  [📄 api_spec.yaml]                      │
│                                                                │
│  REVIEWER CHECKLIST  (complete all 4 to unlock Approve)       │
│  ☐ 2.1 Data model complete + all relations defined?           │
│  ☐ 2.2 Auth/authz mechanism explicitly designed?              │
│  ☐ 2.3 Est. infra cost ($45/mo) within your budget ($50)?     │
│  ☐ 2.4 terraform validate passed (shown below)?               │
│                                                                │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ ✅ Approve (0/4) │  │ ✏️ Give Notes │  │ 🔄 Re-run Stage  │ │
│  └──────────────────┘  └──────────────┘  └──────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

**Gate actions:** Approve (advance + checkpoint, requires 4/4 YES or DEFER) | Give Notes (links to failed Q → agent revises that specific item) | Re-run (clean retry) | Ask (inline clarification) | Stop (pause indefinitely)

**UX rules:**
- Estimated monthly infra cost shown at every gate (not just at the end)
- Stage elapsed time + remaining estimate shown at every gate
- DEFER option available on any checklist item — deferred items logged to `decisions/` vault folder as technical debt
- "24h staging stability" (original Gate 4) reduced to 1h to avoid user abandonment; extended stability run is available as opt-in

**DEFER behavior:**
- DEFER = "I accept this for now and will address it post-launch." The gate **advances immediately** — the pipeline continues.
- DEFER'd items are logged to `state.decisions` with `{"gate": N, "action": "deferred", "item": "checklist item text", "timestamp": ...}`.
- DEFER'd items surface in the Gate 4 (final) review as a "Deferred Items" section — Sam sees everything they deferred before going live.
- DEFER does NOT reset the 24h timeout. If Sam neither approves, defers, nor gives notes within 24h, the gate times out and the pipeline pauses (not fails).
- A paused pipeline can be resumed from the AMC at any time by opening the gate and taking an action.

Any agent can call `ask_human()` mid-task for significant trade-offs — not only at gates. No agent makes irreversible infrastructure decisions without explicit human approval.

---

## 8. BaseAgent Contract

> **Why a shared contract?** (Anthropic) The orchestrator never imports individual agents — only names. Every agent has the same interface, making the system trivially extensible.

```python
class BaseAgent(ABC):
    name: str; stage: str
    skills: list[str]   # skill filenames loaded into context per run()
    _base_skills: ClassVar[list[str]] = ["constitution.md", "critique.md"]

    def __init__(
        self, project_id: str,
        llm: LLMPort,      # injected — never import Anthropic/OpenAI directly
        vault: VaultPort,  # injected — never import Azure/S3 directly
        tools: ToolPort,   # injected — never import Docker/subprocess directly
        human: HumanPort,  # injected — never import WebSocket directly
        logger: LoggingPort,
    ): ...

    run(state: ProjectState) -> ProjectState       # abstract; must NOT raise
    ask_human(state, question, context, options)   # → HumanPort.ask()
    record_decision(state, question, chosen, rationale)  # → state + VaultPort
    emit(state, content) -> ProjectState           # → HumanPort.notify()
    fail(state, error) -> ProjectState             # → LoggingPort + error log
    load_skills() -> str                           # joins skill files into context
```

**Consistency rules (enforced by CI):**
1. `run()` is always `(self, state: ProjectState) -> ProjectState` — never raises
2. All LLM calls use `self.llm.structured_call()` with a Pydantic `output_schema`
3. Agents write to vault AND state — not one or the other
4. `import-linter` CI rule: `agents/` may not import from `adapters/` — only from `core/ports`
5. AH-2 enforcement: `@requires_tool_call` decorator on `structured_call()` — raises `ToolCallMissingError` if LLM returns text without using a tool; auto-retries once, then calls `fail()`

```python
# backend/core/decorators.py
def requires_tool_call(fn):
    """Enforces AH-2: no answer without a tool call first."""
    async def wrapper(self, prompt, output_schema, *args, **kwargs):
        kwargs["tool_choice"] = "required"   # set before expanding — avoids duplicate keyword SyntaxError
        result = await fn(self, prompt, output_schema, *args, **kwargs)
        if not result.tool_calls:
            raise ToolCallMissingError(f"{self.name}: returned text without tool call")
        return result
    return wrapper
```

```python
# backend/orchestrator/registry.py — single source of truth
AGENT_REGISTRY = {
    "analyst": AnalystAgent, "designer": DesignerAgent,
    "architect": ArchitectAgent, "builder": BuilderAgent, "deployer": DeployerAgent,
}
# ⚠️ Performance: Agent instances are singletons — create once at app startup, inject per call.
# The DI container (e.g., dependency_injector or simple module-level dict) holds pre-built instances.
# make_node() below is simplified — production version receives pre-built agent from container, not "new".
_agent_instances: dict[str, BaseAgent] = {}  # populated at FastAPI startup

def get_or_create_agent(name: str, ports: dict) -> BaseAgent:
    if name not in _agent_instances:
        _agent_instances[name] = AGENT_REGISTRY[name](**ports)
    return _agent_instances[name]

def make_node(name: str):   # LangGraph node factory — injects ports from DI container
    def fn(state):
        agent = AGENT_REGISTRY[name](
            project_id=state.meta.project_id,
            llm=ModelRouter("model_registry.yml", task=name),
            vault=AzureBlobVaultAdapter(...),
            tools=RealToolAdapter(...),
            human=WebSocketHumanAdapter(...),
            logger=LangSmithLogger(...),
        )
        return agent.run(state)
    fn.__name__ = name; return fn
```

---

## 9. Cost Controls & Operational Resilience

> **Why from day 1?** (Harper Reed + Anthropic) Cost controls added in phase 5 are always too late. They need to be load-bearing architecture from the start.

> **Realistic baseline:** A simple task tracker app runs in ~2h, 18 LLM calls, 295K tokens, ~$3 LLM + $5-15 Azure = **$8-18 total per project.** Scale from there.

> **Note:** Cost tracking operates at 3 levels: (1) **LLM cost** tracked per-call via LiteLLM router tags; (2) **Infrastructure cost** estimated by Infracost before Gate 2 and after Gate 4; (3) **UI display** shown to Sam at every gate. These are complementary, not duplicate.

**Cost aggregation pipeline:**
1. **LLM per-call:** LiteLLM callback logs `{project_id, model, tokens_in, tokens_out, cost_usd, timestamp}` to PostgreSQL `llm_calls` table on every call.
2. **Per-stage sum:** At each gate, query: `SELECT SUM(cost_usd) FROM llm_calls WHERE project_id = $1` → stored in `ProjectState.meta.usd_spent`.
3. **Infra estimate:** Deployer runs `infracost breakdown` → result stored in `ProjectState.meta.monthly_infra_estimate` (monthly, not per-project).
4. **AMC display:** `ProjectSummary.cost_usd = meta.usd_spent` (LLM only). AMC UI shows both: "$3.42 LLM + $5.00/mo Azure" — two separate numbers, never summed into one misleading total.
5. **Fallback:** If LiteLLM callback fails, cost defaults to token-count estimate: `(tokens_in * model_input_price + tokens_out * model_output_price)`. If Infracost unavailable, show "Azure cost: estimating..." with last known value.

| Control | Mechanism |
|---|---|
| **Per-stage token budget** | Hard limit in `ProjectState`. Agent must summarize + stop if exceeded. |
| **Context window reservation** | Reserve 25% of context for output. Trigger auto-summarize at 60% fill. Never trim `original_requirement`. |
| **Budget exceeded → escalate** | Agent calls `ask_human()` with cost summary + continue/stop options. |
| **Hard project budget cap** | User sets USD limit at intake. Pipeline halts if exceeded — no silent overruns. |
| **Infracost integration** | Deployer calls `infracost breakdown --path=infra/terraform/ --format=json` before Gate 2. Actual cost from Terraform plan — not hardcoded. Result stored as `state.artifacts["infra_cost"]`. AH-1 compliance: cost estimate is tool-grounded, not LLM-hallucinated. Infracost CLI installed in agency Docker image; `INFRACOST_API_KEY` in Key Vault. |
| **Rate limit circuit breaker** | Token bucket per model. If primary + fallback both rate-limited, pipeline pauses + notifies user rather than silently retrying. |
| **Gate cost display** | LLM cost + est. monthly infra shown at every gate (see §7 UI). |
| **Model routing** | `ModelRouter` routes to cheaper fallback if primary rate-limits — not only on error. |
| **Cost tracking per project** | Every LiteLLM call tagged with `project_id` + `agent_name` + `stage`. |
| **Azure quota check** | Deployer runs `az quota list` before provisioning. If quota insufficient, calls `ask_human()` with escalation path. |
| **Zero-tolerance refactoring** | Builder never ships code with known smells (long functions, naming drift, dead code). These fixes cost one agent call — no longer a time tradeoff. |

> **(Willison: Better code)** With agents, "conceptually simple but time-consuming" refactors have zero cost. Builder must flag and fix any of these before Gate 3, not defer them: API naming inconsistencies, file over 300 lines that should be split, duplicate functionality, missing error handling. Use async background agents for large-scale refactors across many files — evaluate in PR, land if good, prompt-and-retry if almost there, throw away if bad.

```python
# Enforced in BaseAgent.run() wrapper
if state.meta.tokens_used > state.meta.token_budget:
    return self.ask_human(state,
        question="Token budget exceeded. How do you want to proceed?",
        context=f"Used {state.meta.tokens_used} of {state.meta.token_budget} tokens.",
        options=["Extend budget by 50%", "Summarize and stop", "Abort stage"],
    )
```

**Day-1 failure modes to have mitigated before launch** (failure-modes-analyst findings):
1. Docker sandbox startup latency (30-120s per run) — pre-warm containers, show timer in UI
2. Dependency install network failure — cache common packages in base image; never `--network=none` during build
3. RLS `SET LOCAL` missing — enforced by `RLSMiddleware` + integration test (see §6)
4. WebSocket disconnect drops gate state — gate state persisted in Redis; reconnect restores it (see §8 HumanPort spec)
5. GitHub repo name collision — pre-check with `GET /repos/{owner}/{name}` before creation
6. Azure provisioning time (15-45 min) — show progress bar + ETA; do not let UI time out

## 9b. Evals & Agent Reliability

> **Why evals?** (Andrew Ng) "The biggest predictor of a team's progress is their diligence in setting up systematic evaluations and doing proper error analysis." Don't tweak prompts endlessly — measure first.
> (OpenAI Harness Engineering) Agent legibility is as important as human readability. Logs must be structured for agent re-reading.

### Every agent has an eval suite
Each agent in `backend/agents/` has a corresponding `backend/evals/{agent_name}/` folder:
- `cases.jsonl` — input→expected_output pairs (dataset-driven, like OpenAI Evals)
- `grader.py` — automated output grader (checks schema, required fields, checklist items)
- `run_evals.sh` — CI command: `pytest evals/ --agent=analyst` etc.

### Eval structure (OpenAI Evals format)
- Input: a `ProjectState` snapshot at stage entry
- Output: the `ProjectState` diff produced by the agent
- Grade: pass/fail per checklist item (our existing binary checklist from critic)
- CI fails if any eval case regresses

### Agent legibility (OpenAI Harness Engineering)
Every agent action writes a machine-legible log entry to the vault:
- Structured JSON: `{timestamp, agent, action, input_summary, output_summary, decision, tokens_used}`
- Future agents (or the same agent on retry) can read this log to understand what was tried
- Dashboard renders these as a human-readable timeline

### PLAN.md in every generated repo (OpenAI Harness Engineering)
The Architect agent commits a `PLAN.md` to the root of every generated GitHub repo. This file:
- Documents the architectural decisions (why this DB, why this auth strategy)
- Lists the acceptance criteria the Builder must satisfy
- Is read by the Builder and QA agents on each run (agents read their own instructions from the repo)

### Reflection prompt structure (Andrew Ng)
The `critique.md` skill is upgraded from a generic review to a structured reflection:
```
After generating output, answer these questions:
1. Does my output fully address the input requirements? (Y/N + explanation)
2. What's the weakest part of what I produced? (1 sentence)
3. What would I do differently with 2x the token budget? (1 sentence)
4. Are there any assumptions I made that the human should validate? (list)
```
Only output that answers "Yes" to Q1 AND has no critical assumptions unvalidated proceeds to the HITL gate.

---

## 10. Build Phases

> **Why 4 phases, not 6?** (Karpathy: "Start minimal.") Original plan had 6 phases including a cross-project knowledge base before the product was even deployed end-to-end. Phases now ordered strictly by value delivered.

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
├── AGENTS.md                      ← agency reads its own instructions (OpenAI Harness pattern)
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── core/
│   │   ├── ports.py               ← 5 abstract ports (LLMPort, VaultPort, ToolPort, HumanPort, LoggingPort)
│   │   ├── state.py               ← ProjectState + ProjectMeta Pydantic models
│   │   └── domain/                ← DDD aggregates: ProjectAggregate, AgentRunAggregate, SkillAggregate
│   ├── agents/                    ← Domain layer; imports only from core/ports
│   │   ├── base.py
│   │   ├── analyst.py
│   │   ├── designer.py
│   │   ├── architect.py
│   │   ├── builder.py
│   │   └── deployer.py
│   ├── adapters/                  ← Concrete implementations; never imported by agents
│   │   ├── llm/
│   │   │   ├── anthropic.py       ← AnthropicLLMAdapter(LLMPort)
│   │   │   ├── openai.py          ← OpenAILLMAdapter(LLMPort)
│   │   │   ├── gemini.py          ← GeminiLLMAdapter(LLMPort)
│   │   │   ├── router.py          ← ModelRouter(LLMPort) — reads model_registry.yml
│   │   │   └── mock.py            ← MockLLM(LLMPort) — for unit tests
│   │   ├── vault/
│   │   │   ├── azure_blob.py      ← AzureBlobVaultAdapter(VaultPort)
│   │   │   └── mock.py            ← MockVault(VaultPort) — for unit tests
│   │   ├── human/
│   │   │   ├── websocket.py       ← WebSocketHumanAdapter(HumanPort) — JWT-validated, project_id-scoped
│   │   │   └── mock.py            ← MockHuman(HumanPort) — for unit tests
│   │   └── tools/
│   │       ├── real.py            ← RealToolAdapter(ToolPort) — web_search, code_executor
│   │       └── mock.py            ← MockTool(ToolPort) — for unit tests
│   ├── skills/
│   │   ├── critique.md
│   │   ├── constitution.md        ← AH-1..4 rules (loaded by all agents)
│   │   ├── tdd.md
│   │   ├── design-system.md
│   │   ├── terraform.md
│   │   ├── security-checklist.md
│   │   ├── api-contract.md
│   │   ├── prompt-style.md        ← portability rules: avoid vendor idioms, reasoning headers, etc.
│   │   ├── gate-checklists.md     ← 5 gates × 4 blocking + 3 advisory YES/NO/DEFER questions
│   │   └── prompts/               ← versioned system prompts
│   │       ├── _schema.yaml       ← registry: current/staging/previous per agent
│   │       ├── analyst/system-v3.2.md
│   │       └── builder/system-v2.8.md
│   ├── llm/
│   │   └── model_registry.yml     ← all models: status, tasks, capabilities, benchmark_score (READ-ONLY at runtime)
│   ├── orchestrator/
│   │   ├── graph.py
│   │   ├── registry.py            ← AGENT_REGISTRY + make_node() factory (injects ports)
│   │   └── checkpointer.py
│   ├── evolution/                 ← ⚠️ DEFERRED (Phase 4+, need 10+ shipped projects first)
│   │   ├── prompt_promoter.py     ← DO NOT implement in Phase 1-3
│   │   ├── skill_analyzer.py
│   │   ├── model_benchmarker.py
│   │   ├── research_agent.py
│   │   ├── drift_detector.py
│   │   └── ooda_orchestrator.py
│   ├── evals/                     ← Per-agent eval suites
│   │   ├── analyst/cases.jsonl
│   │   ├── builder/cases.jsonl
│   │   └── */grader.py
│   └── api/
│       ├── projects.py
│       ├── chat.py
│       └── approvals.py
├── frontend/
│   ├── app/projects/[id]/
│   └── components/
│       ├── ChatPanel.tsx
│       ├── ApprovalGate.tsx        ← renders 4-blocking + 3-advisory checklist per gate with DEFER option
│       ├── ArtifactViewer.tsx
│       ├── CostDisplay.tsx         ← shows est. LLM cost + est. monthly infra at every gate
│       └── PipelineProgress.tsx    ← stage name + elapsed time + est. remaining
├── infra/terraform/
└── .github/workflows/
    ├── ci.yml                     ← runs evals + import-linter + skill validator
    ├── deploy.yml
    ├── prompt-promotion.yml       ← ⚠️ DEFERRED Phase 4+ — do not implement in v1
    └── model-benchmark.yml        ← on-demand: benchmarks new models
```

---

## 12. What We Are NOT Building Yet

> *(Karpathy: "Start minimal, earn complexity.")* These are explicit deferrals, not forgotten features.

| Cut Item | Why deferred |
|---|---|
| **Cross-project knowledge base (Layer 3 memory)** | Needs 100+ projects to be useful. Premature optimization. |
| **Parallel sub-agents** (Frontend ∥ Backend ∥ DB) | Adds coordination complexity before the linear path is proven. |
| **Perplexity Sonar / real-time web search** | Tavily is sufficient for v1. Adds another API dependency. |
| **SWE-agent-style iterative bug-fix loops** | Builder's TDD loop + max-3-retry guard covers 90% of cases. |
| **Voice input on dashboard** | Nice-to-have. Text is sufficient for v1 and easier to test. |
| **Agency Evolution System (§13)** | Phase 4+. Needs 10+ shipped projects + working evals before OODA loop is useful. |

---

## 13. Agency Evolution System

> ⚠️ **Deferred to Phase 4+.** Full implementation requires 10+ shipped projects to accumulate skill-improvement data. Design is complete; build when project volume exists.

> **Why?** The field moves monthly.Without a self-improvement loop, the agency is frozen in time. Every model release, paper, and practice that improves quality should flow into the agency automatically — with human approval at each step.

### OODA Loop (Boyd's framework adapted for AI agencies)

```
OBSERVE (daily)          ORIENT (weekly)          DECIDE (weekly)          ACT (weekly)
─────────────────        ─────────────────        ─────────────────        ─────────────
• Agent telemetry        • Cluster failures        • Propose new           • Create GitHub PR
• Skill failure logs     • Root cause analysis     prompt versions         • Run eval suite
• Model performance      • Drift detection         • Propose skill         • Human approval
• Error patterns         • New models released     file edits                required
• Research papers        • Research findings       • Benchmark new         • Merge → deploy
  (arXiv, HN, GitHub)                              models                  • Cycle repeats
```

### 6 Evolution Components

| Component | Cadence | What it does | Guardrail |
|---|---|---|---|
| **Prompt Promoter** | Weekly | Runs evals on `*-candidate.md` prompts; promotes if score > threshold | Blocked if any eval regresses vs. baseline |
| **Skill Analyzer** | Weekly | Clusters agent failures; proposes edits to `skills/*.md` | Only fires if failure rate > 5% |
| **Model Benchmarker** | On new release | Benchmarks new model across all 5 agent tasks; promotes if better | Blocked if any task regresses > 2% |
| **Research Agent** | Weekly | Searches arXiv/HN/GitHub for "agentic coding" papers; extracts patterns | Filters by relevance score; human review |
| **Drift Detector** | Daily | Monitors agent eval scores; alerts if performance degrades > 10% | Slack/dashboard alert + investigation log |
| **OODA Orchestrator** | Daily/Weekly | Coordinates all phases; aggregates proposals into single approval queue | All proposals as GitHub PRs; one HITL gate |

### Prompt versioning schema

```
backend/skills/prompts/
├── _schema.yaml              ← registry: current/staging/previous version per agent
├── analyst/
│   ├── system-v3.2.md        ← PROMOTED (live)
│   ├── system-v3.3-candidate.md ← STAGING (under eval)
│   └── CHANGELOG.md
└── builder/
    ├── system-v2.8.md        ← PROMOTED
    └── system-v2.9-candidate.md ← STAGING
```

Every evolution proposal surfaces as a **GitHub PR** with eval results attached. Human sees: current score vs. candidate score vs. threshold. One click = approve + deploy. The agency improves without requiring re-engineering — but never without human sign-off.

### 13f. Compound Step (After Every Shipped Project)

> **(Willison + Every.to Compound Engineering)** The compound step runs automatically after Gate 4 approval. It extracts generalizable patterns from the just-completed project and files PRs to update skill files.

| Compound Action | What it does |
|---|---|
| **Pattern extraction** | Deployer reviews project vault; identifies solutions that solved hard problems (e.g., a specific Terraform pattern, a working auth flow) |
| **Skill PR** | Files a PR: `skills/{pattern-name}.md` with the working code example (not prose — actual running code) |
| **Retrospective note** | Appends one-paragraph summary to `decisions/retrospective.md` in project vault: what worked, what to do differently |
| **Failure note** | If any gate was rejected-and-revised, documents the root cause in `decisions/failures.md` |

The compound step is what makes the agency get smarter over time — each project adds proven working examples to the skill hoard that all future agents can recombine.

---

## 14. Prior Art, References & What We Borrow From Each

> *"Good artists borrow, great artists steal." Standing on shoulders of giants.*

| Project / Source | Stars / Reach | What We Borrow |
|---|---|---|
| **OpenClaw** | 182k★ GitHub | Markdown-as-config (SOUL.md, MEMORY.md pattern); skills plugin architecture |
| **MetaGPT** | 65k★ GitHub | Role-based SOP structure; agent prompt templates per role |
| **AutoGen** | 40k★ GitHub | Docker sandbox code execution pattern; secure subprocess isolation |
| **LangGraph** | Official | Our orchestration backbone; HITL interrupt nodes; Redis checkpointing |
| **OpenAI Evals** | Official | Eval harness format (cases.jsonl + grader.py); CI regression testing |
| **OpenAI Harness Engineering** | openai.com | Scaffolding > scripting; PLAN.md in repo; machine-legible logs |
| **Andrew Ng / DeepLearning.AI** | 7M+ learners | 4 agentic patterns (Plan→Act→Reflect→Collaborate); evals-first methodology |
| **Andrej Karpathy** | YC AI School | Loopy Era loop; autonomous iteration within stage (review morning, not each step) |
| **Simon Willison** | simonwillison.net | TDD as agent safety net; "vibe coding = irresponsible"; human judgment for scoping |
| **Harper Reed / Paperclip** | harper.blog | Human = board of directors; cost controls from day 1; checkpointing |
| **No Priors (Karpathy ep.)** | Podcast | Overnight autonomous loops; human reviews PR diffs, not text summaries |
| **No Priors (Simon Last ep.)** | Podcast | Managing agent swarms; HITL gates as PR review, not project manager approval |
| **e2b-dev/awesome-ai-agents** | 17k★ GitHub | Landscape awareness; agent capability benchmarking |
| **Willison: Agentic Engineering Patterns** | simonwillison.net | Red/green TDD; Hoard pattern (skills-as-working-code); Anti-pattern: unreviewed PRs; Compound Engineering step; Zero-tolerance refactoring; Subagents for context management |
| **Every.to Compound Engineering** | every.to | End every project with compound step: document what worked → update agent instructions → compounds over time |
| **Willison: Subagents** | simonwillison.net | Fresh context window per subagent; parallel subagents for independent files; specialist roles (reviewer, test runner, debugger); don't go overboard — 5 agents validated |

### Key Differentiators vs. These Projects

| Feature | This System | MetaGPT | CrewAI | OpenClaw | AutoGen |
|---|---|---|---|---|---|
| Fixed target stack (Next.js + FastAPI) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Azure deployment end-to-end | ✅ | ❌ | ❌ | ❌ | ❌ |
| Human reviews actual GitHub PRs at gate | ✅ | ❌ | ❌ | ❌ | ❌ |
| Skills-as-markdown (not hardcoded) | ✅ | ❌ | Partial | ✅ | ❌ |
| Per-agent eval suites in CI | ✅ | ❌ | ❌ | ❌ | Partial |
| Cost controls with hard budget cap | ✅ | ❌ | ❌ | ❌ | ❌ |
| PLAN.md committed to generated repo | ✅ | Partial | ❌ | ❌ | ❌ |


---

## 15. Known Risks, Open Decisions & What Could Go Wrong

> This section is the output of a 5-critic adversarial review (security audit, first-principles critique, failure-modes analysis, complexity review, and non-technical user journey). Every item here is a real risk with a concrete mitigation path. Items without a mitigation are explicitly flagged.

### 15a. Confirmed Architectural Risks

| Risk | Severity | Mitigation in Plan |
|---|---|---|
| **RLS `SET LOCAL` not called → data leak** | 🔴 HIGH | `RLSMiddleware` + integration test (§6) |
| **WebSocket gate has no auth → user A approves user B** | 🔴 HIGH | JWT validation + project_id scoping on connection (§8 HumanPort spec) |
| **Docker sandbox network undefined → sandbox escape** | 🔴 HIGH | `--network=none` execution + allowlist build phase (§6) |
| **`model_registry.yml` writable at runtime → self-upgrade** | 🔴 HIGH | Read-only at runtime, Git-tracked, Evolution System uses PRs (§6b) |
| **Context overflow on complex projects** | 🟡 MEDIUM | 25% output reserve + auto-summarize at 60% + stream artifacts (§9) |
| **Rate limit cascade (both models hit)** | 🟡 MEDIUM | Circuit breaker pauses pipeline + notifies user (§9) |
| **JWT expiry mid-pipeline (1h token, 2h Builder stage)** | 🟡 MEDIUM | Refresh token endpoint; Builder stage re-authenticates on token expiry |
| **PR body injection in Evolution System** | 🟡 MEDIUM | Sanitize eval output before PR body creation (Phase 4+, deferred) |
| **Terraform state corruption** | 🟡 MEDIUM | Remote state in Azure Blob + state locking; runbook for manual recovery |
| **Azure provisioning quota exhausted** | 🟡 MEDIUM | Pre-flight `az quota list`; warn user; rollback if apply fails (§9) |
| **GitHub repo name collision** | 🟡 MEDIUM | Pre-flight `GET /repos/{owner}/{name}` before create |
| **Docker startup latency 30-120s per sandbox run** | 🟡 MEDIUM | Show elapsed timer; pre-warm containers; happy path has 3 sandbox runs |
| **Blob vault uses shared connection string** | 🟡 MEDIUM | Per-user SAS tokens (not shared key) for all vault operations |
| **WebSocket disconnect drops gate state** | 🟡 MEDIUM | Gate state persisted in Redis; reconnect restores pending question |

### 15f. Business & Competitive Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Bolt.new ships Azure deploy** | 🔴 HIGH | Deepen audit trail + compliance moat; target enterprise before this happens |
| **HITL gates rubber-stamped by non-technical users** | 🔴 HIGH | Gates 2-3 reframed for Sam (cost check + test results only); Gates 0, 1, 4 are meaningful for all users |
| **Fixed stack breaks on Next.js major version** | 🟡 MEDIUM | Monthly CI matrix against latest Next.js; skill PR pipeline for framework upgrades |
| **Napkin AI / Google Stitch ToS violation** | 🟡 MEDIUM | ToS audit pre-launch; fallbacks already specced |
| **Unit economics at $4/project not venture-scale** | 🟡 MEDIUM | Enterprise tier (Phase 3) is the path to 60%+ margin; v1 is about proving PMF not margin |
| **No GTM — users don't find Sam** | 🟡 MEDIUM | Content-led Phase 1; demo videos for 5 app types; partner integrations Phase 2 |
| **Legal exposure — no ToS before launch** | 🔴 HIGH | §18 pre-launch legal checklist; no paid users before ToS drafted |

### 15b. Architectural Decision Log (Recommendations Locked)

| Decision | Option A (current plan) | Option B | Recommended |
|---|---|---|---|
| **Orchestration** | LangGraph (HITL interrupt nodes, Redis checkpointing) | Celery/RQ (simpler linear queue, less state overhead) | **LangGraph** — HITL + parallel branches justify it; if linear only, switch to Celery in Phase 2 |
| **Cloud target** | Azure (Terraform, Container Apps, $45-85/mo) | Railway / Fly.io ($5-30/mo, 30s provision, no IaC) | **Railway for v1 (1 project)**, Azure for v2 (multi-tenant). Swap = adapter change only (DeployerAgent uses ToolPort, not Azure SDK directly) |
| **Hexagonal ports** | Full 5-port design (LLMPort, VaultPort, ToolPort, HumanPort, LoggingPort) | 3-layer only (domain / application / infra), no formal ports | **Keep 5 ports** — `import-linter` rule enforces it; enables zero-LLM unit tests from day 1 |
| **Intake depth** | 5 mandatory + 10 contextual (new) | 3 questions only, rest inferred by Analyst | **5 mandatory** — fewer than 5 produces too many downstream Analyst assumptions |

### 15c. Scope Constraints (What This System Cannot Build)

The following project types are **out of scope** and should be communicated at intake (shown as hard constraint before user starts):

- ❌ Native mobile apps (iOS/Android) — no React Native, no Swift, no Kotlin
- ❌ Shopify / WordPress plugins or themes
- ❌ Machine learning model training pipelines
- ❌ CLI tools or desktop applications
- ❌ Modifications to existing codebases (greenfield only in v1)
- ❌ Projects requiring on-premise deployment
- ✅ Web apps (Next.js frontend + FastAPI backend + PostgreSQL + Azure)

### 15d. Semantic vs. Syntactic Correctness

> **The hardest unsolved problem in this plan:** Pydantic validates that the PRD is a valid `ProjectSpecification` object. It does **not** validate that the market data is accurate, that the user stories are coherent, or that the technical choices are well-reasoned. All required fields can pass schema validation while containing hallucinated content.

**Mitigations we DO have:**
- AH-2: `tool_choice="required"` forces Analyst to call `web_search` before answering (grounds market claims)
- AH-4: `original_requirement` is pinned and re-read at every stage (prevents drift from the idea)
- Human gates: the human reviewer is the semantic correctness check at each gate

**Mitigations we do NOT have (known gaps):**
- No citation tracking: Analyst's market claims are not linked to sources
- No contradiction detection between stages: Designer can contradict PRD without automatic alert
- Pydantic validates syntax, humans validate semantics — this is intentional but must be communicated to users

### 15e. What the Failure-Modes Analyst Found Will Break in Week 1

From the adversarial failure-mode trace on "Build me a task tracker for a team of 5":

> **These are hypothetical failures** derived from adversarial review, not observed production issues. All mitigations are implemented in §6, §9, and the HumanPort spec.

**Within 24 hours of first launch:**
1. Docker sandbox startup latency makes users think the system is frozen (no progress indicator)
2. npm/pip install fails if required package isn't in base image (Builder can't self-fix network-isolated install)
3. RLS data leak if `RLSMiddleware` is not tested with concurrent users

**Within 1 week:**
1. Rate limits cascade after 5-10 projects (both primary and fallback models throttled simultaneously)
2. Context overflow on complex projects — Deployer can't fit its full output in one call
3. Azure free-tier quotas exhausted after 1-2 PostgreSQL-backed projects
4. WebSocket disconnect during gate review loses approval state

**The key insight:** *"This system works on Day 1 for a single happy-path project. It fails in Week 1 under concurrent load, retries, or multi-user access. The failures are structural."* — All mitigations are now in §6, §9, and the HumanPort spec.



---

## 16. Observability: Every Generated App Ships Production-Ready Monitoring

The key insight: observability is not an afterthought. The Builder agent's skill file (`observability.md`) auto-injects OpenTelemetry instrumentation into every generated app. The human never has to configure monitoring — it's there from day 1.

> **Multi-project monitoring:** The Agency Management Console (§21) provides the user-facing layer above raw telemetry — a single dashboard showing pipeline status, gate queue, and cost across all projects. §16 instruments the data; §21 presents it to Sam. Admins see §16 dashboards directly; Sam sees the AMC.

### 16a. What Gets Injected (Builder Agent Skill)

A new skill file `backend/skills/observability.md` instructs Builder to add observability to every generated app:

- **FastAPI:** auto-instrumented with `opentelemetry-instrumentation-fastapi` (traces every request with user_id, project_id, route, status, latency)
- **Next.js:** inject Vercel/Azure App Insights SDK for frontend performance (Core Web Vitals: LCP, CLS, FID)
- **PostgreSQL:** query duration tracing via `opentelemetry-instrumentation-sqlalchemy`
- **Structured JSON logs:** every app must emit `{timestamp, level, service, trace_id, span_id, user_id, message}` — no plain-text logs
- Every generated app gets a `/health` endpoint (returns `{status, version, db_connected, cache_connected, uptime_seconds}`)
- Every generated app gets a `/metrics` endpoint (Prometheus-compatible)

### 16b. Azure Monitor Integration (Deployer Agent)

- Deployer auto-creates an Application Insights workspace per project (Terraform module: `infra/modules/observability/`)
- Connection string injected into Container App environment via Key Vault reference
- Default alert rules (Terraform-managed, not manual):
  - Error rate > 1% for 5min → email + optional PagerDuty
  - p95 latency > 2s for 10min → email
  - App not responding > 2min → immediate page
  - Monthly cost > user's stated budget → email

### 16c. Pre-Built Dashboards

Deployer creates 3 default Azure Monitor workbook dashboards per project:

| Dashboard | Key Metrics |
|---|---|
| **Application Health** | Request rate, error rate, p50/p95/p99 latency, active users |
| **Database Performance** | Query duration heatmap, slow query log, connection pool saturation |
| **Cost & Usage** | Daily Azure spend, LLM token usage, per-feature usage breakdown |

### 16d. Generated App Directory Addition

Builder now adds an `observability/` folder to every generated project:

```
generated-app/
├── backend/
│   └── telemetry.py        ← OpenTelemetry setup (auto-injected by Builder)
├── infra/terraform/
│   └── modules/observability/
│       └── main.tf         ← App Insights + alert rules + dashboards
└── .github/workflows/
    └── monitor-check.yml   ← weekly: validate alerts are still firing correctly
```

### 16e. Gate 4 Addition

Gate 4 (Deployer gate) now has a 5th mandatory check: **"Application Insights connected and receiving telemetry from staging environment?"**

> See **§17 Copilot SDK Analytics** for agency-level observability — instrumenting the agents themselves, not just the apps they build.


---

## 17. GitHub Copilot SDK: Observing the Agency's Own Performance

The key insight: just as we instrument every generated app, we instrument the agency itself. GitHub Copilot SDK (Metrics API + Copilot Telemetry) lets us track exactly how the autonomous development process performs — which agents are expensive, which are slow, which model gives best quality/cost ratio.

### 17a. What We Instrument

Use `@github/copilot-sdk` (GitHub Copilot Extensibility SDK) to emit telemetry events for every agent run:

```typescript
// Every agent run emits this event via Copilot SDK
interface AgentRunEvent {
  event_type: "agent_run_complete";
  project_id: string;
  agent_name: "analyst" | "designer" | "architect" | "builder" | "deployer";
  stage: number;           // 0-4
  model_used: string;      // e.g. "claude-sonnet-4.5"
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  duration_seconds: number;
  retries: number;         // how many LLM retries were needed
  gate_approved: boolean;
  gate_time_seconds: number;  // how long human took to approve
  skill_files_loaded: string[];
  tool_calls_made: number;
}
```

### 17b. Copilot Metrics Dashboard

The Copilot SDK dashboard exposes 5 key agency-level metrics:

| Metric | Why It Matters |
|---|---|
| **Cost per project by stage** | Reveals which agent is the most expensive; targets optimization |
| **Token efficiency ratio** (output tokens / input tokens) | Low ratio = agent over-prompted; high = good compression |
| **Human gate approval time** | Long approval = gate checklist too complex or artifacts unclear |
| **Retry rate per agent** | High retries = schema too complex or model wrong for task |
| **Model quality score** (gate approval rate by model) | Compares GPT vs Claude vs Gemini on same task type |

### 17c. Copilot SDK Integration Code

```python
# backend/adapters/telemetry/copilot_sdk.py
from github_copilot_sdk import CopilotTelemetry

class CopilotSDKAdapter(LoggingPort):
    def __init__(self):
        self.telemetry = CopilotTelemetry(
            extension_id="autonomous-agency",
            version="1.0.0"
        )
    
    async def log(self, level: str, message: str, metadata: dict = None):
        if metadata and metadata.get("event_type") == "agent_run_complete":
            await self.telemetry.emit_event(
                name="agent_run",
                properties=metadata
            )
        # also write to standard Azure Monitor
        await self._azure_monitor.track_event(message, metadata)
```

### 17d. Weekly Agency Performance Report

The agency auto-generates a weekly report (GitHub Actions workflow) using Copilot SDK data:

- Top 3 most expensive projects this week (and why)
- Agent with highest retry rate (prompt improvement candidate)
- Model performance ranking on gate approval rate
- Average idea-to-deployed-app time (track this improving over time)
- Recommendation: "Builder's retry rate is 2.3× higher this week — consider upgrading `tdd.md` skill or switching to claude-sonnet-4.5"

### 17e. Directory Additions

```
backend/
├── adapters/
│   └── telemetry/
│       ├── copilot_sdk.py    ← CopilotSDKAdapter(LoggingPort)
│       └── azure_monitor.py  ← AzureMonitorAdapter(LoggingPort)
.github/workflows/
└── agency-weekly-report.yml  ← runs weekly; queries Copilot SDK metrics; posts summary to GitHub Issues
```

---

## 18. Legal & Compliance: Pre-Launch Requirements

> These are **not engineering tasks** — they require legal counsel. Every item is a launch blocker for commercial operation. This section documents what must exist before first paying customer.

### 18a. Must-Draft Legal Documents (Before Any Paid User)

| Document | Key Clauses Required | Status |
|---|---|---|
| **Terms of Service** | Liability cap (fees paid in preceding 12mo); User owns all generated code; OWASP checklist ≠ security warranty; Refund policy; Arbitration clause | ⬜ Not drafted |
| **Privacy Policy** | Data collected (ideas, credentials, brand assets); Retention policy (90 days post-project, then deleted); GDPR rights (access, erasure, portability); Third-party processors (Anthropic, OpenAI, Google, Azure, LangSmith) | ⬜ Not drafted |
| **Acceptable Use Policy** | Prohibited: malware, illegal content, credential stuffing tools; Content filtering mechanism | ⬜ Not drafted |
| **Data Processing Agreement** | Required if processing EU residents' data; Azure is data processor; Agency is data controller | ⬜ Not drafted (needed for EU launch) |

### 18b. Data Retention & GDPR Compliance

**Data retention policy (must be implemented in code):**
| Data type | Retention | Deletion trigger |
|---|---|---|
| Project vault (Azure Blob) | 90 days post last-active | User deletes project OR account deletion |
| Redis checkpoints | 30 days TTL (already specced §5) | Auto-expire |
| PostgreSQL project rows | 90 days post last-active | Soft-delete then hard-delete job |
| LLM call logs | 30 days | Rolling purge job |
| User credentials (Key Vault) | Until project deleted | Hard-delete on project deletion |

**GDPR right-to-erasure endpoint:** `DELETE /api/v1/users/me` must cascade-delete all vault data, DB rows, Redis keys, and Key Vault secrets for that user. Audit log of deletion stored for 7 years (legal requirement).

**Data residency:** Agency defaults to **Azure West Europe (Ireland)** for EU users and **Azure East US** for US users. User's Azure region selected at project creation. Cross-region transfers require SCCs (auto-attached in ToS for EU users).

### 18c. Security Compliance Roadmap

| Milestone | Target | Required For |
|---|---|---|
| Penetration test (annual) | Phase 2 | Any enterprise customer |
| SOC 2 Type II audit | Phase 3 | Enterprise sales ($500+/mo) |
| GDPR DPA with Azure | Pre-launch | EU users |
| EU AI Act assessment | Pre-EU-launch | EU market entry |
| Incident response SOP | Pre-launch | Any launch |

**Incident response SOP (minimum):**
1. Security event detected → Page on-call (PagerDuty)
2. Within 1 hour: Assess scope (which users, which data)
3. Within 24 hours: Contain (rotate affected credentials, patch vector)
4. Within 72 hours: GDPR breach notification to supervisory authority (if EU users affected)
5. Within 7 days: User notification + post-mortem published

### 18d. IP & Liability

**Code ownership:** All generated code is owned by the user. Agency retains no rights. Users may use, modify, sell, and distribute generated code without restriction.

**LLM copyright audit (required before launch):**
- Anthropic Claude: Verify commercial use terms permit deployment of generated outputs
- OpenAI GPT: Verify API ToS for commercial code generation use case
- Google Gemini: Verify commercial use terms for Stitch/design outputs

**OWASP disclaimer (must appear in Gate 3 UI):**
> ⚠️ *The OWASP checklist is performed by AI, not a certified security engineer. This is NOT a professional security audit. You are responsible for additional security review before processing sensitive user data.*

### 18e. Third-Party API Compliance

| API | ToS Audit Required | Data Retention Risk | Fallback |
|---|---|---|---|
| **Napkin AI** | ✅ Verify commercial use + data retention | Napkin may retain SVG inputs | ASCII flow diagram (already specced) |
| **Google Stitch** | ✅ Verify commercial use + data retention | Google may retain mockup inputs | Gemini-only text mockup |
| **Anthropic Claude** | ✅ Verify no prohibition on code gen for resale | Anthropic zero-retention API option available | GPT-4o fallback |
| **OpenAI GPT** | ✅ Commercial API ToS confirmed | Zero data retention by default on API | Claude fallback |

> **Rule:** If any third-party API retains user data by default, the Privacy Policy must disclose this AND users must be informed at intake.

---

## 19. Business Model, Unit Economics & Competitive Position

> This section is for stakeholders and investors. It documents what we know, what we've validated, and what remains to be proven.

### 19a. Revenue Model (v1)

| Revenue stream | Mechanism | Margin |
|---|---|---|
| **LLM pass-through** | Charge cost + 20% on every LLM call | ~20% gross |
| **Azure infra margin** | User pays Azure directly (no margin in v1) | 0% in v1; target 10% in v2 via reserved capacity |
| **Revision runs** | Same cost model; each patch stage = ~$5-10 | ~20% gross |
| **Enterprise tier (Phase 3+)** | Seat subscription $200-500/mo; includes priority support, SOC 2 compliance, custom models | Target 60%+ gross margin |

**v1 unit economics (honest):**
- Average project: $12 LLM + $8 Azure = $20 cost → $24 price → $4 gross profit
- LTV per user: ~$50-80 (1 project + 2 revisions, then churn) — lifestyle economics
- Path to venture economics: Enterprise subscription LTV = $2,400-6,000/year per team

### 19b. Competitive Positioning

**We are not competing with Bolt.new on speed.** We are competing with:
- **Freelancers** ($5,000-15,000, 2-4 weeks) → We win on cost and speed
- **Dev agencies** ($20,000-80,000, 6-12 weeks) → We win on cost and speed, lose on customization
- **Internal engineering backlog** (3-6 months wait) → We win on speed, lose on integration with existing codebase

**Moat (operational, not structural — must be deepened):**
1. **Audit trail**: Every decision, every agent action, logged and reviewable. Freelancers don't provide this.
2. **HITL + compliance defaults**: OWASP, RLS, App Insights built-in. Freelancers skip these.
3. **Compound skill hoard**: Each project improves the skill files (§13f Compound Step). Over 50+ projects, quality improves in ways competitors can't replicate.

**Competitive threats (6-12 month horizon):**
| Threat | Timeline | Impact | Mitigation |
|---|---|---|---|
| Bolt.new adds Azure deploy | 6 months | HIGH — removes speed+cloud gap | Deepen compliance/audit trail moat; target enterprise |
| GitHub Copilot Workspace adds HITL | 12 months | MEDIUM — existing GitHub users shift | Compete on non-developer founders; add GitHub login as optional not required |
| OpenAI ChatGPT Projects adds deployment | 9 months | HIGH — removes distribution gap | Speed to enterprise tier before ChatGPT reaches it |

### 19c. Go-To-Market (v1 — lean)

**Phase 1 GTM (0-100 users):** Content-led. Ship a "Build [X] in 2 hours" demo video for 5 different app types (task tracker, feedback board, waitlist, internal dashboard, booking tool). Post to Hacker News, Product Hunt, relevant subreddits. Target: developers who refer non-technical founders.

**Phase 2 GTM (100-1000 users):** Partner-led. Integrate with Notion ("turn this Notion doc into an app"), Figma ("turn this Figma design into a deployed app"), and no-code communities (Bubble, Webflow forums). Target: power users of existing no-code tools who have hit their ceiling.

**Phase 3 GTM (1000+ users):** Enterprise outbound. Target: product managers at Series A-B startups with engineering backlogs. Pitch: "Ship internal tools without waiting for eng sprint."

### 19d. What We're NOT Doing (v1 Scope)

| Excluded | Reason |
|---|---|
| Mobile apps | Doubles complexity; separate toolchain |
| Existing codebase modifications | Requires different intake and context management |
| Real-time apps (WebSockets beyond basic) | Builder skill not yet trained on this |
| Competitive pricing with Bolt.new | Different customer; don't race to the bottom |
| Open-source core | Reduces moat; consider after PMF |

---

## 21. Agency Management Console (AMC)

> **Purpose:** Single pane of glass for managing ALL projects across the autonomous dev agency — monitor pipelines in real-time, approve gates, initiate new ideas, and track costs and health. Designed for both Sam (non-technical, approves from phone) and agency admins (monitors infrastructure and skill performance).

> **Design principle:** Every screen is non-technical for Sam. Stages shown as plain English ("Writing tests", "Building code", "Deploying"), not agent names. Costs always in dollars. Gate approval follows the §7 plain-language guide.

### 21a. Core Architecture

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 + TypeScript + TailwindCSS (mobile-first) |
| Backend | FastAPI (Python 3.12) — same service as agency backend |
| Realtime | WebSocket broadcaster (Redis pub/sub) for multi-project updates |
| Auth | JWT + RBAC middleware (admin / owner / viewer roles) |
| Database | Same PostgreSQL instance as agency — RLS scopes projects per user |
| Deployment | Azure Container Apps (same infra as agency) |

**Key decision:** No separate database. Agency state lives in the same PostgreSQL + Redis as the agency backend. A single RLS policy ensures owners see only their own projects; admins see all.

### 21b. The 7 Core Screens

#### Screen 1 — Project Dashboard (`/dashboard/projects`)
Bird's-eye view of all projects. **Real-time via WebSocket.**

| Column | Content |
|---|---|
| Project Name | Link to Pipeline Monitor |
| Stage | "Planning / Designing / Building / Testing / Deploying / Live / Failed" |
| Status | ✅ OK · ⚠️ Gate Pending · 🔴 Failed |
| Progress | Visual bar: N of 5 gates passed |
| Cost | "$3.42 LLM + $5.00 Azure" |
| Gate waiting | "Gate 2 — 3 days pending" or "—" |
| Actions | View · Approve gate · Re-run stage · Archive |

Filters: status, stage, date range, cost range, project name search.

#### Screen 2 — Pipeline Monitor (`/dashboard/projects/:id/monitor`)
Real-time single-project view. Split pane: pipeline diagram (left) + activity feed (right). **Real-time.**

Left pane shows all 5 stages as nodes — each with: ✅/⏳/⏹ status, elapsed time, stage cost, gate status, "View artifacts" link.

Right pane: reverse-chronological activity feed — every agent action, gate opened/approved, cost milestone, error. Searchable and filterable.

Top bar: total cost, elapsed time, estimated completion time.

Actions: Pause · Re-run stage · Cancel project · Download vault zip · Admin override advance.

#### Screen 3 — Gate Queue (`/dashboard/gates`)
Central approval queue across ALL projects. **Persistent badge count in nav. Real-time.**

List sorted by oldest-first (time-to-approval is the key KPI). Each row shows: project name, gate number/name, time waiting, owner, cost so far, checklist completion.

"Open gate" button → modal with full §7 HITL checklist + plain-language guide for Gates 2-3. Approve / Give Notes / Re-run.

Mobile: swipe right on gate card to reveal "Open gate".

#### Screen 4 — New Idea Intake (`/dashboard/projects/new`)
4-step guided form to start a new project. **Synchronous POST → redirect to Pipeline Monitor.**

- Step 1: Idea description (20-2000 chars, example prompts shown)
- Step 2: Budget ($10 / $25 / $50+), timeline preference, access level (public / invite / login / internal)
- Step 3: Brand assets (optional — logo, primary color)
- Step 4: Summary + cost estimate → "Start Pipeline" button

After submit: redirect to Pipeline Monitor, Analyst stage starts immediately, user subscribed to gate notifications.

#### Screen 5 — Cost & Token Dashboard (`/dashboard/costs`)
Financial visibility across all projects. **Updates every 30s for running projects.**

KPIs: total spend (all time), active project cost, avg cost/project, monthly burn rate.

Charts: spend over time (LLM vs Azure stacked area), breakdown table by project. CSV export. Monthly budget alert configuration.

#### Screen 6 — Agency Health Monitor (`/dashboard/health`)
Infrastructure status for admins. **Real-time via WebSocket every 60s.**

Status grid (✅ OK / ⚠️ DEGRADED / 🔴 DOWN) for: ACI Sandbox, PostgreSQL, Redis, each LLM API (Claude / GPT-4o / Gemini), Key Vault, GitHub API, Terraform State, Email service.

Detailed panels: ACI container list + recent sandbox runs, LLM rate limits + latency, DB connections, Redis memory/evictions.

Actions: Force health check · View component logs · Configure alerts · Restart sandbox.

#### Screen 7 — Skill Performance (`/dashboard/skills`)
Agency evolution dashboard for admins. **Updated weekly (Monday 00:00 UTC).**

Leaderboard: each skill file with usage count, eval score (0-10), trend arrow, last improved date.

Detail view: eval score trend chart (8-week), test pass rate, time-to-gate, user approval rate, recent Compound Step PRs with score delta.

Actions: View improvement history · Propose experiment (test new skill version) · Revert to previous version · Archive skill.

### 21c. Data Models (Pydantic v2)

```python
# backend/api/schemas/amc.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

class ProjectSummary(BaseModel):
    """Lightweight project row for dashboard listing."""
    model_config = ConfigDict(use_enum_values=True)
    project_id: UUID
    user_id: UUID
    name: str = Field(..., max_length=200)
    stage: Literal["planning","designing","building","testing","deploying","live","failed"]
    status: Literal["ok","degraded","failed","awaiting_gate"]

**Stage mapping (ProjectState → ProjectSummary):**
```python
STAGE_MAP = {
    "intake": "planning", "analyst": "planning",
    "designer": "designing",
    "architect": "building",
    "builder": "testing",
    "deployer": "deploying",
    "done": "live",
    "failed": "failed",
}
# Usage: summary.stage = STAGE_MAP[project_state.stage]
```
> This mapping translates internal agent-named stages to Sam-friendly display names. The mapping is applied in the API layer (`GET /api/v1/agency/projects`) before serialization.

    cost_usd: float = 0.0
    created_at: datetime
    last_active: datetime
    gate_waiting: Optional[int] = None        # gate number 0-4, or None
    progress_gates_passed: int = 0            # 0-5
    error_message: Optional[str] = None
    archived: bool = False

class AgencyStats(BaseModel):
    """Agency-level aggregate metrics."""
    total_projects: int
    active_projects: int
    completed_projects: int
    failed_projects: int
    active_pipelines: int                     # agents currently running
    gates_waiting: int                        # total open gates
    total_spend_usd: float
    avg_cost_per_project: float
    completion_rate: float = Field(..., ge=0, le=1)
    avg_time_to_completion_hours: float
    avg_gate_approval_time_hours: Optional[float] = None
    last_updated: datetime

class LLMAPIHealth(BaseModel):
    provider: str
    status: Literal["ok","degraded","down"]
    rate_limit_current: int
    rate_limit_max: int
    avg_latency_ms: int
    error_rate_percent: float = Field(..., ge=0, le=100)
    last_check: datetime

class AgencyHealth(BaseModel):
    """Infrastructure health snapshot."""
    aci_sandbox: Literal["ok","degraded","down"]
    postgres: Literal["ok","degraded","down"]
    redis: Literal["ok","degraded","down"]
    llm_apis: dict[str, LLMAPIHealth]
    terraform_state: Literal["locked","unlocked"]
    github_api: Literal["ok","degraded","down"]
    key_vault: Literal["ok","degraded","down"]
    overall_status: Literal["ok","degraded","down"]
    last_checked: datetime
```

### 21d. WebSocket Event Schema

All AMC real-time events pass through `/ws/agency`. **Server-side filtering is mandatory** — the broadcaster checks the authenticated user's `user_id` (from JWT on WebSocket handshake) against the event's `project_id` ownership before sending. An `owner` only receives events for their own projects; an `admin` receives all events. Clients never filter — the server filters for them.

**Implementation:** On WebSocket connect, the server extracts `user_id` from the JWT in `Sec-WebSocket-Protocol`, queries the user's role, and stores `{connection_id: user_id, role}` in a Redis hash. On each event, the broadcaster:
1. If `role == admin` → send event
2. If `role == owner` → check `project.user_id == connection.user_id` → send or skip
3. If `role == viewer` → same as owner but gate approval actions are stripped from payload

```python
# backend/api/ws/events.py
from pydantic import BaseModel
from typing import Any, Literal
from uuid import UUID
from datetime import datetime

class WSEvent(BaseModel):
    event: str                    # e.g. "pipeline.stage_changed"
    project_id: UUID
    timestamp: datetime
    data: dict[str, Any]          # event-specific payload

# Event catalogue:
# pipeline.stage_changed   — data: {from_stage, to_stage, agent_name, cost_so_far}
# pipeline.gate_opened     — data: {gate_number, gate_name, checklist_items}
# pipeline.gate_approved   — data: {gate_number, approved_by, action: "approved"|"deferred"|"notes"}
# pipeline.completed       — data: {staging_url, total_cost_usd, duration_minutes}
# pipeline.failed          — data: {stage, error_message, recoverable: bool}
# agent.action             — data: {agent_name, action_type, description, tokens_used, cost_usd}
# agency.health_check      — data: AgencyHealth dict (broadcast every 60s)
# skill.eval_updated       — data: {skill_name, old_score, new_score, delta}
```

### 21e. REST API Endpoints

```
GET    /api/v1/agency/projects          — paginated ProjectSummary list
                                          query: status, stage, from_date, to_date, page, per_page
GET    /api/v1/agency/stats             — AgencyStats aggregate
GET    /api/v1/agency/health            — AgencyHealth snapshot
GET    /api/v1/agency/gates             — all open gates (filter: owner, gate_number, age_hours)
POST   /api/v1/agency/projects          — initiate new project
                                          body: {idea: str, budget_usd: float, access_level: str, brand_assets_url?: str}
GET    /api/v1/agency/activity          — paginated agent activity feed (filter: project_id, agent, event_type)
GET    /api/v1/agency/costs             — cost breakdown by project / agent / day (filter: from_date, to_date)
GET    /api/v1/agency/skills            — skill leaderboard (filter: stage, agent)
GET    /api/v1/agency/skills/:name      — skill detail + eval trend
WS     /ws/agency                       — broadcast socket for all AMC real-time events
WS     /ws/agency/:project_id           — project-scoped socket (subset of /ws/agency)
```

**Per-endpoint authorization:**

| Endpoint | `admin` | `owner` | `viewer` |
|---|---|---|---|
| `GET /projects` | All projects | Own projects only (RLS) | Own projects only (RLS, read-only) |
| `GET /stats` | Agency-wide stats | Own-project stats only | Own-project stats only |
| `GET /health` | ✅ Full access | ❌ 403 Forbidden | ❌ 403 Forbidden |
| `GET /gates` | All gates | Own gates only (RLS) | Own gates (read-only, no approve) |
| `POST /projects` | ✅ | ✅ | ❌ 403 Forbidden |
| `GET /activity` | All activity | Own-project activity (RLS) | Own-project activity (RLS) |
| `GET /costs` | All costs | Own-project costs (RLS) | Own-project costs (RLS) |
| `GET /skills` | ✅ Full access | ❌ 403 Forbidden | ❌ 403 Forbidden |
| `GET /skills/:name` | ✅ Full access | ❌ 403 Forbidden | ❌ 403 Forbidden |
| `WS /ws/agency` | All events | Own events (server-filtered) | Own events (server-filtered, no actions) |
| `WS /ws/agency/:project_id` | All events for project | Own project only (403 if not owner) | Own project only (read-only, 403 if not owner) |

> **Rule:** Endpoints returning aggregate data (`/stats`, `/health`, `/skills`) are **admin-only**. All project-scoped endpoints use RLS for `owner`/`viewer` isolation. `viewer` cannot write (no POST, no gate approval).

### 21f. Role-Based Access Control

| Role | Who | Capabilities |
|---|---|---|
| `admin` | Agency operator | All screens, all projects, Agency Health, Skill Performance, admin overrides |
| `owner` | Project creator (Sam) | Their own projects only, full gate approval, New Idea, Cost dashboard |
| `viewer` | Stakeholder (Sam's co-founder) | Read-only pipeline status and artifacts, cannot approve gates |

RBAC middleware checks JWT claim `role`. RLS in PostgreSQL enforces data isolation (owner sees only their `user_id` rows regardless of role claim).

### 21g. Non-Technical UX Principles (for Sam)

| Principle | Implementation |
|---|---|
| **One-click new project** | Floating "＋ New Project" button on every screen |
| **Gate badge always visible** | Nav badge count updates in real-time via WebSocket |
| **Plain-English stages** | "Writing tests" not "Builder stage 4"; "Building code" not "Agent node running" |
| **Costs in dollars** | Never show tokens to Sam; convert using current model pricing on the fly |
| **Mobile-first gates** | Gate approval modal is full-screen on mobile, swipe-to-approve |
| **Progressive disclosure** | Sam sees simple summary; "View technical details" expands raw data for Alex |

---

## 20. Implementation Backlog — Build Order & Role Assignments

> **This section replaces a task tracker.** Each item has enough context to be built independently. Items are ordered by dependency: complete each phase before starting the next. Each item references the section of this document that specifies it.

### How to use this backlog
- Pick a phase, pick an item, read the referenced section for the full spec
- Each item is independently shippable — no item should block another within the same phase
- Mark progress in your team's tracker (GitHub Projects, Linear, Notion — your choice)
- After shipping v1, the Evolution System (§13) takes over continuous improvement

---

### Phase 0 — Foundation (no dependencies, start here)

> **Who:** Backend engineer. **Goal:** Runnable skeleton with types, ports, and base class. No LLM calls yet.

- [ ] **`backend/core/state.py`** — Full `ProjectState` + `ProjectMeta` + `IntakeAnswers` Pydantic v2 models. Spec: §8. Use `ConfigDict(use_enum_values=True)`. Include UUID validators, `token_budget`, `usd_budget`, `gate_approvals`, `artifacts` dict.
- [ ] **`backend/core/ports.py`** — 5 abstract port interfaces: `LLMPort`, `VaultPort`, `ToolPort`, `HumanPort`, `LoggingPort`. Spec: §1c. Agents import ONLY from this file — never from `adapters/`.
- [ ] **`backend/agents/base.py`** — `BaseAgent` with constructor port injection, `@requires_tool_call` decorator (`kwargs["tool_choice"] = "required"`), `make_node()` singleton (module-level cache), `_run_with_budget()` circuit breaker. Spec: §8.
- [ ] **`backend/skills/constitution.md`** — AH-1 through AH-4 rules in machine-readable markdown. Loaded by every agent at startup. Spec: §1b.
- [ ] **`backend/skills/gate-checklists.md`** — Gate 0-4 blocking conditions + advisory conditions. Format: YAML frontmatter + markdown body. Spec: §7.
- [ ] **`backend/skills/critique.md`** — Critic skill with structured self-eval prompt (reflection pattern). Spec: §9b.
- [ ] **`backend/skills/registry.py`** — `SkillRegistry` class: discovers skill `.md` files, loads them, validates token count limits (< 2,000 tokens per file), exposes `get(name)`. CI calls `SkillRegistry.validate_all()` on every PR.
- [ ] **`tests/unit/test_state.py`** — Unit tests for ProjectState validation: required fields, UUID format, budget fields default to 0, stage literals only.
- [ ] **`tests/unit/test_base_agent.py`** — Unit tests for BaseAgent: port injection, singleton via `make_node()`, requires_tool_call sets correct kwarg.

---

### Phase 1 — Adapters (requires Phase 0)

> **Who:** Backend engineer. **Goal:** Real and mock implementations of every port. Agents stay untouched.

- [ ] **`backend/adapters/vault/azure_blob.py`** — `AzureBlobVault(VaultPort)` implementation. Methods: `save(namespace, key, content: str | bytes)`, `load(namespace, key) -> str`, `save_binary(namespace, key, content: bytes, mime_type: str) -> str` (returns URL). Container per `project_id`. SAS URL generation for binary assets. Spec: §5, §8.
- [ ] **`backend/adapters/vault/mock.py`** — `MockVault(VaultPort)` backed by `tmp/` directory. Used in all local dev and CI runs. Same interface as AzureBlobVault.
- [ ] **`backend/adapters/llm/router.py`** — `ModelRouter`: loads `agents_config.yaml` once into module-level `_registry_cache` singleton. `route(task) -> adapter`. `_find_primary(task)`: `task in model["primary_tasks"]` (string in list). Adapter prefix mapping: `claude→AnthropicAdapter`, `gpt→OpenAIAdapter`, `gemini→GeminiAdapter`. Spec: §6b.
- [ ] **`backend/adapters/llm/anthropic.py`** — `AnthropicAdapter(LLMPort)`. Wraps Anthropic SDK. Injects project_id tag for LiteLLM cost tracking. Respects `token_budget` from ProjectMeta.
- [ ] **`backend/adapters/llm/openai.py`** — `OpenAIAdapter(LLMPort)`. Wraps OpenAI SDK. Same interface as AnthropicAdapter.
- [ ] **`backend/adapters/llm/gemini.py`** — `GeminiAdapter(LLMPort)`. Used by Designer agent for design brief generation.
- [ ] **`backend/adapters/human/websocket.py`** — WebSocket HITL gate handler. JWT in `Sec-WebSocket-Protocol` header. Scoped to `user_id + project_id`. Gate state persisted in Redis (reconnect-safe). 24h timeout. Idempotent approval. Spec: §7.
- [ ] **`backend/adapters/human/mock.py`** — `MockHumanPort(HumanPort)` that auto-approves all gates. Used in integration tests and demo mode.
- [ ] **`backend/middleware/auth.py`** — `AuthMiddleware`: JWT validation, sets `request.state.user_id`. MUST run BEFORE `RLSMiddleware`. Spec: §6.
- [ ] **`backend/middleware/rls.py`** — `RLSMiddleware`: `SET LOCAL app.user_id = $1` with UUID-validated parameterized query (never f-string). Uses `request.app.state.db` (SQLAlchemy 2.x async + asyncpg). Spec: §6.
- [ ] **`backend/adapters/logging/copilot_sdk.py`** — `CopilotSDKAdapter(LoggingPort)`. Emits `AgentRunEvent` telemetry schema. Spec: §17.
- [ ] **`tests/unit/test_model_router.py`** — Tests: YAML loaded once (singleton), primary task matching, adapter prefix dispatch, fallback chain.
- [ ] **`tests/integration/test_rls_middleware.py`** — Tests: parameterized query used (not f-string), UUID validation rejects non-UUID, middleware order (Auth before RLS).

---

### Phase 2 — Agents & Skills (requires Phase 1)

> **Who:** Backend engineer + prompt engineer. **Goal:** Full 5-agent pipeline. Each agent is a LangGraph node.

- [ ] **`backend/agents/analyst.py`** — `AnalystAgent(BaseAgent)`. Loads `skills/analyst/system-v1.md`. Input: raw idea string. Output: `IntakeAnswers` (5 mandatory + up to 10 contextual fields validated). Runs intake Q&A (§2b). Vaults result as `1_analyst/intake.json`. Spec: §2, §4.
- [ ] **`backend/skills/analyst/system-v1.md`** — Analyst system prompt. Must include: AH-1 (tool calls only), 5 mandatory intake questions, scope constraint list (no mobile, no existing codebase, etc.), output format contract.
- [ ] **`backend/agents/designer.py`** — `DesignerAgent(BaseAgent)`. Calls Gemini for design brief → `DESIGN.md`. Calls Napkin AI API for flow SVGs → `2_design/flows/*.svg`. Calls Google Stitch for HTML mockups → `2_design/mockups/*.html`. Fallback: if Napkin down, ASCII diagram + log to `state.errors` (stage doesn't fail). Saves SVG/HTML as binary via `vault.save_binary()`. Spec: §2, §6.
- [ ] **`backend/skills/designer/system-v1.md`** — Designer prompt. Output contract: DESIGN.md format, SVG file naming convention, HTML mockup structure for iframe rendering.
- [ ] **`backend/agents/architect.py`** — `ArchitectAgent(BaseAgent)`. Generates: `3_arch/DATA_MODEL.md`, `API_CONTRACTS.md`, `AUTH_PLAN.md`, `TECH_DECISIONS.md`. Runs Infracost estimate → sets `state.meta.monthly_infra_estimate`. Spec: §2, §4.
- [ ] **`backend/skills/architect/system-v1.md`** — Architect prompt. Must include: RLS requirement for every table, `app.user_id` convention, PgBouncer session mode requirement, data residency choice (EU-West or US-East).
- [ ] **`backend/agents/builder.py`** — `BuilderAgent(BaseAgent)`. Red phase: writes failing tests first, vaults red log to `4_app/red_phase.txt`. Green phase: writes code until tests pass. Invokes ACI sandbox (2-phase: build with network, verify network-isolated). Injects code via Azure Blob volume mount at `/workspace`. Retrieves output from `/workspace/test_output.txt`. Test runners: `pytest backend/tests/ -v --tb=short` + `npx vitest run --reporter=verbose`. Opens GitHub PR. Spec: §2, §4, §6.
- [ ] **`backend/skills/builder/system-v1.md`** — Builder prompt. Must include: red-phase mandate (write failing test before any implementation), ACI sandbox invocation pattern, OWASP checklist (SQL injection, XSS, auth bypass, secrets in env not code), zero-tolerance refactoring rule.
- [ ] **`backend/agents/deployer.py`** — `DeployerAgent(BaseAgent)`. Runs Terraform plan → apply. Configures Azure Container Apps (not ACI — ACA is for the deployed app; ACI is only for the build sandbox). Runs `infracost breakdown --path=infra/terraform/ --format=json`. Injects OpenTelemetry into generated app. Returns staging URL. Spec: §2, §9, §16.
- [ ] **`backend/skills/deployer/system-v1.md`** — Deployer prompt. Must include: Infracost threshold check (fail if > `usd_budget`), AH-1 (tool calls only, never shell-exec without tool wrapper), staging URL format.
- [ ] **`backend/orchestrator.py`** — LangGraph state machine. Nodes = agent `make_node()` singletons. Edges = gate approval checks. State = `ProjectState`. Handles DEFER (pause → resume) and re-run from checkpoint. Spec: §4.
- [ ] **`tests/integration/test_pipeline.py`** — Happy-path integration test using MockVault + MockHumanPort + MockLLM. Input: "Build me a task tracker for 3 people". Assert: state transitions through all 5 stages, gate_approvals dict populated, artifacts dict has expected keys.

---

### Phase 3 — Infrastructure (can run in parallel with Phase 2)

> **Who:** DevOps / infra engineer. **Goal:** Repeatable Azure provisioning. No manual clicks.

- [ ] **`infra/terraform/main.tf`** — Azure resources: Resource Group, Container Registry, Container Apps Environment (for the running agency), Container Instances (ephemeral build sandbox — NOT Container Apps), PostgreSQL Flexible Server, Redis Cache (Basic C1, `noeviction` policy, 30-day TTL), Key Vault, Storage Account (for Blob vault), App Insights workspace. Spec: §6, §10.
- [ ] **`infra/terraform/variables.tf`** — Inputs: `location` (default: `westeurope`), `project_name`, `environment` (dev/staging/prod), `postgres_sku`, `redis_sku`.
- [ ] **`infra/terraform/outputs.tf`** — Outputs: `acr_login_server`, `aca_url`, `postgres_fqdn`, `redis_host`, `keyvault_uri`, `blob_storage_url`.
- [ ] **`infra/terraform/modules/aci-sandbox/`** — Reusable module for ephemeral ACI build sandbox. Inputs: `workspace_blob_url`, `docker_image`, `network_profile` (on for build phase, off for verify phase). Outputs: `test_output_url`.
- [ ] **`.github/workflows/infra.yml`** — Terraform plan on PR, apply on merge to main. Uses OIDC (not stored credentials). Runs `infracost comment` on PR with cost delta. Spec: §10.
- [ ] **`.github/workflows/ci.yml`** — On every PR: `pytest`, `vitest`, `import-linter` (forbids `agents/` importing `adapters/`), `SkillRegistry.validate_all()`, ruff + mypy. Spec: §1c.
- [ ] **`.github/workflows/deploy.yml`** — Build + push Docker image to ACR, deploy to ACA. Triggered on merge to main. Spec: §10.
- [ ] **`.github/workflows/eval.yml`** — Nightly: runs eval suite (§9b), posts results to GitHub PR comment or Slack. Spec: §9b.
- [ ] **`infra/pgbouncer/pgbouncer.ini`** — Pool mode = **session** (NOT transaction — transaction mode breaks RLS). Max client conn = 100. Server pool size = 20. Spec: §6.
- [ ] **`infra/redis/redis.conf`** — `maxmemory-policy noeviction`. TTL strategy: checkpoints = 30 days, hot state = 24h. Spec: §5.

---

### Phase 4 — Frontend Dashboard (requires Phase 2 gate API)

> **Who:** Frontend engineer. **Goal:** Sam-usable web UI. Non-technical user can approve gates and see results.

- [ ] **`frontend/`** — Next.js 15 app (TypeScript). Pages: `/` (project list), `/projects/[id]` (pipeline view + gates), `/projects/[id]/gate/[n]` (approval UI).
- [ ] **`frontend/components/GateApproval.tsx`** — WebSocket-connected gate component. Shows: cost display, artifact summary, YES/DEFER/GIVE NOTES buttons. Reconnect-safe (gate state from Redis). Spec: §7.
- [ ] **`frontend/components/ArtifactViewer.tsx`** — Renders: `DESIGN.md` (markdown), `*.svg` (inline SVG), `*.html` mockups (sandboxed iframe), `*.json` (collapsible tree). Spec: §7.
- [ ] **`frontend/components/CostDisplay.tsx`** — Shows LLM cost (from LiteLLM), infra estimate (from Infracost), total project spend. Updates in real-time via WebSocket. Spec: §9.
- [ ] **`frontend/components/GatePlainGuide.tsx`** — Plain-language Gate 2 and Gate 3 explanations for Sam. Gate 2: budget check + feature list. Gate 3: test results (green/red) only. Spec: §7 Plain-Language Gate Guide.
- [ ] **`frontend/components/PipelineStatus.tsx`** — Visual pipeline: 5 stages, current stage highlighted, completed stages with ✅, failed with ❌. Shows agent currently running.

---

### Phase 5 — Observability & Analytics (can start after Phase 3)

> **Who:** DevOps + backend engineer. **Goal:** Every generated app ships with monitoring. Agency itself is instrumented.

- [ ] **`backend/skills/observability/otel-injection.md`** — Skill file: instructions for Builder to inject OpenTelemetry into generated FastAPI app. Auto-instruments all HTTP routes. Sends to Azure App Insights. Spec: §16.
- [ ] **`backend/adapters/logging/otel.py`** — OtelAdapter for the agency itself. Traces every agent run as a span. Includes `project_id`, `agent_name`, `stage`, `tokens_used`, `usd_spent` as span attributes. Spec: §16.
- [ ] **`infra/dashboards/agency-performance.json`** — Azure Monitor workbook: token spend/day, gate approval rate, pipeline completion rate, per-agent latency, error rate. Spec: §17.
- [ ] **`infra/dashboards/generated-app-health.json`** — Azure Monitor workbook for generated apps: p50/p95 response time, error rate, active users, DB query latency. Spec: §16.
- [ ] **`infra/alerts/`** — Alert rules: generated app error rate > 5%, agency pipeline failure > 2 consecutive, daily LLM spend > $50, ACI sandbox timeout > 10min. Spec: §16.
- [ ] **`backend/analytics/copilot_report.py`** — Weekly agency performance report via Copilot SDK. Metrics: tokens/project, cost/project, gate approval rate, revision rate, skill improvement delta. Spec: §17.

---

### Phase 6 — Legal & Compliance (required before first paying user)

> **Who:** Founder + legal counsel. **Goal:** Pre-launch legal checklist complete. Not engineering tasks — but documented here for completeness.

- [ ] **Draft Terms of Service** — Key clauses: liability cap (fees paid in preceding 12 months), user owns all generated code, OWASP disclaimer, refund policy. Spec: §18.
- [ ] **Draft Privacy Policy** — Key clauses: data retention (90 days post-project), GDPR rights (access, erasure, portability), third-party processors list (Anthropic, OpenAI, Google, Azure, LangSmith). Spec: §18.
- [ ] **Implement GDPR deletion endpoint** — `DELETE /api/v1/users/me`: cascade-delete vault (Azure Blob), DB rows, Redis keys, Key Vault secrets. Audit log of deletion stored 7 years. Spec: §18b.
- [ ] **Napkin AI + Google Stitch ToS audit** — Verify commercial use permitted, data retention policy, fallback plan if ToS prohibits. Spec: §18e.
- [ ] **Anthropic + OpenAI API ToS audit** — Verify no prohibition on code generation for resale. Anthropic zero-retention API option. Spec: §18e.
- [ ] **Incident response SOP** — Written runbook: detect → contain (1h) → GDPR notification (72h) → user notification (7 days). Spec: §18c.
- [ ] **Data residency configuration** — EU users → Azure West Europe. US users → Azure East US. Choice presented at project creation. Spec: §18b.

---

### Deferred — Phase 4+ (do not build yet)

> These are fully designed in §13 but require 10+ shipped projects to be useful.

- [ ] **`backend/skills/registry/evolution/`** — Compound Step: auto-PR skill improvements after each project. Spec: §13f.
- [ ] **`backend/orchestrator/ooda.py`** — OODA loop meta-agent for agency self-improvement. Spec: §13.
- [ ] **`backend/skills/prompt-promotion.yml`** — Automated prompt versioning and promotion pipeline. Spec: §13.
- [ ] **Multi-model A/B testing** — Split traffic between Claude and GPT-4o on identical tasks, compare eval scores. Spec: §6b, §9b.
- [ ] **SOC 2 Type II audit** — Required for enterprise tier ($500+/mo). Target Phase 3 (post-PMF). Spec: §18c.
- [ ] **Enterprise tier** — Seat subscription, custom models, priority support. Target when 100+ projects shipped. Spec: §19a.

---

### Quick-start commands (once Phase 0-1 are complete)

```bash
# Install deps
cd backend && pip install -r requirements.txt

# Run unit tests (no Azure needed)
pytest tests/unit/ -v

# Run integration test with mocks (no Azure needed)
VAULT_ADAPTER=mock HUMAN_ADAPTER=mock LLM_ADAPTER=mock pytest tests/integration/ -v

# Validate all skill files
python -c "from backend.skills.registry import SkillRegistry; SkillRegistry.validate_all()"

# Run full pipeline locally (demo mode)
DEMO_MODE=true python -m backend.orchestrator --idea "Build me a task tracker for 3 people"

# Provision Azure infrastructure
cd infra/terraform && terraform init && terraform plan -var="environment=dev"
```

---

## 22. Harness Engineering — Building DevStack with AI Agents

> **Sources:** OpenAI "Harness Engineering" (2026), [bradygaster/squad](https://github.com/bradygaster/squad) framework.  
> **Principle:** Engineers don't write code — they design environments where agents write reliable code.

### 22a. Agent Legibility Requirements

DevStack's codebase must be **agent-legible**: AI coding tools (Copilot, Codex, Cursor) should be able to understand, navigate, and modify the project without human hand-holding.

Every PR must maintain or improve the Agent Legibility Score (7 metrics from OpenAI's Build Hour):

| Metric | Target | Enforcement |
|--------|--------|-------------|
| **Bootstrap self-sufficiency** | `make setup` works from clean clone | CI: `make setup && make test` on fresh container |
| **Task entry points** | All in `Makefile` (`setup`, `test`, `lint`, `dev`, `run`, `ci`) | CI: required Makefile targets exist |
| **Validation harness** | 80%+ test coverage on `core/` | CI: coverage gate on `core/` |
| **Linting & formatting** | Zero warnings from ruff + mypy + import-linter | CI: all linters pass |
| **Codebase map** | `AGENTS.md` (<120 lines) + `docs/architecture.md` (<200 lines) | CI: files exist and within line limits |
| **Doc structure** | Progressive disclosure: AGENTS.md → docs/ → PLAN.md | Manual: reviewer checks |
| **Decision records** | ADR for every architectural choice in `docs/decisions/` | Manual: reviewer checks for new decisions |

### 22b. Progressive Disclosure (AGENTS.md Pattern)

A single massive instruction file (like PLAN.md at 125KB) overwhelms agent context windows. Instead:

1. **AGENTS.md** (~80 lines) — The entry point. Quick commands, architecture rules, directory map, links to deeper docs.
2. **docs/architecture.md** (~150 lines) — Codebase map: what's where, how it connects, dependency rules.
3. **docs/decisions/** — Architecture Decision Records (ADRs): why we chose what.
4. **PLAN.md** (deep specs) — Full section-level detail, referenced by section number.

AI agents start at AGENTS.md and follow links only when they need deeper context. This is the same pattern OpenAI uses internally with Codex: "a short AGENTS.md serves as a map with pointers to deeper documentation."

### 22c. Encoding Taste Into the Codebase (Custom Lint Rules)

When a coding agent produces output that violates team preferences, the fix is not to improve the prompt — it's to write a lint rule that makes the violation mechanically impossible. The rule itself can be written by the coding agent.

| Rule | What it catches | Enforcement |
|------|----------------|-------------|
| No adapters in agents | `from adapters.` in `agents/` files | `import-linter` in CI |
| Session mode only | `pool_mode = "transaction"` in any config | Custom ruff rule |
| Parameterized RLS | f-string in SET LOCAL query | Custom ruff rule (AST check) |
| Pydantic v2 syntax | `class Config:` instead of `model_config = ConfigDict(...)` | Custom ruff rule |
| Skill token limit | Skill `.md` file > 2,000 tokens | `SkillRegistry.validate_all()` in CI |
| Middleware ordering | RLSMiddleware registered before AuthMiddleware | Structural integration test |

> **Compound effect:** Each developer's expertise becomes a lint rule. A frontend specialist adds React component rules. A security specialist adds OWASP rules. Every rule makes every agent on the team better.

### 22d. Decision Records (ADRs)

When an architectural decision is made (in PR, discussion, or review):

1. Create `docs/decisions/NNNN-short-title.md`
2. Format: Context → Decision → Consequences → Enforcement
3. Reference in AGENTS.md if it affects coding patterns
4. Existing ADRs:
   - `0001-hexagonal-architecture.md` — Why ports & adapters
   - `0002-fixed-tech-stack.md` — Why the stack is fixed in v1
   - `0003-pgbouncer-session-mode.md` — Why session mode, not transaction
   - `0004-aci-not-aca-sandbox.md` — Why ACI for build sandbox
   - `0005-tdd-red-green-mandatory.md` — Why red/green TDD is enforced

### 22e. Hook Pipeline (Squad-Inspired)

Inspired by the [Squad framework](https://github.com/bradygaster/squad)'s `HookPipeline`, DevStack agents execute through a hook pipeline that provides governance without modifying agent code:

```python
# backend/hooks/pipeline.py
class PreAgentHook(ABC):
    """Runs before each agent's run() method. Returns allow/block/modify."""
    async def check(self, agent_name: str, state: ProjectState) -> HookAction: ...

class PostAgentHook(ABC):
    """Runs after each agent's run() method. For audit, metrics, cleanup."""
    async def check(self, agent_name: str, state: ProjectState, result: ProjectState) -> HookAction: ...

# Built-in hooks (receive ports via constructor injection — same DI as agents):
# - BudgetGuard: blocks execution if token/USD budget exceeded (reads state.meta)
# - AuditLogger: logs every agent invocation via LoggingPort (injected, not direct I/O)
# - PIIFilter: scrubs sensitive data before LLM calls
# - GateEnforcer: blocks agent if prior gate not approved
```

Hook actions: `allow` (proceed), `block` (halt with reason), `modify` (transform state before/after).

### 22f. Knowledge Compounding

Each project shipped through the pipeline produces learning artifacts that compound over time:

1. **Skill improvement PRs** (§13f Compound Step) — already designed, auto-opens PR to improve the skill file used after each project.
2. **Agent history files** (new): `backend/skills/{agent}/history.md` — tracks patterns learned across projects. What worked, what failed, what was revised at each gate.
3. **Decision records** (new): key decisions from each project shipped are added to `docs/decisions/` when they reveal new architectural patterns.
4. **Garbage collection** (new): recurring agent tasks scan for documentation drift, unused imports, dead code, and test coverage gaps. Opens targeted cleanup PRs automatically.

> **Squad parallel:** Squad agents maintain `history.md` files per agent that persist across sessions. DevStack's skill evolution system (§13f) is the equivalent mechanism — but at the pipeline agent level rather than the development team level.

### 22g. Generated Apps Must Also Be Agent-Legible

The apps DevStack **generates** should score well on the Agent Legibility Score. This enables post-deployment maintenance by AI agents (Copilot, Codex) without the customer understanding the code.

Every generated app MUST include:

| File | Purpose |
|------|---------|
| `README.md` | Setup, test, lint, run commands |
| `Makefile` | `setup`, `test`, `lint`, `dev` targets |
| `AGENTS.md` | ~50-line entry point for AI coding agents |
| `.github/copilot-instructions.md` | Project-specific coding rules |
| `docs/architecture.md` | Generated from Architect's output |
| Test suite | Already mandatory via TDD (AH-3) |

This is added to the Builder agent's skill file requirements.

### 22h. Phase 0 — Harness Engineering Additions

These tasks are added to the Phase 0 backlog (no dependencies, start immediately):

- [ ] **`AGENTS.md`** — 80-line AI coding agent entry point. Bootstrap, commands, architecture rules, directory map, progressive disclosure links. Created: ✅
- [ ] **`Makefile`** — Standardized entry points wrapping existing commands. Created: ✅
- [ ] **`docs/decisions/0001-0005`** — Initial ADRs extracted from PLAN.md key decisions. Created: ✅
- [ ] **`docs/architecture.md`** — Codebase map and dependency graph. Created: ✅
- [ ] **`backend/hooks/pipeline.py`** — Pre/post agent execution hook pipeline (Squad pattern). Spec: §22e.
- [ ] **Custom ruff rules** — PgBouncer session mode, RLS parameterization, Pydantic v2 syntax. Spec: §22c.
- [ ] **Builder skill update** — Add agent-legibility requirements for generated apps. Spec: §22g.
- [ ] **CI validation** — Add AGENTS.md + Makefile existence checks to `.github/workflows/ci.yml`. Spec: §22a.

# 🗺️ DevStack Agency — Visual Architecture Guide

> **What this document is:** A visual companion to `PLAN.md`. If PLAN.md is the detailed blueprint, this is the poster on the wall. Read this first, then dive into PLAN.md sections for details.

---

## 1. The Problem We're Solving

### The Gap

```mermaid
graph LR
    A["💡 App Idea<br/>(plain English)"] -->|"THE GAP<br/>weeks + $$$"| B["🌐 Live Web App<br/>(deployed, tested, monitored)"]
    
    style A fill:#ffd700,stroke:#333
    style B fill:#90EE90,stroke:#333
```

**Today, crossing this gap requires:**

| Path | Cost | Time | Quality |
|------|------|------|---------|
| Hire a freelancer | $5,000–15,000 | 2–4 weeks | Variable (often no tests, no monitoring) |
| Hire a dev agency | $20,000–80,000 | 6–12 weeks | High but expensive |
| Build it yourself | Free (but your time) | 2–3 days just for boilerplate | Depends on your skill |
| Bolt.new / Lovable | $0–20 | 10 minutes | Prototype only — no auth, no DB, no deploy |

**Our solution:** An autonomous AI agency that crosses the gap in **~3 hours for under $25** — with tests, security, monitoring, and audit trail included.

---

## 2. System Overview — The 5-Agent Pipeline

```mermaid
graph LR
    subgraph "User Input"
        IDEA["💡 Plain English Idea"]
    end
    
    subgraph "Agent Pipeline"
        A["🔍 Analyst"] -->|Gate 0| D["🎨 Designer"]
        D -->|Gate 1| AR["📐 Architect"]
        AR -->|Gate 2| B["🔨 Builder"]
        B -->|Gate 3| DEP["🚀 Deployer"]
    end
    
    subgraph "Output"
        LIVE["🌐 Live Azure App"]
    end
    
    IDEA --> A
    DEP -->|Gate 4| LIVE
    
    style IDEA fill:#ffd700,stroke:#333
    style A fill:#E8F4FD,stroke:#2196F3
    style D fill:#E8F4FD,stroke:#2196F3
    style AR fill:#E8F4FD,stroke:#2196F3
    style B fill:#E8F4FD,stroke:#2196F3
    style DEP fill:#E8F4FD,stroke:#2196F3
    style LIVE fill:#90EE90,stroke:#333
```

### What Each Agent Does (and Why It Exists)

| Agent | What it does | Why it's separate | What it produces |
|-------|-------------|-------------------|-----------------|
| **🔍 Analyst** | Asks clarifying questions, locks scope | Prevents "build the wrong thing" — cheapest place to catch misunderstandings ($0 at Gate 0) | `intake.json` — structured requirements |
| **🎨 Designer** | Generates mockups, flow diagrams | Sam sees the app before any code — easy to change direction here vs after 500 lines of code | `DESIGN.md`, SVG flows, HTML mockups |
| **📐 Architect** | Designs database, APIs, auth model | Separates "what to build" from "how to structure it" — catches data model mistakes before code | `DATA_MODEL.md`, `API_CONTRACTS.md`, `AUTH_PLAN.md` |
| **🔨 Builder** | Writes tests first, then code | TDD is mandatory — the Builder can't skip tests. Catches bugs before deployment. | Tested code, GitHub PR, red/green test logs |
| **🚀 Deployer** | Provisions Azure infra, deploys app | Infrastructure-as-code ensures repeatability. Same Terraform for every project. | Live staging URL, Terraform state |

---

## 3. The 5 Human Gates — Why Humans Stay in the Loop

```mermaid
graph TD
    G0["🚦 Gate 0<br/>Scope Confirmation<br/><i>'Is this what you want?'</i>"]
    G1["🚦 Gate 1<br/>Design Review<br/><i>'Does this look right?'</i>"]
    G2["🚦 Gate 2<br/>Architecture + Budget<br/><i>'Is $45/mo within budget?'</i>"]
    G3["🚦 Gate 3<br/>Code + Tests<br/><i>'All tests green?'</i>"]
    G4["🚦 Gate 4<br/>Staging Verification<br/><i>'App works as described?'</i>"]
    
    G0 -->|"✅ Approve / ✏️ Notes / ⏭️ Defer"| G1
    G1 -->|"✅ / ✏️ / ⏭️"| G2
    G2 -->|"✅ / ✏️ / ⏭️"| G3
    G3 -->|"✅ / ✏️ / ⏭️"| G4
    G4 -->|"✅ Go Live"| DONE["🌐 Production"]
    
    style G0 fill:#FFF3CD,stroke:#FFC107
    style G1 fill:#FFF3CD,stroke:#FFC107
    style G2 fill:#FFF3CD,stroke:#FFC107
    style G3 fill:#FFF3CD,stroke:#FFC107
    style G4 fill:#FFF3CD,stroke:#FFC107
    style DONE fill:#90EE90,stroke:#333
```

**Why gates, not full automation?**
- "Human = board of directors" (Harper Reed principle). Agents propose, humans approve.
- Gates 0, 1, 4 are intuitive for anyone (look at mockups, check if app works).
- Gates 2-3 have plain-language guides — Sam checks budget and test results, not code.
- Each gate is a cheap undo point. Catching a mistake at Gate 0 costs $0. Catching it after deploy costs $20+.

**Gate actions:**
- **✅ Approve** — pipeline continues
- **✏️ Give Notes** — agent re-runs the stage with feedback
- **⏭️ Defer** — "Accept for now, address later" — pipeline continues, deferred items shown at Gate 4
- **24h timeout** — if no action taken, pipeline pauses (not fails). Resume anytime from AMC.

---

## 4. Architecture — Hexagonal / Ports & Adapters

```mermaid
graph TB
    subgraph "Core (never changes)"
        PORTS["core/ports.py<br/>─────────────<br/>LLMPort<br/>VaultPort<br/>ToolPort<br/>HumanPort<br/>LoggingPort"]
        STATE["core/state.py<br/>─────────────<br/>ProjectState<br/>ProjectMeta<br/>IntakeAnswers"]
        BASE["agents/base.py<br/>─────────────<br/>BaseAgent"]
    end
    
    subgraph "Agents (import only from Core)"
        AN["Analyst"]
        DE["Designer"]
        ARC["Architect"]
        BU["Builder"]
        DEP["Deployer"]
    end
    
    subgraph "Adapters (swappable)"
        LLM1["AnthropicAdapter"]
        LLM2["OpenAIAdapter"]
        LLM3["GeminiAdapter"]
        V1["AzureBlobVault"]
        V2["MockVault"]
        H1["WebSocketHuman"]
        H2["MockHumanPort"]
    end
    
    AN & DE & ARC & BU & DEP --> PORTS
    PORTS --> LLM1 & LLM2 & LLM3
    PORTS --> V1 & V2
    PORTS --> H1 & H2
    
    style PORTS fill:#E8F4FD,stroke:#2196F3,stroke-width:3px
    style STATE fill:#E8F4FD,stroke:#2196F3,stroke-width:3px
    style BASE fill:#E8F4FD,stroke:#2196F3,stroke-width:3px
```

**Why hexagonal?**
- **Agents never know which LLM they're using.** Swap Claude for GPT-4o by changing one YAML line — zero agent code changes.
- **Testing is trivial.** Plug in MockVault + MockHumanPort + MockLLM → full integration test with no Azure account.
- **Enforced by CI:** `import-linter` blocks any PR where `agents/` imports from `adapters/`. The architecture rule can't be accidentally broken.

**Why it matters for this project specifically:**
LLM providers change pricing, add features, and break APIs constantly. With hexagonal architecture, we absorb all of that in the adapter layer. The agents — the expensive, prompt-engineered part — stay stable.

---

## 5. Data Flow — How State Moves Through the Pipeline

```mermaid
sequenceDiagram
    participant Sam as 👤 Sam (User)
    participant AMC as 🖥️ AMC Dashboard
    participant Orch as ⚙️ Orchestrator
    participant Agent as 🤖 Agent
    participant Vault as 📦 Vault (Azure Blob)
    participant Redis as ⚡ Redis (Hot State)
    participant DB as 🗄️ PostgreSQL
    
    Sam->>AMC: "Build me a task tracker"
    AMC->>Orch: POST /api/v1/agency/projects
    Orch->>Redis: Create ProjectState (hot)
    Orch->>Agent: Run Analyst stage
    Agent->>Vault: Save intake.json
    Agent->>Redis: Update ProjectState.stage = "analyst"
    Agent->>Orch: Stage complete
    Orch->>AMC: WebSocket: pipeline.gate_opened (Gate 0)
    AMC->>Sam: 🔔 "Gate 0 ready for review"
    Sam->>AMC: ✅ Approve
    AMC->>Orch: Gate 0 approved
    Orch->>Agent: Run Designer stage
    Note over Agent,Vault: Cycle repeats for each stage...
    Agent->>Vault: Save all artifacts
    Orch->>Redis: ProjectState.stage = "done"
    Redis-->>Vault: Checkpoint archived (cold storage)
    Orch->>AMC: WebSocket: pipeline.completed
    AMC->>Sam: 🎉 "Your app is live!"
```

**Two memory layers (and why):**
- **Redis (hot):** Current pipeline state. Fast reads for real-time AMC updates. 24h TTL for active projects, 30-day TTL for checkpoints. If Redis dies, pipeline pauses but no data is lost (Vault has everything).
- **Azure Blob (cold):** All artifacts (code, designs, configs). Permanent. The "vault" that every agent writes to and reads from. One container per project. SAS URLs for binary assets (SVGs, mockups).

**Why not just a database?**
PostgreSQL stores user/project metadata and LLM call logs (structured, queryable). Redis stores hot pipeline state (fast, ephemeral). Blob stores artifacts (large, binary). Each storage layer does what it's best at.

---

## 6. Security Architecture

```mermaid
graph TB
    subgraph "Request Flow"
        REQ["HTTP Request"] --> AUTH["AuthMiddleware<br/>(JWT validation)"]
        AUTH -->|"sets request.state.user_id"| RLS["RLSMiddleware<br/>(SET LOCAL app.user_id = $1)"]
        RLS --> APP["Application Logic"]
        APP --> PG["PostgreSQL<br/>(RLS policies enforce isolation)"]
    end
    
    subgraph "Build Sandbox"
        CODE["Generated Code"] --> ACI["Azure Container Instances<br/>(ephemeral, isolated)"]
        ACI -->|"Phase 1: network ON"| BUILD["npm install / pip install"]
        ACI -->|"Phase 2: network OFF"| TEST["Run tests (isolated)"]
    end
    
    subgraph "Secrets"
        KV["Azure Key Vault"] --> APP
        KV -.->|"Never in code<br/>Never in env vars"| CODE
    end
    
    style AUTH fill:#FFCDD2,stroke:#F44336,stroke-width:2px
    style RLS fill:#FFCDD2,stroke:#F44336,stroke-width:2px
    style ACI fill:#FFCDD2,stroke:#F44336,stroke-width:2px
    style KV fill:#FFCDD2,stroke:#F44336,stroke-width:2px
```

**Key security decisions and why:**

| Decision | Why | What breaks if violated |
|----------|-----|------------------------|
| **Auth before RLS** in middleware stack | JWT must be validated before we trust the user_id for RLS | Attacker forges user_id → sees all data |
| **Parameterized `$1` queries** for SET LOCAL | f-strings allow SQL injection into the RLS context | Attacker injects `'; DROP TABLE users; --` |
| **PgBouncer session mode** | Transaction mode resets SET LOCAL on connection return | Silent RLS bypass → data leak between users |
| **ACI not ACA** for sandbox | ACA doesn't support Docker-in-Docker | Can't isolate generated code execution |
| **Network off in test phase** | Prevents generated code from phoning home | Exfiltration of secrets or user data |

---

## 7. Tech Stack — What and Why

```mermaid
graph TB
    subgraph "Frontend"
        NEXT["Next.js 15<br/>(TypeScript)"]
        TW["TailwindCSS"]
    end
    
    subgraph "Backend"
        FAST["FastAPI<br/>(Python 3.12)"]
        LG["LangGraph<br/>(Orchestrator)"]
        LITE["LiteLLM<br/>(Model Router)"]
    end
    
    subgraph "Data"
        PG["PostgreSQL<br/>+ PgBouncer"]
        RD["Redis<br/>(noeviction)"]
        BLOB["Azure Blob<br/>(Vault)"]
    end
    
    subgraph "Infrastructure"
        TF["Terraform"]
        ACA["Azure Container Apps"]
        ACI["Azure Container Instances<br/>(Sandbox)"]
        KV["Azure Key Vault"]
        AI["App Insights<br/>(OpenTelemetry)"]
    end
    
    subgraph "CI/CD"
        GHA["GitHub Actions"]
        GH["GitHub<br/>(Repos + Projects)"]
    end
    
    subgraph "Design"
        GEM["Gemini<br/>(Design brief)"]
        NAP["Napkin AI<br/>(Flow SVGs)"]
        STI["Google Stitch<br/>(HTML mockups)"]
    end
    
    NEXT --> FAST
    FAST --> PG & RD & BLOB
    FAST --> LITE --> LLM["Claude / GPT-4o / Gemini"]
    TF --> ACA & ACI & KV & AI
    GHA --> TF
```

**Why this stack is fixed (and why that's a feature, not a limitation):**

The #1 cause of AI hallucination in code generation is **framework choice ambiguity**. "Should I use React or Vue? Express or FastAPI? AWS or Azure?" Each decision doubles the prompt complexity and halves the code quality.

By fixing the stack, we:
1. **Eliminate decision hallucination** — the agent never wastes tokens choosing between frameworks
2. **Maximize prompt quality** — every skill file is optimized for exactly this stack
3. **Enable compound learning** — each project improves the skills for the SAME stack, so quality compounds

**Why THESE specific technologies:**

| Choice | Why this one |
|--------|-------------|
| **Next.js** | Most popular React framework. Largest skill training corpus. Server components reduce client complexity. |
| **FastAPI** | Async Python + automatic OpenAPI docs + Pydantic validation. The generated API is self-documenting. |
| **PostgreSQL** | RLS support (critical for multi-tenancy). The most battle-tested open-source DB. |
| **Azure** | ACI for ephemeral sandboxes (unique capability). Enterprise-friendly. Key Vault for secrets. |
| **Terraform** | Declarative, repeatable, auditable. The agent can generate and validate infra configs deterministically. |

---

## 8. Anti-Hallucination Contract — The 4 Rules

```mermaid
graph TD
    AH1["AH-1: Structured Schemas Only<br/>──────────────────<br/>Every LLM call uses Pydantic<br/>output schemas. No free-form text.<br/>Validator rejects + auto-retries ×3."]
    AH2["AH-2: Tool Calls Before Answer<br/>──────────────────<br/>No agent may state a fact<br/>without grounding it in a<br/>real tool call first."]
    AH3["AH-3: Code Must Execute<br/>──────────────────<br/>Builder cannot pass Gate 3<br/>on schema validation alone.<br/>Docker sandbox run is mandatory."]
    AH4["AH-4: Requirement is Frozen<br/>──────────────────<br/>The original user requirement<br/>from intake is NEVER modified.<br/>Scope can be refined, not changed."]
    
    AH1 & AH2 & AH3 & AH4 --> TRUST["🛡️ Trustworthy Output"]
    
    style AH1 fill:#E3F2FD,stroke:#1976D2
    style AH2 fill:#E3F2FD,stroke:#1976D2
    style AH3 fill:#E3F2FD,stroke:#1976D2
    style AH4 fill:#E3F2FD,stroke:#1976D2
    style TRUST fill:#C8E6C9,stroke:#4CAF50,stroke-width:3px
```

**Why these specific rules?**
- **AH-1** prevents the most common AI failure: unstructured output that drifts from spec. Pydantic schemas reject invalid output and auto-retry with error feedback.
- **AH-2** creates an audit trail — every claim is grounded in a tool call (`web_search`, `read_file`, `run_tests`), never fabricated from training data.
- **AH-3** prevents "it looks right" code that actually crashes at runtime — the Docker sandbox catches this. TDD forces tests written first (red phase) before implementation (green phase).
- **AH-4** prevents scope creep — the single biggest risk in any software project. The `original_requirement` field is `frozen=True` in Pydantic and never summarized away.

---

## 9. Cost Flow — Where Money Goes

```mermaid
graph LR
    subgraph "Per Project (~$24)"
        LLM["LLM Calls<br/>~$12"]
        AZURE["Azure Infra<br/>~$8"]
        MARKUP["Agency Fee (20%)<br/>~$4"]
    end
    
    LLM --> LITELLM["LiteLLM Router<br/>(tracks per-call)"]
    AZURE --> INFRA["Infracost<br/>(estimates pre-Gate 2)"]
    MARKUP --> REV["Revenue"]
    
    LITELLM --> DB["PostgreSQL<br/>llm_calls table"]
    INFRA --> STATE["ProjectState<br/>.meta.monthly_infra_estimate"]
    DB & STATE --> AMC["AMC Cost Dashboard<br/>'$3.42 LLM + $5/mo Azure'"]
    
    style LLM fill:#BBDEFB,stroke:#1976D2
    style AZURE fill:#BBDEFB,stroke:#1976D2
    style MARKUP fill:#C8E6C9,stroke:#4CAF50
```

**Cost controls (why each exists):**

| Control | Why |
|---------|-----|
| **Token budget per project** | Prevents runaway LLM costs from a single complex project |
| **Circuit breaker (3 failures)** | If an LLM is misbehaving, stop spending money and switch to fallback |
| **Infracost before Gate 2** | Sam sees the Azure bill BEFORE infrastructure is provisioned — can change scope |
| **LiteLLM per-call logging** | Every cent is tracked. No surprise bills. Full cost audit trail. |
| **Hard USD budget cap** | User sets max spend at intake. Pipeline halts (not silently overruns) if exceeded. |

---

## 10. SDLC — Full Software Development Lifecycle

```mermaid
graph TB
    subgraph "Phase 1: Requirements"
        I1["User describes idea"] --> I2["Analyst asks clarifying questions"]
        I2 --> I3["IntakeAnswers validated"]
        I3 --> G0["🚦 Gate 0: Scope Lock"]
    end
    
    subgraph "Phase 2: Design"
        G0 --> D1["Gemini generates design brief"]
        D1 --> D2["Napkin AI creates flow SVGs"]
        D2 --> D3["Stitch creates HTML mockups"]
        D3 --> G1["🚦 Gate 1: Design Review"]
    end
    
    subgraph "Phase 3: Architecture"
        G1 --> A1["Data model design"]
        A1 --> A2["API contracts"]
        A2 --> A3["Auth plan + Infracost estimate"]
        A3 --> G2["🚦 Gate 2: Architecture + Budget"]
    end
    
    subgraph "Phase 4: Build & Test"
        G2 --> B1["🔴 Write failing tests (RED)"]
        B1 --> B2["🟢 Write code to pass (GREEN)"]
        B2 --> B3["Run in ACI sandbox"]
        B3 --> B4["OWASP security check"]
        B4 --> B5["Open GitHub PR"]
        B5 --> G3["🚦 Gate 3: Code + Tests"]
    end
    
    subgraph "Phase 5: Deploy"
        G3 --> E1["Terraform plan"]
        E1 --> E2["Terraform apply"]
        E2 --> E3["Deploy to ACA"]
        E3 --> E4["Inject OpenTelemetry"]
        E4 --> E5["Staging URL ready"]
        E5 --> G4["🚦 Gate 4: Staging Verify"]
    end
    
    subgraph "Phase 6: Live"
        G4 --> L1["🌐 Production deploy"]
        L1 --> L2["Monitoring active"]
        L2 --> L3["Audit trail complete"]
    end
```

---

## 11. Agency Management Console (AMC) — The Control Plane

```mermaid
graph TB
    subgraph "AMC Dashboard"
        S1["📊 Project Dashboard<br/>All projects at a glance"]
        S2["🔄 Pipeline Monitor<br/>Live single-project view"]
        S3["✅ Gate Queue<br/>All pending approvals"]
        S4["➕ New Idea Intake<br/>Start a new project"]
        S5["💰 Cost Dashboard<br/>Spend tracking"]
        S6["🏥 Health Monitor<br/>Infrastructure status"]
        S7["📈 Skill Performance<br/>Agent improvement over time"]
    end
    
    subgraph "Real-time"
        WS["WebSocket /ws/agency<br/>(server-side filtered)"]
    end
    
    subgraph "Roles"
        ADMIN["👑 Admin<br/>All screens, all projects"]
        OWNER["👤 Owner (Sam)<br/>Own projects, gate approval"]
        VIEWER["👁️ Viewer<br/>Read-only, no approve"]
    end
    
    WS --> S1 & S2 & S3 & S5 & S6
    ADMIN --> S1 & S2 & S3 & S4 & S5 & S6 & S7
    OWNER --> S1 & S2 & S3 & S4 & S5
    VIEWER --> S1 & S2 & S5
```

**Why the AMC exists:**
When you're running multiple projects, you need one place to see everything — which projects are running, which gates need approval, how much you're spending. Without the AMC, you'd be checking email, GitHub, and Azure Portal separately. The AMC replaces all of that with a single dashboard.

---

## 12. How Everything Connects — Full System Map

```mermaid
graph TB
    USER["👤 Sam"] -->|"idea + budget"| AMC["🖥️ AMC Dashboard"]
    AMC -->|"REST API"| API["FastAPI Backend"]
    AMC <-->|"WebSocket"| WS["WS Broadcaster"]
    
    API --> ORCH["⚙️ LangGraph Orchestrator"]
    ORCH --> AGENTS["🤖 5 Agents"]
    
    AGENTS -->|"structured_call()"| ROUTER["LiteLLM Router"]
    ROUTER --> CLAUDE["Claude"] & GPT["GPT-4o"] & GEMINI["Gemini"]
    
    AGENTS -->|"save/load"| VAULT["📦 Azure Blob Vault"]
    AGENTS -->|"checkpoint"| REDIS["⚡ Redis"]
    
    ORCH -->|"gate opened"| WS
    WS -->|"server-filtered"| AMC
    
    API -->|"RLS-enforced"| PG["🗄️ PostgreSQL"]
    
    ORCH -->|"terraform apply"| AZURE["☁️ Azure (ACA + ACI)"]
    AZURE -->|"staging URL"| AMC
    
    AGENTS -->|"telemetry"| OTEL["📊 OpenTelemetry → App Insights"]
    
    style USER fill:#ffd700,stroke:#333
    style AMC fill:#E8EAF6,stroke:#3F51B5,stroke-width:2px
    style ORCH fill:#E8F4FD,stroke:#2196F3,stroke-width:2px
    style AGENTS fill:#E8F4FD,stroke:#2196F3
```

---

## 13. Building DevStack — Harness Engineering Approach

> **Source:** OpenAI "Harness Engineering" (2026) + [Squad](https://github.com/bradygaster/squad) framework patterns.

```mermaid
graph LR
    subgraph "Traditional Development"
        ENG1["👨‍💻 Engineer"] -->|"writes"| CODE1["📝 Code"]
        CODE1 -->|"reviews"| REVIEW1["🔍 Review"]
        REVIEW1 -->|"deploys"| DEPLOY1["🚀 Deploy"]
    end
    
    subgraph "Harness Engineering"
        ENG2["👨‍💻 Engineer"] -->|"writes"| HARNESS["🔧 Harness<br/>(AGENTS.md + lints + tests + ADRs)"]
        HARNESS -->|"guides"| AGENT["🤖 AI Agent<br/>writes code"]
        AGENT -->|"validates via"| HARNESS
        ENG2 -->|"reviews"| AGENT
    end
    
    style HARNESS fill:#E8F4FD,stroke:#2196F3,stroke-width:3px
    style AGENT fill:#C8E6C9,stroke:#4CAF50
```

**What makes our repo agent-legible:**

| Layer | File | Purpose |
|-------|------|---------|
| **Entry point** | `AGENTS.md` | ~80 lines — first thing any AI agent reads |
| **Commands** | `Makefile` | `make setup`, `test`, `lint`, `dev`, `ci` |
| **Architecture** | `docs/architecture.md` | Codebase map + dependency rules |
| **Decisions** | `docs/decisions/` | ADR files — why we chose what |
| **Guardrails** | Lint rules + CI | Mechanical enforcement of architecture |
| **Deep specs** | `PLAN.md` | Full detail (referenced from AGENTS.md) |

**Progressive disclosure:** AGENTS.md → docs/ → PLAN.md (shallow → deep). AI agents start at AGENTS.md and follow links only when they need deeper context. This prevents overwhelming agent context windows with 125KB of spec.

**Knowledge compounds:** Every lint rule, skill file, or ADR a developer adds makes every AI agent on the team better. A frontend expert encodes React patterns → everyone's agents produce better React. A security expert encodes OWASP rules → everyone's agents produce safer code.

> Full spec: PLAN.md §22

---

## Quick Reference — Section Map to PLAN.md

| This section | Explains | PLAN.md detail |
|---|---|---|
| §1 Problem | Why this exists | §0 Product North Star |
| §2 Pipeline | The 5 agents | §2 Agent Roster |
| §3 Gates | Human approval design | §7 HITL Design |
| §4 Architecture | Hexagonal / ports | §1c Clean Architecture |
| §5 Data flow | State + memory | §5 Memory, §8 BaseAgent |
| §6 Security | Auth, RLS, sandbox | §6 Tech Stack |
| §7 Tech stack | What and why | §6 Tech Stack |
| §8 AH rules | Anti-hallucination | §1b AH Contract |
| §9 Cost flow | Cost tracking | §9 Cost Controls, §19 Business |
| §10 SDLC | Full lifecycle | §4 Core Loop, §10 Build Phases |
| §11 AMC | Dashboard overview | §21 AMC |
| §12 System map | Everything connected | Whole document |
| §13 Harness engineering | How we build with AI agents | §22 Harness Engineering |

---

*This document uses [Mermaid](https://mermaid.js.org/) diagrams. View in any Mermaid-compatible renderer (GitHub, VS Code with Mermaid extension, Obsidian, etc.).*

# ADR-0001: Hexagonal Architecture (Ports & Adapters)

**Status:** Accepted  
**Date:** 2025 (project inception)  
**Reference:** PLAN.md §1c

## Context

Agents must be testable without calling real LLMs, deployable to any cloud, and swappable between providers. LLM providers change pricing, add features, and break APIs constantly. The expensive part (prompt-engineered agents) must be insulated from provider churn.

## Decision

Adopt hexagonal architecture with 5 port interfaces (`LLMPort`, `VaultPort`, `ToolPort`, `HumanPort`, `LoggingPort`). Agents depend ONLY on abstractions in `core/ports.py`. Concrete implementations (Anthropic SDK, Azure SDK, etc.) live in `adapters/` and are injected via constructor.

## Consequences

- **Positive:** Swap Claude for GPT-4o by changing one YAML line — zero agent code changes.
- **Positive:** Full integration tests with MockVault + MockHumanPort + MockLLM — no Azure account needed.
- **Positive:** Architecture rule enforced by CI (`import-linter` blocks any PR where `agents/` imports from `adapters/`).
- **Negative:** More boilerplate (port interfaces + adapter classes for each provider).
- **Negative:** Developers must understand dependency inversion to contribute.

## Enforcement

- `import-linter` in CI: `agents/` cannot import `adapters/`
- `mypy --strict`: all port implementations must satisfy the abstract interface

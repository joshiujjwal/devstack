# ADR-0005: Mandatory Red/Green TDD

**Status:** Accepted  
**Date:** 2025 (project inception)  
**Reference:** PLAN.md §1 (Principle 1), §4 (Builder agent)

## Context

AI-generated code can "look right" but fail at runtime. Without a mandatory test-first approach, the Builder agent could generate code that passes schema validation but crashes in production. This is the most common failure mode in AI code generation.

## Decision

Red/green TDD is mandatory for the Builder agent. The process is:

1. **Red phase:** Write failing tests first. Run them. Confirm they fail. Vault the red-phase log to `4_app/red_phase.txt`.
2. **Green phase:** Write code until all tests pass. Run in ACI sandbox (not just schema validation).
3. **Gate 3:** Cannot be passed without both a red-phase log AND a green test run from the Docker sandbox.

## Consequences

- **Positive:** Every line of generated code is covered by tests written before the implementation.
- **Positive:** AH-3 (code must execute) is mechanically enforced — not just "looks correct."
- **Positive:** Red-phase log proves the test was written first (not retrofitted to match code).
- **Negative:** Slower code generation (two-pass: tests then implementation).
- **Negative:** Builder agent needs more tokens (test code + implementation code).

## Enforcement

- Gate 3 blocks if `4_app/red_phase.txt` is missing from vault
- Gate 3 blocks if Docker sandbox test run didn't execute
- Builder skill file (`backend/skills/builder/system-v1.md`) mandates the red-phase step
- AH-3 contract in `CONSTITUTION.md` references this decision

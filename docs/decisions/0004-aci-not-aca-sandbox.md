# ADR-0004: ACI (Not ACA) for Build Sandbox

**Status:** Accepted  
**Date:** 2025 (project inception)  
**Reference:** PLAN.md §6

## Context

The Builder agent generates code that must be executed in an isolated sandbox before it can pass Gate 3. This requires Docker-in-Docker capability — the sandbox runs `pytest` and `vitest` inside a container with the generated app's dependencies installed.

Azure offers two container hosting options:
- **Azure Container Apps (ACA):** Managed Kubernetes-based service. Does NOT support Docker-in-Docker.
- **Azure Container Instances (ACI):** Ephemeral, isolated containers. Supports Docker-in-Docker.

## Decision

Use ACI for the ephemeral build sandbox. ACA is used for the running agency and deployed apps.

## Consequences

- **Positive:** Full Docker-in-Docker support for isolated code execution.
- **Positive:** Ephemeral containers — each build gets a fresh, clean environment.
- **Positive:** Two-phase execution: Phase 1 (network ON) for `npm install`/`pip install`, Phase 2 (network OFF) for test execution — prevents exfiltration.
- **Negative:** ACI is less feature-rich than ACA (no autoscaling, no managed ingress).
- **Negative:** ACI startup time is slower than pre-warmed ACA instances.

## Enforcement

- Terraform module: `infra/terraform/modules/aci-sandbox/` is the only sandbox provisioner
- Agent skill files explicitly reference ACI, not ACA
- Code review checklist includes ACI/ACA distinction

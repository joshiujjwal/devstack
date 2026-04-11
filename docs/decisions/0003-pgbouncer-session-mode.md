# ADR-0003: PgBouncer Session Mode (Not Transaction Mode)

**Status:** Accepted  
**Date:** 2025 (project inception)  
**Reference:** PLAN.md §6

## Context

DevStack uses PostgreSQL Row-Level Security (RLS) for multi-tenant data isolation. RLS relies on `SET LOCAL app.user_id = $1` to scope queries to the current user. PgBouncer is used for connection pooling.

PgBouncer has two primary pool modes:
- **Transaction mode:** Returns connections to the pool after each transaction. Higher throughput.
- **Session mode:** Returns connections to the pool after the client disconnects. Lower throughput.

## Decision

Use PgBouncer **session mode** exclusively. Transaction mode is explicitly prohibited.

## Consequences

- **Positive:** `SET LOCAL` persists for the duration of the client session — RLS works correctly.
- **Positive:** No silent data leaks between users.
- **Negative:** Lower connection throughput (each client holds a server connection for the full session).
- **Negative:** Requires more careful connection management (close connections promptly).

## Why Transaction Mode Breaks RLS

Transaction mode resets `SET LOCAL app.user_id` when the connection is returned to the pool. The next request that gets that connection may execute queries with the *previous* user's ID still set (or no ID at all), bypassing RLS entirely. This is a **silent data leak** — no error is raised, but User A sees User B's data.

## Enforcement

- `infra/pgbouncer/pgbouncer.ini`: `pool_mode = session` (hardcoded)
- CI: Custom lint rule flags `pool_mode = "transaction"` in any config file
- Integration test: `test_rls_middleware.py` verifies parameterized queries used

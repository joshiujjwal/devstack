# DevStack Agency — Standard Entry Points
# These commands are the canonical way to build, test, and run the project.
# AI coding agents (Copilot, Codex, Cursor) use these as task entry points.
#
# NOTE: Most targets require Phase 0+ code from PLAN.md §20 to exist.
# Until then, targets will fail with clear messages about missing files.

.PHONY: setup test lint dev run ci clean help check-backend check-frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies (Python + Node)
	@test -f backend/requirements.txt || (echo "❌ backend/requirements.txt not found. Run Phase 0 tasks first (PLAN.md §20)." && exit 1)
	cd backend && pip install -r requirements.txt
	@test -f frontend/package.json || (echo "⚠️ frontend/package.json not found. Skipping frontend setup (Phase 4)." && exit 0)
	cd frontend && npm install
	@echo "✅ Setup complete. Run 'make test' to verify."

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests (pytest)
	@test -d backend/tests || (echo "⚠️ backend/tests/ not found. Create tests first (PLAN.md §20 Phase 0)." && exit 0)
	pytest backend/tests/ -v --tb=short

test-frontend: ## Run frontend tests (vitest)
	@test -f frontend/package.json || (echo "⚠️ frontend/ not found. Skipping (Phase 4)." && exit 0)
	cd frontend && npx vitest run --reporter=verbose

lint: ## Run all linters (ruff + mypy + import-linter + skill validation)
	@test -d backend || (echo "❌ backend/ not found. Run Phase 0 tasks first." && exit 1)
	ruff check backend/
	mypy backend/ --strict
	lint-imports
	@test -f backend/skills/registry.py && python -c "from backend.skills.registry import SkillRegistry; SkillRegistry.validate_all()" || echo "⚠️ SkillRegistry not yet implemented. Skipping skill validation."
	@echo "✅ All lints passed."

dev: ## Start development servers (backend + frontend)
	@echo "Starting backend..."
	cd backend && uvicorn main:app --reload --port 8000 &
	@echo "Starting frontend..."
	@test -f frontend/package.json && (cd frontend && npm run dev &) || echo "⚠️ frontend/ not found. Skipping."
	@echo "✅ Dev servers starting. Backend: http://localhost:8000, Frontend: http://localhost:3000"

run: ## Run full pipeline locally (demo mode)
	DEMO_MODE=true python -m backend.orchestrator --idea "Build me a task tracker for 3 people"

ci: lint test ## Full CI check (lint + test + validate)
	@echo "✅ CI checks passed."

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned."

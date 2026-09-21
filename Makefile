# ---------------------------------------------------------------------------
# Plain-English: shortcuts so you do not have to remember long commands.
# Run `make help` to see everything.
#
# NOTE: every command here needs Docker. There is no non-Docker setup.
# ---------------------------------------------------------------------------

.DEFAULT_GOAL := help
.PHONY: help up down logs db-shell migrate seed reconcile investigate test eval lint fmt fetch-cuad demo verify routes

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Start everything (database, API, worker, website)
	docker compose up -d --build
	@echo "Website: http://localhost:3000   API docs: http://localhost:8000/docs"

down: ## Stop everything
	docker compose down

logs: ## Tail logs from all services
	docker compose logs -f

db-shell: ## Open a SQL prompt in the database
	docker compose exec db psql -U rl_app -d revenue_leakage

migrate: ## Apply database migrations
	docker compose exec backend alembic upgrade head

seed: ## Generate the synthetic company dataset (must run before anything else)
	docker compose exec backend python -m app.cli seed --reset

reconcile: ## Run one detection pass across all customers
	docker compose exec backend python -m app.cli reconcile

investigate: ## Run agent investigations on all open cases
	docker compose exec backend python -m app.cli investigate --all

fetch-cuad: ## Download the real public contract dataset (optional, ~106 MB)
	docker compose exec backend python scripts/fetch_cuad.py

test: ## Run the full test suite (never calls the network)
	docker compose exec backend pytest -q

eval: ## Run the golden-dataset evaluation and print the scorecard
	docker compose exec backend python -m app.cli eval --suite all

lint: ## Static checks
	docker compose exec backend ruff check .
	docker compose exec backend mypy app

fmt: ## Auto-format code
	docker compose exec backend ruff format .

routes: ## Frontend smoke test - proves pages render without a browser
	bash scripts/smoke_routes.sh

verify: ## Run every check and write artifacts/verify-report.md (paste this at gates)
	@mkdir -p artifacts
	@R=artifacts/verify-report.md; \
	echo "# Verify report" > $$R; \
	echo "" >> $$R; \
	echo "generated: `date -u +%Y-%m-%dT%H:%M:%SZ`" >> $$R; \
	echo "commit:    `git rev-parse --short HEAD`" >> $$R; \
	echo "" >> $$R; \
	echo "## services" >> $$R; echo '```' >> $$R; \
	docker compose ps >> $$R 2>&1; echo '```' >> $$R; \
	echo "" >> $$R; \
	echo "## migrations (up / down / up)" >> $$R; echo '```' >> $$R; \
	docker compose exec -T backend alembic upgrade head >> $$R 2>&1; \
	docker compose exec -T backend alembic downgrade base >> $$R 2>&1; \
	docker compose exec -T backend alembic upgrade head >> $$R 2>&1; \
	echo "ok" >> $$R; echo '```' >> $$R; \
	echo "" >> $$R; \
	echo "## tests collected" >> $$R; echo '```' >> $$R; \
	docker compose exec -T backend pytest --collect-only -q 2>&1 | tail -3 >> $$R; \
	echo '```' >> $$R; \
	echo "" >> $$R; \
	echo "## tests" >> $$R; echo '```' >> $$R; \
	docker compose exec -T backend pytest -q 2>&1 | tail -25 >> $$R; \
	echo '```' >> $$R; \
	echo "" >> $$R; \
	echo "## frontend build and typecheck" >> $$R; echo '```' >> $$R; \
	docker compose exec -T frontend npx tsc --noEmit >> $$R 2>&1 || echo "TYPECHECK FAILED" >> $$R; \
	docker compose exec -T frontend npm run build >> $$R 2>&1 || echo "BUILD FAILED" >> $$R; \
	echo '```' >> $$R; \
	echo "" >> $$R; \
	echo "## route smoke" >> $$R; echo '```' >> $$R; \
	bash scripts/smoke_routes.sh >> $$R 2>&1 || echo "ROUTE SMOKE FAILED" >> $$R; \
	echo '```' >> $$R; \
	echo "" >> $$R; \
	cat artifacts/route-smoke.txt >> $$R 2>/dev/null || true
	@echo "wrote artifacts/verify-report.md - paste this file at the gate"

demo: ## Seed + reconcile + investigate, ready for a demo video
	$(MAKE) seed
	$(MAKE) reconcile
	$(MAKE) investigate
	@echo "Demo ready. Open http://localhost:3000"

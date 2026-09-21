# ---------------------------------------------------------------------------
# Plain-English: shortcuts so you do not have to remember long commands.
# Run `make help` to see everything.
#
# NOTE: every command here needs Docker. There is no non-Docker setup.
# ---------------------------------------------------------------------------

.DEFAULT_GOAL := help
.PHONY: help up down logs db-shell migrate seed reconcile investigate test eval lint fmt fetch-cuad demo

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

demo: ## Seed + reconcile + investigate, ready for a demo video
	$(MAKE) seed
	$(MAKE) reconcile
	$(MAKE) investigate
	@echo "Demo ready. Open http://localhost:3000"

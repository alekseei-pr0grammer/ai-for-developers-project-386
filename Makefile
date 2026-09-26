# Common commands. Run `make help` to list them.
.PHONY: help install db dev-api dev-web api-client lint test build up down

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	cd backend && uv sync
	cd frontend && npm ci

db: ## Start only Postgres (for local development)
	docker compose up -d db

dev-api: ## Run FastAPI with auto-reload on :8000 (applies migrations first)
	cd backend && uv run alembic upgrade head && uv run fastapi dev app/main.py

dev-web: ## Run Vite dev server on :5173 (proxies /api to :8000)
	cd frontend && npm run dev

api-client: ## Regenerate the typed TS client after changing the API
	cd backend && uv run python scripts/export_openapi.py ../frontend/openapi.json
	cd frontend && npm run api:generate

lint: ## Lint and type-check everything
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint && npm run typecheck

test: ## Run tests
	cd backend && uv run pytest

build: ## Build production Docker images
	docker compose build

up: ## Run the full stack in Docker on http://localhost:8080
	docker compose up --build

down: ## Stop the Docker stack
	docker compose down

# Common commands. Run `make help` to list them.
.PHONY: help install db dev-api dev-web api-client lint test build up down image-check

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	cd backend && uv sync
	cd frontend && npm ci

db: ## Start only Postgres (for local development)
	docker compose up -d --wait db

dev-api: ## Run FastAPI with auto-reload on :8000 (applies migrations first)
	cd backend && uv run alembic upgrade head && SESSION_COOKIE_SECURE=false uv run fastapi dev app/main.py

dev-web: ## Run Vite dev server on :5173 (proxies /api to :8000)
	cd frontend && npm run dev

api-client: ## Regenerate the typed TS client after changing the API
	cd backend && uv run python scripts/export_openapi.py ../frontend/openapi.json
	cd frontend && npm run api:generate

lint: ## Lint and type-check everything
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint && npm run typecheck

test: db ## Run tests (against the calendar_test database on the local Postgres)
	cd backend && uv run pytest

build: ## Build the production Docker image
	docker compose build

image-check: ## Run the image like Hexlet's check (only PORT, no database) and expect GET / = 200
	docker build -t calendar-app:check .
	docker rm -f calendar-app-check >/dev/null 2>&1 || true
	docker run -d --name calendar-app-check -e PORT=8080 -p 8081:8080 calendar-app:check >/dev/null
	@for i in $$(seq 1 30); do \
		status=$$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8081/ || true); \
		[ "$$status" = 200 ] && break; sleep 1; \
	done; \
	docker rm -f calendar-app-check >/dev/null; \
	if [ "$$status" = 200 ]; then echo "GET / -> 200"; else echo "GET / -> $$status" >&2; exit 1; fi

up: ## Run the full stack in Docker on http://localhost:8080
	docker compose up --build

down: ## Stop the Docker stack
	docker compose down

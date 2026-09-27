# Requirements
1. Always fix the root cause not the consequence
2. If there's a code you didn't write - don't touch it if not asked

# Project
Booking calendar service (like cal.com). Hexlet learning project.

```
React (Vite) + shadcn/ui + Tailwind  →  static files (nginx in Docker, or a CDN)
        │  JSON over /api, typed client generated from OpenAPI
        ▼
FastAPI  →  Postgres
```

## Layout
- `backend/`: FastAPI app (Python 3.14, managed by `uv`)
  - `app/main.py`: app and router wiring. All routes live under `/api`.
  - `app/api/`: one router module per resource
  - `app/models/`: SQLAlchemy models. Import each one in `app/models/__init__.py`.
  - `app/config.py`: settings from env vars (`DATABASE_URL`, `CORS_ORIGINS`)
  - `migrations/`: Alembic migrations
- `frontend/`: Vite + React 19 + TypeScript + Tailwind v4 + shadcn/ui
  - `src/components/ui/`: shadcn components (added via CLI, owned by us)
  - `src/api/generated/`: **generated** API client. Never edit by hand.
  - `src/api/client-config.ts`: API base URL (`VITE_API_BASE_URL`, empty = same origin)
  - `openapi.json`: API contract snapshot exported from the backend
- `compose.yaml`: full stack locally (db → migrate → api → web)
- `.github/workflows/hexlet-check.yml`: Hexlet's workflow. **Never edit, rename or delete it.**
- `.github/workflows/ci.yml`: our CI, runs on every push to any branch
- `.github/workflows/release-please.yml`: on push to `main`, opens or updates the release PR

## Commands (run from repo root, `make help` lists all)
- `make install`: install deps
- `make db`, then `make dev-api` and `make dev-web`: local dev at http://localhost:5173
- `make up`: full stack in Docker at http://localhost:8080
- `make lint`, `make test`: must pass before finishing a task
- `make api-client`: regenerate the TS client after any API change

## Rules
- **API changes:** edit FastAPI (Pydantic models are the source of truth), then run `make api-client` and commit `openapi.json` and `src/api/generated/` together with the backend change. CI fails if they're out of sync. Don't hand-write fetch calls or duplicate API types in the frontend.
- **Frontend data fetching:** use TanStack Query with the generated `*Options()` helpers from `@/api/generated/@tanstack/react-query.gen`.
- **UI:** use shadcn/ui components (`npx shadcn@latest add <name>` in `frontend/`) and Tailwind classes. No other UI kits, no per-component CSS files.
- **DB schema changes:** only through Alembic: `cd backend && uv run alembic revision --autogenerate -m "..."`. Review the generated file. Never change tables by hand.
- **Time:** store and transfer datetimes in UTC (timezone-aware). Convert to the user's time zone only in the UI.
- **Booking integrity:** enforce "no overlapping bookings" in the database (constraint), not only in Python code.
- **Config:** use env vars via `app/config.py`. No secrets in code. `VITE_*` vars are public and baked in at build time.
- **Tests:** every new endpoint gets a pytest test in `backend/tests/`.
- **Dependencies:** add with `uv add` / `npm install`. Commit the lock files.
- **CI:** besides `make lint` and `make test`, it checks that `make api-client` output is committed and that `docker compose up --wait` starts healthy, so run those too when you touch the API or Docker files. A red CI run means a real problem: fix the cause, never skip or weaken a check. Debug with `gh run list` and `gh run view <id> --log-failed`. When adding a check, add it to both the `Makefile` and `ci.yml`.
- **Releases:** release-please owns versions and `CHANGELOG.md`. Never bump a version or edit the changelog by hand. The version lives in `.release-please-manifest.json` and is copied to every file listed under `extra-files` in `release-please-config.json`; if you add a new place that holds the app version, add it there. `feat` → minor, `fix` → patch (while < 1.0).
- **Commits:** use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, e.g. `feat(api): add bookings endpoint`, `fix(web): ...`. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `build`, `chore`. Scopes: `api`, `web`, `db`, `docker`.

## Agent skills

### Issue tracker

Issues and specs live in this repo's GitHub Issues, managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and `docs/adr/` at the repo root (created lazily). See `docs/agents/domain.md`.

# The whole app in one image: FastAPI serves the API under /api and the built
# frontend everywhere else, on the port in $PORT (Render and Hexlet's check set it).

# ---- frontend: compile TypeScript/React into static files in /frontend/dist ----
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Empty = the browser calls /api on the same origin, which is this same server.
RUN npm run build

# ---- backend: install Python dependencies into /app/.venv with uv ----
FROM python:3.14-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first: this layer is cached until pyproject.toml/uv.lock change.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --locked --no-dev

# ---- runtime: Python + the venv + app code + built frontend, run as non-root ----
FROM python:3.14-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=backend --chown=app:app /app /app
COPY --from=frontend --chown=app:app /frontend/dist /app/frontend
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/frontend \
    PORT=8080
USER app
EXPOSE 8080
# Migrates the database (when DATABASE_URL is set), then starts the server on $PORT.
CMD ["./scripts/start.sh"]

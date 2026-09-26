# syntax=docker/dockerfile:1

# ---- build: compile TypeScript/React into static files in /app/dist ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
# Baked into the JS at build time. Empty = call /api on the same origin (nginx below).
# For a CDN deploy: --build-arg VITE_API_BASE_URL=https://api.example.com
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ---- runtime: nginx serves dist/ and proxies /api to FastAPI (runs as non-root) ----
FROM nginxinc/nginx-unprivileged:1.29-alpine
# Files in /etc/nginx/templates get ${VARS} substituted at container start.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV API_UPSTREAM=http://api:8000
EXPOSE 8080

import type { CreateClientConfig } from './generated/client.gen'

// Where the API lives. Empty = same origin: the browser calls /api/... on the
// host that served the page (Vite proxy in dev, nginx in Docker).
// For a CDN deploy set VITE_API_BASE_URL=https://api.example.com at build time.
export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
})

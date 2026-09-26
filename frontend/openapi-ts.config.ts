import { defineConfig } from '@hey-api/openapi-ts'

// Generates a typed API client from the FastAPI schema.
// openapi.json is exported by the backend: `make api-client` from the repo root.
export default defineConfig({
  input: './openapi.json',
  output: 'src/api/generated',
  plugins: [
    // src/api/client-config.ts sets the API base URL (see VITE_API_BASE_URL).
    { name: '@hey-api/client-fetch', runtimeConfigPath: './src/api/client-config.ts' },
    '@hey-api/sdk',
    '@hey-api/typescript',
    '@tanstack/react-query',
  ],
})

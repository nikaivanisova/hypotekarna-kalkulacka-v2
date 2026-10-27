import { defineConfig } from 'vite';

// The page calls the API on its own origin (`/api/...`, contract `servers: /`).
// In development Vite forwards those calls to the backend, so no CORS is needed locally.
const backend = process.env.MORTGAGE_API_URL ?? 'http://localhost:8000';

export default defineConfig({
  server: {
    port: Number(process.env.PORT ?? 5173),
    strictPort: true,
    proxy: { '/api': backend },
  },
  test: {
    include: ['tests/unit/**/*.test.js'],
    environment: 'node',
  },
});

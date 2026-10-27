import { defineConfig } from '@playwright/test';

// End-to-end tests against the real backend and the Vite dev server, on their own ports.
// The installed Microsoft Edge is used (channel "msedge"): no browser download is needed, and
// Windows Application Control on the dev machine allows it.
const BACKEND_PORT = 8766;
const FRONTEND_PORT = 5174;

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: false,
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    channel: 'msedge',
  },
  webServer: [
    {
      command: `"../backend/.venv/Scripts/python.exe" -m uvicorn mortgage.api.app:app --port ${BACKEND_PORT}`,
      cwd: '../backend',
      url: `http://127.0.0.1:${BACKEND_PORT}/api/v1/health`,
      reuseExistingServer: false,
      env: { MORTGAGE_CORS_ORIGINS: `http://localhost:${FRONTEND_PORT}` },
    },
    {
      command: 'npx vite',
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: false,
      env: { PORT: String(FRONTEND_PORT), MORTGAGE_API_URL: `http://127.0.0.1:${BACKEND_PORT}` },
    },
  ],
});

import { defineConfig } from '@playwright/test';

// End-to-end tests against the real backend and the Vite dev server, on their own ports.
// Locally the installed Microsoft Edge is used (channel "msedge"): no browser download is needed, and
// Windows Application Control on the dev machine allows it. CI (Linux) sets PLAYWRIGHT_CHANNEL=chromium
// to use Playwright's own Chromium.
const BACKEND_PORT = 8766;
const FRONTEND_PORT = 5174;
const CHANNEL = process.env.PLAYWRIGHT_CHANNEL ?? 'msedge';
const PYTHON = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: false,
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    ...(CHANNEL === 'chromium' ? {} : { channel: CHANNEL }),
  },
  webServer: [
    {
      command: `"${PYTHON}" -m uvicorn mortgage.api.app:app --port ${BACKEND_PORT}`,
      cwd: '../backend',
      url: `http://127.0.0.1:${BACKEND_PORT}/api/v1/health`,
      reuseExistingServer: false,
      // One backend serves every test, so the per-IP rate limit is raised; no Supabase (id is null).
      env: { MORTGAGE_CORS_ORIGINS: `http://localhost:${FRONTEND_PORT}`, MORTGAGE_RATE_LIMIT: '1000/60' },
    },
    {
      command: 'npx vite',
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: false,
      env: { PORT: String(FRONTEND_PORT), MORTGAGE_API_URL: `http://127.0.0.1:${BACKEND_PORT}` },
    },
  ],
});

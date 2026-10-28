# Mortgage Calculator

A fixed-rate annuity mortgage calculator: monthly payment, final payment, total paid and total interest from the loan amount, interest rate and term. It also takes up to 10 one-time extra payments (*mimoriadna splátka*), which shorten the term. Every calculation is saved in Supabase.

V2 is a web app in four parts (plan: [`docs/v2/00-refactor-plan.md`](docs/v2/00-refactor-plan.md); retrospective: [`docs/v2/06-retro.md`](docs/v2/06-retro.md)):

| Folder | Part |
|---|---|
| `frontend/` | Web page (Vite + vanilla JavaScript) |
| `api/` | API contract (`openapi.yaml`, OpenAPI 3.1) |
| `backend/` | Calculations and API server (Python 3.14, FastAPI) |
| `supabase/` | Database migrations (Postgres) |
| `tools/` | `reference.py`: exact-rational reference for the calculation (`py -I tools/reference.py`) |
| `.github/workflows/ci.yml` | CI: backend, reference, frontend, end to end |

V1, the TypeScript command-line version, is in git at tag `v1-final`.

## Run locally

1. Backend (see `backend/README.md`): copy `backend/.env.example` to `backend/.env` and add the Supabase secret key. Without it the app still works and saves nothing (`id: null`).
   ```bash
   cd backend
   uv run --env-file .env python -m uvicorn mortgage.api.app:app --port 8000
   ```
2. Frontend (see `frontend/README.md`):
   ```bash
   cd frontend
   npm.cmd run dev
   ```
3. Open http://localhost:5173.

## Deployment (not done; D10 = local only)

When V2 is deployed:
- Serve the frontend build (`npm run build` → `frontend/dist`) and the backend under one origin, with `/api` routed to the backend. This matches the contract's `servers: /`. Otherwise set `MORTGAGE_CORS_ORIGINS` to the frontend's URL (never `*`).
- Store `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in the host's secret settings, never in the frontend or in git.
- The rate limit (`MORTGAGE_RATE_LIMIT`, default 30 calculations per minute per IP) is in memory, for one process. Behind a proxy every client has the proxy's IP. Use the proxy's own rate limit, or trust `X-Forwarded-For` from that proxy only (a code change).
- Keep the 8 KiB body limit and the security headers of the host's defaults; serve HTTPS only.

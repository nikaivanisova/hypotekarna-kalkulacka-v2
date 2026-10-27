# Backend (Python)

Parsing, validation and the mortgage calculation, served over HTTP with FastAPI; writes to Supabase.

| Phase | Status | Content |
|---|---|---|
| 2 | ✅ done | `mortgage/` — port of V1 M1–M4 and M7 (`domain/`, `input/`, `app/`) |
| 3 | ✅ done | contract tests for `api/openapi.yaml` (`tests/contract/`) |
| 4 | ✅ done | `mortgage/api/`: FastAPI app implementing `api/openapi.yaml` (`tests/api/`) |
| 6 | ✅ done | `mortgage/persistence/`: saves each calculation in Supabase (`tests/persistence/`, `tests/integration/`) — 283 tests in total |
| 7 | — | `mortgage/domain/schedule.py`: extra payments |

## Run the server

```bash
cd backend
uv run --env-file .env python -m uvicorn mortgage.api.app:app --port 8000
```

Settings come from `backend/.env`. Copy `.env.example` and fill in the secret key; the file is gitignored.
- `SUPABASE_URL` and `SUPABASE_SECRET_KEY`: where calculations are saved. Set both or neither. Without them the API still works and returns `id: null` (D5).
- `MORTGAGE_CORS_ORIGINS`: the allowed frontend origins (comma-separated; default `http://localhost:5173`; `*` is refused).

The contract is served at `/openapi.json` and `/docs`. Without a `.env`, drop `--env-file .env`.

## Run the tests

```bash
cd backend
uv sync
uv run python -m pytest
```

Use `python -m pytest`, not `uv run pytest`: Windows Application Control on the dev machine blocks the `pytest.exe` launcher in `.venv`.

## Layers

| Module | V1 | Rule |
|---|---|---|
| `domain/types.py` | M1 | Types only. API field names and error codes (camelCase) are used as-is. |
| `domain/calculation.py` | M4 | Private `Context(prec=40, ROUND_HALF_UP)` entered with `localcontext()`; the caller's context is never changed. |
| `input/parsing.py` | M2 | Strict grammar with `fullmatch` before `Decimal()`; trims exactly the JavaScript `trim()` whitespace set. |
| `input/validation.py` | M3 | Same rules, codes and order as V1; `-0` is `negative` (`is_signed()`). |
| `app/calculator.py` | M7 | Validation, then calculation. Returns data, no display text. |
| `api/app.py` | — | Routes; serves `api/openapi.yaml`; CORS allowlist. Imports only `app/*` and `domain/types`. |
| `api/request.py` | — | Strict body reading: object of 3 string-or-null properties, ≤ 100 chars, no duplicates or lone surrogates → else 400. |
| `api/problems.py` | — | problem+json for every HTTP error; never echoes request values; no `detail` on 5xx. |
| `api/body_limit.py` | — | 1 KiB limit before parsing (Content-Length and streamed) → 413. |
| `persistence/repository.py` | — | `SupabaseRepository.save()` → row id or `None`. Posts to the REST API with the secret key in the `apikey` header only; money as strings; 3 s timeout; never raises; never logs the key. `NullRepository` when not configured. |

Tests never reach the real database: `tests/conftest.py` removes the `SUPABASE_*` variables, except for tests marked `live`. To check the real project on purpose:

```bash
uv run --env-file .env python -m pytest -m live
```

This saves one row, reads it back, then deletes it.

`tests/test_architecture.py` enforces the allowed imports per layer, no I/O, and no cycles.

## Parity checks

- `tests/domain/test_reference_parity.py`: all 6 800 sweep loans equal `tools/reference.py` (exact rationals), cent for cent.
- `tools/v1_parity.py`: all 6 800 sweep loans equal the V1 TypeScript code in `legacy/cli` (run by hand).

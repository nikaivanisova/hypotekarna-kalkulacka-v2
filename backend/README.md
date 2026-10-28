# Backend (Python)

Parsing, validation and the mortgage calculation, served over HTTP with FastAPI; writes to Supabase.

| Phase | Status | Content |
|---|---|---|
| 2 | ✅ done | `mortgage/` — port of V1 M1–M4 and M7 (`domain/`, `input/`, `app/`) |
| 3 | ✅ done | contract tests for `api/openapi.yaml` (`tests/contract/`) |
| 4 | ✅ done | `mortgage/api/`: FastAPI app implementing `api/openapi.yaml` (`tests/api/`) |
| 6 | ✅ done | `mortgage/persistence/`: saves each calculation in Supabase (`tests/persistence/`, `tests/integration/`) |
| 7 | ✅ done | extra payments: `mortgage/domain/schedule.py`, item validation, API fields, `save_calculation` |
| 8 | ✅ done | rate limit (`mortgage/api/rate_limit.py`), CI — 460 tests in total (+2 live) |

## Run the server

```bash
cd backend
uv run --env-file .env python -m uvicorn mortgage.api.app:app --port 8000
```

Settings come from `backend/.env`. Copy `.env.example` and fill in the secret key; the file is gitignored.
- `SUPABASE_URL` and `SUPABASE_SECRET_KEY`: where calculations are saved. Set both or neither. Without them the API still works and returns `id: null` (D5).
- `MORTGAGE_CORS_ORIGINS`: the allowed frontend origins (comma-separated; default `http://localhost:5173`; `*` is refused).
- `MORTGAGE_RATE_LIMIT`: calculations per client IP, `<limit>/<seconds>` (default `30/60`) or `off`. Over the limit → `429` with `Retry-After`.

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
| `domain/types.py` | M1 | Types only. API field names and error codes (camelCase) are used as-is. Phase 7 adds `ExtraPayment`, `AppliedExtraPayment` and the statuses. |
| `domain/schedule.py` | (ADR-9) | The month-by-month run with extra payments (04 §3.2–3.3): schedule / extra / zero-tail endings, used amounts in request order, statuses. `calculate_mortgage` delegates to it; without extras the results are exactly V1. |
| `domain/calculation.py` | M4 | Private `Context(prec=40, ROUND_HALF_UP)` entered with `localcontext()`; the caller's context is never changed. |
| `input/parsing.py` | M2 | Strict grammar with `fullmatch` before `Decimal()`; trims exactly the JavaScript `trim()` whitespace set. |
| `input/validation.py` | M3 | Same rules, codes and order as V1; `-0` is `negative` (`is_signed()`). |
| `app/calculator.py` | M7 | Validation, then calculation. Returns data, no display text. |
| `api/app.py` | — | Routes; serves `api/openapi.yaml`; CORS allowlist. Imports only `app/*`, `domain/types` and `persistence/*`. |
| `api/request.py` | — | Strict body reading: object of 3 string-or-null properties plus optional `extraPayments` (≤ 10 closed `{month, amount}` items), ≤ 100 chars per value, no duplicates or lone surrogates → else 400. |
| `api/problems.py` | — | problem+json for every HTTP error; never echoes request values; no `detail` on 5xx. |
| `api/rate_limit.py` | — | Per client IP (TCP peer; `X-Forwarded-For` not trusted), sliding window, refused requests do not count; in memory, idle clients dropped. Only `POST /api/v1/calculations`. |
| `api/body_limit.py` | — | 8 KiB limit before parsing (Content-Length and streamed) → 413. The form's largest body is 7 216 bytes. |
| `persistence/repository.py` | — | `SupabaseRepository.save()` → row id or `None`. Calls `POST /rest/v1/rpc/save_calculation` with `{"payload": …}` (calculation and extra payments in one transaction), with the secret key in the `apikey` header only; money as strings; 3 s timeout; never raises; never logs the key. `NullRepository` when not configured. |

Tests never reach the real database: `tests/conftest.py` removes the `SUPABASE_*` variables, except for tests marked `live`. To check the real project on purpose:

```bash
uv run --env-file .env python -m pytest -m live
```

This saves two calculations (one of them with three extra payments, in one transaction), reads them back, then deletes them; the extra payments go with them (cascade).

`tests/test_architecture.py` enforces the allowed imports per layer, no I/O, and no cycles.

## Parity checks

- `tests/domain/test_reference_parity.py`: all 6 800 V1 sweep loans equal `tools/reference.py` (exact rationals), cent for cent.
- `tests/domain/test_extra_reference_parity.py`: 803 extra-payment loans (the reference's strata) equal `calc_extra`, statuses included.
- V1 parity with the TypeScript code (`tools/v1_parity.py`, 6 800 loans, 0 mismatches) was run for the last time in Phase 8, before V1 was removed; both are at git tag `v1-final`.

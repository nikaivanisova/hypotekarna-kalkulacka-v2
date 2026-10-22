# V2 Refactor Plan — From CLI to Frontend / API / Backend / Supabase

Status: **Approved** (2026-10-22). All decisions in §8 are made: the author accepted the recommendations for D1–D11, and D7 was decided separately.

## 1. Goal

Split the V1 single-process TypeScript CLI into four parts:

| Part | Technology | Responsibility |
|---|---|---|
| **Frontend** | JavaScript (browser) | Collects user input, shows results and errors, calls the API. No financial math. |
| **API** | OpenAPI 3.1 contract (`api/openapi.yaml`) | The agreement between frontend and backend: which input, which output, which errors. |
| **Backend** | Python (FastAPI) | Parsing, validation and all calculations: regular payment, *mimoriadna splátka* (extra payment), later more logic. Writes to Supabase. |
| **Supabase** | Postgres | Stores the data the application saves (calculations and their extra payments). |

```
 Browser                      Backend (Python)                       Supabase
┌─────────────┐  HTTP/JSON  ┌────────────────────────────────┐  SQL  ┌───────────┐
│ frontend/   │────────────▶│ api layer (FastAPI, Pydantic)  │       │ Postgres  │
│  form, view │  per        │   └▶ app (use case)            │──────▶│ calcula-  │
│  formatting │  api/       │        ├▶ input (parse/valid.) │       │  tions    │
│  messages   │◀────────────│        ├▶ domain (calc, sched.)│       │ (RLS on)  │
└─────────────┘ openapi.yaml│        └▶ persistence          │       └───────────┘
                            └────────────────────────────────┘
```

**Rule that does not change:** the backend keeps full precision and rounds to cents only at the end (CLAUDE.md). Money never travels as a JSON number — always as a decimal string (`"449.04"`), so the browser's binary floats can never change a value.

## 2. Where each V1 module goes

| V1 module | V2 location | Notes |
|---|---|---|
| M1 `domain/types` | `backend/mortgage/domain/types.py` | Dataclasses with `Decimal`. |
| M2 `input/parsing` | `backend/mortgage/input/parsing.py` | Same strict grammar (`NUMBER_PATTERN`), applied *before* `Decimal()`. Python's `Decimal` also accepts `NaN`/`Infinity` — the grammar gate stays mandatory. |
| M3 `input/validation` | `backend/mortgage/input/validation.py` | Same rules table, same error codes, same field order. |
| M4 `domain/calculation` | `backend/mortgage/domain/calculation.py` | Private `decimal.Context(prec=40, rounding=ROUND_HALF_UP)`; never touches the global context. |
| M5 `output/formatting` | `frontend/src/formatting.js` | Display formatting (`1 234,57 €`) is a UI concern. Input is already a 2-dp string, so no rounding happens in the frontend. |
| M6 `output/presentation` | `frontend/src/presentation.js` | Labels, error messages, `shouldShowFinalPayment`. |
| M7 `app/calculator` | `backend/mortgage/app/calculator.py` | Returns domain result or validation errors; no view logic. |
| M8 `ui/cli`, M9 `main` | Retired (or kept as a thin API client — decision D6). | |
| — | `backend/mortgage/api/` | New: FastAPI routes, request/response models. |
| — | `backend/mortgage/persistence/` | New: Supabase repository. |
| — | `backend/mortgage/domain/schedule.py` | New: month-by-month run needed for extra payments (ADR-9). |

## 3. API contract (v1 of the API)

Contract-first: `api/openapi.yaml` is written and reviewed **before** backend or frontend code. Both sides are tested against it.

### `POST /api/v1/calculations`

Request — the user's raw text, so the backend is the single owner of parsing and validation:

```json
{ "loanAmount": "100 000", "annualRate": "3,5", "termYears": "30" }
```

`200 OK` — all money as 2-dp decimal strings:

```json
{
  "id": "6f1c…",                 // Supabase row id (null if persistence is off)
  "numberOfPayments": 360,
  "regularPayment": "449.04",
  "finalPayment": "452.02",
  "totalPaid": "161657.38",
  "totalInterest": "61657.38"
}
```

`422 Unprocessable Entity` — machine-readable codes; the frontend turns them into messages:

```json
{ "errors": [ { "field": "annualRate", "code": "above_max" } ] }
```

Codes are exactly V1's: `required`, `not_a_number`, `negative`, `below_min`, `above_max`, `too_many_decimals`, `not_whole_number`.

### Later endpoints (not in the first cut)

- `GET /api/v1/health` — liveness (added with the backend, trivial).
- `GET /api/v1/calculations/{id}` — reload a saved calculation.
- Extra payments: optional `extraPayments: [{ "month": 24, "amount": "5000" }]` in the same request, plus extra response fields (see Phase 7). An extra payment always shortens the term (D7), so there is no strategy field; the regular payment stays the same. Additive change → stays `/api/v1`.

## 4. Supabase schema (first migration)

```sql
create table public.calculations (
  id                 uuid primary key default gen_random_uuid(),
  created_at         timestamptz not null default now(),
  loan_amount        numeric(12,2) not null,
  annual_rate        numeric(5,2)  not null,
  term_years         smallint      not null,
  number_of_payments smallint      not null,
  regular_payment    numeric(12,2) not null,
  final_payment      numeric(12,2) not null,
  total_paid         numeric(14,2) not null,
  total_interest     numeric(14,2) not null,
  engine_version     text          not null   -- which backend version produced the numbers
);
alter table public.calculations enable row level security;
-- No policies for anon/authenticated: only the backend (service role) can read/write.
```

- `numeric`, never `float`. Values are stored already rounded (the API output), inputs as validated values.
- Supabase keys live only in `backend/.env` (gitignored). The frontend never talks to Supabase directly in this plan (decision D4).
- Migrations are files in `supabase/migrations/`, applied with the Supabase CLI; a local Supabase stack is used for development and tests.
- Phase 7 adds `extra_payments (id, calculation_id → calculations.id, month, amount)`.
## 5. Repository layout

```
api/openapi.yaml              # the contract
backend/                      # Python 3.14, FastAPI, pytest, uv
  pyproject.toml
  mortgage/{domain,input,app,api,persistence}/
  tests/{domain,input,app,api,contract}/
frontend/                     # Vite + vanilla JavaScript, Vitest, Playwright
  index.html
  src/{api-client,formatting,presentation,main}.js
  tests/
supabase/migrations/
tools/reference.py            # exact-rational reference script (retro §6.3)
legacy/cli/                   # V1 TypeScript, moved here until parity is proven, then deleted
docs/v2/
```

## 6. Phases

Each phase ends green (all tests pass), is one commit (or a small series), and updates `docs/handoff.md` and the prompt log. Following the V1 retrospective, every phase is a step in this plan; prompts point to the step and do not restate it.

| # | Phase | Work | Done when |
|---|---|---|---|
| **0** | Decisions & docs | Author answers §8. Update `CLAUDE.md` (V2 scope, prompt log in `docs/v2/prompts.md`, retro §6.1 rules). Write `docs/v2/01-functional.md` delta (web UI; extra payments, D7). | Decisions recorded; CLAUDE.md updated. |
| **1** | Restructure repo | Move V1 TS to `legacy/cli/` with its tests still green. Create empty `backend/`, `frontend/`, `api/`, `supabase/`. Check in `tools/reference.py`. | `legacy` tests 112/112; new folders scaffolded. |
| **2** | Backend core (port) | Port M1–M4 + M7 to Python, test-first. Port every domain/input/app test from V1 (tests 1–61, 80–84, 96–109) with **identical expected values**, including the property sweep (test 108). Architecture guard in Python (import-linter). | pytest green; reference script agrees with every expected value; parity with V1 on a shared input sweep. |
| **3** | API contract | Write `api/openapi.yaml` (§3). Review it (Layer 4-style, independent). | Contract approved by the author. |
| **4** | Backend API | FastAPI routes + Pydantic models generated/checked against the contract. Contract tests (e.g. schemathesis) + API tests for 200/422/400/500. CORS for the frontend origin only. | API tests green; `/docs` matches `openapi.yaml`. |
| **5** | Frontend | Vite + vanilla JS: form (3 fields), per-field error display, result view; port M5/M6 tests (62–79) to Vitest; API client with a mock server for unit tests. Playwright e2e against the real backend. | Vitest + Playwright green; manual check in the browser. |
| **6** | Supabase | Migration (§4), local stack, `persistence/` repository, `POST` saves and returns `id`. Integration test against local Supabase. Decide behaviour if Supabase is down (D5). | Row written per successful calculation; RLS verified (anon key cannot read). |
| **7** | Mimoriadna splátka | Layer 1 spec first (D7), then independent review, then `domain/schedule.py` with its own sweep tests, API extension, `extra_payments` table, frontend UI. | Spec reviewed; sweep + mutation checks pass; e2e covers an extra payment. |
| **8** | Clean-up & CI | Delete `legacy/` (or keep CLI as API client), GitHub Actions: pytest, Vitest, reference script, contract tests, Playwright. Retro for V2. | CI green on `master`. |

Phases 2 and 3 can run in parallel; 5 can start on a mock server as soon as 3 is approved.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Python port gives different cents than V1 | Port tests with the same expected values; run a seeded sweep comparing V1 (TS) and V2 (Python) outputs before deleting `legacy/`. |
| Floats sneak in (JSON numbers, JS `Number`, Postgres `float`) | Money as strings in the contract; `numeric` in SQL; a contract test rejects numeric money fields. |
| Validation drifts between frontend and backend | Backend is the only validator; frontend does at most "field is empty" hints. |
| Supabase secret leaks to the browser | Service key only in backend env; RLS on with no public policies; `.env` gitignored. |
| Extra-payment rules decided during the build (V1 lesson) | Phase 7 starts with spec + review; no code until every finding has a decision. |
| Windows tooling friction | Document `npm.cmd`, `uv run` commands; CI on Linux and Windows. |
| `python` is not on PATH on the dev machine (it opens the Microsoft Store alias) | Python 3.14.3 is installed and reachable as `py`; `uv` 0.13.5 is installed (2026-10-22). The user Scripts folder is on the user PATH, so `uv` runs directly. |

## 8. Decisions (all made 2026-10-22)

| # | Question | Decision |
|---|---|---|
| D1 | Frontend: vanilla JS or a framework (React/Vue/Svelte)? | **Vite + vanilla JS** — 3 inputs and one result view don't need a framework. |
| D2 | Backend framework? | **FastAPI** — generates OpenAPI, Pydantic validation, easy tests. |
| D3 | Who parses user text: frontend or backend? | **Backend** (raw strings in the API) — one owner of the V1 grammar. |
| D4 | Does the frontend talk to Supabase directly? | **No** — only via the backend; simpler security. Revisit if user accounts (Supabase Auth) are added. |
| D5 | If Supabase is down, should a calculation still return a result? | **Yes**, with `id: null` and a logged warning. |
| D6 | Keep the CLI? | **Retire it** after parity is proven (Phase 8). |
| D7 | Extra payments (*mimoriadna splátka*)? | **In scope (2026-10-22, Prompt 28): an extra payment shortens the term; the regular payment does not change.** Still open, for the Phase 7 spec: one-time or recurring? Fee? Limits (min/max amount, which months)? Suggested first cut: one-time payments at a given month, no fee. |
| D8 | UI language: Slovak, English, or both? | **English**, as in V1 (01 §3.5), so the V1 UI texts and their tests carry over unchanged. All texts stay in one messages table, so switching to Slovak later is a one-file change. |
| D9 | Users / login, or anonymous calculations? | **Anonymous** for V2; auth later. |
| D10 | Hosting (later): e.g. frontend on Netlify/Vercel, backend on Render/Fly, Supabase cloud. | Decide at Phase 8; develop locally until then. |
| D11 | Use an existing Supabase project or create a new one? | **Decide at Phase 6:** use an existing project if the author names one, otherwise create a new one. Phases 1–5 need no Supabase. |

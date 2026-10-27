# V2 Prompt Log

Prompts 21–26 (the V2 plan, the Python setup and decision D7) are logged in `docs/v1/prompts.md`, which was still the active log at the time. This log continues the numbering.

## Prompt 27 — Accept the decisions; Phase 0 and Phase 1

### Prompt

> you can use recommended answers for D1-D11 and continue

### Output

- **Decisions:** D1–D11 recorded as decided in `00-refactor-plan.md` §8. D8 (language) = English, the same as V1 01 §3.5, so the V1 texts and tests carry over. D11 (which Supabase project) is settled at Phase 6. Also fixed a table row in §7 that was broken when the extra-payment row was removed.
- **Phase 0:**
  - `CLAUDE.md` rewritten for V2: the four parts, backend-only rounding, no float money, the retro §6.1 rules, the prompt log in `docs/v2/prompts.md`, Windows notes.
  - `docs/v2/01-functional.md`: V1 behaviour kept exactly; web UI rules; FR-4 "save calculation"; open V1 questions keep V1 behaviour.
  - Checked against the V1 tests: term `"10,0"` → `too_many_decimals`, not `not_whole_number`. A draft line was corrected.
  - Committed as "docs: V2 refactor plan, decisions and functional delta (Phase 0)".
- **Phase 1:**
  - V1 moved to `legacy/cli/` (`git mv`, shown as renames). `npm.cmd ci && npm.cmd test` there → 112/112; typecheck 0 errors.
  - `tools/reference.py` (REF-ET) checked in and made self-checking → 8/8 ok, sweep 6 800 / 767 / 0, exit 0.
  - Scaffolded `api/`, `backend/`, `frontend/`, `supabase/migrations/` (README only); `.gitignore` extended; root README rewritten.
  - Committed as "refactor: move V1 to legacy/cli and scaffold V2 parts (Phase 1)". `no-plan/` was left uncommitted.

## Prompt 28 — Restore extra payments

### Prompt

> im sorry, i deleted extra-payment, but it should be in it. can you return it?

### Output

- Interrupted Phase 2 (Prompt in progress: "Start Phase 2: port the calculation to Python in backend/, test-first."). Only the V1 sources and tests had been read; nothing was written in `backend/` yet. Phase 2 resumes next.
- Restored extra payments, with the Prompt 24 rule (an extra payment shortens the term; the regular payment stays the same):
  - `00-refactor-plan.md`: D7 = in scope; Phase 7 "Mimoriadna splátka" is back; Clean-up & CI is Phase 8 again (D6 and D10 point to it). Also restored: the `extraPayments` API field (no strategy field), the `extra_payments` table, the `domain/schedule.py` row and the extra-payment risk row. Fixed two headings that had lost their blank line in the removal.
  - `01-functional.md`: new FR-5 "Extra payment", with the questions the Phase 7 spec must answer; removed extra payments from the out-of-scope list.
  - `CLAUDE.md`, `legacy/cli/README.md`: `legacy/` is deleted in Phase 8. `backend/README.md`: Phase 7 added.
  - Updated `docs/handoff.md`.
- Committed as "docs: restore extra payments (FR-5, Phase 7) in the V2 plan".

## Prompt 29 — Phase 2: port the calculation to Python (interrupted)

### Prompt

> Start Phase 2: port the calculation to Python in backend/, test-first.

### Output

- Interrupted by Prompt 28 after reading the V1 sources and tests; nothing was written. Resumed in Prompt 30.

## Prompt 30 — Phase 2 resumed

### Prompt

> Resume Phase 2: port the calculation to Python in backend/, test-first.

### Output

- `backend/` is a `uv` project: Python 3.14, pytest 9.1.1 pinned, no runtime dependencies, `package = false`.
- **Red:** I wrote the tests first: `tests/input/test_parsing.py`, `test_validation.py`, `tests/domain/test_calculation.py`, `test_reference_parity.py`, `tests/app/test_calculator.py`, `tests/test_architecture.py`. All five modules that import `mortgage` failed to import.
- **Green:** `mortgage/domain/types.py`, `domain/calculation.py`, `input/parsing.py`, `input/validation.py`, `app/calculator.py` → **123 passed**.
- Port decisions:
  - The V1 test names and expected values are unchanged. Amounts are compared as 2-dp strings.
  - The private `Context(prec=40, ROUND_HALF_UP)` is entered with `localcontext()`, because Python applies the thread context to arithmetic.
  - The grammar check uses `fullmatch`; trimming uses exactly the JavaScript `trim()` set; `-0` is detected with `is_signed()`. Each has a new test.
  - M7 returns data (`Calculated` / `Rejected`), not views. Display moves to the frontend.
- Second guards added after a hand mutation check: a new zero-tail loan (found by search, confirmed by `tools/reference.py`), the private context, `-0`, and the whole-number check. 13 mutations; all caught by ≥ 2 tests.
- Parity: all 6 800 sweep loans equal `tools/reference.py` (pytest) and the V1 TypeScript code (`tools/v1_parity.py`, new) → 0 mismatches.
- Found: Windows Application Control blocks `.venv\Scripts\pytest.exe`, so tests run with `uv run python -m pytest` (documented in `backend/README.md`).
- Updated `backend/README.md` and `docs/handoff.md`. Committed as "feat: port calculation core to Python backend (Phase 2)".

## Prompt 31 — Phase 3: API contract

### Prompt

> Start Phase 3: write api/openapi.yaml from plan §3.

### Output

- Wrote `api/openapi.yaml` (OpenAPI 3.1.0).
  - `POST /api/v1/calculations` with 5 named request examples and matching 200/422 response examples.
  - `GET /api/v1/health`.
  - Problem+json for malformed requests.
- Contract tests in `backend/tests/contract/test_openapi.py`:
  - They check that the spec is valid OpenAPI 3.1, that every example is valid against its schema, and that every request example run through `run_calculator` gives exactly its documented response.
  - They check that money is never a number and that the error vocabulary equals the backend types.
  - Dev dependencies added and pinned exactly: `pyyaml`, `openapi-spec-validator`, `openapi-schema-validator`, `jsonschema`, `referencing`.
- Independent review by a separate agent → `docs/v2/03-api-review.md`.
  - Verdict "approve with changes": 5 Major, 8 Minor, no Blocker.
  - The reviewer verified the contract's behavioural claims on 200 008 inputs.
  - With a throwaway FastAPI app outside the repo, the reviewer found that FastAPI's defaults return 422 for malformed requests, echo input values, and crash on `"\ud800"` with a plain-text 500.
- Applied all 13 findings:
  - Responses and the error vocabulary are open; the request stays closed.
  - Phase 4 must override FastAPI's defaults.
  - Error bodies never contain input values.
  - Added 413 (1 KiB), 415 and 429; added a CORS allowlist note.
  - The frontend sets `maxlength="100"`.
  - `RawInput` whitespace wording made precise; `totalPaid` and `numberOfPayments` worded for Phase 7; `id: null` also covers "not configured".
  - Client behaviour defined per status; `servers: /`.
  - Every example is now validated.
- The plan's Phase 4 row is updated (the overrides, "done when" = conformance to `openapi.yaml`). Added `api/README.md`.
- Backend: 160 passed. Committed as "feat: API contract with independent review (Phase 3)". Waiting for the author's approval of the contract.

## Prompt 32 — Approve the contract; Phase 4: backend API

### Prompt

> I approve api/openapi.yaml. Start Phase 4: build the FastAPI backend API.

### Output

- Recorded the approval (`03-api-review.md`, `docs/handoff.md`); Phase 3 is complete.
- Dependencies (pinned exactly):
  - Runtime: `fastapi` 0.159.1, `uvicorn` 0.54.0, `pyyaml` 6.0.3.
  - Dev: `httpx2` 2.16.0. Starlette 1.9 deprecates `httpx` for its test client.
- Tried **schemathesis** 4.32.3 and removed it: Windows Application Control blocks its native `jsonschema_rs` DLL. Replaced it with a per-response contract check in every API test and a 600-request seeded fuzz test.
- **Red:** `tests/api/test_api.py` written first, which failed with `No module named 'mortgage.api'`.
- **Green:** `mortgage/api/app.py`, `request.py`, `problems.py`, `body_limit.py`.
  - The body is parsed by hand, so FastAPI's default 422 never runs.
  - `api/openapi.yaml` is served as `/openapi.json`.
  - Problem+json for every HTTP error; a 1 KiB limit; a CORS allowlist from `MORTGAGE_CORS_ORIGINS` (`*` refused).
- Fixed a test bug found on the first run: the fuzz test sent `json=None`, which means no body, so the app correctly answered 415. It now always sends a JSON body.
- The architecture guard gained the `api` layer: it may import `app/*` and `domain/types`. The no-I/O check is limited to the core layers.
- Real-server smoke test (uvicorn + curl): health, 200, 422, 400 (`\ud800`, number), 413, 415, the CORS preflight and `/openapi.json` all as documented, and the server log was empty.
- Hand mutation check:
  - 19 mutations of the API layer; all were caught. One was rewritten because it was equivalent to the original code.
  - Second test cases were added until each rule failed ≥ 2 tests.
  - The redundant `parse_constant` (`NaN`) guard was removed: the string check already rejects `NaN`.
- Interrupted by Prompt 33 before the final run.

## Prompt 33 — Pause

### Prompt

> can you pause and resume when i say to?

### Output

- Stopped. Nothing was committed; the state was summarised for resuming.

## Prompt 34 — Resume

### Prompt

> resume

### Output

- After the session restart, checked that the uncommitted Phase 4 work was intact.
- Full suite → 225 passed (deprecations as errors).
- All 19 API mutations caught by ≥ 2 tests. The two Content-Length tests were split into parametrized cases, so each rule visibly has two tests.
- **Not implemented:** rate limiting (`429`, optional in the contract). The limits are a policy decision, carried over to Phase 8.
- Updated `backend/README.md`, `docs/handoff.md` and `03-api-review.md`. Committed as "feat: FastAPI backend implementing the API contract (Phase 4)".

## Prompt 35 — Phase 5: frontend

### Prompt

> Start Phase 5

### Output

- `frontend/`: Vite 8.3.5 + vanilla JS; Vitest 5.0.5 + jsdom 30.1.3; Playwright 1.64.1 (all pinned exactly). Playwright drives the installed Edge (`channel: 'msedge'`) instead of downloading a browser.
- **Red:** wrote 5 unit test files first (formatting, presentation, api-client, page, no-money-math); all 5 failed because `src/` did not exist.
- **Green:** `src/formatting.js`, `presentation.js`, `api-client.js`, `page.js`, `main.js`, `styles.css`, `index.html` → all pass.
- Ported V1 tests 62–79 with their names and texts. Tests 66–67 (padding and rounding) became "non-canonical amounts are rejected", because the frontend must not round (CLAUDE.md, contract).
- New behaviour from the contract:
  - Unknown codes give "<Label> is invalid."; unknown fields and other statuses give one general message.
  - Response shapes are checked; the client never rejects; one request at a time; `maxlength="100"`.
- 9 Playwright e2e tests against the real backend (browser versions of V1 tests 89–91 plus V2 cases) → 9 passed.
- **Hand mutation check:** 18 mutations; 17 caught by ≥ 2 guards, 1 equivalent.
  - Added tests: hide an empty Result panel after a failure, prototype names as codes, second cases for single guards.
  - Removed one vacuous test.
- **Manual check in the built-in browser:** results, errors, kept values, no horizontal scroll at 375 px, and no JS errors.
- Added `.claude/launch.json` (backend + frontend previews), `frontend/README.md`, and Playwright output folders to `.gitignore`. Updated `docs/handoff.md`. Committed as "feat: web frontend calling the API (Phase 5)".

## Prompt 36 — Phase 6: Supabase (new project)

### Prompt

> Create a new one

### Output

- D11 = a new project. The organization (the author's only one) is on the free plan. Created `hypotekarna-kalkulacka` in `eu-central-1`: quoted $0, no cost confirmation needed, status ACTIVE_HEALTHY. The existing `PDA-1` (inactive) was not touched.
- Migration `create_calculations` (version `20261027221257`): the plan §4 table plus CHECK constraints for the ranges, `number_of_payments ≤ term × 12` and `interest = paid − loan`. RLS on with no policies; all privileges revoked from `anon` and `authenticated`.
  - Verified: two bad rows rejected, `anon` → permission denied, 0 rows.
  - Security advisor: only INFO "RLS enabled, no policy" (intended).
- Checked in Supabase's docs (search results only, not the full text) how secret keys are sent: in the `apikey` header only.
- **Red:** wrote `tests/persistence/test_supabase_repository.py` (mock transport), new API tests (fake repository), `tests/conftest.py` (no test reaches the real DB unless marked `live`) and `tests/integration/test_supabase_live.py` (skipped without a key). They failed with `No module named 'mortgage.persistence'`.
- **Green:** `mortgage/persistence/repository.py`; `api/app.py` saves through `save_best_effort` (D5); `Calculated` now carries the validated `loan` → 267 passed.
- Hand mutation check: 17 mutations, all caught. Second guards were added until each rule fails ≥ 2 tests → **283 passed, 1 skipped**.
- `httpx2` moved to runtime dependencies; `live` marker registered.
- The architecture guard has a `persistence` layer.
- Added `backend/.env.example`, `supabase/README.md`, and README, plan and handoff updates.
- **Not done:** the live check. It needs the project's secret key, which only the author can copy from the dashboard: the Supabase MCP exposes publishable keys only, and secret values are not handled by the assistant.
- Committed as "feat: save calculations in Supabase (Phase 6)".

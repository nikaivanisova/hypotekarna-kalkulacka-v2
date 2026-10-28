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

## Prompt 37 — Key added (live check)

### Prompt

> Key added

### Output

- `backend/.env` did not exist. Searched the project for the key without printing any value: no real `sb_secret_` key in any project file (so nothing was exposed or committed), no `.env` variants, and no `SUPABASE_SECRET_KEY` environment variable.
- Created `backend/.env` from `.env.example` (URL filled in, key empty; ignored by git). Opening it in an editor failed (no supported editor installed), so the author got Notepad steps.
- The live check did not run.

## Prompt 38 — Pause and save

### Prompt

> pause and save my work

### Output

- All code was already committed (`5f9b3ac`, Phase 6). Recorded Prompts 37–38 and the paused state in `docs/handoff.md` (Next Steps 1: how to resume the live check).
- Committed as "docs: record paused Phase 6 live check". `backend/.env` stays uncommitted (gitignored); `no-plan/` stays uncommitted as before.

## Prompt 39 — What is the secret key?

### Prompt

> what is the supabase_secret_key

### Output

- Explained what the secret API key is (`sb_secret_…`, server-side only, the only way into the locked-down table), that the assistant cannot read it, and where it is in the dashboard (project `hypotekarna-kalkulacka` → Project Settings → API Keys → Secret keys). Explained how it differs from the publishable key, the legacy `eyJ…` keys and the database password. Asked the author not to paste it into the chat.

## Prompt 40 — Where to paste it

### Prompt

> do i need to paste it here or to the backend\.env

### Output

- Only into `backend\.env`, never into the chat (chat history keeps it). Gave the Notepad steps, and what to do if it was pasted into the chat by mistake (rotate the key).

## Prompt 41 — Publishable key too?

### Prompt

> ma tam byt aj sb_publishable?

### Output

- (Answered in Slovak.) No: only `SUPABASE_URL` and `SUPABASE_SECRET_KEY`. The frontend never talks to Supabase (D4), the table is closed to the publishable key, and the backend refuses non-`sb_secret_` keys.

## Prompt 42 — Prefix or not?

### Prompt

> so if the key looked like sb_publishable_12345 i need to paste 12345?

### Output

- No: the publishable key is not used at all. The secret key is pasted whole, including the `sb_secret_` prefix (the dashboard's copy button copies it that way).

## Prompt 43 — "I have it"

### Prompt

> okay, i have it

### Output

- Checked `backend/.env` without printing the key: it held the **publishable** key. That is not a leak (publishable keys are public), but the backend cannot use it. Told the author where the Secret keys section is.

## Prompt 44 — Look now (live check)

### Prompt

> look now

### Output

- `backend/.env` now holds a key starting with `sb_secret_`, with no quotes or spaces; URL correct; ignored by git.
- `uv run --env-file .env python -m pytest -m live` → **1 passed** (saved, read back, deleted).
- `.claude/launch.json` backend now uses `uv run --env-file backend/.env`. Restarted both previews.
- Submitted 123 456,78 € / 4,25 % / 25 y on the page: 668,81 / 670,10 / 200 644,29 / 77 187,51 €, which equals `tools/reference.py`.
  - The response id `d1b55276-…` exists in Supabase with the same values and `engine_version` `v2-calc-1`.
  - The row was left in place (1 row in the table).
- **Phase 6 complete.** Updated `docs/handoff.md`. Committed as "chore: load backend/.env in the preview; record Phase 6 live check".

## Prompt 45 — Plan extra payments (Phase 7, Layer 1)

### Prompt

> Plan extra payments

### Interview

Asked one question at a time, each with a recommended option:

| # | Question | Answer |
|---|---|---|
| X1 | Kind of extra payment | One-time payments (recommended) |
| X2 | How many per loan | Up to 10 (recommended) |
| X3 | Fee | No fee (recommended) |
| X4 | When does an extra in month k reduce the loan | With month k's regular payment, after that month's interest (recommended) |
| X5 | Extra larger than what is owed | Pay off; use only what is owed; later ones listed as "not used" (recommended) |
| X6 | Allowed amounts | 0,01 € – 1 000 000 € (recommended) |
| X7 | Two extras in the same month | Allowed; they add up (recommended) |
| X8 | Allowed months | 1 to term × 12 (recommended) |
| X9 | Extra outputs (multi-select) | New loan length, Time saved, Interest saved. "Extra paid in total" was not chosen |

### Output

- Implemented the rules first as exact arithmetic: `tools/reference.py` `calc_extra`, with a self-checking sweep (`check_extra_sweep`, 3 000 loans) and 8 examples (`EXPECTED_EXTRA`).
- The first version counted an extra in the last month as "0,06 € used" (example E4), only because V1's final payment is above the regular payment. The rule was corrected: in a month where the loan ends on its own schedule (month n, or V1's early termination), extras are "not used".
- The zero-tail ending never occurred randomly, so `zero_tail_extra` now builds it on purpose. All three endings occur (schedule 409, extra 591, zero tail 1 000); 0 violations; without extras the results equal V1.
- Wrote `docs/v2/04-extra-payments.md`: decisions X1–X9, inputs, domain rules, used amounts, totals, API, page, messages, storage, examples E1–E8, build plan, and questions R1–R5 for the reviewer.
- Rechecked the spec's own numbers. The body-size estimate was wrong (2 400 → about 2 700 bytes in ASCII; non-ASCII can exceed 4 KiB → 413) and was corrected before the review.
- Started an independent review (a separate agent) → `docs/v2/05-extra-payments-review.md`.

## Prompt 46 — Is the review still running? (and decision X10)

### Prompt

> does it still run?

### Output

- Yes; the independent review was still running.
- The review came back with "approve with changes": 6 Major, 7 Minor (→ `docs/v2/05-extra-payments-review.md`). Reproduced its counterexample first: 1 000,02 / 20 % / 30 y, extras 264: 783,50 and 265: 1 000 → K 265, the second item used 0,00, but it saves 1 month and 0,01 €.
- **Asked the author** about review finding 4, a rule the drafting agent had changed without asking: an extra in a month where the loan ends anyway. **Answer: "Not needed", 0,00 used (recommended) → decision X10.**
- Applied all 13 findings:
  - `tools/reference.py`:
    - 6 per-item statuses (`used`, `partly_used`, `after_payoff`, `loan_ends_this_month`, `tiny_balance`, `covered_by_earlier`);
    - helpers that build edge cases on purpose;
    - a stratified sweep with an independent paid-off check, greedy-split and status checks, and interest saved ≥ 0;
    - examples E9–E12.
    - Result: 0 violations; every ending and status reached.
  - Mutation-tested the sweep itself: 10/10 mutations caught (one only through coverage, so noted).
  - `04-extra-payments.md` rewritten:
    - X10 and the statuses;
    - the interest-saved proof;
    - the request shape and the row map;
    - notes and durations;
    - an 8 KiB limit, from measured sizes;
    - the RPC security;
    - the list of contract changes.
  - Plan §4 deviation logged.
- Committed as "docs: extra-payment spec, review and exact reference (Phase 7 spec)". Waiting for the author's approval.

## Prompt 47 — Approve the spec; build Phase 7

### Prompt

> Approve, start build

### Output

- Recorded the approval in `04-extra-payments.md` and `05-extra-payments-review.md`. Built build plan §7, test-first, step by step.
- **Step 1, domain** (commit `6ea9c3e`):
  - `domain/schedule.py` (the three endings, used amounts in request order, 6 statuses); `calculate_mortgage` delegates to it (ADR-9).
  - Tests: E1–E12 as literal values, D7, request order, outputs as exact cents, and the private context.
  - V1 tests unchanged and green; `tools/v1_parity.py` → 0 mismatches. The architecture guard caught the new import and was updated deliberately.
- **Step 2, API** (`02beb8c`):
  - Item validation: month 1–term × 12, or 360 while the term is invalid; amount 0,01–1 000 000; V1 codes; errors with `index` and `property`.
  - The request parser accepts the closed items (else 400); results gain `monthsSaved`, `interestSaved` and `extraPayments`; 8 KiB limit.
  - `api/openapi.yaml` updated (the 04 §4.1 list); contract tests updated.
  - Not test-first for one part: the validation tests were written before the code, but not run red before it passed.
  - An independent contract review found 4 Minor issues, all applied (`1e570bb`). They removed the bounds from response schemas, updated two info sentences, added the month-limit sweep test, and added the "not expressible" bullet.
- **Step 3, parity** (`a0ce866`): `tools/reference.py` got `extra_sweep_cases` (the same stratified generator; the sweep output is unchanged). `test_extra_reference_parity.py`: the backend equals `calc_extra` on 803 loans, cent for cent, statuses included.
- **Hand mutation checks:**
  - Backend: 21 mutations. All caught except one that is equivalent (`due <= paid_now` → `<`: an exact pay-off then ends through the zero tail with identical results). Second guards were added until each rule fails ≥ 2 tests.
  - Frontend: 20 mutations. They found one real gap (notes not cleared after a failure), now tested.
  - Persistence: 10 mutations, all caught.
  - Two script problems on the way: a pytest output decoding error, and patterns that did not match. Both were fixed and the runs repeated.
- **Step 4, storage:**
  - Migration `20261028205501_extra_payments` (columns, the `extra_payments` table, `save_calculation`) applied with the Supabase MCP.
  - Verified: invoker, empty `search_path`, EXECUTE only for `service_role`; the publishable key gets 401 on the RPC and on both tables; E3 saved correctly in a rolled-back transaction; a month beyond the term is rejected; the advisor shows only the intended INFO notices.
  - The repository now calls the RPC (`ENGINE_VERSION` `v2-calc-2`). Live tests 2/2 passed.
  - E1 was saved through the page's API path (`99688ff5-…`, left in place).
- **Step 5, frontend:**
  - Extra-payment rows (add/remove, at most 10, blank rows skipped after JS `trim`), the sent-index → row map for errors, extra result lines, durations, notes per status, generic texts for unknown values.
  - 133 unit tests and 13 e2e tests (Edge, real backend) pass.
- **Final:** backend 429 passed (+2 live); frontend 133 + 13.
- **Not verified by hand in the browser:** the browser pane was hidden at the end. The e2e tests cover the page flows.
- READMEs and the handoff updated. Committed as "docs: Phase 7 complete (extra payments)" and "feat: save extra payments through save_calculation (Phase 7, step 4)".

## Prompt 48 — (background reviews)

The contract-change review and the mutation runs reported back during Prompt 47; no user prompt.


## Prompt 49 — Phase 8: clean-up and CI

### Prompt

> Start Phase 8

### Decisions (asked)

| Question | Answer |
|---|---|
| D10: where V2 runs | Local only for now (recommended) |
| The 429 rate limit | A simple limit in the app (recommended) |

### Output

- The repo has a GitHub remote (`nikaivanisova/hypotekarna-kalkulacka-v2`). Nothing was pushed.
- **V1 removed:** a final V1 parity run gave 6 800 loans, 0 mismatches, and V1's tests 112/112. Created tag `v1-final` (local). Removed `legacy/` (23 files) and `tools/v1_parity.py`; the source comments now point to the tag.
- **Rate limit:** `api/rate_limit.py`.
  - Per IP, a sliding window, 30/60 by default, `MORTGAGE_RATE_LIMIT`, only on `POST /calculations`; 429 with `Retry-After`; refusals do not count; CORS is kept.
  - The tests were written first but not run red first.
  - Hand mutation check: 10 mutations. One survived ("refused requests recorded"), which showed a weak test; it was fixed and given a second guard. Finally 10/10 caught by ≥ 2 tests.
  - The contract text now states the policy. Tests switch the limit off by default; the e2e backend uses `1000/60`.
- **CI:** `.github/workflows/ci.yml` (backend, reference, frontend, e2e with Chromium). `playwright.config.js` is portable (`PLAYWRIGHT_CHANNEL`, the Python path per OS). The YAML parses, but CI has **not run** (nothing pushed).
- **Retrospective** `docs/v2/06-retro.md`. Rechecked its own numbers and fixed two before committing: 140 mutations over 9 runs, and 19 Minor review findings.
- Updated `CLAUDE.md` (V2 complete, `v1-final`, the Windows constraints), the root `README.md` (how to run, deployment notes), the plan status and D10, `backend/README.md` and `docs/handoff.md`.
- Tests: backend 460 passed (+2 live); frontend 133 + 13 e2e.
- Committed as "feat: remove V1 legacy CLI, add rate limiting and CI (Phase 8)" and "docs: V2 retrospective and Phase 8 docs".


## Prompt 50 — Push and watch CI

### Prompt

> Push and watch CI

### Output

- The remote `master` was at `f0466e5`, so the push was a fast-forward of 19 commits. The repository is **public**.
- Secret scan of the 19 commits before pushing: the only key-like string was the fake `sb_secret_TESTKEY…` in the unit tests, and no `.env` file is tracked.
- Pushed `master` (`f0466e5..42e6182`) and the tag `v1-final`.
- First CI run (https://github.com/nikaivanisova/hypotekarna-kalkulacka-v2/actions/runs/40775599950): **all 4 jobs green** in about 1 min.
  - Backend: 460 passed, 2 skipped.
  - Reference: V1 sweep 0 violations, E1–E12 ok, extra sweep 0 violations.
  - Frontend: 133 passed; build ok.
  - E2E: 13 passed in Chromium on Linux.
- Recorded the run in `docs/handoff.md` and `docs/v2/06-retro.md`. This record was committed locally as "docs: record the first green CI run" and is not pushed yet.


## Prompt 51 — Push the CI record

### Prompt

> Push it

### Output

- Secret scan of the commit: nothing found. Pushed `master` `42e6182..cf733e4`.
- Second CI run (https://github.com/nikaivanisova/hypotekarna-kalkulacka-v2/actions/runs/40776395067): **all 4 jobs green**.
- This log entry is committed locally only, so that logging does not start another push and CI run. It goes up with the next push.


## Prompt 52 — What next?

### Prompt

> what is next step?

### Output

- Answered from `docs/handoff.md` Next Steps and `docs/v2/06-retro.md` §4: optional branch protection, deployment when wanted, V3 planning, the `no-plan/` decision. Committed locally (not pushed).

# Handoff

Notes for whoever picks up this project next: current state, open questions, and next steps.

## Current State

**V1 project: 100 % complete.**

| Part | Status |
|---|---|
| Part A (Planning: `docs/v1/01`–`05`) | ✅ 100 % complete |
| Part B (Build V1: Steps 1–9) | ✅ 100 % complete: 112/112 tests, 0 type errors |
| Experiment (no-plan build, `no-plan/`) | ✅ complete |
| Retrospective (`docs/v1/06-retro.md`) | ✅ 100 % complete |

Items carried over to V2 are listed under "Open Questions" and "Next Steps" below.

- Base project structure created (docs, README, CLAUDE.md, git repo).
- Layer 1 (functional definition) approved: `docs/v1/01-functional.md`.
- Layer 2 (architecture) complete: `docs/v1/02-architecture.md`.
  - Stack: Node.js 24 LTS + TypeScript (strict) + decimal.js + Vitest; tests run with `npm test`.
  - Platform: interactive CLI (ADR-1), with the UI isolated behind `app/calculator`.
  - 9 modules: `domain/types`, `domain/calculation` (pure, isolated), `input/parsing`, `input/validation`, `output/formatting`, `output/presentation`, `app/calculator`, `ui/cli`, `main`.
- Layer 3 (test scenarios) complete: `docs/v1/03-test-scenarios.md`.
  - Originally 95 scenarios (82 unit, 9 functional, 4 e2e); 112 after the review revision (see below).
  - Expected values verified with an independent Python `decimal` script (in the doc's appendix) and a separate Node.js PMT check.
  - Defines the exact UI texts (prompts, result labels, error messages) that the tests assert.
  - Note: the reference example P=100000, 3.5 %, 30y has Final 452.02 / Total Paid 161657.38 (not 449.04 / 161654.40); see the note in 03.
- Layer 4 (independent review) complete: `docs/v1/04-review.md`.
  - 24 findings: 1 Blocker, 5 Major, 18 Minor. Decisions are recorded for #1–#6; #7–#24 are still open.
  - **Blocker #1:** the §4.4 final-payment rule gives negative final payments for valid inputs (e.g. P = 1 000.29, 20 %, 30 y → Final −97.42).
  - Major: the M8 readline adapter breaks with piped stdin/EOF (e2e 89–92); the number grammar is undefined (decimal.js accepts `0x…`, `Infinity`, `NaN`); there is no domain-wide invariant test; extra payments and variable rates touch 5+ modules.
  - All financial reference values in 03 were re-verified with exact rational arithmetic: 0 errors.
- Review findings #1–#6 resolved (2026-10-21) and applied to 01/02/03:
  - #1 early termination when the amount due ≤ the regular payment (01 §4.4); #2 line-queue terminal reader (02 M8, ADR-10); #3 strict number grammar before decimal.js (01 §3.2, 02 M2); #4 property sweep (test 108; Final ≤ Regular only for early-terminated loans); #5/#6 accepted trade-offs (ADR-9, V2 schedule module).
  - 03 now has 112 tests (96–112 new) and reference REF-ET (exact rationals, Appendix B).
- Final execution plan complete: `docs/v1/05-plan.md`.
  - Goals G1–G4, all 112 test names mapped to 9 build steps, acceptance criteria AC-1–AC-7, a per-step Definition of Done, tooling, and risks.
- **Part B, Step 1 complete (2026-10-21):** project scaffold, M1 `src/domain/types.ts`, and the architecture guard `tests/architecture.test.ts` (tests 93–95).
  - `npm test` → 3 passed; `npm run typecheck` → 0 errors. `npm start` has no `src/main.ts` yet; that is expected until Step 9.
  - Versions: Node 24.20.0, npm 11.19.0, decimal.js 10.6.0 (only runtime dependency), TypeScript 5.9.3, tsx 4.23.15, Vitest 5.0.5, @types/node 24.
  - **Conventions for the next steps:**
    - Import decimal.js as a **named** import: `import { Decimal } from 'decimal.js'`. The default import is a namespace under NodeNext.
    - Relative imports use the `.js` extension (`./types.js`), as NodeNext ESM requires.
    - Tests live in `tests/<layer>/<module>.test.ts`, and every `it()` name is copied verbatim from 03.
  - The architecture guard's allow-list: domain → domain/types; input/output → domain/types (plus validation → parsing, presentation → formatting); app → domain, input, output; ui → app, domain/types; main → ui. Node built-ins and `process`/`console` are only allowed in ui/ and main; decimal.js is allowed in domain/input/output/app.
  - npm 11 warns that esbuild's install script was not approved (`npm install-scripts`). Vitest and tsx work without it; no action is needed.
- **Part B, Step 2 complete (2026-10-21):** M2 `src/input/parsing.ts` + `tests/input/parsing.test.ts` (tests 1–16, 96–100), built test-first (red: 21 failed → green).
  - `npm test` → 24 passed; `npm run typecheck` → 0 errors.
  - The exports are `ParseResult`, `NUMBER_PATTERN` and `parseNumber`. `NUMBER_PATTERN` runs before `new Decimal()`.
  - **Literal-spec choices for open findings (relevant to Step 3):**
    - Only U+0020 spaces are removed inside a number (#12): a tab or NBSP inside a number → `not_a_number`. At the edges, JS `trim()` removes all whitespace, including NBSP.
    - `"-0"` and `"-0,00"` parse to a negative-zero Decimal (#9). `isNegative()` is `true` for it, so M3 will report `negative` unless the author decides otherwise.
- **Part B, Step 3 complete (2026-10-21):** M3 `src/input/validation.ts` + `tests/input/validation.test.ts` (tests 17–40, 101), built test-first (red: 25 failed → green).
  - `npm test` → 49 passed; `npm run typecheck` → 0 errors.
  - The exports are `FieldRule`, `V1_RULES` and `validateLoanInput(raw, rules = V1_RULES)`. There is one error per field, in the 02 order, and errors are reported in field order (loan, rate, term). `termYears` is converted to a JS integer.
  - Confirmed: rate `"-0"` → `[{annualRate, negative}]` (literal reading of 01 §3.3; open finding #9).
  - **Step 4 notes:** `LoanInput` values are `Decimal`s from decimal.js's global constructor. M4 must re-wrap them in its private clone (`new Dec(input.principal)`) before doing arithmetic (test 61).
- **Part B, Step 4 complete (2026-10-21):** M4 `src/domain/calculation.ts` + `tests/domain/calculation.test.ts` (tests 41–61, 102–108), built test-first (red: 28 failed → green).
  - `npm test` → 77 passed (the sweep in test 108 takes ≈ 3.9 s); `npm run typecheck` → 0 errors.
  - The exports are `roundToCents` and `calculateMortgage`. M4 uses a private `Decimal.clone({ precision: 40, rounding: ROUND_HALF_UP })`. It has the amount-due loop with early termination and the zero-tail rule. `numberOfPayments` is the number of payments actually made.
  - Mutation check: the early-termination tests (102–106, 108) and the zero-tail test (106) fail when the respective rule is removed. Only test 106 guards the zero-tail rule: the sweep domain contains no such case.
  - **Step 5 notes:**
    - `formatMoney` receives cents-rounded `Decimal`s, but must still round half up with an **explicit** mode (`toFixed(2, Decimal.ROUND_HALF_UP)`), never the global default (test 67, 04 #16).
    - It must use ASCII spaces only (test 68).
- **Part B, Step 5 complete (2026-10-21):** M5 `src/output/formatting.ts` + `tests/output/formatting.test.ts` (tests 62–68), built test-first (red: 7 failed → green).
  - `npm test` → 84 passed; `npm run typecheck` → 0 errors.
  - `formatMoney(amount)` → e.g. `1 234,57 €`. It uses an explicit `ROUND_HALF_UP`, ASCII spaces and no `Intl`. Test 67 also runs under a global `ROUND_DOWN`, which proves the explicit mode.
  - **Step 6 notes:**
    - M6 may import only M1 types and M5 (`./formatting.js`).
    - Every UI text is the exact string from 03's "Expected UI texts" section.
    - `shouldShowFinalPayment` compares the already-rounded amounts: |final − regular| ≥ 0.01.
- **Part B, Step 6 complete (2026-10-21):** M6 `src/output/presentation.ts` + `tests/output/presentation.test.ts` (tests 69–79), built test-first (red: 11 failed → green).
  - `npm test` → 95 passed; `npm run typecheck` → 0 errors.
  - The exports are `FIELD_LABELS`, `shouldShowFinalPayment`, `toResultView` and `toErrorView`, plus the view types. All texts are in one `MESSAGES` table.
  - `toErrorView` keeps one message per field, in field order.
  - **Step 7 notes:**
    - `runCalculator(raw)` → `{ kind: 'result', view }` or `{ kind: 'invalid', view }`. It must not call `calculateMortgage` for invalid input.
    - Tests 82–83 need a partial `vi.mock` of `src/domain/calculation`, because `vi.spyOn` cannot replace ES module exports (05-plan §6.2).
- **Part B, Step 7 complete (2026-10-21):** M7 `src/app/calculator.ts` + `tests/app/calculator.test.ts` (tests 80–84, 109), built test-first (red: 6 failed → green).
  - `npm test` → 101 passed; `npm run typecheck` → 0 errors.
  - The exports are `CalculatorOutcome` and `runCalculator(raw)`: `validateLoanInput` → `toErrorView` if invalid (no calculation) → otherwise `calculateMortgage` → `toResultView`.
  - Tests 80 and 82–84 assert the call count of `calculateMortgage` through a partial `vi.mock` that wraps the real function. Mutation check: calling `calculateMortgage` before the validity check makes tests 80 and 82–84 fail.
  - **Step 8 notes:**
    - M8 imports only `app/calculator` and `domain/types` (architecture guard); it must not import M2–M6 directly.
    - `createNodeTerminalIo(input?, output?)` is the line queue from 02 M8 / ADR-10. Tests 111–112 use in-memory `PassThrough` streams; tests 85–88 use a scripted fake `TerminalIo`.
- **Part B, Step 8 complete (2026-10-21):** M8 `src/ui/cli.ts` + `tests/ui/cli.test.ts` (tests 85–88, 111–112), built test-first (red: 6 failed → green).
  - `npm test` → 107 passed; `npm run typecheck` → 0 errors.
  - The exports are `TerminalIo`, `createNodeTerminalIo(input = process.stdin, output = process.stdout)` and `runCli(io)`.
  - `createNodeTerminalIo` is the event-driven line queue (ADR-10): one readline interface, a FIFO queue, a single pending resolver, and `undefined` for the pending and every later `ask` after EOF. `close()` is idempotent. Test 111 also covers CRLF input.
  - `runCli` re-asks only the invalid fields, prints `label: value` result lines (exit 0) or returns 1 when input closes early, and always calls `io.close()` so stdin does not keep the process alive.
  - Mutation check: dropping lines that arrive with no pending `ask` makes test 111 fail.
  - Commit message: the plan's Step 8 message was used (the prompt quoted a different one).
  - **Step 9 notes:**
    - `src/main.ts` may import only `ui/*`: `process.exitCode = await runCli(createNodeTerminalIo());`.
    - E2E tests spawn `process.execPath` with `['--import', 'tsx', 'src/main.ts']`, not `npx` (Windows, 05-plan §6.2).
    - AC-3 and AC-4 are checked by hand and recorded here.
- **Part B, Step 9 complete (2026-10-21):** M9 `src/main.ts` + `tests/e2e/cli.e2e.test.ts` (tests 89–92, 110), built test-first (red: 4 failed → green).
  - `npm test` → 9 files, **112 passed (112)**; `npm run typecheck` → 0 errors.
  - `src/main.ts` imports only `ui/cli`: `process.exitCode = await runCli(createNodeTerminalIo(process.stdin, process.stdout))`. It uses `exitCode` (02 M9) instead of `process.exit()`, so stdout is flushed before the process ends.
  - The e2e tests spawn `process.execPath` with `['--import', 'tsx', 'src/main.ts']` and pipe stdin. During Red, test 92 passed vacuously, because a missing module also exits with code 1. It only carries weight together with the other four tests.
  - **AC-4 (checked by hand):** `printf '100 000\n3,5\n30\n' | npm start` → the 4 result lines of test 89, exit 0. `printf '100000\n' | npm start` → no result lines, exit 1.
  - **AC-3 (partly checked):** in an interactive terminal, `npm start` shows `Loan amount (EUR): ` with no default and waits. The author still needs to confirm the full interactive run (typing all three values, exit 0).
  - Windows: in PowerShell, `npm start` is blocked by the execution policy (`npm.ps1`); use `npm.cmd start`.
  - Deviations from the prompt (file path, `process.exit`, commit message): the 05-plan / 02 versions were used. See Prompt 17 in `docs/v1/prompts.md`.

- **Experiment (complete):** a mortgage CLI built from the single prompt "Build a simple mortgage calculator CLI application in Node.js/TypeScript." without the plan (Prompts 18–19). It is in `no-plan/` (7 tests green, 0 type errors) and is **not committed**; the `experiment/no-plan` branch has no commits of its own.
- **Retrospective complete (2026-10-21):** `docs/v1/06-retro.md` (Prompt 20).
  - Both builds were run on the same inputs. The no-plan totals are internally inconsistent and overstate Total Paid by up to €107.17 (P = 1 000.29, 20 %, 30 y).
  - The review's two silent bugs (#1 negative final payment, #3 hex accepted) would not have been found by the original 95 tests.
  - All 9 build prompts disagreed with `05-plan.md`; the plan was followed each time.
  - Section 6 lists the V2 rules, process changes and tooling.

## Open Questions (carried over to V2)
- Author decisions on findings #7–#24 in `docs/v1/04-review.md` (all Minor). Still undecided: `-0` (#9), space grouping / NBSP (#12), term `"10,0"` (#13), duplicated rounding and limits (#16, #17), the `ui → domain` rule (#18).
- Author confirmation of the sub-half-cent tail rule (01 §4.4 step 3; 05 §6.3). It is guarded by test 106 only.
- Whether to display the number of payments when a loan ends early (V1 outputs do not show it).

## V2 Refactor (started 2026-10-22)
- **Plan drafted:** `docs/v2/00-refactor-plan.md` (Prompt 21). Splits the app into Frontend (JS), API (OpenAPI contract), Backend (Python/FastAPI) and Supabase, in 9 phases (0–8).
- **Decisions D1–D11 made (Prompt 27):** the author accepted the recommendations; D8 = English (as in V1), D11 is settled at Phase 6.
- **Phase 0 complete (Prompt 27):** `CLAUDE.md` rewritten for V2 (prompt log moves to `docs/v2/prompts.md`); `docs/v2/01-functional.md` written (V1 behaviour kept exactly, plus web UI and FR-4 "save calculation").
- **D7, final (Prompt 28):** extra payments (*mimoriadna splátka*) are **in scope**: an extra payment shortens the term and the regular payment stays the same (as decided in Prompt 24). Prompt 25 had removed them; Prompt 28 restored them as **Phase 7**, with Clean-up & CI as Phase 8. They are FR-5 in `docs/v2/01-functional.md`. The detailed rules (one-time/recurring, fee, limits, outputs) are decided in the Phase 7 spec.
- Python setup (Prompt 22): Python **3.14.3** is installed and reachable as `py` (the bare `python` command opens the Microsoft Store alias). `uv` 0.13.5 is installed with `py -m pip install --user uv`; it finds Python 3.14. Its folder `%APPDATA%\Python\Python314\Scripts` was added to the user PATH (Prompt 23), so `uv` works in new terminals. The backend targets Python 3.14.

- **Phase 1 complete (Prompt 27):** V1 moved with `git mv` to `legacy/cli/` (history kept). There, `npm.cmd ci` + `npm.cmd test` → 112/112, typecheck 0 errors. The root `node_modules/` was deleted; V1 now has its own in `legacy/cli/`.
  - `tools/reference.py`: REF-ET from 03 Appendix B, now self-checking. `py -I tools/reference.py` → 8/8 examples ok, sweep 6 800 / 767 early / 0 violations, exit 0.
  - `api/`, `backend/`, `frontend/`, `supabase/migrations/` scaffolded with a README each (no code yet). `.gitignore` covers Python, `.env` and `dist/`.

- **Phase 2 complete (Prompts 29–30):** `backend/mortgage/` is a Python port of V1 M1–M4 and M7, built test-first (red: 5 modules failed to import → green).
  - `uv run python -m pytest` (in `backend/`) → **123 passed** (≈ 18 s; the reference parity test takes ≈ 16 s). Python 3.14.3, pytest 9.1.1 (pinned), no runtime dependencies.
  - Every V1 test of 03 for M2, M3, M4 and M7 (1–61, 80–84, 93–95, 96–109) was ported with the same name and expected values. The amounts are compared as 2-dp strings, which is stricter than V1.
  - M7 now returns data (`Calculated` / `Rejected` with error codes), not display text. Labels, messages and "hide an equal Final Payment" move to the frontend (Phase 5, tests 62–79).
  - New in V2:
    - Python-specific guards: the JS `trim()` whitespace set, `fullmatch` instead of a `$` anchor, ASCII digits only, and `-0` via `is_signed()`.
    - Second guards for single-test rules: a second zero-tail loan (1 176.40 € / 20 % / 25 y → 298 payments, from `tools/reference.py`), the private context, `-0` and the whole-number check.
    - `test_reference_parity`: all 6 800 sweep loans equal the exact reference.
  - **Hand mutation check:** 13 mutations, all caught; every rule now fails ≥ 2 tests. The mutations covered early termination, the zero-tail rule, half-even rounding, intermediate rounding, the global context, the grammar gate, `match` instead of `fullmatch`, `str.strip()`, `-0`, the whole-number check, the call order, I/O in the domain, and the import direction.
  - **V1 parity:** `tools/v1_parity.py` → 6 800 loans, **0 mismatches** against `legacy/cli` (TypeScript).
  - **Windows Application Control blocks `.venv\Scripts\pytest.exe`**: use `uv run python -m pytest`. Bash sessions that were open before the PATH change don't see `uv`; use `py -m uv`.

- **Phase 3 complete (Prompt 31; approved by the author in Prompt 32):** `api/openapi.yaml` (OpenAPI 3.1.0).
  - Contents:
    - `POST /api/v1/calculations`: raw strings in; 2-dp `Money` strings out; `422 {errors:[{field, code}]}`; `400`/`413`/`415`/`429`/`500` as problem+json.
    - `GET /api/v1/health`.
  - Independent review: `docs/v2/03-api-review.md`. Verdict "approve with changes": 5 Major, 8 Minor, **all applied**. Responses and the error vocabulary are open for Phase 7, the request stays closed, FastAPI's defaults must be overridden, error bodies never echo input, there is a 1 KiB body limit, and CORS uses an allowlist.
  - `backend/tests/contract/test_openapi.py`: 37 tests. They check that the spec is valid, that every example is valid against its schema, that every request example matches the real backend, and that money is never a number. Backend total: **160 passed**.
  - The plan's Phase 4 "done when" is now "API tests prove conformance to `openapi.yaml`" and lists the required overrides.

- **Phase 4 complete (Prompts 32–34):** FastAPI app in `backend/mortgage/api/`, implementing `api/openapi.yaml`.
  - `app.py` (routes, `create_app(cors_origins)`, serves the YAML as `/openapi.json`), `request.py` (strict body reading → 400), `problems.py` (problem+json for every HTTP error; no `detail` on 5xx), `body_limit.py` (1 KiB, checked on Content-Length and while streaming → 413).
  - The body is parsed by hand (no Pydantic body model), so FastAPI's default 422 never runs. The 400/422 split is exact by construction.
  - Run: `uv run python -m uvicorn mortgage.api.app:app --port 8000`. Set `MORTGAGE_CORS_ORIGINS` (comma-separated; default `http://localhost:5173`, the Vite dev server; `*` is refused at startup).
  - `tests/api/test_api.py`:
    - Every response is checked against the contract (status documented, Content-Type, body valid against the schema).
    - Every contract request example is run end to end.
    - All malformed cases → 400, including `"\ud800"`, invalid UTF-8, duplicate keys and `NaN`. Error bodies never echo values.
    - 413 is tested both on Content-Length and on a chunked body; 415 and 500 are tested; CORS is tested allowed and refused.
    - A 600-request seeded fuzz test checks that every response conforms.
  - **Backend: 225 passed** (deprecations as errors). Real-server smoke test with curl: 200/422/400/413/415/CORS/openapi all as documented, and the server log was empty.
  - **Hand mutation check:** 19 API mutations, all caught, each by ≥ 2 tests. One redundant guard (`parse_constant` for `NaN`) was removed, because the string check already rejects it.
  - Dependencies, pinned exactly:
    - Runtime: `fastapi` 0.159.1, `uvicorn` 0.54.0, `pyyaml` 6.0.3.
    - Test client: `httpx2` 2.16.0, because Starlette 1.9 deprecates `httpx`.
  - **Not used: schemathesis.** Windows Application Control blocks its native `jsonschema_rs` DLL, so it was replaced by the per-response contract check and the fuzz test.
  - **Not implemented: rate limiting (`429`).** The contract makes it optional and leaves the policy to configuration. It needs a decision on the limits and, once deployed, on whether a proxy handles it. Carried over to Phase 8.

- **Phase 5 complete (Prompt 35):** `frontend/`, built with Vite 8.3.5 + vanilla JS, tested with Vitest 5.0.5 (jsdom 30.1.3) and Playwright 1.64.1. All versions are pinned exactly.
  - **Modules:**
    - `formatting.js` (M5): accepts only canonical Money strings and never rounds.
    - `presentation.js` (M6): V1 texts; `shouldShowFinalPayment` compares strings; unknown codes and fields get a generic message.
    - `api-client.js`: result / invalid / failure; checks the response shape; never rejects.
    - `page.js`: per-field errors with `aria-invalid`, one general error, `maxlength="100"`, one request at a time.
    - `main.js`.
  - **Tests:**
    - **66 unit tests:** M5/M6 tests 62–79 ported. Tests 66–67 (padding and rounding) became "non-canonical amounts are rejected", because the frontend must not round. Plus client, page and a no-money-arithmetic source guard.
    - **9 Playwright e2e tests in the installed Edge against the real backend:** browser versions of V1 tests 89–91, plus early termination, all fields missing, exact text sent, the Enter key, backend unreachable and `maxlength`.
  - **Hand mutation check:** 18 mutations. 17 are caught, each by ≥ 2 guards (unit or e2e). The one that survives ("other statuses treated as 422") is equivalent: problem bodies have no `errors` list, so they are a failure either way.
    - The check showed one real gap, an empty Result panel staying visible after a failure; now tested.
    - It also showed one vacuous test, "renders text not HTML", which could not fail; removed.
  - **Manual check in the built-in browser (both servers through `.claude/launch.json`):**
    - The standard loan shows the 4 lines.
    - Invalid input shows messages under the fields, keeps the values and hides the old result.
    - At 375 px there is no horizontal scroll.
    - No JS errors; the only console line is the browser's network log for the expected 422.
  - `npm.cmd run build` works (5.6 kB JS).
  - **Windows notes:**
    - Playwright uses `channel: 'msedge'`; no browser download, and Application Control allows Edge.
    - In dev, Vite proxies `/api` to the backend, so the page and the API share one origin.

## Next Steps
1. V2, **Phase 6 — Supabase** (plan §4):
   - The `calculations` migration in `supabase/migrations/`, RLS on, no public policies.
   - `backend/mortgage/persistence/`; `POST` saves and returns `id` (still `null` if saving fails, D5).
   - **Decision D11 first:** use an existing Supabase project or create a new one.
   - Also decide whether development uses a local Supabase stack (needs Docker and the Supabase CLI) or a dedicated dev project.
2. Before Phase 8: decide the rate-limit policy (`429`).

Open for Phase 7: the FR-5 extra-payment questions in `docs/v2/01-functional.md` §2.2.

V1 is complete. Before or at the start of V2:
1. Confirm AC-3 by hand: run `npm start` (`npm.cmd start` in PowerShell), type `100 000`, `3,5` and `30`, then check the 4 result lines and exit code 0.
2. Decide whether to keep the `no-plan/` experiment (commit it on `experiment/no-plan`) or delete it.
3. Apply the V2 recommendations from `docs/v1/06-retro.md` section 6: add the rules to `CLAUDE.md`, decide the open questions above in V2's Layer 1, and start V2 planning in `docs/v2/`.

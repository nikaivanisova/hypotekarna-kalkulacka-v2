# Handoff

Notes for whoever picks up this project next: current state, open questions, and next steps.

## Current State

**Part A (Planning): complete.** **Part B (Build V1): in progress.** Steps 1–5 of `docs/v1/05-plan.md` are complete (84/84 tests green). Step 6 (Presentation, M6) is next.

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

## Open Questions
- Author decisions on findings #7–#24 in `docs/v1/04-review.md` (all Minor). Still undecided: `-0` (#9), space grouping / NBSP (#12), term `"10,0"` (#13), duplicated rounding and limits (#16, #17), the `ui → domain` rule (#18).
- Whether to display the number of payments when a loan ends early (V1 outputs do not show it).

## Next Steps
Part B, following `docs/v1/05-plan.md` section 3. Each step is test-first and ends with exactly one commit and a handoff update:
1. Scaffold + Types (M1) + architecture guard: tests 93–95 (3 total).
2. Parsing (M2): tests 1–16, 96–100 (24 total).
3. Validation (M3): tests 17–40, 101 (49 total).
4. Calculation (M4): tests 41–61, 102–108 (77 total).
5. Formatting (M5): tests 62–68 (84 total).
6. Presentation (M6): tests 69–79 (95 total).
7. Calculator facade (M7): tests 80–84, 109 (101 total).
8. CLI adapter (M8): tests 85–88, 111–112 (107 total).
9. Main + e2e (M9): tests 89–92, 110 (112 total).

**Steps 1–5: done. Current step: 6 (Presentation, M6): tests 69–79 → 95 tests in total.**

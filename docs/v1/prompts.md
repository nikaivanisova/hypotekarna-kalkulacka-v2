# V1 Prompt Log

## Prompt 1 — Project setup

### Prompt

> Create the base project structure for a V1 Mortgage Calculator.
> Create a docs/v1/ directory containing an empty prompts.md file, and create a docs/handoff.md file.
> Create a README.md with the project name and a brief description.
> Create a CLAUDE.md file with project guidelines (e.g., V1 mortgage calculator development, explicit rule for mathematical rounding to cents at the end of calculations, and logging all prompts in docs/v1/prompts.md).
> Initialize a git repository if it isn't already initialized.

### Output

- Initialized a new git repository (none existed).
- `README.md` — project name ("Mortgage Calculator") and a one-line description.
- `CLAUDE.md` — project guidelines:
  - Scope is the V1 Mortgage Calculator.
  - Keep full precision in intermediate calculations; round to cents (2 decimal places) only at the end.
  - Log every prompt in `docs/v1/prompts.md`, in chronological order.
  - Keep `docs/handoff.md` up to date.
- `docs/v1/prompts.md` — created empty.
- `docs/handoff.md` — "Current State" and "Next Steps" sections; next step is implementing the V1 calculation logic.

## Prompt 2 — Log setup and commit

### Prompt

> Log Prompt 1 and your setup output into `docs/v1/prompts.md`.
> Then, make a git commit with the message "docs: initialize project structure".

### Output

- Logged Prompt 1 (prompt text and setup output summary) in `docs/v1/prompts.md`.
- Committed all project files as `234b524 docs: initialize project structure`.

## Prompt 3 — Layer 1 interview: functional scope (01-functional.md)

### Prompt

> Log my previous request (logging setup + commit) as Prompt 2 in docs/v1/prompts.md.
>
> Then, start the interview for Layer 1 (01-functional.md):
> Interview me about the functional scope of V1 for a Mortgage Calculator.
> Ask me one question at a time to define:
> 1. Target user and core purpose (one sentence).
> 2. Functional requirements (short name, inputs, outputs, calculation rules).
> 3. Inputs and their boundaries (min/max ranges, units, required/optional, invalid input definitions).
> 4. Domain rules (formula, rounding to cents, last payment behavior).
> 5. Explicitly OUT OF SCOPE features for V1 (with a 1-sentence reason for each).
> 6. Open questions.
>
> Push back if I try to add features that are too complex for V1 (like extraordinary payments, variable interest rates, or extra fees). Keep it strictly focused on a fixed-rate annuity mortgage calculation.

### Interview

**Q1 — Target user and core purpose.** Asked who the user is and what they need (consumer vs professional; payment only vs totals; schedule needed?).

> **Answer:** The user is a consumer; main output is the payment plus totals; they don't need a month-by-month repayment schedule.

Result: *"A consumer who wants to know the fixed monthly payment, total amount paid and total interest for a fixed-rate annuity mortgage, given a loan amount, interest rate and term."*

**Q2 — Functional requirements.** Proposed FR-1 (monthly payment), FR-2 (totals), FR-3 (input validation); asked about term unit and 0% interest.

> **Answer:**
> 1. Term unit: The user enters the term in years.
> 2. 0% interest: Allowed. If interest rate = 0%, the monthly payment is simply Loan Amount / (Years * 12). Any rounding difference should go into the final payment.
>
> All listed requirements (FR-1, FR-2, FR-3) are confirmed.

**Q3 — Inputs and boundaries.** Proposed EUR, ranges, decimals, invalid-input definition; asked about currency/limits, rate convention, required fields and defaults.

> **Answer:**
> 1. Currency is € (EUR). Loan amount min €1,000.00, max €1,000,000.00. Annual interest rate min 0.00%, max 20.00%. Term min 1 year, max 30 years (whole numbers only).
> 2. Yes, nominal annual rate compounded monthly (monthly rate = annual interest rate / 12 / 100).
> 3. All three inputs are required with no defaults pre-filled. An error message must be shown for invalid/missing fields, and calculation must not run until all inputs pass validation.

Min/max recorded as inclusive.

**Q4 — Domain rules.** Proposed annuity formula and 0% formula with rounding only at the end; asked about final-payment adjustment for r > 0, rounding method, and displaying the final payment.

> **Answer:**
> 1. Yes, apply rounding adjustments to the final payment for r > 0 as well, ensuring the remaining balance reaches exactly €0.00.
> 2. Standard round half up (2.345 -> 2.35).
> 3. Show the final payment as a separate output field if it differs from the regular payment. Outputs will be: Regular Monthly Payment, Final Payment (if different), Total Paid, and Total Interest.

**Q5 — Out of scope.** Proposed 9 exclusions with reasons (schedule, extra payments, variable rates, fees/APR, non-monthly frequencies, multiple currencies, comparison, save/export, affordability); also raised whether internal monthly interest is rounded.

> **Answer:**
> 1. I confirm the entire Out of Scope list exactly as proposed.
> 2. Regarding the internal month-by-month calculation: Keep full precision for intermediate monthly interest calculations as well. Do not round intermediate values to cents step-by-step; round only the final outputs and payment amounts to cents.

**Q6 — Open questions.** Asked about input number format, output format, language, final-payment display threshold, and platform/UI.

> **Answer:**
> 1. Number inputs: Accept both '.' and ',' as decimal separators (e.g. 1000.50 or 1000,50). Ignore internal spaces if entered as thousands separators.
> 2. Output format: Slovak/EU currency style (e.g., "1 234,57 €").
> 3. Language: English for UI and error messages (to match test scenarios and code docs).
> 4. Final payment display: Yes, show the final payment whenever it differs from the regular payment by €0.01 or more.
> 5. Platform / UI: Leave open for Layer 2 (Architecture).
>
> The functional scope is now fully approved! Save the complete functional definition to `docs/v1/01-functional.md` using the required structure.
>
> After saving:
> 1. Log this entire interview prompt and response sequence into `docs/v1/prompts.md` as Prompt 3.
> 2. Make a git commit with the message "docs: create functional definition (01-functional.md)".

### Output

- Logged Prompt 2 in `docs/v1/prompts.md`.
- Conducted the six-question interview above.
- Created `docs/v1/01-functional.md` with sections: Target User and Core Purpose, Functional Requirements (FR-1–FR-3 + outputs), Inputs and Boundaries (fields, parsing, invalid input, output format, language), Domain Rules (formulas, round half up, full-precision internal balance run, final payment, totals), Out of Scope (9 items), Open Questions (OQ-1: platform/UI, deferred to Layer 2).
- Derived parsing rule recorded: a number with more than one decimal separator (e.g. `1,000.50`) is invalid, since `,` and `.` are only decimal separators.
- Updated `docs/handoff.md`.
- Committed as "docs: create functional definition (01-functional.md)".

## Prompt 4 — Layer 2: architecture (02-architecture.md)

### Prompt

> Read `docs/v1/01-functional.md`.
> Propose a modular architecture for V1 of the Mortgage Calculator and save it directly to `docs/v1/02-architecture.md`.
>
> Choose a minimal, modern tech stack (e.g., Node.js/TypeScript with Vitest, or Python with Pytest). Include a single sentence justifying each choice and state the exact command to run tests.
>
> For each module, define:
> 1. Name and single responsibility (one sentence without using the word "and").
> 2. Interface (functions, input/output types with full TypeScript or Python typing).
> 3. Which functional requirements from 01-functional.md it implements (e.g., FR-1, FR-2, FR-3).
> 4. Dependencies on other modules (ensure the calculation module is completely isolated from UI and I/O).
> 5. Extension points for features listed as "Out of Scope" in 01-functional.md.
>
> Also include:
> - Dependency direction rules (strictly no circular dependencies).
> - Data model section (explain what data V1 holds and where, e.g., in-memory state).
> - Architectural Decision Records (ADR format: Decision -> Reason -> Alternative considered).
>
> After saving `docs/v1/02-architecture.md`:
> 1. Log this prompt and a summary of the generated architecture into `docs/v1/prompts.md` as Prompt 4.
> 2. Update `docs/handoff.md` to reflect Layer 2 completion.
> 3. Make a git commit with the message "docs: create architecture definition (02-architecture.md)".

### Output

- Created `docs/v1/02-architecture.md`.
- **Tech stack:** Node.js 24 LTS, TypeScript 5 (strict), decimal.js (only runtime dependency), Vitest, tsx, npm. Tests run with `npm test` (`vitest run`).
- **OQ-1 resolved:** V1 is an interactive CLI (ADR-1); a web UI can be added later as another adapter.
- **Modules (9):**
  - M1 `domain/types`: shared types (`RawLoanInput`, `LoanInput`, `MortgageResult`, `ValidationError`, `ValidationResult`).
  - M2 `input/parsing`: `parseNumber` (`.`/`,` separators, inner spaces, written decimal count). FR-3.
  - M3 `input/validation`: `validateLoanInput` with a data-driven `V1_RULES` table, returns error codes. FR-3.
  - M4 `domain/calculation`: `calculateMortgage`, `roundToCents`; pure and isolated (depends only on types + decimal.js). FR-1, FR-2.
  - M5 `output/formatting`: `formatMoney` → `1 234,57 €`.
  - M6 `output/presentation`: `toResultView`, `toErrorView`, `shouldShowFinalPayment`; all English texts. FR-1, FR-2, FR-3.
  - M7 `app/calculator`: `runCalculator` (validate → calculate only if valid → present). FR-3 gate.
  - M8 `ui/cli`: `runCli` over an injectable `TerminalIo` port; the only module with user I/O.
  - M9 `main`: composition root.
- **Dependency rules:** `main → ui → app → {input, output} → domain`; domain has no I/O; input and output don't import each other; no cycles; enforced by `tests/architecture.test.ts`.
- **Data model:** stateless, in-memory only; one-way data flow from raw strings to `Decimal` values to display strings; all money as `Decimal`, never `number`.
- **Extension points:** schedule (`amortize` generator extracted from the balance run), extra payments (per-month adjustment hook), variable rates (`rateForMonth`), payment frequency (`paymentsPerYear`), currencies (formatter/parser options), fees/APR and affordability (new domain modules), comparison (`runComparison`, `toComparisonView`), save/export (`app/export` use case + adapter outside domain).
- **ADRs (8):** CLI platform; TypeScript/Node vs Python; decimal.js vs float/integer cents/big.js; custom formatter vs `Intl`; error codes vs messages in validation; full-precision balance run vs closed-form; architecture test vs dependency-cruiser; pure core with I/O behind a port.
- Updated `docs/handoff.md`.
- Committed as "docs: create architecture definition (02-architecture.md)".

## Prompt 5 — Layer 3: test scenarios (03-test-scenarios.md)

### Prompt

> Read `docs/v1/01-functional.md` and `docs/v1/02-architecture.md`.
> Propose test scenarios for V1 in a single markdown table and save it to `docs/v1/03-test-scenarios.md`.
>
> The table must include the following columns:
> - Test Name (unique snake_case or camelCase name to be used directly as the test name in code, e.g., test_annuity_standard_rate)
> - Level (unit / functional / e2e)
> - Module & Implemented Requirement (which module and FR ID it checks, e.g., calculation / FR-1)
> - Input & Expected Output (exact values, money down to the cent, e.g., Input: P=100000, r=3.5%, term=30y -> Regular: 449.04 EUR, Final: 449.04 EUR, Total Paid: 161654.40 EUR, Interest: 61654.40 EUR)
> - Reference Source (independently verified source, e.g., manual calculation, spreadsheet formula, or external calculator)
> - Type (happy path / edge case / invalid input)
>
> Minimum Coverage Requirements:
> 1. Every functional requirement (FR-1, FR-2, FR-3) must have at least one test.
> 2. Every module with calculation logic must have edge cases (e.g., 0% interest rate, 1 year term, 30 year term, rounding boundary conditions like .005) and invalid inputs (e.g., negative loan, text string, multiple decimal points).
> 3. Include at least one full end-to-end scenario (E2E) testing the CLI application from user input prompt to displayed output.
>
> After saving `docs/v1/03-test-scenarios.md`:
> 1. Log this prompt and a summary of the generated test scenarios into `docs/v1/prompts.md` as Prompt 5.
> 2. Update `docs/handoff.md` to show Layer 3 completion.
> 3. Make a git commit with the message "docs: create test scenarios (03-test-scenarios.md)".

### Output

- Created `docs/v1/03-test-scenarios.md` with **95 scenarios** in one table (columns: #, Test Name, Level, Module & Implemented Requirement, Input & Expected Output, Reference Source, Type).
  - By module: parsing 16, validation 24, calculation 21 (incl. `roundToCents`), formatting 7, presentation 11, calculator 5, CLI 4, e2e 4, architecture 3.
  - By level: 82 unit, 9 functional (calculator + CLI with fake `TerminalIo`), 4 e2e (spawned `npx tsx src/main.ts` with piped stdin).
  - Coverage: FR-1, FR-2 and FR-3 each covered by many tests; edge cases for 0 % rate, 1-year and 30-year terms, min/max boundaries (inclusive and just outside), exact half-cent (`P=1000.14, 0 %, 1y → 83.345 → 83.35`), just above/below half-cent with interest, final payment equal / ±€0.01 / lower than regular; invalid inputs for negative values, text, multiple separators, too many decimals, fractional term, missing fields.
- **Reference values** were computed with an independent Python `decimal` script (60 digits, ROUND_HALF_UP, iterative balance run cross-checked against the closed-form remaining balance; script in the doc's appendix) and re-checked with a separate float PMT implementation in Node.js. All values agreed.
- **Correction to the prompt's example:** P=100000, 3.5 %, 30y gives Final **452.02** (not 449.04), Total Paid **161657.38**, Interest **61657.38**, because the regular payment is rounded down and the final payment absorbs the €2.98 shortfall (01-functional.md §4.4).
- Added an "Expected UI texts" section that fixes the exact CLI prompts, result labels and English error messages per error code, since 01/02 did not define them.
- Documented that the calculation module receives only validated input, so its invalid-input coverage is the calculator tests asserting `calculateMortgage` is never called for invalid input.
- Updated `docs/handoff.md`.
- Committed as "docs: create test scenarios (03-test-scenarios.md)".

## Prompt 6 — Layer 4: independent review (04-review.md)

### Prompt

> You are an independent code reviewer. You did not write this plan.
> Read ONLY `docs/v1/01-functional.md`, `docs/v1/02-architecture.md`, and `docs/v1/03-test-scenarios.md`.
> Do not trust claims; verify them critically against the files.
>
> Perform the following independent audit:
> 1. Coverage: Does every requirement in 01-functional.md have a module in 02-architecture.md and a test in 03-test-scenarios.md? Does every test check a real requirement?
> 2. Ambiguities: Identify any requirements or rules that could be implemented in two different ways with different results.
> 3. Missing Scenarios: List unhandled edge cases or invalid input formats not covered in 03-test-scenarios.md.
> 4. Architecture Stress Test: For 3 out-of-scope features (e.g., extra payments, variable rates, repayment schedule), detail exactly which modules would need to change. Flag an architectural issue if more than one existing module must be modified.
> 5. Reference Value Audit: Write and run a standalone verification script to recompute all financial test values in 03-test-scenarios.md. Do not estimate.
>
> Format all findings into a Markdown table in `docs/v1/04-review.md` with columns:
> - `#` (Finding number)
> - `Severity` (Blocker / Major / Minor)
> - `Affects` (Requirement, Module, or Test)
> - `Finding` (Detailed description of the issue)
> - `Author Decision` (Leave blank)
> - `Reason` (Leave blank)
>
> Do not modify any files other than `docs/v1/04-review.md`.
>
> After saving `docs/v1/04-review.md`:
> 1. Log this prompt into `docs/v1/prompts.md` as Prompt 6.
> 2. Update `docs/handoff.md` to reflect Layer 4 audit completion.
> 3. Make a git commit with the message "docs: create independent review findings (04-review.md)".

### Output

- Created `docs/v1/04-review.md` with **24 findings** (1 Blocker, 5 Major, 18 Minor) in one table. The `Author Decision` and `Reason` columns are left blank.
- **Blocker (#1):** the §4.4 final-payment rule gives a **negative Final Payment** for valid inputs. Example: P = 1 000.29, 20 %, 30 y → Regular 16.72, Final −97.42. Thousands of such inputs exist at high rates and 25–30-year terms, and even at 8 %/30 y. The architecture invariant `finalPayment > 0` is false, and test 60 does not detect it.
- **Major:** the M8 `readline/promises` adapter loses piped stdin lines and hangs on EOF (verified on Node 24.20.0, exit 13), so e2e tests 89–92 would fail; the number grammar is undefined and decimal.js accepts `0x3E8`, `Infinity` and `NaN`; there is no domain-wide invariant sweep; extra payments and variable rates each require changes to 5+ existing modules (architectural issues).
- **Minor:** ambiguities ("exactly €0.00" vs a rounded final payment, `-0`, edge separators, `+` and Unicode signs, space grouping and NBSP, term `"10,0"`, the meaning of "full precision", half-up for negatives); duplicated rounding and limits across modules; contradictory `ui → domain` rules; tests asserting texts defined only in 03; inflated traceability; the non-reproducible REF-PMT; the schedule stress test; and missing parser/validation/CLI scenarios.
- **Reference value audit:** recomputed with exact rational arithmetic (Python `fractions`). **All 18 calculation scenarios, 11 rounding checks and the M claims in 03 are correct.** 40-digit Decimal matched the exact results on 300 random inputs. The scripts and their outputs are in the appendix of 04.
- Updated `docs/handoff.md`.
- Committed as "docs: create independent review findings (04-review.md)".

## Prompt 7 — Review resolutions for findings #1–#6

### Prompt

> Update `docs/v1/04-review.md` by populating the 'Author Decision' and 'Reason' columns for findings #1 through #6 with the following resolutions:
>
> 1. Finding #1 (Blocker - Negative Final Payment):
>    - Decision: Accepted.
>    - Resolution: Update 01-functional.md, 02-architecture.md, and 03-test-scenarios.md so that if compound interest creates an overpayment scenario where the loan balance reaches <= €0.00 before month n, the loan terminates early. The final payment is defined as the exact remaining balance plus accrued interest for that final active month, and any remaining future months are skipped. Update test scenarios to cover early termination cases.
>
> 2. Finding #2 (Major - Node readline stdin stream handling):
>    - Decision: Accepted.
>    - Resolution: Update 02-architecture.md's CLI module interface to handle EOF gracefully and process piped inputs using a robust stream reader pattern (handling line events rather than relying on sequential readline question promises).
>
> 3. Finding #3 (Major - Number formatting and strict parsing):
>    - Decision: Accepted.
>    - Resolution: Update 01-functional.md and parsing module specs to strictly enforce regex validation on raw inputs prior to passing to decimal.js, explicitly rejecting hex (0x), exponent notation (1e5), NaN, and Infinity.
>
> 4. Finding #4 (Major - Invariant tests):
>    - Decision: Accepted.
>    - Resolution: Add a property-based / invariant test scenario to 03-test-scenarios.md that asserts: Total Paid == Sum of Payments, and Final Payment is strictly > 0 and <= Regular Payment.
>
> 5. Findings #5 & #6 (Major - Architecture Stress Test out-of-scope friction):
>    - Decision: Accepted as documented trade-offs.
>    - Resolution: Retain V1 architecture as designed. Note in 02-architecture.md that V2 extension for variable rates will introduce a dedicated schedule calculation module.
>
> Save `04-review.md`, update `01-functional.md`, `02-architecture.md`, and `03-test-scenarios.md` with these accepted changes, and make a git commit with message "docs: update specs with review resolutions (01, 02, 03, 04)".

### Clarification

**Q — Invariant "Final ≤ Regular" (finding #4).** It is false for many verified full-term loans (e.g. test 43: Final 452.02 > Regular 449.04). How should it read?

> **Answer:** Scope it: Final > 0 always; Final ≤ Regular only when the loan ends early.

### Output

- `04-review.md`: Author Decision / Reason filled in for #1–#6; #7–#24 remain open.
- `01-functional.md`: §3.2 strict grammar `^-?[0-9]+([.,][0-9]+)?$` applied before conversion (rejects hex/binary/octal, exponents, `NaN`, `Infinity`, bare separators, `+` and Unicode signs); §4.4 rewritten with an amount-due loop, early termination, the "rounds to €0.00" rule (previous payment becomes final) and result properties; §4.5 and FR-2 use k = payments made.
- `02-architecture.md`: M1 `numberOfPayments` = payments made; M2 `NUMBER_PATTERN` and ordered parsing steps; M4 early-termination steps and invariants; M4 V2 note (dedicated schedule module for variable rates); M8 event-driven line-queue terminal reader with injectable streams; ADR-9 (accepted extension friction) and ADR-10 (line queue); test strategy updated.
- `03-test-scenarios.md`: tests 96–112 added (strict grammar 96–101, early termination 102–106, full-term counter-case 107, property sweep 108, calculator/e2e early termination 109–110, terminal reader 111–112); new reference REF-ET (exact rationals, Appendix B, run as published: sweep 6 800 inputs, 767 early, 0 violations); coverage tables updated. Existing values unchanged.
- Verified a prototype of the line-queue reader on Node 24.20.0 (piped stdin, CRLF, EOF).
- Updated `docs/handoff.md`.
- Committed as "docs: update specs with review resolutions (01, 02, 03, 04)".

## Prompt 8 — Final execution plan (05-plan.md)

### Prompt

> Read `docs/v1/01-functional.md` through `docs/v1/04-review.md`.
> Write the final execution plan to `docs/v1/05-plan.md`.
>
> Structure the document with the following required sections:
> 1. V1 Goals: 2-4 measurable boolean goals (e.g., 100% test scenario pass rate across all 112 tests, clean execution on Node 24 LTS, zero external runtime UI dependencies).
> 2. Final Scope & Acceptance Criteria:
>    - Explicit list of exact test names (tests 1 through 112) from 03-test-scenarios.md that MUST pass.
>    - Technical acceptance criteria (e.g., `npm test` runs with 0 failures, CLI runs interactively via `npm start`).
> 3. Implementation Order:
>    - Modules in strict dependency order:
>      1. Types (`types.ts`)
>      2. Parsing (`parsing.ts`)
>      3. Validation (`validation.ts`)
>      4. Calculation (`calculation.ts`)
>      5. Formatting (`formatting.ts`)
>      6. Presentation (`presentation.ts`)
>      7. Calculator Facade (`calculator.ts`)
>      8. CLI Terminal Adapter (`cli.ts`)
>      9. Main Entrypoint (`main.ts`)
>    - For each module, list: module to build, corresponding test IDs from 03-test-scenarios.md, and explicit single git commit message.
> 4. Definition of Done per Step: Unit tests green, all previous tests remain green, single git commit, update `docs/handoff.md`.
> 5. Execution Tooling: Vitest test runner, event-driven line queue stream strategy for CLI stdin.
> 6. Risks & Contingencies: Summary of addressed review findings (early payoff rule, sub-half-cent rounding tail rule, non-blocking stream reader for CLI).
>
> After saving `docs/v1/05-plan.md`:
> 1. Log this prompt into `docs/v1/prompts.md` as Prompt 8.
> 2. Update `docs/handoff.md` to show Part A (Planning) complete and Part B (Build V1) ready to commence.
> 3. Make a git commit with the message "docs: create final execution plan (05-plan.md)".

### Output

- Created `docs/v1/05-plan.md`:
  - **Goals G1–G4:** 112/112 tests pass with 0 skipped; Node 24 + clean type-check + interactive `npm start`; `decimal.js` is the only runtime dependency; the architecture rules hold.
  - **Scope & acceptance:** all 112 exact test names (generated from 03, each mapped to its build step) and technical criteria AC-1–AC-7. Open Minor findings #7–#24 follow the literal spec text and do not block the build.
  - **Implementation order:** 9 steps (M1 with scaffold and architecture guard → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9), with test IDs, cumulative counts (3/24/49/77/84/95/101/107/112) and one commit message per step.
  - **Definition of Done:** step tests green, all earlier tests green, type-check clean, handoff and prompt log updated, exactly one commit; expected values in 03 are never changed during the build.
  - **Tooling:** Vitest, tsx, tsc, decimal.js, and the event-driven line-queue stdin reader.
  - **Risks:** the addressed findings (early payoff, sub-half-cent tail rule, line-queue reader, strict grammar, property sweep, trade-offs) plus implementation risks (ES-module spying for tests 82–83, sweep runtime, `npx` spawn on Windows, CRLF, global Decimal rounding) and the unconfirmed points.
- Updated `docs/handoff.md` (Part A complete, Part B ready).
- Committed as "docs: create final execution plan (05-plan.md)".

## Prompt 9 — Part B, Step 1: project setup, domain types, architecture guard

### Prompt

> Read `docs/v1/05-plan.md`. We are starting Part B (Build V1), Step 1.
>
> Execute Step 1 according to the plan:
> 1. Set up project configuration: `package.json`, `tsconfig.json`, `vitest.config.ts`, installing `decimal.js` as the sole runtime dependency, and `typescript`, `tsx`, and `vitest` as dev dependencies.
> 2. Implement Module 1 (`src/types.ts`) with shared data types and interfaces.
> 3. Write architecture dependency tests (`tests/architecture.test.ts`) covering test IDs 93, 94, and 95 from `docs/v1/03-test-scenarios.md`.
> 4. Run `npm test` and type-checking to verify that tests 93-95 pass.
>
> After verifying Step 1 completion:
> 1. Log this build step into `docs/v1/prompts.md` as Prompt 9.
> 2. Update `docs/handoff.md` showing Step 1 complete and Step 2 (Parsing) ready.
> 3. Make a git commit with the message specified in `05-plan.md` for Step 1: "feat: setup project structure and domain types".

### Output

- **Configuration:** `package.json` (`"type": "module"`, `engines.node >= 24`, scripts `test` / `start` / `typecheck`), `tsconfig.json` (`strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `module`/`moduleResolution: NodeNext`, `verbatimModuleSyntax`, `noEmit`), `vitest.config.ts` (`tests/**/*.test.ts`), `.gitignore`.
- **Dependencies:** `decimal.js` 10.6.0 is the only runtime dependency. Dev dependencies: `typescript` 5.9.3, `tsx` 4.23.15, `vitest` 5.0.5, `@types/node` 24.
  - npm initially chose TypeScript 7 and `@types/node` 26. They were pinned to `^5` / `^24` to match 02 §1 (TypeScript 5) and the Node 24 runtime.
- **M1:** `src/domain/types.ts`, exactly as in 02 M1, with `numberOfPayments` documented as the payments actually made.
  - The path follows 05-plan / 02 (`src/domain/`), not `src/types.ts` as written in the prompt, because the layer rules and test 94 depend on it.
  - It uses `import type { Decimal } from 'decimal.js'`: under NodeNext, the default import resolves to a namespace (TS2709).
- **Architecture guard:** `tests/architecture.test.ts` with tests 93–95 (`test_architecture_dependency_direction`, `test_architecture_domain_has_no_io`, `test_architecture_no_circular_dependencies`).
  - It has an explicit per-layer allow-list, an I/O-global check and a DFS cycle check.
  - Each test also asserts that the checker rejects known-bad edges and cycles, so it cannot pass vacuously.
  - Confirmed by temporarily adding violating files to `src/`: all 3 tests failed with the expected messages, then passed again after the files were removed.
- **Verification:** `npm test` → 1 file, **3 passed (3)**; `npm run typecheck` → 0 errors.
- Commit message: the exact Step 1 message from `05-plan.md` §3 was used ("feat: scaffold project and add domain types with architecture guard (M1)"), because the message quoted in the prompt differs from the plan.
- Updated `docs/handoff.md`.

## Prompt 10 — Part B, Step 2: parsing (M2), test-first

### Prompt

> Read `docs/v1/05-plan.md`. We are executing Part B (Build V1), Step 2.
>
> Follow the Test-First (TDD) workflow for Module 2 (Parsing):
> 1. Write unit tests in `tests/parsing.test.ts` for test IDs 1 through 21 (from `docs/v1/03-test-scenarios.md`).
> 2. Verify that running `npm test` fails as expected (Red).
> 3. Implement `src/parsing/parse-input.ts` matching M2 in `02-architecture.md` (and strict number validation rules from review finding #3). Remember to use `.js` relative imports (e.g., `import { ... } from '../domain/types.js'`).
> 4. Run `npm test` and `npm run typecheck` to verify that all 24 tests (3 existing architecture tests + 21 parsing tests) pass cleanly with zero type errors (Green).
>
> After verifying Step 2 completion:
> 1. Log this step into `docs/v1/prompts.md` as Prompt 10.
> 2. Update `docs/handoff.md` to show Step 2 complete and Step 3 (Validation) ready.
> 3. Make a git commit using the exact message specified in `05-plan.md` for Step 2: "feat: implement input parsing with strict numeric cleaning (M2)".

### Output

- **Deviations from the prompt, following `05-plan.md` §3:**
  - **Test IDs:** the 21 parsing tests are IDs **1–16 and 96–100**. IDs 17–21 are validation tests (Step 3).
  - **Paths:** `src/input/parsing.ts` and `tests/input/parsing.test.ts`. `src/parsing/` is not a layer in 02 §2, and the architecture guard (test 93) rejects modules outside the known layers.
  - **Commit message:** the plan's Step 2 message ("feat: add strict number parsing (M2)") was used; the prompt's quoted message differs from the plan.
- **Red:** with a missing module, the suite failed to load. With a throwing stub, the result was **21 failed, 3 passed**.
- **Green:** `src/input/parsing.ts` exports `ParseResult`, `NUMBER_PATTERN` (`/^-?[0-9]+(?:[.,]([0-9]+))?$/`) and `parseNumber`, in the order from 02 M2:
  1. `undefined`, or empty after trimming → `empty`;
  2. trim, then remove inner spaces;
  3. `NUMBER_PATTERN` gatekeeper → `not_a_number`;
  4. `,` → `.`, then `new Decimal()`.
  `writtenDecimals` counts the fraction digits as typed.
- **Verification:** `npm test` → 2 files, **24 passed (24)**; `npm run typecheck` → 0 errors.
- Updated `docs/handoff.md`.

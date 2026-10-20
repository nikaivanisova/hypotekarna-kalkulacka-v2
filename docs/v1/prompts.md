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

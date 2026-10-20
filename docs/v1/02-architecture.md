# 02 — Architecture (V1)

Status: **Proposed** (2026-10-20)

Source of requirements: [`01-functional.md`](01-functional.md) (FR-1, FR-2, FR-3; Out of Scope list in section 5).

This document resolves **OQ-1 (Platform / UI)**: V1 is an **interactive command-line application** (see ADR-1). The CLI is a thin adapter, so a web or desktop UI can replace it later without touching the calculation core.

---

## 1. Tech Stack

| Choice | Justification |
|---|---|
| **Node.js 24 LTS** | A long-term-support runtime that runs the same TypeScript core in a terminal now and in a browser later. |
| **TypeScript 5 (strict mode)** | Static types make every module interface explicit and checked at compile time. |
| **decimal.js** | Arbitrary-precision decimal arithmetic gives the full intermediate precision and exact round-half-up that section 4.3 requires, which binary floating point cannot. |
| **Vitest** | A fast, zero-config TypeScript-native test runner with built-in assertions and coverage. |
| **tsx** | Runs TypeScript directly in development without a separate build step. |
| **npm** | The package manager bundled with Node.js, so no extra tool is needed. |

No other runtime dependencies are used. `decimal.js` is the only production dependency.

### Commands

| Purpose | Command |
|---|---|
| Install dependencies | `npm install` |
| **Run tests** | **`npm test`** (runs `vitest run`) |
| Run the calculator | `npm start` (runs `tsx src/main.ts`) |
| Type-check | `npm run typecheck` (runs `tsc --noEmit`) |

### TypeScript settings

`strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`, `module: "NodeNext"`.

---

## 2. Module Overview

```
src/
├── domain/
│   ├── types.ts          # M1  Domain types
│   └── calculation.ts    # M4  Mortgage calculation (pure, isolated)
├── input/
│   ├── parsing.ts        # M2  Number parsing
│   └── validation.ts     # M3  Input validation
├── output/
│   ├── formatting.ts     # M5  Money formatting
│   └── presentation.ts   # M6  View building + English texts
├── app/
│   └── calculator.ts     # M7  Use-case orchestration
├── ui/
│   └── cli.ts            # M8  Terminal adapter (only module with user I/O)
└── main.ts               # M9  Composition root / entry point

tests/                    # mirrors src/, one *.test.ts per module
└── architecture.test.ts  # enforces the dependency rules in section 4
```

### Requirement coverage

| Requirement | Modules |
|---|---|
| FR-1 Calculate monthly payment | M4 (formula, final payment), M5 (money format), M6 (final payment visibility) |
| FR-2 Calculate totals | M4 (totals), M5, M6 |
| FR-3 Validate inputs | M2 (parsing rules 3.2), M3 (invalid-input rules 3.3), M6 (English error messages), M7 (no calculation until valid) |
| Section 3.4 Output format | M5 |
| Section 3.5 Language | M6 |

---

## 3. Module Specifications

All code samples are TypeScript. `Decimal` refers to the `decimal.js` class.

### M1 — `domain/types`

1. **Responsibility:** Defines the shared data shapes that flow between modules.
2. **Interface:**

   ```ts
   import type Decimal from 'decimal.js';

   export type Field = 'loanAmount' | 'annualRate' | 'termYears';

   /** Exactly what the user typed; `undefined` means the field was not provided. */
   export interface RawLoanInput {
     readonly loanAmount: string | undefined;
     readonly annualRate: string | undefined;
     readonly termYears: string | undefined;
   }

   /** A loan request that has passed validation (M3 is the only producer). */
   export interface LoanInput {
     readonly principal: Decimal;          // EUR, 1 000.00 – 1 000 000.00
     readonly annualRatePercent: Decimal;  // 0.00 – 20.00
     readonly termYears: number;           // integer, 1 – 30
   }

   /** All amounts are already rounded to cents (round half up). */
   export interface MortgageResult {
     readonly numberOfPayments: number;    // n = termYears × 12
     readonly regularPayment: Decimal;     // M_rounded
     readonly finalPayment: Decimal;
     readonly totalPaid: Decimal;
     readonly totalInterest: Decimal;
   }

   export type ValidationErrorCode =
     | 'required'
     | 'not_a_number'
     | 'negative'
     | 'below_min'
     | 'above_max'
     | 'too_many_decimals'
     | 'not_whole_number';

   export interface ValidationError {
     readonly field: Field;
     readonly code: ValidationErrorCode;
   }

   export type ValidationResult =
     | { readonly ok: true; readonly value: LoanInput }
     | { readonly ok: false; readonly errors: readonly ValidationError[] };
   ```

3. **Implements:** none directly; it is the shared vocabulary for FR-1, FR-2 and FR-3.
4. **Dependencies:** `decimal.js` (type only). No project modules.
5. **Extension points:**
   - *Payment frequencies other than monthly:* add `paymentsPerYear` to `LoanInput` (V1 fixes it at 12 inside M4).
   - *Multiple currencies:* add a `currency` field to `LoanInput` and `MortgageResult`.
   - *Variable rates:* replace `annualRatePercent` with a `RateSchedule` type (a list of rate periods).
   - *Extra payments:* add an optional `extraPayments: readonly { month: number; amount: Decimal }[]`.

---

### M2 — `input/parsing`

1. **Responsibility:** Converts one raw text value into an exact decimal number according to the V1 number format rules.
2. **Interface:**

   ```ts
   import type Decimal from 'decimal.js';

   export type ParseResult =
     | {
         readonly ok: true;
         readonly value: Decimal;
         /** Decimal places as written by the user, e.g. "1000,500" → 3. */
         readonly writtenDecimals: number;
       }
     | { readonly ok: false; readonly error: 'empty' | 'not_a_number' };

   export function parseNumber(raw: string | undefined): ParseResult;
   ```

   Rules (section 3.2): trim leading and trailing whitespace; remove inner spaces; accept `.` or `,` as the single decimal separator; reject more than one separator (`1,000.50` → `not_a_number`); a leading `-` is parsed, so M3 can report `negative`. `writtenDecimals` counts the digits as typed, so trailing zeros count (`1000,500` is 3 places).

3. **Implements:** FR-3 (section 3.2 parsing; the "empty" and "not a number" cases in section 3.3).
4. **Dependencies:** `decimal.js`. No project modules.
5. **Extension points:**
   - *Multiple currencies / locales:* add an optional `options: { decimalSeparators: readonly string[] }` parameter with today's rules as the default.

---

### M3 — `input/validation`

1. **Responsibility:** Decides whether a set of raw inputs forms a valid loan request.
2. **Interface:**

   ```ts
   import type Decimal from 'decimal.js';
   import type { Field, RawLoanInput, ValidationResult } from '../domain/types';

   export interface FieldRule {
     readonly min: Decimal;           // inclusive
     readonly max: Decimal;           // inclusive
     readonly maxDecimals: number;    // 2 for money/rate, 0 for term
     readonly wholeNumber: boolean;
   }

   export const V1_RULES: Readonly<Record<Field, FieldRule>>;

   export function validateLoanInput(
     raw: RawLoanInput,
     rules?: Readonly<Record<Field, FieldRule>>,   // defaults to V1_RULES
   ): ValidationResult;
   ```

   Every field is checked independently, so all invalid fields are reported at once. Each field gets at most one error, checked in this order: `required` → `not_a_number` → `negative` → `not_whole_number` (term only) → `too_many_decimals` → `below_min` / `above_max`.

3. **Implements:** FR-3 (section 3.1 boundaries, section 3.3 invalid-input definition).
4. **Dependencies:** M1, M2, `decimal.js`.
5. **Extension points:**
   - *New inputs (fees, extra payments, income for affordability):* add a `Field` value and a `FieldRule` entry. The validation loop is driven by data, not rewritten.
   - *Different limits per product or currency:* pass a different `rules` table.

---

### M4 — `domain/calculation`

1. **Responsibility:** Computes the payment figures of a fixed-rate annuity mortgage from a valid loan request.
2. **Interface:**

   ```ts
   import Decimal from 'decimal.js';
   import type { LoanInput, MortgageResult } from './types';

   export function calculateMortgage(input: LoanInput): MortgageResult;

   /** Round half up to 2 decimal places (section 4.3). */
   export function roundToCents(amount: Decimal): Decimal;
   ```

   Internal steps, which are not exported (sections 4.1–4.5):
   1. `n = termYears × 12`, `r = annualRatePercent ÷ 12 ÷ 100` (full precision).
   2. `M = r > 0 ? P·r·(1+r)ⁿ / ((1+r)ⁿ − 1) : P ÷ n`; then `M_rounded = roundToCents(M)`.
   3. Balance run: `B = P`; for months 1 … n−1, `B = B·(1+r) − M_rounded`, with no intermediate rounding.
   4. `finalPayment = roundToCents(B·(1+r))`.
   5. `totalPaid = M_rounded·(n−1) + finalPayment`; `totalInterest = totalPaid − P`.

   The module uses a private `Decimal.clone({ precision: 40, rounding: Decimal.ROUND_HALF_UP })` so it never depends on or changes global Decimal settings.

   **Invariants covered by tests:** the balance after the final payment is within half a cent of €0.00 before rounding; `totalInterest ≥ 0`; `finalPayment > 0`; at 0 % the final payment equals `P − M_rounded·(n−1)` exactly.

3. **Implements:** FR-1 (regular and final payment), FR-2 (totals).
4. **Dependencies:** M1, `decimal.js`. **Nothing else.** It performs no I/O, holds no state, uses no clock or randomness, and does not know about strings, formatting, validation messages or the UI. It is a pure function of its input.
5. **Extension points:**
   - *Month-by-month schedule:* extract the balance run (step 3) into an exported generator `amortize(input): Iterable<ScheduleRow>`. `calculateMortgage` then consumes it, so the schedule and totals can never disagree.
   - *Extra / one-off payments:* the balance run gains an optional per-month adjustment hook `(month, balance) => Decimal`.
   - *Variable rates:* replace the constant `r` with a `rateForMonth(month)` function derived from a `RateSchedule`.
   - *Other payment frequencies:* replace the constant `12` with `paymentsPerYear`.
   - *Fees, insurance, APR/RPMN:* add a **new** module `domain/costs` that takes `LoanInput` + `MortgageResult` as input. M4 does not change.
   - *Affordability checks:* add a **new** module `domain/affordability` that takes `MortgageResult` + income data. M4 does not change.

---

### M5 — `output/formatting`

1. **Responsibility:** Renders a monetary amount as Slovak/EU-style euro text.
2. **Interface:**

   ```ts
   import type Decimal from 'decimal.js';

   /** e.g. 1234.567 → "1 234,57 €" (regular ASCII spaces, round half up). */
   export function formatMoney(amount: Decimal): string;
   ```

3. **Implements:** section 3.4 (output format for FR-1 and FR-2 results).
4. **Dependencies:** `decimal.js`. No project modules. It does not use `Intl` (see ADR-4).
5. **Extension points:**
   - *Multiple currencies:* add an optional `options: { symbol: string; thousandsSeparator: string; decimalSeparator: string; symbolPosition: 'before' | 'after' }` parameter with the EUR/SK style as the default.

---

### M6 — `output/presentation`

1. **Responsibility:** Turns calculation results or validation errors into display-ready English text.
2. **Interface:**

   ```ts
   import type { Field, MortgageResult, ValidationError } from '../domain/types';

   export interface ResultLine {
     readonly label: string;   // e.g. "Regular Monthly Payment"
     readonly value: string;   // e.g. "1 234,57 €"
   }

   export interface ResultView {
     readonly lines: readonly ResultLine[];
   }

   export interface FieldErrorView {
     readonly field: Field;
     readonly label: string;    // e.g. "Loan amount"
     readonly message: string;  // e.g. "Loan amount must be between 1 000,00 € and 1 000 000,00 €."
   }

   export interface ErrorView {
     readonly errors: readonly FieldErrorView[];
   }

   export const FIELD_LABELS: Readonly<Record<Field, string>>;

   /** True when |finalPayment − regularPayment| ≥ €0.01 (section 2, Outputs). */
   export function shouldShowFinalPayment(result: MortgageResult): boolean;

   export function toResultView(result: MortgageResult): ResultView;
   export function toErrorView(errors: readonly ValidationError[]): ErrorView;
   ```

   Output order: Regular Monthly Payment, Final Payment (only if shown), Total Paid, Total Interest.

3. **Implements:** FR-1 and FR-2 (which outputs are shown, and their labels), FR-3 (one English error message per invalid field), section 3.5 (English).
4. **Dependencies:** M1, M5.
5. **Extension points:**
   - *Month-by-month schedule:* add `toScheduleView(rows)`.
   - *Comparing scenarios:* add `toComparisonView(results: readonly MortgageResult[])`. The existing views stay unchanged.
   - *Fees/APR, affordability:* add more `ResultLine`s produced from the new domain modules' results.
   - *Other languages:* all texts sit in one `MESSAGES` table, which can be replaced by a locale lookup.

---

### M7 — `app/calculator`

1. **Responsibility:** Orchestrates one calculation request from raw inputs to a display-ready outcome.
2. **Interface:**

   ```ts
   import type { RawLoanInput } from '../domain/types';
   import type { ErrorView, ResultView } from '../output/presentation';

   export type CalculatorOutcome =
     | { readonly kind: 'result'; readonly view: ResultView }
     | { readonly kind: 'invalid'; readonly view: ErrorView };

   export function runCalculator(raw: RawLoanInput): CalculatorOutcome;
   ```

   Flow: `validateLoanInput` → if invalid, return `toErrorView` and **do not call** `calculateMortgage` (FR-3) → otherwise `calculateMortgage` → `toResultView`.

3. **Implements:** FR-3 (the "no calculation until all inputs are valid" rule), plus the end-to-end flow for FR-1 and FR-2.
4. **Dependencies:** M1, M3, M4, M6. It is pure and synchronous, with no I/O.
5. **Extension points:**
   - *Any new UI (web, desktop):* calls `runCalculator` exactly as the CLI does.
   - *Comparing scenarios:* add `runComparison(raws: readonly RawLoanInput[])`, which maps over the same pipeline.
   - *Saving / exporting / sharing:* add a separate `app/export` use case that takes the `CalculatorOutcome` plus a port interface (`ResultSink`). The file or network adapter lives in `ui/` (or a new `infra/`), never in `domain/`.

---

### M8 — `ui/cli`

1. **Responsibility:** Exchanges text with the user through the terminal.
2. **Interface:**

   ```ts
   /** Port: the only way the CLI touches the outside world (injectable for tests). */
   export interface TerminalIo {
     ask(question: string): Promise<string | undefined>;  // undefined = input stream closed
     print(line: string): void;
     close(): void;
   }

   export function createNodeTerminalIo(): TerminalIo;  // node:readline/promises + stdout
   export async function runCli(io: TerminalIo): Promise<number>;  // returns the process exit code
   ```

   Behaviour: asks for loan amount, annual interest rate and term (no pre-filled defaults). It passes the answers to `runCalculator`. On `invalid`, it prints each field's message and asks again for the invalid fields only. On `result`, it prints `label: value` lines and exits with code 0. If the input stream closes (Ctrl+D / Ctrl+C), it exits with code 1.

3. **Implements:** the user-facing part of FR-1, FR-2 and FR-3 (shows results and per-field errors). This resolves OQ-1.
4. **Dependencies:** M1 (types), M7, `node:readline/promises`. It does **not** import M2–M6 directly.
5. **Extension points:**
   - *Web/desktop UI:* add a sibling adapter (e.g. `ui/web`) with the same dependency on M7. M8 stays as is.
   - *Saving / exporting:* add an `--export <file>` option that calls the future `app/export` use case.

---

### M9 — `main`

1. **Responsibility:** Wires the Node.js terminal to the CLI adapter at program start.
2. **Interface:**

   ```ts
   // Entry point, no exports.
   // const io = createNodeTerminalIo();
   // process.exitCode = await runCli(io);
   ```

3. **Implements:** none directly; it is the composition root.
4. **Dependencies:** M8.
5. **Extension points:**
   - *Alternative front-ends / configuration:* choose the adapter or rules table here (e.g. a `--web` flag) without changing the inner modules.

---

## 4. Dependency Direction Rules

```
            main (M9)
               │
               ▼
           ui/cli (M8)
               │
               ▼
        app/calculator (M7)
        │       │        │
        ▼       ▼        ▼
 input/ (M2,M3)  output/ (M5,M6)
        │       │        │
        ▼       ▼        ▼
        domain/ (M1 types, M4 calculation)
```

Rules:

1. **Dependencies point inward only:** `main → ui → app → {input, output} → domain`. A module may import only from its own layer or the layers below it in this list.
2. **`domain/` imports nothing from the project except `domain/types`**, and nothing from outside except `decimal.js`. It never imports Node built-ins (`fs`, `readline`, `process`, …).
3. **`input/` and `output/` do not import each other.** Both depend only on `domain/types` (and `output/presentation` on `output/formatting`).
4. **Only `ui/` and `main` may touch I/O** (`node:*` modules, `process`, `console`).
5. **`ui/` talks to the core only through `app/`.** It never calls validation, calculation or formatting directly.
6. **No circular dependencies**, including within a layer. Inside a layer the allowed order is `parsing → validation` (M3 uses M2) and `formatting → presentation` (M6 uses M5). The reverse is never allowed.
7. **Enforcement:** `tests/architecture.test.ts` reads every `import` in `src/`, checks it against an allow-list per layer, and runs a cycle check. A violation fails `npm test`.

---

## 5. Data Model

V1 is **stateless**. There is no database, no file storage, no configuration file and no global mutable state. All data exists only in memory for the length of one calculation and flows in one direction:

| Stage | Type | Held by | Lifetime |
|---|---|---|---|
| User keystrokes | `string` | M8 local variables | Until the user answers a prompt |
| Raw request | `RawLoanInput` | Passed to M7 | One call to `runCalculator` |
| Parsed numbers | `ParseResult` | M3 locals | Inside `validateLoanInput` |
| Valid request | `LoanInput` (`Decimal` values) | Passed from M3 to M4 | One call |
| Intermediate values (`n`, `r`, `M`, balance `B`) | `Decimal`, full precision (40 significant digits) | M4 locals | Inside `calculateMortgage`, never exposed |
| Result | `MortgageResult` (cents-rounded `Decimal`s) | Passed from M4 to M6 | One call |
| Display model | `ResultView` / `ErrorView` (`string`s) | Returned by M7 to M8 | Until printed |

**Constants (read-only, in code):** `V1_RULES` (input limits, M3), English labels and messages (M6), months per year = 12 and Decimal precision/rounding (M4).

**Monetary representation:** every money value and rate is a `Decimal`, never a JS `number`. The term in years and `numberOfPayments` are plain integers.

---

## 6. Architectural Decision Records

### ADR-1 — Platform: interactive command-line application (resolves OQ-1)
- **Decision:** V1 ships as an interactive Node.js CLI that prompts for the three inputs and prints results or per-field errors.
- **Reason:** It is the smallest UI that meets FR-1–FR-3, needs no build or hosting, and is easy to test end-to-end through the injectable `TerminalIo` port. The UI-independent core (M1–M7) means a richer UI can be added later as just another adapter.
- **Alternative considered:** a static web page (Vite + HTML form). It was rejected for V1 because it adds a bundler, DOM testing and hosting for no functional gain. It remains the intended next adapter (`ui/web`).

### ADR-2 — Language and runtime: TypeScript on Node.js
- **Decision:** Write V1 in strict TypeScript on Node.js 24 LTS, tested with Vitest.
- **Reason:** Typed interfaces document the module contracts, and the same core can later run unchanged in a browser for a web UI.
- **Alternative considered:** Python 3.12 + pytest with the standard-library `decimal` module. It is an equally good choice for the arithmetic, but it would need a second language or a separate server to reach a future web front-end.

### ADR-3 — Exact decimal arithmetic with decimal.js
- **Decision:** All money and rate calculations use `decimal.js` with 40 significant digits and `ROUND_HALF_UP`, in a private Decimal clone inside M4.
- **Reason:** Section 4.3 requires full intermediate precision and true round half up. Binary floats cannot represent values such as 2.345 or 1.005 exactly, so they would round them incorrectly (e.g. `Math.round(1.005 * 100) / 100 === 1`).
- **Alternatives considered:** (a) native `number`, rejected because of the rounding errors above. (b) Integer cents, rejected because intermediate values would be rounded to cents, which violates section 4.3. (c) `big.js`, which is smaller, but `decimal.js` offers per-instance configuration (`Decimal.clone`) and a wider set of maths functions for future features such as APR solving.

### ADR-4 — Custom money formatter instead of `Intl.NumberFormat`
- **Decision:** M5 builds the `1 234,57 €` string itself, with ordinary spaces.
- **Reason:** `Intl.NumberFormat('sk-SK', …)` outputs non-breaking or narrow non-breaking spaces depending on the ICU version. That makes exact-string test assertions fragile across Node versions, and it works on floats rather than `Decimal`.
- **Alternative considered:** `Intl.NumberFormat` with post-processing to replace the special spaces. It was rejected as more fragile than the roughly 15-line formatter.

### ADR-5 — Validation returns error codes; texts live in presentation
- **Decision:** M3 returns `{ field, code }` pairs. M6 maps them to English sentences.
- **Reason:** It keeps validation free of wording, lets tests assert on stable codes, and keeps all user-facing language in one module (section 3.5), ready for future localisation.
- **Alternative considered:** M3 returns finished English messages. That is simpler, but it mixes rule logic with UI text and would force validation changes for any wording or language change.

### ADR-6 — Final payment via full-precision balance run
- **Decision:** M4 computes the final payment by running the balance forward month by month in full precision (section 4.4), not with a closed-form shortcut.
- **Reason:** It follows the specification literally, so the balance ends at exactly €0.00 for every rate including 0 %. The same loop is the natural seed for the out-of-scope repayment schedule, extra payments and variable rates.
- **Alternative considered:** a closed-form remaining-balance formula `B_{n−1} = P(1+r)^{n−1} − M_rounded·((1+r)^{n−1} − 1)/r`. It is faster (360 iterations are negligible), but it needs a separate r = 0 branch and is harder to extend.

### ADR-7 — Dependency rules enforced by a test, not a linter plugin
- **Decision:** A Vitest test (`tests/architecture.test.ts`) parses imports and fails on forbidden directions or cycles.
- **Reason:** It needs no extra dev dependency, runs with the normal `npm test`, and the rules are short enough to state in about 40 lines of code.
- **Alternative considered:** `dependency-cruiser` or `eslint-plugin-boundaries`. Both are more powerful, but they add tooling and configuration that a 9-module project does not need.

### ADR-8 — Pure, synchronous core with I/O behind a port
- **Decision:** M1–M7 are pure, synchronous functions. All terminal access goes through the `TerminalIo` interface in M8.
- **Reason:** Pure functions can be unit-tested with plain input/output assertions, and the CLI can be tested end-to-end with a fake `TerminalIo` that scripts answers and captures printed lines.
- **Alternative considered:** calling `readline`/`console.log` directly inside the calculator flow. It was rejected because it couples logic to the terminal and blocks UI replacement.

---

## 7. Test Strategy (summary)

| Module | Test focus |
|---|---|
| M2 parsing | Separators `.`/`,`, inner spaces, trimming, multiple separators → `not_a_number`, `writtenDecimals` counts |
| M3 validation | Every error code per field, inclusive boundaries (min, max, just outside), all errors reported at once |
| M4 calculation | Reference values from known annuity examples, r = 0 case, final-payment rounding absorption, invariants (section 3, M4) |
| M5 formatting | `0 → "0,00 €"`, `1234.565 → "1 234,57 €"`, `1000000 → "1 000 000,00 €"` |
| M6 presentation | Final payment shown only when it differs by ≥ €0.01; output order; one message per error code |
| M7 calculator | Calculation is never invoked for invalid input |
| M8 cli | Scripted `TerminalIo`: happy path, re-prompt only invalid fields, closed stream → exit code 1 |
| Architecture | Dependency rules and no cycles (section 4) |

Run all tests with **`npm test`**.

# 05 — Execution Plan (V1)

Status: **Final** (2026-10-21)

Sources: [`01-functional.md`](01-functional.md) (requirements, revised after review), [`02-architecture.md`](02-architecture.md) (modules M1–M9, ADR-1 to ADR-10), [`03-test-scenarios.md`](03-test-scenarios.md) (tests 1–112), [`04-review.md`](04-review.md) (findings #1–#6 resolved, #7–#24 open).

This plan closes **Part A (Planning)**. **Part B (Build V1)** starts with Step 1 below.

---

## 1. V1 Goals

Each goal is a yes/no check that can be verified by running a command.

| # | Goal | How it is checked | Pass when |
|---|---|---|---|
| G1 | **All 112 test scenarios pass.** | `npm test` | Vitest reports **112 passed, 0 failed, 0 skipped**. The 112 `it()` names match section 2 exactly, with no extra and no missing names. |
| G2 | **Clean run on Node.js 24 LTS.** | `node --version`, `npm run typecheck`, `npm start` | Node is `v24.x`, `tsc --noEmit` reports 0 errors, and the CLI completes a calculation interactively. |
| G3 | **Only one runtime dependency, and no UI dependencies.** | `package.json` | `dependencies` contains exactly one entry, `decimal.js`. Everything else (`typescript`, `vitest`, `tsx`, `@types/node`) is in `devDependencies`. |
| G4 | **The architecture rules hold.** | `tests/architecture.test.ts` (tests 93–95) | There are no forbidden imports and no import cycles, and `src/domain/**` performs no I/O. |

---

## 2. Final Scope & Acceptance Criteria

### 2.1 Scope

- **In scope:** everything in 01 (FR-1, FR-2, FR-3, sections 3–4), as designed in 02 and tested in 03, including the review resolutions:
  - early termination and the sub-half-cent tail rule (01 §4.4),
  - the strict number grammar (01 §3.2),
  - the line-queue terminal reader (02 M8, ADR-10).
- **Out of scope:** everything in 01 section 5. For extra payments and variable rates, the extension friction is accepted (02 ADR-9).
- **Open Minor findings (04 #7–#24):** no extra behaviour is built for them. Where a test in 03 fixes the behaviour (e.g. test 35 for `"10,0"`, the "Expected UI texts" section), the test is binding. Where nothing fixes it (e.g. `-0`, #9; NBSP, #12), the implementation follows the literal text of 01/02, and the case is noted in `docs/handoff.md`. Decisions on these findings do not block the build.

### 2.2 Tests that MUST pass

All 112 tests from 03. The **Test name** is the exact string passed to `it('<name>', …)`. The **Step** is the build step in section 3 that introduces the test.

| # | Test name | Level | Module / Requirement | Step |
|---|---|---|---|---|
| 1 | `test_parse_dot_decimal_separator` | unit | parsing (M2) / FR-3 | 2 |
| 2 | `test_parse_comma_decimal_separator` | unit | parsing (M2) / FR-3 | 2 |
| 3 | `test_parse_spaces_as_thousands_separator` | unit | parsing (M2) / FR-3 | 2 |
| 4 | `test_parse_integer_without_separator` | unit | parsing (M2) / FR-3 | 2 |
| 5 | `test_parse_trims_leading_trailing_whitespace` | unit | parsing (M2) / FR-3 | 2 |
| 6 | `test_parse_counts_written_trailing_zeros` | unit | parsing (M2) / FR-3 | 2 |
| 7 | `test_parse_negative_number_is_parsed` | unit | parsing (M2) / FR-3 | 2 |
| 8 | `test_parse_empty_string` | unit | parsing (M2) / FR-3 | 2 |
| 9 | `test_parse_whitespace_only` | unit | parsing (M2) / FR-3 | 2 |
| 10 | `test_parse_undefined_input` | unit | parsing (M2) / FR-3 | 2 |
| 11 | `test_parse_text_string` | unit | parsing (M2) / FR-3 | 2 |
| 12 | `test_parse_mixed_separators_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 13 | `test_parse_multiple_dots_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 14 | `test_parse_multiple_commas_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 15 | `test_parse_currency_symbol_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 16 | `test_parse_scientific_notation_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 17 | `test_validate_all_valid_inputs` | unit | validation (M3) / FR-3 | 3 |
| 18 | `test_validate_loan_min_inclusive` | unit | validation (M3) / FR-3 | 3 |
| 19 | `test_validate_loan_max_inclusive` | unit | validation (M3) / FR-3 | 3 |
| 20 | `test_validate_loan_below_min` | unit | validation (M3) / FR-3 | 3 |
| 21 | `test_validate_loan_above_max` | unit | validation (M3) / FR-3 | 3 |
| 22 | `test_validate_loan_negative` | unit | validation (M3) / FR-3 | 3 |
| 23 | `test_validate_loan_too_many_decimals` | unit | validation (M3) / FR-3 | 3 |
| 24 | `test_validate_loan_written_trailing_zero_decimals` | unit | validation (M3) / FR-3 | 3 |
| 25 | `test_validate_rate_zero_inclusive` | unit | validation (M3) / FR-3 | 3 |
| 26 | `test_validate_rate_max_inclusive` | unit | validation (M3) / FR-3 | 3 |
| 27 | `test_validate_rate_above_max` | unit | validation (M3) / FR-3 | 3 |
| 28 | `test_validate_rate_negative` | unit | validation (M3) / FR-3 | 3 |
| 29 | `test_validate_rate_too_many_decimals` | unit | validation (M3) / FR-3 | 3 |
| 30 | `test_validate_term_min_inclusive` | unit | validation (M3) / FR-3 | 3 |
| 31 | `test_validate_term_max_inclusive` | unit | validation (M3) / FR-3 | 3 |
| 32 | `test_validate_term_zero` | unit | validation (M3) / FR-3 | 3 |
| 33 | `test_validate_term_above_max` | unit | validation (M3) / FR-3 | 3 |
| 34 | `test_validate_term_fractional` | unit | validation (M3) / FR-3 | 3 |
| 35 | `test_validate_term_with_zero_decimal` | unit | validation (M3) / FR-3 | 3 |
| 36 | `test_validate_term_text` | unit | validation (M3) / FR-3 | 3 |
| 37 | `test_validate_missing_field` | unit | validation (M3) / FR-3 | 3 |
| 38 | `test_validate_all_fields_empty` | unit | validation (M3) / FR-3 | 3 |
| 39 | `test_validate_multiple_invalid_fields` | unit | validation (M3) / FR-3 | 3 |
| 40 | `test_validate_one_error_per_field` | unit | validation (M3) / FR-3 | 3 |
| 41 | `test_round_to_cents_exact_half_rounds_up` | unit | calculation (M4) / FR-1 | 4 |
| 42 | `test_round_to_cents_below_half_rounds_down` | unit | calculation (M4) / FR-1 | 4 |
| 43 | `test_annuity_standard_rate_30y` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 44 | `test_annuity_standard_rate_25y` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 45 | `test_annuity_payment_rounded_up_final_lower` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 46 | `test_annuity_non_round_loan_amount` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 47 | `test_annuity_final_equals_regular` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 48 | `test_annuity_final_differs_by_one_cent` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 49 | `test_annuity_one_year_term` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 50 | `test_annuity_min_loan_min_positive_rate` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 51 | `test_annuity_max_loan_max_rate_30y` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 52 | `test_annuity_min_loan_max_rate_30y` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 53 | `test_annuity_just_above_half_cent` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 54 | `test_annuity_just_below_half_cent` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 55 | `test_zero_rate_exact_division` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 56 | `test_zero_rate_rounding_absorbed_by_final` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 57 | `test_zero_rate_30y_final_lower` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 58 | `test_zero_rate_max_loan_30y` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 59 | `test_zero_rate_exact_half_cent_rounds_up` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 60 | `test_calculation_invariants_hold` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 61 | `test_calculation_leaves_global_decimal_config_unchanged` | unit | calculation (M4) / FR-1 | 4 |
| 62 | `test_format_money_thousands_separator` | unit | formatting (M5) / FR-1, FR-2 | 5 |
| 63 | `test_format_money_below_thousand` | unit | formatting (M5) / FR-1, FR-2 | 5 |
| 64 | `test_format_money_millions` | unit | formatting (M5) / FR-1, FR-2 | 5 |
| 65 | `test_format_money_pads_two_decimals` | unit | formatting (M5) / FR-1, FR-2 | 5 |
| 66 | `test_format_money_zero` | unit | formatting (M5) / FR-2 | 5 |
| 67 | `test_format_money_rounds_half_up` | unit | formatting (M5) / FR-1 | 5 |
| 68 | `test_format_money_uses_ascii_spaces_only` | unit | formatting (M5) / FR-1 | 5 |
| 69 | `test_show_final_payment_when_one_cent_different` | unit | presentation (M6) / FR-1 | 6 |
| 70 | `test_hide_final_payment_when_equal` | unit | presentation (M6) / FR-1 | 6 |
| 71 | `test_show_final_payment_when_lower` | unit | presentation (M6) / FR-1 | 6 |
| 72 | `test_result_view_with_final_payment` | unit | presentation (M6) / FR-1, FR-2 | 6 |
| 73 | `test_result_view_without_final_payment` | unit | presentation (M6) / FR-1, FR-2 | 6 |
| 74 | `test_error_view_required_message` | unit | presentation (M6) / FR-3 | 6 |
| 75 | `test_error_view_not_a_number_message` | unit | presentation (M6) / FR-3 | 6 |
| 76 | `test_error_view_negative_message` | unit | presentation (M6) / FR-3 | 6 |
| 77 | `test_error_view_range_messages` | unit | presentation (M6) / FR-3 | 6 |
| 78 | `test_error_view_decimal_messages` | unit | presentation (M6) / FR-3 | 6 |
| 79 | `test_error_view_one_message_per_field_in_field_order` | unit | presentation (M6) / FR-3 | 6 |
| 80 | `test_calculator_valid_input_returns_result` | functional | calculator (M7) / FR-1, FR-2, FR-3 | 7 |
| 81 | `test_calculator_zero_rate_full_flow` | functional | calculator (M7) / FR-1, FR-2 | 7 |
| 82 | `test_calculator_invalid_input_skips_calculation` | functional | calculator (M7) / FR-3 | 7 |
| 83 | `test_calculator_partial_invalid_returns_no_results` | functional | calculator (M7) / FR-3 | 7 |
| 84 | `test_calculator_all_missing` | functional | calculator (M7) / FR-3 | 7 |
| 85 | `test_cli_prompts_in_order` | functional | cli (M8) / FR-3 | 8 |
| 86 | `test_cli_prints_results_and_exits_zero` | functional | cli (M8) / FR-1, FR-2 | 8 |
| 87 | `test_cli_reprompts_only_invalid_fields` | functional | cli (M8) / FR-3 | 8 |
| 88 | `test_cli_closed_input_exits_one` | functional | cli (M8) / FR-3 | 8 |
| 89 | `test_e2e_cli_standard_mortgage` | e2e | main + cli → all modules / FR-1, FR-2, FR-3 | 9 |
| 90 | `test_e2e_cli_zero_rate_hides_final_payment` | e2e | main + cli → all modules / FR-1, FR-2 | 9 |
| 91 | `test_e2e_cli_invalid_then_corrected_input` | e2e | main + cli → all modules / FR-1, FR-2, FR-3 | 9 |
| 92 | `test_e2e_cli_input_closed_early` | e2e | main + cli → all modules / FR-3 | 9 |
| 93 | `test_architecture_dependency_direction` | unit | all modules (02 §4) / — | 1 |
| 94 | `test_architecture_domain_has_no_io` | unit | calculation (M4), types (M1) / FR-1, FR-2 | 1 |
| 95 | `test_architecture_no_circular_dependencies` | unit | all modules (02 §4) / — | 1 |
| 96 | `test_parse_hex_binary_octal_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 97 | `test_parse_nan_and_infinity_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 98 | `test_parse_exponent_variants_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 99 | `test_parse_separator_without_digits_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 100 | `test_parse_sign_other_than_leading_minus_rejected` | unit | parsing (M2) / FR-3 | 2 |
| 101 | `test_validate_hex_loan_amount_rejected` | unit | validation (M3) / FR-3 | 3 |
| 102 | `test_early_termination_rounded_up_payment` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 103 | `test_early_termination_largest_overpayment` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 104 | `test_early_termination_round_loan_amount` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 105 | `test_early_termination_one_month_early_low_rate` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 106 | `test_early_termination_remainder_rounds_to_zero` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 107 | `test_full_term_final_far_below_regular` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 108 | `test_calculation_invariants_property_sweep` | unit | calculation (M4) / FR-1, FR-2 | 4 |
| 109 | `test_calculator_early_termination_equal_final_hidden` | functional | calculator (M7) / FR-1, FR-2 | 7 |
| 110 | `test_e2e_cli_early_termination` | e2e | main + cli → all modules / FR-1, FR-2 | 9 |
| 111 | `test_node_terminal_io_answers_all_piped_lines` | functional | cli (M8) / FR-3 | 8 |
| 112 | `test_node_terminal_io_pending_ask_resolves_at_eof` | functional | cli (M8) / FR-3 | 8 |

### 2.3 Technical acceptance criteria

| # | Criterion | Command / check |
|---|---|---|
| AC-1 | All tests pass, with 0 failures and 0 skipped. | `npm test` (runs `vitest run`) |
| AC-2 | The type-check is clean under `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` and `module: NodeNext`. | `npm run typecheck` |
| AC-3 | The CLI runs interactively, prompts for the three inputs with no defaults, prints the results, and exits with code 0. | `npm start` |
| AC-4 | The CLI works with piped input and reports end of input with exit code 1. | `printf '100 000\n3,5\n30\n' \| npx tsx src/main.ts` → the 4 result lines of test 89, exit 0. `printf '100000\n' \| npx tsx src/main.ts` → no result lines, exit 1. |
| AC-5 | Money and rates are never JS `number`s. Only `termYears` and `numberOfPayments` are integers. | Code review of `src/`, plus the `Decimal` types in M1 |
| AC-6 | Every commit leaves the repository green: AC-1 and AC-2 pass at each step's commit. | `git log`, re-run per step |
| AC-7 | `docs/handoff.md` and `docs/v1/prompts.md` are current at every commit (CLAUDE.md). | Review |

---

## 3. Implementation Order

The modules are built in strict dependency order. Every module depends only on modules from earlier steps (02 §4). Each step is test-first: write that step's tests from 03, see them fail, implement the module, and see them pass.

| Step | Module to build | File(s) | Depends on | Test IDs (03) | Tests added / cumulative | Commit message |
|---|---|---|---|---|---|---|
| 1 | **Types (M1)**, plus project scaffold and the architecture guard | `package.json`, `tsconfig.json`, `vitest.config.ts`, `src/domain/types.ts`, `tests/architecture.test.ts` | — | 93, 94, 95 | 3 / 3 | `feat: scaffold project and add domain types with architecture guard (M1)` |
| 2 | **Parsing (M2)** | `src/input/parsing.ts`, `tests/input/parsing.test.ts` | M1 | 1–16, 96–100 | 21 / 24 | `feat: add strict number parsing (M2)` |
| 3 | **Validation (M3)** | `src/input/validation.ts`, `tests/input/validation.test.ts` | M1, M2 | 17–40, 101 | 25 / 49 | `feat: add input validation (M3)` |
| 4 | **Calculation (M4)** | `src/domain/calculation.ts`, `tests/domain/calculation.test.ts` | M1 | 41–61, 102–108 | 28 / 77 | `feat: add mortgage calculation with early termination (M4)` |
| 5 | **Formatting (M5)** | `src/output/formatting.ts`, `tests/output/formatting.test.ts` | — (`decimal.js` only) | 62–68 | 7 / 84 | `feat: add money formatting (M5)` |
| 6 | **Presentation (M6)** | `src/output/presentation.ts`, `tests/output/presentation.test.ts` | M1, M5 | 69–79 | 11 / 95 | `feat: add result and error presentation (M6)` |
| 7 | **Calculator Facade (M7)** | `src/app/calculator.ts`, `tests/app/calculator.test.ts` | M1, M3, M4, M6 | 80–84, 109 | 6 / 101 | `feat: add calculator use case (M7)` |
| 8 | **CLI Terminal Adapter (M8)** | `src/ui/cli.ts`, `tests/ui/cli.test.ts` | M1, M7 | 85–88, 111, 112 | 6 / 107 | `feat: add CLI adapter with line-queue terminal reader (M8)` |
| 9 | **Main Entrypoint (M9)** | `src/main.ts`, `tests/e2e/cli.e2e.test.ts` | M8 | 89–92, 110 | 5 / 112 | `feat: add main entry point and end-to-end tests (M9)` |

Notes per step:

- **Step 1.** The scaffold sets up `npm test` (`vitest run`), `npm start` (`tsx src/main.ts`) and `npm run typecheck` (`tsc --noEmit`), plus the TypeScript settings from 02 §1. M1 contains types only, so its correctness is checked by the type-check and by later steps. The architecture tests come first so that every later step is checked against the dependency rules from the start. Before Step 9, `npm start` has no `src/main.ts` to run. That is expected, and AC-3 is first checked in Step 9.
- **Step 2.** `NUMBER_PATTERN` (01 §3.2) runs **before** `new Decimal()` (tests 16, 96–100).
- **Step 4.**
  - M4 uses a private `Decimal.clone({ precision: 40, rounding: ROUND_HALF_UP })` (test 61).
  - The balance run implements the amount-due loop with early termination, plus the rule that a final payment rounding to €0.00 moves the end to the previous month (tests 102–107).
  - Test 108 is the property sweep over 6 800 inputs.
  - Tests 43–59 must keep the values verified in 04.
- **Step 5.** `formatMoney` rounds half up with an **explicit** rounding mode, never decimal.js's global default (see 04 #16).
- **Step 7.** Tests 82–83 assert that `calculateMortgage` is never called for invalid input (see the risks for how to spy on it with ES modules).
- **Step 8.** `createNodeTerminalIo(input?, output?)` is the line queue from 02 M8 / ADR-10. Tests 111–112 drive it with in-memory `PassThrough` streams.
- **Step 9.** The e2e tests spawn the real program with piped stdin (tests 89–92, 110). AC-3 and AC-4 are checked by hand and recorded in the handoff.

---

## 4. Definition of Done (per step)

A step is done only when **all** of the following are true:

1. **The step's tests exist and pass.** All test IDs listed for the step in section 3 are written with the exact names from section 2.2, and they pass.
2. **All earlier tests still pass.** `npm test` passes with the cumulative count from section 3 (e.g. 49 after Step 3) and 0 failures. No test is skipped, marked `.todo`, or weakened, and no expected value from 03 is changed.
3. **The type-check is clean.** `npm run typecheck` reports 0 errors.
4. **The architecture guard is green.** Tests 93–95 pass (they are included in item 2, but they are listed here because they guard every new import).
5. **`docs/handoff.md` is updated.** It records the current step, the cumulative test count, any deviations or newly found ambiguities, and the next step. The step's prompt is logged in `docs/v1/prompts.md` (CLAUDE.md).
6. **Exactly one git commit is made**, with the commit message from section 3. It contains the module, its tests and the documentation updates.

If an expected value in 03 seems wrong during a step, the value is **not** changed in the code or the test. The step stops, and the case goes back to the author (see section 6.3).

---

## 5. Execution Tooling

| Concern | Tool / strategy |
|---|---|
| Runtime | Node.js 24 LTS |
| Language | TypeScript 5, strict mode (02 §1) |
| Decimal arithmetic | `decimal.js`, the only runtime dependency. M4 uses a private clone with 40 significant digits and `ROUND_HALF_UP` (ADR-3). |
| **Test runner** | **Vitest** (`npm test` → `vitest run`). One `*.test.ts` per module under `tests/`, mirroring `src/`, plus `tests/architecture.test.ts` and `tests/e2e/`. |
| Development runner | `tsx` (`npm start` → `tsx src/main.ts`), so no build step is needed. |
| Type-check | `tsc --noEmit` (`npm run typecheck`) |
| **CLI stdin strategy** | **Event-driven line queue** (02 M8, ADR-10). One `node:readline` interface subscribes to `line` and `close` at creation. Lines go into a FIFO queue. `ask()` writes the prompt and resolves from the queue, or waits as a single pending resolver. On `close` (EOF), the pending `ask` and every later `ask` resolve to `undefined`, and the CLI exits with code 1. Sequential `readline/promises` `question()` calls are **not** used: they lose piped lines and hang at EOF (verified, 04 #2). |
| CLI test doubles | A scripted fake `TerminalIo` (tests 85–88) and in-memory `PassThrough` streams (tests 111–112). |
| E2E | Spawn `src/main.ts` through `tsx` as a child process with piped stdin/stdout, and assert on stdout and the exit code (tests 89–92, 110). |
| Reference values | REF-PY (03 Appendix A, full-term loans), REF-ET (03 Appendix B, early termination), and the exact-rational audit scripts (04 Appendix). |

---

## 6. Risks & Contingencies

### 6.1 Review findings already addressed in the specs

| Finding | Risk it addressed | Resolution now in the specs | Verified by |
|---|---|---|---|
| 04 #1 — **early payoff rule** | Valid inputs produced a negative final payment (e.g. P = 1 000.29, 20 %, 30 y → −97.42). | 01 §4.4 step 2: if the amount due D = B·(1 + r) ≤ M_rounded before month n, that month is the last. The Final Payment is D rounded to cents, and the remaining months are skipped. P = 1 000.29 now ends at month 354 with a Final Payment of 8.08. | Tests 102–105, 108–110 (REF-ET) |
| 04 #1 — **sub-half-cent rounding tail rule** | When the amount due in the last month is below €0.005, the Final Payment would round to €0.00, which breaks "Final > 0". | 01 §4.4 step 3: the payment of the previous month (M_rounded) becomes the Final Payment, and the loan ends one month earlier. Example: P = 1 075.15, 20 %, 30 y → 355 payments of 17.97, and the Final Payment line is hidden. | Tests 106, 109 |
| 04 #2 — **non-blocking stream reader for CLI** | Piped stdin lost lines, and EOF left a promise unsettled (exit 13 instead of 1). | 02 M8 / ADR-10: event-driven line queue. A prototype was verified on Node 24.20.0 with piped input, CRLF and EOF. | Tests 88, 89–92, 110, 111–112 |
| 04 #3 — strict number grammar | decimal.js accepts `0x3E8`, `1e5`, `NaN` and `Infinity`. | 01 §3.2: `^-?[0-9]+([.,][0-9]+)?$` is checked before decimal.js. | Tests 16, 96–101 |
| 04 #4 — invariant coverage | Invariants were checked only on hand-picked inputs. | Property sweep over 6 800 inputs. "Final ≤ Regular" is asserted only for early-terminated loans. | Test 108 |
| 04 #5, #6 — extension friction | Extra payments and variable rates would change 5–6 modules. | Accepted trade-off (ADR-9). V2 variable rates will get a dedicated schedule module. | — (out of scope) |

### 6.2 Implementation risks

| Risk | Likelihood | Contingency |
|---|---|---|
| **ES module spying (tests 82–83).** `vi.spyOn` cannot replace an export of an ES module namespace, so the "called 0 times" assertion may not be wired correctly. | Medium | Use a partial module mock: `vi.mock('../../src/domain/calculation', async (importOriginal) => { const mod = await importOriginal<typeof import('../../src/domain/calculation')>(); return { ...mod, calculateMortgage: vi.fn(mod.calculateMortgage) }; })`, and assert on the mock. Do not change M7's interface just to make it testable. |
| **Runtime of the property sweep (test 108).** 6 800 inputs × up to 360 decimal.js iterations at 40 digits may take seconds. | Medium | Measure it in Step 4. If it exceeds Vitest's default timeout, raise the timeout for test 108 only (e.g. `{ timeout: 60_000 }`). The input domain is not reduced without the author's approval, because it is part of the 03 contract. |
| **Spawning on Windows (e2e).** `npx` is `npx.cmd` on Windows, so `spawn('npx', …)` fails without a shell. | High on this machine | Spawn `process.execPath` with `['--import', 'tsx', 'src/main.ts']`. This is equivalent to `npx tsx src/main.ts` and works on every OS. |
| **Line endings.** Piped input on Windows may contain CRLF. | Low | `node:readline` already strips `\r\n` (checked in the M8 prototype). Test 111 can add a CRLF variant if it is ever needed. |
| **Global Decimal configuration.** decimal.js `toFixed()` without a rounding mode uses the global `Decimal.rounding`, which test 61 changes. | Medium | M5 passes `Decimal.ROUND_HALF_UP` explicitly. Vitest isolates test files, but M5 must not rely on that. |
| **Duplicated limits in messages (04 #17).** The range texts in M6 duplicate `V1_RULES`. | Low (V1 has a single rules table) | Accept this for V1. A code comment in M6 points to `V1_RULES`. |

### 6.3 Unconfirmed points and escalation

- **Sub-half-cent tail rule (01 §4.4 step 3).** It was added while resolving finding #1, because it is needed to keep "Final > 0". Tests 106 and 109 depend on it. If the author rejects it, only those two tests and the step 3 text change.
- **Number of payments is not displayed.** When a loan ends early, V1 shows no month count (`MortgageResult.numberOfPayments` is computed but not shown). This is listed in the handoff as an open question. Adding it would be a new output and a change to the requirements, so it is not part of this plan.
- **Escalation rule.** If any expected value or spec rule turns out to be wrong or ambiguous during Part B, stop the current step, record the case in `docs/handoff.md`, and ask the author. Do not adjust tests to fit the code.

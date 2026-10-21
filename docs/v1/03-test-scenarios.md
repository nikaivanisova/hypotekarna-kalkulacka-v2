# 03 — Test Scenarios (V1)

Status: **Proposed** (2026-10-21). Revised 2026-10-21 after the independent review ([`04-review.md`](04-review.md) findings #1–#4): tests 96–112 added (strict number grammar, early termination, property-based invariant sweep, stream-based terminal reader). Existing test numbers are unchanged.

Sources: [`01-functional.md`](01-functional.md) (FR-1, FR-2, FR-3; sections 3–4) and [`02-architecture.md`](02-architecture.md) (modules M1–M9).

## How to read this document

- **Test Name** is the exact name to use in code: `it('<name>', …)` in the Vitest file for that module (e.g. `tests/domain/calculation.test.ts`).
- **Levels:**
  - *unit*: one module in isolation.
  - *functional*: `app/calculator` or `ui/cli` with a fake `TerminalIo`, with no process spawned.
  - *e2e*: the real program `npx tsx src/main.ts`, spawned as a child process with piped stdin/stdout.
- **Money notation:**
  - Unit-level calculation results are `Decimal` values written as `449.04`.
  - Display-level values are exact strings written as `449,04 €` (ASCII spaces, see section 3.4 of 01-functional.md).
- **Calculation outputs** are listed as *Regular / Final / Total Paid / Interest*. All are cents-rounded (round half up).
- **Inputs** for calculation tests are `P` (loan amount in €), `rate` (annual %) and `term` (years). For parsing, validation and UI tests, inputs are the raw strings the user types.

### Reference sources

| ID | Source |
|---|---|
| **REF-PY** | Independent reference script in Python 3.14 using the standard-library `decimal` module (60 significant digits, `ROUND_HALF_UP`). It implements sections 4.1–4.5 with the month-by-month balance run, and checks every final payment against the closed-form remaining balance `B = P(1+r)^(n−1) − M·((1+r)^(n−1) − 1)/r` (both must round to the same cent). The script is in Appendix A. |
| **REF-PMT** | Second, independent check in a different language: a float implementation of the PMT formula `M = P·r / (1 − (1+r)^−n)` plus the balance run in Node.js. It agreed with REF-PY on every regular payment (to 9 decimals) and on every final payment after rounding. The same regular payment can be checked in any spreadsheet with `=ROUND(PMT(rate/1200; term*12; -P); 2)`. |
| **REF-ET** | Reference script for the revised section 4.4 (early termination) in Python using exact rational arithmetic (`fractions.Fraction`, no precision limit, round half up). It runs the month-by-month amount due `D = B·(1+r)`, stops at month n or when `D ≤ M_rounded`, and applies the "rounds to €0.00" rule. It reproduces every value of tests 43–59 and 91 unchanged, because none of those loans ends early, and it is the only source for tests 102–110. REF-PY's closed-form cross-check assumes a full term, so REF-PY does not apply to early-terminated loans. The script is in Appendix B. |
| **MANUAL** | Hand calculation shown in the cell (simple arithmetic or a direct reading of a spec rule). |
| **SPEC §x** | The expected result follows directly from the cited section of `01-functional.md` or `02-architecture.md`. |

> **Note on the example in the Layer 3 prompt.** The prompt's example (P = 100 000, 3.5 %, 30 y → Final 449.04, Total Paid 161 654.40) leaves the loan **under-repaid by €2.98**. The regular payment is rounded *down* (449.0447 → 449.04) 359 times, and that shortfall gathers interest. Section 4.4 says the final payment absorbs the difference, so the correct values are **Final 452.02, Total Paid 161 657.38, Interest 61 657.38** (REF-PY and REF-PMT agree). The table uses the corrected values.

### Expected UI texts (test contract for M6 and M8)

These strings were not fixed in 01/02. This document defines them, and the presentation (M6) and CLI (M8) tests assert them exactly.

| Kind | Exact text |
|---|---|
| Field labels | `Loan amount`, `Annual interest rate`, `Term` |
| CLI prompts | `Loan amount (EUR): `, `Annual interest rate (%): `, `Term (years): ` |
| Result line format | `<label>: <money>`. The labels are `Regular Monthly Payment`, `Final Payment`, `Total Paid`, `Total Interest`. |
| `required` | `<Label> is required.` |
| `not_a_number` | `<Label> must be a number.` |
| `negative` | `<Label> must not be negative.` |
| `below_min` / `above_max` | Loan amount: `Loan amount must be between 1 000,00 € and 1 000 000,00 €.` Rate: `Annual interest rate must be between 0,00 % and 20,00 %.` Term: `Term must be between 1 and 30 years.` |
| `too_many_decimals` | Loan amount / rate: `<Label> can have at most 2 decimal places.` Term: `Term must be a whole number of years.` |
| `not_whole_number` | `Term must be a whole number of years.` |

---

## Test Scenarios

| # | Test Name | Level | Module & Implemented Requirement | Input & Expected Output | Reference Source | Type |
|---|---|---|---|---|---|---|
| 1 | `test_parse_dot_decimal_separator` | unit | parsing (M2) / FR-3 | `"1000.50"` → ok, value `1000.5`, writtenDecimals `2` | SPEC §3.2 | happy path |
| 2 | `test_parse_comma_decimal_separator` | unit | parsing (M2) / FR-3 | `"1000,50"` → ok, value `1000.5`, writtenDecimals `2` | SPEC §3.2 | happy path |
| 3 | `test_parse_spaces_as_thousands_separator` | unit | parsing (M2) / FR-3 | `"1 000 000,50"` → ok, value `1000000.5`, writtenDecimals `2` | SPEC §3.2 | happy path |
| 4 | `test_parse_integer_without_separator` | unit | parsing (M2) / FR-3 | `"30"` → ok, value `30`, writtenDecimals `0` | SPEC §3.2 | happy path |
| 5 | `test_parse_trims_leading_trailing_whitespace` | unit | parsing (M2) / FR-3 | `"  250000  "` → ok, value `250000`, writtenDecimals `0` | SPEC §3.2 | edge case |
| 6 | `test_parse_counts_written_trailing_zeros` | unit | parsing (M2) / FR-3 | `"1000,500"` → ok, value `1000.5`, writtenDecimals `3` (trailing zero counts) | SPEC §3.3, 02 M2 | edge case |
| 7 | `test_parse_negative_number_is_parsed` | unit | parsing (M2) / FR-3 | `"-5000"` → ok, value `-5000` (validation reports `negative`) | 02 M2 | edge case |
| 8 | `test_parse_empty_string` | unit | parsing (M2) / FR-3 | `""` → error `empty` | SPEC §3.3 | invalid input |
| 9 | `test_parse_whitespace_only` | unit | parsing (M2) / FR-3 | `"   "` → error `empty` | SPEC §3.2, §3.3 | invalid input |
| 10 | `test_parse_undefined_input` | unit | parsing (M2) / FR-3 | `undefined` → error `empty` | SPEC §3.3 | invalid input |
| 11 | `test_parse_text_string` | unit | parsing (M2) / FR-3 | `"abc"` → error `not_a_number` | SPEC §3.3 | invalid input |
| 12 | `test_parse_mixed_separators_rejected` | unit | parsing (M2) / FR-3 | `"1,000.50"` → error `not_a_number` | SPEC §3.3 (example) | invalid input |
| 13 | `test_parse_multiple_dots_rejected` | unit | parsing (M2) / FR-3 | `"1.000.50"` → error `not_a_number` | SPEC §3.2 | invalid input |
| 14 | `test_parse_multiple_commas_rejected` | unit | parsing (M2) / FR-3 | `"1,000,50"` → error `not_a_number` | SPEC §3.2 | invalid input |
| 15 | `test_parse_currency_symbol_rejected` | unit | parsing (M2) / FR-3 | `"1000 €"` → error `not_a_number` | SPEC §3.3 | invalid input |
| 16 | `test_parse_scientific_notation_rejected` | unit | parsing (M2) / FR-3 | `"1e5"` → error `not_a_number` (fails `NUMBER_PATTERN`: only digits, one separator, optional leading `-`) | SPEC §3.2 (strict grammar) | invalid input |
| 17 | `test_validate_all_valid_inputs` | unit | validation (M3) / FR-3 | loan `"100 000"`, rate `"3,5"`, term `"30"` → ok, principal `100000`, annualRatePercent `3.5`, termYears `30` | SPEC §3.1 | happy path |
| 18 | `test_validate_loan_min_inclusive` | unit | validation (M3) / FR-3 | loan `"1000"` (rate `"3"`, term `"10"`) → ok | SPEC §3.1 | edge case |
| 19 | `test_validate_loan_max_inclusive` | unit | validation (M3) / FR-3 | loan `"1 000 000,00"` (rate `"3"`, term `"10"`) → ok | SPEC §3.1 | edge case |
| 20 | `test_validate_loan_below_min` | unit | validation (M3) / FR-3 | loan `"999,99"` → errors `[{loanAmount, below_min}]` | SPEC §3.1 | invalid input |
| 21 | `test_validate_loan_above_max` | unit | validation (M3) / FR-3 | loan `"1000000,01"` → errors `[{loanAmount, above_max}]` | SPEC §3.1 | invalid input |
| 22 | `test_validate_loan_negative` | unit | validation (M3) / FR-3 | loan `"-100000"` → errors `[{loanAmount, negative}]` (not `below_min`) | SPEC §3.3, 02 M3 order | invalid input |
| 23 | `test_validate_loan_too_many_decimals` | unit | validation (M3) / FR-3 | loan `"100000,555"` → errors `[{loanAmount, too_many_decimals}]` | SPEC §3.1 | invalid input |
| 24 | `test_validate_loan_written_trailing_zero_decimals` | unit | validation (M3) / FR-3 | loan `"100000,500"` → errors `[{loanAmount, too_many_decimals}]` | SPEC §3.3 ("written with") | edge case |
| 25 | `test_validate_rate_zero_inclusive` | unit | validation (M3) / FR-3 | rate `"0"` (loan `"100000"`, term `"10"`) → ok, annualRatePercent `0` | SPEC §3.1 | edge case |
| 26 | `test_validate_rate_max_inclusive` | unit | validation (M3) / FR-3 | rate `"20,00"` (loan `"100000"`, term `"10"`) → ok, annualRatePercent `20` | SPEC §3.1 | edge case |
| 27 | `test_validate_rate_above_max` | unit | validation (M3) / FR-3 | rate `"20,01"` → errors `[{annualRate, above_max}]` | SPEC §3.1 | invalid input |
| 28 | `test_validate_rate_negative` | unit | validation (M3) / FR-3 | rate `"-0,5"` → errors `[{annualRate, negative}]` | SPEC §3.3 | invalid input |
| 29 | `test_validate_rate_too_many_decimals` | unit | validation (M3) / FR-3 | rate `"3,555"` → errors `[{annualRate, too_many_decimals}]` | SPEC §3.1 | invalid input |
| 30 | `test_validate_term_min_inclusive` | unit | validation (M3) / FR-3 | term `"1"` (loan `"100000"`, rate `"3"`) → ok, termYears `1` | SPEC §3.1 | edge case |
| 31 | `test_validate_term_max_inclusive` | unit | validation (M3) / FR-3 | term `"30"` (loan `"100000"`, rate `"3"`) → ok, termYears `30` | SPEC §3.1 | edge case |
| 32 | `test_validate_term_zero` | unit | validation (M3) / FR-3 | term `"0"` → errors `[{termYears, below_min}]` | SPEC §3.1 | invalid input |
| 33 | `test_validate_term_above_max` | unit | validation (M3) / FR-3 | term `"31"` → errors `[{termYears, above_max}]` | SPEC §3.1 | invalid input |
| 34 | `test_validate_term_fractional` | unit | validation (M3) / FR-3 | term `"2,5"` → errors `[{termYears, not_whole_number}]` | SPEC §3.3 | invalid input |
| 35 | `test_validate_term_with_zero_decimal` | unit | validation (M3) / FR-3 | term `"10,0"` → errors `[{termYears, too_many_decimals}]` (whole value, but 1 written decimal > 0 allowed) | SPEC §3.3, 02 M3 order | edge case |
| 36 | `test_validate_term_text` | unit | validation (M3) / FR-3 | term `"thirty"` → errors `[{termYears, not_a_number}]` | SPEC §3.3 | invalid input |
| 37 | `test_validate_missing_field` | unit | validation (M3) / FR-3 | loan `"100000"`, rate `"3"`, term `undefined` → errors `[{termYears, required}]` | SPEC §3.1, §3.3 | invalid input |
| 38 | `test_validate_all_fields_empty` | unit | validation (M3) / FR-3 | `""`, `""`, `""` → errors `[{loanAmount, required}, {annualRate, required}, {termYears, required}]` (all at once, field order) | SPEC §3.3 | invalid input |
| 39 | `test_validate_multiple_invalid_fields` | unit | validation (M3) / FR-3 | loan `"abc"`, rate `"25"`, term `"0"` → errors `[{loanAmount, not_a_number}, {annualRate, above_max}, {termYears, below_min}]` | SPEC §3.3 | invalid input |
| 40 | `test_validate_one_error_per_field` | unit | validation (M3) / FR-3 | loan `"-1000,555"` → exactly one error `[{loanAmount, negative}]` (precedence over `too_many_decimals`) | 02 M3 order | edge case |
| 41 | `test_round_to_cents_exact_half_rounds_up` | unit | calculation (M4) / FR-1 | `roundToCents`: `2.345 → 2.35`; `1.005 → 1.01`; `2.675 → 2.68`; `0.125 → 0.13`; `0.005 → 0.01` | MANUAL (round half up, SPEC §4.3) | edge case |
| 42 | `test_round_to_cents_below_half_rounds_down` | unit | calculation (M4) / FR-1 | `roundToCents`: `2.344999 → 2.34`; `0.004999 → 0.00`; `897.914997950 → 897.91` | MANUAL (SPEC §4.3) | edge case |
| 43 | `test_annuity_standard_rate_30y` | unit | calculation (M4) / FR-1, FR-2 | P=100000, rate=3.5%, term=30y → n=360; Regular **449.04** (M=449.044687…), Final **452.02**, Total Paid **161657.38**, Interest **61657.38** | REF-PY, REF-PMT | happy path |
| 44 | `test_annuity_standard_rate_25y` | unit | calculation (M4) / FR-1, FR-2 | P=200000, rate=4.5%, term=25y → Regular **1111.66**, Final **1114.40**, Total Paid **333500.74**, Interest **133500.74** | REF-PY, REF-PMT | happy path |
| 45 | `test_annuity_payment_rounded_up_final_lower` | unit | calculation (M4) / FR-1, FR-2 | P=250000, rate=6%, term=20y → Regular **1791.08** (M=1791.077646…), Final **1789.99**, Total Paid **429858.11**, Interest **179858.11** | REF-PY, REF-PMT | happy path |
| 46 | `test_annuity_non_round_loan_amount` | unit | calculation (M4) / FR-1, FR-2 | P=50000.55, rate=2.25%, term=7y → Regular **643.91**, Final **643.62**, Total Paid **54088.15**, Interest **4087.60** | REF-PY, REF-PMT | happy path |
| 47 | `test_annuity_final_equals_regular` | unit | calculation (M4) / FR-1, FR-2 | P=10000, rate=3.25%, term=5y → Regular **180.80**, Final **180.80**, Total Paid **10848.00**, Interest **848.00** | REF-PY, REF-PMT | edge case |
| 48 | `test_annuity_final_differs_by_one_cent` | unit | calculation (M4) / FR-1, FR-2 | P=10000, rate=2.5%, term=1y → Regular **844.66**, Final **844.67**, Total Paid **10135.93**, Interest **135.93** | REF-PY, REF-PMT | edge case |
| 49 | `test_annuity_one_year_term` | unit | calculation (M4) / FR-1, FR-2 | P=10000, rate=5%, term=1y → n=12; Regular **856.07**, Final **856.13**, Total Paid **10272.90**, Interest **272.90** | REF-PY, REF-PMT | edge case |
| 50 | `test_annuity_min_loan_min_positive_rate` | unit | calculation (M4) / FR-1, FR-2 | P=1000, rate=0.01%, term=1y → Regular **83.34**, Final **83.31**, Total Paid **1000.05**, Interest **0.05** | REF-PY, REF-PMT | edge case |
| 51 | `test_annuity_max_loan_max_rate_30y` | unit | calculation (M4) / FR-1, FR-2 | P=1000000, rate=20%, term=30y → Regular **16710.19**, Final **16638.10**, Total Paid **6015596.31**, Interest **5015596.31** | REF-PY, REF-PMT | edge case |
| 52 | `test_annuity_min_loan_max_rate_30y` | unit | calculation (M4) / FR-1, FR-2 | P=1000, rate=20%, term=30y → Regular **16.71**, Final **21.00**, Total Paid **6019.89**, Interest **5019.89** | REF-PY, REF-PMT | edge case |
| 53 | `test_annuity_just_above_half_cent` | unit | calculation (M4) / FR-1, FR-2 | P=150000, rate=2%, term=20y → M=758.825002567…, Regular **758.83**, Final **757.36**, Total Paid **182117.73**, Interest **32117.73** | REF-PY, REF-PMT | edge case |
| 54 | `test_annuity_just_below_half_cent` | unit | calculation (M4) / FR-1, FR-2 | P=100000, rate=1.5%, term=10y → M=897.914997950…, Regular **897.91**, Final **898.56**, Total Paid **107749.85**, Interest **7749.85** | REF-PY, REF-PMT | edge case |
| 55 | `test_zero_rate_exact_division` | unit | calculation (M4) / FR-1, FR-2 | P=120000, rate=0%, term=10y → Regular **1000.00**, Final **1000.00**, Total Paid **120000.00**, Interest **0.00** | MANUAL (120000 ÷ 120) | edge case |
| 56 | `test_zero_rate_rounding_absorbed_by_final` | unit | calculation (M4) / FR-1, FR-2 | P=1000, rate=0%, term=1y → Regular **83.33** (1000÷12=83.333…), Final **83.37** (1000 − 83.33×11), Total Paid **1000.00**, Interest **0.00** | MANUAL, REF-PY | edge case |
| 57 | `test_zero_rate_30y_final_lower` | unit | calculation (M4) / FR-1, FR-2 | P=1000, rate=0%, term=30y → Regular **2.78** (2.777…), Final **1.98** (1000 − 2.78×359), Total Paid **1000.00**, Interest **0.00** | MANUAL, REF-PY | edge case |
| 58 | `test_zero_rate_max_loan_30y` | unit | calculation (M4) / FR-1, FR-2 | P=1000000, rate=0%, term=30y → Regular **2777.78**, Final **2776.98** (1000000 − 2777.78×359), Total Paid **1000000.00**, Interest **0.00** | MANUAL, REF-PY | edge case |
| 59 | `test_zero_rate_exact_half_cent_rounds_up` | unit | calculation (M4) / FR-1, FR-2 | P=1000.14, rate=0%, term=1y → M=83.345 exactly → Regular **83.35** (half-even would give 83.34), Final **83.29** (1000.14 − 83.35×11), Total Paid **1000.14**, Interest **0.00** | MANUAL, REF-PY | edge case |
| 60 | `test_calculation_invariants_hold` | unit | calculation (M4) / FR-1, FR-2 | For every input in tests 43–59: `numberOfPayments = n` (none ends early); `totalPaid = regular×(n−1) + final`; `totalInterest = totalPaid − P`; `finalPayment > 0`; `totalInterest ≥ 0`; `totalInterest = 0` when rate = 0. The whole input domain is covered by test 108 | SPEC §4.4, §4.5 | edge case |
| 61 | `test_calculation_leaves_global_decimal_config_unchanged` | unit | calculation (M4) / FR-1 | Set `Decimal.set({precision: 5, rounding: ROUND_DOWN})`, then call with P=100000, 3.5%, 30y → result still Regular **449.04**, Final **452.02**; global config still `precision 5, ROUND_DOWN` | 02 M4 (private clone), REF-PY | edge case |
| 62 | `test_format_money_thousands_separator` | unit | formatting (M5) / FR-1, FR-2 | `1234.57` → `"1 234,57 €"` | SPEC §3.4 (example) | happy path |
| 63 | `test_format_money_below_thousand` | unit | formatting (M5) / FR-1, FR-2 | `449.04` → `"449,04 €"` | SPEC §3.4 | happy path |
| 64 | `test_format_money_millions` | unit | formatting (M5) / FR-1, FR-2 | `6015596.31` → `"6 015 596,31 €"` | SPEC §3.4 | happy path |
| 65 | `test_format_money_pads_two_decimals` | unit | formatting (M5) / FR-1, FR-2 | `1000000` → `"1 000 000,00 €"`; `0.5` → `"0,50 €"` | SPEC §3.4 | edge case |
| 66 | `test_format_money_zero` | unit | formatting (M5) / FR-2 | `0` → `"0,00 €"` | SPEC §3.4 | edge case |
| 67 | `test_format_money_rounds_half_up` | unit | formatting (M5) / FR-1 | `1234.565` → `"1 234,57 €"`; `1234.564999` → `"1 234,56 €"` | MANUAL (SPEC §3.4, §4.3) | edge case |
| 68 | `test_format_money_uses_ascii_spaces_only` | unit | formatting (M5) / FR-1 | `1234567.89` → `"1 234 567,89 €"`; contains no U+00A0 or U+202F characters | 02 ADR-4 | edge case |
| 69 | `test_show_final_payment_when_one_cent_different` | unit | presentation (M6) / FR-1 | regular `844.66`, final `844.67` → `true` | SPEC §2 Outputs | edge case |
| 70 | `test_hide_final_payment_when_equal` | unit | presentation (M6) / FR-1 | regular `180.80`, final `180.80` → `false` | SPEC §2 Outputs | edge case |
| 71 | `test_show_final_payment_when_lower` | unit | presentation (M6) / FR-1 | regular `1791.08`, final `1789.99` → `true` | SPEC §2 Outputs | happy path |
| 72 | `test_result_view_with_final_payment` | unit | presentation (M6) / FR-1, FR-2 | Result (449.04, 452.02, 161657.38, 61657.38) → 4 lines in order: `Regular Monthly Payment: 449,04 €`, `Final Payment: 452,02 €`, `Total Paid: 161 657,38 €`, `Total Interest: 61 657,38 €` | SPEC §2 Outputs, REF-PY | happy path |
| 73 | `test_result_view_without_final_payment` | unit | presentation (M6) / FR-1, FR-2 | Result (180.80, 180.80, 10848.00, 848.00) → 3 lines: `Regular Monthly Payment: 180,80 €`, `Total Paid: 10 848,00 €`, `Total Interest: 848,00 €` | SPEC §2 Outputs | edge case |
| 74 | `test_error_view_required_message` | unit | presentation (M6) / FR-3 | `{loanAmount, required}` → label `Loan amount`, message `"Loan amount is required."` | Expected UI texts | invalid input |
| 75 | `test_error_view_not_a_number_message` | unit | presentation (M6) / FR-3 | `{annualRate, not_a_number}` → `"Annual interest rate must be a number."` | Expected UI texts | invalid input |
| 76 | `test_error_view_negative_message` | unit | presentation (M6) / FR-3 | `{loanAmount, negative}` → `"Loan amount must not be negative."` | Expected UI texts | invalid input |
| 77 | `test_error_view_range_messages` | unit | presentation (M6) / FR-3 | `{loanAmount, below_min}` → `"Loan amount must be between 1 000,00 € and 1 000 000,00 €."`; `{annualRate, above_max}` → `"Annual interest rate must be between 0,00 % and 20,00 %."`; `{termYears, above_max}` → `"Term must be between 1 and 30 years."` | Expected UI texts | invalid input |
| 78 | `test_error_view_decimal_messages` | unit | presentation (M6) / FR-3 | `{annualRate, too_many_decimals}` → `"Annual interest rate can have at most 2 decimal places."`; `{termYears, not_whole_number}` and `{termYears, too_many_decimals}` → `"Term must be a whole number of years."` | Expected UI texts | invalid input |
| 79 | `test_error_view_one_message_per_field_in_field_order` | unit | presentation (M6) / FR-3 | `[{termYears, below_min}, {loanAmount, required}]` → 2 entries ordered `Loan amount`, then `Term` | SPEC §3.3 | edge case |
| 80 | `test_calculator_valid_input_returns_result` | functional | calculator (M7) / FR-1, FR-2, FR-3 | raw `"100 000"`, `"3,5"`, `"30"` → kind `result`; lines `449,04 €`, `452,02 €`, `161 657,38 €`, `61 657,38 €` | REF-PY | happy path |
| 81 | `test_calculator_zero_rate_full_flow` | functional | calculator (M7) / FR-1, FR-2 | raw `"1 000"`, `"0"`, `"1"` → kind `result`; `Regular Monthly Payment: 83,33 €`, `Final Payment: 83,37 €`, `Total Paid: 1 000,00 €`, `Total Interest: 0,00 €` | MANUAL, REF-PY | edge case |
| 82 | `test_calculator_invalid_input_skips_calculation` | functional | calculator (M7) / FR-3 | raw `"-100000"`, `"3,5"`, `"30"` → kind `invalid`; errors `["Loan amount must not be negative."]`; spy on `calculateMortgage` called **0** times | SPEC §3.3 | invalid input |
| 83 | `test_calculator_partial_invalid_returns_no_results` | functional | calculator (M7) / FR-3 | raw `"100000"`, `"abc"`, `"30"` → kind `invalid`; errors `["Annual interest rate must be a number."]`; no result lines; `calculateMortgage` called 0 times | SPEC §3.3 | invalid input |
| 84 | `test_calculator_all_missing` | functional | calculator (M7) / FR-3 | raw `undefined` ×3 → kind `invalid`; 3 messages: `"Loan amount is required."`, `"Annual interest rate is required."`, `"Term is required."` | SPEC §3.3 | invalid input |
| 85 | `test_cli_prompts_in_order` | functional | cli (M8) / FR-3 | Fake `TerminalIo` answers `"100000"`, `"3.5"`, `"30"` → `ask` called with `"Loan amount (EUR): "`, `"Annual interest rate (%): "`, `"Term (years): "` in that order, with no pre-filled values | SPEC §3.1, Expected UI texts | happy path |
| 86 | `test_cli_prints_results_and_exits_zero` | functional | cli (M8) / FR-1, FR-2 | Answers `"100000"`, `"3.5"`, `"30"` → printed lines `Regular Monthly Payment: 449,04 €`, `Final Payment: 452,02 €`, `Total Paid: 161 657,38 €`, `Total Interest: 61 657,38 €`; returns exit code `0` | REF-PY | happy path |
| 87 | `test_cli_reprompts_only_invalid_fields` | functional | cli (M8) / FR-3 | Answers `"abc"`, `"3,5"`, `"31"`, then `"100000"`, `"30"` → prints `"Loan amount must be a number."`, `"Term must be between 1 and 30 years."`; the 4th and 5th `ask` calls are `Loan amount (EUR): ` and `Term (years): ` (the rate is not asked again); then prints the result of test 86; exit `0` | SPEC §3.3, 02 M8 | invalid input |
| 88 | `test_cli_closed_input_exits_one` | functional | cli (M8) / FR-3 | `ask` returns `undefined` at the first prompt → no result lines printed; returns exit code `1` | 02 M8 | edge case |
| 89 | `test_e2e_cli_standard_mortgage` | e2e | main + cli → all modules / FR-1, FR-2, FR-3 | Spawn `npx tsx src/main.ts`, stdin `"100 000\n3,5\n30\n"` → stdout contains the 3 prompts, then `Regular Monthly Payment: 449,04 €`, `Final Payment: 452,02 €`, `Total Paid: 161 657,38 €`, `Total Interest: 61 657,38 €`; exit code `0` | REF-PY, REF-PMT | happy path |
| 90 | `test_e2e_cli_zero_rate_hides_final_payment` | e2e | main + cli → all modules / FR-1, FR-2 | stdin `"120000\n0\n10\n"` → stdout contains `Regular Monthly Payment: 1 000,00 €`, `Total Paid: 120 000,00 €`, `Total Interest: 0,00 €`, and does **not** contain `Final Payment`; exit `0` | MANUAL | edge case |
| 91 | `test_e2e_cli_invalid_then_corrected_input` | e2e | main + cli → all modules / FR-1, FR-2, FR-3 | stdin `"1,000.50\n25\n10\n1000,50\n2,5\n"` → stdout contains `Loan amount must be a number.` and `Annual interest rate must be between 0,00 % and 20,00 %.`, re-prompts loan and rate only, then `Regular Monthly Payment: 9,43 €`, `Final Payment: 9,66 €`, `Total Paid: 1 131,83 €`, `Total Interest: 131,33 €`; exit `0` | REF-PY, REF-PMT | invalid input |
| 92 | `test_e2e_cli_input_closed_early` | e2e | main + cli → all modules / FR-3 | stdin `"100000\n"` then EOF → stdout has no result lines; exit code `1` | 02 M8 | edge case |
| 93 | `test_architecture_dependency_direction` | unit | all modules (02 §4) / — | Scan every `import` in `src/` → no import breaks rules 1–6 (e.g. `domain/` → `ui/` is a failure) | 02 §4 | happy path |
| 94 | `test_architecture_domain_has_no_io` | unit | calculation (M4), types (M1) / FR-1, FR-2 | `src/domain/**` imports only `decimal.js` and `./types`; no `node:*`, `process` or `console` usage | 02 §4 rule 2 | edge case |
| 95 | `test_architecture_no_circular_dependencies` | unit | all modules (02 §4) / — | The import graph of `src/` has no cycles | 02 §4 rule 6 | edge case |
| 96 | `test_parse_hex_binary_octal_rejected` | unit | parsing (M2) / FR-3 | `"0x3E8"`, `"0b1010"`, `"0o17"` → error `not_a_number` each (decimal.js would accept them; `NUMBER_PATTERN` runs first) | SPEC §3.2 (strict grammar), 02 M2 | invalid input |
| 97 | `test_parse_nan_and_infinity_rejected` | unit | parsing (M2) / FR-3 | `"NaN"`, `"Infinity"`, `"-Infinity"` → error `not_a_number` each | SPEC §3.2 (strict grammar) | invalid input |
| 98 | `test_parse_exponent_variants_rejected` | unit | parsing (M2) / FR-3 | `"1E5"`, `"1e-2"`, `"2,5e3"` → error `not_a_number` each | SPEC §3.2 (strict grammar) | invalid input |
| 99 | `test_parse_separator_without_digits_rejected` | unit | parsing (M2) / FR-3 | `"1000,"`, `",50"`, `".5"` → error `not_a_number` each | SPEC §3.2 (strict grammar) | invalid input |
| 100 | `test_parse_sign_other_than_leading_minus_rejected` | unit | parsing (M2) / FR-3 | `"+30"`, `"−5000"` (U+2212), `"5000-"` → error `not_a_number` each | SPEC §3.2 (strict grammar) | invalid input |
| 101 | `test_validate_hex_loan_amount_rejected` | unit | validation (M3) / FR-3 | loan `"0x3E8"`, rate `"3"`, term `"10"` → errors `[{loanAmount, not_a_number}]` (not accepted as 1 000) | SPEC §3.2, §3.3 | invalid input |
| 102 | `test_early_termination_rounded_up_payment` | unit | calculation (M4) / FR-1, FR-2 | P=1000.29, rate=20%, term=30y → M=16.715032816…, Regular **16.72**, numberOfPayments **354** (of 360), Final **8.08**, Total Paid **5910.24**, Interest **4909.95** (the old rule would have given Final −97.42) | REF-ET | edge case |
| 103 | `test_early_termination_largest_overpayment` | unit | calculation (M4) / FR-1, FR-2 | P=1011.06, rate=20%, term=30y → M=16.895001529…, Regular **16.90**, numberOfPayments **354**, Final **8.63**, Total Paid **5974.33**, Interest **4963.27** | REF-ET | edge case |
| 104 | `test_early_termination_round_loan_amount` | unit | calculation (M4) / FR-1, FR-2 | P=1000, rate=10%, term=30y → M=8.775715700…, Regular **8.78**, numberOfPayments **359**, Final **7.88**, Total Paid **3151.12**, Interest **2151.12** | REF-ET | edge case |
| 105 | `test_early_termination_one_month_early_low_rate` | unit | calculation (M4) / FR-1, FR-2 | P=1001.01, rate=8%, term=30y → M=7.345056760…, Regular **7.35**, numberOfPayments **359**, Final **7.33**, Total Paid **2638.63**, Interest **1637.62** | REF-ET | edge case |
| 106 | `test_early_termination_remainder_rounds_to_zero` | unit | calculation (M4) / FR-1, FR-2 | P=1075.15, rate=20%, term=30y → M=17.965957405…, Regular **17.97**; the month-356 amount due is 0.004910… and rounds to 0.00, so month 355 is the last: numberOfPayments **355**, Final **17.97** (= Regular), Total Paid **6379.35** (17.97 × 355), Interest **5304.20** | REF-ET, SPEC §4.4 step 3 | edge case |
| 107 | `test_full_term_final_far_below_regular` | unit | calculation (M4) / FR-1, FR-2 | P=1003.93, rate=20%, term=20y → M=17.055009882…, Regular **17.06**, numberOfPayments **240** (full term, no early termination), Final **1.54**, Total Paid **4078.88**, Interest **3074.95** | REF-ET | edge case |
| 108 | `test_calculation_invariants_property_sweep` | unit | calculation (M4) / FR-1, FR-2 | Seeded sweep with no extra dependency: grid P = 1000.00 … 1005.99 (step 0.01) × rate ∈ {8, 10, 15, 20} % × term ∈ {25, 30} y (4 800 inputs) plus 2 000 seeded random valid inputs (P, rate, term uniform over 01 §3.1). For **every** result: `finalPayment > 0`; `totalPaid` = sum of payments = `regular×(numberOfPayments−1) + final`; `totalInterest = totalPaid − P ≥ 0`; `numberOfPayments ≤ n`; if `numberOfPayments < n` then `finalPayment ≤ regularPayment`; if rate = 0 then `numberOfPayments = n`. (REF-ET on the same domain: 6 800 inputs, 767 end early, 0 violations.) | REF-ET, SPEC §4.4, §4.5 | edge case |
| 109 | `test_calculator_early_termination_equal_final_hidden` | functional | calculator (M7) / FR-1, FR-2 | raw `"1 075,15"`, `"20"`, `"30"` → kind `result`; 3 lines: `Regular Monthly Payment: 17,97 €`, `Total Paid: 6 379,35 €`, `Total Interest: 5 304,20 €` (no `Final Payment` line, because Final = Regular) | REF-ET, SPEC §2 Outputs | edge case |
| 110 | `test_e2e_cli_early_termination` | e2e | main + cli → all modules / FR-1, FR-2 | stdin `"1000,29\n20\n30\n"` → stdout contains `Regular Monthly Payment: 16,72 €`, `Final Payment: 8,08 €`, `Total Paid: 5 910,24 €`, `Total Interest: 4 909,95 €`; exit `0` | REF-ET | edge case |
| 111 | `test_node_terminal_io_answers_all_piped_lines` | functional | cli (M8) / FR-3 | `createNodeTerminalIo(input, output)` with in-memory `PassThrough` streams; write `"100 000\n3,5\n30\n"` as **one chunk** and end the input before the first `ask` → the first three `ask` calls return `"100 000"`, `"3,5"`, `"30"` in order, the 4th returns `undefined`; `output` contains the three prompts | 02 M8 (Terminal reader), ADR-10 | edge case |
| 112 | `test_node_terminal_io_pending_ask_resolves_at_eof` | functional | cli (M8) / FR-3 | Call `ask("Loan amount (EUR): ")` with no input yet, then end the input stream → the promise resolves to `undefined` (it must not hang; test timeout 1 s) | 02 M8 (Terminal reader), ADR-10 | edge case |

---

## Coverage Summary

### By functional requirement

| Requirement | Tests |
|---|---|
| **FR-1** Calculate monthly payment | 41–61, 62–65, 67–73, 80–81, 86, 89–91, 94, 102–110 |
| **FR-2** Calculate totals | 43–60, 62–66, 72–73, 80–81, 86, 89–91, 94, 102–110 |
| **FR-3** Validate inputs | 1–40, 74–80, 82–85, 87–89, 91–92, 96–101, 111–112 |

### By module

| Module | Happy path | Edge case | Invalid input |
|---|---|---|---|
| parsing (M2) | 1–4 | 5–7 | 8–16, 96–100 |
| validation (M3) | 17 | 18–19, 24–26, 30–31, 35, 40 | 20–23, 27–29, 32–34, 36–39, 101 |
| calculation (M4) | 43–46 | 41–42, 47–61, 102–108 | via 82–83 (see note) |
| formatting (M5) | 62–64 | 65–68 | — (only receives `Decimal`s) |
| presentation (M6) | 71–72 | 69–70, 73, 79 | 74–78 |
| calculator (M7) | 80 | 81, 109 | 82–84 |
| cli (M8) | 85–86 | 88, 111–112 | 87 |
| e2e | 89 | 90, 92, 110 | 91 |
| architecture | 93 | 94–95 | — |

**Note on invalid input for calculation (M4):** by design (02 §3, M4 and M7), `calculateMortgage` accepts only a validated `LoanInput`, and invalid values can never reach it. Its invalid-input coverage is the guarantee that it is **never called** for invalid input (tests 82–83, spy count 0). The input boundaries it relies on are covered by tests 18–40.

### Required edge cases checklist

| Required edge case | Tests |
|---|---|
| 0 % interest rate | 25, 55–59, 81, 90 |
| 1-year term | 30, 48–50, 56, 59, 81 |
| 30-year term | 31, 43, 51–52, 57–58, 89 |
| Rounding boundary (.005) | 41, 53, 54, 59, 67 |
| Negative loan | 7, 22, 82 |
| Text string | 11, 36, 83, 87 |
| Multiple decimal points | 12–14, 91 |
| Final payment = / ≠ regular (±€0.01) | 47, 48, 69–71, 73, 90 |
| Min / max boundaries (inclusive and just outside) | 18–21, 25–27, 30–33, 50–52 |
| Full E2E (prompt → displayed output) | 89–92, 110 |
| Early termination (loan repaid before month n) | 102–106, 108–110 (and 107 as the full-term counter-case) |
| Strict number grammar (hex, exponent, `NaN`, `Infinity`, bare separators, signs) | 16, 96–101 |
| Invariants over the whole valid input domain | 108 |
| Piped stdin and EOF in the real terminal reader | 89–92, 110–112 |

---

## Appendix A — Reference script (REF-PY)

This script implements section 4.4 as it was before the review revision (always n payments). It is valid for every loan that runs the full term, which includes all of tests 43–59 and 91. For early-terminated loans use REF-ET (Appendix B).

Run with Python 3.8+ (no third-party packages):

```python
from decimal import Decimal as D, getcontext, ROUND_HALF_UP
getcontext().prec = 60
CENT = D('0.01')

def rc(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)

def calc(P, rate, years):
    P, rate = D(P), D(rate)
    n = years * 12
    r = rate / 12 / 100
    M = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    Mr = rc(M)
    B = P
    for _ in range(n - 1):            # full-precision balance run (section 4.4)
        B = B * (1 + r) - Mr
    final = rc(B * (1 + r))
    # independent closed-form cross-check of the remaining balance
    B2 = P * (1 + r) ** (n - 1) - Mr * ((1 + r) ** (n - 1) - 1) / r if r > 0 else P - Mr * (n - 1)
    assert rc(B2 * (1 + r)) == final
    total = Mr * (n - 1) + final
    return {'M': M, 'regular': Mr, 'final': final, 'total_paid': total, 'total_interest': total - P}

print(calc('100000', '3.5', 30))
# {'M': Decimal('449.0446878088…'), 'regular': Decimal('449.04'), 'final': Decimal('452.02'),
#  'total_paid': Decimal('161657.38'), 'total_interest': Decimal('61657.38')}
```

## Appendix B — Reference script (REF-ET, revised section 4.4)

Run with Python 3.8+ (no third-party packages). Exact rational arithmetic, so there is no precision limit.

```python
from fractions import Fraction as F
import math, random

def rc(x):                                   # round half up to cents, exact
    c = x * 100; s = -1 if c < 0 else 1; c = abs(c); fl = math.floor(c)
    return F(s * (fl + (1 if c - fl >= F(1, 2) else 0)), 100)

def calc(P, rate, years):
    P = F(P); r = F(rate) / 1200; n = years * 12
    M = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    Mr = rc(M); B = P
    for k in range(1, n + 1):                # section 4.4 step 2
        D = B * (1 + r)                      # balance + interest accrued this month
        if k == n or D <= Mr:
            break                            # last active month (early termination if k < n)
        B = D - Mr
    final, payments = rc(D), k
    if final == 0:                           # section 4.4 step 3: remainder rounds to 0.00
        final, payments = Mr, k - 1
    total = Mr * (payments - 1) + final
    return dict(regular=Mr, payments=payments, n=n, final=final, total=total, interest=total - P)

def show(t, *a):
    x = calc(*a)
    print(t, a, 'regular', float(x['regular']), 'payments', x['payments'], 'final', float(x['final']),
          'total', float(x['total']), 'interest', float(x['interest']))

for t, a in [(102, ('1000.29', '20', 30)), (103, ('1011.06', '20', 30)), (104, ('1000', '10', 30)),
             (105, ('1001.01', '8', 30)), (106, ('1075.15', '20', 30)), (107, ('1003.93', '20', 20)),
             (43, ('100000', '3.5', 30)), (52, ('1000', '20', 30))]:
    show(t, *a)

random.seed(7)                               # test 108 domain
grid = [(c, rt, y) for c in range(100000, 100600) for rt in (2000, 1500, 1000, 800) for y in (30, 25)]
grid += [(random.randint(100000, 100000000), random.randint(0, 2000), random.randint(1, 30)) for _ in range(2000)]
early = bad = 0
for c, rt, y in grid:
    P = F(c, 100); x = calc(P, F(rt, 100), y)
    payments = [x['regular']] * (x['payments'] - 1) + [x['final']]
    is_early = x['payments'] < x['n']; early += is_early
    ok = (x['final'] > 0 and sum(payments) == x['total'] and x['payments'] <= x['n']
          and x['interest'] == x['total'] - P and x['interest'] >= 0
          and (not is_early or x['final'] <= x['regular']) and (rt != 0 or not is_early))
    bad += not ok
print('sweep', len(grid), 'early', early, 'violations', bad)
```

Output:

```
102 ('1000.29', '20', 30) regular 16.72 payments 354 final 8.08 total 5910.24 interest 4909.95
103 ('1011.06', '20', 30) regular 16.9 payments 354 final 8.63 total 5974.33 interest 4963.27
104 ('1000', '10', 30) regular 8.78 payments 359 final 7.88 total 3151.12 interest 2151.12
105 ('1001.01', '8', 30) regular 7.35 payments 359 final 7.33 total 2638.63 interest 1637.62
106 ('1075.15', '20', 30) regular 17.97 payments 355 final 17.97 total 6379.35 interest 5304.2
107 ('1003.93', '20', 20) regular 17.06 payments 240 final 1.54 total 4078.88 interest 3074.95
43 ('100000', '3.5', 30) regular 449.04 payments 360 final 452.02 total 161657.38 interest 61657.38
52 ('1000', '20', 30) regular 16.71 payments 360 final 21.0 total 6019.89 interest 5019.89
sweep 6800 early 767 violations 0
```

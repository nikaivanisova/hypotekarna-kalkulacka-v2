# 04 — Independent Review (V1)

Status: **Author decisions recorded for findings #1–#6** (2026-10-21). Findings #7–#24 are still open.

Scope: an independent audit of [`01-functional.md`](01-functional.md), [`02-architecture.md`](02-architecture.md) and [`03-test-scenarios.md`](03-test-scenarios.md). No other files were used as a source. I treated claims in the documents as unverified. Where a finding says **verified**, it was reproduced by running a script or program (see the Appendix).

Severity scale:
- **Blocker**: V1 produces wrong results for valid inputs, or the plan cannot be implemented as written.
- **Major**: likely defect or rework, or a requirement two implementers would build differently.
- **Minor**: a clarity, traceability or coverage gap.

---

## Findings

| # | Severity | Affects | Finding | Author Decision | Reason |
|---|---|---|---|---|---|
| 1 | Blocker | Requirement §4.4 / FR-1, FR-2; Module M4 (invariant `finalPayment > 0`); Test 60 | **Valid inputs give a negative Final Payment (verified).** M_rounded is fixed for all n−1 payments, so the cents-rounding error δ = M_rounded − M (up to ±€0.005) compounds over the term. At high rates and long terms this outweighs the payment itself. Example: P = 1 000.29, rate 20 %, term 30 y → M = 16.715033…, Regular **16.72**, the balance goes negative after month 354, Final **−97.42**, Total Paid 5 905.06, Interest 4 904.77. In the range P = 1 000.00–1 199.99 at 20 %/30 y, 8 396 of 20 000 inputs give Final ≤ 0 (minimum −97.95 at P = 1 011.06). The problem also occurs at 20 %/25 y (min −25.46), 15 %/30 y (−21.86), 15 %/25 y (−3.28), 12 %/30 y (−7.12), 10 %/30 y (−2.47) and 8 %/30 y (−0.06), all with P in 1 000–1 099.99. At 0 % it cannot happen (Final ≥ P/n − 0.005·(n−1) ≥ €0.98). 01 does not define what happens when the loan is paid off before payment n. The architecture invariant `finalPayment > 0` is false over the valid input domain. Test 60 passes only because it checks the 17 hand-picked inputs from tests 43–59. Test 52 (P = 1 000, 20 %, 30 y, Final 21.00 vs Regular 16.71) shows the same effect in the opposite direction. The author must choose a rule, e.g. (a) restrict the input domain, (b) end the loan early with a shorter n and a partial last payment, (c) recompute the payment so the schedule stays positive, or (d) reject such inputs with a validation error. The choice changes FR-1/FR-2 outputs, M4, M6 and tests 43–60. | Accepted | If the amount due (balance + accrued interest) in a month k < n is ≤ M_rounded, the loan terminates early: the Final Payment is that exact amount due, rounded to cents, and the remaining months are skipped. If it rounds to €0.00, the previous month's payment is the final one. Applied in 01 §4.4/§4.5 and FR-1/FR-2, in 02 M1 (`numberOfPayments` = payments made) and M4 (steps 3–5, invariants), and in 03 tests 102–110 (values from the new exact-rational reference REF-ET, Appendix B). Existing tests 43–59 and 91 are unchanged, because none of them ends early. |
| 2 | Major | Module M8 (`createNodeTerminalIo`); Tests 88, 89–92 | **The Node terminal adapter as specified cannot pass the e2e tests (verified on Node 24.20.0).** M8 specifies `node:readline/promises` and `ask(): Promise<string \| undefined>` with "undefined = input stream closed". A straightforward `rl.question()` loop with piped stdin (`printf '100 000\n3,5\n30\n' \| node …`) receives only the first answer. Readline emits the remaining buffered lines as `line` events while no question is pending, and they are lost. The second `question()` promise then never settles on EOF, and Node exits with code 13 ("unsettled top-level await") instead of 1. So tests 89–92 (piped stdin) and the "closed stream → exit 1" rule would fail with the obvious implementation. 02 should specify a line-queue design, e.g. `for await (const line of rl)` / an async line iterator plus a `close` listener that resolves pending asks with `undefined`, and the expected exit code on EOF. | Accepted | 02 M8 now specifies an event-driven line queue over `node:readline` (`line`/`close` events, FIFO buffer, pending and later asks resolve to `undefined` at EOF) instead of sequential `readline/promises` questions, with injectable streams (ADR-10). A prototype was verified with piped stdin, CRLF input and EOF on Node 24.20.0. New tests 111–112. |
| 3 | Major | Requirement §3.2/§3.3; Module M2; Test 16 | **The accepted number grammar is not defined, and decimal.js accepts more than the spec intends.** 01 §3.2 lists separators and spaces but never states which characters may appear. M2's description does not state a whitelist either. Test 16 says "only digits, one separator, optional leading `-`" and labels it *derived*. Per decimal.js documentation, `new Decimal()` also accepts `"0x3E8"` (= 1000), `"0b…"`, `"0o…"`, `"Infinity"`, `"NaN"` and exponent forms like `"1e5"`. An M2 that only normalises separators and then calls `new Decimal()` would accept `0x3E8` as a valid loan of €1 000. Only `1e5` is tested. The grammar should be stated in 01 §3.2 (e.g. `^-?\d+([.,]\d+)?$` after space removal), and tests added for hex/binary/octal prefixes, `Infinity`, `NaN` and `-Infinity`. | Accepted | 01 §3.2 defines the strict grammar `^-?[0-9]+([.,][0-9]+)?$`, checked after trimming and removing spaces and **before** decimal.js. Hex/binary/octal, exponent notation, `NaN` and `Infinity` are explicitly rejected. 02 M2 exports `NUMBER_PATTERN` and orders the steps. New tests 96–101. The same grammar also settles the edge-separator and sign questions of findings #10 and #11, and the non-ASCII digits in #23. `-0` (#9) and the space rules (#12) are not affected. |
| 4 | Major | Test 60; Module M4 (invariants) | **The invariant test has no sweep over the input domain.** Test 60 checks invariants only on the fixed inputs of tests 43–59, so it could not find Finding 1. Any invariant that is claimed for every valid input (`finalPayment > 0`, `totalInterest ≥ 0`, residual within half a cent) should be tested with a property-based or grid sweep over P, rate and term, including small P with high rates and long terms. | Accepted | Test 108 adds a seeded sweep over 6 800 valid inputs that asserts: Final > 0, Total Paid = sum of payments, Interest = Total Paid − P ≥ 0, payments ≤ n, and 0 % never ends early. Per the author, "Final ≤ Regular" is asserted **only for early-terminated loans**, because full-term loans may correctly have Final > Regular (e.g. tests 43, 52). REF-ET: 767 early terminations, 0 violations. |
| 5 | Major | Architecture (stress test): **Extra / one-off payments**; Modules M1, M3, M4, M6, M7, M8 | **Architectural issue: 5–6 existing modules must change.** M1: `LoanInput.extraPayments` and a matching raw input shape. `RawLoanInput` holds only three scalar strings. M3: the data-driven `FieldRule` model (min/max/decimals per scalar `Field`) cannot validate a list of `{month, amount}`, so the validation loop itself must change, not just the `V1_RULES` data (this contradicts the M3 extension-point claim). There are also cross-field rules: month ≤ n, and an extra payment ≤ the balance. M4: the adjustment hook alone is not enough. Early payoff changes `numberOfPayments`, the meaning of "final payment", and the totals formula `M_rounded·(n−1) + Final` (§4.5), which no longer holds. M6: new output lines (e.g. months saved, interest saved). M7: still unchanged in signature, but its outcome now carries extra data. M8: new prompts. | Accepted as documented trade-off | The V1 architecture is retained as designed. The friction for extra payments is recorded in 02 ADR-9. |
| 6 | Major | Architecture (stress test): **Variable / adjustable rates**; Modules M1, M3, M4, M6, M8 | **Architectural issue: 5 existing modules must change, including a breaking type change.** M1: replacing `annualRatePercent` with `RateSchedule` breaks every consumer of `LoanInput` (M3, M4 and their tests). `MortgageResult` has a single `regularPayment`, but with variable rates an annuity is re-amortised at each rate change, so there is one regular payment per rate period. M4: the claimed extension (replace constant `r` with `rateForMonth`) is wrong on its own. If M_rounded stays fixed while r changes, the "final payment" absorbs the whole difference, which makes Finding 1 much worse. The payment must be recomputed per period. M3: validation of a schedule (period boundaries, coverage of all n months). M6: payment per period. M8: schedule input. | Accepted as documented trade-off | The V1 architecture is retained as designed. 02 M4 (extension points) and ADR-9 state that V2 variable rates will introduce a dedicated schedule calculation module (e.g. `domain/schedule`) instead of extending M4 in place. |
| 7 | Minor | Architecture (stress test): **Month-by-month repayment schedule**; Modules M1, M4, M6, M7, M8 | **Architectural issue (milder): 5 existing modules must change, but the changes are additive.** M1: a new `ScheduleRow` type. M4: export `amortize()` (the planned extraction). M6: `toScheduleView`. M7: `CalculatorOutcome` / `ResultView` must carry the rows, or a new use case is needed. M8: printing or an option. There is also a requirement conflict that the extension point hides: displayed rows need per-row cents-rounded interest/principal/balance, but §4.3 forbids intermediate rounding, so rounded rows will not sum to the displayed totals. The author must decide on a display-only rounding rule before the schedule can be added. |  |  |
| 8 | Minor | Requirement §4.4; Module M4 (invariant text) | **"The loan balance ends at exactly €0.00" contradicts "Final Payment = B × (1 + r), rounded to cents" (verified).** Rounding the final payment leaves a residual of up to ±€0.005. In the reference cases it ranges from −0.003586 (test 51) to +0.003696 (test 52), and it is only exactly 0 at 0 %. 02 M4 quietly restates the rule as "within half a cent". An implementer who follows the "exactly €0.00" sentence could leave the final payment unrounded, or round it up (ceil). 01 should say that the balance is €0.00 *to the cent*. |  |  |
| 9 | Minor | Requirement §3.3 ("negative"); Module M2/M3; Tests 7, 22, 28 | **Negative zero is ambiguous.** `"-0"`, `"-0,00"` and `"-0.0"` are not negative numbers mathematically, but `new Decimal('-0').isNeg()` is `true` in decimal.js. One implementation reports `negative`, another accepts them as a valid 0 % rate. 01 should say which, and a test should be added. |  |  |
| 10 | Minor | Requirement §3.2; Module M2 | **A separator at the start or end of a number is undefined.** `"1000,"`, `"1000."`, `",5"` and `".5"` could be accepted (as 1000 with writtenDecimals 0 or 1, and 0.5) or rejected as `not_a_number`. For `"1000,"` it is also unclear whether writtenDecimals is 0, and that decides `too_many_decimals` for the term (`"10,"`). No test covers these. |  |  |
| 11 | Minor | Requirement §3.2; Module M2 | **Sign characters other than `-` are undefined.** A leading `+` (`"+30"`), a Unicode minus `−` (U+2212) and a trailing minus (`"5000-"`) can each be accepted or rejected. A space between sign and digits (`"- 5000"`) becomes `-5000` under the "spaces are ignored" rule, which is probably intended, but it is not stated. |  |  |
| 12 | Minor | Requirement §3.2; Module M2; Tests 3, 5 | **The space rules are ambiguous in two ways.** (a) Grouping: "spaces are treated as thousands separators" suggests groups of three, but "spaces inside a number are ignored" accepts `"10 00"`, `"1 0 0 0"` and `"1000 ,50"`. The two readings give different results for the same input. (b) Character set: it is unclear whether "space" means only U+0020, or also tab, NBSP (U+00A0) and narrow NBSP (U+202F). Users copying numbers from Slovak-formatted documents typically paste U+00A0/U+202F. JS `trim()` removes them at the edges, but an inner-space regex `/ /g` does not, so `"1 000"` with NBSP would be `not_a_number` in the middle but accepted at the ends. Tests use only ASCII spaces. |  |  |
| 13 | Minor | Requirement §3.1/§3.3 (term); Module M3; Test 35 | **The term `"10,0"` is decided by the tests, not by the spec.** 01 lists both "more decimal places than allowed" and "not a whole number". `"10,0"` is a whole number written with one decimal. Test 35 rejects it, while an implementation that checks the value would accept it as 10. The rule (reject / accept) should be written in 01 §3.1. |  |  |
| 14 | Minor | Requirement §4.3; Module M4 (precision 40); ADR-3 | **"Full precision" is not literally achievable, and the tolerance is not stated.** (1 + r)ⁿ is a rational with a huge denominator. 02 chooses 40 significant digits and REF-PY uses 60. I compared the 40-digit `ROUND_HALF_UP` arithmetic with exact rational arithmetic on all 18 reference inputs and 300 random valid inputs: **0 mismatches**, so the practical risk is low. 01/02 should still say that "full precision" means at least N significant digits, and that an output only fails if it differs from the exact rational result after rounding to cents. |  |  |
| 15 | Minor | Requirement §4.3; Modules M4, M5 | **Round half up is undefined for negative amounts, and negative money formatting is unspecified.** "Half up" can mean toward +∞ (−2.345 → −2.34) or away from zero (−2.35, decimal.js `ROUND_HALF_UP`). V1 assumes all outputs are positive, but Finding 1 shows a negative Final Payment is reachable, and then M5's output (`-97,42 €`? `−97,42 €`?) is also undefined. This is resolved automatically if Finding 1 is resolved so that no output can be negative. |  |  |
| 16 | Minor | Modules M4, M5; Dependency rule 3; Tests 61, 67 | **Two independent round-half-up implementations.** Rule 3 says `output/` depends only on `domain/types`, so M5 cannot reuse M4's `roundToCents` and must round again (test 67). If M5 uses decimal.js `toFixed(2)` without an explicit rounding mode, it uses the *global* `Decimal.rounding`, which test 61 shows can be changed. M5 has no equivalent of test 61. Options: allow `output → domain/calculation.roundToCents`, move rounding into a shared domain helper, or require M5 to only accept already-rounded amounts and to pass an explicit rounding mode. |  |  |
| 17 | Minor | Modules M3, M6; Dependency rule 3; Tests 77 | **The input limits are duplicated.** The range limits live in `V1_RULES` (M3), but the range messages in M6 hard-code `1 000,00 €`, `1 000 000,00 €`, `0,00 %`, `20,00 %` and `1 and 30` (03 "Expected UI texts"), because M6 may not import M3. The M3 extension point "pass a different `rules` table" would then show wrong limits in the error messages. The `ValidationError` could carry `min`/`max`, or the rules table could move into `domain/`. |  |  |
| 18 | Minor | Dependency rules 1 and 5; Module M8; Test 93 | **The dependency rules contradict each other for `ui → domain`.** Rule 1 allows `ui` to import any lower layer. Rule 5 says `ui` talks to the core *only* through `app`, while M8 lists M1 (types) as a dependency. The allow-list for test 93 is therefore not uniquely defined (is `ui/cli → domain/types` legal? `import type` only?). The allow-list should be stated as an explicit table. |  |  |
| 19 | Minor | Tests 74–79, 85, 87, 88, 92; Requirement §3.3, §3.5 | **Some tests assert a contract that no requirement states.** The exact error sentences, labels, CLI prompts, the percent format `0,00 %`, "re-prompt only the invalid fields" and the exit codes 0/1 are defined in 03 ("Expected UI texts") or 02 M8, not in 01. 01 only requires "its own error message, in English". The tests are reasonable, but their traceability column claims FR-3. The texts should be approved by the author and linked to FR-3 / ADR-1, or the column should cite 02/03. |  |  |
| 20 | Minor | Test 85; Requirement §3.1 ("no default values are pre-filled") | **Test 85 cannot fail on the "no pre-filled defaults" part.** The `TerminalIo.ask(question)` port has no way to pass a pre-filled value, so asserting "with no pre-filled values" is trivially true. Either drop the claim and cover the requirement by design review, or assert the exact prompt string (no default shown in brackets, e.g. `Loan amount (EUR) [100000]: `). |  |  |
| 21 | Minor | 03 Coverage Summary | **The traceability in the coverage summary is inflated.** Test 94 (architecture, domain has no I/O) is counted for FR-1 and FR-2, formatting tests 62–65 for FR-1, and test 89 for FR-3 although it uses only valid input. Tests 93 and 95 trace to no requirement ("—"), which is acceptable for architecture tests but should be marked as non-functional instead of being counted. The coverage counts per FR are therefore overstated. Every FR still has genuine tests (FR-1: 43–59, 69–72; FR-2: 43–60, 72–73; FR-3: 1–40, 82–84, 87). |  |  |
| 22 | Minor | Test sources REF-PMT; 03 "Reference sources" | **REF-PMT cannot be reproduced.** The Node float PMT check is described ("agreed … to 9 decimals") but its code is not included, so the claim cannot be checked from the documents. REF-PY is also labelled "Python 3.14", while the appendix says "Python 3.8+". This audit recomputed all values independently (see below), so no value is in doubt, but the reference should be reproducible. |  |  |
| 23 | Minor | Missing scenarios: M2/M3 | Not covered in 03: negative term (`"-5"` → `negative`); whitespace-only input at the M3 level (`"   "` → `required`, so far tested only in M2 test 9); inner space in the term (`"3 0"`); the minimum positive rate at validation level (`"0,01"`, `"0.00"`); leading zeros (`"0001000"`, `"007"` term); very long inputs (e.g. 400 digits, or `"1000,"` followed by 1 000 zeros) for `above_max` / `too_many_decimals` and performance; non-ASCII digits (full-width `１０００`). Hex/`Infinity`/`NaN` are covered by Finding 3, edge separators by 10, signs by 11, NBSP/tab by 12 and `-0` by 9. |  |  |
| 24 | Minor | Missing scenarios: M6/M8/e2e | Not covered in 03: a second consecutive invalid answer for the same field (the re-prompt loop runs more than once); EOF during a re-prompt (not only at the first prompt); Windows CRLF input (`"100000\r\n…"`) in e2e, which matters on the project's Windows environment; whether error lines are printed before the re-prompts and whether the CLI prints the `label` or only the `message` of `FieldErrorView`; a Final Payment that is lower by exactly €0.01 (only higher by €0.01, test 69, and lower by €1.09, test 71, are covered). |  |  |

---

## 1. Coverage Audit (summary)

| 01 requirement | Module(s) in 02 | Tests in 03 | Verdict |
|---|---|---|---|
| FR-1 monthly payment (§4.1, §4.2, §4.4) | M4, M5, M6 | 43–59, 69–72 | Covered, but the §4.4 rule is defective for part of the input domain (#1) |
| FR-2 totals (§4.5) | M4, M5, M6 | 43–60, 72–73 | Covered |
| FR-3 validation (§3.1, §3.3) | M2, M3, M6, M7 | 17–40, 74–84, 87 | Covered, with grammar gaps (#3, #9–#13) |
| §3.1 "no default values" | M8 | 85 (not able to fail) | Weak (#20) |
| §3.2 parsing | M2 | 1–16 | Covered, with ambiguities (#10–#12) |
| §3.4 output format | M5 | 62–68 | Covered |
| §3.5 English | M6 | 74–79 (texts defined only in 03) | Traceability gap (#19) |
| §4.3 rounding | M4 (and M5) | 41–42, 53–54, 59, 67 | Covered, duplicated implementation (#16) |
| Outputs table: show Final only if ≠ | M6 | 69–71, 73, 90 | Covered |

Tests that check no requirement from 01: 93, 95 (architecture rules), 61 (a 02 design choice), 88 and 92 (exit codes from 02). Tests 74–79 and 85 check texts defined only in 03 (#19).

## 2. Reference Value Audit

All financial values in 03 were recomputed with **exact rational arithmetic** (Python `fractions.Fraction`, no precision limit), a different method from REF-PY (60-digit `decimal`). Months were run one by one as in §4.4, and every value was compared exactly to the cent.

| Test | Input | Regular | Final | Total Paid | Interest | Result |
|---|---|---|---|---|---|---|
| 43 / 61 / 72 / 80 / 86 / 89 | 100 000, 3.5 %, 30 y | 449.04 | 452.02 | 161 657.38 | 61 657.38 | ✅ |
| 44 | 200 000, 4.5 %, 25 y | 1 111.66 | 1 114.40 | 333 500.74 | 133 500.74 | ✅ |
| 45 / 71 | 250 000, 6 %, 20 y | 1 791.08 | 1 789.99 | 429 858.11 | 179 858.11 | ✅ |
| 46 | 50 000.55, 2.25 %, 7 y | 643.91 | 643.62 | 54 088.15 | 4 087.60 | ✅ |
| 47 / 70 / 73 | 10 000, 3.25 %, 5 y | 180.80 | 180.80 | 10 848.00 | 848.00 | ✅ |
| 48 / 69 | 10 000, 2.5 %, 1 y | 844.66 | 844.67 | 10 135.93 | 135.93 | ✅ |
| 49 | 10 000, 5 %, 1 y | 856.07 | 856.13 | 10 272.90 | 272.90 | ✅ |
| 50 | 1 000, 0.01 %, 1 y | 83.34 | 83.31 | 1 000.05 | 0.05 | ✅ |
| 51 / 64 | 1 000 000, 20 %, 30 y | 16 710.19 | 16 638.10 | 6 015 596.31 | 5 015 596.31 | ✅ |
| 52 | 1 000, 20 %, 30 y | 16.71 | 21.00 | 6 019.89 | 5 019.89 | ✅ |
| 53 | 150 000, 2 %, 20 y | 758.83 | 757.36 | 182 117.73 | 32 117.73 | ✅ |
| 54 | 100 000, 1.5 %, 10 y | 897.91 | 898.56 | 107 749.85 | 7 749.85 | ✅ |
| 55 / 90 | 120 000, 0 %, 10 y | 1 000.00 | 1 000.00 | 120 000.00 | 0.00 | ✅ |
| 56 / 81 | 1 000, 0 %, 1 y | 83.33 | 83.37 | 1 000.00 | 0.00 | ✅ |
| 57 | 1 000, 0 %, 30 y | 2.78 | 1.98 | 1 000.00 | 0.00 | ✅ |
| 58 | 1 000 000, 0 %, 30 y | 2 777.78 | 2 776.98 | 1 000 000.00 | 0.00 | ✅ |
| 59 | 1 000.14, 0 %, 1 y | 83.35 | 83.29 | 1 000.14 | 0.00 | ✅ |
| 91 | 1 000.50, 2.5 %, 10 y | 9.43 | 9.66 | 1 131.83 | 131.33 | ✅ |

Other checks:
- **Unrounded M claims:** 43 (449.044687…, appendix 449.0446878088…), 45 (1791.077646…), 53 (758.825002567…), 54 (897.914997950…) are all correct. Test 59: M = 83.345 exactly, and half-even would give 83.34, as stated.
- **`roundToCents` / `formatMoney` rounding (tests 41, 42, 67):** all 11 values are correct.
- **Note on the Layer 3 prompt example:** confirmed. With Final = 449.04, the loan would be under-repaid by €2.978…, so 452.02 is correct under §4.4.
- **Test 61 discriminates:** with global precision 5 and `ROUND_DOWN`, M would compute as 450.49, so the test detects a module that uses the global Decimal config.
- **Invariants (test 60)** hold for all 18 reference inputs. They do **not** hold across the valid domain (Finding 1).
- **40-digit precision (02 ADR-3)** vs exact: 0 mismatches in the 18 reference cases + 300 random valid inputs (Finding 14).

**Result: 0 of 18 reference scenarios are wrong.** Every financial value in 03 is correct under the rules as written. The defect is in the rule (Finding 1), not in the reference values.

---

## Appendix — Verification scripts

Run with Python 3.8+ and Node.js 24. No third-party packages are needed. The scripts were run on 2026-10-21 (Python 3.14.3, Node 24.20.0).

### A. `verify.py` — recompute all reference values (exact rationals)

```python
from fractions import Fraction as F
from decimal import Decimal, getcontext, ROUND_HALF_EVEN, ROUND_DOWN
import math

def rhu(x):                      # round half up (away from zero) to cents, exact
    c = x * 100; s = -1 if c < 0 else 1; c = abs(c); fl = math.floor(c)
    return F(s * (fl + (1 if c - fl >= F(1, 2) else 0)), 100)

def calc(P, rate, years):
    P, rate = F(P), F(rate); n = years * 12; r = rate / 12 / 100
    if r > 0:
        g = (1 + r) ** n; M = P * r * g / (g - 1)
    else:
        M = P / n
    Mr = rhu(M); B = P
    for _ in range(n - 1):       # §4.4 month-by-month, no rounding
        B = B * (1 + r) - Mr
    fin_exact = B * (1 + r); fin = rhu(fin_exact); total = Mr * (n - 1) + fin
    return dict(n=n, M=M, regular=Mr, final=fin, total=total, interest=total - P,
                residual=fin_exact - fin)

cases = {  # test: (P, rate, years, regular, final, total paid, interest) as written in 03
 43: ('100000','3.5',30,'449.04','452.02','161657.38','61657.38'),
 44: ('200000','4.5',25,'1111.66','1114.40','333500.74','133500.74'),
 45: ('250000','6',20,'1791.08','1789.99','429858.11','179858.11'),
 46: ('50000.55','2.25',7,'643.91','643.62','54088.15','4087.60'),
 47: ('10000','3.25',5,'180.80','180.80','10848.00','848.00'),
 48: ('10000','2.5',1,'844.66','844.67','10135.93','135.93'),
 49: ('10000','5',1,'856.07','856.13','10272.90','272.90'),
 50: ('1000','0.01',1,'83.34','83.31','1000.05','0.05'),
 51: ('1000000','20',30,'16710.19','16638.10','6015596.31','5015596.31'),
 52: ('1000','20',30,'16.71','21.00','6019.89','5019.89'),
 53: ('150000','2',20,'758.83','757.36','182117.73','32117.73'),
 54: ('100000','1.5',10,'897.91','898.56','107749.85','7749.85'),
 55: ('120000','0',10,'1000.00','1000.00','120000.00','0.00'),
 56: ('1000','0',1,'83.33','83.37','1000.00','0.00'),
 57: ('1000','0',30,'2.78','1.98','1000.00','0.00'),
 58: ('1000000','0',30,'2777.78','2776.98','1000000.00','0.00'),
 59: ('1000.14','0',1,'83.35','83.29','1000.14','0.00'),
 91: ('1000.50','2.5',10,'9.43','9.66','1131.83','131.33'),
}
fails = 0
for t, (P, rate, y, *exp) in cases.items():
    res = calc(P, rate, y)
    got = [res['regular'], res['final'], res['total'], res['interest']]
    ok = all(g == F(e) for g, e in zip(got, exp)); fails += not ok
    print(t, 'OK' if ok else 'FAIL', [float(g) for g in got], 'residual', float(res['residual']))
    assert res['final'] > 0 and res['interest'] >= 0 and abs(res['residual']) <= F(1, 200)
    if F(rate) == 0:
        assert res['interest'] == 0 and res['final'] == F(P) - res['regular'] * (res['n'] - 1)

for v, e in [('2.345','2.35'),('1.005','1.01'),('2.675','2.68'),('0.125','0.13'),('0.005','0.01'),
             ('2.344999','2.34'),('0.004999','0.00'),('897.914997950','897.91'),
             ('1234.565','1234.57'),('1234.564999','1234.56'),('1234.567','1234.57')]:
    ok = rhu(F(v)) == F(e); fails += not ok; print('round', v, 'OK' if ok else 'FAIL')

print('T59 half-even:', Decimal('83.345').quantize(Decimal('0.01'), ROUND_HALF_EVEN))
print('Underpayment if final=449.04:', float(calc('100000','3.5',30)['final'] - F('449.04')))
getcontext().prec = 5; getcontext().rounding = ROUND_DOWN
P = Decimal(100000); rr = Decimal('3.5') / 12 / 100; g = (1 + rr) ** 360
print('T61 global prec-5 M:', P * rr * g / (g - 1))
print('FAILURES:', fails)
```

Output (abridged): all 18 cases `OK`, all 11 rounding checks `OK`, `T59 half-even: 83.34`, `Underpayment if final=449.04: 2.98` (exact unrounded shortfall: 2.9786934608…), `T61 global prec-5 M: 450.49`, `FAILURES: 0`.

### B. `edge.py` — search the valid domain for negative final payments (Finding 1) and check 40-digit precision (Finding 14)

```python
from fractions import Fraction as F
from decimal import Decimal as D, Context, ROUND_HALF_UP
import math, random

def rhu(x):
    c = x * 100; s = -1 if c < 0 else 1; c = abs(c); fl = math.floor(c)
    return F(s * (fl + (1 if c - fl >= F(1, 2) else 0)), 100)

def closed(P, r, n):             # exact remaining balance before payment n, times (1+r)
    P = F(P)
    if r == 0:
        M = P / n; Mr = rhu(M); return M, Mr, P - Mr * (n - 1)
    g = (1 + r) ** n; M = P * r * g / (g - 1); Mr = rhu(M); h = (1 + r) ** (n - 1)
    return M, Mr, (P * h - Mr * (h - 1) / r) * (1 + r)

for rate in ['20', '15', '12', '10', '8']:
    for years in [30, 25, 20]:
        rr, nn = F(rate) / 1200, years * 12
        fins = [closed(F(c, 100), rr, nn)[2] for c in range(100000, 110000)]  # P 1000.00–1099.99
        print(rate, years, 'final<=0:', sum(rhu(f) <= 0 for f in fins), 'min:', float(min(fins)))

P = F('1000.29'); r = F(20) / 1200; n = 360
g = (1 + r) ** n; M = P * r * g / (g - 1); Mr = rhu(M); B = P
for k in range(1, n):
    B = B * (1 + r) - Mr
fin = rhu(B * (1 + r)); tot = Mr * (n - 1) + fin
print('P=1000.29 20% 30y:', float(Mr), float(fin), float(tot), float(tot - P))

ctx = Context(prec=40, rounding=ROUND_HALF_UP); random.seed(1); mism = 0
for _ in range(300):
    Pc, rc, years = random.randint(100000, 100000000), random.randint(0, 2000), random.randint(1, 30)
    P, rate, nn = F(Pc, 100), F(rc, 100), years * 12
    _, Mr, fe = closed(P, rate / 1200, nn)
    Pd = D(Pc) / 100; rd = ctx.divide(ctx.divide(D(rc) / 100, 12), 100)
    if rd > 0:
        gd = ctx.power(ctx.add(1, rd), nn)
        Md = ctx.divide(ctx.multiply(ctx.multiply(Pd, rd), gd), ctx.subtract(gd, 1))
    else:
        Md = ctx.divide(Pd, nn)
    Mrd = Md.quantize(D('0.01'), rounding=ROUND_HALF_UP); B = Pd
    for _ in range(nn - 1):
        B = ctx.subtract(ctx.multiply(B, ctx.add(1, rd)), Mrd)
    fd = ctx.multiply(B, ctx.add(1, rd)).quantize(D('0.01'), rounding=ROUND_HALF_UP)
    mism += F(str(Mrd)) != Mr or F(str(fd)) != rhu(fe)
print('40-digit vs exact mismatches:', mism)
```

Output: see Finding 1 (e.g. `20 30 final<=0: 4234 min: -97.95…`, `8 30 final<=0: 5 min: -0.06…`, all 20-year terms `0`), `P=1000.29 20% 30y: 16.72 -97.42 5905.06 4904.77`, `40-digit vs exact mismatches: 0`.

### C. `rl.mjs` — Node readline/promises with piped stdin (Finding 2)

```js
import * as readline from 'node:readline/promises';
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
let closed = false; rl.on('close', () => { closed = true; });
const ask = async (q) => (closed ? undefined : rl.question(q));
const a = [];
for (const q of ['Q1: ', 'Q2: ', 'Q3: ', 'Q4: ']) a.push(await ask(q));
console.log('\nANSWERS', JSON.stringify(a));
rl.close();
```

`printf '100 000\n3,5\n30\n' | node rl.mjs` → prints `Q1: Q2:`, then "Warning: Detected unsettled top-level await", exit code **13**. Answers 2 and 3 are lost, and the pending question never resolves on EOF.

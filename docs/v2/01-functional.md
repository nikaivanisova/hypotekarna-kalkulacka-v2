# 01 — Functional Definition (V2)

Status: **Approved** (2026-10-22), from the decisions in [`00-refactor-plan.md`](00-refactor-plan.md) §8.

V2 is the V1 calculator as a **web app**, with each successful calculation saved to a database. **The calculation does not change.** This document lists only what differs from [`../v1/01-functional.md`](../v1/01-functional.md); everything not mentioned here applies unchanged.

---

## 1. Unchanged from V1

| V1 section | Content | V2 |
|---|---|---|
| §1 | Target user and core purpose | Unchanged. |
| §2 FR-1, FR-2, FR-3 | Payment, totals, validation | Unchanged. |
| §3.1 | Input fields and limits | Unchanged. |
| §3.2 | Number parsing (strict grammar) | Unchanged. Applied by the backend only (D3). |
| §3.3 | Invalid input | Unchanged rules and error codes. |
| §3.4 | Money format `1 234,57 €` | Unchanged; applied by the frontend to the API's 2-dp strings. |
| §3.5 | Language: English | Unchanged (D8). |
| §4 | Domain rules (formula, rounding, final payment, early termination, totals) | **Unchanged, cent for cent.** Every V1 expected value must be reproduced by the Python backend. |

## 2. What changes

### 2.1 Platform

- A web page replaces the interactive CLI. It has three input fields (Loan amount (EUR), Annual interest rate (%), Term (years)) and a **Calculate** button. No values are pre-filled.
- The page sends the text exactly as typed to the backend API ([`00-refactor-plan.md`](00-refactor-plan.md) §3). The browser does no parsing, validation or rounding.
- **Valid input:** the page shows the same result lines as V1, with the same labels and the same "show Final Payment only if it differs by ≥ €0.01" rule.
- **Invalid input:** the page shows the V1 error message under each invalid field and no results. The typed values stay in the fields so the user can correct them. (This replaces the CLI's "ask again for the invalid fields".)
- **Backend unreachable:** the page shows one general error message and no results.

### 2.2 New requirement

| ID | Short name | Rule |
|---|---|---|
| FR-4 | Save calculation | Every successful calculation is saved in Supabase: the validated inputs, the results, and the time. Calculations are anonymous (D9). If saving fails, the result is still shown (D5). The user cannot list, reload or delete saved calculations in V2. |

### 2.3 Out of scope for V2

Everything in V1 §5 stays out of scope, except that results are now **stored** (FR-4). Still out of scope, among others:

- Extra or one-off payments (*mimoriadna splátka*) — decided D7.
- A repayment schedule, variable rates, fees, comparisons, affordability checks.
- User accounts and login (D9); viewing, exporting or sharing saved calculations.

## 3. Open questions carried over from V1

These were open at the end of V1 (`docs/v1/06-retro.md` §2.3). **For the port, the V1 behaviour is kept exactly**, so that Phase 2 can prove parity. Changing any of them is a separate, later decision.

| Question | V2 behaviour (same as V1) |
|---|---|
| Review findings #7–#24 (`docs/v1/04-review.md`), e.g. `-0` (#9), NBSP inside numbers (#12), term `"10,0"` (#13) | As built in V1: `-0` → `negative`; only U+0020 spaces are removed inside a number; term `"10,0"` → `too_many_decimals` (V1 validation test, line 107). |
| The sub-half-cent tail rule (V1 01 §4.4 step 3) | Kept; guarded by the ported test 106 and the sweep. |
| Show the number of payments when a loan ends early? | Not shown on the page (as in V1). The API already returns `numberOfPayments`, so it can be shown later without a backend change. |

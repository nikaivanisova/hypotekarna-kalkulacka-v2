# 01 — Functional Definition (V1)

Status: **Approved** (2026-10-20). Revised 2026-10-21 after the independent review ([`04-review.md`](04-review.md) findings #1 and #3): early loan termination (section 4.4) and strict number grammar (section 3.2).

V1 is a calculator for a **fixed-rate annuity mortgage** with monthly payments. Anything beyond that is out of scope (see section 5).

---

## 1. Target User and Core Purpose

> A consumer who wants to know the fixed monthly payment, total amount paid and total interest for a fixed-rate annuity mortgage, given a loan amount, interest rate and term.

---

## 2. Functional Requirements

| ID | Short name | Inputs | Outputs | Calculation rule |
|---|---|---|---|---|
| FR-1 | Calculate monthly payment | Loan amount, annual interest rate, term (years) | Regular Monthly Payment; Final Payment (only if different) | Annuity formula (section 4.2); final payment absorbs the rounding difference, and the loan may end before month n (section 4.4) |
| FR-2 | Calculate totals | Same as FR-1 | Total Paid, Total Interest | Total Paid = Regular Payment × (k − 1) + Final Payment, where k ≤ n is the number of payments made (section 4.5); Total Interest = Total Paid − Loan Amount |
| FR-3 | Validate inputs | Same as FR-1 | Error message per invalid or missing field | No calculation runs until all inputs pass validation (section 3.3) |

### Outputs

| Output | Shown when | Format |
|---|---|---|
| Regular Monthly Payment | Always (after a valid calculation) | Money (section 3.4) |
| Final Payment | Only if it differs from the regular payment by €0.01 or more | Money |
| Total Paid | Always | Money |
| Total Interest | Always | Money |

---

## 3. Inputs and Boundaries

### 3.1 Input fields

| Input | Unit | Required | Min (inclusive) | Max (inclusive) | Format |
|---|---|---|---|---|---|
| Loan amount (P) | EUR (€) | Yes | 1 000,00 | 1 000 000,00 | Up to 2 decimal places |
| Annual interest rate | % per year, nominal, compounded monthly | Yes | 0,00 | 20,00 | Up to 2 decimal places |
| Term | Years | Yes | 1 | 30 | Whole numbers only |

- All three inputs are required.
- No default values are pre-filled.

### 3.2 Number input parsing

- Both `.` and `,` are accepted as the decimal separator, so `1000.50` and `1000,50` are equivalent.
- Spaces inside a number are ignored and treated as thousands separators: `1 000,50` → `1000.50`.
- A number may contain at most one decimal separator. `,` and `.` are never treated as thousands separators.
- Leading and trailing whitespace is ignored.
- **Strict grammar.** After trimming and removing inner spaces, the text must match the regular expression `^-?[0-9]+([.,][0-9]+)?$`: an optional leading `-`, one or more ASCII digits, and optionally one decimal separator followed by one or more digits. This check runs **before** the text is converted to a number. Anything that does not match is not a number (section 3.3), in particular:
  - hexadecimal, binary or octal notation (`0x3E8`, `0b1010`, `0o17`),
  - exponent notation (`1e5`, `1E5`, `2,5e3`),
  - `NaN`, `Infinity`, `-Infinity`,
  - a separator without digits on both sides (`1000,`, `,50`, `.5`),
  - any sign other than a leading `-` (`+30`, `−5000` with U+2212).

### 3.3 Invalid input

An input is invalid if it is:

- empty or missing,
- not a number after parsing (section 3.2), i.e. not matching the strict grammar, including values with more than one decimal separator (e.g. `1,000.50`),
- negative,
- outside its min–max range,
- written with more decimal places than allowed,
- (for the term) not a whole number.

Behaviour on invalid input:

- Each invalid or missing field shows its own error message, in English.
- No calculation runs, and no results are shown, until all inputs are valid.

### 3.4 Output format

- Money is displayed in Slovak/EU style: space as the thousands separator, comma as the decimal separator, always 2 decimal places, and `€` after the number with a space.
  Example: `1 234,57 €`.

### 3.5 Language

- UI text and error messages are in **English**, to match test scenarios and code documentation.

---

## 4. Domain Rules

### 4.1 Derived values

- Number of payments: **n = years × 12**
- Monthly interest rate: **r = annual interest rate ÷ 12 ÷ 100**

### 4.2 Regular monthly payment

- If r > 0: **M = P × r × (1 + r)ⁿ / ((1 + r)ⁿ − 1)**
- If r = 0: **M = P ÷ n**
- The regular payment shown and charged is **M rounded to cents**.

### 4.3 Rounding

- Method: **round half up** (e.g. 2.345 → 2.35).
- All intermediate values keep **full precision**, including the internal month-by-month interest and balance calculation.
- Only the output amounts are rounded to cents: Regular Monthly Payment, Final Payment, Total Paid, Total Interest.

### 4.4 Final payment (last payment behaviour)

The final payment absorbs all rounding differences, so the loan balance ends at **€0.00** (to the cent). This applies to every rate, including 0%.

Calculation (internal only, the schedule is never displayed):

1. Start with balance B = P (full precision).
2. For each month k = 1, 2, …, n, compute the **amount due** D = B × (1 + r): the remaining balance plus the interest accrued in that month (full precision, no intermediate rounding).
   - If k = n, **or** D ≤ M_rounded (the regular payment would bring the balance to €0.00 or below), month k is the **last active month**. The Final Payment is D, rounded to cents, and the loan ends. Any remaining months are skipped (**early termination**).
   - Otherwise, the regular payment is made: B = D − M_rounded, and the next month follows.
3. If the Final Payment from step 2 rounds to €0.00 (D < €0.005), month k is not a payment month. The payment of month k − 1 (M_rounded) is the Final Payment, and the loan ends at month k − 1.

The number of payments actually made is **k ≤ n**.

**Why a loan can end early.** M_rounded is used for every month, so its rounding difference compounds with interest. When M is rounded **up** at a high rate and a long term, the accumulated overpayment repays the loan before month n. Example: P = 1 000.29, 20 %, 30 years → M_rounded = 16.72, and the loan ends at month 354 with a Final Payment of 8.08. Without early termination, the month-360 payment would be negative (−97.42).

**Properties of the result:**
- The Final Payment is always **> €0.00**.
- If the loan ends early (k < n), the Final Payment is **≤ M_rounded**.
- If the loan runs the full term (k = n), the Final Payment may be higher or lower than M_rounded.
- For r = 0 the loan always runs the full term, and the rule reduces to: Final Payment = P − M_rounded × (n − 1).

### 4.5 Totals

- **Total Paid = M_rounded × (k − 1) + Final Payment**, where k is the number of payments made (section 4.4). This equals the sum of all payments.
- **Total Interest = Total Paid − P**

---

## 5. Out of Scope for V1

| Feature | Reason |
|---|---|
| Month-by-month repayment schedule | Consumers don't need it; V1 shows only the payment and totals. |
| Extra or one-off payments | These change the balance mid-term and need recalculation logic beyond a fixed annuity. |
| Variable or adjustable interest rates | V1 is limited to one fixed rate for the whole term. |
| Fees, insurance, taxes (e.g. origination fees, APR/RPMN) | These need extra inputs and different rules that a basic payment calculation doesn't cover. |
| Payment frequencies other than monthly | Monthly payments fit the consumer use case and keep the formula fixed. |
| Multiple currencies | Only EUR is supported, so no currency conversion or formatting rules are needed. |
| Comparing loans or scenarios side by side | It's a separate feature on top of the core calculation. |
| Saving, exporting or sharing results | It needs storage or file output, and V1 is a stateless calculator. |
| Affordability checks (income or debt ratios) | They need personal financial inputs and lending rules outside a payment calculator. |

---

## 6. Open Questions

| # | Question | Status |
|---|---|---|
| OQ-1 | Platform / UI (web page, desktop app, or command line), which also determines how error messages are displayed. | Deferred to Layer 2 (Architecture) |

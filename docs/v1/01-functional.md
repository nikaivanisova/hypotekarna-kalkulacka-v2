# 01 — Functional Definition (V1)

Status: **Approved** (2026-10-20)

V1 is a calculator for a **fixed-rate annuity mortgage** with monthly payments. Anything beyond that is out of scope (see section 5).

---

## 1. Target User and Core Purpose

> A consumer who wants to know the fixed monthly payment, total amount paid and total interest for a fixed-rate annuity mortgage, given a loan amount, interest rate and term.

---

## 2. Functional Requirements

| ID | Short name | Inputs | Outputs | Calculation rule |
|---|---|---|---|---|
| FR-1 | Calculate monthly payment | Loan amount, annual interest rate, term (years) | Regular Monthly Payment; Final Payment (only if different) | Annuity formula (section 4.2); final payment absorbs the rounding difference (section 4.4) |
| FR-2 | Calculate totals | Same as FR-1 | Total Paid, Total Interest | Total Paid = Regular Payment × (n − 1) + Final Payment; Total Interest = Total Paid − Loan Amount |
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

### 3.3 Invalid input

An input is invalid if it is:

- empty or missing,
- not a number after parsing (section 3.2), including values with more than one decimal separator (e.g. `1,000.50`),
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

The final payment absorbs all rounding differences, so the loan balance ends at exactly **€0.00**. This applies to every rate, including 0%.

Calculation (internal only, the schedule is never displayed):

1. Start with balance B = P (full precision).
2. For months 1 … n − 1: B = B × (1 + r) − M_rounded (no intermediate rounding).
3. Final Payment = B × (1 + r), rounded to cents.

For r = 0 this reduces to: Final Payment = P − M_rounded × (n − 1).

### 4.5 Totals

- **Total Paid = M_rounded × (n − 1) + Final Payment**
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

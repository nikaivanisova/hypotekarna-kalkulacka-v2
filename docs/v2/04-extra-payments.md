# 04 — Extra Payments (FR-5, Phase 7)

Status: **Approved by the author** (Prompt 47, 2026-10-28). Reviewed; all findings applied. The decisions in §1 are the author's (Prompts 45–46). Independent review: [`05-extra-payments-review.md`](05-extra-payments-review.md). No code is written before the author approves this document.

An extra payment (*mimoriadna splátka*) is a one-time payment on top of the regular monthly payment. It **shortens the term**, and the regular monthly payment does not change (D7). Without extra payments, every result is **exactly** the V1 result (V1 01 §4); this is tested.

---

## 1. Decisions (author)

| # | Question | Decision |
|---|---|---|
| X1 | Kind | **One-time** payments only (no recurring). |
| X2 | How many | **0 to 10** per loan. |
| X3 | Fee | **None** (fees stay out of scope, as in V1 §5). |
| X4 | Timing | Paid **together with month k's regular payment**, after month k's interest is charged. |
| X5 | Larger than what is owed | It **pays the loan off**: only what is owed is used (to the cent). The result shows the amount actually used; later extra payments are listed as **not used**. |
| X6 | Amount | **0,01 € to 1 000 000,00 €**, at most 2 decimals, V1 number format. |
| X7 | Same month | **Allowed; the amounts add up.** |
| X8 | Months | **1 to term × 12** (any month of the original term). |
| X9 | Extra outputs | **New loan length**, **time saved**, **interest saved** (the sum of extra payments is *not* shown). |
| X10 | Extra in a month where the loan ends anyway (month n, or V1's own early ending) | **Not needed**: 0,00 € used, with its own note (Prompt 46; review finding 4). |

---

## 2. Inputs

The three V1 inputs are unchanged. New optional input: a list of **0–10 extra payments**, each with:

| Input | Unit | Min | Max | Format and checks (V1 rules) |
|---|---|---|---|---|
| Month | month of the loan, 1 = first payment | 1 | term × 12 | whole number, as the V1 term: `"2,5"` → `not_whole_number`, `"24,0"` → `too_many_decimals` |
| Amount | EUR | 0,01 | 1 000 000,00 | up to 2 decimals, as the V1 loan amount |

- Both are parsed with the V1 grammar (V1 01 §3.2: spaces, `.` or `,`, the strict pattern). They are validated in the V1 order of checks: `required` → `not_a_number` → `negative` → `not_whole_number` → `too_many_decimals` → `below_min` / `above_max`. No new error codes are needed.
- **Month maximum.** When the term is valid, the month maximum is term × 12. When the term is invalid, the month is checked against 1–360 (the largest possible term), and the term's own error is reported. A month above a valid term × 12 gets `above_max`.
- **Request shape (malformed → `400`, not `422`):**
  - `extraPayments` may be absent, `null` or `[]`, which all mean "no extra payments".
  - Otherwise it must be an array of at most 10 items.
  - Each item must be an object with only the properties `month` and `amount`. Each property is a RawInput: a string of at most 100 characters, or `null`.
  - A non-array, more than 10 items, an item that is not an object, an unknown property in an item, or a non-string value is a `400`.
  - Inside an item, an absent, `null`, empty or whitespace-only property gives `required`. So `{}` gives two `required` errors.
- **Blank rows (frontend).** A form row whose month and amount are both empty after JavaScript `trim` (the same whitespace set as V1's `required`) is not sent. The frontend keeps a map from each sent index to its form row, and uses it for errors and notes (review finding 5).
- Nothing is calculated while any input is invalid (FR-3 unchanged).

---

## 3. Domain rules

### 3.1 Definitions

V1 values, unchanged: n = term × 12, r = annual rate ÷ 12 ÷ 100, **M** = the regular payment rounded to cents (V1 §4.2). M **never changes** because of extra payments (D7).

**X_k** = the sum of all extra amounts with month k (X7), or 0. Extra amounts are exact cents.

### 3.2 Month-by-month run

Start with balance B = P (full precision). For k = 1, 2, …, n:

1. Amount due **D = B × (1 + r)** (full precision, as in V1 §4.4).
2. **Schedule ending:** if k = n, or D ≤ M, month k is the last month. This is V1's own rule, including V1's early termination. Extra payments in this month are **not needed** (X10).
3. **Extra ending:** otherwise, if D ≤ M + X_k, the extra payments pay the loan off in month k.
4. Otherwise the borrower pays M + X_k: **B = D − M − X_k**, and the next month follows.

In the last month k (ending 2 or 3), the payment is **Final = D rounded to cents** (half up). It absorbs all rounding, as in V1. In an extra ending, Final is the regular payment plus the extra actually used that month. Final − M lies in [0,00, X_k].

**Zero tail (V1 §4.4 step 3, unchanged):**
- If Final rounds to 0,00 € (D < 0,005 €), month k is not a payment month.
- The payment of month k − 1, which is M + X_{k−1}, is then the final payment, and the loan ends in month k − 1.
- This happens when the balance after month k − 1 is so small that B × (1 + r) < 0,005 €. With extra payments, that can follow an extra payment, or a regular payment after earlier extra payments.

The number of payments actually made is **K** (K ≤ n).

### 3.3 Extra payments actually used, and their status

Used amount per month m:

| Month m | Used in that month |
|---|---|
| m < K | all of X_m |
| m = K, zero tail | all of X_m |
| m = K, extra ending | Final − M |
| m = K, schedule ending | 0,00 (X10) |
| m > K | 0,00 |

If a month has several items (X7), its used amount goes to the items **in request order**: each item takes as much as is left, up to its own amount ("the first one entered is used first"). Each item gets a **usedAmount** between 0,00 € and its amount, in whole cents, and exactly one **status**:

| Status | When | Meaning for the user |
|---|---|---|
| `used` | usedAmount = amount | fully used |
| `partly_used` | 0 < usedAmount < amount | only part was needed to pay off the loan |
| `after_payoff` | usedAmount = 0 and m > K | the loan was already paid off |
| `loan_ends_this_month` | usedAmount = 0, m = K, schedule ending | not needed: this month's normal payment ends the loan |
| `tiny_balance` | usedAmount = 0, m = K, extra ending with Final = M | not needed: less than half a cent was still owed after the regular payment |
| `covered_by_earlier` | usedAmount = 0, m = K, extra ending with Final > M | not needed: an earlier extra payment in the same month already paid off the loan |

**`tiny_balance` still has an effect** (review finding 1). In an extra ending, a remainder below half a cent is written off in month K, where V1 would carry it into month K + 1. So the loan can end one month earlier, and up to 0,01 € of interest can be saved, even when every item in month K is `tiny_balance`. Example E9 shows this.

### 3.4 Totals

- **Total Paid** = M × (K − 1) + (sum of X_m for m < K) + Final. This equals the sum of all payments made.
- **Total Interest** = Total Paid − P.
- **Months saved** = K₀ − K, where K₀ is the number of payments of the same loan without extra payments (V1).
- **Interest saved** = Total Interest₀ − Total Interest, where ₀ is the same loan without extra payments.
- Rounding (CLAUDE.md): the run keeps full precision. Only M (V1 §4.2) and Final are rounded to cents, half up. Every other output is a sum or difference of cent amounts, so all outputs are exact cents.

### 3.5 Properties

Claimed, and checked for every loan in the sweep below:

1. Without extra payments, every output equals V1 exactly, and months saved = interest saved = 0.
2. Regular payment = V1's M; Final > 0; 1 ≤ K ≤ K₀ (so months saved ≥ 0).
3. **The loan is paid off.** Rebuilding the balance from P with full-precision interest, minus the actual payments, ends in [−0,005 €, 0,005 €). This rebuild is independent of the Total Paid formula.
4. Total Paid = the sum of the payments; Total Interest = Total Paid − P ≥ 0.
5. **Interest saved ≥ 0** for every valid input (review finding 3). Proof:
   - Write Total Interest = I + e. I is the full-precision interest charged. e is the last payment's rounding: Final − D, or −D in a zero tail. So e ∈ (−0,005, 0,005].
   - By induction, every balance with extra payments is ≤ the balance without them: B′ = D′ − M − X ≤ D − M.
   - The run with extra payments also ends no later: when V1 ends in month k, D′ ≤ D ≤ M.
   - So I′ ≤ I₀, and interest saved = (I₀ − I′) + (e₀ − e′) > −0,01 €. Interest saved is a whole number of cents, so it is ≥ 0. The same argument gives Total Interest ≥ 0.
6. In an extra ending, Final − M ∈ [0, X_K], and the items of month K use exactly Final − M in total. In a zero tail, Final = M + X_K.
7. The used amounts are split greedily in request order; usedAmount is in whole cents and 0 ≤ usedAmount ≤ amount. Every status follows the §3.3 table.

**Reference and sweep.** `tools/reference.py` implements §3.2–3.4 with exact rational arithmetic (`calc_extra`). `check_extra_sweep` checks properties 1–7 on 3 200 seeded loans in 8 strata. Cases the random sweep would almost never reach are built on purpose:

| Stratum | Content | Loans |
|---|---|---|
| no extras (×2) | must equal V1 | 800 |
| random | 1–10 random extras | 400 |
| 0 % | random extras plus an **exact pay-off** (D = M + X is reachable only at 0 %) | 400 (320 exact) |
| zero tail | one item that leaves less than half a cent owed | 400 |
| zero tail, several items | the zero-tail extra split into 3 items, after earlier extras | 399 (149 split, 250 after earlier extras) |
| tiny balance | an extra that leaves D within half a cent above M next month, plus an item in that month | 400 |
| covered by earlier | a pay-off month with several items, plus random ones | 400 |

Result: **0 violations**, every ending (schedule 217, extra 1 383, zero tail 799) and every status occurs, and E1–E12 match.

**The sweep itself is mutation-tested** (review finding 2). Each mutation of `calc_extra` must make the sweep fail on its own, without the examples. See `05-extra-payments-review.md` for the list and results.

---

## 4. Outputs

### 4.1 API (`POST /api/v1/calculations`, additive, stays `/api/v1`)

**Request:** optional `extraPayments`, shape as in §2.

**Result (`200`):** new properties, always present (also without extra payments):

| Property | Type | Meaning |
|---|---|---|
| `monthsSaved` | integer ≥ 0 | K₀ − K |
| `interestSaved` | Money (≥ 0, §3.5 property 5) | Total Interest₀ − Total Interest |
| `extraPayments` | array, request order | one `{ "month": integer, "amount": Money, "usedAmount": Money, "status": string }` per request item (validated values) |

- `numberOfPayments` is K. `totalPaid`, `totalInterest` and `finalPayment` follow §3.4. `regularPayment` is unchanged.
- `status` is an **open vocabulary**: the six values of §3.3 today. A client shows a generic note for a status it does not know (the contract's forward-compatibility rule).

**Validation errors (`422`):**
- Item errors use `field: "extraPayments"`, `index` (0-based, in the request), and a new **`property`** (`"month"` or `"amount"`). `index` and `property` are **required** when `field` is `extraPayments`. A client shows the general message if either is missing or unknown.
- Order: the three V1 fields first, then items by index, month before amount. There is at most one error per (field, index, property).

```json
{ "errors": [ { "field": "extraPayments", "index": 1, "property": "amount", "code": "too_many_decimals" } ] }
```

**Body limit: 8 KiB** (raised from 1 KiB). The form can send 23 text fields of up to 100 characters (3 V1 fields and 10 items × 2). Sizes measured by the reviewer:
- plain ASCII: 2 616 bytes;
- 100 × `"` or `\` per field, escaped by `JSON.stringify`: 4 916 bytes;
- 100 × `€` per field (3 bytes in UTF-8): 7 216 bytes, which is the most the form can send. The browser's `maxlength` counts UTF-16 units, and one unit is at most 3 bytes in UTF-8.

So 8 KiB covers every request the form can produce. Larger bodies are not from the form and get `413`. Control characters escaped as `\uXXXX` (up to 14 116 bytes) can't be typed into a text field.

**Contract text that changes** (review finding 11; the contract change is reviewed in build step 2):
- 1 KiB → 8 KiB in `info.description` and in `PayloadTooLarge`.
- "At most one error per input" → one per (field, index, property).
- "Until then, sending it is a 400" → the `extraPayments` request schema.
- `totalPaid` description → "the sum of all payments made".
- `CalculationResult.required` gains `monthsSaved`, `interestSaved` and `extraPayments`.
- `ValidationError` gains `property`; `index` and `property` are required for `field: extraPayments`.

### 4.2 Page

**Form:**
- A section **"Extra payments (optional)"** under the three fields, with an **"Add extra payment"** button (up to 10 rows). Each row has **Month** and **Amount (EUR)** fields (`maxlength="100"`) and a **Remove** button.
- Help text: "If several extra payments are in the same month, the first one entered is used first."
- Blank rows are not sent (§2).

**Result:**
- Without extra payments, the result is exactly the V1 view. The extra lines appear when the response's `extraPayments` is not empty.
- `Final Payment` keeps its V1 label and V1 show/hide rule. In an extra or zero-tail ending it includes the extra used that month, e.g. E2: 90 146,42 €.
- With extra payments, after the V1 lines:
  - `Loan paid off after: 27 years 8 months (332 payments)`
  - `Time saved: 2 years 4 months`, or `Time saved: none` when months saved is 0
  - `Interest saved: 7 778,30 €`
- **Durations** come from the integers `numberOfPayments` and `monthsSaved`, as years = ⌊m ÷ 12⌋ and months = m mod 12:
  - Singular and plural: `1 year`, `2 years`, `1 month`, `2 months`.
  - A zero part is left out: `5 years`, `11 months`.
  - 12 months is `1 year`.
  - Payments: `(1 payment)`, `(332 payments)`.
- **One note per item that is not `used`.** `<m>` is the month and `<a>` the amount. The page compares nothing and does no arithmetic on money: it shows `status`, `usedAmount` and `amount` as received.

  | Status | Note |
  |---|---|
  | `partly_used` | `Extra payment in month <m>: only <used> of <a> was needed to pay off the loan.` |
  | `after_payoff` | `Extra payment in month <m> (<a>) was not used: the loan was already paid off.` |
  | `loan_ends_this_month` | `Extra payment in month <m> (<a>) was not needed: the loan ends with this month's regular payment.` |
  | `tiny_balance` | `Extra payment in month <m> (<a>) was not needed: less than half a cent was still owed after the regular payment.` |
  | `covered_by_earlier` | `Extra payment in month <m> (<a>) was not needed: an earlier extra payment in the same month already paid off the loan.` |
  | unknown | `Extra payment in month <m> (<a>): see the result above.` |

### 4.3 Error messages (English, D8)

`<n>` is the **form row** number (1-based), found through the sent-index → row map (§2).

| Code | Month | Amount |
|---|---|---|
| `required` | `Extra payment <n>: month is required.` | `Extra payment <n>: amount is required.` |
| `not_a_number` | `Extra payment <n>: month must be a number.` | `Extra payment <n>: amount must be a number.` |
| `negative` | `Extra payment <n>: month must not be negative.` | `Extra payment <n>: amount must not be negative.` |
| `below_min` / `above_max` | `Extra payment <n>: month must be between 1 and the last month of the loan term.` | `Extra payment <n>: amount must be between 0,01 € and 1 000 000,00 €.` |
| `too_many_decimals` / `not_whole_number` | `Extra payment <n>: month must be a whole number.` | `Extra payment <n>: amount can have at most 2 decimal places.` |
| unknown code | `Extra payment <n>: month is invalid.` | `Extra payment <n>: amount is invalid.` |

---

## 5. Storage (FR-4)

This deviates from plan §4's sketch `extra_payments (id, calculation_id, month, amount)`: the primary key is (calculation_id, position), and `used_amount` and `status` are added. The deviation is logged here and in the plan (review finding 13).

**`public.calculations` gets:**
- `months_saved smallint not null default 0 check (months_saved >= 0)`;
- `interest_saved numeric(14,2) not null default 0 check (interest_saved >= 0)`.

**New table `public.extra_payments`:**
- columns: `calculation_id uuid not null references public.calculations(id) on delete cascade`, `position smallint not null`, `month smallint not null`, `amount numeric(12,2) not null`, `used_amount numeric(12,2) not null`, `status text not null`;
- primary key: (`calculation_id`, `position`);
- checks: `position between 0 and 9`, `month between 1 and 360`, `amount between 0.01 and 1000000`, `used_amount between 0 and amount`, `length(status) between 1 and 40`;
- access: RLS on with no policies; all privileges revoked from `anon` and `authenticated` (same as `calculations`).

**Saving atomically:** a calculation and its items are saved in **one transaction**, by the function `public.save_calculation(payload jsonb) returns uuid`. It is called through the REST API as `POST /rest/v1/rpc/save_calculation` with the body `{"payload": {…}}` and the secret key, and the response is the new id as a JSON string.
- **Security (review finding 6):**
  - `security invoker`. The `service_role` the secret key maps to already has `BYPASSRLS` and the table privileges, so no `security definer` is needed.
  - `set search_path = ''`, with fully qualified names inside.
  - A new function is executable by `PUBLIC`, and Supabase's default privileges grant `anon` and `authenticated` too. So the migration runs `revoke execute on function public.save_calculation(jsonb) from public, anon, authenticated;` and `grant execute on function public.save_calculation(jsonb) to service_role;`.
  - The migration verifies the grants: with the publishable key, `/rest/v1/rpc/save_calculation` must be refused.
- **Checks inside the function** (the table cannot express them): each item's month ≤ the row's `term_years × 12`, and positions 0 … count − 1 without gaps.
- `ENGINE_VERSION` becomes `v2-calc-2`: results with extra payments come from new rules. Without extras the numbers are unchanged.

---

## 6. Examples (from `tools/reference.py`, `EXPECTED_EXTRA`)

All values are computed with exact rational arithmetic and checked by `py -I tools/reference.py`. The reviewer also recomputed E1–E8 independently from the text of §3.

| # | Loan | Extra payments (month: amount) | K (of n) | Final | Total Paid | Total Interest | usedAmount — status | Months saved | Interest saved | Ending |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 100 000 / 3,5 % / 30 y | 24: 5 000 | 332 (360) | 246,84 | 153 879,08 | 53 879,08 | 5 000,00 used | 28 | 7 778,30 | schedule |
| E2 | 100 000 / 3,5 % / 30 y | 60: 200 000 | 60 | 90 146,42 | 116 639,78 | 16 639,78 | 89 697,38 partly | 300 | 45 017,60 | extra |
| E3 | 100 000 / 3,5 % / 30 y | 60: 50 000; 60: 50 000; 120: 1 000 | 60 | 90 146,42 | 116 639,78 | 16 639,78 | 50 000,00 used; 39 697,38 partly; 0,00 after payoff | 300 | 45 017,60 | extra |
| E4 | 10 000 / 5 % / 1 y | 12: 500 | 12 (12) | 856,13 | 10 272,90 | 272,90 | 0,00 loan ends this month | 0 | 0,00 | schedule |
| E5 | 200 000 / 4,5 % / 25 y | 12, 36, 60: 10 000 each | 236 (300) | 670,04 | 291 910,14 | 91 910,14 | all used | 64 | 41 590,60 | schedule |
| E6 | 120 000 / 0 % / 10 y | 1: 1 000 | 119 (120) | 1 000,00 | 120 000,00 | 0,00 | 1 000,00 used | 1 | 0,00 | schedule |
| E7 | 100 000 / 3,5 % / 30 y | 100: 81 757,90 | 100 | 82 206,94 | 126 661,90 | 26 661,90 | 81 757,90 used | 260 | 34 995,48 | zero tail |
| E8 | 1 000,29 / 20 % / 30 y | 354: 100 | 354 (360) | 8,08 | 5 910,24 | 4 909,95 | 0,00 loan ends this month | 0 | 0,00 | schedule |
| E9 | 1 000,02 / 20 % / 30 y | 264: 783,50; 265: 1 000 | 265 (360) | 16,71 | 5 211,65 | 4 211,63 | 783,50 used; 0,00 tiny balance | 95 | 815,92 | extra |
| E10 | 100 000 / 3,5 % / 30 y | 60: 95 000; 60: 5 000 | 60 | 90 146,42 | 116 639,78 | 16 639,78 | 89 697,38 partly; 0,00 covered by earlier | 300 | 45 017,60 | extra |
| E11 | 250 000 / 6 % / 20 y | 120: 200 000 | 120 (240) | 163 119,24 | 376 257,76 | 126 257,76 | 161 328,16 partly | 120 | 53 600,35 | extra |
| E12 | 100 000 / 3,5 % / 30 y | 1: 200 000 | 1 (360) | 100 291,67 | 100 291,67 | 291,67 | 99 842,63 partly | 359 | 61 365,71 | extra |

- **E1** is the main example: the regular payment stays 449,04 €.
- **E2**, **E3**, **E10**, **E11** and **E12** show the pay-off rule:
  - E3 and E10 split the used amount within one month.
  - E3 also has a later item, which is not used.
  - E11 is an independent loan.
  - E12 is paid off after one payment.
- **E4** and **E8** are extras in a month where the loan ends anyway: month n, and V1's own early termination (X10).
- **E6** is 0 %.
- **E7** is the zero tail: Final = 449,04 + 81 757,90.
- **E9** is the `tiny_balance` case. With only the first item, the loan would end in month 266 with a 0,01 € payment (interest saved 815,91 €). With the second item it ends in month 265 (815,92 €), although that item's used amount is 0,00 (§3.3).

---

## 7. Build plan (after approval)

1. `backend/mortgage/domain/schedule.py`, the month-by-month run of §3.2 (ADR-9), with statuses. `calculate_mortgage` keeps its V1 results; the 6 800-loan V1 sweep and `tools/v1_parity.py` stay green.
2. Validation of items (§2), use case, API (§4.1). Update the contract (§4.1 list) with a short independent review of the contract change. 8 KiB limit.
3. Tests:
   - E1–E12, each rule guarded by ≥ 2 independent examples or tests;
   - a seeded sweep comparing the backend to `calc_extra` cent for cent, statuses included (as in Phase 2), using the §3.5 strata;
   - properties 1–7;
   - a hand mutation check of the backend (≥ 2 tests per rule).
4. Migration (§5): tables, `save_calculation`, grants verified with the publishable key; persistence; live check.
5. Frontend (§4.2–4.3): rows, the row map, notes, durations; e2e with extra payments; mutation check.

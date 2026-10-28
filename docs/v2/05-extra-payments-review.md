# 05 — Extra Payments Spec Review (Phase 7)

Status: **All findings resolved** (2026-10-28) in [`04-extra-payments.md`](04-extra-payments.md) and `tools/reference.py`. 04 approved by the author (Prompt 47).

An independent reviewer reviewed the first draft of 04: a separate agent that had not written it, under the Layer 4 rules ("you did not write this", run things, do not estimate). The verdict was **approve with changes**: 6 Major, 7 Minor, no Blocker.

## What the reviewer verified by running code

- They wrote their own implementation from the **text** of §3, without using `calc_extra`. It matches all of E1–E8 in every value: K, Final, totals, usedAmount, savings and ending.
- Text vs `calc_extra`: **0 mismatches** on the 2 000 sweep loans with extras, plus 3 000 adversarial loans. These include 0 %, tiny extras near the end, several items in a zero-tail month and exact pay-offs.
- Final − M in an extra ending was always within [0, X_K] (5 000 cases).
- Interest saved was never negative in 6 000 adversarial cases, and they gave a proof that it never can be (finding 3).
- They measured the body sizes the form can produce (finding 7).

## Findings and resolutions

| # | Sev. | Finding | Resolution |
|---|---|---|---|
| 1 | Major | An extra reported as "not used" can still shorten the loan. Example: 1 000,02 / 20 % / 30 y, extras 264: 783,50 and 265: 1 000. Month 265 owes less than half a cent above M, so the extra ending writes the remainder off: K is 265 instead of 266, and 0,01 € of interest is saved. | Reproduced. New status **`tiny_balance`** with its own note. §3.3 says it still has an effect. Example **E9**; a sweep stratum builds the case on purpose (400 loans). |
| 2 | Major | The §3.5 sweep could not catch errors in the pay-off rule: "used = 0" and "used = everything" both passed with 0 violations. Several cases were never reached. Invariant 3 was a tautology. | Sweep rewritten (8 strata, 3 200 loans), with an **independent paid-off check** (balance rebuilt from P, ends in [−0,005, 0,005)), a greedy-split check, status checks and constructed edge cases. The **sweep itself was mutation-tested** (below). |
| 3 | Major | R4 was left open, but Money is "never negative" in the contract. | The reviewer's **proof** that interest saved ≥ 0 is in §3.5 (property 5). It is checked in the sweep and becomes `check (interest_saved >= 0)` in the database. |
| 4 | Major | An extra in a schedule-ending month (month n, or V1's own early termination) was "not used" with a false note ("already paid off"). This reading of X5 was the drafting agent's, not the author's. | **The author decided (X10, Prompt 46): "not needed", 0,00 used.** Status `loan_ends_this_month` with a correct note. |
| 5 | Major | Once a blank row is dropped, error row numbers are wrong (they used index + 1). | The frontend keeps a **sent-index → form-row map** for errors and notes. "Blank" means empty after JS `trim` (§2, §4.3). |
| 6 | Major | The `save_calculation` RPC left its security undefined. New functions are executable by PUBLIC, and Supabase's default privileges also grant `anon`. | §5: `security invoker`, `set search_path = ''`, `revoke … from public, anon, authenticated`, `grant … to service_role`, verified with the publishable key. Body `{"payload": …}`, a uuid response, and checks inside the function (month ≤ term × 12, positions without gaps). |
| 7 | Minor | 4 KiB is too small for bodies the form can produce: escaped `"` 4 916 bytes; `€` 7 216 bytes. | **8 KiB**, with the reviewer's measured sizes in §4.1. |
| 8 | Minor | The month range message "(1 to term × 12)" could not be filled in. | Fixed text: "…between 1 and the last month of the loan term." |
| 9 | Minor | The request item shape was undefined (`null`, non-object items, unknown keys, numbers, `{}`). | §2: `null` = absent = `[]`; the item is closed (`month` and `amount` only, as RawInput); the rest is `400`; `{}` gives two `required` errors. |
| 10 | Minor | Page formats were incomplete: singular forms, 12 months, the trigger, and Final including the extra. | §4.2: duration rules (1 year / 2 years, 12 months = 1 year, zero parts left out, 1 payment); the trigger is a non-empty `extraPayments`; Final keeps its label and includes the extra used. The page uses `status`, so it does no arithmetic on money. |
| 11 | Minor | Several sentences in the contract must change. | Listed in §4.1. Applied and reviewed in build step 2. |
| 12 | Minor | Wording: "only Final is rounded" (M is rounded too); the zero tail has more causes. | Fixed in §3.2 and §3.4. |
| 13 | Minor | Process: plan §4 deviation not logged; R1 and R4 needed decisions before the build; the extra-ending rule relied on one loan. | Deviation logged in §5 and in the plan; R1 = X10, R4 = proven. Independent extra-ending examples **E10, E11, E12** added. |

## Answers to the draft's questions

- **R1** (extras in a schedule-ending month): see finding 4, now decision X10.
- **R2** (split in request order): acceptable. The help text says "the first one entered is used first", and the sweep checks the greedy split.
- **R3** (`property`): yes. `ValidationError` is open, so it is additive. `index` and `property` are required for `field: extraPayments`.
- **R4** (negative interest saved): impossible, proven (finding 3).
- **R5** (breaking changes): none. The contract text must change as listed in §4.1.

## Mutation check of the reference sweep (finding 2)

Each mutation of `calc_extra` was run against `check_extra_sweep(loans=800)` alone, without the examples (scratch script `mutate_reference.py`):

| Mutation | Sweep | Violations |
|---|---|---|
| Extra ending uses nothing (`used = 0`) | fails | 253 |
| Extra ending uses everything (`used = X_K`) | fails | 342 |
| Split in reverse order | fails | 2 348 |
| Extras counted in a schedule-ending month | fails | 0 (caught only because the status `loan_ends_this_month` is never reached; see note) |
| Zero tail ignores the extra (`Final = M`) | fails | 525 |
| Extra paid before that month's interest | fails | 563 |
| `tiny_balance` reported as `covered_by_earlier` | fails | 100 |
| `after_payoff` reported as `loan_ends_this_month` | fails | 4 |
| Zero tail not detected | fails | 200 |
| Months saved off by one | fails | 600 |

**Note:** the schedule-ending mutation is caught only by coverage, not by a property. Examples E4 and E8 also catch it; together that is two independent guards. The backend's tests (build step 3) must assert the `loan_ends_this_month` cases directly, not only through the sweep.

## Result

`py -I tools/reference.py` → exit 0, about 100 s:
- V1: 8/8 examples and the 6 800-loan sweep, 0 violations;
- extra payments: E1–E12 ok;
- extra sweep: 800 loans without extras (= V1) and 2 399 with extras, 0 violations;
- endings: schedule 217, extra 1 383, zero tail 799;
- every status occurs: used 4 005, partly used 663, after payoff 1 755, loan ends this month 15, tiny balance 400, covered by earlier 311.

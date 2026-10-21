# 06 — Retrospective (V1)

Status: **Final** (2026-10-21)

Scope: the whole V1 process, from Part A (Planning: Layers 1–5, [`01-functional.md`](01-functional.md) to [`05-plan.md`](05-plan.md)) through Part B (Build: Steps 1–9) and the no-plan experiment (branch `experiment/no-plan`, folder `no-plan/`).

Sources: `docs/v1/01`–`05`, [`prompts.md`](prompts.md) (Prompts 1–19), [`../handoff.md`](../handoff.md), the git history (`234b524` … `f89a394`), and the source and tests in `src/`, `tests/` and `no-plan/`. The comparison numbers in section 5 were measured on 2026-10-21 by running both builds on the same inputs.

---

## Summary

| Metric | Value |
|---|---|
| Planning documents | 5 (01–05), about 1 490 lines |
| Review findings | 24 (1 Blocker, 5 Major, 18 Minor). #1–#6 decided, #7–#24 still open |
| Test scenarios | 95 before the review, 112 after it (+17) |
| Build steps | 9. Each one had a red phase, a green phase and exactly one commit |
| Final state | 112/112 tests pass, 0 type errors, `decimal.js` is the only runtime dependency |
| Expected values from 03 changed during the build | **0** |
| Spec escalations during the build (05 §6.3) | **0** |
| Rework commits (reverts, fix-ups) | **0** |
| Build prompts that disagreed with the plan | **9 of 9** (see section 3) |

**Main lesson.** Most of the value came from the review and the plan. The review found the bugs before any code was written. The plan then acted as the single source of truth, so the build could ignore wrong details in the prompts. The weakest part of the process was the prompts themselves.

---

## 1. What the Plan Got Right

These decisions held through all 9 build steps without being changed. Each one prevented rework that would otherwise have happened.

| Decision | Where | Rework it prevented |
|---|---|---|
| **The calculation module is pure and isolated** (M4 depends only on `domain/types` and `decimal.js`) | 02 M4, §4 rule 2, ADR-8 | The Blocker #1 fix (early termination) changed only the balance loop in **one file**, `src/domain/calculation.ts` (66 lines). Parsing, validation, the CLI and every earlier test were unaffected. M4's 28 tests run with plain inputs and outputs, with no mocks. |
| **Private 40-digit `Decimal` context with `ROUND_HALF_UP`** (`Decimal.clone`) | ADR-3, test 61 | Exact half-up rounding for values such as 83.345 → 83.35 (test 59), where half-even would give 83.34. The review checked 40 digits against exact rational arithmetic on 318 inputs: **0 mismatches**. Test 61 changes the global Decimal config, and M4 still gives the right result. Step 5 used the same pattern (explicit `ROUND_HALF_UP` in `toFixed`), so review finding #16 never became a bug. |
| **Event-driven line-queue reader** (FIFO queue, one pending resolver, `undefined` after EOF) | 02 M8, ADR-10 | Steps 8 and 9 passed the first time they went green. Piped stdin, CRLF input and EOF all worked, and every e2e test (89–92, 110) passed with no debugging of hangs. The obvious `readline/promises` design would have lost lines and exited with code 13 (04 #2). |
| **Strict number grammar checked before `decimal.js`** (`NUMBER_PATTERN`) | 01 §3.2, 02 M2 | `0x3E8`, `1e5`, `NaN` and `Infinity` are rejected at one point (tests 96–101). Without the gate, `0x3E8` would have been accepted as a €1 000 loan, and no test would have noticed. |
| **Architecture guard written in Step 1** (tests 93–95) | 02 §4, ADR-7, 05 Step 1 | Every later step was checked against the layer rules from the first commit. In Steps 2, 7 and 9 the prompts asked for files in the wrong layer (`src/parsing/`, `src/domain/calculator.ts`). The guard would have failed those files, so the plan's paths were used instead. The guard also tests itself with known-bad imports, so it cannot pass with nothing to check. |
| **Validation returns codes; all texts live in presentation** | ADR-5 | Validation tests compare stable codes, and M6 checks its `MESSAGES` table with `satisfies` against every error code. The UI text contract in 03 changed nothing in M3. |
| **Exact test names and per-step test IDs in the plan** | 05 §2.2, §3 | Every step had a fixed red/green target (3 → 24 → 49 → 77 → 84 → 95 → 101 → 107 → 112). When a prompt gave the wrong test IDs (4 of 9 steps), the plan's table settled it at once. |
| **Implementation risks written down before the build** | 05 §6.2 | Four of the six risks happened, and the contingency was ready each time: ES-module spying (partial `vi.mock`, Step 7), the sweep runtime (≈ 3.9 s with a raised timeout, Step 4), spawning `npx` on Windows (`process.execPath --import tsx`, Step 9), and global Decimal rounding (Step 5). |
| **"Never change an expected value during the build"** | 05 §4, §6.3 | No value from 03 was changed, and none needed to be. Every value had already been checked twice (REF-PY / REF-ET and the exact-rational audit in 04). |

---

## 2. What the Plan Missed

### 2.1 Found by the review (Layer 4), before any code existed

These gaps were in the specs as written by Layers 1–3. Each one needed a spec change in Prompt 7.

| # | Gap | Effect if it had been built as written | Change required |
|---|---|---|---|
| **Blocker #1** | **Early loan payoff was not defined.** 01 §4.4 always charged M_rounded for n − 1 months. When M is rounded **up** at a high rate over a long term, the overpayment compounds and repays the loan before month n. | Valid inputs give a **negative Final Payment**: P = 1 000.29, 20 %, 30 y → Final **−97.42**. At 20 %/30 y, 8 396 of 20 000 tested inputs (P 1 000–1 199.99) gave Final ≤ 0. The problem reached down to 8 %/30 y. Test 60 checked invariants only on 17 hand-picked inputs, so it would still have passed. | 01 §4.4 rewritten as an amount-due loop: if D = B·(1 + r) ≤ M_rounded before month n, that month is the last one, and the Final Payment is D rounded to cents. P = 1 000.29 now ends at month 354 with a Final Payment of **8.08**. Changes in FR-1/FR-2, §4.5 (totals use k, the number of payments made), M1 (`numberOfPayments`), M4 steps 3–5 and tests 102–110 (new exact-rational reference REF-ET). |
| **Blocker #1, part 2** | **The sub-half-cent rounding tail.** This gap was found while fixing #1, not by the review. If the amount due in the last active month is below €0.005, the Final Payment rounds to €0.00, which breaks "Final > 0". | A €0.00 "final payment" line, and a payment count that is one too high. | 01 §4.4 step 3: the previous month's payment (M_rounded) becomes the Final Payment, and the loan ends one month earlier. Example: P = 1 075.15, 20 %, 30 y → 355 payments of 17.97, and the Final Payment line is hidden. Tests 106 and 109. This rule was **added by the agent**, not chosen by the author, and is listed as unconfirmed in 05 §6.3. |
| **Major #2** | **Piped stdin and EOF.** 02 M8 specified sequential `readline/promises` `question()` calls. | Verified on Node 24.20.0: only the first piped answer was received, and the pending question never settled at EOF, so the process exited with code **13** ("unsettled top-level await") instead of 1. All piped e2e tests (89–92) and the exit-code-1 rule would have failed in Step 9. Fixing it then would have meant redesigning M8 after Step 8 was committed. | The line-queue reader (02 M8, ADR-10), prototyped and verified with piped input, CRLF and EOF. New tests 111–112. |
| **Major #3** | **The number grammar was not defined.** 01 §3.2 listed separators but no allowed character set. | `new Decimal('0x3E8')` is 1 000, so a hex string would be a valid loan. The same goes for `0b…`, `0o…` and exponents. This is a silent bug: no existing test used these inputs. | `^-?[0-9]+([.,][0-9]+)?$`, checked before conversion. Tests 96–101. |
| **Major #4** | **No invariant sweep.** The invariants claimed for every valid input were tested only on fixed inputs. | Finding #1 could not be found by the test suite. | Test 108: a seeded sweep over 6 800 inputs. It found 767 early terminations (11 %) and 0 violations. |
| **Major #5, #6** | **Extension friction.** Extra payments would change 5–6 modules, and variable rates would change 5, including a breaking change to `LoanInput`. 02 claimed simpler extension points than the design supports (e.g. "replace `r` with `rateForMonth`" would make Finding #1 much worse). | No V1 effect, but V2 would have started from wrong assumptions. | Accepted as a documented trade-off (ADR-9). V2 variable rates get a dedicated `domain/schedule` module. |

The Layer 3 prompt's own example was also wrong: it gave Final 449.04 and Total Paid 161 654.40 for P = 100 000, 3.5 %, 30 y. That leaves the loan **under-repaid by €2.98**. 03 used the correct values (452.02 / 161 657.38). During Prompt 7, the invariant "Final ≤ Regular" was also wrong as worded: it is false for correct full-term loans such as test 43. A clarifying question was asked, and the author scoped it to early-terminated loans.

### 2.2 Found during the build (Part B)

None of these needed a spec or test change. Each was a detail the plan did not foresee.

| Step | Discovery | How it was handled |
|---|---|---|
| 1 | npm installed **TypeScript 7** and **`@types/node` 26** by default. | Pinned to `^5` / `^24` to match 02 §1 and the Node 24 runtime. The plan named major versions but did not pin them. |
| 1 | `import Decimal from 'decimal.js'` resolves to a namespace under `NodeNext` (TS2709). The interface samples in 02 use this default import. | Named import `import { Decimal } from 'decimal.js'`, written into the handoff as a convention for the later steps. |
| 1 | npm 11 warns that esbuild's install script was not approved. | No action needed. Vitest and tsx work without it. |
| 2 | 04 #12 (NBSP and tab inside numbers) and #9 (`-0`) were still open. | The literal spec text was followed (only U+0020 is removed inside a number, and `-0` → `negative`), and both were recorded in the handoff, as 05 §2.1 requires. |
| 4 | `LoanInput` holds `Decimal`s from the **global** constructor, so M4's private clone must re-wrap them before doing arithmetic. Not stated in 02. | `new Dec(input.principal)`. Test 61 checks it. |
| 4 | **Only test 106 guards the zero-tail rule.** The 6 800-input sweep contains no such case. Mutation testing showed this. | Recorded in the handoff. It is a weak spot: one hand-picked input guards a whole spec rule. |
| 6 | The prompt said 9 tests (69–77); the plan has 11 (69–79). Tests 78–79 were not scheduled in any other step. | The plan was followed. |
| 6 | 04 #17 (range limits duplicated in M6 texts) was accepted in 05 §6.2. | A code comment in M6 points to `V1_RULES`. |
| 9 | **Test 92 passed during the red phase** without `src/main.ts`, because a missing module also exits with code 1. | Recorded. Test 92 only carries weight together with tests 89–91 and 110. An exit-code-only assertion cannot fail. |
| 9 | 02 M9 uses `process.exitCode`; the prompt asked for `process.exit(code)`, which can cut off stdout on a pipe. | `process.exitCode` (02 M9) was kept. |
| 9 | In PowerShell, `npm start` is blocked by the execution policy (`npm.ps1`). | Use `npm.cmd start`. Recorded in the handoff. |
| 9 | **AC-3 (full interactive run) cannot be checked by the agent**, because it cannot type into a TTY. | The first prompt was checked (`Loan amount (EUR): `, no default). The rest is a manual check for the author. |

### 2.3 Still open at the end of V1

- **Review findings #7–#24** (all Minor) have no author decision. The build followed the literal spec text for them (05 §2.1).
- **The sub-half-cent tail rule** (01 §4.4 step 3) still needs the author's confirmation (05 §6.3).
- **The number of payments is not displayed**, even when a loan ends early. For P = 1 000.29, 20 %, 30 y, the user sees a Final Payment of 8,08 € but not that the loan ends after 354 months instead of 360.
- **AC-3**: the full interactive run still needs to be checked by hand.

---

## 3. Prompting Impact

### 3.1 Structured planning prompts (Layers 1–5)

The planning prompts listed the sections, the columns and the checks they expected (for example: "single responsibility without the word 'and'", "exact values, money down to the cent", "write and run a standalone verification script, do not estimate"). The output followed that structure each time, and the instruction to verify by running code is what produced the evidence in 04.

| Prompt feature | Effect on the output |
|---|---|
| **Interview one question at a time** (Layer 1) | Six focused questions settled the platform-independent rules: rounding method, 0 %, separators, output format, language and the final-payment threshold. The one item left open (OQ-1, platform) was resolved in Layer 2. |
| **"Push back on scope creep"** (Layer 1) | The 9-item out-of-scope list was fixed early. Nothing out of scope was built later. |
| **Required columns, including "Reference Source"** (Layer 3) | Every expected value had to name an independent source. That led to the REF-PY script, which corrected the prompt's own wrong example. |
| **"You did not write this plan. Do not trust claims. Run a script, do not estimate."** (Layer 4) | This framing produced the most valuable output of the project. Blocker #1 was found by a domain search with a script, not by reading. |
| **Decisions given with a reason, one per finding** (Prompt 7) | They were applied consistently to 01, 02, 03 and 04 in one commit. The one ambiguous decision (the "Final ≤ Regular" invariant) was raised as a question before anything was written. |

### 3.2 Build prompts (Steps 1–9)

The build prompts were also structured (red, green, verify, log, commit), but they **repeated details from memory instead of pointing to the plan**. Every build prompt disagreed with `05-plan.md` somewhere:

| Kind of mismatch | Steps | Count |
|---|---|---|
| Commit message differs from 05 §3 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 9 of 9 |
| Wrong test IDs or test count | 2 (1–21 instead of 1–16 + 96–100), 4 (102–109 instead of 61 + 102–108), 6 (9 tests instead of 11), 7 (80–83, 109–110 instead of 80–84, 109) | 4 of 9 |
| Wrong file path or layer | 1 (`src/types.ts`), 2 (`src/parsing/`), 7 (`src/domain/calculator.ts`), 9 (`tests/e2e.test.ts`) | 4 of 9 |
| Wrong technical instruction | 4 (`Decimal.clone({ precision: 40 })` without a rounding mode), 5 (non-breaking spaces, which test 68 forbids), 7 (mock `calculateAnnuity`, which does not exist), 9 (`process.exit(code)`) | 4 of 9 |

Two of the path errors would have failed the architecture guard. The NBSP instruction would have failed test 68. Each mismatch was caught because every prompt began with "Read `docs/v1/05-plan.md`", and the plan was treated as the more authoritative source. Each deviation was logged in `prompts.md`.

### 3.3 Conclusions on prompting

1. **A specific but wrong prompt is worse than a vague one.** A vague prompt leaves the decision to the plan. A specific prompt with a wrong detail (a test range, a path, NBSP) forces a conflict that must be spotted and resolved. Without the plan as a reference, those details would have been built as written.
2. **Prompts should point to the plan, not copy it.** "Execute Step 4 of `05-plan.md`" carries less risk than retyping the step's test IDs and commit message.
3. **The useful structure is about verification, not format.** The instructions that improved quality most were "run a script, do not estimate", "verify red before green", and "you did not write this plan". Required columns and section lists made the output consistent, but did not by themselves make it correct.
4. **Concrete examples in prompts need checking too.** The Layer 3 example and the Prompt 7 invariant were both wrong, and both were caught only because the agent recomputed them.

---

## 4. Review Value

### 4.1 What the independent audit found

The review (Prompt 6) read only 01–03, treated every claim as unverified, and ran three scripts (04 Appendix A–C): an exact-rational recomputation of every reference value, a domain search for negative final payments, and a Node readline reproduction.

| Finding | Kind of bug | Would the build have caught it? |
|---|---|---|
| **#1 negative Final Payment** | **Silent wrong result.** Valid inputs give a negative payment and wrong totals. | **No.** All 95 original tests, including invariant test 60, would have passed. The bug would have shipped. |
| **#3 hex / exponent / NaN accepted** | **Silent wrong acceptance.** `0x3E8` becomes a €1 000 loan. | **No.** No test used these inputs. |
| **#2 readline loses lines and hangs at EOF** | Loud failure, but late. | **Yes, in Step 9**, as failing e2e tests after M8 was committed. It would have meant redesigning M8 and re-opening a finished step. |
| **#4 no invariant sweep** | Gap in the tests. | No. This is the reason #1 was invisible. |
| **#5, #6 extension friction** | Wrong design claims. | No. It would have surfaced only in V2. |

So of the six decided findings, **two were silent bugs** that the planned test suite could not detect, one was a late loud failure, and three were gaps in tests or design. The review also confirmed what was right: **all 18 reference calculations, 11 rounding checks and the 40-digit precision choice were correct**, so the build could trust 03 completely. That is why 0 expected values changed in Part B.

### 4.2 Why independence mattered

- **Different method from the author.** 03 used 60-digit `decimal` (REF-PY). The review used exact `fractions.Fraction`. Agreement between two different methods is real evidence. A re-run of the same script would not be.
- **Searching instead of sampling.** The author's tests were chosen inputs. The review searched the input domain (20 000 inputs per rate/term pair) and found the failing region. Hand-picked inputs could not have found it.
- **Reproduction instead of reading.** Finding #2 was a 10-line script with a measured exit code (13). That made it impossible to argue with, and it gave the fix (ADR-10) a ready test.

### 4.3 Limits of the review

- **The review was a document audit, not a code review.** No independent review of the code in Part B took place. The build's own checks (mutation tests in Steps 1, 4, 5, 7 and 8, and the red phase for every step) partly cover this, but they were done by the same agent that wrote the code.
- **18 of 24 findings were never decided.** The build had to make literal-reading choices for `-0`, NBSP and the term `"10,0"`. These are product decisions, not implementation details.
- **The sub-half-cent tail rule was created while fixing a finding and was never reviewed itself.** The fix for the review introduced a new rule that no independent check looked at. It is guarded by exactly one test (106).
- **Severity was not tested against reality.** Minor #24 (CRLF on Windows) mattered on this machine and was covered by the line-queue design. Minor #9 (`-0`) was mostly theoretical. The scale did not separate these well.

---

## 5. Experiment Results: Full Plan vs. `experiment/no-plan`

### 5.1 Setup

The same agent built a second calculator from one prompt: *"Build a simple mortgage calculator CLI application in Node.js/TypeScript."* (Prompts 18–19). It did not read `docs/v1/`. It is in `no-plan/` with its own `package.json`. The same prompt was given a second time, and the existing build was re-checked instead of rebuilt.

**Caveat (contamination).** The experiment ran in the same repository and session context as V1. Some no-plan choices look like they were carried over from V1 rather than made fresh: the private `Decimal.clone({ precision: 40, rounding: ROUND_HALF_UP })` (identical to ADR-3), `crlfDelay: Infinity`, and a readline async iterator (the alternative listed in ADR-10). The no-plan build is therefore probably **better** than a truly fresh one would be, so the differences below are a lower bound.

### 5.2 Quantitative comparison

| Measure | Full plan (V1) | No plan |
|---|---|---|
| Prompts | 17 (8 planning + 9 build) | 1 |
| Planning text | ≈ 1 490 lines in 5 documents | 0 |
| Source lines | 471 (9 modules) | 141 (2 files) |
| Test lines | 1 327 | 65 |
| Tests | 112 (unit, functional, e2e, architecture, a 6 800-input sweep) | 7 (unit only) |
| E2E tests / architecture guard | 5 / 3 | 0 / 0 |
| Expected values checked by an independent method | All 18 reference cases, twice | None (values written by the same code author) |
| Runtime dependencies | 1 (`decimal.js`) | 1 (`decimal.js`) |
| Type-check | 0 errors | 0 errors |

### 5.3 Same inputs, different results

Both builds were run on the same inputs (2026-10-21). The no-plan build computes Total Paid as the **unrounded** payment × n and has no final payment.

| Input (P, rate, term) | No plan: Monthly / Total Paid | Displayed monthly × n | V1: Regular / Final / Total Paid |
|---|---|---|---|
| 100 000, 3.5 %, 30 y | 449.04 / 161 656.09 | 161 654.40 | 449,04 € / 452,02 € / 161 657,38 € |
| 250 000, 6 %, 20 y | 1 791.08 / 429 858.64 | 429 859.20 | 1 791,08 € / 1 789,99 € / 429 858,11 € |
| 1 000 000, 20 %, 30 y | 16 710.19 / 6 015 667.27 | 6 015 668.40 | 16 710,19 € / 16 638,10 € / 6 015 596,31 € |
| 1 000.29, 20 %, 30 y | 16.72 / 6 017.41 | 6 019.20 | 16,72 € / 8,08 € (month 354) / 5 910,24 € |
| 1 075.15, 20 %, 30 y | 17.97 / 6 467.74 | 6 469.20 | 17,97 € (355 payments, no Final line) / 6 379,35 € |

Observations:

- **The no-plan output is not internally consistent.** For 100 000 / 3.5 % / 30 y it shows a monthly payment of 449.04 and 360 payments, but 449.04 × 360 = 161 654.40, not the 161 656.09 it shows as Total Paid. Neither number is what a borrower would pay (161 657.38, because the 359 rounded-down payments leave a €2.98 shortfall that the final payment must cover).
- **The error grows exactly where Blocker #1 lives.** For P = 1 000.29 at 20 %/30 y the no-plan build tells the user to pay 16.72 for 360 months (6 019.20 in total). The loan is in fact repaid after 354 months, and the borrower pays **5 910.24**. The no-plan build overstates the total by **€107.17**. For the largest loan, the difference is **€70.96**.
- **The no-plan build never hits the negative final payment**, but only because it never models a final payment at all. It avoids the bug by not answering the question.

### 5.4 Qualitative comparison

| Area | Full plan (V1) | No plan |
|---|---|---|
| Requirements | Consumer-confirmed: EUR, limits 1 000–1 000 000 €, 0–20 %, 1–30 y, Slovak format `1 234,57 €` | Guessed: no currency, amount > 0 with no upper limit (`0.01` and `999999999` are accepted), rate 0–100 %, term 1–50 y, English format `1,234.50` |
| Decimal comma | `1000,50` accepted (01 §3.2) | `1000,50` rejected as "not a number", although this is the normal format for the Slovak user |
| Hex / exponent / `NaN` | Rejected by `NUMBER_PATTERN` | Also rejected (its regex `^\d+(\.\d+)?$` is strict too, probably carried over; see the caveat) |
| Final payment / early payoff | Specified, tested (tests 43–59, 102–110) and swept over 6 800 inputs | Not modelled; totals do not match the payments shown |
| Error messages | One message per field, all invalid fields reported at once, re-prompts only the invalid fields | One field at a time; generic "Please enter a number" message |
| Architecture | 9 modules, guarded layer rules, UI-independent core ready for a web adapter | Calculation, parsing, validation and formatting in one file; CLI reads `process.stdin` at import time (not testable without spawning) |
| Piped stdin / EOF | Line queue, tested (111–112, e2e 89–92) | Async iterator; works when tried by hand, but untested |
| Time to a working CLI | 17 prompts | 1 prompt |

### 5.5 Verdict

The no-plan build is a **working calculator for a different, guessed product**. It is fast, small and clean, and for a demo it would be enough. It is **not V1**: it uses the wrong number format for the target user, has no realistic limits, and gives totals that are internally inconsistent and wrong by up to €107 in the region where the real rules matter. None of its 7 tests would notice, because its expected values come from the same author as its code.

The plan's cost was about 16 more prompts and roughly 10× the test code. What it bought was the **requirements** (decimal comma, limits, format), the **rules** for the final payment and early payoff, and the **independent evidence** that the numbers are right. The no-plan build cannot get the first two right except by luck, and cannot show the third at all.

---

## 6. Methodology Recommendations for V2

### 6.1 Rules (add to `CLAUDE.md`)

1. **The plan is the source of truth. Prompts point to it and do not restate it.** A build prompt says "Execute Step N of `docs/v2/05-plan.md`" and adds only what is new. If a prompt and the plan disagree, the plan wins and the deviation is logged. (In V1, 9 of 9 build prompts disagreed with the plan.)
2. **Every rule over a numeric domain gets a sweep test, not only examples.** Any invariant claimed "for every valid input" needs a seeded property sweep over the full domain, including the corners (small P, high rate, long term). Finding #1 was invisible to 17 hand-picked inputs.
3. **Every spec rule needs at least two tests that can fail.** After each step, mutation-test every rule (remove it, see which tests fail). A rule guarded by one test (the zero-tail rule, test 106) or by a test that passes vacuously (test 92 in the red phase) is a gap.
4. **Rules created while fixing a finding go back through review.** The sub-half-cent tail rule was never independently checked. V2 should re-run a short review on every spec change made in a resolution prompt.
5. **Every finding gets a decision before the build starts**, even if the decision is "accept the literal reading". V1 started Part B with 18 undecided findings, and the build had to make product choices (`-0`, NBSP, `"10,0"`).
6. **Examples in prompts are hypotheses.** Any concrete value in a prompt (an expected payment, an invariant) is recomputed before it is used, as with the Layer 3 example and the "Final ≤ Regular" invariant in V1.

### 6.2 Process and structure

| Change | Why |
|---|---|
| **Add a Layer 4b: independent code review after the build** (same rules as Layer 4: "you did not write this", run things, do not estimate) | V1's review covered only the documents. The code was checked only by the agent that wrote it. |
| **Run the experiment in a clean context** (fresh session, separate clone without `docs/` and `src/`) | The V1 no-plan build probably copied choices from V1, which weakens the comparison. |
| **Measure time and tokens per layer and step** | V1 can compare prompts and lines, but not effort. V2 should record wall-clock time and token use from the start, so the plan's cost can be stated exactly. |
| **Start V2 with the `domain/schedule` module** (ADR-9) | Variable rates and extra payments both need a month-by-month schedule with per-period re-amortisation. Building it first, with its own sweep, avoids extending M4 in place, which the review showed would make Finding #1 worse. |
| **Decide the display rules for a schedule before designing it** (04 #7) | Rounded rows will not add up to the rounded totals, because §4.3 forbids intermediate rounding. This is a product decision and must be in 01, not found during the build. |
| **Show the number of payments when a loan ends early** | V1 hides the most useful fact about an early payoff. Decide this in V2's Layer 1. |
| **Move shared rules into `domain/`** (04 #16, #17) | The rounding helper and the input limits are duplicated between layers today. With more inputs in V2, the duplicates will drift. |

### 6.3 Tooling

| Tool / setting | Purpose |
|---|---|
| Pin exact versions in `package.json` from Step 1 (`typescript@5.9.3`, `@types/node@24`, etc.) | npm picked TypeScript 7 and `@types/node` 26 by default in V1. |
| Keep the architecture test (ADR-7) and extend its allow-list as an explicit table in 02 | It caught all wrong-layer paths in V1. Writing the table in 02 also resolves 04 #18. |
| Keep the exact-rational reference script (`fractions.Fraction`) as a checked-in file, e.g. `tools/reference.py`, run in CI | In V1 it lived only in document appendices. A checked-in script can be run again when V2 changes the rules. |
| Add a mutation-testing tool (e.g. StrykerJS) for `domain/` | V1 mutation checks were done by hand in each step. A tool makes rule 3 above cheap to enforce. |
| Add a CI job: `npm test`, `npm run typecheck`, the reference script, and the piped-stdin smoke test from AC-4 | V1 ran these only by hand at each commit (AC-6). |
| Use `npm.cmd` (or a cross-platform runner script) in all Windows instructions | `npm.ps1` is blocked by the PowerShell execution policy on this machine. |
| Add an interactive TTY test with a pseudo-terminal (e.g. `node-pty`) | AC-3 could not be verified by the agent in V1. |

---

## 7. Closing State

- **Part A (Planning):** complete. Documents 01–05; findings #1–#6 decided.
- **Part B (Build V1):** complete. 9 steps, 9 commits, 112/112 tests, 0 type errors.
- **Experiment:** complete. `no-plan/` (7 tests, 0 type errors), compared in section 5.
- **Retrospective:** this document.
- **Carried over to V2:** findings #7–#24, author confirmation of the sub-half-cent tail rule, whether to display the number of payments, and a manual check of AC-3.

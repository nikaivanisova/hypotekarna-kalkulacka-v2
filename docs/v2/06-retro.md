# 06 — V2 Retrospective

Status: **Complete** (2026-10-28). It covers the V2 refactor from the plan (Prompt 21) to Phase 8 (Prompt 49), and checks how V2 applied the rules from the V1 retrospective ([`../v1/06-retro.md`](../v1/06-retro.md) §6).

## Summary

| | V2 result |
|---|---|
| Parts | Frontend (Vite + vanilla JS), API contract (OpenAPI 3.1), backend (Python 3.14, FastAPI), Supabase (Postgres) |
| Features | V1 calculation, unchanged to the cent; web page; FR-4 saving; FR-5 extra payments that shorten the term; a rate limit |
| Commits | 18 on `master` since the V1 retrospective (`f0466e5..a9ff4a1`); tag `v1-final` marks the last commit with the V1 CLI |
| Code and tests | 59 files, about 8 600 lines (backend, frontend, API, Supabase, tools, CI) |
| Tests | backend **460** (+2 live, skipped without a key); frontend **133** unit + **13** e2e; `tools/reference.py` (12 + 8 examples, 6 800 + 3 200 sweep loans) |
| Independent reviews | 3: API contract (Phase 3), extra-payment spec (Phase 7), contract change (Phase 7). 0 Blockers, 11 Major, 19 Minor (5 + 8, 6 + 7, 0 + 4); all resolved |
| Hand mutation checks | about 140 mutations over 9 runs (Phases 2, 4, 5, 6, the reference sweep, the Phase 7 backend, frontend and persistence, and the rate limit); every one caught by ≥ 2 tests, except 2 that were shown to be equivalent |
| CI | First run green after the push (Prompt 50): 4/4 jobs on Linux, the same counts as locally |
| Not done | No deployment (D10: local only); time and tokens per phase not measured |

---

## 1. What worked

- **The exact-rational reference was the backbone.**
  - `tools/reference.py` (from V1's appendix, made self-checking in Phase 1) was the oracle for every numeric claim.
  - It checked the Python port against V1 (6 800 loans, 0 mismatches, Phase 2) and every extra-payment rule before any code (Phase 7). Every example in the spec came from it, not from reasoning.
  - Phase 2 and Phase 7 compare the backend with it cent for cent.
- **Contract first paid off twice.**
  - The Phase 3 review found that FastAPI's defaults break the contract: malformed requests return 422 and echo the input, and `"\ud800"` gives a plain-text 500. So Phase 4 parsed the body by hand and never hit the problem.
  - The open response schema and open vocabularies (03 #1, #2) let Phase 7 add fields, codes and statuses without breaking the Phase 5 frontend. The contract-change review confirmed the old frontend still works.
- **Independent reviews found real defects that the author of the code could not see.**
  - The extra-payment review found the `tiny_balance` case: an extra "not used" that still saves a month.
  - It proved that interest saved is never negative.
  - It showed that the first reference sweep could not detect a broken pay-off rule.
  - It found the wrong error row after a blank row, and the open `EXECUTE` grant on new Postgres functions.
- **Mutation checks found weak tests in every phase.** Examples: a vacuous frontend test ("renders text not HTML"), an empty Result panel staying visible after a failure, stale notes after a failure, a rate-limit test whose refusals expired with the first request, and redundant code (the `NaN` guard).
- **Asking one question at a time kept decisions with the author.** Ten extra-payment decisions (X1–X10), D1–D11, hosting and the rate limit were all decided by the author, with a recommendation each time.

## 2. What went wrong or was missed

| # | What happened | Effect | Lesson |
|---|---|---|---|
| 1 | The drafting agent changed an extra-payment rule while writing the spec: the "0,06 € used" in month n case. The author had not decided it. | The review caught it (05 #4); the author then decided X10. | The rule "decisions before build" also applies inside the spec: any reading the agent chooses is flagged as a question. |
| 2 | Extra payments were removed and restored within two prompts (Prompts 25, 28). | Small rework in the plan; nothing built. | A scope change asks "remove, or postpone?" before editing the plan. |
| 3 | The first reference sweep for extra payments was too weak: random inputs never reached the zero tail, the `tiny_balance` case or an exact pay-off, and one invariant was a tautology. | Found by the review. Fixed by building strata on purpose and mutation-testing the sweep itself (10/10). | A sweep is only evidence after its own mutation check. Count which paths it reaches and fail if one is never reached. |
| 4 | Two test groups were written before the code but **not run red first**: the item validation (Phase 7 step 2) and the rate limit (Phase 8). | The mutation check found one weak rate-limit test afterwards. | Keep the red run even when the tests look obviously right; it is cheap. |
| 5 | The secret key was hard to set up. `backend/.env` did not exist, then it held the publishable key. | Three prompts of explanation. No leak: every check was done without printing the key. | Give the exact file, the exact dashboard path and what the key looks like, before asking for it. |
| 6 | **Windows Application Control** blocked `.venv\Scripts\pytest.exe` and schemathesis' `jsonschema_rs` DLL. | `python -m pytest` instead; a per-response contract check and a seeded fuzz test instead of schemathesis. | Check native tools early on a locked-down machine and write the workaround into CLAUDE.md. |
| 7 | Shell quoting broke several inline scripts (heredocs with `'''`, `\n`, `\ud800`). | Retries; one edit was silently not applied and only caught by a check. | Write any non-trivial script to a file; verify every edit with a check, not with the absence of an error. |
| 8 | Time and tokens per phase were **not measured**, although the V1 retrospective asked for it (§6.2). | The cost of the plan-first method can still not be stated. | Record wall-clock time and tokens per phase from the start of V3. |
| 9 | CI was written before it could run (nothing was pushed until Prompt 50). | The first run was green on Linux, so the portable paths and Chromium worked first time; this was luck as much as design. | Push and watch the first run before calling CI done. |

## 3. V1 retrospective rules: were they followed?

| V1 rule (06 §6.1) | V2 |
|---|---|
| 1. The plan is the source of truth | Yes. Every phase followed `00-refactor-plan.md` §6. Deviations were logged: the `extra_payments` table shape (plan §4 vs 04 §5), schemathesis replaced, and Phase 4 "done when" changed after review. |
| 2. Sweep tests for numeric domains | Yes, and stronger than V1: stratified sweeps with constructed edge cases, a sweep of the month limit over terms 1–30, and the extra sweep mutation-tested. |
| 3. ≥ 2 tests per rule, checked by removing the rule | Yes, in every build phase (hand mutation checks, about 140 mutations). The 2 survivors were each shown to be equivalent: `due <= paid_now` → `<` for an exact pay-off, and a 422-vs-failure path in the client. |
| 4. Rules created while fixing a finding go back through review | Partly. The spec rewrite after the review was not reviewed again as a whole; the contract change was. |
| 5. Every finding gets a decision before the build | Yes for V2's own findings. The V1 Minor findings #7–#24 were kept as "V1 behaviour exactly" (01-functional V2 §3), which is a decision, not a review of each. |
| 6. Examples in prompts are hypotheses | Yes. Every number in the specs was recomputed, and two wrong ones were caught before review: the body-size estimate (2 400 → 2 700 bytes) and "10,0 → not_whole_number" (it is `too_many_decimals`). |

## 4. Recommendations for V3

1. **Make CI the gate.** The first run passed (Prompt 50); require it on `master` (branch protection).
2. **Measure** time and tokens per phase (V1 06 §6.2, still open).
3. **Deployment**, when needed (D10):
   - Host the backend and frontend under one origin, or set the CORS allowlist to the frontend's URL.
   - Store the secret key in the host's secrets.
   - Replace or confirm the in-memory rate limit behind the proxy, and trust `X-Forwarded-For` only from that proxy.
   - See the deployment notes in `README.md`.
4. **Re-review fixes as a whole:** after a review's findings are applied, run a short second review of the changed sections (rule 4, partly missed).
5. **Write the machine's constraints into CLAUDE.md** (Application Control, `npm.cmd`, `python -m pytest`), so a new session does not have to discover them again.
6. **Undecided V1 Minor findings (#7–#24):** decide them explicitly in V3's Layer 1, or record "keep V1" per finding.

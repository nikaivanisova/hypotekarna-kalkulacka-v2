# V2 Prompt Log

Prompts 21–26 (the V2 plan, the Python setup and decision D7) are logged in `docs/v1/prompts.md`, which was still the active log at the time. This log continues the numbering.

## Prompt 27 — Accept the decisions; Phase 0 and Phase 1

### Prompt

> you can use recommended answers for D1-D11 and continue

### Output

- **Decisions:** D1–D11 recorded as decided in `00-refactor-plan.md` §8. D8 (language) = English, the same as V1 01 §3.5, so the V1 texts and tests carry over. D11 (which Supabase project) is settled at Phase 6. Also fixed a table row in §7 that was broken when the extra-payment row was removed.
- **Phase 0:**
  - `CLAUDE.md` rewritten for V2: the four parts, backend-only rounding, no float money, the retro §6.1 rules, the prompt log in `docs/v2/prompts.md`, Windows notes.
  - `docs/v2/01-functional.md`: V1 behaviour kept exactly; web UI rules; FR-4 "save calculation"; open V1 questions keep V1 behaviour.
  - Checked against the V1 tests: term `"10,0"` → `too_many_decimals`, not `not_whole_number`. A draft line was corrected.
  - Committed as "docs: V2 refactor plan, decisions and functional delta (Phase 0)".
- **Phase 1:**
  - V1 moved to `legacy/cli/` (`git mv`, shown as renames). `npm.cmd ci && npm.cmd test` there → 112/112; typecheck 0 errors.
  - `tools/reference.py` (REF-ET) checked in and made self-checking → 8/8 ok, sweep 6 800 / 767 / 0, exit 0.
  - Scaffolded `api/`, `backend/`, `frontend/`, `supabase/migrations/` (README only); `.gitignore` extended; root README rewritten.
  - Committed as "refactor: move V1 to legacy/cli and scaffold V2 parts (Phase 1)". `no-plan/` was left uncommitted.

## Prompt 28 — Restore extra payments

### Prompt

> im sorry, i deleted extra-payment, but it should be in it. can you return it?

### Output

- Interrupted Phase 2 (Prompt in progress: "Start Phase 2: port the calculation to Python in backend/, test-first."). Only the V1 sources and tests had been read; nothing was written in `backend/` yet. Phase 2 resumes next.
- Restored extra payments, with the Prompt 24 rule (an extra payment shortens the term; the regular payment stays the same):
  - `00-refactor-plan.md`: D7 = in scope; Phase 7 "Mimoriadna splátka" is back; Clean-up & CI is Phase 8 again (D6 and D10 point to it). Also restored: the `extraPayments` API field (no strategy field), the `extra_payments` table, the `domain/schedule.py` row and the extra-payment risk row. Fixed two headings that had lost their blank line in the removal.
  - `01-functional.md`: new FR-5 "Extra payment", with the questions the Phase 7 spec must answer; removed extra payments from the out-of-scope list.
  - `CLAUDE.md`, `legacy/cli/README.md`: `legacy/` is deleted in Phase 8. `backend/README.md`: Phase 7 added.
  - Updated `docs/handoff.md`.
- Committed as "docs: restore extra payments (FR-5, Phase 7) in the V2 plan".

## Prompt 29 — Phase 2: port the calculation to Python (interrupted)

### Prompt

> Start Phase 2: port the calculation to Python in backend/, test-first.

### Output

- Interrupted by Prompt 28 after reading the V1 sources and tests; nothing was written. Resumed in Prompt 30.

## Prompt 30 — Phase 2 resumed

### Prompt

> Resume Phase 2: port the calculation to Python in backend/, test-first.

### Output

- `backend/` is a `uv` project: Python 3.14, pytest 9.1.1 pinned, no runtime dependencies, `package = false`.
- **Red:** I wrote the tests first: `tests/input/test_parsing.py`, `test_validation.py`, `tests/domain/test_calculation.py`, `test_reference_parity.py`, `tests/app/test_calculator.py`, `tests/test_architecture.py`. All five modules that import `mortgage` failed to import.
- **Green:** `mortgage/domain/types.py`, `domain/calculation.py`, `input/parsing.py`, `input/validation.py`, `app/calculator.py` → **123 passed**.
- Port decisions:
  - The V1 test names and expected values are unchanged. Amounts are compared as 2-dp strings.
  - The private `Context(prec=40, ROUND_HALF_UP)` is entered with `localcontext()`, because Python applies the thread context to arithmetic.
  - The grammar check uses `fullmatch`; trimming uses exactly the JavaScript `trim()` set; `-0` is detected with `is_signed()`. Each has a new test.
  - M7 returns data (`Calculated` / `Rejected`), not views. Display moves to the frontend.
- Second guards added after a hand mutation check: a new zero-tail loan (found by search, confirmed by `tools/reference.py`), the private context, `-0`, and the whole-number check. 13 mutations; all caught by ≥ 2 tests.
- Parity: all 6 800 sweep loans equal `tools/reference.py` (pytest) and the V1 TypeScript code (`tools/v1_parity.py`, new) → 0 mismatches.
- Found: Windows Application Control blocks `.venv\Scripts\pytest.exe`, so tests run with `uv run python -m pytest` (documented in `backend/README.md`).
- Updated `backend/README.md` and `docs/handoff.md`. Committed as "feat: port calculation core to Python backend (Phase 2)".

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

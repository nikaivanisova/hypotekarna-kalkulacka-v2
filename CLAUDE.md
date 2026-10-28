# CLAUDE.md

Guidelines for working on this project.

## Project
- This is the **Mortgage Calculator V2**: a web app in four parts — frontend (JavaScript), API contract (OpenAPI), backend (Python) and Supabase.
- The plan is `docs/v2/00-refactor-plan.md`; the functional scope is `docs/v2/01-functional.md`. Keep scope to them.
- V1 (TypeScript CLI) is complete. `docs/v1/` is read-only history. The V1 code was removed in Phase 8 and is in git at tag `v1-final`.
- V2 is complete (`docs/v2/06-retro.md`). It runs locally (D10); there is no deployment.

## Calculation Rules
- Keep full precision in all intermediate calculations.
- **Round to cents (2 decimal places) only at the end of a calculation**, never in intermediate steps.
- All calculation and rounding happens in the backend. The frontend only formats amounts it receives.
- Money is never a float: `Decimal` in Python, decimal strings in the API (`"449.04"`), `numeric` in Postgres.

## Working Rules (from `docs/v1/06-retro.md` §6.1)
- The plan is the source of truth. If a prompt and the plan disagree, follow the plan and log the deviation.
- Every rule over a numeric domain gets a sweep test, not only examples.
- Every spec rule needs at least two tests that can fail; check by removing the rule.
- Every open question gets a decision before the build step that needs it.
- Concrete values in prompts are hypotheses: recompute them before use (`tools/reference.py`).

## Prompt Logging
- Log every prompt given for this project in `docs/v2/prompts.md`, in chronological order. (`docs/v1/prompts.md` is closed at Prompt 26.)

## Handoff
- Keep `docs/handoff.md` up to date with current state and next steps.

## Windows
- Use `npm.cmd` in PowerShell (`npm.ps1` is blocked by the execution policy).
- Python is 3.14, reached as `py` or through `uv`; the bare `python` command opens the Microsoft Store alias.
- Windows Application Control blocks `.venv\Scripts\pytest.exe` and some native wheels (e.g. `jsonschema_rs`): run tests as `uv run python -m pytest`.
- Playwright uses the installed Edge locally (`channel: 'msedge'`) and Chromium in CI (`PLAYWRIGHT_CHANNEL=chromium`).
- Write non-trivial scripts to a file instead of inline heredocs (quoting broke several edits in V2).

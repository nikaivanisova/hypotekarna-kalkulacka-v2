# Handoff

Notes for whoever picks up this project next: current state, open questions, and next steps.

## Current State

**Part A (Planning): complete.** **Part B (Build V1): ready to start**, at Step 1 of `docs/v1/05-plan.md`.

- Base project structure created (docs, README, CLAUDE.md, git repo).
- Layer 1 (functional definition) approved: `docs/v1/01-functional.md`.
- Layer 2 (architecture) complete: `docs/v1/02-architecture.md`.
  - Stack: Node.js 24 LTS + TypeScript (strict) + decimal.js + Vitest; tests run with `npm test`.
  - Platform: interactive CLI (ADR-1), with the UI isolated behind `app/calculator`.
  - 9 modules: `domain/types`, `domain/calculation` (pure, isolated), `input/parsing`, `input/validation`, `output/formatting`, `output/presentation`, `app/calculator`, `ui/cli`, `main`.
- Layer 3 (test scenarios) complete: `docs/v1/03-test-scenarios.md`.
  - Originally 95 scenarios (82 unit, 9 functional, 4 e2e); 112 after the review revision (see below).
  - Expected values verified with an independent Python `decimal` script (in the doc's appendix) and a separate Node.js PMT check.
  - Defines the exact UI texts (prompts, result labels, error messages) that the tests assert.
  - Note: the reference example P=100000, 3.5 %, 30y has Final 452.02 / Total Paid 161657.38 (not 449.04 / 161654.40); see the note in 03.
- Layer 4 (independent review) complete: `docs/v1/04-review.md`.
  - 24 findings: 1 Blocker, 5 Major, 18 Minor. Decisions are recorded for #1–#6; #7–#24 are still open.
  - **Blocker #1:** the §4.4 final-payment rule gives negative final payments for valid inputs (e.g. P = 1 000.29, 20 %, 30 y → Final −97.42).
  - Major: the M8 readline adapter breaks with piped stdin/EOF (e2e 89–92); the number grammar is undefined (decimal.js accepts `0x…`, `Infinity`, `NaN`); there is no domain-wide invariant test; extra payments and variable rates touch 5+ modules.
  - All financial reference values in 03 were re-verified with exact rational arithmetic: 0 errors.
- Review findings #1–#6 resolved (2026-10-21) and applied to 01/02/03:
  - #1 early termination when the amount due ≤ the regular payment (01 §4.4); #2 line-queue terminal reader (02 M8, ADR-10); #3 strict number grammar before decimal.js (01 §3.2, 02 M2); #4 property sweep (test 108; Final ≤ Regular only for early-terminated loans); #5/#6 accepted trade-offs (ADR-9, V2 schedule module).
  - 03 now has 112 tests (96–112 new) and reference REF-ET (exact rationals, Appendix B).
- Final execution plan complete: `docs/v1/05-plan.md`.
  - Goals G1–G4, all 112 test names mapped to 9 build steps, acceptance criteria AC-1–AC-7, a per-step Definition of Done, tooling, and risks.
- No source code exists yet.

## Open Questions
- Author decisions on findings #7–#24 in `docs/v1/04-review.md` (all Minor). Still undecided: `-0` (#9), space grouping / NBSP (#12), term `"10,0"` (#13), duplicated rounding and limits (#16, #17), the `ui → domain` rule (#18).
- Whether to display the number of payments when a loan ends early (V1 outputs do not show it).

## Next Steps
Part B, following `docs/v1/05-plan.md` section 3. Each step is test-first and ends with exactly one commit and a handoff update:
1. Scaffold + Types (M1) + architecture guard: tests 93–95 (3 total).
2. Parsing (M2): tests 1–16, 96–100 (24 total).
3. Validation (M3): tests 17–40, 101 (49 total).
4. Calculation (M4): tests 41–61, 102–108 (77 total).
5. Formatting (M5): tests 62–68 (84 total).
6. Presentation (M6): tests 69–79 (95 total).
7. Calculator facade (M7): tests 80–84, 109 (101 total).
8. CLI adapter (M8): tests 85–88, 111–112 (107 total).
9. Main + e2e (M9): tests 89–92, 110 (112 total).

**Current step: 1 (not started).**

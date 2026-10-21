# Handoff

Notes for whoever picks up this project next: current state, open questions, and next steps.

## Current State
- Base project structure created (docs, README, CLAUDE.md, git repo).
- Layer 1 (functional definition) approved: `docs/v1/01-functional.md`.
- Layer 2 (architecture) complete: `docs/v1/02-architecture.md`.
  - Stack: Node.js 24 LTS + TypeScript (strict) + decimal.js + Vitest; tests run with `npm test`.
  - Platform: interactive CLI (ADR-1), with the UI isolated behind `app/calculator`.
  - 9 modules: `domain/types`, `domain/calculation` (pure, isolated), `input/parsing`, `input/validation`, `output/formatting`, `output/presentation`, `app/calculator`, `ui/cli`, `main`.
- Layer 3 (test scenarios) complete: `docs/v1/03-test-scenarios.md`.
  - 95 scenarios (82 unit, 9 functional, 4 e2e) covering FR-1, FR-2 and FR-3, with edge cases and invalid inputs per module.
  - Expected values verified with an independent Python `decimal` script (in the doc's appendix) and a separate Node.js PMT check.
  - Defines the exact UI texts (prompts, result labels, error messages) that the tests assert.
  - Note: the reference example P=100000, 3.5 %, 30y has Final 452.02 / Total Paid 161657.38 (not 449.04 / 161654.40); see the note in 03.
- Layer 4 (independent review) complete: `docs/v1/04-review.md`.
  - 24 findings: 1 Blocker, 5 Major, 18 Minor. `Author Decision` / `Reason` columns await the author.
  - **Blocker #1:** the §4.4 final-payment rule gives negative final payments for valid inputs (e.g. P = 1 000.29, 20 %, 30 y → Final −97.42).
  - Major: the M8 readline adapter breaks with piped stdin/EOF (e2e 89–92); the number grammar is undefined (decimal.js accepts `0x…`, `Infinity`, `NaN`); there is no domain-wide invariant test; extra payments and variable rates touch 5+ modules.
  - All financial reference values in 03 were re-verified with exact rational arithmetic: 0 errors.
- Review findings #1–#6 resolved (2026-10-21) and applied to 01/02/03:
  - #1 early termination when the amount due ≤ the regular payment (01 §4.4); #2 line-queue terminal reader (02 M8, ADR-10); #3 strict number grammar before decimal.js (01 §3.2, 02 M2); #4 property sweep (test 108; Final ≤ Regular only for early-terminated loans); #5/#6 accepted trade-offs (ADR-9, V2 schedule module).
  - 03 now has 112 tests (96–112 new) and reference REF-ET (exact rationals, Appendix B).
- No source code exists yet.

## Open Questions
- Author decisions on findings #7–#24 in `docs/v1/04-review.md` (all Minor). Still undecided: `-0` (#9), space grouping / NBSP (#12), term `"10,0"` (#13), duplicated rounding and limits (#16, #17), the `ui → domain` rule (#18).
- Whether to display the number of payments when a loan ends early (V1 outputs do not show it).

## Next Steps
- Decide findings #7–#24 in `04-review.md` and update 01/02/03 where accepted.
- Scaffold the project: `package.json` (scripts `test`, `start`, `typecheck`), `tsconfig.json` (strict), install `decimal.js`, `vitest`, `tsx`, `typescript`.
- Implement test-first, module by module, using the test names from `03-test-scenarios.md` verbatim: M4 calculation → M2 parsing → M3 validation → M5 formatting → M6 presentation → M7 calculator → M8 CLI → M9 main → e2e.
- Add `tests/architecture.test.ts` (tests 93–95) to enforce the dependency rules.

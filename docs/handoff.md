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
- No source code exists yet.

## Open Questions
- None.

## Next Steps
- Scaffold the project: `package.json` (scripts `test`, `start`, `typecheck`), `tsconfig.json` (strict), install `decimal.js`, `vitest`, `tsx`, `typescript`.
- Implement test-first, module by module, using the test names from `03-test-scenarios.md` verbatim: M4 calculation → M2 parsing → M3 validation → M5 formatting → M6 presentation → M7 calculator → M8 CLI → M9 main → e2e.
- Add `tests/architecture.test.ts` (tests 93–95) to enforce the dependency rules.

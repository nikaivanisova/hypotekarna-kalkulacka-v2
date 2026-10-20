# Handoff

Notes for whoever picks up this project next: current state, open questions, and next steps.

## Current State
- Base project structure created (docs, README, CLAUDE.md, git repo).
- Layer 1 (functional definition) approved: `docs/v1/01-functional.md`.
- Layer 2 (architecture) complete: `docs/v1/02-architecture.md`.
  - Stack: Node.js 24 LTS + TypeScript (strict) + decimal.js + Vitest; tests run with `npm test`.
  - Platform: interactive CLI (ADR-1), with the UI isolated behind `app/calculator`.
  - 9 modules: `domain/types`, `domain/calculation` (pure, isolated), `input/parsing`, `input/validation`, `output/formatting`, `output/presentation`, `app/calculator`, `ui/cli`, `main`.
- No source code exists yet.

## Open Questions
- None. OQ-1 (Platform / UI) was resolved in Layer 2 as an interactive CLI.

## Next Steps
- Scaffold the project: `package.json` (scripts `test`, `start`, `typecheck`), `tsconfig.json` (strict), install `decimal.js`, `vitest`, `tsx`, `typescript`.
- Implement modules bottom-up with tests first: M4 calculation → M2 parsing → M3 validation → M5 formatting → M6 presentation → M7 calculator → M8 CLI → M9 main.
- Add `tests/architecture.test.ts` to enforce the dependency rules (section 4 of `02-architecture.md`).

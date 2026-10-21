/**
 * M7 — app/calculator (02-architecture.md §3, M7; 01-functional.md FR-3).
 *
 * Orchestrates one calculation request: raw inputs → validation → calculation → display-ready view.
 * Pure and synchronous; no I/O.
 */
import { calculateMortgage } from '../domain/calculation.js';
import type { RawLoanInput } from '../domain/types.js';
import { validateLoanInput } from '../input/validation.js';
import { toErrorView, toResultView, type ErrorView, type ResultView } from '../output/presentation.js';

export type CalculatorOutcome =
  | { readonly kind: 'result'; readonly view: ResultView }
  | { readonly kind: 'invalid'; readonly view: ErrorView };

/** Nothing is calculated until all inputs are valid (FR-3). */
export function runCalculator(raw: RawLoanInput): CalculatorOutcome {
  const validation = validateLoanInput(raw);
  if (!validation.ok) return { kind: 'invalid', view: toErrorView(validation.errors) };
  return { kind: 'result', view: toResultView(calculateMortgage(validation.value)) };
}

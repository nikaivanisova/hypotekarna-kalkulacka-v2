/**
 * M1 — Domain types (02-architecture.md §3, M1).
 *
 * The shared vocabulary for FR-1, FR-2 and FR-3. Types only: no runtime code.
 */
// Named import: under `module: NodeNext`, decimal.js's CommonJS typings make the default import a namespace.
import type { Decimal } from 'decimal.js';

export type Field = 'loanAmount' | 'annualRate' | 'termYears';

/** Exactly what the user typed; `undefined` means the field was not provided. */
export interface RawLoanInput {
  readonly loanAmount: string | undefined;
  readonly annualRate: string | undefined;
  readonly termYears: string | undefined;
}

/** A loan request that has passed validation (M3 is the only producer). */
export interface LoanInput {
  readonly principal: Decimal; // EUR, 1 000.00 – 1 000 000.00
  readonly annualRatePercent: Decimal; // 0.00 – 20.00
  readonly termYears: number; // integer, 1 – 30
}

/** All amounts are already rounded to cents (round half up). */
export interface MortgageResult {
  /** Payments actually made: termYears × 12, or fewer if the loan ends early (01 §4.4). */
  readonly numberOfPayments: number;
  /** M_rounded. */
  readonly regularPayment: Decimal;
  readonly finalPayment: Decimal;
  readonly totalPaid: Decimal;
  readonly totalInterest: Decimal;
}

export type ValidationErrorCode =
  | 'required'
  | 'not_a_number'
  | 'negative'
  | 'below_min'
  | 'above_max'
  | 'too_many_decimals'
  | 'not_whole_number';

export interface ValidationError {
  readonly field: Field;
  readonly code: ValidationErrorCode;
}

export type ValidationResult =
  | { readonly ok: true; readonly value: LoanInput }
  | { readonly ok: false; readonly errors: readonly ValidationError[] };

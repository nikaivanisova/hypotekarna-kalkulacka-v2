/**
 * M6 — Presentation (02-architecture.md §3, M6; 01-functional.md §2 Outputs, §3.3, §3.5).
 *
 * Turns calculation results or validation errors into display-ready English text.
 * Every text is the exact string from 03-test-scenarios.md, "Expected UI texts".
 */
import type { Field, MortgageResult, ValidationError, ValidationErrorCode } from '../domain/types.js';
import { formatMoney } from './formatting.js';

export interface ResultLine {
  readonly label: string; // e.g. "Regular Monthly Payment"
  readonly value: string; // e.g. "1 234,57 €"
}

export interface ResultView {
  readonly lines: readonly ResultLine[];
}

export interface FieldErrorView {
  readonly field: Field;
  readonly label: string; // e.g. "Loan amount"
  readonly message: string; // e.g. "Loan amount must be between 1 000,00 € and 1 000 000,00 €."
}

export interface ErrorView {
  readonly errors: readonly FieldErrorView[];
}

export const FIELD_LABELS: Readonly<Record<Field, string>> = {
  loanAmount: 'Loan amount',
  annualRate: 'Annual interest rate',
  termYears: 'Term',
};

/** Fields in the order their messages are shown. */
const FIELD_ORDER: readonly Field[] = ['loanAmount', 'annualRate', 'termYears'];

/** Range texts mirror V1_RULES in input/validation (output/ may not import input/, 02 §4 rule 3). */
const RANGE_MESSAGES: Readonly<Record<Field, string>> = {
  loanAmount: 'Loan amount must be between 1 000,00 € and 1 000 000,00 €.',
  annualRate: 'Annual interest rate must be between 0,00 % and 20,00 %.',
  termYears: 'Term must be between 1 and 30 years.',
};

/** All user-facing English texts (01 §3.5). */
const MESSAGES = {
  resultLabels: {
    regularPayment: 'Regular Monthly Payment',
    finalPayment: 'Final Payment',
    totalPaid: 'Total Paid',
    totalInterest: 'Total Interest',
  },
  errors: {
    required: (field) => `${FIELD_LABELS[field]} is required.`,
    not_a_number: (field) => `${FIELD_LABELS[field]} must be a number.`,
    negative: (field) => `${FIELD_LABELS[field]} must not be negative.`,
    below_min: (field) => RANGE_MESSAGES[field],
    above_max: (field) => RANGE_MESSAGES[field],
    too_many_decimals: (field) =>
      field === 'termYears'
        ? 'Term must be a whole number of years.'
        : `${FIELD_LABELS[field]} can have at most 2 decimal places.`,
    not_whole_number: () => 'Term must be a whole number of years.',
  } satisfies Record<ValidationErrorCode, (field: Field) => string>,
} as const;

/** True when |finalPayment − regularPayment| ≥ €0.01 (01 §2, Outputs). */
export function shouldShowFinalPayment(result: MortgageResult): boolean {
  return result.finalPayment.minus(result.regularPayment).abs().greaterThanOrEqualTo(0.01);
}

/** Output order: Regular Monthly Payment, Final Payment (only if shown), Total Paid, Total Interest. */
export function toResultView(result: MortgageResult): ResultView {
  const labels = MESSAGES.resultLabels;
  const lines: ResultLine[] = [{ label: labels.regularPayment, value: formatMoney(result.regularPayment) }];
  if (shouldShowFinalPayment(result)) {
    lines.push({ label: labels.finalPayment, value: formatMoney(result.finalPayment) });
  }
  lines.push(
    { label: labels.totalPaid, value: formatMoney(result.totalPaid) },
    { label: labels.totalInterest, value: formatMoney(result.totalInterest) },
  );
  return { lines };
}

/** One message per invalid field (the first error given for it), in field order. */
export function toErrorView(errors: readonly ValidationError[]): ErrorView {
  return {
    errors: FIELD_ORDER.flatMap((field) => {
      const error = errors.find((e) => e.field === field);
      return error ? [{ field, label: FIELD_LABELS[field], message: MESSAGES.errors[error.code](field) }] : [];
    }),
  };
}

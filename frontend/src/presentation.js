/**
 * M6 — Presentation (docs/v1/01-functional.md §2 Outputs, §3.3, §3.5), ported from legacy/cli.
 *
 * Turns an API CalculationResult or validation errors into display-ready English text.
 * The V1 texts are the exact strings from docs/v1/03-test-scenarios.md, "Expected UI texts".
 */
import { formatMoney } from './formatting.js';

/** The inputs, in the order their messages are shown. */
export const FIELDS = ['loanAmount', 'annualRate', 'termYears'];

export const FIELD_LABELS = {
  loanAmount: 'Loan amount',
  annualRate: 'Annual interest rate',
  termYears: 'Term',
};

/** Form labels: the V1 CLI prompts without the trailing ": ". */
export const INPUT_LABELS = {
  loanAmount: 'Loan amount (EUR)',
  annualRate: 'Annual interest rate (%)',
  termYears: 'Term (years)',
};

/** Range texts mirror the backend's V1_RULES (backend/mortgage/input/validation.py). */
const RANGE_MESSAGES = {
  loanAmount: 'Loan amount must be between 1 000,00 € and 1 000 000,00 €.',
  annualRate: 'Annual interest rate must be between 0,00 % and 20,00 %.',
  termYears: 'Term must be between 1 and 30 years.',
};

/** All user-facing English texts (01 §3.5, D8). */
export const MESSAGES = {
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
  },
  // New in V2 (contract: the error vocabulary is open; other statuses show one general message).
  unknownCode: (field) => `${FIELD_LABELS[field]} is invalid.`,
  invalidInput: 'Some of the input is not valid. Please check the form.',
  failure: 'The calculation could not be completed. Please try again later.',
  calculate: 'Calculate',
  resultHeading: 'Result',
};

/**
 * True when |finalPayment − regularPayment| ≥ €0.01 (01 §2, Outputs). Both are canonical 2-dp
 * strings (contract Money), so they differ by at least one cent exactly when the strings differ.
 */
export function shouldShowFinalPayment(result) {
  return result.finalPayment !== result.regularPayment;
}

/** Output order: Regular Monthly Payment, Final Payment (only if shown), Total Paid, Total Interest. */
export function toResultView(result) {
  const labels = MESSAGES.resultLabels;
  const lines = [{ label: labels.regularPayment, value: formatMoney(result.regularPayment) }];
  if (shouldShowFinalPayment(result)) {
    lines.push({ label: labels.finalPayment, value: formatMoney(result.finalPayment) });
  }
  lines.push(
    { label: labels.totalPaid, value: formatMoney(result.totalPaid) },
    { label: labels.totalInterest, value: formatMoney(result.totalInterest) },
  );
  return { lines };
}

function messageFor(field, code) {
  // Object.hasOwn: a code such as "toString" must not reach Object.prototype.
  return Object.hasOwn(MESSAGES.errors, code) ? MESSAGES.errors[code](field) : MESSAGES.unknownCode(field);
}

/**
 * One message per known field (the first error given for it), in field order.
 * Errors for fields this page does not know (e.g. Phase 7 `extraPayments`) give the general message.
 */
export function toErrorView(errors) {
  const fieldErrors = FIELDS.flatMap((field) => {
    const error = errors.find((e) => e.field === field);
    return error ? [{ field, label: FIELD_LABELS[field], message: messageFor(field, error.code) }] : [];
  });
  const hasUnknownField = errors.some((e) => !FIELDS.includes(e.field));
  return { errors: fieldErrors, general: hasUnknownField ? MESSAGES.invalidInput : null };
}

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
  // Phase 7: extra payments (docs/v2/04-extra-payments.md §4.2–4.3).
  extra: {
    legend: 'Extra payments (optional)',
    help: 'If several extra payments are in the same month, the first one entered is used first.',
    add: 'Add extra payment',
    remove: 'Remove',
    month: 'Month',
    amount: 'Amount (EUR)',
    paidOffAfter: 'Loan paid off after',
    timeSaved: 'Time saved',
    timeSavedNone: 'none',
    interestSaved: 'Interest saved',
  },
  notes: {
    partly_used: (e) => `Extra payment in month ${e.month}: only ${formatMoney(e.usedAmount)} of ${formatMoney(e.amount)} was needed to pay off the loan.`,
    after_payoff: (e) => `Extra payment in month ${e.month} (${formatMoney(e.amount)}) was not used: the loan was already paid off.`,
    loan_ends_this_month: (e) => `Extra payment in month ${e.month} (${formatMoney(e.amount)}) was not needed: the loan ends with this month's regular payment.`,
    tiny_balance: (e) => `Extra payment in month ${e.month} (${formatMoney(e.amount)}) was not needed: less than half a cent was still owed after the regular payment.`,
    covered_by_earlier: (e) => `Extra payment in month ${e.month} (${formatMoney(e.amount)}) was not needed: an earlier extra payment in the same month already paid off the loan.`,
  },
  unknownNote: (e) => `Extra payment in month ${e.month} (${formatMoney(e.amount)}): see the result above.`,
  itemErrors: {
    month: {
      required: 'month is required.',
      not_a_number: 'month must be a number.',
      negative: 'month must not be negative.',
      below_min: 'month must be between 1 and the last month of the loan term.',
      above_max: 'month must be between 1 and the last month of the loan term.',
      too_many_decimals: 'month must be a whole number.',
      not_whole_number: 'month must be a whole number.',
    },
    amount: {
      required: 'amount is required.',
      not_a_number: 'amount must be a number.',
      negative: 'amount must not be negative.',
      below_min: 'amount must be between 0,01 € and 1 000 000,00 €.',
      above_max: 'amount must be between 0,01 € and 1 000 000,00 €.',
      too_many_decimals: 'amount can have at most 2 decimal places.',
      not_whole_number: 'amount can have at most 2 decimal places.',
    },
  },
};

const ITEM_PROPERTIES = ['month', 'amount'];

const plural = (count, one, many) => `${count} ${count === 1 ? one : many}`;

/**
 * A whole number of months as years and months (04 §4.2): "1 year", "2 years 4 months", "11 months".
 * Integer arithmetic on a count of months, never on money.
 */
export function formatDuration(months) {
  const rest = months % 12;
  const years = (months - rest) / 12;
  const parts = [];
  if (years > 0) parts.push(plural(years, 'year', 'years'));
  if (rest > 0) parts.push(plural(rest, 'month', 'months'));
  return parts.join(' ');
}

export function formatPayments(count) {
  return `(${plural(count, 'payment', 'payments')})`;
}

function noteFor(item) {
  // Object.hasOwn: a status such as "toString" must not reach Object.prototype.
  return Object.hasOwn(MESSAGES.notes, item.status) ? MESSAGES.notes[item.status](item) : MESSAGES.unknownNote(item);
}

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
  // Phase 7: extra lines and notes only when the result has extra payments (04 §4.2).
  const extras = Array.isArray(result.extraPayments) ? result.extraPayments : [];
  if (extras.length === 0) return { lines, notes: [] };
  const extra = MESSAGES.extra;
  lines.push(
    { label: extra.paidOffAfter, value: `${formatDuration(result.numberOfPayments)} ${formatPayments(result.numberOfPayments)}` },
    { label: extra.timeSaved, value: result.monthsSaved > 0 ? formatDuration(result.monthsSaved) : extra.timeSavedNone },
    { label: extra.interestSaved, value: formatMoney(result.interestSaved) },
  );
  return { lines, notes: extras.filter((item) => item.status !== 'used').map(noteFor) };
}

function messageFor(field, code) {
  // Object.hasOwn: a code such as "toString" must not reach Object.prototype.
  return Object.hasOwn(MESSAGES.errors, code) ? MESSAGES.errors[code](field) : MESSAGES.unknownCode(field);
}

/**
 * One message per known field (the first error given for it), in field order, plus one message per
 * extra-payment item error. `rowOf(index)` gives the form row (1-based) the sent item came from (04 §2).
 * Errors the page cannot place (an unknown field, or an item error without a usable index or
 * property) give the general message.
 */
export function toErrorView(errors, rowOf = (index) => index + 1) {
  const fieldErrors = FIELDS.flatMap((field) => {
    const error = errors.find((e) => e.field === field);
    return error ? [{ field, label: FIELD_LABELS[field], message: messageFor(field, error.code) }] : [];
  });
  const itemErrors = [];
  let unplaced = false;
  for (const error of errors) {
    if (FIELDS.includes(error.field)) continue;
    const row = error.field === 'extraPayments' && Number.isInteger(error.index) ? rowOf(error.index) : undefined;
    if (row === undefined || !ITEM_PROPERTIES.includes(error.property)) {
      unplaced = true;
      continue;
    }
    const texts = MESSAGES.itemErrors[error.property];
    const text = Object.hasOwn(texts, error.code) ? texts[error.code] : `${error.property} is invalid.`;
    itemErrors.push({ index: error.index, property: error.property, message: `Extra payment ${row}: ${text}` });
  }
  return { errors: fieldErrors, itemErrors, general: unplaced ? MESSAGES.invalidInput : null };
}

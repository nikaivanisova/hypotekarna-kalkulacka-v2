/**
 * Phase 7 — extra payments on the page: durations, result lines, notes and item errors
 * (docs/v2/04-extra-payments.md §4.2–4.3). The page does no arithmetic on Money: it shows the
 * API's `status`, `usedAmount` and `amount` as received; durations come from integers.
 */
import { describe, expect, it } from 'vitest';
import { formatDuration, formatPayments, toErrorView, toResultView, MESSAGES } from '../../src/presentation.js';

const E1 = {
  id: null, numberOfPayments: 332, regularPayment: '449.04', finalPayment: '246.84', totalPaid: '153879.08',
  totalInterest: '53879.08', monthsSaved: 28, interestSaved: '7778.30',
  extraPayments: [{ month: 24, amount: '5000.00', usedAmount: '5000.00', status: 'used' }],
};

const E3 = {
  id: null, numberOfPayments: 60, regularPayment: '449.04', finalPayment: '90146.42', totalPaid: '116639.78',
  totalInterest: '16639.78', monthsSaved: 300, interestSaved: '45017.60',
  extraPayments: [
    { month: 60, amount: '50000.00', usedAmount: '50000.00', status: 'used' },
    { month: 60, amount: '50000.00', usedAmount: '39697.38', status: 'partly_used' },
    { month: 120, amount: '1000.00', usedAmount: '0.00', status: 'after_payoff' },
  ],
};

const lines = (result) => toResultView(result).lines.map((l) => `${l.label}: ${l.value}`);

describe('durations (04 §4.2)', () => {
  it.each([
    [1, '1 month'], [2, '2 months'], [11, '11 months'], [12, '1 year'], [13, '1 year 1 month'],
    [24, '2 years'], [28, '2 years 4 months'], [300, '25 years'], [332, '27 years 8 months'], [359, '29 years 11 months'],
  ])('test_duration_%i_months', (months, text) => {
    expect(formatDuration(months)).toBe(text);
  });

  it.each([[1, '(1 payment)'], [2, '(2 payments)'], [332, '(332 payments)']])('test_payments_%i', (n, text) => {
    expect(formatPayments(n)).toBe(text);
  });
});

describe('result with extra payments (04 §4.2)', () => {
  it('test_result_lines_with_extra_payments', () => {
    expect(lines(E1)).toEqual([
      'Regular Monthly Payment: 449,04 €',
      'Final Payment: 246,84 €',
      'Total Paid: 153 879,08 €',
      'Total Interest: 53 879,08 €',
      'Loan paid off after: 27 years 8 months (332 payments)',
      'Time saved: 2 years 4 months',
      'Interest saved: 7 778,30 €',
    ]);
    expect(toResultView(E1).notes).toEqual([]);
  });

  it('test_result_without_extra_payments_is_the_v1_view', () => {
    const v1 = { ...E1, numberOfPayments: 360, finalPayment: '452.02', totalPaid: '161657.38', totalInterest: '61657.38',
      monthsSaved: 0, interestSaved: '0.00', extraPayments: [] };
    expect(lines(v1)).toEqual([
      'Regular Monthly Payment: 449,04 €',
      'Final Payment: 452,02 €',
      'Total Paid: 161 657,38 €',
      'Total Interest: 61 657,38 €',
    ]);
    expect(toResultView(v1).notes).toEqual([]);
  });

  it('test_result_from_an_older_server_without_the_new_fields_is_the_v1_view', () => {
    const { monthsSaved, interestSaved, extraPayments, ...old } = E1;
    expect(lines(old)).toHaveLength(4);
  });

  it('test_time_saved_none', () => {
    const r = { ...E1, monthsSaved: 0, extraPayments: [{ month: 360, amount: '100.00', usedAmount: '0.00', status: 'loan_ends_this_month' }] };
    expect(lines(r)).toContain('Time saved: none');
  });

  it('test_notes_for_each_item_that_is_not_used', () => {
    expect(toResultView(E3).notes).toEqual([
      'Extra payment in month 60: only 39 697,38 € of 50 000,00 € was needed to pay off the loan.',
      'Extra payment in month 120 (1 000,00 €) was not used: the loan was already paid off.',
    ]);
  });

  it.each([
    ['loan_ends_this_month', 'Extra payment in month 360 (100,00 €) was not needed: the loan ends with this month\'s regular payment.'],
    ['tiny_balance', 'Extra payment in month 360 (100,00 €) was not needed: less than half a cent was still owed after the regular payment.'],
    ['covered_by_earlier', 'Extra payment in month 360 (100,00 €) was not needed: an earlier extra payment in the same month already paid off the loan.'],
    ['some_future_status', 'Extra payment in month 360 (100,00 €): see the result above.'],
  ])('test_note_for_status_%s', (status, note) => {
    const r = { ...E1, extraPayments: [{ month: 360, amount: '100.00', usedAmount: '0.00', status }] };
    expect(toResultView(r).notes).toEqual([note]);
  });

  it.each(['toString', 'constructor', 'hasOwnProperty'])('test_note_lookup_ignores_prototype_names (%s)', (status) => {
    const r = { ...E1, extraPayments: [{ month: 2, amount: '1.00', usedAmount: '0.00', status }] };
    expect(toResultView(r).notes).toEqual(['Extra payment in month 2 (1,00 €): see the result above.']);
  });

  it('test_time_saved_none_with_a_tiny_balance_item', () => {
    const r = { ...E1, monthsSaved: 0, interestSaved: '0.00',
      extraPayments: [{ month: 5, amount: '1.00', usedAmount: '0.00', status: 'tiny_balance' }] };
    expect(lines(r)[lines(r).length - 2]).toBe('Time saved: none');
  });
});

describe('item errors (04 §4.3)', () => {
  // The page sent rows 2 and 3 of the form as items 0 and 1 (row 1 was blank).
  const rowOf = (index) => [2, 3][index];

  it('test_item_errors_name_the_form_row', () => {
    const view = toErrorView([
      { field: 'extraPayments', index: 0, property: 'month', code: 'not_a_number' },
      { field: 'extraPayments', index: 1, property: 'amount', code: 'too_many_decimals' },
    ], rowOf);
    expect(view.itemErrors).toEqual([
      { index: 0, property: 'month', message: 'Extra payment 2: month must be a number.' },
      { index: 1, property: 'amount', message: 'Extra payment 3: amount can have at most 2 decimal places.' },
    ]);
    expect(view.general).toBeNull();
  });

  it.each([
    ['month', 'required', 'Extra payment 2: month is required.'],
    ['month', 'negative', 'Extra payment 2: month must not be negative.'],
    ['month', 'below_min', 'Extra payment 2: month must be between 1 and the last month of the loan term.'],
    ['month', 'above_max', 'Extra payment 2: month must be between 1 and the last month of the loan term.'],
    ['month', 'not_whole_number', 'Extra payment 2: month must be a whole number.'],
    ['month', 'too_many_decimals', 'Extra payment 2: month must be a whole number.'],
    ['amount', 'required', 'Extra payment 2: amount is required.'],
    ['amount', 'not_a_number', 'Extra payment 2: amount must be a number.'],
    ['amount', 'negative', 'Extra payment 2: amount must not be negative.'],
    ['amount', 'below_min', 'Extra payment 2: amount must be between 0,01 € and 1 000 000,00 €.'],
    ['amount', 'above_max', 'Extra payment 2: amount must be between 0,01 € and 1 000 000,00 €.'],
    ['amount', 'too_many_decimals', 'Extra payment 2: amount can have at most 2 decimal places.'],
    ['month', 'future_code', 'Extra payment 2: month is invalid.'],
    ['amount', 'constructor', 'Extra payment 2: amount is invalid.'],
    ['month', 'toString', 'Extra payment 2: month is invalid.'],
    ['amount', '__proto__', 'Extra payment 2: amount is invalid.'],
  ])('test_item_message_%s_%s', (property, code, message) => {
    const view = toErrorView([{ field: 'extraPayments', index: 0, property, code }], rowOf);
    expect(view.itemErrors[0].message).toBe(message);
  });

  it.each([
    [{ field: 'extraPayments', code: 'required', property: 'month' }],
    [{ field: 'extraPayments', code: 'required', index: 0 }],
    [{ field: 'extraPayments', code: 'required', index: 0, property: 'fee' }],
    [{ field: 'extraPayments', code: 'required', index: 7, property: 'month' }],
  ])('test_item_error_without_a_usable_index_or_property_gives_the_general_message (%j)', (error) => {
    const view = toErrorView([error], rowOf);
    expect(view.itemErrors).toEqual([]);
    expect(view.general).toBe(MESSAGES.invalidInput);
  });

  it('test_v1_field_errors_are_unchanged_next_to_item_errors', () => {
    const view = toErrorView([
      { field: 'termYears', code: 'required' },
      { field: 'extraPayments', index: 0, property: 'month', code: 'required' },
    ], rowOf);
    expect(view.errors.map((e) => e.message)).toEqual(['Term is required.']);
    expect(view.itemErrors).toHaveLength(1);
  });
});

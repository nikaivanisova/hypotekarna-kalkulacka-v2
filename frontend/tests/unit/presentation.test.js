/**
 * M6 — presentation (docs/v1/03-test-scenarios.md tests 69–79; "Expected UI texts"), ported from legacy/cli.
 *
 * Results arrive as the API's CalculationResult (Money as 2-dp strings).
 */
import { describe, expect, it } from 'vitest';
import { MESSAGES, shouldShowFinalPayment, toErrorView, toResultView } from '../../src/presentation.js';

function result(regular, final, totalPaid = '0.00', totalInterest = '0.00', numberOfPayments = 360) {
  return { id: null, numberOfPayments, regularPayment: regular, finalPayment: final, totalPaid, totalInterest };
}

const resultLines = (r) => toResultView(r).lines.map((line) => `${line.label}: ${line.value}`);
const messageFor = (error) => toErrorView([error]).errors[0]?.message;

describe('presentation (M6)', () => {
  it('test_show_final_payment_when_one_cent_different', () => {
    expect(shouldShowFinalPayment(result('844.66', '844.67'))).toBe(true);
  });

  it('test_hide_final_payment_when_equal', () => {
    expect(shouldShowFinalPayment(result('180.80', '180.80'))).toBe(false);
  });

  it('test_show_final_payment_when_lower', () => {
    expect(shouldShowFinalPayment(result('1791.08', '1789.99'))).toBe(true);
  });

  it('test_result_view_with_final_payment', () => {
    expect(resultLines(result('449.04', '452.02', '161657.38', '61657.38'))).toEqual([
      'Regular Monthly Payment: 449,04 €',
      'Final Payment: 452,02 €',
      'Total Paid: 161 657,38 €',
      'Total Interest: 61 657,38 €',
    ]);
  });

  it('test_result_view_without_final_payment', () => {
    expect(resultLines(result('180.80', '180.80', '10848.00', '848.00', 60))).toEqual([
      'Regular Monthly Payment: 180,80 €',
      'Total Paid: 10 848,00 €',
      'Total Interest: 848,00 €',
    ]);
  });

  it('test_error_view_required_message', () => {
    expect(toErrorView([{ field: 'loanAmount', code: 'required' }]).errors).toEqual([
      { field: 'loanAmount', label: 'Loan amount', message: 'Loan amount is required.' },
    ]);
  });

  it('test_error_view_not_a_number_message', () => {
    expect(messageFor({ field: 'annualRate', code: 'not_a_number' })).toBe('Annual interest rate must be a number.');
  });

  it('test_error_view_negative_message', () => {
    expect(messageFor({ field: 'loanAmount', code: 'negative' })).toBe('Loan amount must not be negative.');
  });

  it('test_error_view_range_messages', () => {
    expect(messageFor({ field: 'loanAmount', code: 'below_min' })).toBe(
      'Loan amount must be between 1 000,00 € and 1 000 000,00 €.',
    );
    expect(messageFor({ field: 'annualRate', code: 'above_max' })).toBe(
      'Annual interest rate must be between 0,00 % and 20,00 %.',
    );
    expect(messageFor({ field: 'termYears', code: 'above_max' })).toBe('Term must be between 1 and 30 years.');
  });

  it('test_error_view_decimal_messages', () => {
    expect(messageFor({ field: 'annualRate', code: 'too_many_decimals' })).toBe(
      'Annual interest rate can have at most 2 decimal places.',
    );
    expect(messageFor({ field: 'termYears', code: 'not_whole_number' })).toBe('Term must be a whole number of years.');
    expect(messageFor({ field: 'termYears', code: 'too_many_decimals' })).toBe('Term must be a whole number of years.');
  });

  it('test_error_view_one_message_per_field_in_field_order', () => {
    const view = toErrorView([
      { field: 'termYears', code: 'below_min' },
      { field: 'loanAmount', code: 'required' },
    ]);
    expect(view.errors.map((e) => e.label)).toEqual(['Loan amount', 'Term']);
  });

  // --- New in V2: open error vocabulary (contract `Field`, `ValidationErrorCode`) ---

  it('test_error_view_unknown_code_gets_a_generic_field_message', () => {
    expect(messageFor({ field: 'annualRate', code: 'some_future_code' })).toBe('Annual interest rate is invalid.');
  });

  it.each(['toString', 'constructor', '__proto__', 'hasOwnProperty'])(
    'test_error_view_prototype_names_are_unknown_codes (%s)', (code) => {
      expect(messageFor({ field: 'termYears', code })).toBe('Term is invalid.');
    },
  );

  it('test_error_view_unknown_field_gets_the_general_message', () => {
    const view = toErrorView([{ field: 'extraPayments', code: 'above_max', index: 0 }, { field: 'termYears', code: 'required' }]);
    expect(view.errors.map((e) => e.field)).toEqual(['termYears']);
    expect(view.general).toBe(MESSAGES.invalidInput);
  });

  it('test_error_view_known_fields_only_has_no_general_message', () => {
    expect(toErrorView([{ field: 'loanAmount', code: 'required' }]).general).toBeNull();
  });

  it('test_final_payment_rule_compares_strings_not_numbers', () => {
    // Canonical 2-dp strings differ exactly when the amounts differ by >= 0.01.
    expect(shouldShowFinalPayment(result('0.10', '0.10'))).toBe(false);
    expect(shouldShowFinalPayment(result('16710.19', '16638.10'))).toBe(true);
  });
});

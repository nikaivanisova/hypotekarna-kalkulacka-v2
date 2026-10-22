/**
 * M6 — output/presentation (03-test-scenarios.md tests 69–79; "Expected UI texts").
 */
import { Decimal } from 'decimal.js';
import { describe, expect, it } from 'vitest';
import type { MortgageResult, ValidationError } from '../../src/domain/types.js';
import { shouldShowFinalPayment, toErrorView, toResultView } from '../../src/output/presentation.js';

function result(
  regular: string,
  final: string,
  totalPaid = '0',
  totalInterest = '0',
  numberOfPayments = 360,
): MortgageResult {
  return {
    numberOfPayments,
    regularPayment: new Decimal(regular),
    finalPayment: new Decimal(final),
    totalPaid: new Decimal(totalPaid),
    totalInterest: new Decimal(totalInterest),
  };
}

function resultLines(mortgage: MortgageResult): string[] {
  return toResultView(mortgage).lines.map((line) => `${line.label}: ${line.value}`);
}

function messageFor(error: ValidationError): string | undefined {
  return toErrorView([error]).errors[0]?.message;
}

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
});

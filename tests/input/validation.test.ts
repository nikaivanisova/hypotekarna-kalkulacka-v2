/**
 * M3 — input/validation (03-test-scenarios.md tests 17–40, 101).
 */
import { Decimal } from 'decimal.js';
import { describe, expect, it } from 'vitest';
import type { LoanInput, RawLoanInput, ValidationError } from '../../src/domain/types.js';
import { validateLoanInput } from '../../src/input/validation.js';

/** Valid values for the fields a scenario does not mention. */
const VALID: RawLoanInput = { loanAmount: '100000', annualRate: '3', termYears: '10' };

type Overrides = { readonly [K in keyof RawLoanInput]?: string | undefined };

function expectValid(overrides: Overrides): LoanInput {
  const result = validateLoanInput({ ...VALID, ...overrides });
  if (!result.ok) throw new Error(`expected valid input, got ${JSON.stringify(result.errors)}`);
  return result.value;
}

function expectErrors(overrides: Overrides, errors: readonly ValidationError[]): void {
  expect(validateLoanInput({ ...VALID, ...overrides })).toEqual({ ok: false, errors });
}

function expectDecimal(actual: Decimal, expected: string): void {
  expect(actual.equals(new Decimal(expected)), `${actual.toString()} = ${expected}`).toBe(true);
}

describe('validation (M3)', () => {
  it('test_validate_all_valid_inputs', () => {
    const value = expectValid({ loanAmount: '100 000', annualRate: '3,5', termYears: '30' });
    expectDecimal(value.principal, '100000');
    expectDecimal(value.annualRatePercent, '3.5');
    expect(value.termYears).toBe(30);
  });

  it('test_validate_loan_min_inclusive', () => {
    expectDecimal(expectValid({ loanAmount: '1000', annualRate: '3', termYears: '10' }).principal, '1000');
  });

  it('test_validate_loan_max_inclusive', () => {
    expectDecimal(expectValid({ loanAmount: '1 000 000,00', annualRate: '3', termYears: '10' }).principal, '1000000');
  });

  it('test_validate_loan_below_min', () => {
    expectErrors({ loanAmount: '999,99' }, [{ field: 'loanAmount', code: 'below_min' }]);
  });

  it('test_validate_loan_above_max', () => {
    expectErrors({ loanAmount: '1000000,01' }, [{ field: 'loanAmount', code: 'above_max' }]);
  });

  it('test_validate_loan_negative', () => {
    expectErrors({ loanAmount: '-100000' }, [{ field: 'loanAmount', code: 'negative' }]);
  });

  it('test_validate_loan_too_many_decimals', () => {
    expectErrors({ loanAmount: '100000,555' }, [{ field: 'loanAmount', code: 'too_many_decimals' }]);
  });

  it('test_validate_loan_written_trailing_zero_decimals', () => {
    expectErrors({ loanAmount: '100000,500' }, [{ field: 'loanAmount', code: 'too_many_decimals' }]);
  });

  it('test_validate_rate_zero_inclusive', () => {
    const value = expectValid({ loanAmount: '100000', annualRate: '0', termYears: '10' });
    expectDecimal(value.annualRatePercent, '0');
  });

  it('test_validate_rate_max_inclusive', () => {
    const value = expectValid({ loanAmount: '100000', annualRate: '20,00', termYears: '10' });
    expectDecimal(value.annualRatePercent, '20');
  });

  it('test_validate_rate_above_max', () => {
    expectErrors({ annualRate: '20,01' }, [{ field: 'annualRate', code: 'above_max' }]);
  });

  it('test_validate_rate_negative', () => {
    expectErrors({ annualRate: '-0,5' }, [{ field: 'annualRate', code: 'negative' }]);
  });

  it('test_validate_rate_too_many_decimals', () => {
    expectErrors({ annualRate: '3,555' }, [{ field: 'annualRate', code: 'too_many_decimals' }]);
  });

  it('test_validate_term_min_inclusive', () => {
    expect(expectValid({ loanAmount: '100000', annualRate: '3', termYears: '1' }).termYears).toBe(1);
  });

  it('test_validate_term_max_inclusive', () => {
    expect(expectValid({ loanAmount: '100000', annualRate: '3', termYears: '30' }).termYears).toBe(30);
  });

  it('test_validate_term_zero', () => {
    expectErrors({ termYears: '0' }, [{ field: 'termYears', code: 'below_min' }]);
  });

  it('test_validate_term_above_max', () => {
    expectErrors({ termYears: '31' }, [{ field: 'termYears', code: 'above_max' }]);
  });

  it('test_validate_term_fractional', () => {
    expectErrors({ termYears: '2,5' }, [{ field: 'termYears', code: 'not_whole_number' }]);
  });

  it('test_validate_term_with_zero_decimal', () => {
    expectErrors({ termYears: '10,0' }, [{ field: 'termYears', code: 'too_many_decimals' }]);
  });

  it('test_validate_term_text', () => {
    expectErrors({ termYears: 'thirty' }, [{ field: 'termYears', code: 'not_a_number' }]);
  });

  it('test_validate_missing_field', () => {
    expectErrors({ loanAmount: '100000', annualRate: '3', termYears: undefined }, [
      { field: 'termYears', code: 'required' },
    ]);
  });

  it('test_validate_all_fields_empty', () => {
    expectErrors({ loanAmount: '', annualRate: '', termYears: '' }, [
      { field: 'loanAmount', code: 'required' },
      { field: 'annualRate', code: 'required' },
      { field: 'termYears', code: 'required' },
    ]);
  });

  it('test_validate_multiple_invalid_fields', () => {
    expectErrors({ loanAmount: 'abc', annualRate: '25', termYears: '0' }, [
      { field: 'loanAmount', code: 'not_a_number' },
      { field: 'annualRate', code: 'above_max' },
      { field: 'termYears', code: 'below_min' },
    ]);
  });

  it('test_validate_one_error_per_field', () => {
    expectErrors({ loanAmount: '-1000,555' }, [{ field: 'loanAmount', code: 'negative' }]);
  });

  it('test_validate_hex_loan_amount_rejected', () => {
    expectErrors({ loanAmount: '0x3E8', annualRate: '3', termYears: '10' }, [
      { field: 'loanAmount', code: 'not_a_number' },
    ]);
  });
});

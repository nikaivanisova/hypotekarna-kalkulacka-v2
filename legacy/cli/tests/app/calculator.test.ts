/**
 * M7 — app/calculator (03-test-scenarios.md tests 80–84, 109).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { runCalculator, type CalculatorOutcome } from '../../src/app/calculator.js';
import { calculateMortgage } from '../../src/domain/calculation.js';
import type { RawLoanInput } from '../../src/domain/types.js';

// vi.spyOn cannot replace an ES module export, so wrap the real function in a mock (05-plan §6.2).
vi.mock('../../src/domain/calculation.js', async (importOriginal) => {
  const mod = await importOriginal<typeof import('../../src/domain/calculation.js')>();
  return { ...mod, calculateMortgage: vi.fn(mod.calculateMortgage) };
});

function raw(
  loanAmount: string | undefined,
  annualRate: string | undefined,
  termYears: string | undefined,
): RawLoanInput {
  return { loanAmount, annualRate, termYears };
}

function resultLines(outcome: CalculatorOutcome): string[] {
  if (outcome.kind !== 'result') throw new Error(`Expected kind "result", got "${outcome.kind}"`);
  return outcome.view.lines.map((line) => `${line.label}: ${line.value}`);
}

function errorMessages(outcome: CalculatorOutcome): string[] {
  if (outcome.kind !== 'invalid') throw new Error(`Expected kind "invalid", got "${outcome.kind}"`);
  return outcome.view.errors.map((error) => error.message);
}

describe('calculator (M7)', () => {
  beforeEach(() => {
    vi.mocked(calculateMortgage).mockClear();
  });

  it('test_calculator_valid_input_returns_result', () => {
    const outcome = runCalculator(raw('100 000', '3,5', '30'));
    expect(outcome.kind).toBe('result');
    expect(resultLines(outcome)).toEqual([
      'Regular Monthly Payment: 449,04 €',
      'Final Payment: 452,02 €',
      'Total Paid: 161 657,38 €',
      'Total Interest: 61 657,38 €',
    ]);
    expect(calculateMortgage).toHaveBeenCalledTimes(1);
  });

  it('test_calculator_zero_rate_full_flow', () => {
    const outcome = runCalculator(raw('1 000', '0', '1'));
    expect(outcome.kind).toBe('result');
    expect(resultLines(outcome)).toEqual([
      'Regular Monthly Payment: 83,33 €',
      'Final Payment: 83,37 €',
      'Total Paid: 1 000,00 €',
      'Total Interest: 0,00 €',
    ]);
  });

  it('test_calculator_invalid_input_skips_calculation', () => {
    const outcome = runCalculator(raw('-100000', '3,5', '30'));
    expect(outcome.kind).toBe('invalid');
    expect(errorMessages(outcome)).toEqual(['Loan amount must not be negative.']);
    expect(calculateMortgage).toHaveBeenCalledTimes(0);
  });

  it('test_calculator_partial_invalid_returns_no_results', () => {
    const outcome = runCalculator(raw('100000', 'abc', '30'));
    expect(outcome.kind).toBe('invalid');
    expect(errorMessages(outcome)).toEqual(['Annual interest rate must be a number.']);
    expect(outcome).not.toHaveProperty('view.lines');
    expect(calculateMortgage).toHaveBeenCalledTimes(0);
  });

  it('test_calculator_all_missing', () => {
    const outcome = runCalculator(raw(undefined, undefined, undefined));
    expect(outcome.kind).toBe('invalid');
    expect(errorMessages(outcome)).toEqual([
      'Loan amount is required.',
      'Annual interest rate is required.',
      'Term is required.',
    ]);
    expect(calculateMortgage).toHaveBeenCalledTimes(0);
  });

  it('test_calculator_early_termination_equal_final_hidden', () => {
    const outcome = runCalculator(raw('1 075,15', '20', '30'));
    expect(outcome.kind).toBe('result');
    expect(resultLines(outcome)).toEqual([
      'Regular Monthly Payment: 17,97 €',
      'Total Paid: 6 379,35 €',
      'Total Interest: 5 304,20 €',
    ]);
  });
});

/**
 * M4 — domain/calculation (03-test-scenarios.md tests 41–61, 102–108).
 */
import { Decimal } from 'decimal.js';
import { describe, expect, it } from 'vitest';
import { calculateMortgage, roundToCents } from '../../src/domain/calculation.js';
import type { MortgageResult } from '../../src/domain/types.js';

function calc(principal: string, ratePercent: string, termYears: number): MortgageResult {
  return calculateMortgage({
    principal: new Decimal(principal),
    annualRatePercent: new Decimal(ratePercent),
    termYears,
  });
}

interface Expected {
  readonly payments?: number;
  readonly regular: string;
  readonly final: string;
  readonly totalPaid: string;
  readonly interest: string;
}

function expectAmount(actual: Decimal, expected: string, label: string): void {
  expect(actual.equals(new Decimal(expected)), `${label}: got ${actual.toFixed()}, expected ${expected}`).toBe(true);
}

function expectResult(result: MortgageResult, expected: Expected): void {
  if (expected.payments !== undefined) expect(result.numberOfPayments).toBe(expected.payments);
  expectAmount(result.regularPayment, expected.regular, 'regular');
  expectAmount(result.finalPayment, expected.final, 'final');
  expectAmount(result.totalPaid, expected.totalPaid, 'totalPaid');
  expectAmount(result.totalInterest, expected.interest, 'totalInterest');
}

function expectRounded(cases: ReadonlyArray<readonly [string, string]>): void {
  for (const [input, expected] of cases) expectAmount(roundToCents(new Decimal(input)), expected, input);
}

/** Inputs of tests 43–59 (all run the full term). */
const FULL_TERM_INPUTS: ReadonlyArray<readonly [string, string, number]> = [
  ['100000', '3.5', 30],
  ['200000', '4.5', 25],
  ['250000', '6', 20],
  ['50000.55', '2.25', 7],
  ['10000', '3.25', 5],
  ['10000', '2.5', 1],
  ['10000', '5', 1],
  ['1000', '0.01', 1],
  ['1000000', '20', 30],
  ['1000', '20', 30],
  ['150000', '2', 20],
  ['100000', '1.5', 10],
  ['120000', '0', 10],
  ['1000', '0', 1],
  ['1000', '0', 30],
  ['1000000', '0', 30],
  ['1000.14', '0', 1],
];

/** Invariants of 02 M4 that must hold for every valid input. */
function expectInvariants(principal: Decimal, ratePercent: Decimal, termYears: number): void {
  const label = `P=${principal.toFixed()} rate=${ratePercent.toFixed()} term=${termYears}`;
  const result = calculateMortgage({ principal, annualRatePercent: ratePercent, termYears });
  const n = termYears * 12;
  const { numberOfPayments: k, regularPayment, finalPayment, totalPaid, totalInterest } = result;

  expect(finalPayment.greaterThan(0), `${label}: final > 0`).toBe(true);
  expect(totalPaid.equals(regularPayment.times(k - 1).plus(finalPayment)), `${label}: totalPaid = sum`).toBe(true);
  expect(totalInterest.equals(totalPaid.minus(principal)), `${label}: interest = paid − P`).toBe(true);
  expect(totalInterest.greaterThanOrEqualTo(0), `${label}: interest ≥ 0`).toBe(true);
  expect(k <= n && k >= 1, `${label}: 1 ≤ payments ≤ n`).toBe(true);
  if (k < n) expect(finalPayment.lessThanOrEqualTo(regularPayment), `${label}: early ⇒ final ≤ regular`).toBe(true);
  if (ratePercent.isZero()) expect(k, `${label}: 0 % runs the full term`).toBe(n);
}

/** mulberry32: a small seeded PRNG, so the sweep is reproducible without extra dependencies. */
function seededRandom(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function randomInt(random: () => number, min: number, max: number): number {
  return min + Math.floor(random() * (max - min + 1));
}

describe('calculation (M4)', () => {
  it('test_round_to_cents_exact_half_rounds_up', () => {
    expectRounded([
      ['2.345', '2.35'],
      ['1.005', '1.01'],
      ['2.675', '2.68'],
      ['0.125', '0.13'],
      ['0.005', '0.01'],
    ]);
  });

  it('test_round_to_cents_below_half_rounds_down', () => {
    expectRounded([
      ['2.344999', '2.34'],
      ['0.004999', '0.00'],
      ['897.914997950', '897.91'],
    ]);
  });

  it('test_annuity_standard_rate_30y', () => {
    expectResult(calc('100000', '3.5', 30), {
      payments: 360,
      regular: '449.04',
      final: '452.02',
      totalPaid: '161657.38',
      interest: '61657.38',
    });
  });

  it('test_annuity_standard_rate_25y', () => {
    expectResult(calc('200000', '4.5', 25), {
      regular: '1111.66',
      final: '1114.40',
      totalPaid: '333500.74',
      interest: '133500.74',
    });
  });

  it('test_annuity_payment_rounded_up_final_lower', () => {
    expectResult(calc('250000', '6', 20), {
      regular: '1791.08',
      final: '1789.99',
      totalPaid: '429858.11',
      interest: '179858.11',
    });
  });

  it('test_annuity_non_round_loan_amount', () => {
    expectResult(calc('50000.55', '2.25', 7), {
      regular: '643.91',
      final: '643.62',
      totalPaid: '54088.15',
      interest: '4087.60',
    });
  });

  it('test_annuity_final_equals_regular', () => {
    expectResult(calc('10000', '3.25', 5), {
      regular: '180.80',
      final: '180.80',
      totalPaid: '10848.00',
      interest: '848.00',
    });
  });

  it('test_annuity_final_differs_by_one_cent', () => {
    expectResult(calc('10000', '2.5', 1), {
      regular: '844.66',
      final: '844.67',
      totalPaid: '10135.93',
      interest: '135.93',
    });
  });

  it('test_annuity_one_year_term', () => {
    expectResult(calc('10000', '5', 1), {
      payments: 12,
      regular: '856.07',
      final: '856.13',
      totalPaid: '10272.90',
      interest: '272.90',
    });
  });

  it('test_annuity_min_loan_min_positive_rate', () => {
    expectResult(calc('1000', '0.01', 1), {
      regular: '83.34',
      final: '83.31',
      totalPaid: '1000.05',
      interest: '0.05',
    });
  });

  it('test_annuity_max_loan_max_rate_30y', () => {
    expectResult(calc('1000000', '20', 30), {
      regular: '16710.19',
      final: '16638.10',
      totalPaid: '6015596.31',
      interest: '5015596.31',
    });
  });

  it('test_annuity_min_loan_max_rate_30y', () => {
    expectResult(calc('1000', '20', 30), {
      regular: '16.71',
      final: '21.00',
      totalPaid: '6019.89',
      interest: '5019.89',
    });
  });

  it('test_annuity_just_above_half_cent', () => {
    expectResult(calc('150000', '2', 20), {
      regular: '758.83',
      final: '757.36',
      totalPaid: '182117.73',
      interest: '32117.73',
    });
  });

  it('test_annuity_just_below_half_cent', () => {
    expectResult(calc('100000', '1.5', 10), {
      regular: '897.91',
      final: '898.56',
      totalPaid: '107749.85',
      interest: '7749.85',
    });
  });

  it('test_zero_rate_exact_division', () => {
    expectResult(calc('120000', '0', 10), {
      regular: '1000.00',
      final: '1000.00',
      totalPaid: '120000.00',
      interest: '0.00',
    });
  });

  it('test_zero_rate_rounding_absorbed_by_final', () => {
    expectResult(calc('1000', '0', 1), {
      regular: '83.33',
      final: '83.37',
      totalPaid: '1000.00',
      interest: '0.00',
    });
  });

  it('test_zero_rate_30y_final_lower', () => {
    expectResult(calc('1000', '0', 30), {
      regular: '2.78',
      final: '1.98',
      totalPaid: '1000.00',
      interest: '0.00',
    });
  });

  it('test_zero_rate_max_loan_30y', () => {
    expectResult(calc('1000000', '0', 30), {
      regular: '2777.78',
      final: '2776.98',
      totalPaid: '1000000.00',
      interest: '0.00',
    });
  });

  it('test_zero_rate_exact_half_cent_rounds_up', () => {
    expectResult(calc('1000.14', '0', 1), {
      regular: '83.35',
      final: '83.29',
      totalPaid: '1000.14',
      interest: '0.00',
    });
  });

  it('test_calculation_invariants_hold', () => {
    for (const [principal, rate, years] of FULL_TERM_INPUTS) {
      expect(calc(principal, rate, years).numberOfPayments, `${principal}/${rate}/${years}`).toBe(years * 12);
      expectInvariants(new Decimal(principal), new Decimal(rate), years);
      if (rate === '0') expectAmount(calc(principal, rate, years).totalInterest, '0', 'interest at 0 %');
    }
  });

  it('test_calculation_leaves_global_decimal_config_unchanged', () => {
    const saved = { precision: Decimal.precision, rounding: Decimal.rounding };
    try {
      Decimal.set({ precision: 5, rounding: Decimal.ROUND_DOWN });
      const result = calc('100000', '3.5', 30);
      expectAmount(result.regularPayment, '449.04', 'regular');
      expectAmount(result.finalPayment, '452.02', 'final');
      expect(Decimal.precision).toBe(5);
      expect(Decimal.rounding).toBe(Decimal.ROUND_DOWN);
    } finally {
      Decimal.set(saved);
    }
  });

  it('test_early_termination_rounded_up_payment', () => {
    expectResult(calc('1000.29', '20', 30), {
      payments: 354,
      regular: '16.72',
      final: '8.08',
      totalPaid: '5910.24',
      interest: '4909.95',
    });
  });

  it('test_early_termination_largest_overpayment', () => {
    expectResult(calc('1011.06', '20', 30), {
      payments: 354,
      regular: '16.90',
      final: '8.63',
      totalPaid: '5974.33',
      interest: '4963.27',
    });
  });

  it('test_early_termination_round_loan_amount', () => {
    expectResult(calc('1000', '10', 30), {
      payments: 359,
      regular: '8.78',
      final: '7.88',
      totalPaid: '3151.12',
      interest: '2151.12',
    });
  });

  it('test_early_termination_one_month_early_low_rate', () => {
    expectResult(calc('1001.01', '8', 30), {
      payments: 359,
      regular: '7.35',
      final: '7.33',
      totalPaid: '2638.63',
      interest: '1637.62',
    });
  });

  it('test_early_termination_remainder_rounds_to_zero', () => {
    expectResult(calc('1075.15', '20', 30), {
      payments: 355,
      regular: '17.97',
      final: '17.97',
      totalPaid: '6379.35',
      interest: '5304.20',
    });
  });

  it('test_full_term_final_far_below_regular', () => {
    expectResult(calc('1003.93', '20', 20), {
      payments: 240,
      regular: '17.06',
      final: '1.54',
      totalPaid: '4078.88',
      interest: '3074.95',
    });
  });

  it('test_calculation_invariants_property_sweep', { timeout: 120_000 }, () => {
    let checked = 0;
    for (let cents = 100000; cents <= 100599; cents++) {
      for (const rate of ['8', '10', '15', '20']) {
        for (const years of [25, 30]) {
          expectInvariants(new Decimal(cents).div(100), new Decimal(rate), years);
          checked++;
        }
      }
    }
    const random = seededRandom(7);
    for (let i = 0; i < 2000; i++) {
      const principal = new Decimal(randomInt(random, 100000, 100000000)).div(100);
      const rate = new Decimal(randomInt(random, 0, 2000)).div(100);
      expectInvariants(principal, rate, randomInt(random, 1, 30));
      checked++;
    }
    expect(checked).toBe(6800);
  });
});

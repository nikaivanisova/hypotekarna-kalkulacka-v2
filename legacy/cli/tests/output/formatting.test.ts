/**
 * M5 — output/formatting (03-test-scenarios.md tests 62–68).
 */
import { Decimal } from 'decimal.js';
import { describe, expect, it } from 'vitest';
import { formatMoney } from '../../src/output/formatting.js';

function format(amount: string): string {
  return formatMoney(new Decimal(amount));
}

describe('formatting (M5)', () => {
  it('test_format_money_thousands_separator', () => {
    expect(format('1234.57')).toBe('1 234,57 €');
  });

  it('test_format_money_below_thousand', () => {
    expect(format('449.04')).toBe('449,04 €');
  });

  it('test_format_money_millions', () => {
    expect(format('6015596.31')).toBe('6 015 596,31 €');
  });

  it('test_format_money_pads_two_decimals', () => {
    expect(format('1000000')).toBe('1 000 000,00 €');
    expect(format('0.5')).toBe('0,50 €');
  });

  it('test_format_money_zero', () => {
    expect(format('0')).toBe('0,00 €');
  });

  it('test_format_money_rounds_half_up', () => {
    expect(format('1234.565')).toBe('1 234,57 €');
    expect(format('1234.564999')).toBe('1 234,56 €');

    // The rounding mode must be explicit, not decimal.js's global default (04 #16).
    const saved = { rounding: Decimal.rounding };
    try {
      Decimal.set({ rounding: Decimal.ROUND_DOWN });
      expect(format('1234.565')).toBe('1 234,57 €');
    } finally {
      Decimal.set(saved);
    }
  });

  it('test_format_money_uses_ascii_spaces_only', () => {
    const text = format('1234567.89');
    expect(text).toBe('1 234 567,89 €');
    expect(text).not.toMatch(/[  ]/);
  });
});

/**
 * M5 — formatting (docs/v1/03-test-scenarios.md tests 62–68), ported from legacy/cli.
 *
 * V2 change: the API sends canonical 2-dp strings (contract `Money`) and the frontend must not
 * round or do arithmetic (CLAUDE.md). So tests 66–67, which fed V1 unrounded Decimals, now
 * check that the formatter never rounds: anything that is not a canonical amount is rejected.
 */
import { describe, expect, it } from 'vitest';
import { formatMoney } from '../../src/formatting.js';

describe('formatting (M5)', () => {
  it('test_format_money_thousands_separator', () => {
    expect(formatMoney('1234.57')).toBe('1 234,57 €');
  });

  it('test_format_money_below_thousand', () => {
    expect(formatMoney('449.04')).toBe('449,04 €');
  });

  it('test_format_money_millions', () => {
    expect(formatMoney('6015596.31')).toBe('6 015 596,31 €');
  });

  it('test_format_money_pads_two_decimals', () => {
    // V2: the backend pads (contract Money); the formatter keeps both decimals as sent.
    expect(formatMoney('1000000.00')).toBe('1 000 000,00 €');
    expect(formatMoney('0.50')).toBe('0,50 €');
  });

  it('test_format_money_zero', () => {
    expect(formatMoney('0.00')).toBe('0,00 €');
  });

  it('test_format_money_rounds_half_up', () => {
    // V2: rounding is the backend's job; an unrounded or non-canonical amount is a contract violation.
    for (const amount of ['1234.565', '1234.5', '1234', '01.00', '-1.00', '1e3', ' 1.00', '1,00']) {
      expect(() => formatMoney(amount), amount).toThrow(TypeError);
    }
  });

  it('test_format_money_uses_ascii_spaces_only', () => {
    const text = formatMoney('1234567.89');
    expect(text).toBe('1 234 567,89 €');
    expect(text).not.toMatch(/[  ]/);
  });

  // --- New in V2 ---

  it('test_format_money_rejects_numbers', () => {
    expect(() => formatMoney(449.04)).toThrow(TypeError);
    expect(() => formatMoney(undefined)).toThrow(TypeError);
  });

  it('test_format_money_groups_every_length', () => {
    const cases = { '1.00': '1,00 €', '12.00': '12,00 €', '123.00': '123,00 €', '1234.00': '1 234,00 €',
      '12345.00': '12 345,00 €', '123456.00': '123 456,00 €', '1234567.00': '1 234 567,00 €' };
    for (const [amount, text] of Object.entries(cases)) expect(formatMoney(amount)).toBe(text);
  });
});

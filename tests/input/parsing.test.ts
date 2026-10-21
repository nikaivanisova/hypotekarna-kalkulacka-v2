/**
 * M2 — input/parsing (03-test-scenarios.md tests 1–16, 96–100).
 */
import { Decimal } from 'decimal.js';
import { describe, expect, it } from 'vitest';
import { parseNumber } from '../../src/input/parsing.js';

function expectNumber(raw: string, value: string, writtenDecimals?: number): void {
  const result = parseNumber(raw);
  if (!result.ok) throw new Error(`"${raw}" was rejected with "${result.error}"`);
  expect(result.value.equals(new Decimal(value)), `value of "${raw}" is ${result.value.toString()}`).toBe(true);
  if (writtenDecimals !== undefined) expect(result.writtenDecimals).toBe(writtenDecimals);
}

function expectError(raw: string | undefined, error: 'empty' | 'not_a_number'): void {
  expect(parseNumber(raw), `parseNumber(${JSON.stringify(raw)})`).toEqual({ ok: false, error });
}

describe('parsing (M2)', () => {
  it('test_parse_dot_decimal_separator', () => {
    expectNumber('1000.50', '1000.5', 2);
  });

  it('test_parse_comma_decimal_separator', () => {
    expectNumber('1000,50', '1000.5', 2);
  });

  it('test_parse_spaces_as_thousands_separator', () => {
    expectNumber('1 000 000,50', '1000000.5', 2);
  });

  it('test_parse_integer_without_separator', () => {
    expectNumber('30', '30', 0);
  });

  it('test_parse_trims_leading_trailing_whitespace', () => {
    expectNumber('  250000  ', '250000', 0);
  });

  it('test_parse_counts_written_trailing_zeros', () => {
    expectNumber('1000,500', '1000.5', 3);
  });

  it('test_parse_negative_number_is_parsed', () => {
    expectNumber('-5000', '-5000');
  });

  it('test_parse_empty_string', () => {
    expectError('', 'empty');
  });

  it('test_parse_whitespace_only', () => {
    expectError('   ', 'empty');
  });

  it('test_parse_undefined_input', () => {
    expectError(undefined, 'empty');
  });

  it('test_parse_text_string', () => {
    expectError('abc', 'not_a_number');
  });

  it('test_parse_mixed_separators_rejected', () => {
    expectError('1,000.50', 'not_a_number');
  });

  it('test_parse_multiple_dots_rejected', () => {
    expectError('1.000.50', 'not_a_number');
  });

  it('test_parse_multiple_commas_rejected', () => {
    expectError('1,000,50', 'not_a_number');
  });

  it('test_parse_currency_symbol_rejected', () => {
    expectError('1000 €', 'not_a_number');
  });

  it('test_parse_scientific_notation_rejected', () => {
    expectError('1e5', 'not_a_number');
  });

  it('test_parse_hex_binary_octal_rejected', () => {
    for (const raw of ['0x3E8', '0b1010', '0o17']) expectError(raw, 'not_a_number');
  });

  it('test_parse_nan_and_infinity_rejected', () => {
    for (const raw of ['NaN', 'Infinity', '-Infinity']) expectError(raw, 'not_a_number');
  });

  it('test_parse_exponent_variants_rejected', () => {
    for (const raw of ['1E5', '1e-2', '2,5e3']) expectError(raw, 'not_a_number');
  });

  it('test_parse_separator_without_digits_rejected', () => {
    for (const raw of ['1000,', ',50', '.5']) expectError(raw, 'not_a_number');
  });

  it('test_parse_sign_other_than_leading_minus_rejected', () => {
    for (const raw of ['+30', '−5000', '5000-']) expectError(raw, 'not_a_number');
  });
});

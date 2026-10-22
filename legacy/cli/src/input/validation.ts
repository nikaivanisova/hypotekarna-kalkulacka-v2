/**
 * M3 — Input validation (02-architecture.md §3, M3; 01-functional.md §3.1, §3.3).
 *
 * Decides whether a set of raw inputs forms a valid loan request.
 */
import { Decimal } from 'decimal.js';
import type {
  Field,
  RawLoanInput,
  ValidationError,
  ValidationErrorCode,
  ValidationResult,
} from '../domain/types.js';
import { parseNumber } from './parsing.js';

export interface FieldRule {
  readonly min: Decimal; // inclusive
  readonly max: Decimal; // inclusive
  readonly maxDecimals: number; // 2 for money/rate, 0 for term
  readonly wholeNumber: boolean;
}

/** Input limits from 01 §3.1. */
export const V1_RULES: Readonly<Record<Field, FieldRule>> = {
  loanAmount: { min: new Decimal('1000'), max: new Decimal('1000000'), maxDecimals: 2, wholeNumber: false },
  annualRate: { min: new Decimal('0'), max: new Decimal('20'), maxDecimals: 2, wholeNumber: false },
  termYears: { min: new Decimal('1'), max: new Decimal('30'), maxDecimals: 0, wholeNumber: true },
};

/** Fields in the order their errors are reported. */
const FIELD_ORDER: readonly Field[] = ['loanAmount', 'annualRate', 'termYears'];

type FieldCheck = { readonly ok: true; readonly value: Decimal } | { readonly ok: false; readonly code: ValidationErrorCode };

/**
 * Checks one field and returns at most one error, in this order:
 * required → not_a_number → negative → not_whole_number → too_many_decimals → below_min / above_max.
 */
function checkField(raw: string | undefined, rule: FieldRule): FieldCheck {
  const parsed = parseNumber(raw);
  if (!parsed.ok) return { ok: false, code: parsed.error === 'empty' ? 'required' : 'not_a_number' };

  const { value, writtenDecimals } = parsed;
  if (value.isNegative()) return { ok: false, code: 'negative' };
  if (rule.wholeNumber && !value.isInteger()) return { ok: false, code: 'not_whole_number' };
  if (writtenDecimals > rule.maxDecimals) return { ok: false, code: 'too_many_decimals' };
  if (value.lessThan(rule.min)) return { ok: false, code: 'below_min' };
  if (value.greaterThan(rule.max)) return { ok: false, code: 'above_max' };
  return { ok: true, value };
}

export function validateLoanInput(
  raw: RawLoanInput,
  rules: Readonly<Record<Field, FieldRule>> = V1_RULES,
): ValidationResult {
  const values = new Map<Field, Decimal>();
  const errors: ValidationError[] = [];

  for (const field of FIELD_ORDER) {
    const check = checkField(raw[field], rules[field]);
    if (check.ok) values.set(field, check.value);
    else errors.push({ field, code: check.code });
  }

  const principal = values.get('loanAmount');
  const annualRatePercent = values.get('annualRate');
  const termYears = values.get('termYears');
  if (errors.length > 0 || !principal || !annualRatePercent || !termYears) return { ok: false, errors };

  return { ok: true, value: { principal, annualRatePercent, termYears: termYears.toNumber() } };
}

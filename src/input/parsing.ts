/**
 * M2 — Number parsing (02-architecture.md §3, M2; 01-functional.md §3.2).
 *
 * Converts one raw text value into an exact decimal number.
 */
import { Decimal } from 'decimal.js';

export type ParseResult =
  | {
      readonly ok: true;
      readonly value: Decimal;
      /** Decimal places as written by the user, e.g. "1000,500" → 3. */
      readonly writtenDecimals: number;
    }
  | { readonly ok: false; readonly error: 'empty' | 'not_a_number' };

/** Strict number grammar from 01 §3.2, applied after trimming and removing inner spaces. */
export const NUMBER_PATTERN: RegExp = /^-?[0-9]+(?:[.,]([0-9]+))?$/;

export function parseNumber(raw: string | undefined): ParseResult {
  const trimmed = raw?.trim() ?? '';
  if (trimmed === '') return { ok: false, error: 'empty' };

  const compact = trimmed.replaceAll(' ', '');

  // Gatekeeper: decimal.js also accepts hex/binary/octal, exponents, NaN and Infinity,
  // so it must only ever see text that matches the V1 grammar.
  const match = NUMBER_PATTERN.exec(compact);
  if (match === null) return { ok: false, error: 'not_a_number' };

  return {
    ok: true,
    value: new Decimal(compact.replace(',', '.')),
    writtenDecimals: match[1]?.length ?? 0,
  };
}

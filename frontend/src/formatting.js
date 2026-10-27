/**
 * M5 — Money formatting (docs/v1/01-functional.md §3.4; ADR-4), ported from legacy/cli.
 *
 * Renders an API Money string as Slovak/EU-style euro text, e.g. "1234.57" → "1 234,57 €".
 * Pure string work: the backend has already rounded to cents, and the frontend never does
 * arithmetic on money (api/openapi.yaml). ASCII spaces only, no Intl (ADR-4).
 */

/** Contract `Money`: non-negative, no leading zeros, exactly two decimals. */
const MONEY_PATTERN = /^(0|[1-9][0-9]*)\.([0-9]{2})$/;

const THOUSANDS_SEPARATOR = ' ';
const DECIMAL_SEPARATOR = ',';
const CURRENCY_SUFFIX = ' €';

export function isMoney(value) {
  return typeof value === 'string' && MONEY_PATTERN.test(value);
}

export function formatMoney(amount) {
  const match = typeof amount === 'string' ? MONEY_PATTERN.exec(amount) : null;
  if (match === null) throw new TypeError(`Not a canonical Money amount: ${String(amount)}`);
  const [, integerPart, fractionPart] = match;
  const grouped = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, THOUSANDS_SEPARATOR);
  return `${grouped}${DECIMAL_SEPARATOR}${fractionPart}${CURRENCY_SUFFIX}`;
}

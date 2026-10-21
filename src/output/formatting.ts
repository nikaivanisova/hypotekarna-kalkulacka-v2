/**
 * M5 — Money formatting (02-architecture.md §3, M5; 01-functional.md §3.4; ADR-4).
 *
 * Renders a monetary amount as Slovak/EU-style euro text, e.g. 1234.567 → "1 234,57 €".
 * Uses ordinary ASCII spaces only, and no Intl (ADR-4).
 */
import { Decimal } from 'decimal.js';

const THOUSANDS_SEPARATOR = ' ';
const DECIMAL_SEPARATOR = ',';
const CURRENCY_SUFFIX = ' €';

export function formatMoney(amount: Decimal): string {
  // Explicit rounding mode: never depend on decimal.js's global settings (04 #16).
  const fixed = amount.toFixed(2, Decimal.ROUND_HALF_UP);
  const negative = fixed.startsWith('-') && /[1-9]/.test(fixed);
  const [integerPart = '0', fractionPart = '00'] = fixed.replace('-', '').split('.');
  const grouped = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, THOUSANDS_SEPARATOR);
  return `${negative ? '-' : ''}${grouped}${DECIMAL_SEPARATOR}${fractionPart}${CURRENCY_SUFFIX}`;
}

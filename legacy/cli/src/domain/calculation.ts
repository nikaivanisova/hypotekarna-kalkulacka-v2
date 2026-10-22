/**
 * M4 — Mortgage calculation (02-architecture.md §3, M4; 01-functional.md §4).
 *
 * Computes the payment figures of a fixed-rate annuity mortgage from a valid loan request.
 * Pure: no I/O, no state, no clock. Depends only on domain/types and decimal.js.
 */
import { Decimal } from 'decimal.js';
import type { LoanInput, MortgageResult } from './types.js';

/** Private Decimal context (ADR-3): never reads or changes the global decimal.js settings. */
const Dec = Decimal.clone({ precision: 40, rounding: Decimal.ROUND_HALF_UP });

const MONTHS_PER_YEAR = 12;

/** Round half up to 2 decimal places (01 §4.3). */
export function roundToCents(amount: Decimal): Decimal {
  return new Dec(amount).toDecimalPlaces(2, Dec.ROUND_HALF_UP);
}

export function calculateMortgage(input: LoanInput): MortgageResult {
  // 01 §4.1: derived values, full precision.
  const principal = new Dec(input.principal);
  const n = input.termYears * MONTHS_PER_YEAR;
  const r = new Dec(input.annualRatePercent).div(MONTHS_PER_YEAR).div(100);
  const growth = r.plus(1);

  // 01 §4.2: annuity payment, rounded to cents only once.
  const regularPayment = roundToCents(annuityPayment(principal, r, n));

  // 01 §4.4 step 2: month-by-month run with early termination, no intermediate rounding.
  let balance = principal;
  let month = 1;
  let amountDue = balance.times(growth);
  while (month < n && amountDue.greaterThan(regularPayment)) {
    balance = amountDue.minus(regularPayment);
    month++;
    amountDue = balance.times(growth);
  }

  // 01 §4.4 step 3: a remainder that rounds to €0.00 makes the previous payment the final one.
  let numberOfPayments = month;
  let finalPayment = roundToCents(amountDue);
  if (finalPayment.isZero()) {
    numberOfPayments = month - 1;
    finalPayment = regularPayment;
  }

  // 01 §4.5: totals.
  const totalPaid = regularPayment.times(numberOfPayments - 1).plus(finalPayment);
  const totalInterest = totalPaid.minus(principal);

  return {
    numberOfPayments,
    regularPayment,
    finalPayment,
    totalPaid: roundToCents(totalPaid),
    totalInterest: roundToCents(totalInterest),
  };
}

/** M = P·r·(1+r)ⁿ / ((1+r)ⁿ − 1), or P ÷ n at 0 %. */
function annuityPayment(principal: Decimal, r: Decimal, n: number): Decimal {
  if (r.isZero()) return principal.div(n);
  const growthN = r.plus(1).pow(n);
  return principal.times(r).times(growthN).div(growthN.minus(1));
}

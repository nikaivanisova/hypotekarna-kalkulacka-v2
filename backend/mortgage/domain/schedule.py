"""Month-by-month run of the loan, with one-time extra payments (ADR-9; docs/v2/04-extra-payments.md §3).

Pure: no I/O. Must be called inside the calculation's private decimal context (domain/calculation).
The rules and their exact-rational reference are in tools/reference.py (`calc_extra`).
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from mortgage.domain.types import AppliedExtraPayment, ExtraPayment, ExtraPaymentStatus

type Ending = Literal['schedule', 'extra', 'zero_tail']

ZERO = Decimal('0.00')
CENT = Decimal('0.01')


@dataclass(frozen=True)
class Run:
    number_of_payments: int  # K
    final_payment: Decimal  # cents
    ending: Ending
    total_paid: Decimal  # unrounded only in form; exact cents by construction (§3.4)


def extras_by_month(extras: tuple[ExtraPayment, ...]) -> dict[int, Decimal]:
    """X_k: the extras of each month added up (X7)."""
    totals: dict[int, Decimal] = {}
    for extra in extras:
        totals[extra.month] = totals.get(extra.month, ZERO) + extra.amount
    return totals


def run(principal: Decimal, r: Decimal, n: int, regular: Decimal, extra: dict[int, Decimal],
        round_to_cents) -> Run:
    """§3.2: amount due D = B·(1+r) each month; the loan ends on schedule (k = n or D ≤ M), by an
    extra (D ≤ M + X_k), or one month earlier through the V1 zero tail (round(D) = 0.00)."""
    growth = r + 1
    balance = principal
    month = 1
    while True:
        due = balance * growth
        paid_now = regular + extra.get(month, ZERO)
        if month == n or due <= regular:
            ending: Ending = 'schedule'
            break
        if due <= paid_now:
            ending = 'extra'
            break
        balance = due - paid_now
        month += 1

    payments = month
    final = round_to_cents(due)
    if final.is_zero():  # zero tail (V1 01 §4.4 step 3): month k is not a payment month
        payments, ending = month - 1, 'zero_tail'
        final = regular + extra.get(payments, ZERO)

    total = regular * (payments - 1) + sum((x for m, x in extra.items() if m < payments), ZERO) + final
    return Run(payments, final, ending, total)


def apply_extras(extras: tuple[ExtraPayment, ...], result: Run, regular: Decimal) -> tuple[AppliedExtraPayment, ...]:
    """§3.3: what each month uses, split over its items in request order, and each item's status."""
    last = result.number_of_payments
    left: dict[int, Decimal] = {}
    for month, total in extras_by_month(extras).items():
        if month < last or (month == last and result.ending == 'zero_tail'):
            left[month] = total
        elif month == last and result.ending == 'extra':
            left[month] = min(total, result.final_payment - regular)
        else:
            left[month] = ZERO

    applied = []
    for extra in extras:
        used = min(extra.amount, left[extra.month])
        left[extra.month] -= used
        status = _status(extra, used, result, regular)
        # quantize() is exact here: every value is already whole cents; it only fixes the exponent ("5000" → "5000.00").
        applied.append(AppliedExtraPayment(extra.month, extra.amount.quantize(CENT), used.quantize(CENT), status))
    return tuple(applied)


def _status(extra: ExtraPayment, used: Decimal, result: Run, regular: Decimal) -> ExtraPaymentStatus:
    if used == extra.amount:
        return 'used'
    if used > 0:
        return 'partly_used'
    if extra.month > result.number_of_payments:
        return 'after_payoff'
    if result.ending == 'schedule':
        return 'loan_ends_this_month'
    if result.final_payment == regular:  # extra ending with less than half a cent owed after M
        return 'tiny_balance'
    return 'covered_by_earlier'

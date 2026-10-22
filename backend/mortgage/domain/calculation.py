"""M4 — Mortgage calculation (docs/v1/02-architecture.md §3, M4; 01-functional.md §4), ported from legacy/cli.

Computes the payment figures of a fixed-rate annuity mortgage from a valid loan request.
Pure: no I/O, no state, no clock. Depends only on domain.types and decimal.
"""
from decimal import ROUND_HALF_UP, Context, Decimal, localcontext

from mortgage.domain.types import LoanInput, MortgageResult

# Private decimal context (ADR-3): 40 significant digits, round half up.
# Python applies the *thread* context to arithmetic, so it is entered with localcontext(),
# which restores the caller's context afterwards; the global context is never changed.
CONTEXT = Context(prec=40, rounding=ROUND_HALF_UP)

CENT = Decimal('0.01')
MONTHS_PER_YEAR = 12


def round_to_cents(amount: Decimal) -> Decimal:
    """Round half up to 2 decimal places (01 §4.3)."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP, context=CONTEXT)


def calculate_mortgage(loan: LoanInput) -> MortgageResult:
    with localcontext(CONTEXT):
        # 01 §4.1: derived values, full precision.
        principal = loan.principal
        n = loan.term_years * MONTHS_PER_YEAR
        r = loan.annual_rate_percent / MONTHS_PER_YEAR / 100
        growth = r + 1

        # 01 §4.2: annuity payment, rounded to cents only once.
        regular_payment = round_to_cents(annuity_payment(principal, r, n))

        # 01 §4.4 step 2: month-by-month run with early termination, no intermediate rounding.
        balance = principal
        month = 1
        amount_due = balance * growth
        while month < n and amount_due > regular_payment:
            balance = amount_due - regular_payment
            month += 1
            amount_due = balance * growth

        # 01 §4.4 step 3: a remainder that rounds to €0.00 makes the previous payment the final one.
        number_of_payments = month
        final_payment = round_to_cents(amount_due)
        if final_payment.is_zero():
            number_of_payments = month - 1
            final_payment = regular_payment

        # 01 §4.5: totals.
        total_paid = regular_payment * (number_of_payments - 1) + final_payment
        total_interest = total_paid - principal

        return MortgageResult(
            number_of_payments=number_of_payments,
            regular_payment=regular_payment,
            final_payment=final_payment,
            total_paid=round_to_cents(total_paid),
            total_interest=round_to_cents(total_interest),
        )


def annuity_payment(principal: Decimal, r: Decimal, n: int) -> Decimal:
    """M = P·r·(1+r)ⁿ / ((1+r)ⁿ − 1), or P ÷ n at 0 %. Call inside the private context."""
    if r.is_zero():
        return principal / n
    growth_n = (r + 1) ** n
    return principal * r * growth_n / (growth_n - 1)

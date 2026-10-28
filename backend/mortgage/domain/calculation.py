"""M4 — Mortgage calculation (docs/v1/02-architecture.md §3, M4; 01-functional.md §4), ported from V1 (legacy/cli; removed in Phase 8, see git tag v1-final).

Computes the payment figures of a fixed-rate annuity mortgage from a valid loan request, including
one-time extra payments (Phase 7; docs/v2/04-extra-payments.md). The month-by-month run lives in
domain/schedule (ADR-9); without extra payments the results are exactly V1's.
Pure: no I/O, no state, no clock. Depends only on domain/types, domain/schedule and decimal.
"""
from decimal import ROUND_HALF_UP, Context, Decimal, localcontext

from mortgage.domain.schedule import apply_extras, extras_by_month, run
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

        # 01 §4.2: annuity payment, rounded to cents only once. Extra payments never change it (D7).
        regular_payment = round_to_cents(annuity_payment(principal, r, n))

        # 01 §4.4 / 04 §3.2: month-by-month run, no intermediate rounding.
        base = run(principal, r, n, regular_payment, {}, round_to_cents)
        result = (run(principal, r, n, regular_payment, extras_by_month(loan.extra_payments), round_to_cents)
                  if loan.extra_payments else base)

        # 01 §4.5 / 04 §3.4: totals and savings (sums of cent amounts; rounded only to fix the exponent).
        total_interest = result.total_paid - principal
        base_interest = base.total_paid - principal

        return MortgageResult(
            number_of_payments=result.number_of_payments,
            regular_payment=regular_payment,
            final_payment=result.final_payment,
            total_paid=round_to_cents(result.total_paid),
            total_interest=round_to_cents(total_interest),
            months_saved=base.number_of_payments - result.number_of_payments,
            interest_saved=round_to_cents(base_interest - total_interest),
            extra_payments=apply_extras(loan.extra_payments, result, regular_payment),
        )


def annuity_payment(principal: Decimal, r: Decimal, n: int) -> Decimal:
    """M = P·r·(1+r)ⁿ / ((1+r)ⁿ − 1), or P ÷ n at 0 %. Call inside the private context."""
    if r.is_zero():
        return principal / n
    growth_n = (r + 1) ** n
    return principal * r * growth_n / (growth_n - 1)

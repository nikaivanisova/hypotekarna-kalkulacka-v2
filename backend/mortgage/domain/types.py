"""M1 — Domain types (docs/v1/02-architecture.md §3, M1), ported from legacy/cli.

The shared vocabulary for FR-1, FR-2 and FR-3. Types only: no logic.
Field names and error codes are the API's (camelCase), so they pass through unchanged.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, TypedDict

type Field = Literal['loanAmount', 'annualRate', 'termYears']


class RawLoanInput(TypedDict):
    """Exactly what the user typed; None means the field was not provided."""
    loanAmount: str | None
    annualRate: str | None
    termYears: str | None


@dataclass(frozen=True)
class ExtraPayment:
    """A one-time extra payment (FR-5; docs/v2/04-extra-payments.md §2), validated."""
    month: int  # 1 – term_years × 12; paid together with that month's regular payment
    amount: Decimal  # EUR, 0.01 – 1 000 000.00


@dataclass(frozen=True)
class LoanInput:
    """A loan request that has passed validation (input.validation is the only producer)."""
    principal: Decimal  # EUR, 1 000.00 – 1 000 000.00
    annual_rate_percent: Decimal  # 0.00 – 20.00
    term_years: int  # 1 – 30
    extra_payments: tuple[ExtraPayment, ...] = ()  # in request order


# Per-item outcome (docs/v2/04-extra-payments.md §3.3). An open vocabulary in the API.
type ExtraPaymentStatus = Literal[
    'used',
    'partly_used',
    'after_payoff',
    'loan_ends_this_month',
    'tiny_balance',
    'covered_by_earlier',
]


@dataclass(frozen=True)
class AppliedExtraPayment:
    month: int
    amount: Decimal
    used_amount: Decimal  # 0.00 – amount, in cents
    status: ExtraPaymentStatus


@dataclass(frozen=True)
class MortgageResult:
    """All amounts are already rounded to cents (round half up)."""
    number_of_payments: int  # payments actually made: term_years × 12, or fewer if the loan ends early (01 §4.4)
    regular_payment: Decimal  # M_rounded; never changed by extra payments (D7)
    final_payment: Decimal
    total_paid: Decimal
    total_interest: Decimal
    # Phase 7 (all zero / empty without extra payments):
    months_saved: int = 0
    interest_saved: Decimal = Decimal('0.00')
    extra_payments: tuple[AppliedExtraPayment, ...] = ()  # one per input item, same order


type ValidationErrorCode = Literal[
    'required',
    'not_a_number',
    'negative',
    'below_min',
    'above_max',
    'too_many_decimals',
    'not_whole_number',
]


@dataclass(frozen=True)
class ValidationError:
    field: Field
    code: ValidationErrorCode


@dataclass(frozen=True)
class Valid:
    value: LoanInput


@dataclass(frozen=True)
class Invalid:
    errors: tuple[ValidationError, ...]


type ValidationResult = Valid | Invalid

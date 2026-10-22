"""M3 — Input validation (docs/v1/02-architecture.md §3, M3; 01-functional.md §3.1, §3.3), ported from legacy/cli.

Decides whether a set of raw inputs forms a valid loan request.
"""
from dataclasses import dataclass
from decimal import Decimal

from mortgage.domain.types import (
    Field,
    Invalid,
    LoanInput,
    RawLoanInput,
    Valid,
    ValidationError,
    ValidationErrorCode,
    ValidationResult,
)
from mortgage.input.parsing import ParseFailure, parse_number


@dataclass(frozen=True)
class FieldRule:
    min: Decimal  # inclusive
    max: Decimal  # inclusive
    max_decimals: int  # 2 for money/rate, 0 for term
    whole_number: bool


# Input limits from 01 §3.1.
V1_RULES: dict[Field, FieldRule] = {
    'loanAmount': FieldRule(Decimal('1000'), Decimal('1000000'), 2, False),
    'annualRate': FieldRule(Decimal('0'), Decimal('20'), 2, False),
    'termYears': FieldRule(Decimal('1'), Decimal('30'), 0, True),
}

# Fields in the order their errors are reported.
FIELD_ORDER: tuple[Field, ...] = ('loanAmount', 'annualRate', 'termYears')


def check_field(raw: str | None, rule: FieldRule) -> Decimal | ValidationErrorCode:
    """Checks one field and returns its value or at most one error code, in this order:
    required → not_a_number → negative → not_whole_number → too_many_decimals → below_min / above_max.
    """
    parsed = parse_number(raw)
    if isinstance(parsed, ParseFailure):
        return 'required' if parsed.error == 'empty' else 'not_a_number'

    value = parsed.value
    # is_signed(), not `< 0`: "-0" must be reported as negative, as in V1 (finding #9).
    if value.is_signed():
        return 'negative'
    if rule.whole_number and value != value.to_integral_value():
        return 'not_whole_number'
    if parsed.written_decimals > rule.max_decimals:
        return 'too_many_decimals'
    if value < rule.min:
        return 'below_min'
    if value > rule.max:
        return 'above_max'
    return value


def validate_loan_input(raw: RawLoanInput, rules: dict[Field, FieldRule] = V1_RULES) -> ValidationResult:
    values: dict[Field, Decimal] = {}
    errors: list[ValidationError] = []

    for field in FIELD_ORDER:
        check = check_field(raw.get(field), rules[field])
        if isinstance(check, Decimal):
            values[field] = check
        else:
            errors.append(ValidationError(field, check))

    if errors:
        return Invalid(tuple(errors))
    return Valid(LoanInput(values['loanAmount'], values['annualRate'], int(values['termYears'])))

"""M3 — input/validation (docs/v1/03-test-scenarios.md tests 17–40, 101), ported from legacy/cli."""
from decimal import Decimal

import pytest

from mortgage.domain.types import Invalid, LoanInput, RawLoanInput, Valid, ValidationError
from mortgage.input.validation import validate_loan_input

# Valid values for the fields a scenario does not mention.
VALID: RawLoanInput = {'loanAmount': '100000', 'annualRate': '3', 'termYears': '10'}


def expect_valid(**overrides: str | None) -> LoanInput:
    result = validate_loan_input({**VALID, **overrides})
    assert isinstance(result, Valid), f'expected valid input, got {result}'
    return result.value


def expect_errors(errors: list[tuple[str, str]], **overrides: str | None) -> None:
    expected = Invalid(tuple(ValidationError(field, code) for field, code in errors))
    assert validate_loan_input({**VALID, **overrides}) == expected


def expect_decimal(actual: Decimal, expected: str) -> None:
    assert actual == Decimal(expected), f'{actual} = {expected}'


def test_validate_all_valid_inputs():
    value = expect_valid(loanAmount='100 000', annualRate='3,5', termYears='30')
    expect_decimal(value.principal, '100000')
    expect_decimal(value.annual_rate_percent, '3.5')
    assert value.term_years == 30
    assert type(value.term_years) is int


def test_validate_loan_min_inclusive():
    expect_decimal(expect_valid(loanAmount='1000', annualRate='3', termYears='10').principal, '1000')


def test_validate_loan_max_inclusive():
    expect_decimal(expect_valid(loanAmount='1 000 000,00', annualRate='3', termYears='10').principal, '1000000')


def test_validate_loan_below_min():
    expect_errors([('loanAmount', 'below_min')], loanAmount='999,99')


def test_validate_loan_above_max():
    expect_errors([('loanAmount', 'above_max')], loanAmount='1000000,01')


def test_validate_loan_negative():
    expect_errors([('loanAmount', 'negative')], loanAmount='-100000')


def test_validate_loan_too_many_decimals():
    expect_errors([('loanAmount', 'too_many_decimals')], loanAmount='100000,555')


def test_validate_loan_written_trailing_zero_decimals():
    expect_errors([('loanAmount', 'too_many_decimals')], loanAmount='100000,500')


def test_validate_rate_zero_inclusive():
    expect_decimal(expect_valid(loanAmount='100000', annualRate='0', termYears='10').annual_rate_percent, '0')


def test_validate_rate_max_inclusive():
    expect_decimal(expect_valid(loanAmount='100000', annualRate='20,00', termYears='10').annual_rate_percent, '20')


def test_validate_rate_above_max():
    expect_errors([('annualRate', 'above_max')], annualRate='20,01')


def test_validate_rate_negative():
    expect_errors([('annualRate', 'negative')], annualRate='-0,5')


def test_validate_rate_too_many_decimals():
    expect_errors([('annualRate', 'too_many_decimals')], annualRate='3,555')


def test_validate_term_min_inclusive():
    assert expect_valid(loanAmount='100000', annualRate='3', termYears='1').term_years == 1


def test_validate_term_max_inclusive():
    assert expect_valid(loanAmount='100000', annualRate='3', termYears='30').term_years == 30


def test_validate_term_zero():
    expect_errors([('termYears', 'below_min')], termYears='0')


def test_validate_term_above_max():
    expect_errors([('termYears', 'above_max')], termYears='31')


def test_validate_term_fractional():
    expect_errors([('termYears', 'not_whole_number')], termYears='2,5')


def test_validate_term_with_zero_decimal():
    expect_errors([('termYears', 'too_many_decimals')], termYears='10,0')


def test_validate_term_text():
    expect_errors([('termYears', 'not_a_number')], termYears='thirty')


def test_validate_missing_field():
    expect_errors([('termYears', 'required')], loanAmount='100000', annualRate='3', termYears=None)


def test_validate_all_fields_empty():
    expect_errors(
        [('loanAmount', 'required'), ('annualRate', 'required'), ('termYears', 'required')],
        loanAmount='', annualRate='', termYears='',
    )


def test_validate_multiple_invalid_fields():
    expect_errors(
        [('loanAmount', 'not_a_number'), ('annualRate', 'above_max'), ('termYears', 'below_min')],
        loanAmount='abc', annualRate='25', termYears='0',
    )


def test_validate_one_error_per_field():
    expect_errors([('loanAmount', 'negative')], loanAmount='-1000,555')


def test_validate_hex_loan_amount_rejected():
    expect_errors([('loanAmount', 'not_a_number')], loanAmount='0x3E8', annualRate='3', termYears='10')


# --- New in V2: Python-specific parity guard (not in V1 03) -----------------------------------


@pytest.mark.parametrize(('field', 'raw'), [('annualRate', '-0'), ('loanAmount', '-0,00')])
def test_validate_negative_zero_is_negative(field, raw):
    """V1 behaviour kept (01-functional V2 §3, finding #9): Decimal('-0') < 0 is False in Python, so sign must be checked."""
    expect_errors([(field, 'negative')], **{field: raw})


def test_validate_term_fractional_near_max():
    """A second guard for the whole-number check: without it, "29,9" would be reported as too_many_decimals."""
    expect_errors([('termYears', 'not_whole_number')], termYears='29,9')

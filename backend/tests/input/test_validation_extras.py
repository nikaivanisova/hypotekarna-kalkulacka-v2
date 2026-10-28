"""Phase 7 — validation of extra payments (docs/v2/04-extra-payments.md §2)."""
from decimal import Decimal

import pytest

from mortgage.domain.types import ExtraPayment, Invalid, Valid, ValidationError
from mortgage.input.validation import validate_loan_input

BASE = {'loanAmount': '100000', 'annualRate': '3', 'termYears': '30'}


def validate(extras, **base):
    return validate_loan_input({**BASE, **base, 'extraPayments': extras})


def item_error(index, prop, code):
    return ValidationError('extraPayments', code, index, prop)


def errors_of(result):
    assert isinstance(result, Invalid), result
    return list(result.errors)


def test_valid_items_become_extra_payments_in_order():
    result = validate([{'month': '24', 'amount': '5 000'}, {'month': ' 12 ', 'amount': '1000,50'}])
    assert isinstance(result, Valid)
    assert result.value.extra_payments == (ExtraPayment(24, Decimal('5000')), ExtraPayment(12, Decimal('1000.50')))
    assert type(result.value.extra_payments[0].month) is int


@pytest.mark.parametrize('raw', [{**BASE}, {**BASE, 'extraPayments': []}, {**BASE, 'extraPayments': None}])
def test_absent_null_or_empty_list_means_no_extra_payments(raw):
    result = validate_loan_input(raw)
    assert isinstance(result, Valid) and result.value.extra_payments == ()


@pytest.mark.parametrize(('month', 'code'), [
    ('', 'required'), (None, 'required'), ('   ', 'required'), ('abc', 'not_a_number'), ('-1', 'negative'),
    ('-0', 'negative'), ('2,5', 'not_whole_number'), ('24,0', 'too_many_decimals'), ('12,00', 'too_many_decimals'),
    ('0', 'below_min'),
    ('361', 'above_max'), ('1e2', 'not_a_number'),
])
def test_month_errors(month, code):
    assert errors_of(validate([{'month': month, 'amount': '100'}])) == [item_error(0, 'month', code)]


@pytest.mark.parametrize(('amount', 'code'), [
    ('', 'required'), (None, 'required'), ('abc', 'not_a_number'), ('-5', 'negative'), ('-0', 'negative'),
    ('0', 'below_min'), ('0,00', 'below_min'), ('0,001', 'too_many_decimals'), ('1,234', 'too_many_decimals'),
    ('1000000,01', 'above_max'), ('1 000 001', 'above_max'), ('0x10', 'not_a_number'),
])
def test_amount_errors(amount, code):
    assert errors_of(validate([{'month': '12', 'amount': amount}])) == [item_error(0, 'amount', code)]


@pytest.mark.parametrize(('month', 'amount'), [('1', '0,01'), ('360', '1 000 000,00'), ('1', '1000000')])
def test_bounds_are_inclusive(month, amount):
    assert isinstance(validate([{'month': month, 'amount': amount}]), Valid)


def test_month_maximum_follows_a_valid_term():
    assert isinstance(validate([{'month': '120', 'amount': '1'}], termYears='10'), Valid)
    assert errors_of(validate([{'month': '121', 'amount': '1'}], termYears='10')) == [item_error(0, 'month', 'above_max')]


def test_month_is_checked_against_360_when_the_term_is_invalid():
    """§2: the term's own error is reported, and the month is still checked against the largest term."""
    assert errors_of(validate([{'month': '300', 'amount': '1'}], termYears='31')) == [
        ValidationError('termYears', 'above_max')]
    assert errors_of(validate([{'month': '361', 'amount': '1'}], termYears='abc')) == [
        ValidationError('termYears', 'not_a_number'), item_error(0, 'month', 'above_max')]


def test_an_empty_item_gives_two_required_errors():
    assert errors_of(validate([{}])) == [item_error(0, 'month', 'required'), item_error(0, 'amount', 'required')]


def test_error_order_is_v1_fields_then_items_then_month_before_amount():
    result = validate([{'month': '1', 'amount': '1'}, {'month': 'x', 'amount': 'y'}, {'month': '0', 'amount': '1'}],
                      loanAmount='abc')
    assert errors_of(result) == [
        ValidationError('loanAmount', 'not_a_number'),
        item_error(1, 'month', 'not_a_number'),
        item_error(1, 'amount', 'not_a_number'),
        item_error(2, 'month', 'below_min'),
    ]


def test_invalid_items_mean_no_calculation_input():
    result = validate([{'month': '12', 'amount': '100'}, {'month': '12', 'amount': '0'}])
    assert isinstance(result, Invalid)


def test_v1_errors_keep_their_shape():
    """index and property stay None for the V1 fields (unchanged API shape for them)."""
    [error] = errors_of(validate_loan_input({**BASE, 'loanAmount': ''}))
    assert (error.index, error.property) == (None, None)


# --- Sweep of the month limit (contract review 7c finding 3; CLAUDE.md: rules over a numeric domain get a sweep) ---


@pytest.mark.parametrize('term', range(1, 31))
def test_month_limit_follows_every_valid_term(term):
    last = term * 12
    assert isinstance(validate([{'month': str(last), 'amount': '1'}], termYears=str(term)), Valid)
    assert isinstance(validate([{'month': '1', 'amount': '1'}], termYears=str(term)), Valid)
    assert errors_of(validate([{'month': str(last + 1), 'amount': '1'}], termYears=str(term))) == [
        item_error(0, 'month', 'above_max')]


@pytest.mark.parametrize('term', ['0', '31', 'abc', '', None, '2,5', '-1'])
def test_month_limit_is_360_while_the_term_is_invalid(term):
    within = [e for e in errors_of(validate([{'month': '360', 'amount': '1'}], termYears=term)) if e.field == 'extraPayments']
    beyond = [e for e in errors_of(validate([{'month': '361', 'amount': '1'}], termYears=term)) if e.field == 'extraPayments']
    assert within == []
    assert beyond == [item_error(0, 'month', 'above_max')]

"""Phase 7 — extra payments in the domain (docs/v2/04-extra-payments.md §3, examples §6).

Values are the spec's E1–E12, computed with exact rationals in tools/reference.py (EXPECTED_EXTRA).
Without extra payments the results must stay exactly V1 (tests in test_calculation.py, unchanged).
"""
import decimal
from decimal import Decimal

import pytest

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import ExtraPayment, LoanInput

# (id, loan, extras, payments, final, total, interest, used per item, status per item, months saved, interest saved)
EXAMPLES = [
    ('E1', ('100000', '3.5', 30), [(24, '5000')], 332, '246.84', '153879.08', '53879.08',
     ['5000.00'], ['used'], 28, '7778.30'),
    ('E2', ('100000', '3.5', 30), [(60, '200000')], 60, '90146.42', '116639.78', '16639.78',
     ['89697.38'], ['partly_used'], 300, '45017.60'),
    ('E3', ('100000', '3.5', 30), [(60, '50000'), (60, '50000'), (120, '1000')], 60, '90146.42', '116639.78', '16639.78',
     ['50000.00', '39697.38', '0.00'], ['used', 'partly_used', 'after_payoff'], 300, '45017.60'),
    ('E4', ('10000', '5', 1), [(12, '500')], 12, '856.13', '10272.90', '272.90',
     ['0.00'], ['loan_ends_this_month'], 0, '0.00'),
    ('E5', ('200000', '4.5', 25), [(12, '10000'), (36, '10000'), (60, '10000')], 236, '670.04', '291910.14', '91910.14',
     ['10000.00', '10000.00', '10000.00'], ['used', 'used', 'used'], 64, '41590.60'),
    ('E6', ('120000', '0', 10), [(1, '1000')], 119, '1000.00', '120000.00', '0.00',
     ['1000.00'], ['used'], 1, '0.00'),
    ('E7', ('100000', '3.5', 30), [(100, '81757.90')], 100, '82206.94', '126661.90', '26661.90',
     ['81757.90'], ['used'], 260, '34995.48'),
    ('E8', ('1000.29', '20', 30), [(354, '100')], 354, '8.08', '5910.24', '4909.95',
     ['0.00'], ['loan_ends_this_month'], 0, '0.00'),
    ('E9', ('1000.02', '20', 30), [(264, '783.50'), (265, '1000')], 265, '16.71', '5211.65', '4211.63',
     ['783.50', '0.00'], ['used', 'tiny_balance'], 95, '815.92'),
    ('E10', ('100000', '3.5', 30), [(60, '95000'), (60, '5000')], 60, '90146.42', '116639.78', '16639.78',
     ['89697.38', '0.00'], ['partly_used', 'covered_by_earlier'], 300, '45017.60'),
    ('E11', ('250000', '6', 20), [(120, '200000')], 120, '163119.24', '376257.76', '126257.76',
     ['161328.16'], ['partly_used'], 120, '53600.35'),
    ('E12', ('100000', '3.5', 30), [(1, '200000')], 1, '100291.67', '100291.67', '291.67',
     ['99842.63'], ['partly_used'], 359, '61365.71'),
]


def loan(principal: str, rate: str, years: int, extras) -> LoanInput:
    return LoanInput(Decimal(principal), Decimal(rate), years,
                     tuple(ExtraPayment(month, Decimal(amount)) for month, amount in extras))


@pytest.mark.parametrize('example', EXAMPLES, ids=[e[0] for e in EXAMPLES])
def test_schedule_spec_examples(example):
    _, args, extras, payments, final, total, interest, used, statuses, months_saved, interest_saved = example
    r = calculate_mortgage(loan(*args, extras))
    assert r.number_of_payments == payments
    assert (str(r.final_payment), str(r.total_paid), str(r.total_interest)) == (final, total, interest)
    assert [str(e.used_amount) for e in r.extra_payments] == used
    assert [e.status for e in r.extra_payments] == statuses
    assert (r.months_saved, str(r.interest_saved)) == (months_saved, interest_saved)


@pytest.mark.parametrize('example', EXAMPLES, ids=[e[0] for e in EXAMPLES])
def test_schedule_keeps_the_regular_payment(example):
    """D7: an extra payment never changes the regular monthly payment."""
    _, args, extras, *_ = example
    assert calculate_mortgage(loan(*args, extras)).regular_payment == calculate_mortgage(loan(*args, [])).regular_payment


@pytest.mark.parametrize('example', EXAMPLES, ids=[e[0] for e in EXAMPLES])
def test_schedule_echoes_each_item_in_request_order(example):
    _, args, extras, *_ = example
    items = calculate_mortgage(loan(*args, extras)).extra_payments
    assert [(e.month, e.amount) for e in items] == [(m, Decimal(a)) for m, a in extras]


def test_schedule_without_extras_reports_no_savings():
    r = calculate_mortgage(loan('100000', '3.5', 30, []))
    assert (r.months_saved, str(r.interest_saved), r.extra_payments) == (0, '0.00', ())
    assert (r.number_of_payments, str(r.total_paid)) == (360, '161657.38')


@pytest.mark.parametrize('extras', [[(360, '100')], [(360, '100'), (360, '0.01')]])
def test_schedule_extra_in_month_n_is_not_needed(extras):
    """X10, review 05 note: a schedule-ending month must be asserted directly, not only via the sweep."""
    r = calculate_mortgage(loan('1000', '20', 30, extras))
    assert [e.status for e in r.extra_payments] == ['loan_ends_this_month'] * len(extras)
    assert [str(e.used_amount) for e in r.extra_payments] == ['0.00'] * len(extras)
    assert (str(r.final_payment), str(r.total_paid), r.months_saved) == ('21.00', '6019.89', 0)


def test_schedule_extra_counted_only_once_when_split_over_items():
    """X7: two items in one month act as one payment of their sum."""
    split = calculate_mortgage(loan('100000', '3.5', 30, [(24, '2000'), (24, '3000')]))
    whole = calculate_mortgage(loan('100000', '3.5', 30, [(24, '5000')]))
    assert (split.number_of_payments, split.total_paid, split.final_payment) == (
        whole.number_of_payments, whole.total_paid, whole.final_payment)


def test_schedule_outputs_are_exact_cents():
    r = calculate_mortgage(loan('123456.78', '4.25', 25, [(13, '1234.56'), (200, '99999.99')]))
    amounts = [r.regular_payment, r.final_payment, r.total_paid, r.total_interest, r.interest_saved]
    amounts += [e.used_amount for e in r.extra_payments]
    assert all(a == a.quantize(Decimal('0.01')) and a.as_tuple().exponent == -2 for a in amounts)


def test_schedule_ignores_a_low_precision_global_context():
    with decimal.localcontext() as ctx:
        ctx.prec = 4
        ctx.rounding = decimal.ROUND_DOWN
        r = calculate_mortgage(loan('100000', '3.5', 30, [(24, '5000')]))
    assert (r.number_of_payments, str(r.interest_saved)) == (332, '7778.30')

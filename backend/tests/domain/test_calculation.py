"""M4 — domain/calculation (docs/v1/03-test-scenarios.md tests 41–61, 102–108), ported from V1 (legacy/cli; removed in Phase 8, see git tag v1-final).

Amounts are compared as strings ("449.04"), which is stricter than V1's numeric equality:
it also proves every output already has exactly two decimal places, as the API will send it.
"""
import decimal
from decimal import Decimal

import pytest

from mortgage.domain.calculation import calculate_mortgage, round_to_cents
from mortgage.domain.types import LoanInput, MortgageResult
from tests.sweep import sweep_inputs


def calc(principal: str, rate_percent: str, term_years: int) -> MortgageResult:
    return calculate_mortgage(LoanInput(Decimal(principal), Decimal(rate_percent), term_years))


def expect_result(result: MortgageResult, regular: str, final: str, total_paid: str, interest: str,
                  payments: int | None = None) -> None:
    if payments is not None:
        assert result.number_of_payments == payments
    assert str(result.regular_payment) == regular
    assert str(result.final_payment) == final
    assert str(result.total_paid) == total_paid
    assert str(result.total_interest) == interest


def expect_rounded(cases: list[tuple[str, str]]) -> None:
    for value, expected in cases:
        assert str(round_to_cents(Decimal(value))) == expected, value


# Inputs of tests 43–59 (all run the full term).
FULL_TERM_INPUTS = [
    ('100000', '3.5', 30),
    ('200000', '4.5', 25),
    ('250000', '6', 20),
    ('50000.55', '2.25', 7),
    ('10000', '3.25', 5),
    ('10000', '2.5', 1),
    ('10000', '5', 1),
    ('1000', '0.01', 1),
    ('1000000', '20', 30),
    ('1000', '20', 30),
    ('150000', '2', 20),
    ('100000', '1.5', 10),
    ('120000', '0', 10),
    ('1000', '0', 1),
    ('1000', '0', 30),
    ('1000000', '0', 30),
    ('1000.14', '0', 1),
]


def expect_invariants(principal: Decimal, rate_percent: Decimal, term_years: int) -> None:
    """Invariants of 02 M4 that must hold for every valid input."""
    label = f'P={principal} rate={rate_percent} term={term_years}'
    r = calculate_mortgage(LoanInput(principal, rate_percent, term_years))
    n = term_years * 12
    k = r.number_of_payments

    assert r.final_payment > 0, f'{label}: final > 0'
    assert r.total_paid == r.regular_payment * (k - 1) + r.final_payment, f'{label}: totalPaid = sum'
    assert r.total_interest == r.total_paid - principal, f'{label}: interest = paid − P'
    assert r.total_interest >= 0, f'{label}: interest ≥ 0'
    assert 1 <= k <= n, f'{label}: 1 ≤ payments ≤ n'
    if k < n:
        assert r.final_payment <= r.regular_payment, f'{label}: early ⇒ final ≤ regular'
    if rate_percent.is_zero():
        assert k == n, f'{label}: 0 % runs the full term'


def test_round_to_cents_exact_half_rounds_up():
    expect_rounded([('2.345', '2.35'), ('1.005', '1.01'), ('2.675', '2.68'), ('0.125', '0.13'), ('0.005', '0.01')])


def test_round_to_cents_below_half_rounds_down():
    expect_rounded([('2.344999', '2.34'), ('0.004999', '0.00'), ('897.914997950', '897.91')])


def test_annuity_standard_rate_30y():
    expect_result(calc('100000', '3.5', 30), '449.04', '452.02', '161657.38', '61657.38', payments=360)


def test_annuity_standard_rate_25y():
    expect_result(calc('200000', '4.5', 25), '1111.66', '1114.40', '333500.74', '133500.74')


def test_annuity_payment_rounded_up_final_lower():
    expect_result(calc('250000', '6', 20), '1791.08', '1789.99', '429858.11', '179858.11')


def test_annuity_non_round_loan_amount():
    expect_result(calc('50000.55', '2.25', 7), '643.91', '643.62', '54088.15', '4087.60')


def test_annuity_final_equals_regular():
    expect_result(calc('10000', '3.25', 5), '180.80', '180.80', '10848.00', '848.00')


def test_annuity_final_differs_by_one_cent():
    expect_result(calc('10000', '2.5', 1), '844.66', '844.67', '10135.93', '135.93')


def test_annuity_one_year_term():
    expect_result(calc('10000', '5', 1), '856.07', '856.13', '10272.90', '272.90', payments=12)


def test_annuity_min_loan_min_positive_rate():
    expect_result(calc('1000', '0.01', 1), '83.34', '83.31', '1000.05', '0.05')


def test_annuity_max_loan_max_rate_30y():
    expect_result(calc('1000000', '20', 30), '16710.19', '16638.10', '6015596.31', '5015596.31')


def test_annuity_min_loan_max_rate_30y():
    expect_result(calc('1000', '20', 30), '16.71', '21.00', '6019.89', '5019.89')


def test_annuity_just_above_half_cent():
    expect_result(calc('150000', '2', 20), '758.83', '757.36', '182117.73', '32117.73')


def test_annuity_just_below_half_cent():
    expect_result(calc('100000', '1.5', 10), '897.91', '898.56', '107749.85', '7749.85')


def test_zero_rate_exact_division():
    expect_result(calc('120000', '0', 10), '1000.00', '1000.00', '120000.00', '0.00')


def test_zero_rate_rounding_absorbed_by_final():
    expect_result(calc('1000', '0', 1), '83.33', '83.37', '1000.00', '0.00')


def test_zero_rate_30y_final_lower():
    expect_result(calc('1000', '0', 30), '2.78', '1.98', '1000.00', '0.00')


def test_zero_rate_max_loan_30y():
    expect_result(calc('1000000', '0', 30), '2777.78', '2776.98', '1000000.00', '0.00')


def test_zero_rate_exact_half_cent_rounds_up():
    expect_result(calc('1000.14', '0', 1), '83.35', '83.29', '1000.14', '0.00')


@pytest.mark.parametrize(('principal', 'rate', 'years'), FULL_TERM_INPUTS)
def test_calculation_invariants_hold(principal, rate, years):
    assert calc(principal, rate, years).number_of_payments == years * 12
    expect_invariants(Decimal(principal), Decimal(rate), years)
    if rate == '0':
        assert str(calc(principal, rate, years).total_interest) == '0.00'


def test_calculation_leaves_global_decimal_config_unchanged():
    with decimal.localcontext() as ctx:
        ctx.prec = 5
        ctx.rounding = decimal.ROUND_DOWN
        result = calc('100000', '3.5', 30)
        assert str(result.regular_payment) == '449.04'
        assert str(result.final_payment) == '452.02'
        assert decimal.getcontext().prec == 5
        assert decimal.getcontext().rounding == decimal.ROUND_DOWN


def test_early_termination_rounded_up_payment():
    expect_result(calc('1000.29', '20', 30), '16.72', '8.08', '5910.24', '4909.95', payments=354)


def test_early_termination_largest_overpayment():
    expect_result(calc('1011.06', '20', 30), '16.90', '8.63', '5974.33', '4963.27', payments=354)


def test_early_termination_round_loan_amount():
    expect_result(calc('1000', '10', 30), '8.78', '7.88', '3151.12', '2151.12', payments=359)


def test_early_termination_one_month_early_low_rate():
    expect_result(calc('1001.01', '8', 30), '7.35', '7.33', '2638.63', '1637.62', payments=359)


def test_early_termination_remainder_rounds_to_zero():
    expect_result(calc('1075.15', '20', 30), '17.97', '17.97', '6379.35', '5304.20', payments=355)


def test_full_term_final_far_below_regular():
    expect_result(calc('1003.93', '20', 20), '17.06', '1.54', '4078.88', '3074.95', payments=240)


# --- New in V2: second guards, so no rule depends on a single test (docs/v1/06-retro.md §6.1 rule 3) ---


def test_early_termination_remainder_rounds_to_zero_25y():
    """A second zero-tail loan (V1 had only test 106). Values from tools/reference.py (exact rationals)."""
    expect_result(calc('1176.40', '20', 25), '19.75', '19.75', '5885.50', '4709.10', payments=298)


def test_calculation_ignores_a_low_precision_global_context():
    with decimal.localcontext() as ctx:
        ctx.prec = 3
        ctx.rounding = decimal.ROUND_UP
        expect_result(calc('1000.29', '20', 30), '16.72', '8.08', '5910.24', '4909.95', payments=354)


def test_calculation_invariants_property_sweep():
    inputs = sweep_inputs()
    for principal, rate, years in inputs:
        expect_invariants(principal, rate, years)
    assert len(inputs) == 6800

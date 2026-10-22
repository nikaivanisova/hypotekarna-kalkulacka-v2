"""M7 — app/calculator (docs/v1/03-test-scenarios.md tests 80–84, 109), ported from legacy/cli.

In V2 the use case returns the domain result or the validation errors; turning them into labels,
messages and "hide an equal Final Payment" is the frontend's job (plan §2). The scenarios and
expected values are V1's; the assertions check the data behind V1's display lines.
"""
import pytest

import mortgage.app.calculator as calculator_module
from mortgage.app.calculator import Calculated, Rejected, run_calculator
from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import RawLoanInput, ValidationError


@pytest.fixture
def calls(monkeypatch) -> list[object]:
    """Wraps the real calculate_mortgage and records each call."""
    recorded: list[object] = []

    def spy(loan):
        recorded.append(loan)
        return calculate_mortgage(loan)

    monkeypatch.setattr(calculator_module, 'calculate_mortgage', spy)
    return recorded


def raw(loan_amount: str | None, annual_rate: str | None, term_years: str | None) -> RawLoanInput:
    return {'loanAmount': loan_amount, 'annualRate': annual_rate, 'termYears': term_years}


def amounts(outcome) -> tuple[str, str, str, str]:
    assert isinstance(outcome, Calculated), f'expected a result, got {outcome}'
    r = outcome.result
    return str(r.regular_payment), str(r.final_payment), str(r.total_paid), str(r.total_interest)


def errors(outcome) -> tuple[ValidationError, ...]:
    assert isinstance(outcome, Rejected), f'expected validation errors, got {outcome}'
    return outcome.errors


def test_calculator_valid_input_returns_result(calls):
    outcome = run_calculator(raw('100 000', '3,5', '30'))
    assert amounts(outcome) == ('449.04', '452.02', '161657.38', '61657.38')
    assert len(calls) == 1


def test_calculator_zero_rate_full_flow(calls):
    assert amounts(run_calculator(raw('1 000', '0', '1'))) == ('83.33', '83.37', '1000.00', '0.00')


def test_calculator_invalid_input_skips_calculation(calls):
    outcome = run_calculator(raw('-100000', '3,5', '30'))
    assert errors(outcome) == (ValidationError('loanAmount', 'negative'),)
    assert len(calls) == 0


def test_calculator_partial_invalid_returns_no_results(calls):
    outcome = run_calculator(raw('100000', 'abc', '30'))
    assert errors(outcome) == (ValidationError('annualRate', 'not_a_number'),)
    assert not hasattr(outcome, 'result')
    assert len(calls) == 0


def test_calculator_all_missing(calls):
    outcome = run_calculator(raw(None, None, None))
    assert errors(outcome) == (
        ValidationError('loanAmount', 'required'),
        ValidationError('annualRate', 'required'),
        ValidationError('termYears', 'required'),
    )
    assert len(calls) == 0


def test_calculator_early_termination_equal_final_hidden(calls):
    # V1 hid the Final Payment line here because it equals the regular payment (frontend rule in V2).
    outcome = run_calculator(raw('1 075,15', '20', '30'))
    assert amounts(outcome) == ('17.97', '17.97', '6379.35', '5304.20')
    assert outcome.result.number_of_payments == 355

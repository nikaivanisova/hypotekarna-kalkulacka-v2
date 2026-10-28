"""Phase 7, build step 3: the backend equals the exact-rational reference on the spec's sweep strata.

tools/reference.py `extra_sweep_cases` builds the edge cases on purpose (exact pay-off at 0 %, zero
tails with several items and after earlier extras, tiny balances, items covered by earlier ones).
Every output is compared cent for cent, statuses included. 800 loans: 100 per stratum.
"""
import importlib.util
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import ExtraPayment, LoanInput

REFERENCE_PATH = Path(__file__).resolve().parents[3] / 'tools' / 'reference.py'
LOANS = 800
# `loan_ends_this_month` is rare in the strata (15 in 3 200 loans), so these cases make sure the
# comparison covers it: extras in month n and in V1's own early-termination month (X10).
SCHEDULE_ENDING_CASES = [
    (Fraction('1000'), Fraction('20'), 30, [(360, Fraction('100'))]),
    (Fraction('1000.29'), Fraction('20'), 30, [(354, Fraction('100')), (354, Fraction('0.01'))]),
    (Fraction('10000'), Fraction('5'), 1, [(12, Fraction('500')), (3, Fraction('100'))]),
]


def load_reference():
    spec = importlib.util.spec_from_file_location('reference', REFERENCE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def to_decimal(value: Fraction) -> Decimal:
    """Exact for the reference's inputs, which are whole cents."""
    assert (value * 100).denominator == 1, value
    return Decimal(int(value * 100)) / 100


def test_backend_matches_the_exact_reference_on_every_stratum():
    reference = load_reference()
    mismatches, statuses, endings_seen = [], set(), set()
    cases = list(reference.extra_sweep_cases(LOANS))
    cases += [(-1, 'schedule ending', P, rate, years, extras, None) for P, rate, years, extras in SCHEDULE_ENDING_CASES]
    for i, stratum, P, rate, years, extras, _built in cases:
        loan = LoanInput(to_decimal(P), to_decimal(rate), years,
                         tuple(ExtraPayment(month, to_decimal(amount)) for month, amount in extras))
        got = calculate_mortgage(loan)
        want = reference.calc_extra(P, rate, years, extras)
        endings_seen.add(want['ending'])
        statuses.update(want['statuses'])
        same = (
            got.number_of_payments == want['payments']
            and Fraction(got.regular_payment) == want['regular']
            and Fraction(got.final_payment) == want['final']
            and Fraction(got.total_paid) == want['total']
            and Fraction(got.total_interest) == want['interest']
            and got.months_saved == want['months_saved']
            and Fraction(got.interest_saved) == want['interest_saved']
            and [Fraction(e.used_amount) for e in got.extra_payments] == want['used']
            and [e.status for e in got.extra_payments] == want['statuses']
        )
        if not same:
            mismatches.append((i, stratum, str(P), str(rate), years))
    assert mismatches == []
    # The sample must actually reach every path, or the comparison proves little.
    assert endings_seen == {'schedule', 'extra', 'zero_tail'}
    assert statuses == set(reference.STATUSES)

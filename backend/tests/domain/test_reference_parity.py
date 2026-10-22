"""New in V2: the backend agrees with the exact-rational reference (tools/reference.py) on every sweep loan.

V1 only checked invariants over the sweep; this checks every output value, cent for cent.
"""
import importlib.util
from fractions import Fraction
from pathlib import Path

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import LoanInput
from tests.sweep import sweep_inputs

REFERENCE_PATH = Path(__file__).resolve().parents[3] / 'tools' / 'reference.py'


def load_reference():
    spec = importlib.util.spec_from_file_location('reference', REFERENCE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_calculation_matches_exact_reference_on_sweep():
    reference = load_reference()
    mismatches = []
    for principal, rate, years in sweep_inputs():
        got = calculate_mortgage(LoanInput(principal, rate, years))
        want = reference.calc(Fraction(principal), Fraction(rate), years)
        if (got.number_of_payments, Fraction(got.regular_payment), Fraction(got.final_payment),
                Fraction(got.total_paid), Fraction(got.total_interest)) != (
                want['payments'], want['regular'], want['final'], want['total'], want['interest']):
            mismatches.append((str(principal), str(rate), years))
    assert mismatches == []

"""M7 — app/calculator (docs/v1/02-architecture.md §3, M7; 01-functional.md FR-3), ported from legacy/cli.

Orchestrates one calculation request: raw inputs → validation → calculation.
Pure and synchronous; no I/O. Presentation (labels, messages) belongs to the frontend in V2.
"""
from dataclasses import dataclass

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import Invalid, MortgageResult, RawLoanInput, ValidationError
from mortgage.input.validation import validate_loan_input


@dataclass(frozen=True)
class Calculated:
    result: MortgageResult


@dataclass(frozen=True)
class Rejected:
    errors: tuple[ValidationError, ...]


type CalculatorOutcome = Calculated | Rejected


def run_calculator(raw: RawLoanInput) -> CalculatorOutcome:
    """Nothing is calculated until all inputs are valid (FR-3)."""
    validation = validate_loan_input(raw)
    if isinstance(validation, Invalid):
        return Rejected(validation.errors)
    return Calculated(calculate_mortgage(validation.value))

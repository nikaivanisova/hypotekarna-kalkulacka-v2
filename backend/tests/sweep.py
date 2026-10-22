"""Shared input domain of the property sweep (test 108) and the reference parity test."""
import random
from decimal import Decimal


def sweep_inputs() -> list[tuple[Decimal, Decimal, int]]:
    """The corner grid plus 2 000 seeded random loans (6 800 in total).

    Seed 7 with Python's `random`, in the same order as tools/reference.py, so both sweep the same loans.
    """
    grid = [(Decimal(cents) / 100, Decimal(rate), years)
            for cents in range(100000, 100600) for rate in ('20', '15', '10', '8') for years in (30, 25)]
    rng = random.Random(7)
    for _ in range(2000):
        cents, rate_bp, years = rng.randint(100000, 100000000), rng.randint(0, 2000), rng.randint(1, 30)
        grid.append((Decimal(cents) / 100, Decimal(rate_bp) / 100, years))
    return grid

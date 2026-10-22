"""Exact-rational reference for the mortgage calculation (REF-ET).

Source: docs/v1/03-test-scenarios.md, Appendix B, checked in as recommended by docs/v1/06-retro.md §6.3.
Implements docs/v1/01-functional.md §4 with fractions.Fraction (no precision limit, round half up).
It is the independent oracle for the backend: the backend may use Decimal, this script must not.

Run:  py -I tools/reference.py     (exit code 0 = every expected value and the sweep agree)
"""
from fractions import Fraction as F
import math
import random
import sys


def rc(x):
    """Round half up to cents, exact."""
    c = x * 100
    s = -1 if c < 0 else 1
    c = abs(c)
    fl = math.floor(c)
    return F(s * (fl + (1 if c - fl >= F(1, 2) else 0)), 100)


def calc(P, rate, years):
    P = F(P)
    r = F(rate) / 1200
    n = years * 12
    M = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    Mr = rc(M)
    B = P
    for k in range(1, n + 1):  # §4.4 step 2
        D = B * (1 + r)  # balance + interest accrued this month
        if k == n or D <= Mr:
            break  # last active month (early termination if k < n)
        B = D - Mr
    final, payments = rc(D), k
    if final == 0:  # §4.4 step 3: remainder rounds to 0.00
        final, payments = Mr, k - 1
    total = Mr * (payments - 1) + final
    return dict(regular=Mr, payments=payments, n=n, final=final, total=total, interest=total - P)


# (test id, inputs, regular, payments, final, total, interest) — Appendix B output.
EXPECTED = [
    (102, ('1000.29', '20', 30), '16.72', 354, '8.08', '5910.24', '4909.95'),
    (103, ('1011.06', '20', 30), '16.90', 354, '8.63', '5974.33', '4963.27'),
    (104, ('1000', '10', 30), '8.78', 359, '7.88', '3151.12', '2151.12'),
    (105, ('1001.01', '8', 30), '7.35', 359, '7.33', '2638.63', '1637.62'),
    (106, ('1075.15', '20', 30), '17.97', 355, '17.97', '6379.35', '5304.20'),
    (107, ('1003.93', '20', 20), '17.06', 240, '1.54', '4078.88', '3074.95'),
    (43, ('100000', '3.5', 30), '449.04', 360, '452.02', '161657.38', '61657.38'),
    (52, ('1000', '20', 30), '16.71', 360, '21.00', '6019.89', '5019.89'),
]


def check_examples():
    failures = 0
    for test_id, args, regular, payments, final, total, interest in EXPECTED:
        x = calc(*args)
        got = (x['regular'], x['payments'], x['final'], x['total'], x['interest'])
        want = (F(regular), payments, F(final), F(total), F(interest))
        ok = got == want
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} test {test_id} {args}")
    return failures


def check_sweep():
    """Test 108 domain: invariants over 6 800 loans, seeded."""
    random.seed(7)
    grid = [(c, rt, y) for c in range(100000, 100600) for rt in (2000, 1500, 1000, 800) for y in (30, 25)]
    grid += [(random.randint(100000, 100000000), random.randint(0, 2000), random.randint(1, 30)) for _ in range(2000)]
    early = bad = 0
    for c, rt, y in grid:
        P = F(c, 100)
        x = calc(P, F(rt, 100), y)
        payments = [x['regular']] * (x['payments'] - 1) + [x['final']]
        is_early = x['payments'] < x['n']
        early += is_early
        ok = (x['final'] > 0 and sum(payments) == x['total'] and x['payments'] <= x['n']
              and x['interest'] == x['total'] - P and x['interest'] >= 0
              and (not is_early or x['final'] <= x['regular']) and (rt != 0 or not is_early))
        bad += not ok
    print(f"sweep {len(grid)} early {early} violations {bad}")
    return int(bad > 0 or (len(grid), early) != (6800, 767))


if __name__ == '__main__':
    sys.exit(1 if check_examples() + check_sweep() else 0)

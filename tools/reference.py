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


# --- Phase 7: one-time extra payments (docs/v2/04-extra-payments.md) ---------------------------

# Per-item outcome (spec §3.3). Each item gets exactly one.
STATUSES = ('used', 'partly_used', 'after_payoff', 'loan_ends_this_month', 'tiny_balance', 'covered_by_earlier')


def calc_extra(P, rate, years, extras):
    """V1 calculation plus one-time extra payments that shorten the term (D7, FR-5).

    extras: list of (month, amount) in request order; amounts are cents, months 1..n.
    Each month the borrower pays M + X_k (X_k = sum of that month's extras), right after that
    month's interest. The loan ends in month k, with a final payment of round(D) that absorbs all
    rounding as in V1, when:
      'schedule': k == n or D <= M (V1's own ending; that month's extras are not needed), or
      'extra':    D <= M + X_k (the extras pay the loan off; only final - M of them is used).
    The V1 zero-tail rule is unchanged: if round(D) is 0.00, month k is not a payment month and the
    previous month's payment (M + X_{k-1}, extras fully used) was the final one ('zero_tail').
    """
    P = F(P)
    r = F(rate) / 1200
    n = years * 12
    M = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    Mr = rc(M)
    X = {}
    for month, amount in extras:
        X[month] = X.get(month, 0) + F(amount)
    B = P
    for k in range(1, n + 1):
        D = B * (1 + r)
        if k == n or D <= Mr:
            ending = 'schedule'
            break
        if D <= Mr + X.get(k, 0):
            ending = 'extra'
            break
        B = D - Mr - X.get(k, 0)
    final, payments = rc(D), k
    if final == 0:  # zero tail: month k is not a payment month
        payments, ending = k - 1, 'zero_tail'
        final = Mr + X.get(payments, 0)
    # Extra actually used per month: all of it before the last payment month (and in a zero-tail
    # last month); in an 'extra' last month only final - M; nothing in a 'schedule' last month or later.
    used_month = {}
    for month, total in X.items():
        if month < payments or (month == payments and ending == 'zero_tail'):
            used_month[month] = total
        elif month == payments and ending == 'extra':
            used_month[month] = min(total, max(F(0), final - Mr))
        else:
            used_month[month] = F(0)
    # Split each month's used amount over its items in request order, and give each item a status.
    left = dict(used_month)
    used, statuses = [], []
    for month, amount in extras:
        amount = F(amount)
        take = min(amount, left[month])
        left[month] -= take
        used.append(take)
        if take == amount:
            status = 'used'
        elif take > 0:
            status = 'partly_used'
        elif month > payments:
            status = 'after_payoff'
        elif ending == 'schedule':
            status = 'loan_ends_this_month'
        elif final == Mr:  # 'extra' ending with less than half a cent owed after the regular payment
            status = 'tiny_balance'
        else:
            status = 'covered_by_earlier'
        statuses.append(status)
    total_paid = Mr * (payments - 1) + sum(X.get(j, 0) for j in range(1, payments)) + final
    base = calc(P, rate, years)
    interest = total_paid - P
    return dict(regular=Mr, payments=payments, n=n, final=final, total=total_paid, interest=interest,
                used=used, statuses=statuses, ending=ending,
                months_saved=base['payments'] - payments, interest_saved=base['interest'] - interest)


# Spec examples (docs/v2/04-extra-payments.md §6), computed by calc_extra above:
# (id, inputs, extras, payments, final, total, interest, used per item, status per item,
#  months_saved, interest_saved, ending)
EXPECTED_EXTRA = [
    ('E1', ('100000', '3.5', 30), [(24, '5000')], 332, '246.84', '153879.08', '53879.08',
     ['5000.00'], ['used'], 28, '7778.30', 'schedule'),
    ('E2', ('100000', '3.5', 30), [(60, '200000')], 60, '90146.42', '116639.78', '16639.78',
     ['89697.38'], ['partly_used'], 300, '45017.60', 'extra'),
    ('E3', ('100000', '3.5', 30), [(60, '50000'), (60, '50000'), (120, '1000')], 60, '90146.42', '116639.78', '16639.78',
     ['50000.00', '39697.38', '0.00'], ['used', 'partly_used', 'after_payoff'], 300, '45017.60', 'extra'),
    ('E4', ('10000', '5', 1), [(12, '500')], 12, '856.13', '10272.90', '272.90',
     ['0.00'], ['loan_ends_this_month'], 0, '0.00', 'schedule'),
    ('E5', ('200000', '4.5', 25), [(12, '10000'), (36, '10000'), (60, '10000')], 236, '670.04', '291910.14', '91910.14',
     ['10000.00', '10000.00', '10000.00'], ['used', 'used', 'used'], 64, '41590.60', 'schedule'),
    ('E6', ('120000', '0', 10), [(1, '1000')], 119, '1000.00', '120000.00', '0.00',
     ['1000.00'], ['used'], 1, '0.00', 'schedule'),
    ('E7', ('100000', '3.5', 30), [(100, '81757.90')], 100, '82206.94', '126661.90', '26661.90',
     ['81757.90'], ['used'], 260, '34995.48', 'zero_tail'),
    ('E8', ('1000.29', '20', 30), [(354, '100')], 354, '8.08', '5910.24', '4909.95',
     ['0.00'], ['loan_ends_this_month'], 0, '0.00', 'schedule'),
    ('E9', ('1000.02', '20', 30), [(264, '783.50'), (265, '1000')], 265, '16.71', '5211.65', '4211.63',
     ['783.50', '0.00'], ['used', 'tiny_balance'], 95, '815.92', 'extra'),
    ('E10', ('100000', '3.5', 30), [(60, '95000'), (60, '5000')], 60, '90146.42', '116639.78', '16639.78',
     ['89697.38', '0.00'], ['partly_used', 'covered_by_earlier'], 300, '45017.60', 'extra'),
    ('E11', ('250000', '6', 20), [(120, '200000')], 120, '163119.24', '376257.76', '126257.76',
     ['161328.16'], ['partly_used'], 120, '53600.35', 'extra'),
    ('E12', ('100000', '3.5', 30), [(1, '200000')], 1, '100291.67', '100291.67', '291.67',
     ['99842.63'], ['partly_used'], 359, '61365.71', 'extra'),
]


def check_extra_examples():
    failures = 0
    for name, args, extras, payments, final, total, interest, used, statuses, saved_m, saved_i, ending in EXPECTED_EXTRA:
        x = calc_extra(*args, [(m, F(a)) for m, a in extras])
        got = (x['payments'], x['final'], x['total'], x['interest'], x['used'], x['statuses'], x['months_saved'],
               x['interest_saved'], x['ending'])
        want = (payments, F(final), F(total), F(interest), [F(u) for u in used], statuses, saved_m, F(saved_i), ending)
        ok = got == want
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name} {args} {extras}" + ('' if ok else f'\n     got  {got}\n     want {want}'))
    return failures


# --- Building edge cases on purpose (the random sweep would almost never reach them) -----------


def run_until(P, rate, years, extras, month):
    """Amount due D in `month`, given the extras before it, or None if the loan ends earlier."""
    P, r, n = F(P), F(rate) / 1200, years * 12
    Mr = calc(P, rate, years)['regular']
    X = {}
    for m, a in extras:
        X[m] = X.get(m, 0) + F(a)
    B = P
    for k in range(1, month + 1):
        D = B * (1 + r)
        if k == month:
            return D
        if k == n or D <= Mr or D <= Mr + X.get(k, 0):
            return None
        B = D - Mr - X.get(k, 0)
    return None


def zero_tail_extra(P, rate, years, month, before=()):
    """An extra for `month` that leaves less than half a cent owed afterwards (zero-tail path),
    given the extras `before` (all in earlier months), or None if the balance does not allow one."""
    r, n = F(rate) / 1200, years * 12
    Mr = calc(P, rate, years)['regular']
    D = run_until(P, rate, years, list(before), month)
    if D is None or month >= n or D <= Mr:
        return None
    rest = D - Mr
    extra = F(math.floor(rest * 100), 100)
    left = rest - extra
    return extra if extra > 0 and 0 < left and rc(left * (1 + r)) == 0 else None


def tiny_balance_extra(P, rate, years, month):
    """An extra for `month` after which month + 1 owes D in (M, M + 0.005): an item in month + 1
    then gets the 'tiny_balance' status (spec §3.3). None if not possible at that month."""
    r, n = F(rate) / 1200, years * 12
    Mr = calc(P, rate, years)['regular']
    if month + 1 >= n:
        return None
    D = run_until(P, rate, years, [], month)
    if D is None or D <= Mr:
        return None
    target = (Mr + F(1, 400)) / (1 + r)  # balance after `month` whose next D is M + 0.0025
    extra = rc(D - Mr - target)
    if extra <= 0:
        return None
    nxt = (D - Mr - extra) * (1 + r)
    return extra if Mr < nxt < Mr + F(1, 200) else None


def random_extras(rng, n, cents, count=None):
    count = rng.randint(1, 10) if count is None else count
    return [(rng.randint(1, n), F(rng.choice([rng.randint(1, 100), rng.randint(1, 10**6), rng.randint(1, cents * 2)]), 100))
            for _ in range(count)]


def expected_month_totals(x, extras):
    """What each month's items must use in total (spec §3.3), from the result's K, ending and final."""
    X = {}
    for m, a in extras:
        X[m] = X.get(m, 0) + a
    K, totals = x['payments'], {}
    for m, total in X.items():
        if m < K or (m == K and x['ending'] == 'zero_tail'):
            totals[m] = total
        elif m == K and x['ending'] == 'extra':
            totals[m] = x['final'] - x['regular']
        else:
            totals[m] = F(0)
    return X, totals


def check_loan(P, rate, years, extras, x, b):
    """All §3.5 properties for one loan with extras. Returns the properties that fail."""
    r = F(rate) / 1200
    fails = []
    X, totals = expected_month_totals(x, extras)
    K, Mr = x['payments'], x['regular']
    # Rebuild the loan month by month from the payments and full-precision interest: it must end paid off.
    B = F(P)
    for j in range(1, K + 1):
        pay = x['final'] if j == K else Mr + X.get(j, 0)
        B = B * (1 + r) - pay
    if not (-F(1, 200) <= B < F(1, 200)):
        fails.append('loan not paid off')
    pays = [Mr + X.get(j, 0) for j in range(1, K)] + [x['final']]
    if sum(pays) != x['total']:
        fails.append('total != sum of payments')
    if not (x['final'] > 0 and Mr == b['regular'] and 1 <= K <= b['payments']):
        fails.append('final/regular/K')
    if not (x['interest'] == x['total'] - F(P) and x['interest'] >= 0):
        fails.append('interest')
    if not (x['months_saved'] == b['payments'] - K and x['months_saved'] >= 0):
        fails.append('months saved')
    if not (x['interest_saved'] == b['interest'] - x['interest'] and x['interest_saved'] >= 0):
        fails.append('interest saved >= 0')
    if x['ending'] == 'extra' and not (0 <= x['final'] - Mr <= X.get(K, 0)):
        fails.append('extra ending: final - M not in [0, X_K]')
    if x['ending'] == 'zero_tail' and x['final'] != Mr + X.get(K, 0):
        fails.append('zero tail: final != M + X_K')
    # Greedy split in request order, cents, bounds, statuses (recomputed from the definitions).
    left = dict(totals)
    for (m, a), u, s in zip(extras, x['used'], x['statuses']):
        want = min(a, left[m])
        left[m] -= want
        if u != want or u * 100 != int(u * 100) or not (0 <= u <= a):
            fails.append('split')
        want_status = ('used' if u == a else 'partly_used' if u > 0 else 'after_payoff' if m > K
                       else 'loan_ends_this_month' if x['ending'] == 'schedule'
                       else 'tiny_balance' if x['final'] == Mr else 'covered_by_earlier')
        if s != want_status:
            fails.append('status')
    return fails


def check_extra_sweep(loans=3200):
    """§3.5 properties over seeded loans in 8 strata, so that every ending and status occurs."""
    rng = random.Random(11)
    bad, built = [], {}
    endings = {'schedule': 0, 'extra': 0, 'zero_tail': 0}
    statuses = {s: 0 for s in STATUSES}
    loans_with_extras = loans_without = 0
    for i in range(loans):
        stratum = i % 8
        cents, years = rng.randint(100000, 100000000), rng.randint(1, 30)
        rate_bp = 0 if stratum == 3 else rng.randint(0, 2000)
        P, rate, n = F(cents, 100), F(rate_bp, 100), years * 12
        extras = []
        if stratum == 2:
            extras = random_extras(rng, n, cents)
        elif stratum == 3:  # 0 %: random extras, plus an exact pay-off (D == M + X is reachable only at 0 %)
            extras = [e for e in random_extras(rng, n, cents, rng.randint(0, 3)) if e[0] < n // 2]
            if n > 2:
                m = rng.randint(n // 2, n - 1)
                D = run_until(P, rate, years, extras, m)
                Mr = calc(P, rate, years)['regular']
                if D is not None and D > Mr:
                    extras.append((m, D - Mr))
                    built['exact pay-off'] = built.get('exact pay-off', 0) + 1
        elif stratum in (4, 5):  # zero tail; in stratum 5 after earlier extras and split into several items
            before = random_extras(rng, n, max(cents // 50, 1), rng.randint(1, 3)) if stratum == 5 else []
            for m in rng.sample(range(1, n), min(n - 1, 40)):
                prior = [e for e in before if e[0] < m]
                extra = zero_tail_extra(P, rate, years, m, prior)
                if extra is None:
                    continue
                if stratum == 5 and extra >= F(3, 100):
                    cut1 = F(rng.randint(1, int(extra * 100) - 2), 100)
                    cut2 = F(rng.randint(1, int((extra - cut1) * 100) - 1), 100)
                    parts = [cut1, cut2, extra - cut1 - cut2]
                else:
                    parts = [extra]
                extras = prior + [(m, a) for a in parts]
                key = 'zero tail, several items' + (' after earlier extras' if prior else '') if len(parts) > 1 else 'zero tail, one item'
                built[key] = built.get(key, 0) + 1
                break
        elif stratum == 6:  # tiny balance: the next month owes less than half a cent above M
            for m in rng.sample(range(1, max(n - 1, 2)), min(max(n - 2, 1), 40)):
                extra = tiny_balance_extra(P, rate, years, m)
                if extra is not None:
                    extras = [(m, extra), (m + 1, F(rng.randint(1, 10**6), 100))]
                    built['tiny balance'] = built.get('tiny balance', 0) + 1
                    break
        elif stratum == 7:  # pay-off month with several items: later ones are covered by earlier ones
            m = rng.randint(1, n)
            extras = [(m, F(cents * 2, 100)), (m, F(rng.randint(1, 10**6), 100))] + random_extras(rng, n, cents, 2)
        x = calc_extra(P, rate, years, extras)
        b = calc(P, rate, years)
        if not extras:
            if stratum not in (0, 1):
                continue  # a construction did not fit this loan
            loans_without += 1
            same = all(x[k] == b[k] for k in ('regular', 'payments', 'final', 'total', 'interest'))
            if not (same and x['months_saved'] == 0 and x['interest_saved'] == 0 and x['used'] == []):
                bad.append((i, 'no extras differs from V1'))
            continue
        loans_with_extras += 1
        endings[x['ending']] += 1
        for s in x['statuses']:
            statuses[s] += 1
        for fail in check_loan(P, rate, years, extras, x, b):
            bad.append((i, fail))
    print(f'extra sweep: {loans_without} loans without extras (= V1), {loans_with_extras} with extras; '
          f'endings {endings}; statuses {statuses}; built {built}; violations {len(bad)}')
    for item in bad[:5]:
        print('   ', item)
    missing = [s for s, c in statuses.items() if c == 0] + [e for e, c in endings.items() if c == 0]
    if missing:
        print('    never reached:', missing)
    return int(bool(bad) or bool(missing) or len(built) < 5)


if __name__ == '__main__':
    sys.exit(1 if check_examples() + check_sweep() + check_extra_examples() + check_extra_sweep() else 0)

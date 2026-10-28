"""Live check against the real Supabase project (Phases 6–7). Skipped unless configured.

Run on purpose from backend/ with the secret key in backend/.env (never committed):
    uv run --env-file .env python -m pytest -m live
Each test saves one calculation through `save_calculation`, reads it back with the secret key, then
deletes it (its extra payments go with it: `on delete cascade`).
"""
import asyncio
import os
from decimal import Decimal

import httpx2
import pytest

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import ExtraPayment, LoanInput
from mortgage.persistence.repository import ENGINE_VERSION, repository_from_env

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not (os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_SECRET_KEY')),
                       reason='SUPABASE_URL and SUPABASE_SECRET_KEY are not set'),
]


def rest(table: str) -> str:
    return os.environ['SUPABASE_URL'].rstrip('/') + f'/rest/v1/{table}'


def headers() -> dict[str, str]:
    return {'apikey': os.environ['SUPABASE_SECRET_KEY']}


def save_and_read(loan: LoanInput):
    row_id = asyncio.run(repository_from_env().save(loan, calculate_mortgage(loan)))
    assert row_id is not None
    rows = httpx2.get(rest('calculations'), params={'id': f'eq.{row_id}'}, headers=headers(), timeout=10).json()
    items = httpx2.get(rest('extra_payments'), params={'calculation_id': f'eq.{row_id}', 'order': 'position'},
                       headers=headers(), timeout=10).json()
    return row_id, rows, items


def delete(row_id: str) -> None:
    httpx2.delete(rest('calculations'), params={'id': f'eq.{row_id}'}, headers=headers(), timeout=10)
    assert httpx2.get(rest('calculations'), params={'id': f'eq.{row_id}'}, headers=headers(), timeout=10).json() == []
    assert httpx2.get(rest('extra_payments'), params={'calculation_id': f'eq.{row_id}'},
                      headers=headers(), timeout=10).json() == []


def test_live_save_read_back_and_delete():
    row_id, rows, items = save_and_read(LoanInput(Decimal('1075.15'), Decimal('20'), 30))
    try:
        assert len(rows) == 1
        row = rows[0]
        # numeric columns come back as JSON numbers from PostgREST; compare them as decimals of their text.
        assert Decimal(str(row['total_paid'])) == Decimal('6379.35')
        assert (row['number_of_payments'], row['months_saved'], row['engine_version']) == (355, 0, ENGINE_VERSION)
        assert items == []
    finally:
        delete(row_id)


def test_live_save_with_extra_payments_in_one_transaction():
    loan = LoanInput(Decimal('100000'), Decimal('3.5'), 30, (
        ExtraPayment(60, Decimal('50000')), ExtraPayment(60, Decimal('50000')), ExtraPayment(120, Decimal('1000'))))
    row_id, rows, items = save_and_read(loan)
    try:
        assert len(rows) == 1
        assert (rows[0]['number_of_payments'], rows[0]['months_saved']) == (60, 300)
        assert Decimal(str(rows[0]['interest_saved'])) == Decimal('45017.60')
        assert [(i['position'], i['month'], Decimal(str(i['used_amount'])), i['status']) for i in items] == [
            (0, 60, Decimal('50000'), 'used'), (1, 60, Decimal('39697.38'), 'partly_used'), (2, 120, Decimal('0'), 'after_payoff')]
    finally:
        delete(row_id)

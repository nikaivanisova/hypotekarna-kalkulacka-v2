"""Live check against the real Supabase project (Phase 6). Skipped unless configured.

Run on purpose from backend/ with the secret key in backend/.env (never committed):
    uv run --env-file .env python -m pytest -m live
The test saves one row, reads it back with the secret key, then deletes it.
"""
import asyncio
import os
from decimal import Decimal

import httpx2
import pytest

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import LoanInput
from mortgage.persistence.repository import ENGINE_VERSION, repository_from_env

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not (os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_SECRET_KEY')),
                       reason='SUPABASE_URL and SUPABASE_SECRET_KEY are not set'),
]


def test_live_save_read_back_and_delete():
    loan = LoanInput(Decimal('1075.15'), Decimal('20'), 30)
    result = calculate_mortgage(loan)
    row_id = asyncio.run(repository_from_env().save(loan, result))
    assert row_id is not None

    url = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/calculations'
    headers = {'apikey': os.environ['SUPABASE_SECRET_KEY']}
    try:
        rows = httpx2.get(url, params={'id': f'eq.{row_id}'}, headers=headers, timeout=10).json()
        assert len(rows) == 1
        row = rows[0]
        # numeric columns come back as JSON numbers from PostgREST; compare them as decimals of their text.
        assert Decimal(str(row['total_paid'])) == Decimal('6379.35')
        assert (row['number_of_payments'], row['engine_version']) == (355, ENGINE_VERSION)
    finally:
        httpx2.delete(url, params={'id': f'eq.{row_id}'}, headers=headers, timeout=10)
    assert httpx2.get(url, params={'id': f'eq.{row_id}'}, headers=headers, timeout=10).json() == []

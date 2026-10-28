"""Saving calculations (FR-4) in Supabase through its REST API (plan §4; D4, D5; 04-extra-payments.md §5).

The calculation and its extra payments are saved in one transaction by the database function
`save_calculation(payload jsonb) returns uuid`, called as `POST /rest/v1/rpc/save_calculation`.

Best effort: save() returns the new row's id, or None if the row could not be saved. It never
raises and never logs the secret key. Money is sent as decimal strings, never as JSON numbers.

Settings (environment), both or neither:
    SUPABASE_URL         https://<project>.supabase.co (http:// only for a local stack)
    SUPABASE_SECRET_KEY  sb_secret_... (server-side only; never in the frontend or in git)
"""
import logging
import os
import uuid
from typing import Protocol

import httpx2

from mortgage.domain.types import LoanInput, MortgageResult

# Which calculation rules produced a row. Change it whenever the results for the same input could change.
ENGINE_VERSION = 'v2-calc-2'  # Phase 7: extra payments (04 §5)

log = logging.getLogger(__name__)


class CalculationRepository(Protocol):
    async def save(self, loan: LoanInput, result: MortgageResult) -> str | None: ...


class NullRepository:
    """Used when Supabase is not configured (D5: the result is still returned, with id null)."""

    async def save(self, loan: LoanInput, result: MortgageResult) -> str | None:
        return None


def _row(loan: LoanInput, result: MortgageResult) -> dict[str, object]:
    return {
        'loan_amount': str(loan.principal),
        'annual_rate': str(loan.annual_rate_percent),
        'term_years': loan.term_years,
        'number_of_payments': result.number_of_payments,
        'regular_payment': str(result.regular_payment),
        'final_payment': str(result.final_payment),
        'total_paid': str(result.total_paid),
        'total_interest': str(result.total_interest),
        'months_saved': result.months_saved,
        'interest_saved': str(result.interest_saved),
        'engine_version': ENGINE_VERSION,
        'extra_payments': [{'month': e.month, 'amount': str(e.amount), 'used_amount': str(e.used_amount),
                            'status': e.status} for e in result.extra_payments],
    }


def _saved_id(response: httpx2.Response) -> str | None:
    """The id the function returns: PostgREST sends a scalar `uuid` result as one JSON string."""
    try:
        row_id = response.json()
    except ValueError:
        return None
    try:
        return str(uuid.UUID(row_id)) if isinstance(row_id, str) else None
    except ValueError:
        return None


class SupabaseRepository:
    def __init__(self, url: str, secret_key: str, *, transport: httpx2.AsyncBaseTransport | None = None,
                 timeout_seconds: float = 3.0) -> None:
        local = url.startswith(('http://127.0.0.1', 'http://localhost'))
        if not (url.startswith('https://') or local):
            raise ValueError('SUPABASE_URL must be an https:// URL (http:// only for a local stack).')
        if not secret_key.startswith('sb_secret_'):
            raise ValueError('SUPABASE_SECRET_KEY must be a Supabase secret key (sb_secret_...).')
        self._endpoint = url.rstrip('/') + '/rest/v1/rpc/save_calculation'
        self._secret_key = secret_key
        self._transport = transport
        self.timeout_seconds = timeout_seconds

    def __repr__(self) -> str:
        return f'SupabaseRepository({self._endpoint!r})'

    async def save(self, loan: LoanInput, result: MortgageResult) -> str | None:
        headers = {'apikey': self._secret_key}  # the Supabase gateway derives Authorization from it
        try:
            async with httpx2.AsyncClient(transport=self._transport, timeout=self.timeout_seconds) as client:
                response = await client.post(self._endpoint, headers=headers, json={'payload': _row(loan, result)})
        except httpx2.HTTPError as error:
            log.warning('calculation not saved: %s', type(error).__name__)
            return None
        if response.status_code != 200:
            log.warning('calculation not saved: HTTP %d', response.status_code)
            return None
        row_id = _saved_id(response)
        if row_id is None:
            log.warning('calculation not saved: unexpected response body')
        return row_id


def repository_from_env() -> CalculationRepository:
    url = os.environ.get('SUPABASE_URL', '').strip()
    key = os.environ.get('SUPABASE_SECRET_KEY', '').strip()
    if url and key:
        return SupabaseRepository(url, key)
    if url or key:
        raise ValueError('Set both SUPABASE_URL and SUPABASE_SECRET_KEY, or neither.')
    return NullRepository()

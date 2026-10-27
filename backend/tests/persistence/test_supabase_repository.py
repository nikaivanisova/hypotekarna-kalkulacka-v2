"""Phase 6 — saving calculations in Supabase (FR-4, D5; plan §4), against a mock HTTP transport."""
import asyncio
import json
import logging
from decimal import Decimal

import httpx2
import pytest

from mortgage.domain.calculation import calculate_mortgage
from mortgage.domain.types import LoanInput
from mortgage.persistence.repository import (
    ENGINE_VERSION,
    NullRepository,
    SupabaseRepository,
    repository_from_env,
)

URL = 'https://project.supabase.co'
KEY = 'sb_secret_TESTKEYtestkey1234567890_abcd1234'
ROW_ID = '6f1c2d3e-4b5a-4c6d-8e7f-001122334455'
LOAN = LoanInput(Decimal('100000'), Decimal('3.5'), 30)
RESULT = calculate_mortgage(LOAN)


def repository(handler, url: str = URL) -> SupabaseRepository:
    return SupabaseRepository(url, KEY, transport=httpx2.MockTransport(handler))


def save(repo, loan=LOAN, result=RESULT):
    return asyncio.run(repo.save(loan, result))


def created(request):
    return httpx2.Response(201, json=[{'id': ROW_ID}])


def test_save_posts_one_row_to_the_rest_api():
    seen = []

    def handler(request):
        seen.append(request)
        return created(request)

    assert save(repository(handler)) == ROW_ID
    request = seen[0]
    assert request.method == 'POST'
    assert str(request.url) == f'{URL}/rest/v1/calculations?select=id'
    assert request.headers['apikey'] == KEY
    assert 'authorization' not in request.headers  # the gateway derives it from apikey (Supabase docs)
    assert request.headers['prefer'] == 'return=representation'
    assert request.headers['content-type'] == 'application/json'


def test_save_sends_money_as_strings_never_floats():
    bodies = []

    def handler(request):
        bodies.append(request.content.decode())
        return created(request)

    save(repository(handler))
    body = json.loads(bodies[0])
    assert body == {
        'loan_amount': '100000',
        'annual_rate': '3.5',
        'term_years': 30,
        'number_of_payments': 360,
        'regular_payment': '449.04',
        'final_payment': '452.02',
        'total_paid': '161657.38',
        'total_interest': '61657.38',
        'engine_version': ENGINE_VERSION,
    }
    parsed_with_floats_rejected = json.loads(bodies[0], parse_float=lambda s: pytest.fail(f'float in body: {s}'))
    assert parsed_with_floats_rejected == body


def test_save_normalises_a_trailing_slash_in_the_url():
    urls = []
    save(repository(lambda r: urls.append(str(r.url)) or created(r), url=URL + '/'))
    assert urls == [f'{URL}/rest/v1/calculations?select=id']


@pytest.mark.parametrize('status', [400, 401, 403, 404, 409, 500, 503])
def test_save_error_status_returns_none(status):
    assert save(repository(lambda r: httpx2.Response(status, json={'message': 'x'}))) is None


@pytest.mark.parametrize('error', [httpx2.ConnectError('refused'), httpx2.ReadTimeout('slow'), httpx2.RemoteProtocolError('x')])
def test_save_network_error_returns_none(error):
    def handler(request):
        raise error

    assert save(repository(handler)) is None


@pytest.mark.parametrize('body', [[], [{}], {'id': ROW_ID}, [{'id': 'not-a-uuid'}], [{'id': 12}], 'x',
                                  [{'id': ROW_ID}, {'id': ROW_ID}]])
def test_save_unexpected_response_returns_none(body):
    assert save(repository(lambda r: httpx2.Response(201, json=body))) is None


def test_save_non_json_response_returns_none():
    assert save(repository(lambda r: httpx2.Response(201, text='<html>'))) is None


def test_failures_are_logged_without_the_key(caplog):
    caplog.set_level(logging.WARNING)
    save(repository(lambda r: httpx2.Response(401, json={'message': f'bad key {KEY}'})))

    def handler(request):
        raise httpx2.ConnectError(f'cannot reach {KEY}')

    save(repository(handler))
    assert len(caplog.records) == 2
    assert all(record.levelno == logging.WARNING for record in caplog.records)
    assert KEY not in caplog.text
    assert '401' in caplog.text


def test_save_has_a_short_timeout():
    assert SupabaseRepository(URL, KEY).timeout_seconds <= 5


def test_null_repository_saves_nothing():
    assert asyncio.run(NullRepository().save(LOAN, RESULT)) is None


def test_repository_from_env_uses_supabase_when_configured(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', URL)
    monkeypatch.setenv('SUPABASE_SECRET_KEY', KEY)
    assert isinstance(repository_from_env(), SupabaseRepository)


def test_repository_from_env_is_null_when_not_configured():
    assert isinstance(repository_from_env(), NullRepository)


@pytest.mark.parametrize('variables', [{'SUPABASE_URL': URL}, {'SUPABASE_SECRET_KEY': KEY}])
def test_repository_from_env_refuses_half_a_configuration(monkeypatch, variables):
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        repository_from_env()


@pytest.mark.parametrize('url', ['http://project.supabase.co', 'ftp://x', 'project.supabase.co'])
def test_repository_refuses_a_non_https_url(url):
    with pytest.raises(ValueError):
        SupabaseRepository(url, KEY)


def test_repository_allows_http_for_a_local_stack():
    SupabaseRepository('http://127.0.0.1:54321', KEY)


@pytest.mark.parametrize('key', ['', 'sb_publishable_abc', 'eyJhbGciOi.anon'])
def test_repository_refuses_a_key_that_is_not_a_secret_key(key):
    with pytest.raises(ValueError):
        SupabaseRepository(URL, key)


def test_repository_repr_does_not_show_the_key():
    assert KEY not in repr(SupabaseRepository(URL, KEY))


# --- Second guards (docs/v1/06-retro.md §6.1 rule 3) -------------------------------------------


@pytest.mark.parametrize('status', [200, 202, 409])
def test_save_non_201_status_with_a_valid_looking_body_returns_none(status):
    assert save(repository(lambda r: httpx2.Response(status, json=[{'id': ROW_ID}]))) is None


def test_save_three_rows_returns_none():
    assert save(repository(lambda r: httpx2.Response(201, json=[{'id': ROW_ID}] * 3))) is None


def test_save_empty_201_body_returns_none():
    assert save(repository(lambda r: httpx2.Response(201, content=b''))) is None


def test_save_money_fields_are_strings():
    bodies = []
    save(repository(lambda r: bodies.append(json.loads(r.content)) or created(r)))
    for field in ('loan_amount', 'annual_rate', 'regular_payment', 'final_payment', 'total_paid', 'total_interest'):
        assert isinstance(bodies[0][field], str), field


def test_the_key_is_sent_only_in_the_apikey_header():
    seen = []
    save(repository(lambda r: seen.append(r) or created(r)))
    carrying = [name for name, value in seen[0].headers.items() if KEY in value]
    assert carrying == ['apikey']


@pytest.mark.parametrize('suffix', ['//', '/'])
def test_save_normalises_trailing_slashes(suffix):
    urls = []
    save(repository(lambda r: urls.append(str(r.url)) or created(r), url=URL + suffix))
    assert urls == [f'{URL}/rest/v1/calculations?select=id']


def test_repository_from_env_has_the_short_timeout(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', URL)
    monkeypatch.setenv('SUPABASE_SECRET_KEY', KEY)
    assert repository_from_env().timeout_seconds <= 5


def test_repository_str_does_not_show_the_key():
    assert KEY not in str(SupabaseRepository(URL, KEY))


@pytest.mark.parametrize('status', [403, 503])
def test_error_status_is_logged_without_the_key(caplog, status):
    caplog.set_level(logging.WARNING)
    save(repository(lambda r: httpx2.Response(status, json={'hint': KEY})))
    assert str(status) in caplog.text and KEY not in caplog.text

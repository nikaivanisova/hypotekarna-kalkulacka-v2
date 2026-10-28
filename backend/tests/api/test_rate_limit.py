"""Phase 8 — rate limiting (api/openapi.yaml `TooManyRequests`; decision Prompt 49: a simple limit in the app).

Per client IP, at most `limit` calculation requests per `window` seconds; then 429 problem+json
with Retry-After. Only POST /api/v1/calculations is limited. In memory, one server process.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from mortgage.api.app import create_app
from mortgage.api.rate_limit import RateLimit, RateLimitMiddleware, rate_limit_from_env
from mortgage.persistence.repository import NullRepository
from tests.api.test_api import CALC, VALID, conforms


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make_client(limit=3, window=60, clock=None) -> TestClient:
    app = create_app(cors_origins=['http://localhost:5173'], repository=NullRepository(),
                     rate_limit=RateLimit(limit, window), clock=clock or Clock())
    return TestClient(app, raise_server_exceptions=False)


def test_requests_up_to_the_limit_pass():
    client = make_client(limit=3)
    assert [client.post(CALC, json=VALID).status_code for _ in range(3)] == [200, 200, 200]


def test_the_request_over_the_limit_is_429_with_retry_after():
    clock = Clock()
    client = make_client(limit=3, window=60, clock=clock)
    for _ in range(3):
        client.post(CALC, json=VALID)
    clock.now += 10
    response = client.post(CALC, json=VALID)
    problem = conforms(response)
    assert response.status_code == 429
    assert problem['status'] == 429 and 'detail' not in problem
    assert response.headers['retry-after'] == '50'  # the oldest request leaves the window 50 s from now


def test_the_limit_resets_when_the_window_passes():
    clock = Clock()
    client = make_client(limit=2, window=60, clock=clock)
    client.post(CALC, json=VALID)
    client.post(CALC, json=VALID)
    assert client.post(CALC, json=VALID).status_code == 429
    clock.now += 60
    assert client.post(CALC, json=VALID).status_code == 200


def test_it_is_a_sliding_window_not_a_fixed_one():
    clock = Clock()
    client = make_client(limit=2, window=60, clock=clock)
    client.post(CALC, json=VALID)  # t = 1000
    clock.now += 30
    client.post(CALC, json=VALID)  # t = 1030
    clock.now += 31                # t = 1061: the first one has left, the second has not
    assert client.post(CALC, json=VALID).status_code == 200
    assert client.post(CALC, json=VALID).status_code == 429


def test_refused_requests_do_not_extend_the_wait():
    clock = Clock()
    client = make_client(limit=1, window=60, clock=clock)
    client.post(CALC, json=VALID)  # t = 1000
    for _ in range(5):
        clock.now += 10  # refused at t = 1010 … 1050; none of them may count
        response = client.post(CALC, json=VALID)
        assert response.status_code == 429
    assert response.headers['retry-after'] == '10'
    clock.now = 1060
    assert client.post(CALC, json=VALID).status_code == 200


def test_invalid_requests_count_too():
    client = make_client(limit=2)
    client.post(CALC, json={'loanAmount': 'abc'})
    client.post(CALC, content=b'not json', headers={'content-type': 'application/json'})
    assert client.post(CALC, json=VALID).status_code == 429


def test_health_and_the_contract_are_not_limited():
    client = make_client(limit=1)
    client.post(CALC, json=VALID)
    assert [client.get('/api/v1/health').status_code for _ in range(5)] == [200] * 5
    assert client.get('/openapi.json').status_code == 200


def test_cors_headers_are_set_on_429():
    client = make_client(limit=1)
    client.post(CALC, json=VALID, headers={'origin': 'http://localhost:5173'})
    response = client.post(CALC, json=VALID, headers={'origin': 'http://localhost:5173'})
    assert response.status_code == 429
    assert response.headers.get('access-control-allow-origin') == 'http://localhost:5173'


def run_middleware(middleware, host):
    sent = []

    async def inner(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b''})

    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    async def send(message):
        sent.append(message)

    middleware.app = inner
    scope = {'type': 'http', 'method': 'POST', 'path': CALC, 'headers': [], 'client': (host, 5000)}
    asyncio.run(middleware(scope, receive, send))
    return sent[0]['status']


def test_each_client_ip_has_its_own_limit():
    middleware = RateLimitMiddleware(None, RateLimit(1, 60), Clock())
    assert [run_middleware(middleware, '10.0.0.1'), run_middleware(middleware, '10.0.0.2')] == [200, 200]
    assert [run_middleware(middleware, '10.0.0.1'), run_middleware(middleware, '10.0.0.2')] == [429, 429]


def test_forwarded_headers_are_not_trusted():
    """Behind no proxy (local only, D10), X-Forwarded-For would let a client choose its own IP."""
    middleware = RateLimitMiddleware(None, RateLimit(1, 60), Clock())
    run_middleware(middleware, '10.0.0.1')

    sent = []

    async def inner(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})

    async def receive():
        return {'type': 'http.request', 'body': b''}

    async def send(message):
        sent.append(message)

    middleware.app = inner
    scope = {'type': 'http', 'method': 'POST', 'path': CALC, 'client': ('10.0.0.1', 1),
             'headers': [(b'x-forwarded-for', b'203.0.113.9')]}
    asyncio.run(middleware(scope, receive, send))
    assert sent[0]['status'] == 429


def test_memory_is_bounded_by_dropping_idle_clients():
    clock = Clock()
    middleware = RateLimitMiddleware(None, RateLimit(1, 60), clock, max_clients=100)
    for i in range(100):
        run_middleware(middleware, f'10.0.{i // 250}.{i % 250}')
    clock.now += 61
    run_middleware(middleware, '192.0.2.1')
    assert middleware.tracked_clients() == 1


@pytest.mark.parametrize(('value', 'expected'), [
    (None, RateLimit(30, 60)), ('30/60', RateLimit(30, 60)), ('5/1', RateLimit(5, 1)), (' 100 / 3600 ', RateLimit(100, 3600)),
    ('off', None)])
def test_rate_limit_from_env(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv('MORTGAGE_RATE_LIMIT', raising=False)
    else:
        monkeypatch.setenv('MORTGAGE_RATE_LIMIT', value)
    assert rate_limit_from_env() == expected


@pytest.mark.parametrize('value', ['30', 'abc', '0/60', '30/0', '-1/60', '30/60/1', ''])
def test_rate_limit_from_env_refuses_bad_values(monkeypatch, value):
    monkeypatch.setenv('MORTGAGE_RATE_LIMIT', value)
    with pytest.raises(ValueError):
        rate_limit_from_env()


def test_the_default_app_is_limited(monkeypatch):
    monkeypatch.delenv('MORTGAGE_RATE_LIMIT', raising=False)
    client = TestClient(create_app(cors_origins=['http://x'], repository=NullRepository()))
    statuses = [client.post(CALC, json=VALID).status_code for _ in range(31)]
    assert statuses[:30] == [200] * 30 and statuses[30] == 429


# --- Second guards (docs/v1/06-retro.md §6.1 rule 3) -------------------------------------------


def test_retry_after_rounds_up_to_whole_seconds():
    clock = Clock()
    client = make_client(limit=1, window=60, clock=clock)
    client.post(CALC, json=VALID)
    clock.now += 0.5
    assert client.post(CALC, json=VALID).headers['retry-after'] == '60'  # 59.5 s → 60


@pytest.mark.parametrize('path', ['/api/v1/health', '/openapi.json', '/docs'])
def test_other_paths_never_count(path):
    middleware = RateLimitMiddleware(None, RateLimit(1, 60), Clock())
    sent = []

    async def inner(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})

    async def send(message):
        sent.append(message)

    middleware.app = inner
    for _ in range(3):
        asyncio.run(middleware({'type': 'http', 'method': 'GET', 'path': path, 'headers': [], 'client': ('10.0.0.1', 1)},
                               None, send))
    assert [m['status'] for m in sent] == [200, 200, 200]
    assert run_middleware(middleware, '10.0.0.1') == 200  # the calculation limit is untouched


def test_three_clients_are_independent():
    middleware = RateLimitMiddleware(None, RateLimit(2, 60), Clock())
    statuses = [run_middleware(middleware, ip) for ip in ['a', 'b', 'c', 'a', 'b', 'c', 'a']]
    assert statuses == [200, 200, 200, 200, 200, 200, 429]


def test_idle_clients_are_dropped_but_active_ones_kept():
    clock = Clock()
    middleware = RateLimitMiddleware(None, RateLimit(1, 60), clock, max_clients=3)
    for ip in ['a', 'b', 'c']:
        run_middleware(middleware, ip)
    clock.now += 30
    run_middleware(middleware, 'd')  # 4 > 3: drops nobody yet (all are inside the window)
    assert middleware.tracked_clients() == 4
    clock.now += 31                  # a, b, c are now idle; d is not
    run_middleware(middleware, 'e')
    assert middleware.tracked_clients() == 2
    assert run_middleware(middleware, 'd') == 429  # d's limit survived the clean-up


def test_a_refusal_just_before_the_window_ends_does_not_count():
    clock = Clock()
    client = make_client(limit=1, window=60, clock=clock)
    client.post(CALC, json=VALID)  # t = 1000
    clock.now = 1059
    assert client.post(CALC, json=VALID).headers['retry-after'] == '1'
    clock.now = 1060
    assert client.post(CALC, json=VALID).status_code == 200

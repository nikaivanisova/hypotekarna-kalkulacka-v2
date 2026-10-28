"""Phase 4 — HTTP API (api/openapi.yaml; review docs/v2/03-api-review.md).

Every response the tests receive is checked against the contract: its status must be documented
for the operation, its Content-Type must match, and its body must be valid against the schema.
"""
import json
import random

import pytest
import yaml
from fastapi.testclient import TestClient
from openapi_schema_validator import OAS31Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

import mortgage.api.app as app_module
from mortgage.api.app import create_app
from mortgage.api.body_limit import MAX_BODY_BYTES
from tests.contract.test_openapi import SPEC_PATH

SPEC = yaml.safe_load(SPEC_PATH.read_text(encoding='utf-8'))
REGISTRY = Registry().with_resource('spec', Resource.from_contents(SPEC, default_specification=DRAFT202012))
CALC = '/api/v1/calculations'
OP = SPEC['paths'][CALC]['post']
REQUEST_EXAMPLES = OP['requestBody']['content']['application/json']['examples']
FRONTEND = 'http://localhost:5173'
VALID = {'loanAmount': '100 000', 'annualRate': '3,5', 'termYears': '30'}


def resolve(node: dict) -> dict:
    while '$ref' in node:
        target = SPEC
        for part in node['$ref'].removeprefix('#/').split('/'):
            target = target[part]
        node = target
    return node


def conforms(response, path: str = CALC, method: str = 'post') -> dict | None:
    """Asserts the response is documented in the contract; returns the parsed body."""
    documented = SPEC['paths'][path][method]['responses']
    status = str(response.status_code)
    assert status in documented, f'{status} is not documented for {method.upper()} {path}: {response.text}'
    content = resolve(documented[status]).get('content', {})
    media_type = response.headers.get('content-type', '').split(';')[0].strip()
    assert media_type in content, f'{status}: Content-Type {media_type!r} not in {list(content)}'
    body = response.json()
    schema = content[media_type]['schema']
    validator = OAS31Validator({'$ref': f'spec{schema["$ref"]}'} if '$ref' in schema else schema, registry=REGISTRY)
    assert [e.message for e in validator.iter_errors(body)] == []
    return body


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(cors_origins=[FRONTEND]), raise_server_exceptions=False)


def post_raw(client: TestClient, content: bytes | str, content_type: str | None = 'application/json'):
    headers = {'content-type': content_type} if content_type else {}
    return client.post(CALC, content=content, headers=headers)


# --- 200 / 422: the contract's own examples, end to end ------------------------------------------


@pytest.mark.parametrize('name', sorted(REQUEST_EXAMPLES))
def test_api_request_examples_give_the_documented_responses(client, name):
    response = client.post(CALC, json=REQUEST_EXAMPLES[name]['value'])
    body = conforms(response)
    if response.status_code == 200:
        expected = OP['responses']['200']['content']['application/json']['examples'][name]['value']
        assert body == dict(expected, id=None)  # no persistence before Phase 6
    else:
        assert response.status_code == 422
        assert body == OP['responses']['422']['content']['application/json']['examples'][name]['value']


def test_api_money_is_sent_as_strings(client):
    raw = client.post(CALC, json=VALID).text
    assert '"regularPayment":"449.04"' in raw.replace(' ', '')
    assert '449.04,' not in raw


def test_api_absent_null_empty_and_whitespace_are_required(client):
    body = conforms(client.post(CALC, json={'annualRate': None, 'termYears': '   '}))
    assert body == {'errors': [{'field': f, 'code': 'required'} for f in ('loanAmount', 'annualRate', 'termYears')]}


def test_api_empty_object_is_a_422_not_a_400(client):
    assert client.post(CALC, json={}).status_code == 422


# --- 400: malformed requests -------------------------------------------------------------------

MALFORMED = {
    'not json': b'loanAmount=1000',
    'truncated json': b'{"loanAmount": "1000"',
    'empty body': b'',
    'array': b'[]',
    'string': b'"100000"',
    'null': b'null',
    'number for a field': b'{"loanAmount": 100000}',
    'boolean for a field': b'{"loanAmount": true}',
    'object for a field': b'{"loanAmount": {"value": "1"}}',
    'unknown property': b'{"loanamount": "100000"}',
    'extraPayments not an array': b'{"extraPayments": {"month": "1", "amount": "1"}}',
    'extraPayments as a string': b'{"extraPayments": "none"}',
    'eleven extra payments': json.dumps({'extraPayments': [{'month': '1', 'amount': '1'}] * 11}).encode(),
    'extra payment not an object': b'{"extraPayments": ["12:100"]}',
    'extra payment null item': b'{"extraPayments": [null]}',
    'unknown property in an item': b'{"extraPayments": [{"month": "1", "amount": "1", "fee": "0"}]}',
    'misspelled property in an item': b'{"extraPayments": [{"Month": "1", "amount": "1"}]}',
    'number in an item': b'{"extraPayments": [{"month": 12, "amount": "100"}]}',
    '101 characters in an item': json.dumps({'extraPayments': [{'month': '1', 'amount': '1' * 101}]}).encode(),
    'lone surrogate in an item': b'{"extraPayments": [{"month": "\\ud800", "amount": "1"}]}',
    'duplicate property': b'{"loanAmount": "1000", "loanAmount": "2000"}',
    'duplicate property, same value': b'{"termYears": "30", "annualRate": "3", "termYears": "30"}',
    'NaN literal': b'{"loanAmount": NaN}',
    'Infinity literal': b'{"annualRate": Infinity}',
    'lone surrogate': b'{"loanAmount": "\\ud800"}',
    'lone low surrogate in another field': b'{"termYears": "3\\udfff0"}',
    'lone surrogate in a key': b'{"\\udc00": "1"}',
    'invalid utf-8': b'{"loanAmount": "\xff\xfe"}',
    '101 characters': json.dumps({'loanAmount': '1' * 101}).encode(),
    '150 characters in another field': json.dumps({'annualRate': ' ' * 150}).encode(),
}


@pytest.mark.parametrize('body', MALFORMED.values(), ids=MALFORMED.keys())
def test_api_malformed_request_is_400_problem(client, body):
    response = post_raw(client, body)
    problem = conforms(response)
    assert response.status_code == 400
    assert problem['status'] == 400


def test_api_100_characters_is_not_a_400(client):
    response = client.post(CALC, json={'loanAmount': '1' * 100, 'annualRate': '3', 'termYears': '10'})
    assert conforms(response) == {'errors': [{'field': 'loanAmount', 'code': 'above_max'}]}


@pytest.mark.parametrize('value', ['secret-value-123', '9' * 101, 'été'])
def test_api_problem_never_echoes_request_values(client, value):
    for body in ({'loanAmount': value, 'unknownProp': value}, {'loanAmount': [value]}):
        response = client.post(CALC, json=body)
        assert response.status_code == 400
        assert value not in response.text


def test_api_unknown_property_name_is_named(client):
    assert 'loanamount' in conforms(client.post(CALC, json={'loanamount': '1'}))['detail']


@pytest.mark.parametrize('key', ['k' * 41, 'line\nbreak', 'café'])
def test_api_unsafe_property_name_is_not_echoed(client, key):
    assert conforms(client.post(CALC, json={key: '1'}))['detail'] == 'Unknown property.'


# --- 413 / 415 ---------------------------------------------------------------------------------


def padded(size: int) -> bytes:
    """A valid request body of exactly `size` bytes (JSON whitespace padding)."""
    core = json.dumps(VALID).encode()
    return core[:-1] + b' ' * (size - len(core)) + b'}'


def test_api_body_at_the_limit_is_accepted(client):
    body = padded(MAX_BODY_BYTES)
    assert len(body) == 8192
    assert post_raw(client, body).status_code == 200


def test_api_body_over_the_limit_is_413(client):
    response = post_raw(client, padded(MAX_BODY_BYTES + 1))
    assert response.status_code == 413
    conforms(response)


def test_api_largest_form_body_reaches_validation_not_413(client):
    """04 §4.1: 23 fields × 100 '€' (3 bytes each in UTF-8) is the most the form can send."""
    euros = '€' * 100
    body = json.dumps({'loanAmount': euros, 'annualRate': euros, 'termYears': euros,
                       'extraPayments': [{'month': euros, 'amount': euros}] * 10}, ensure_ascii=False).encode()
    assert 7000 < len(body) <= MAX_BODY_BYTES
    response = post_raw(client, body)
    assert response.status_code == 422
    assert len(conforms(response)['errors']) == 23


@pytest.mark.parametrize(('count', 'status'), [(10, 200), (11, 400)])
def test_api_extra_payment_count_limit(client, count, status):
    items = [{'month': str(m), 'amount': '100'} for m in range(1, count + 1)]
    response = client.post(CALC, json={**VALID, 'extraPayments': items})
    assert response.status_code == status
    conforms(response)


def test_api_extra_payments_end_to_end(client):
    body = conforms(client.post(CALC, json={**VALID, 'extraPayments': [{'month': '24', 'amount': '5 000'}]}))
    assert (body['numberOfPayments'], body['regularPayment'], body['monthsSaved'], body['interestSaved']) == (
        332, '449.04', 28, '7778.30')
    assert body['extraPayments'] == [{'month': 24, 'amount': '5000.00', 'usedAmount': '5000.00', 'status': 'used'}]


def test_api_without_extra_payments_reports_empty_savings(client):
    body = conforms(client.post(CALC, json=VALID))
    assert (body['monthsSaved'], body['interestSaved'], body['extraPayments']) == (0, '0.00', [])


def test_api_item_errors_carry_index_and_property(client):
    body = conforms(client.post(CALC, json={**VALID, 'extraPayments': [{'month': '1', 'amount': '1'}, {}]}))
    assert body == {'errors': [{'field': 'extraPayments', 'code': 'required', 'index': 1, 'property': 'month'},
                               {'field': 'extraPayments', 'code': 'required', 'index': 1, 'property': 'amount'}]}


def test_api_chunked_body_over_the_limit_is_413(client):
    """No Content-Length: the limit is enforced while the body streams in."""
    chunks = iter([b'{"loanAmount": "', b'1' * 5000, b'1' * 5000, b'"}'])
    response = client.post(CALC, content=chunks, headers={'content-type': 'application/json'})
    assert 'content-length' not in response.request.headers
    assert response.status_code == 413
    conforms(response)


async def run_middleware(headers: list[tuple[bytes, bytes]]) -> tuple[int, bool]:
    """Calls the body-limit middleware directly; returns (status, whether the body was read)."""
    from mortgage.api.body_limit import BodySizeLimitMiddleware

    read = False
    sent: list[dict] = []

    async def receive():
        nonlocal read
        read = True
        return {'type': 'http.request', 'body': b'{}', 'more_body': False}

    async def send(message):
        sent.append(message)

    async def inner(scope, receive_, send_):
        await receive_()
        await send_({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send_({'type': 'http.response.body', 'body': b''})

    scope = {'type': 'http', 'method': 'POST', 'path': CALC, 'headers': headers}
    await BodySizeLimitMiddleware(inner)(scope, receive, send)
    return sent[0]['status'], read


@pytest.mark.parametrize(('declared', 'expected'), [
    (b'50000', (413, False)), (str(MAX_BODY_BYTES + 1).encode(), (413, False)),
    (str(MAX_BODY_BYTES).encode(), (200, True)), (b'2', (200, True))])
def test_api_declared_oversized_body_is_refused_without_reading_it(declared, expected):
    import asyncio

    assert asyncio.run(run_middleware([(b'content-length', declared)])) == expected


@pytest.mark.parametrize('declared', [b'-1', b'12abc'])
def test_api_invalid_content_length_is_400_without_reading_the_body(declared):
    import asyncio

    assert asyncio.run(run_middleware([(b'content-length', declared)])) == (400, False)


@pytest.mark.parametrize('origins', [['*'], [FRONTEND, '*']])
def test_api_cors_wildcard_is_refused(origins):
    with pytest.raises(ValueError):
        create_app(cors_origins=origins)


def test_api_chunked_body_one_byte_over_the_limit_is_413(client):
    body = padded(MAX_BODY_BYTES + 1)
    response = client.post(CALC, content=iter([body[:5000], body[5000:]]), headers={'content-type': 'application/json'})
    assert response.status_code == 413


def test_api_openapi_document_has_the_contract_only_parts(client):
    """FastAPI's generated document would have no problem responses and no `servers: /`."""
    document = client.get('/openapi.json').json()
    assert document['servers'] == [{'url': '/', 'description': SPEC['servers'][0]['description']}]
    assert '413' in document['paths'][CALC]['post']['responses']


@pytest.mark.parametrize('content_type', ['text/plain', 'application/x-www-form-urlencoded', None])
def test_api_non_json_content_type_is_415(client, content_type):
    response = post_raw(client, json.dumps(VALID), content_type)
    assert response.status_code == 415
    conforms(response)


def test_api_json_content_type_with_charset_is_accepted(client):
    assert post_raw(client, json.dumps(VALID), 'application/json; charset=utf-8').status_code == 200


# --- 500 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize('error', [RuntimeError, KeyError, ZeroDivisionError])
def test_api_unexpected_error_is_500_problem_without_detail(client, monkeypatch, error):
    def boom(_raw):
        raise error('database password is hunter2')

    monkeypatch.setattr(app_module, 'run_calculator', boom)
    response = client.post(CALC, json=VALID)
    problem = conforms(response)
    assert response.status_code == 500
    assert 'detail' not in problem
    assert 'hunter2' not in response.text and 'Traceback' not in response.text


# --- health, OpenAPI document, other routes ----------------------------------------------------


def test_api_health(client):
    response = client.get('/api/v1/health')
    assert conforms(response, '/api/v1/health', 'get') == {'status': 'ok'}


def test_api_serves_the_contract_as_its_openapi_document(client):
    assert client.get('/openapi.json').json() == SPEC
    assert client.get('/docs').status_code == 200


@pytest.mark.parametrize(('method', 'path', 'status'), [('get', '/nope', 404), ('get', CALC, 405)])
def test_api_other_http_errors_are_problems_too(client, method, path, status):
    response = client.request(method, path)
    assert response.status_code == status
    assert response.headers['content-type'].startswith('application/problem+json')
    assert response.json()['status'] == status


# --- CORS --------------------------------------------------------------------------------------


def preflight(client: TestClient, origin: str):
    return client.options(CALC, headers={
        'origin': origin, 'access-control-request-method': 'POST', 'access-control-request-headers': 'content-type'})


def test_api_cors_allows_the_frontend_origin(client):
    assert preflight(client, FRONTEND).headers.get('access-control-allow-origin') == FRONTEND
    response = client.post(CALC, json=VALID, headers={'origin': FRONTEND})
    assert response.headers.get('access-control-allow-origin') == FRONTEND


def test_api_cors_rejects_other_origins(client):
    assert 'access-control-allow-origin' not in preflight(client, 'https://evil.example').headers
    response = client.post(CALC, json=VALID, headers={'origin': 'https://evil.example'})
    assert 'access-control-allow-origin' not in response.headers


def test_api_cors_origins_come_from_the_environment(monkeypatch):
    monkeypatch.setenv('MORTGAGE_CORS_ORIGINS', 'https://a.example, https://b.example')
    env_client = TestClient(create_app())
    assert preflight(env_client, 'https://b.example').headers.get('access-control-allow-origin') == 'https://b.example'
    assert 'access-control-allow-origin' not in preflight(env_client, FRONTEND).headers


# --- Phase 6: saving (FR-4, D5) ----------------------------------------------------------------

SAVED_ID = '6f1c2d3e-4b5a-4c6d-8e7f-001122334455'


class FakeRepository:
    def __init__(self, returns=SAVED_ID, raises=None):
        self.calls = []
        self.returns = returns
        self.raises = raises

    async def save(self, loan, result):
        self.calls.append((loan, result))
        if self.raises:
            raise self.raises
        return self.returns


def client_with(repository) -> TestClient:
    return TestClient(create_app(cors_origins=[FRONTEND], repository=repository), raise_server_exceptions=False)


@pytest.mark.parametrize('saved_id', [SAVED_ID, '00000000-0000-4000-8000-000000000001'])
def test_api_saves_a_successful_calculation_and_returns_its_id(saved_id):
    repository = FakeRepository(returns=saved_id)
    body = conforms(client_with(repository).post(CALC, json=VALID))
    assert body['id'] == saved_id
    [(loan, result)] = repository.calls
    assert (str(loan.principal), str(loan.annual_rate_percent), loan.term_years) == ('100000', '3.5', 30)
    assert str(result.regular_payment) == '449.04'


@pytest.mark.parametrize('body', [{'loanAmount': 'abc'}, {'loanamount': '1'}])
def test_api_saves_nothing_for_invalid_or_malformed_requests(body):
    repository = FakeRepository()
    response = client_with(repository).post(CALC, json=body)
    assert response.status_code in (400, 422)
    assert repository.calls == []


def test_api_returns_the_result_with_null_id_when_saving_fails():
    body = conforms(client_with(FakeRepository(returns=None)).post(CALC, json=VALID))
    assert body['id'] is None
    assert body['regularPayment'] == '449.04'


@pytest.mark.parametrize('error', [RuntimeError('db down'), ConnectionError('refused'), ValueError('bad')])
def test_api_returns_the_result_with_null_id_when_the_repository_raises(error):
    """D5: saving is best effort, even if a repository breaks its own 'never raises' promise."""
    response = client_with(FakeRepository(raises=error)).post(CALC, json=VALID)
    body = conforms(response)
    assert response.status_code == 200
    assert body['id'] is None


def test_api_without_supabase_settings_saves_nothing():
    assert conforms(TestClient(create_app(cors_origins=[FRONTEND])).post(CALC, json=VALID))['id'] is None


# --- Seeded fuzz: every response conforms, whatever the body -----------------------------------


def random_value(rng: random.Random, depth: int = 0):
    kind = rng.randrange(9 if depth < 2 else 6)
    match kind:
        case 0: return None
        case 1: return rng.choice([True, False])
        case 2: return rng.randint(-10**6, 10**12)
        case 3: return rng.uniform(-1e6, 1e6)
        case 4: return ''.join(rng.choice('0123456789 ,.-eE+xa −') for _ in range(rng.randint(0, 12)))
        case 5: return rng.choice(['100000', '3,5', '30', '', ' ', '1 000 000,00', '0', '-0', '1e5', 'NaN'])
        case 6: return [random_value(rng, depth + 1) for _ in range(rng.randint(0, 3))]
        case 7: return {rng.choice(['loanAmount', 'x']): random_value(rng, depth + 1)}
        case _: return '9' * rng.randint(95, 105)


def test_api_fuzz_every_response_conforms(client):
    rng = random.Random(4)
    statuses = set()
    plausible = ['100000', '3,5', '30', '1 000 000,00', '0', '20', '1', '12,5', '', ' ', '-0', '1e5', None]
    for _ in range(600):
        roll = rng.random()
        if roll < 0.15:
            body = random_value(rng)
        elif roll < 0.5:
            body = {k: rng.choice(plausible) for k in ('loanAmount', 'annualRate', 'termYears')}
        else:
            keys = rng.sample(['loanAmount', 'annualRate', 'termYears', 'loanamount', 'extra'], rng.randint(0, 4))
            body = {k: random_value(rng) for k in keys}
        response = post_raw(client, json.dumps(body))  # json=None would send no body at all
        conforms(response)
        statuses.add(response.status_code)
    assert statuses == {200, 400, 422}

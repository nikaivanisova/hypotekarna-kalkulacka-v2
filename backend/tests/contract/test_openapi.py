"""Contract checks for api/openapi.yaml (Phase 3; review: docs/v2/03-api-review.md).

- The document is valid OpenAPI 3.1.
- Every example in the document is valid against its own schema.
- Every request example, run through the real calculator, gives exactly the documented response
  example of the same name (docs/v1/06-retro.md §6.1 rule 6: examples are hypotheses until recomputed).
- Money is a string everywhere in the contract, never a number.
- Requests are closed, responses are open (forward compatibility for Phase 7).
Phase 4 adds HTTP-level contract tests against the running FastAPI app.
"""
from pathlib import Path
from typing import get_args

import pytest
import yaml
from openapi_schema_validator import OAS31Validator
from openapi_spec_validator import validate as validate_spec
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from mortgage.app.calculator import Calculated, Rejected, run_calculator
from mortgage.domain.types import ExtraPaymentProperty, ExtraPaymentStatus, Field, ValidationErrorCode

SPEC_PATH = Path(__file__).resolve().parents[3] / 'api' / 'openapi.yaml'
SPEC = yaml.safe_load(SPEC_PATH.read_text(encoding='utf-8'))
SCHEMAS = SPEC['components']['schemas']
OPERATION = SPEC['paths']['/api/v1/calculations']['post']
REQUEST_EXAMPLES = OPERATION['requestBody']['content']['application/json']['examples']
RESULT_EXAMPLES = OPERATION['responses']['200']['content']['application/json']['examples']
ERROR_EXAMPLES = OPERATION['responses']['422']['content']['application/json']['examples']
MONEY_FIELDS = ('regularPayment', 'finalPayment', 'totalPaid', 'totalInterest', 'interestSaved')
REGISTRY = Registry().with_resource('spec', Resource.from_contents(SPEC, default_specification=DRAFT202012))


def validator(schema: dict) -> OAS31Validator:
    """Validates against a schema that may $ref '#/components/...' of the spec."""
    return OAS31Validator({'$ref': f'spec{schema["$ref"]}'} if '$ref' in schema else schema, registry=REGISTRY)


def resolve(node: dict) -> dict:
    while '$ref' in node:
        target = SPEC
        for part in node['$ref'].removeprefix('#/').split('/'):
            target = target[part]
        node = target
    return node


def media_objects():
    """Every (location, media object) with a schema: request bodies and responses, incl. components."""
    responses = [(f'components.responses.{n}', r) for n, r in SPEC['components']['responses'].items()]
    for path, item in SPEC['paths'].items():
        for method, op in item.items():
            if 'requestBody' in op:
                responses.append((f'{method} {path} request', op['requestBody']))
            responses += [(f'{method} {path} {status}', r) for status, r in op['responses'].items()]
    for location, holder in responses:
        for media_type, media in resolve(holder).get('content', {}).items():
            if 'schema' in media:
                yield f'{location} {media_type}', media


def all_examples():
    for location, media in media_objects():
        if 'example' in media:
            yield location, media['schema'], media['example']
        for name, example in media.get('examples', {}).items():
            yield f'{location} [{name}]', media['schema'], example['value']


def test_contract_is_valid_openapi_31():
    validate_spec(SPEC)
    assert SPEC['openapi'].startswith('3.1')


@pytest.mark.parametrize(('location', 'schema', 'value'), list(all_examples()), ids=lambda x: x if isinstance(x, str) else '')
def test_contract_examples_match_their_schemas(location, schema, value):
    assert [e.message for e in validator(schema).iter_errors(value)] == []


def test_contract_every_request_example_has_one_response_example():
    assert set(REQUEST_EXAMPLES) == set(RESULT_EXAMPLES) | set(ERROR_EXAMPLES)
    assert not set(RESULT_EXAMPLES) & set(ERROR_EXAMPLES)


@pytest.mark.parametrize('name', sorted(REQUEST_EXAMPLES))
def test_contract_example_matches_backend(name):
    body = REQUEST_EXAMPLES[name]['value']
    raw = {field: body.get(field) for field in ('loanAmount', 'annualRate', 'termYears')}
    raw['extraPayments'] = body.get('extraPayments')
    outcome = run_calculator(raw)
    if name in RESULT_EXAMPLES:
        assert isinstance(outcome, Calculated), outcome
        expected = {k: v for k, v in RESULT_EXAMPLES[name]['value'].items() if k != 'id'}
        r = outcome.result
        assert {'numberOfPayments': r.number_of_payments, 'regularPayment': str(r.regular_payment),
                'finalPayment': str(r.final_payment), 'totalPaid': str(r.total_paid),
                'totalInterest': str(r.total_interest), 'monthsSaved': r.months_saved,
                'interestSaved': str(r.interest_saved),
                'extraPayments': [{'month': e.month, 'amount': str(e.amount), 'usedAmount': str(e.used_amount),
                                   'status': e.status} for e in r.extra_payments]} == expected
    else:
        assert isinstance(outcome, Rejected), outcome
        errors = [{'field': e.field, 'code': e.code, **({'index': e.index, 'property': e.property}
                                                          if e.index is not None else {})} for e in outcome.errors]
        assert errors == ERROR_EXAMPLES[name]['value']['errors']


def test_contract_money_is_never_a_number():
    result_validator = validator({'$ref': '#/components/schemas/CalculationResult'})
    for field in MONEY_FIELDS:
        assert SCHEMAS['CalculationResult']['properties'][field]['$ref'] == '#/components/schemas/Money'
        sample = dict(RESULT_EXAMPLES['standard']['value'], **{field: 449.04})
        assert not result_validator.is_valid(sample), f'{field} accepted a JSON number'
    assert SCHEMAS['Money']['type'] == 'string'


@pytest.mark.parametrize('value', ['449.0', '449', '-1.00', '01.00', '1e2', '449.040'])
def test_contract_money_pattern_rejects_non_canonical_amounts(value):
    assert not validator({'$ref': '#/components/schemas/Money'}).is_valid(value)


def test_contract_request_is_closed_and_responses_are_open():
    """Review findings #1, #9: unknown request properties are a 400 (also inside extra-payment items);
    responses may gain properties."""
    assert SCHEMAS['CalculationRequest']['additionalProperties'] is False
    closed = [name for name, schema in SCHEMAS.items() if schema.get('additionalProperties') is False]
    closed += [location for location, media in media_objects()
               if 'request' not in location and resolve(media['schema']).get('additionalProperties') is False]
    assert sorted(closed) == ['CalculationRequest', 'ExtraPaymentInput']  # request side only


def test_contract_known_codes_and_fields_equal_the_backend_types():
    """Review finding #2: the vocabulary is open (no enum), but the documented values are exactly the backend's."""
    for name in ('Field', 'ValidationErrorCode', 'ExtraPaymentStatus'):
        assert 'enum' not in SCHEMAS[name], name
    assert SCHEMAS['Field']['examples'] == list(get_args(Field.__value__)) + ['extraPayments']
    assert set(SCHEMAS['ValidationErrorCode']['examples']) == set(get_args(ValidationErrorCode.__value__))
    assert set(SCHEMAS['ExtraPaymentStatus']['examples']) == set(get_args(ExtraPaymentStatus.__value__))
    assert SCHEMAS['ValidationError']['properties']['property']['examples'] == list(get_args(ExtraPaymentProperty.__value__))


def test_contract_item_errors_require_index_and_property():
    """05 finding 11: for field extraPayments, index and property are required (if/then)."""
    error = validator({'$ref': '#/components/schemas/ValidationError'})
    assert error.is_valid({'field': 'extraPayments', 'code': 'required', 'index': 0, 'property': 'month'})
    assert not error.is_valid({'field': 'extraPayments', 'code': 'required', 'index': 0})
    assert not error.is_valid({'field': 'extraPayments', 'code': 'required', 'property': 'month'})
    assert error.is_valid({'field': 'loanAmount', 'code': 'required'})


def test_contract_extra_payment_items_are_closed_and_limited():
    request = validator({'$ref': '#/components/schemas/CalculationRequest'})
    item = {'month': '12', 'amount': '100'}
    assert request.is_valid({'extraPayments': [item] * 10})
    assert request.is_valid({'extraPayments': None}) and request.is_valid({'extraPayments': []})
    assert not request.is_valid({'extraPayments': [item] * 11})
    assert not request.is_valid({'extraPayments': [{**item, 'fee': '1'}]})
    assert not request.is_valid({'extraPayments': [{'month': 12, 'amount': '100'}]})
    assert not request.is_valid({'extraPayments': item})

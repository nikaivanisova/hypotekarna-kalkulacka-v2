"""Strict reading of the CalculationRequest body (api/openapi.yaml `CalculationRequest`, `RawInput`).

Anything that is not exactly an object of the three optional string-or-null properties, plus the
optional `extraPayments` list of closed {month, amount} items (Phase 7), is a malformed request (400).
Whether the strings are valid input is decided later (422).
"""
import json

from mortgage.domain.types import Field, RawExtraPayment, RawLoanInput

FIELDS: tuple[Field, ...] = ('loanAmount', 'annualRate', 'termYears')
EXTRA_PAYMENTS = 'extraPayments'
ITEM_PROPERTIES = ('month', 'amount')
MAX_EXTRA_PAYMENTS = 10
MAX_LENGTH = 100  # code points, as JSON Schema counts them


class RequestError(Exception):
    """The body does not match the contract. `detail` names properties, never values."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise RequestError('Duplicate property.')
    return dict(pairs)


def _is_valid_text(text: str) -> bool:
    """False for lone surrogates such as "\\ud800", which JSON can encode but UTF-8 cannot."""
    try:
        text.encode('utf-8')
    except UnicodeEncodeError:
        return False
    return True


def _safe_name(key: str) -> bool:
    return key.isascii() and key.isprintable() and len(key) <= 40


def parse_calculation_request(body: bytes) -> RawLoanInput:
    try:
        text = body.decode('utf-8')
    except UnicodeDecodeError:
        raise RequestError('Request body is not valid UTF-8.') from None
    try:
        # NaN/Infinity literals parse to floats, which the string check below rejects.
        data = json.loads(text, object_pairs_hook=_reject_duplicates)
    except ValueError:
        raise RequestError('Request body is not valid JSON.') from None

    if not isinstance(data, dict):
        raise RequestError('Request body must be a JSON object.')
    for key in data:
        if key not in FIELDS and key != EXTRA_PAYMENTS:
            raise RequestError(f'Unknown property: {key}' if _safe_name(key) else 'Unknown property.')

    raw: RawLoanInput = {'loanAmount': None, 'annualRate': None, 'termYears': None}
    for field in FIELDS:
        raw[field] = _raw_input(data.get(field), field)
    raw['extraPayments'] = _extra_payments(data.get(EXTRA_PAYMENTS))
    return raw


def _raw_input(value: object, name: str) -> str | None:
    """A RawInput: null, or a valid string of at most 100 characters (contract `RawInput`)."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise RequestError(f'Property {name} must be a string or null.')
    if not _is_valid_text(value):
        raise RequestError(f'Property {name} is not a valid string.')
    if len(value) > MAX_LENGTH:
        raise RequestError(f'Property {name} is longer than {MAX_LENGTH} characters.')
    return value


def _extra_payments(value: object) -> list[RawExtraPayment]:
    """04 §2: absent / null / [] = none; otherwise an array of at most 10 closed {month, amount} objects."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise RequestError(f'Property {EXTRA_PAYMENTS} must be an array or null.')
    if len(value) > MAX_EXTRA_PAYMENTS:
        raise RequestError(f'Property {EXTRA_PAYMENTS} has more than {MAX_EXTRA_PAYMENTS} items.')
    items: list[RawExtraPayment] = []
    for index, item in enumerate(value):
        where = f'{EXTRA_PAYMENTS}[{index}]'
        if not isinstance(item, dict):
            raise RequestError(f'Item {where} must be an object.')
        for key in item:
            if key not in ITEM_PROPERTIES:
                raise RequestError(f'Unknown property in {where}: {key}' if _safe_name(key) else f'Unknown property in {where}.')
        items.append({prop: _raw_input(item.get(prop), f'{where}.{prop}') for prop in ITEM_PROPERTIES})
    return items

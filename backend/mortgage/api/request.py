"""Strict reading of the CalculationRequest body (api/openapi.yaml `CalculationRequest`, `RawInput`).

Anything that is not exactly an object of the three optional string-or-null properties is a
malformed request (400). Whether the strings are valid input is decided later (422).
"""
import json

from mortgage.domain.types import Field, RawLoanInput

FIELDS: tuple[Field, ...] = ('loanAmount', 'annualRate', 'termYears')
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
        if key not in FIELDS:
            raise RequestError(f'Unknown property: {key}' if _safe_name(key) else 'Unknown property.')

    raw: RawLoanInput = {'loanAmount': None, 'annualRate': None, 'termYears': None}
    for field in FIELDS:
        value = data.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise RequestError(f'Property {field} must be a string or null.')
        if not _is_valid_text(value):
            raise RequestError(f'Property {field} is not a valid string.')
        if len(value) > MAX_LENGTH:
            raise RequestError(f'Property {field} is longer than {MAX_LENGTH} characters.')
        raw[field] = value
    return raw

"""M2 — Number parsing (docs/v1/02-architecture.md §3, M2; 01-functional.md §3.2), ported from legacy/cli.

Converts one raw text value into an exact decimal number.
"""
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

# Strict number grammar from 01 §3.2, applied after trimming and removing inner spaces.
# Used with fullmatch(): `$` would also match before a trailing newline. [0-9] is ASCII only (unlike \d).
NUMBER_PATTERN = re.compile(r'-?[0-9]+(?:[.,]([0-9]+))?')

# The characters JavaScript's String.prototype.trim() removes, so trimming matches V1 exactly.
# Python's str.strip() differs: it misses U+FEFF and also removes U+001C–U+001F and U+0085.
JS_WHITESPACE = (
    '\t\n\v\f\r          '
    '        　﻿'
)


@dataclass(frozen=True)
class Parsed:
    value: Decimal
    written_decimals: int  # decimal places as written by the user, e.g. "1000,500" → 3


@dataclass(frozen=True)
class ParseFailure:
    error: Literal['empty', 'not_a_number']


type ParseResult = Parsed | ParseFailure


def parse_number(raw: str | None) -> ParseResult:
    trimmed = (raw or '').strip(JS_WHITESPACE)
    if trimmed == '':
        return ParseFailure('empty')

    compact = trimmed.replace(' ', '')

    # Gatekeeper: Decimal() also accepts exponents, NaN, Infinity, underscores and non-ASCII digits,
    # so it must only ever see text that matches the V1 grammar.
    match = NUMBER_PATTERN.fullmatch(compact)
    if match is None:
        return ParseFailure('not_a_number')

    decimals = match.group(1)
    return Parsed(Decimal(compact.replace(',', '.')), len(decimals) if decimals else 0)

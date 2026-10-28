"""M2 — input/parsing (docs/v1/03-test-scenarios.md tests 1–16, 96–100), ported from V1 (legacy/cli; removed in Phase 8, see git tag v1-final)."""
from decimal import Decimal

import pytest

from mortgage.input.parsing import ParseFailure, Parsed, parse_number


def expect_number(raw: str, value: str, written_decimals: int | None = None) -> None:
    result = parse_number(raw)
    assert isinstance(result, Parsed), f'"{raw}" was rejected with {result}'
    assert result.value == Decimal(value), f'value of "{raw}" is {result.value}'
    if written_decimals is not None:
        assert result.written_decimals == written_decimals


def expect_error(raw: str | None, error: str) -> None:
    assert parse_number(raw) == ParseFailure(error), f'parse_number({raw!r})'


def test_parse_dot_decimal_separator():
    expect_number('1000.50', '1000.5', 2)


def test_parse_comma_decimal_separator():
    expect_number('1000,50', '1000.5', 2)


def test_parse_spaces_as_thousands_separator():
    expect_number('1 000 000,50', '1000000.5', 2)


def test_parse_integer_without_separator():
    expect_number('30', '30', 0)


def test_parse_trims_leading_trailing_whitespace():
    expect_number('  250000  ', '250000', 0)


def test_parse_counts_written_trailing_zeros():
    expect_number('1000,500', '1000.5', 3)


def test_parse_negative_number_is_parsed():
    expect_number('-5000', '-5000')


def test_parse_empty_string():
    expect_error('', 'empty')


def test_parse_whitespace_only():
    expect_error('   ', 'empty')


def test_parse_undefined_input():
    expect_error(None, 'empty')


def test_parse_text_string():
    expect_error('abc', 'not_a_number')


def test_parse_mixed_separators_rejected():
    expect_error('1,000.50', 'not_a_number')


def test_parse_multiple_dots_rejected():
    expect_error('1.000.50', 'not_a_number')


def test_parse_multiple_commas_rejected():
    expect_error('1,000,50', 'not_a_number')


def test_parse_currency_symbol_rejected():
    expect_error('1000 €', 'not_a_number')


def test_parse_scientific_notation_rejected():
    expect_error('1e5', 'not_a_number')


@pytest.mark.parametrize('raw', ['0x3E8', '0b1010', '0o17'])
def test_parse_hex_binary_octal_rejected(raw):
    expect_error(raw, 'not_a_number')


@pytest.mark.parametrize('raw', ['NaN', 'Infinity', '-Infinity'])
def test_parse_nan_and_infinity_rejected(raw):
    expect_error(raw, 'not_a_number')


@pytest.mark.parametrize('raw', ['1E5', '1e-2', '2,5e3'])
def test_parse_exponent_variants_rejected(raw):
    expect_error(raw, 'not_a_number')


@pytest.mark.parametrize('raw', ['1000,', ',50', '.5'])
def test_parse_separator_without_digits_rejected(raw):
    expect_error(raw, 'not_a_number')


@pytest.mark.parametrize('raw', ['+30', '−5000', '5000-'])
def test_parse_sign_other_than_leading_minus_rejected(raw):
    expect_error(raw, 'not_a_number')


# --- New in V2: Python-specific parity guards (not in V1 03) ---------------------------------


@pytest.mark.parametrize('raw', ['﻿30', '30　', ' 30\t'])
def test_parse_trims_the_javascript_whitespace_set(raw):
    """V1 trimmed with JS String.trim(); Python's str.strip() misses U+FEFF, so the set is explicit."""
    expect_number(raw, '30', 0)


@pytest.mark.parametrize('raw', ['\x1c30', '30\x85', '30\n5', '٣٠', '3 0'])
def test_parse_rejects_what_javascript_trim_and_ascii_digits_reject(raw):
    """str.strip() would remove U+001C and U+0085, `$` would allow a newline, and `\\d` would allow Arabic-Indic digits."""
    expect_error(raw, 'not_a_number')

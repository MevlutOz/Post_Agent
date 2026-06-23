import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from secim import parse_choice


def test_valid_choice_returns_zero_based_index():
    assert parse_choice("1", 15) == 0
    assert parse_choice("15", 15) == 14


def test_strips_whitespace():
    assert parse_choice("  3  ", 15) == 2


def test_empty_returns_none():
    assert parse_choice("", 15) is None
    assert parse_choice("   ", 15) is None


def test_non_digit_returns_none():
    assert parse_choice("abc", 15) is None
    assert parse_choice("2x", 15) is None


def test_out_of_range_returns_none():
    assert parse_choice("0", 15) is None
    assert parse_choice("16", 15) is None
    assert parse_choice("-1", 15) is None


def test_double_sign_returns_none():
    assert parse_choice("--3", 15) is None
    assert parse_choice("+-3", 15) is None

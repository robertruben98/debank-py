"""Regression tests: token integer fields must not lose precision.

DeBank returns ``raw_amount`` as the exact smallest-unit balance — an integer
that routinely exceeds float64's 2**53 exact-integer mantissa (e.g. a wei-scale
ERC-20 balance). Typing it as ``float`` silently rounds it; it must be ``int``.
``time_at`` is a Unix-seconds integer and is typed ``int`` for the same reason.
"""

from debank import Token


def test_raw_amount_round_trips_a_wei_scale_integer_exactly():
    # 1.5e18 + 1 wei: the trailing "1" is lost if coerced through float64.
    raw = 1_500_000_000_000_000_001
    token = Token.model_validate({"id": "0xabc", "raw_amount": raw})
    assert token.raw_amount == raw
    assert isinstance(token.raw_amount, int)


def test_large_raw_amount_is_preserved():
    raw = 21_709_487_132_565_774_000
    token = Token.model_validate({"id": "0xabc", "raw_amount": raw})
    assert token.raw_amount == raw


def test_time_at_is_an_integer():
    token = Token.model_validate({"id": "0xabc", "time_at": 1700000000})
    assert token.time_at == 1700000000
    assert isinstance(token.time_at, int)


def test_amount_remains_float_for_human_readable_balance():
    # `amount` is the decimal-adjusted balance and stays a float.
    token = Token.model_validate({"id": "0xabc", "amount": 1.5})
    assert token.amount == 1.5
    assert isinstance(token.amount, float)

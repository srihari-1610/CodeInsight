import math

import pytest

from core.complexity import ExpressionError, cross_check, estimate_ops, growth_exponent, growth_series, judge, safe_eval


def test_basic_evaluation():
    assert safe_eval("n * log2(n)", {"n": 1024}) == pytest.approx(10240)
    assert safe_eval("(n + m) * 2", {"n": 3, "m": 4}) == 14
    assert safe_eval("n^2", {"n": 10}) == 100


@pytest.mark.parametrize("expr", [
    "__import__('os').system('echo hi')", "open('x')", "n.real", "[1,2]", "lambda: 1",
    "n if n else 1", "log2(n, 2)", "unknown + 1", "",
])
def test_rejects_unsafe_or_invalid(expr):
    with pytest.raises(ExpressionError):
        safe_eval(expr, {"n": 5})


def test_overflow_becomes_infinity():
    assert math.isinf(estimate_ops("2 ** n", 10**6, 1, 1))


def test_growth_exponent():
    assert growth_exponent("n", 1000, 1, 1) == pytest.approx(1.0)
    assert growth_exponent("n * n / 2", 1000, 1, 1) == pytest.approx(2.0)
    assert 1.0 < growth_exponent("n * log2(n)", 100000, 1, 1) < 1.1
    assert growth_exponent("bad ++", 10, 1, 1) is None


def test_verdict_levels():
    assert judge(1e6, 1.0, "C++").level == "safe"
    assert judge(8e7, 1.0, "C++").level == "borderline"
    assert judge(5e9, 1.0, "C++").level == "tle"
    assert judge(2e7, 1.0, "Python").level == "tle"
    assert judge(math.inf, 1.0, "Java").level == "tle"


def test_cross_check_messages():
    assert cross_check(3, 1.0, False, 0) is not None
    assert cross_check(1, 3.0, False, 0) is not None
    assert cross_check(1, 3.0, True, 0) is None
    assert cross_check(2, 2.0, False, 0) is None
    assert cross_check(None, 2.0, False, 0) is None


def test_growth_series_monotonic():
    series = growth_series("(n + m) * log2(m + 2)", 1000, 2000, 1)
    assert len(series) == 40
    assert all(b[1] >= a[1] for a, b in zip(series, series[1:]))

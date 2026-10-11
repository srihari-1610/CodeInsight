"""Safe evaluation of the model's operation-count expression + a TLE-risk heuristic."""
from __future__ import annotations

import ast
import math
from dataclasses import dataclass

# Rough "simple operations per second" a judge can sustain (deliberately conservative).
OPS_PER_SECOND = {"Python": 1e7, "C++": 1e8, "Java": 5e7}

_FUNCS = {"log2": math.log2, "log": math.log, "log10": math.log10, "sqrt": math.sqrt}
_LOG_FUNCS = {"log2", "log", "log10", "sqrt"}


class ExpressionError(ValueError):
    """Raised when an operation-count expression is unsafe or cannot be evaluated."""


def _eval(node: ast.AST, env: dict[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in env:
            return float(env[node.id])
        raise ExpressionError(f"unknown variable '{node.id}'")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        val = _eval(node.operand, env)
        return -val if isinstance(node.op, ast.USub) else val
    if isinstance(node, ast.BinOp):
        left, right = _eval(node.left, env), _eval(node.right, env)
        op = type(node.op)
        if op is ast.Add:
            return left + right
        if op is ast.Sub:
            return left - right
        if op is ast.Mult:
            return left * right
        if op is ast.Div:
            if right == 0:
                raise ExpressionError("division by zero")
            return left / right
        if op is ast.Pow:
            try:
                result = left**right
            except OverflowError:
                return math.inf
            except ZeroDivisionError as exc:
                raise ExpressionError("division by zero") from exc
            if isinstance(result, complex):
                raise ExpressionError("complex result")
            return float(result)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCS
        and len(node.args) == 1
        and not node.keywords
    ):
        arg = _eval(node.args[0], env)
        if node.func.id in _LOG_FUNCS and arg <= 0 and node.func.id != "sqrt":
            raise ExpressionError("log of a non-positive number")
        if node.func.id == "sqrt" and arg < 0:
            raise ExpressionError("sqrt of a negative number")
        return float(_FUNCS[node.func.id](arg))
    raise ExpressionError("unsupported syntax in expression")


def safe_eval(expr: str, env: dict[str, float]) -> float:
    if not expr or len(expr) > 200:
        raise ExpressionError("empty or too long expression")
    try:
        tree = ast.parse(expr.replace("^", "**").strip(), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"cannot parse expression: {exc.msg}") from exc
    return float(_eval(tree.body, env))


def estimate_ops(expr: str, n: float, m: float, k: float) -> float:
    return safe_eval(expr, {"n": n, "m": m, "k": k})


def growth_exponent(expr: str, n: float, m: float, k: float) -> float | None:
    """Empirical polynomial exponent: log2(f(2x) / f(x)). ~1 linear, ~2 quadratic."""
    try:
        f1 = estimate_ops(expr, n, m, k)
        f2 = estimate_ops(expr, 2 * n, 2 * m, 2 * k)
    except ExpressionError:
        return None
    if not (math.isfinite(f1) and math.isfinite(f2)) or f1 <= 0 or f2 <= 0:
        return None
    return math.log2(f2 / f1)


@dataclass(frozen=True)
class Verdict:
    level: str  # "safe" | "borderline" | "tle"
    ratio: float
    ops: float
    budget: float
    ops_per_sec: float

    @property
    def label(self) -> str:
        return {"safe": "Safe", "borderline": "Borderline", "tle": "Likely TLE"}[self.level]


def judge(ops: float, time_limit_s: float, language: str) -> Verdict:
    rate = OPS_PER_SECOND.get(language, 1e8)
    budget = max(time_limit_s, 1e-9) * rate
    ratio = math.inf if math.isinf(ops) else ops / budget
    level = "safe" if ratio <= 0.35 else "borderline" if ratio <= 1.0 else "tle"
    return Verdict(level=level, ratio=ratio, ops=ops, budget=budget, ops_per_sec=rate)


def format_number(x: float) -> str:
    if math.isinf(x):
        return "∞"
    if x >= 1e4:
        return f"{x:.2e}"
    return f"{x:,.0f}"


def cross_check(loop_depth: int | None, exponent: float | None, has_recursion: bool, sort_calls: int) -> str | None:
    """Compare static loop nesting with the exponent implied by the model's expression."""
    if loop_depth is None or exponent is None:
        return None
    if loop_depth >= exponent + 1.5:
        return (
            f"Static analysis finds loop nesting depth {loop_depth}, but the reported complexity grows like "
            f"n^{exponent:.1f}. Verify that the inner loops really are bounded (e.g. two pointers, amortised work)."
        )
    if exponent >= loop_depth + 1.5 and not has_recursion and sort_calls == 0:
        return (
            f"The reported complexity grows like n^{exponent:.1f} but loop nesting is only {loop_depth} with no "
            "recursion or sorting. Check for hidden costs (library calls, string copies) or an over-estimate."
        )
    return None


def growth_series(expr: str, n: float, m: float, k: float, points: int = 40) -> list[tuple[float, float]]:
    """(input size, operations) pairs on a log grid, scaling m and k proportionally with n."""
    hi = max(n * 10, 100.0)
    out: list[tuple[float, float]] = []
    for i in range(points):
        x = 10 ** (1 + i * (math.log10(hi) - 1) / (points - 1))
        scale = x / max(n, 1.0)
        try:
            ops = estimate_ops(expr, x, m * scale, k * scale)
        except ExpressionError:
            return []
        if math.isfinite(ops) and ops > 0:
            out.append((x, ops))
    return out

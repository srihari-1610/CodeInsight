"""Local, no-AI static checks used to cross-validate the model's complexity claim.

Python is analysed with `ast`; C++/Java with a small brace/paren scanner. These are
heuristics (loop nesting depth, recursion, sort calls, slow-I/O patterns), not proofs.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field


@dataclass
class StaticReport:
    language: str
    loop_depth: int | None = None
    recursive_functions: list[str] = field(default_factory=list)
    sort_calls: int = 0
    notes: list[str] = field(default_factory=list)
    parse_error: str | None = None


# ------------------------------------------------------------------ Python
def _py_loop_depth(node: ast.AST, depth: int = 0) -> int:
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
            best = max(best, _py_loop_depth(child, depth + 1))
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            best = max(best, _py_loop_depth(child, depth + len(child.generators)))
        else:
            best = max(best, _py_loop_depth(child, depth))
    return best


def _py_recursive_functions(tree: ast.AST) -> list[str]:
    found: set[str] = set()
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(fn):
            if not isinstance(call, ast.Call):
                continue
            f = call.func
            direct = isinstance(f, ast.Name) and f.id == fn.name
            method = (
                isinstance(f, ast.Attribute)
                and f.attr == fn.name
                and isinstance(f.value, ast.Name)
                and f.value.id in {"self", "cls"}
            )
            if direct or method:
                found.add(fn.name)
                break
    return sorted(found)


def _py_input_in_loop(tree: ast.AST) -> bool:
    def has_input(nodes) -> bool:
        for n in nodes:
            for sub in ast.walk(n):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == "input":
                    return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)) and has_input(node.body):
            return True
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and has_input([node.elt]):
            return True
        if isinstance(node, ast.DictComp) and has_input([node.value]):
            return True
    return False


def _analyze_python(code: str) -> StaticReport:
    rep = StaticReport(language="Python")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        rep.parse_error = f"line {exc.lineno}: {exc.msg}"
        return rep
    rep.loop_depth = _py_loop_depth(tree)
    rep.recursive_functions = _py_recursive_functions(tree)
    rep.sort_calls = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and (
            (isinstance(n.func, ast.Name) and n.func.id == "sorted")
            or (isinstance(n.func, ast.Attribute) and n.func.attr == "sort")
        )
    )
    if _py_input_in_loop(tree):
        rep.notes.append("input() inside a loop is slow for large inputs; read via sys.stdin instead.")
    if rep.recursive_functions and "setrecursionlimit" not in code:
        rep.notes.append(
            f"Recursive function(s) {', '.join(rep.recursive_functions)}: Python's default recursion "
            "limit is ~1000; raise it or convert to iteration for deep inputs."
        )
    return rep


# ------------------------------------------------------------------ C++ / Java
_C_NOISE = re.compile(
    r"//[^\n]*"
    r"|/\*.*?\*/"
    r'|"(?:\\.|[^"\\\n])*"'
    r"|'(?:\\.|[^'\\\n])*'",
    re.DOTALL,
)
_FUNC_DEF = re.compile(
    r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:const|noexcept|override|final|throws\s+[\w.,\s]+)?\s*\{"
)
_NOT_FUNCS = {"if", "for", "while", "switch", "catch", "return", "sizeof", "else", "do", "synchronized"}


def _strip_c_like(src: str) -> str:
    """Blank out comments and string/char literals, keeping line structure."""
    return _C_NOISE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), src)


def c_like_loop_depth(src: str) -> int:
    """Maximum loop nesting depth for brace languages (handles braceless loops and do-while)."""
    code = _strip_c_like(src)
    n = len(code)
    i = 0
    paren = 0
    stack: list[int] = []  # loops contributed by each open '{'
    current = 0
    max_depth = 0
    pending = 0  # loop headers closed, body not yet started
    pending_paren = 0
    header_at: int | None = None  # paren level where a for/while header began

    while i < n:
        ch = code[i]
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1
            word = code[i:j]
            if word in ("for", "while") and header_at is None:
                header_at = paren
            elif word == "do":
                pending += 1
                pending_paren = paren
            i = j
            continue
        if ch == "(":
            paren += 1
        elif ch == ")":
            paren = max(0, paren - 1)
            if header_at is not None and paren == header_at:
                header_at = None
                k = i + 1
                while k < n and code[k].isspace():
                    k += 1
                # `while (...) ;` is a do-while tail (or an empty-body loop): not a new level
                if not (k < n and code[k] == ";"):
                    pending += 1
                    pending_paren = paren
        elif ch == "{":
            if pending and paren == pending_paren:
                stack.append(pending)
                current += pending
                max_depth = max(max_depth, current)
                pending = 0
            else:
                stack.append(0)
        elif ch == "}":
            if stack:
                current -= stack.pop()
        elif ch == ";" and pending and paren == pending_paren:
            max_depth = max(max_depth, current + pending)
            pending = 0
        i += 1
    return max_depth


def _matching_body(code: str, open_idx: int) -> str:
    depth = 0
    for idx in range(open_idx, len(code)):
        if code[idx] == "{":
            depth += 1
        elif code[idx] == "}":
            depth -= 1
            if depth == 0:
                return code[open_idx + 1 : idx]
    return code[open_idx + 1 :]


def _c_like_recursive_functions(src: str) -> list[str]:
    code = _strip_c_like(src)
    found: set[str] = set()
    for m in _FUNC_DEF.finditer(code):
        name = m.group(1)
        if name in _NOT_FUNCS:
            continue
        body = _matching_body(code, m.end() - 1)
        if re.search(rf"\b{re.escape(name)}\s*\(", body):
            found.add(name)
    return sorted(found)


def _analyze_c_like(code: str, language: str) -> StaticReport:
    rep = StaticReport(language=language)
    stripped = _strip_c_like(code)
    rep.loop_depth = c_like_loop_depth(code)
    rep.recursive_functions = _c_like_recursive_functions(code)
    rep.sort_calls = len(re.findall(r"\bsort\s*\(|Arrays\.sort\s*\(|Collections\.sort\s*\(", stripped))

    if language == "C++":
        if rep.loop_depth >= 1 and re.search(r"\bendl\b", stripped):
            rep.notes.append("std::endl flushes on every use; prefer '\\n' in output-heavy loops.")
        if re.search(r"\bcin\b", stripped) and "sync_with_stdio" not in stripped:
            rep.notes.append("Add ios::sync_with_stdio(false); cin.tie(nullptr); for fast input with cin.")
    else:  # Java
        if re.search(r"new\s+Scanner\s*\(", stripped):
            rep.notes.append("Scanner is slow for large inputs; use BufferedReader or StreamTokenizer.")
        if rep.loop_depth >= 1 and re.search(r"System\.out\.print", stripped):
            rep.notes.append("Many System.out calls are slow; collect output in a StringBuilder/PrintWriter.")
    return rep


# ------------------------------------------------------------------ public API
def analyze_static(code: str, language: str) -> StaticReport:
    rep = _analyze_python(code) if language == "Python" else _analyze_c_like(code, language)
    if rep.loop_depth is not None and rep.loop_depth >= 3:
        rep.notes.append(
            f"Loop nesting depth is {rep.loop_depth}: confirm inner-loop bounds or expect up to O(n^{rep.loop_depth})."
        )
    return rep

"""Input validation and light language detection (the code is never executed)."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

SUPPORTED_LANGUAGES = ["Python", "C++", "Java"]


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def detect_language(code: str) -> str | None:
    """Best-effort guess; returns None when the signal is weak."""
    scores = {lang: 0 for lang in SUPPORTED_LANGUAGES}
    if re.search(r"#\s*include\s*[<\"]", code):
        scores["C++"] += 3
    if "using namespace" in code:
        scores["C++"] += 2
    if re.search(r"\b(cin|cout|scanf|printf)\b|vector\s*<", code):
        scores["C++"] += 2
    if re.search(r"\bpublic\s+(final\s+)?class\b|\bSystem\.out\b|\bimport\s+java\.", code):
        scores["Java"] += 3
    if re.search(r"static\s+void\s+main", code):
        scores["Java"] += 2
    if re.search(r"^\s*def\s+\w+\s*\(.*\)\s*(->.*)?:", code, re.M):
        scores["Python"] += 3
    if re.search(r"^\s*(import|from)\s+\w+", code, re.M) and ";" not in code:
        scores["Python"] += 1
    if re.search(r"\bprint\s*\(|\binput\s*\(|\belif\b|\brange\s*\(", code) and ";" not in code:
        scores["Python"] += 2
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None


def validate_submission(code: str, language: str, max_chars: int, max_lines: int) -> ValidationResult:
    res = ValidationResult()
    if not code.strip():
        res.errors.append("Paste some code first.")
    elif len(code) > max_chars:
        res.errors.append(f"Code is too long ({len(code):,} chars). Limit is {max_chars:,}.")
    elif code.count("\n") + 1 > max_lines:
        res.errors.append(f"Code has too many lines. Limit is {max_lines}.")

    if res.ok:
        guess = detect_language(code)
        if guess and guess != language:
            res.warnings.append(f"The code looks like {guess} but {language} is selected.")
        if language == "Python":
            try:
                ast.parse(code)
            except SyntaxError as exc:
                res.warnings.append(
                    f"Python syntax error on line {exc.lineno}: {exc.msg}. The analysis may be unreliable."
                )
    return res

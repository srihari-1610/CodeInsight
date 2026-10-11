"""Central configuration: environment variables, Streamlit secrets and defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    db_path: Path
    max_code_chars: int = 12_000
    max_code_lines: int = 400
    request_timeout: float = 90.0

    @property
    def gemini_api_key(self) -> str:
        return self.api_key

    @property
    def gemini_model(self) -> str:
        return self.model


def _streamlit_secret(name: str) -> str | None:
    """Read a key from Streamlit secrets if configured."""

    try:
        import streamlit as st

        value = st.secrets.get(name)
        return str(value) if value else None
    except Exception:
        return None


def load_settings() -> Settings:
    """Load configuration from environment variables and defaults."""

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or _streamlit_secret("GEMINI_API_KEY")
        or ""
    )

    model = os.getenv("CODEINSIGHT_MODEL") or DEFAULT_MODEL

    db_path = Path(
        os.getenv("CODEINSIGHT_DB")
        or BASE_DIR / "data" / "history.db"
    )

    return Settings(
        api_key=api_key.strip(),
        model=model.strip(),
        db_path=db_path,
    )


settings = load_settings()
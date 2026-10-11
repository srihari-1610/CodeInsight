"""SQLite persistence for past analyses (also acts as a cache keyed by request hash)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    language     TEXT NOT NULL,
    title        TEXT NOT NULL,
    model        TEXT NOT NULL,
    mode         TEXT NOT NULL,
    payload      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analyses_hash ON analyses(request_hash);
"""


class HistoryStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._conn()) as conn, conn:
            conn.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["payload"] = json.loads(d["payload"])
        return d

    def save(self, *, request_hash: str, language: str, title: str, model: str, mode: str, payload: dict) -> int:
        with closing(self._conn()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO analyses (created_at, request_hash, language, title, model, mode, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), request_hash, language, title, model, mode,
                 json.dumps(payload)),
            )
            return int(cur.lastrowid)

    def find_by_hash(self, request_hash: str) -> dict[str, Any] | None:
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM analyses WHERE request_hash = ? ORDER BY id DESC LIMIT 1", (request_hash,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def get(self, analysis_id: int) -> dict[str, Any] | None:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT id, created_at, language, title, mode FROM analyses ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, analysis_id: int) -> None:
        with closing(self._conn()) as conn, conn:
            conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))

    def clear(self) -> None:
        with closing(self._conn()) as conn, conn:
            conn.execute("DELETE FROM analyses")

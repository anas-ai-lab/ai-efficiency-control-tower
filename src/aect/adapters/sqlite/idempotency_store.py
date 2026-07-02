"""SQLiteIdempotencyStore -- implementiert IdempotencyStorePort mit SQLite.

Persistenz-Strategie: einfache Key-Value-Tabelle (Idempotency-Key -> Case-ID).
created_at als Audit-Trail (aect-security-checklist v2.1: Audit-Trail
append-only -- wer/wann ist hier "welcher Key wann zuletzt verwendet").

Hinweis: SQLiteIdempotencyStore wird in get_idempotency_store() pro Request
erzeugt -- _init_db() laeuft damit pro Request (idempotent, analog
SQLiteRepository). Nutzt dieselbe DB-Datei wie SQLiteRepository, eigene
Tabelle -- kein Konflikt (separate Connections, separate CREATE TABLE).
"""

from __future__ import annotations

from pathlib import Path

from aect.adapters.sqlite.connection import connect

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key        TEXT PRIMARY KEY,
    case_id    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


class SQLiteIdempotencyStore:
    """SQLite-Backend fuer Idempotency-Key -> Case-ID.

    Jede DB-Operation oeffnet eine eigene, kurzlebige Verbindung ueber
    connection.connect() (WAL, busy_timeout=5000, explizites close) --
    kein geteilter State, analog SQLiteRepository.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with connect(self._db_path) as conn:
            conn.execute(_CREATE_TABLE_SQL)

    def get(self, key: str) -> str | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT case_id FROM idempotency_keys WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return str(row[0])

    def set(self, key: str, case_id: str) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO idempotency_keys (key, case_id) VALUES (?, ?)",
                (key, case_id),
            )

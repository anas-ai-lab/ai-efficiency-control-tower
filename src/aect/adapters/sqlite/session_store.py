"""SQLiteSessionStore -- implementiert SessionStorePort mit SQLite.

Persistenz-Strategie: eine schmale Tabelle admin_sessions (token_hash -> Zeiten).
Nur der sha256-Hash des Tokens wird gespeichert, nie das Klartext-Token.
Zeitstempel als ISO-8601-Strings (konsistent mit SQLiteRepository.submitted_at).

Nutzt dieselbe DB-Datei wie SQLiteRepository, eigene Tabelle -- kein Konflikt
(separate Connections, separate CREATE TABLE, analog SQLiteIdempotencyStore).
Jede Operation oeffnet eine eigene kurzlebige Verbindung ueber connect()
(WAL, busy_timeout, explizites close).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aect.adapters.sqlite.connection import connect
from aect.application.ports.session_store import AdminSession

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admin_sessions (
    token_hash TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
)
"""


class SQLiteSessionStore:
    """SQLite-Backend fuer Admin-Sessions (token_hash -> created_at/expires_at)."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with connect(self._db_path) as conn:
            conn.execute(_CREATE_TABLE_SQL)

    def create(self, session: AdminSession) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO admin_sessions "
                "(token_hash, created_at, expires_at) VALUES (?, ?, ?)",
                (
                    session.token_hash,
                    session.created_at.isoformat(),
                    session.expires_at.isoformat(),
                ),
            )

    def get(self, token_hash: str) -> AdminSession | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT token_hash, created_at, expires_at "
                "FROM admin_sessions WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
        if row is None:
            return None
        return AdminSession(
            token_hash=str(row[0]),
            created_at=datetime.fromisoformat(str(row[1])),
            expires_at=datetime.fromisoformat(str(row[2])),
        )

    def delete(self, token_hash: str) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "DELETE FROM admin_sessions WHERE token_hash = ?",
                (token_hash,),
            )

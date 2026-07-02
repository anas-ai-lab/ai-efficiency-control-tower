"""Gemeinsame SQLite-Verbindungs-Hygiene fuer alle SQLite-Adapter (F-012/F-013).

Warum ein eigener Context Manager statt `with sqlite3.connect(...)`:
  sqlite3.Connection als Context Manager steuert nur die Transaktion
  (Commit/Rollback), schliesst die Verbindung aber NICHT -- das Schliessen
  hing bisher am CPython-Refcount. Dieser Helper garantiert close() im
  finally-Block und setzt pro Verbindung:

  PRAGMA journal_mode=WAL   -- Leser blockieren Schreiber nicht (persistiert
                               in der DB-Datei, Setzen ist idempotent).
  PRAGMA busy_timeout=5000  -- bei gesperrter DB bis zu 5 s warten statt
                               sofort "database is locked" zu werfen.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_BUSY_TIMEOUT_MS = 5000


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Oeffnet eine kurzlebige Verbindung: WAL + busy_timeout, commit, close.

    Innerhalb des with-Blocks gelten die ueblichen Transaktions-Semantiken
    (Commit bei Erfolg, Rollback bei Exception); danach wird die Verbindung
    in jedem Fall geschlossen.
    """
    conn = sqlite3.connect(str(db_path), timeout=_BUSY_TIMEOUT_MS / 1000)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        with conn:
            yield conn
    finally:
        conn.close()

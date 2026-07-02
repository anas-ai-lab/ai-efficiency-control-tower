"""Tests fuer connection.connect() -- SQLite-Verbindungs-Hygiene (F-012/F-013)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aect.adapters.sqlite.connection import connect


def test_connect_sets_wal_mode(tmp_path: Path) -> None:
    """WAL wird gesetzt und persistiert in der DB-Datei."""
    db_path = tmp_path / "wal.db"
    with connect(db_path) as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")

    # Frische, unabhaengige Verbindung sieht den persistierten Modus.
    raw = sqlite3.connect(str(db_path))
    try:
        mode = raw.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        raw.close()
    assert mode == "wal"


def test_connect_sets_busy_timeout(tmp_path: Path) -> None:
    db_path = tmp_path / "busy.db"
    with connect(db_path) as conn:
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    assert timeout == 5000


def test_connect_closes_connection_after_block(tmp_path: Path) -> None:
    """Nach dem with-Block ist die Verbindung geschlossen, nicht nur committed."""
    db_path = tmp_path / "closed.db"
    with connect(db_path) as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_connect_commits_on_success_and_rolls_back_on_error(tmp_path: Path) -> None:
    db_path = tmp_path / "tx.db"
    with connect(db_path) as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")

    with pytest.raises(RuntimeError), connect(db_path) as conn:
        conn.execute("INSERT INTO t VALUES (2)")
        raise RuntimeError("abbruch")

    with connect(db_path) as conn:
        rows = conn.execute("SELECT x FROM t").fetchall()
    assert rows == [(1,)]

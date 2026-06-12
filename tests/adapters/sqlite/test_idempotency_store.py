"""Unit-Tests fuer SQLiteIdempotencyStore."""

from __future__ import annotations

from pathlib import Path

from aect.adapters.sqlite.idempotency_store import SQLiteIdempotencyStore


def test_unknown_key_returns_none(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    assert store.get("missing") is None


def test_set_then_get_returns_case_id(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    store.set("key-1", "case-123")
    assert store.get("key-1") == "case-123"


def test_set_overwrites_existing_key(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    store.set("key-1", "case-123")
    store.set("key-1", "case-456")
    assert store.get("key-1") == "case-456"


def test_persists_across_instances(tmp_path: Path) -> None:
    """Neue Instanz auf gleicher DB-Datei sieht denselben Stand (Persistenz)."""
    db_path = tmp_path / "idempotency.db"
    SQLiteIdempotencyStore(db_path).set("key-1", "case-123")
    reopened = SQLiteIdempotencyStore(db_path)
    assert reopened.get("key-1") == "case-123"

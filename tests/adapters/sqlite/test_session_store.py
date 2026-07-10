"""Tests fuer SQLiteSessionStore (V4-P-Auth) -- Persistenz der Admin-Sessions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from aect.adapters.sqlite.session_store import SQLiteSessionStore
from aect.application.ports.session_store import AdminSession


def _session(token_hash: str = "abc123") -> AdminSession:
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=UTC)
    return AdminSession(
        token_hash=token_hash,
        created_at=now,
        expires_at=now + timedelta(hours=12),
    )


def test_create_and_get_roundtrip(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "aect.db")
    session = _session()
    store.create(session)
    fetched = store.get(session.token_hash)
    assert fetched is not None
    assert fetched.token_hash == session.token_hash
    assert fetched.created_at == session.created_at
    assert fetched.expires_at == session.expires_at


def test_get_missing_returns_none(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "aect.db")
    assert store.get("does-not-exist") is None


def test_delete_removes_session(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "aect.db")
    session = _session()
    store.create(session)
    store.delete(session.token_hash)
    assert store.get(session.token_hash) is None


def test_delete_missing_is_noop(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "aect.db")
    store.delete("nichts")  # kein Raise


def test_persists_across_instances(tmp_path: Path) -> None:
    db = tmp_path / "aect.db"
    session = _session()
    SQLiteSessionStore(db).create(session)
    # Neue Instanz auf derselben Datei sieht die Session (Neustart-Simulation).
    fetched = SQLiteSessionStore(db).get(session.token_hash)
    assert fetched is not None
    assert fetched.token_hash == session.token_hash


def test_create_replaces_same_token_hash(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "aect.db")
    store.create(_session())
    later = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    store.create(
        AdminSession(
            token_hash="abc123",
            created_at=later,
            expires_at=later + timedelta(hours=12),
        )
    )
    fetched = store.get("abc123")
    assert fetched is not None
    assert fetched.created_at == later

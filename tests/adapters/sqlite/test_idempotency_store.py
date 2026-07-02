"""Unit-Tests fuer SQLiteIdempotencyStore."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
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


# ---------------------------------------------------------------------------
# F-010: claim/release (Claim-then-fill)
# ---------------------------------------------------------------------------


def test_claim_free_key_reserves_it(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    claimed, existing = store.claim("key-1")
    assert claimed is True
    assert existing is None
    # Platzhalter ist keine fertige Zuordnung.
    assert store.get("key-1") is None


def test_claim_filled_key_returns_case_id(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    store.set("key-1", "case-123")
    claimed, existing = store.claim("key-1")
    assert claimed is False
    assert existing == "case-123"


def test_claim_in_flight_key_returns_no_case_id(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    store.claim("key-1")
    claimed, existing = store.claim("key-1")
    assert claimed is False
    assert existing is None


def test_release_frees_placeholder_but_not_filled_entry(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    store.claim("key-1")
    store.release("key-1")
    claimed, _ = store.claim("key-1")
    assert claimed is True  # wieder frei

    store.set("key-2", "case-123")
    store.release("key-2")  # No-op auf gefuelltem Eintrag
    assert store.get("key-2") == "case-123"


def test_claim_is_atomic_under_parallel_access(tmp_path: Path) -> None:
    """Genau EIN Thread gewinnt den claim() -- die INSERT-ON-CONFLICT-Pruefung
    ist atomar. Mit get -> set (alter Codepfad) gewannen regelmaessig mehrere."""
    store = SQLiteIdempotencyStore(tmp_path / "idempotency.db")
    barrier = threading.Barrier(8)

    def try_claim() -> bool:
        barrier.wait(timeout=5)
        claimed, _ = store.claim("key-race")
        return claimed

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: try_claim(), range(8)))

    assert sum(results) == 1

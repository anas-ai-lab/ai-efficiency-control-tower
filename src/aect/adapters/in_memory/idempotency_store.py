"""InMemoryIdempotencyStore -- implementiert IdempotencyStorePort mit einem dict."""

from __future__ import annotations


class InMemoryIdempotencyStore:
    """In-Memory-dict als Idempotency-Key-Speicher.

    Lebensdauer: Prozess-gebunden -- kein State nach Neustart.
    Zweck: Entwicklung, Tests, Baseline vor SQLiteIdempotencyStore.

    Security: kein Locking -- Single-Thread-Only (analog InMemoryRepository).
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, case_id: str) -> None:
        self._store[key] = case_id

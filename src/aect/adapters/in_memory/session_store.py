"""InMemorySessionStore -- implementiert SessionStorePort mit einem dict."""

from __future__ import annotations

from aect.application.ports.session_store import AdminSession


class InMemorySessionStore:
    """In-Memory-dict als Admin-Session-Speicher (token_hash -> AdminSession).

    Lebensdauer: Prozess-gebunden -- kein State nach Neustart (analog
    InMemoryIdempotencyStore). Fuer Dev/Test und den lokalen Demo-Betrieb ohne
    AECT_DB_PATH. Security: kein Locking -- Single-Thread-Only.
    """

    def __init__(self) -> None:
        self._store: dict[str, AdminSession] = {}

    def create(self, session: AdminSession) -> None:
        self._store[session.token_hash] = session

    def get(self, token_hash: str) -> AdminSession | None:
        return self._store.get(token_hash)

    def delete(self, token_hash: str) -> None:
        self._store.pop(token_hash, None)

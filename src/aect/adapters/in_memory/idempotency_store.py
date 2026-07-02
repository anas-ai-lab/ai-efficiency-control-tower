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

    # Platzhalter-Wert fuer claim() ohne set() (F-010): leere case_id,
    # dasselbe Encoding wie in SQLiteIdempotencyStore.
    def get(self, key: str) -> str | None:
        case_id = self._store.get(key)
        if not case_id:
            return None
        return case_id

    def set(self, key: str, case_id: str) -> None:
        self._store[key] = case_id

    def claim(self, key: str) -> tuple[bool, str | None]:
        """Reserviert den Key atomar (F-010). Kein Lock noetig: der Aufrufer
        (Route) ist synchroner Code ohne await -- auf dem Event-Loop
        unteilbar, analog zur GIL-Atomizitaet einzelner dict-Zugriffe."""
        if key in self._store:
            case_id = self._store[key]
            return (False, case_id if case_id else None)
        self._store[key] = ""
        return (True, None)

    def release(self, key: str) -> None:
        if self._store.get(key) == "":
            del self._store[key]

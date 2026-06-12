"""IdempotencyStorePort -- Persistenz-Abstraktion fuer Idempotency-Keys.

Bildet ab: Idempotency-Key (Client-generiert, z. B. UUID) -> Case-ID
(Server-generiert, von TriageService.submit_use_case()).

Der Application Service kennt dieses Interface nicht -- die Idempotency-
Pruefung findet in der Adapter-Schicht (adapters/api/routes/triage.py)
statt, bevor der Service aufgerufen wird. Grund: Idempotency ist ein
HTTP-/Transport-Anliegen, keine Domain- oder Anwendungslogik.
"""

from __future__ import annotations

from typing import Protocol


class IdempotencyStorePort(Protocol):
    """Speichert und liest die Zuordnung Idempotency-Key -> Case-ID.

    Aktuelle Impl.: InMemoryIdempotencyStore (Dev/Test),
    SQLiteIdempotencyStore (persistent, Phase B).
    """

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, case_id: str) -> None: ...

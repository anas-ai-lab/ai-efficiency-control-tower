"""IdempotencyStorePort -- Persistenz-Abstraktion fuer Idempotency-Keys.

Bildet ab: Idempotency-Key (Client-generiert, z. B. UUID) -> Case-ID
(Server-generiert, von TriageService.submit_use_case()).

Der Application Service kennt dieses Interface nicht -- die Idempotency-
Pruefung findet in der Adapter-Schicht (adapters/api/routes/triage.py)
statt, bevor der Service aufgerufen wird. Grund: Idempotency ist ein
HTTP-/Transport-Anliegen, keine Domain- oder Anwendungslogik.

Claim-then-fill (F-010): das fruehere get -> verarbeiten -> set war nicht
atomar -- zwei parallele Requests mit demselben Key lasen beide "kein
Eintrag" und verarbeiteten beide. claim() reserviert den Key atomar mit
einem Platzhalter (leere case_id), BEVOR verarbeitet wird; set() fuellt
den Platzhalter danach mit der echten Case-ID. release() raeumt den
Platzhalter auf, wenn die Verarbeitung fehlschlaegt.
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

    def claim(self, key: str) -> tuple[bool, str | None]:
        """Reserviert den Key atomar (F-010).

        Returns:
            (True, None)       -- Key war frei und ist jetzt reserviert; der
                                  Aufrufer verarbeitet und ruft danach set().
            (False, case_id)   -- Key ist bereits mit einer Case-ID gefuellt
                                  (Replay-Kandidat).
            (False, None)      -- Key ist reserviert, aber noch ungefuellt:
                                  ein paralleler Request verarbeitet gerade.
        """
        ...

    def release(self, key: str) -> None:
        """Gibt einen reservierten, noch ungefuellten Key wieder frei.

        No-op, wenn der Key fehlt oder bereits gefuellt ist -- ein Replay
        darf durch einen fehlgeschlagenen Parallel-Request nicht verloren
        gehen.
        """
        ...

"""RepositoryPort -- Persistenz-Abstraktion fuer SubmittedCase."""

from __future__ import annotations

from typing import Protocol

from aect.application.models import SubmittedCase


class RepositoryPort(Protocol):
    """Speichert und liest SubmittedCase-Objekte.

    Der Application Service kennt nur dieses Interface, nie die Implementierung.
    Aktuelle Impl.: InMemoryRepository. Naechste: SQLiteRepository (Phase B).
    """

    def save(self, case: SubmittedCase) -> None: ...
    def get(self, case_id: str) -> SubmittedCase | None: ...
    def list_all(self) -> list[SubmittedCase]: ...

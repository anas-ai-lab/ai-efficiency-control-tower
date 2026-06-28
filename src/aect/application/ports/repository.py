"""RepositoryPort -- Persistenz-Abstraktion fuer SubmittedCase."""

from __future__ import annotations

from typing import Protocol

from aect.application.models import SubmittedCase


class RepositoryPort(Protocol):
    """Speichert und liest SubmittedCase-Objekte.

    Der Application Service kennt nur dieses Interface, nie die Implementierung.
    Impl.: InMemoryRepository (Tests) + SQLiteRepository (Phase B).

    Sync- und async-Varianten (AUDIT-001, ADR-0037): Die sync-Methoden bleiben
    der Vertrag fuer synchrone Aufrufer. Die *_async-Varianten kapseln die
    blockierende I/O via asyncio.to_thread, damit sie aus async-Service-Methoden
    (sharpen_case/propose_solution/generate_compliance_hints) den Event-Loop
    nicht blockieren.
    """

    def save(self, case: SubmittedCase) -> None: ...
    def get(self, case_id: str) -> SubmittedCase | None: ...
    def list_all(self) -> list[SubmittedCase]: ...

    async def save_async(self, case: SubmittedCase) -> None: ...
    async def get_async(self, case_id: str) -> SubmittedCase | None: ...
    async def list_all_async(self) -> list[SubmittedCase]: ...

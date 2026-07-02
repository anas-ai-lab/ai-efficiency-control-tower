"""RepositoryPort -- Persistenz-Abstraktion fuer SubmittedCase."""

from __future__ import annotations

from typing import Literal, Protocol

from aect.application.models import SubmittedCase

# Nachtraeglich befuellbare Einzelfelder eines SubmittedCase (F-011).
# embedding wird als JSON-String uebergeben (dasselbe Format wie die Spalte
# in SQLite) -- der jeweilige Adapter dekodiert bei Bedarf.
CaseUpdateField = Literal[
    "sharpened_content_json",
    "proposal_text",
    "compliance_hints_json",
    "embedding",
]


class RepositoryPort(Protocol):
    """Speichert und liest SubmittedCase-Objekte.

    Der Application Service kennt nur dieses Interface, nie die Implementierung.
    Impl.: InMemoryRepository (Tests) + SQLiteRepository (Phase B).

    Sync- und async-Varianten (AUDIT-001, ADR-0037): Die sync-Methoden bleiben
    der Vertrag fuer synchrone Aufrufer. Die *_async-Varianten kapseln die
    blockierende I/O via asyncio.to_thread, damit sie aus async-Service-Methoden
    (sharpen_case/propose_solution/generate_compliance_hints) den Event-Loop
    nicht blockieren.

    update_field / update_field_async (F-011): schreibt genau EIN nachgelagert
    befuelltes Feld, statt den ganzen Case per save() zu ersetzen. Parallele
    LLM-Operationen (z. B. /sharpen + /propose-solution auf demselben Case)
    ueberschreiben sich damit nicht mehr gegenseitig (Lost Update: beide lesen
    den Case vor dem LLM-Call, der langsamere save() gewann und loeschte das
    Feld des schnelleren). No-op, wenn case_id nicht existiert (analog delete).
    """

    def save(self, case: SubmittedCase) -> None: ...
    def get(self, case_id: str) -> SubmittedCase | None: ...
    def list_all(self) -> list[SubmittedCase]: ...
    def delete(self, case_id: str) -> None: ...
    def update_field(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None: ...

    async def save_async(self, case: SubmittedCase) -> None: ...
    async def get_async(self, case_id: str) -> SubmittedCase | None: ...
    async def list_all_async(self) -> list[SubmittedCase]: ...
    async def delete_async(self, case_id: str) -> None: ...
    async def update_field_async(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None: ...

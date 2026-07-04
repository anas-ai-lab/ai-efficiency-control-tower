"""RepositoryPort -- Persistenz-Abstraktion fuer SubmittedCase."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol

from aect.application.models import MonitoringEntry, SubmittedCase
from aect.domain.types import CaseStatus, ReviewerDecision

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

    record_decision / record_decision_async (ADR-0043, minimaler
    Decision-Record): eigene Methode statt Wiederverwendung von update_field --
    setzt drei zusammengehoerige Felder (reviewer_decision, reviewer_note,
    decided_at) atomar in einem dedizierten UPDATE. No-op, wenn case_id nicht
    existiert (analog delete/update_field).

    update_status / update_status_async (Case-Lifecycle, siehe Lifecycle-ADR):
    dediziertes UPDATE der zwei zusammengehoerigen Spalten status + status_
    updated_at (F-011-Muster, analog record_decision mit decided_at) -- kein
    save() der ganzen Zeile, kein Lost-Update gegenueber parallelen LLM-Feld-
    Schreibvorgaengen. No-op, wenn case_id nicht existiert.

    add_monitoring_entry / list_monitoring_entries (Monitoring-ADR): eigene
    append-only Tabelle statt einer JSON-Spalte am Case -- kein Lost-Update
    (jeder Eintrag ist ein eigener INSERT, F-011-Lehre). add ist INSERT-only,
    list liefert chronologisch aufsteigend (ORDER BY created_at, id). Es gibt
    bewusst KEINE UPDATE-/DELETE-Methode fuer einzelne Eintraege; die einzige
    Loeschung ist die DSGVO-Kaskade in delete()/delete_async (Art. 17,
    ADR-0038), die die Eintraege eines Case mit-loescht.
    """

    def save(self, case: SubmittedCase) -> None: ...
    def get(self, case_id: str) -> SubmittedCase | None: ...
    def list_all(self) -> list[SubmittedCase]: ...
    def delete(self, case_id: str) -> None: ...
    def update_field(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None: ...
    def record_decision(
        self,
        case_id: str,
        decision: ReviewerDecision,
        note: str | None,
        decided_at: datetime,
    ) -> None: ...
    def update_status(
        self, case_id: str, status: CaseStatus, updated_at: datetime
    ) -> None: ...
    def add_monitoring_entry(self, entry: MonitoringEntry) -> None: ...
    def list_monitoring_entries(self, case_id: str) -> list[MonitoringEntry]: ...

    async def save_async(self, case: SubmittedCase) -> None: ...
    async def get_async(self, case_id: str) -> SubmittedCase | None: ...
    async def list_all_async(self) -> list[SubmittedCase]: ...
    async def delete_async(self, case_id: str) -> None: ...
    async def update_field_async(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None: ...
    async def record_decision_async(
        self,
        case_id: str,
        decision: ReviewerDecision,
        note: str | None,
        decided_at: datetime,
    ) -> None: ...
    async def update_status_async(
        self, case_id: str, status: CaseStatus, updated_at: datetime
    ) -> None: ...
    async def add_monitoring_entry_async(self, entry: MonitoringEntry) -> None: ...
    async def list_monitoring_entries_async(
        self, case_id: str
    ) -> list[MonitoringEntry]: ...

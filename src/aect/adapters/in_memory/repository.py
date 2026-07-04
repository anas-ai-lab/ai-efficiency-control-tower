"""InMemoryRepository -- implementiert RepositoryPort mit einem dict."""

from __future__ import annotations

import json
from datetime import datetime

from aect.application.models import SubmittedCase
from aect.application.ports.repository import CaseUpdateField
from aect.domain.types import CaseStatus, ReviewerDecision


class InMemoryRepository:
    """In-Memory-dict als Persistenz-Backend.

    Lebensdauer: Prozess-gebunden -- kein State nach Neustart.
    Zweck: Entwicklung, Tests, Baseline vor SQLiteRepository (Phase B).

    Security: kein Locking -- Single-Thread-Only. Fuer Produktivbetrieb
    wuerde ein SQLite-Adapter mit echtem Transaktionsmanagement benoetigt.
    """

    def __init__(self) -> None:
        self._store: dict[str, SubmittedCase] = {}

    def save(self, case: SubmittedCase) -> None:
        self._store[case.id] = case

    def get(self, case_id: str) -> SubmittedCase | None:
        return self._store.get(case_id)

    def list_all(self) -> list[SubmittedCase]:
        return list(self._store.values())

    def delete(self, case_id: str) -> None:
        """Loescht einen Case per ID (DSGVO Art. 17, ADR-0038). Idempotent."""
        self._store.pop(case_id, None)

    def update_field(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None:
        """Schreibt genau ein nachgelagert befuelltes Feld (F-011). No-op
        bei unbekannter case_id (analog delete). embedding kommt als
        JSON-String (Port-Kontrakt) und wird hier zurueck-dekodiert."""
        case = self._store.get(case_id)
        if case is None:
            return
        if field == "embedding":
            case.embedding = (
                [float(x) for x in json.loads(value)] if value is not None else None
            )
        else:
            setattr(case, field, value)

    def record_decision(
        self,
        case_id: str,
        decision: ReviewerDecision,
        note: str | None,
        decided_at: datetime,
    ) -> None:
        """Setzt Entscheidung + Notiz + Zeitstempel (ADR-0043). No-op bei
        unbekannter case_id (analog delete/update_field)."""
        case = self._store.get(case_id)
        if case is None:
            return
        case.reviewer_decision = decision
        case.reviewer_note = note
        case.decided_at = decided_at

    def update_status(
        self, case_id: str, status: CaseStatus, updated_at: datetime
    ) -> None:
        """Setzt Lifecycle-Status + Zeitstempel (Lifecycle-ADR). No-op bei
        unbekannter case_id (analog delete/update_field/record_decision)."""
        case = self._store.get(case_id)
        if case is None:
            return
        case.status = status
        case.status_updated_at = updated_at

    # async-Varianten (AUDIT-001, ADR-0037): erfuellen den RepositoryPort-
    # Vertrag. In-Memory-dict-Zugriffe blockieren nicht -> kein to_thread
    # noetig, direkter Aufruf der sync-Methode genuegt.
    async def save_async(self, case: SubmittedCase) -> None:
        self.save(case)

    async def get_async(self, case_id: str) -> SubmittedCase | None:
        return self.get(case_id)

    async def list_all_async(self) -> list[SubmittedCase]:
        return self.list_all()

    async def delete_async(self, case_id: str) -> None:
        self.delete(case_id)

    async def update_field_async(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None:
        self.update_field(case_id, field, value)

    async def record_decision_async(
        self,
        case_id: str,
        decision: ReviewerDecision,
        note: str | None,
        decided_at: datetime,
    ) -> None:
        self.record_decision(case_id, decision, note, decided_at)

    async def update_status_async(
        self, case_id: str, status: CaseStatus, updated_at: datetime
    ) -> None:
        self.update_status(case_id, status, updated_at)

"""InMemoryRepository -- implementiert RepositoryPort mit einem dict."""

from __future__ import annotations

from aect.application.models import SubmittedCase


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

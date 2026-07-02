"""Concurrency-Test fuer F-011 (Lost Update auf SubmittedCase-Narrativen).

Reproduziert das Audit-Szenario: /sharpen und /propose-solution laufen
parallel auf demselben Case. Vor dem Fix las jede Operation den ganzen Case
VOR ihrem LLM-Call und schrieb ihn danach komplett per INSERT OR REPLACE
zurueck -- der langsamere save() ueberschrieb das Feld der schnelleren
Operation mit None (reproduziert 6/6). Mit per-Feld-UPDATE (update_field_async)
bleiben beide Narrative erhalten.

Bewusst gegen SQLiteRepository statt InMemoryRepository: das In-Memory-dict
gibt beiden Operationen DASSELBE Objekt zurueck und maskiert den Lost Update.
"""

from __future__ import annotations

import asyncio
import datetime
from pathlib import Path

from aect.adapters.sqlite.repository import SQLiteRepository
from aect.application.ports.llm import LLMMessage, LLMResponse, ToolDefinition
from aect.application.ports.retriever import RetrievedChunk
from aect.application.service import TriageService
from aect.domain.models import UseCaseInput
from aect.domain.roi import ROIConfig

_FIXED_TIME = datetime.datetime(2026, 6, 10, 10, 0, 0, tzinfo=datetime.UTC)


class _FixedClock:
    def now(self) -> datetime.datetime:
        return _FIXED_TIME


class _SequentialIdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def generate(self) -> str:
        self._counter += 1
        return f"id-{self._counter:03d}"


class _RendezvousLLMAdapter:
    """Antwortet erst, wenn BEIDE parallelen complete()-Calls angekommen sind.

    Erzwingt deterministisch die Interleaving-Reihenfolge des Audits:
    beide Service-Methoden haben den Case bereits gelesen, bevor eine
    von beiden ihr Ergebnis persistiert.
    """

    def __init__(self, expected_calls: int = 2) -> None:
        self._expected = expected_calls
        self._arrived = 0
        self._all_arrived = asyncio.Event()

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        self._arrived += 1
        if self._arrived >= self._expected:
            self._all_arrived.set()
        await asyncio.wait_for(self._all_arrived.wait(), timeout=5.0)
        return LLMResponse(content="parallel-antwort", tool_calls=None)


class _EmptyRetriever:
    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return []


async def test_parallel_sharpen_and_propose_keep_both_narratives(
    tmp_path: Path, roi_config: ROIConfig, sample_use_case: UseCaseInput
) -> None:
    repo = SQLiteRepository(tmp_path / "concurrency.db")
    service = TriageService(
        repository=repo,
        clock=_FixedClock(),
        id_generator=_SequentialIdGenerator(),
        roi_config=roi_config,
        llm=_RendezvousLLMAdapter(expected_calls=2),
        retriever=_EmptyRetriever(),
    )
    case = service.submit_use_case(sample_use_case)

    sharpened, proposal = await asyncio.gather(
        service.sharpen_case(case.id),
        service.propose_solution(case.id),
    )
    assert sharpened is not None
    assert proposal is not None

    loaded = repo.get(case.id)
    assert loaded is not None
    # Vor F-011 gewann der langsamere save() und loeschte das Feld der
    # anderen Operation -- genau eines der beiden Felder war wieder None.
    assert loaded.sharpened_content_json is not None
    assert loaded.proposal_text == "parallel-antwort"


async def test_update_field_does_not_touch_other_columns(
    tmp_path: Path, roi_config: ROIConfig, sample_use_case: UseCaseInput
) -> None:
    """update_field schreibt genau eine Spalte -- alle anderen bleiben stehen."""
    repo = SQLiteRepository(tmp_path / "update_field.db")
    service = TriageService(
        repository=repo,
        clock=_FixedClock(),
        id_generator=_SequentialIdGenerator(),
        roi_config=roi_config,
        llm=_RendezvousLLMAdapter(expected_calls=1),
        retriever=_EmptyRetriever(),
    )
    case = service.submit_use_case(sample_use_case)

    repo.update_field(case.id, "proposal_text", "bestehender-vorschlag")
    repo.update_field(case.id, "sharpened_content_json", '{"raw_text": "x"}')
    repo.update_field(case.id, "embedding", "[0.1, 0.2]")

    loaded = repo.get(case.id)
    assert loaded is not None
    assert loaded.proposal_text == "bestehender-vorschlag"
    assert loaded.sharpened_content_json == '{"raw_text": "x"}'
    assert loaded.embedding == [0.1, 0.2]

    # No-op bei unbekannter ID (analog delete) -- kein Fehler, keine Aenderung.
    repo.update_field("gibt-es-nicht", "proposal_text", "verloren")
    assert repo.get("gibt-es-nicht") is None

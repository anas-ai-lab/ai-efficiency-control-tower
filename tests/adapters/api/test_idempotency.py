"""Integrations-Tests fuer Idempotency-Keys auf POST /triage.

Methode: dependency_overrides fuer Auth, TriageService UND IdempotencyStore
pro Test (kein geteilter State zwischen Tests).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import (
    get_idempotency_store,
    get_settings,
    get_triage_service,
)
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.idempotency_store import InMemoryIdempotencyStore
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.in_memory.retriever import MockRetriever
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config

TEST_API_KEY = "test-api-key-aect-2026"

_VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. "
        "Dieser Prozess dauert pro Rechnung ca. 15 Minuten und bindet "
        "erhebliche Kapazitaet im Finance-Team."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch "
        "auslesen, Pflichtfelder erkennen und direkt in SAP befuellen. "
        "Ziel ist eine Reduktion der manuellen Bearbeitungszeit auf unter "
        "2 Minuten pro Vorgang und eine Fehlerquote von unter 1 Prozent."
    ),
    "example_process": (
        "Eingehende Rechnung von Lieferant X wird manuell gescannt "
        "und Betraege sowie Kostenstellen haendig abgetippt."
    ),
    "time_per_case_hours_current": 0.2,
    "time_per_case_hours_with_ai": 0.0,
    "occurrences_per_employee_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "fixed_process_step",
    "implementation_approach": "development_on_existing",
    "data_classification": "no_personal_data",
}


def _make_idempotency_app() -> FastAPI:
    """App mit pro-Instanz geteiltem TriageService und IdempotencyStore.

    Beide muessen denselben State ueber mehrere Requests hinweg sehen --
    die Replay-Pruefung liest in Request 2, was Request 1 geschrieben hat.
    Deshalb Instanzen AUSSERHALB der Lambda erzeugen (Override-Lambdas
    werden pro Request neu aufgerufen, ohne Depends-Cache-Scope).
    """
    app = create_app()
    repository = InMemoryRepository()
    idempotency_store = InMemoryIdempotencyStore()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    app.dependency_overrides[get_idempotency_store] = lambda: idempotency_store
    return app


async def test_repeated_request_with_same_key_returns_same_case_id() -> None:
    app = _make_idempotency_app()
    headers = {"X-API-Key": TEST_API_KEY, "Idempotency-Key": "key-001"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)
        second = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.headers["Idempotent-Replay"] == "true"
    assert first.json()["id"] == second.json()["id"]


async def test_different_keys_create_different_cases() -> None:
    app = _make_idempotency_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = await client.post(
            "/triage",
            json=_VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY, "Idempotency-Key": "key-a"},
        )
        second = await client.post(
            "/triage",
            json=_VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY, "Idempotency-Key": "key-b"},
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


async def test_request_without_idempotency_key_behaves_unchanged() -> None:
    """Kein Header -> jede Anfrage erzeugt einen neuen Case (Status 201)."""
    app = _make_idempotency_app()
    headers = {"X-API-Key": TEST_API_KEY}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)
        second = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert "Idempotent-Replay" not in second.headers
    assert first.json()["id"] != second.json()["id"]


# ---------------------------------------------------------------------------
# F-010: Claim-then-fill (Race zwischen get und set)
# ---------------------------------------------------------------------------


def _make_idempotency_app_with_state() -> tuple[
    FastAPI, InMemoryRepository, InMemoryIdempotencyStore
]:
    """Wie _make_idempotency_app(), gibt Repository + Store mit zurueck --
    die F-010-Tests pruefen den State direkt (Case-Anzahl, Platzhalter)."""
    app = create_app()
    repository = InMemoryRepository()
    idempotency_store = InMemoryIdempotencyStore()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    app.dependency_overrides[get_idempotency_store] = lambda: idempotency_store
    return app, repository, idempotency_store


async def test_concurrent_requests_with_same_key_create_only_one_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-010: zwei ueberlappende Requests mit demselben Key -> genau EIN Case.

    Der alte Codepfad (get -> verarbeiten -> set) verlor das Rennen an
    seinem ersten await (check_similarity): Request 2 las "kein Eintrag",
    beide erzeugten einen Case und antworteten 201. Der Test haelt Request 1
    deterministisch in check_similarity fest, waehrend Request 2 eintrifft.
    """
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocking_check_similarity(self: TriageService, case: object) -> None:
        entered.set()
        await asyncio.wait_for(release.wait(), timeout=5.0)
        return None

    monkeypatch.setattr(TriageService, "check_similarity", blocking_check_similarity)

    app, repository, _ = _make_idempotency_app_with_state()
    headers = {"X-API-Key": TEST_API_KEY, "Idempotency-Key": "key-race"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first_task = asyncio.create_task(
            client.post("/triage", json=_VALID_PAYLOAD, headers=headers)
        )
        await asyncio.wait_for(entered.wait(), timeout=5.0)

        second_task = asyncio.create_task(
            client.post("/triage", json=_VALID_PAYLOAD, headers=headers)
        )
        # Alter Codepfad: Request 2 haengt ebenfalls in check_similarity
        # (Duplikat bereits erzeugt) und wird hier NICHT fertig.
        done, _pending = await asyncio.wait({second_task}, timeout=1.0)
        release.set()
        first = await first_task
        second = await second_task

    assert second_task in done, "Request 2 haette sofort 409 antworten muessen"
    assert sorted([first.status_code, second.status_code]) == [201, 409]
    assert len(repository.list_all()) == 1


async def test_in_flight_key_returns_409() -> None:
    app, _, store = _make_idempotency_app_with_state()
    claimed, existing = store.claim("key-in-flight")
    assert claimed is True and existing is None

    headers = {"X-API-Key": TEST_API_KEY, "Idempotency-Key": "key-in-flight"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)

    assert resp.status_code == 409


async def test_failed_request_releases_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Schlaegt die Verarbeitung fehl, wird der Platzhalter freigegeben --
    ein Wiederholungs-Request mit demselben Key laeuft normal durch."""
    original = TriageService.submit_use_case
    calls = {"n": 0}

    def failing_once(self: TriageService, use_case: object) -> object:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("kaputt")
        return original(self, use_case)  # type: ignore[arg-type]

    monkeypatch.setattr(TriageService, "submit_use_case", failing_once)

    app, _, store = _make_idempotency_app_with_state()
    headers = {"X-API-Key": TEST_API_KEY, "Idempotency-Key": "key-retry"}
    # raise_app_exceptions=False: der globale Exception-Handler antwortet 500,
    # der Transport soll die RuntimeError nicht in den Test durchreichen.
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        first = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)
        second = await client.post("/triage", json=_VALID_PAYLOAD, headers=headers)

    assert first.status_code == 500
    assert second.status_code == 201
    assert store.get("key-retry") == second.json()["id"]

"""Integrations-Tests fuer Idempotency-Keys auf POST /triage.

Methode: dependency_overrides fuer Auth, TriageService UND IdempotencyStore
pro Test (kein geteilter State zwischen Tests).
"""

from __future__ import annotations

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
    "time_savings_hours_per_case": 0.2,
    "frequency_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "mandatory",
    "implementation_approach": "standard_product",
    "implementation_complexity": 2,
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

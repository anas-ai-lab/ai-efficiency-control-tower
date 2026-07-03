"""Integrations-Tests fuer DELETE /cases/{case_id} (DSGVO Art. 17, ADR-0038).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage und das nachfolgende DELETE
denselben Zustand sehen.

Hinweis: Es gibt keinen GET /cases/{id}-Detail-Endpoint -- die erfolgreiche
Entfernung wird daher ueber ein zweites DELETE (-> 404) belegt.
"""

from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings, get_triage_service
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.in_memory.retriever import MockRetriever
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config

TEST_API_KEY = "test-api-key-aect-2026"
_AUTH = {"X-API-Key": TEST_API_KEY}

_VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. "
        "Dieser Prozess dauert pro Rechnung ca. 15 Minuten."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch "
        "auslesen, Pflichtfelder erkennen und direkt in SAP befuellen. "
        "Ziel ist eine Reduktion der Bearbeitungszeit auf unter 2 Minuten."
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


def _make_app() -> FastAPI:
    """App mit Test-Key und EINEM geteilten TriageService (gemeinsamer Repo)."""
    service = TriageService(
        repository=InMemoryRepository(),
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: service
    return app


async def test_delete_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.delete("/cases/some-id")
    assert response.status_code == 401


async def test_delete_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.delete("/cases/does-not-exist", headers=_AUTH)
    assert response.status_code == 404


async def test_delete_existing_case_returns_204_and_removes_it() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        assert created.status_code == 201
        case_id = created.json()["id"]

        deleted = await client.delete(f"/cases/{case_id}", headers=_AUTH)
        assert deleted.status_code == 204

        # Kein GET /cases/{id}-Endpoint -> Entfernung ueber zweites DELETE belegen.
        again = await client.delete(f"/cases/{case_id}", headers=_AUTH)
        assert again.status_code == 404

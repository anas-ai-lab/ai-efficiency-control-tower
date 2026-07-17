"""Integrations-Tests fuer die Monitoring-Endpoints (append-only, Monitoring-ADR):
POST /cases/{case_id}/monitoring und GET /cases/{case_id}/monitoring.

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage und die nachfolgenden
Monitoring-Calls denselben Zustand sehen -- analog test_decision.py/test_status.py.
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
    "time_per_case_hours_current": 0.2,
    "time_per_case_hours_with_ai": 0.0,
    "occurrences_per_employee_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "fixed_process_step",
    "evidence_level": "pure_estimate",
    "implementation_approach": "development_on_existing",
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


async def _create_case(client: AsyncClient) -> str:
    created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
    return created.json()["id"]


async def test_add_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/monitoring", json={"note": "hi"})
    assert response.status_code == 401


async def test_list_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases/some-id/monitoring")
    assert response.status_code == 401


async def test_add_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/does-not-exist/monitoring",
            json={"note": "hi"},
            headers=_AUTH,
        )
    assert response.status_code == 404


async def test_list_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases/does-not-exist/monitoring", headers=_AUTH)
    assert response.status_code == 404


async def test_empty_note_returns_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/monitoring", json={"note": ""}, headers=_AUTH
        )
    assert response.status_code == 422


async def test_missing_note_returns_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/monitoring", json={}, headers=_AUTH
        )
    assert response.status_code == 422


async def test_whitespace_only_note_returns_422_and_creates_no_entry() -> None:
    # V4.1-S10: min_length=1 allein liess "   " durch -- ein append-only
    # Eintrag ohne Inhalt, der per ADR-0046 nie wieder loeschbar waere.
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/monitoring", json={"note": "   "}, headers=_AUTH
        )
        entries = await client.get(f"/cases/{case_id}/monitoring", headers=_AUTH)

    assert response.status_code == 422
    assert entries.json() == []


async def test_note_is_stored_trimmed() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "  Pilot gestartet  "},
            headers=_AUTH,
        )

    assert response.status_code == 201
    assert response.json()["note"] == "Pilot gestartet"


async def test_note_exceeding_max_length_returns_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "x" * 2001},
            headers=_AUTH,
        )
    assert response.status_code == 422


async def test_extra_field_returns_422() -> None:
    # extra="forbid": ein unbekanntes Feld wird abgewiesen.
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "ok", "status_snapshot": "hacked"},
            headers=_AUTH,
        )
    assert response.status_code == 422


async def test_add_returns_201_with_status_snapshot() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)

        response = await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "Pilot gestartet"},
            headers=_AUTH,
        )

    assert response.status_code == 201
    body = response.json()
    assert body["case_id"] == case_id
    assert body["note"] == "Pilot gestartet"
    assert body["status_snapshot"] == "submitted"
    assert body["id"]
    assert body["created_at"] is not None


async def test_list_returns_entries_chronologically_after_status_change() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)

        await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "vor Review"},
            headers=_AUTH,
        )
        await client.post(
            f"/cases/{case_id}/status",
            json={"status": "in_review"},
            headers=_AUTH,
        )
        await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "in Review"},
            headers=_AUTH,
        )

        listed = await client.get(f"/cases/{case_id}/monitoring", headers=_AUTH)

    assert listed.status_code == 200
    body = listed.json()
    assert isinstance(body, list)
    assert [e["note"] for e in body] == ["vor Review", "in Review"]
    # Snapshots eingefroren zum jeweiligen Eintrags-Zeitpunkt.
    assert [e["status_snapshot"] for e in body] == ["submitted", "in_review"]


async def test_delete_case_removes_monitoring_entries() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await client.post(
            f"/cases/{case_id}/monitoring",
            json={"note": "wird mitgeloescht"},
            headers=_AUTH,
        )

        await client.delete(f"/cases/{case_id}", headers=_AUTH)
        # Case weg -> GET Monitoring 404 (kein verwaister Eintrag abrufbar).
        listed = await client.get(f"/cases/{case_id}/monitoring", headers=_AUTH)

    assert listed.status_code == 404


async def test_list_of_case_without_entries_is_empty_list() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        listed = await client.get(f"/cases/{case_id}/monitoring", headers=_AUTH)

    assert listed.status_code == 200
    assert listed.json() == []

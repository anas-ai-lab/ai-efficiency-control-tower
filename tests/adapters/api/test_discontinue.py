"""Integrations-Tests fuer POST /cases/{case_id}/discontinue + /reinstate
(Monitoring, V4.1-S7).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), analog test_status.py/test_decision.py.
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


async def test_discontinue_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/discontinue")
    assert response.status_code == 401


async def test_discontinue_wrong_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/some-id/discontinue", headers={"X-API-Key": "wrong-key"}
        )
    assert response.status_code == 401


async def test_reinstate_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/reinstate")
    assert response.status_code == 401


async def test_discontinue_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/does-not-exist/discontinue", headers=_AUTH)
    assert response.status_code == 404


async def test_reinstate_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/does-not-exist/reinstate", headers=_AUTH)
    assert response.status_code == 404


async def test_discontinue_sets_flag_and_returns_200() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        response = await client.post(f"/cases/{case_id}/discontinue", headers=_AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert body["discontinued"] is True


async def test_reinstate_clears_flag_and_returns_200() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]
        await client.post(f"/cases/{case_id}/discontinue", headers=_AUTH)

        response = await client.post(f"/cases/{case_id}/reinstate", headers=_AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert body["discontinued"] is False


async def test_discontinued_field_visible_in_case_detail() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        before = await client.get(f"/cases/{case_id}", headers=_AUTH)
        await client.post(f"/cases/{case_id}/discontinue", headers=_AUTH)
        after = await client.get(f"/cases/{case_id}", headers=_AUTH)

    assert before.json()["discontinued"] is False
    assert after.json()["discontinued"] is True


async def test_discontinued_field_visible_in_case_list() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]
        await client.post(f"/cases/{case_id}/discontinue", headers=_AUTH)

        listed = await client.get("/cases", headers=_AUTH)

    entries = {c["id"]: c for c in listed.json()}
    assert entries[case_id]["discontinued"] is True


async def test_discontinue_does_not_change_lifecycle_status() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]
        await client.post(
            f"/cases/{case_id}/status", json={"status": "approved"}, headers=_AUTH
        )

        response = await client.post(f"/cases/{case_id}/discontinue", headers=_AUTH)
        detail = await client.get(f"/cases/{case_id}", headers=_AUTH)

    assert response.status_code == 200
    assert detail.json()["status"] == "approved"
    assert detail.json()["discontinued"] is True

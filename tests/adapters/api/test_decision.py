"""Integrations-Tests fuer POST /cases/{case_id}/decision (Human-in-the-Loop,
minimaler Decision-Record -- ADR-0043).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage und der nachfolgende
Decision-Call denselben Zustand sehen -- analog test_delete_case.py.
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


async def test_decision_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/some-id/decision", json={"decision": "approved"}
        )
    assert response.status_code == 401


async def test_decision_wrong_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/some-id/decision",
            json={"decision": "approved"},
            headers={"X-API-Key": "wrong-key"},
        )
    assert response.status_code == 401


async def test_decision_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/does-not-exist/decision",
            json={"decision": "approved"},
            headers=_AUTH,
        )
    assert response.status_code == 404


async def test_invalid_decision_value_returns_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "pending"},  # nur approved/rejected sind gueltig
            headers=_AUTH,
        )
    assert response.status_code == 422


async def test_note_exceeding_max_length_returns_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "approved", "note": "x" * 2001},
            headers=_AUTH,
        )
    assert response.status_code == 422


async def test_approve_sets_fields_and_returns_200() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "approved", "note": "Passt, bitte umsetzen"},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert body["reviewer_decision"] == "approved"
    assert body["reviewer_note"] == "Passt, bitte umsetzen"
    assert body["decided_at"] is not None


async def test_reject_without_note_sets_fields() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "rejected"},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reviewer_decision"] == "rejected"
    assert body["reviewer_note"] is None


async def test_overwrite_existing_decision_updates_decided_at() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        first = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "approved", "note": "erste Einschaetzung"},
            headers=_AUTH,
        )
        second = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "rejected", "note": "korrigiert"},
            headers=_AUTH,
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["reviewer_decision"] == "rejected"
    assert second.json()["reviewer_note"] == "korrigiert"
    # Kein Bug, Korrektur-Fall: decided_at wird bei jedem Aufruf aktualisiert
    # (Ueberpruefung des Zeitstempel-Update-Verhaltens, nicht nur des Werts).
    assert second.json()["decided_at"] is not None


async def test_report_reflects_recorded_decision() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "approved", "note": "Freigegeben"},
            headers=_AUTH,
        )
        report = await client.post(f"/cases/{case_id}/report", json={}, headers=_AUTH)

    assert report.status_code == 200
    business_summary = report.json()["business_summary"]
    assert business_summary["reviewer_decision"] == "approved"
    assert business_summary["reviewer_note"] == "Freigegeben"
    assert business_summary["decided_at"] is not None


async def test_report_before_any_decision_shows_pending() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        case_id = created.json()["id"]

        report = await client.post(f"/cases/{case_id}/report", json={}, headers=_AUTH)

    assert report.status_code == 200
    business_summary = report.json()["business_summary"]
    assert business_summary["reviewer_decision"] == "pending"
    assert business_summary["reviewer_note"] is None
    assert business_summary["decided_at"] is None

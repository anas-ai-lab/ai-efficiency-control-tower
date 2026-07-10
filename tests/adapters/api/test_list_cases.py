"""Integrations-Tests fuer GET /cases (Portfolio-Read, P2).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage und der nachfolgende
GET /cases denselben Zustand sehen -- analog test_decision.py/test_status.py.

Prueft, dass die um Portfolio-Felder erweiterte CaseSummary die neuen Werte
liefert: (a) ein Case mit bestandenem Vorfilter (alle Werte gesetzt) und
(b) ein Case mit Vorfilter-Fail (zone/net/composite/hours null).
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

_PASSING_PAYLOAD: dict = {
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
    "implementation_approach": "development_on_existing",
    "data_classification": "no_personal_data",
}

# Winziger Nutzen -> Vorfilter faellt durch (analog test_report._FAILING_PAYLOAD).
_FAILING_PAYLOAD: dict = {
    **_PASSING_PAYLOAD,
    "title": "Sehr kleiner Use Case ohne nennenswerten Nutzen",
    "department": "Legal",
    "time_per_case_hours_current": 0.01,
    "occurrences_per_employee_per_year": 5,
    "affected_employees_count": 1,
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


async def test_summary_of_passing_case_has_all_portfolio_fields() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_PASSING_PAYLOAD, headers=_AUTH)
        assert created.json()["passed_vorfilter"] is True

        listed = await client.get("/cases", headers=_AUTH)

    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    summary = body[0]
    assert summary["department"] == "Finance"
    assert summary["status"] == "submitted"
    assert summary["is_actionable"] is True
    # Vorfilter bestanden -> alle abgeleiteten Felder gesetzt (nicht None).
    assert summary["zone"] is not None
    assert summary["net_expected_benefit_eur"] is not None
    assert summary["composite_total"] is not None
    assert summary["hours_per_year"] is not None


async def test_summary_of_failing_case_has_null_derived_fields() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_FAILING_PAYLOAD, headers=_AUTH)
        assert created.json()["passed_vorfilter"] is False

        listed = await client.get("/cases", headers=_AUTH)

    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    summary = body[0]
    assert summary["department"] == "Legal"
    assert summary["status"] == "submitted"
    # Vorfilter durchgefallen -> zone/net/composite/hours null (wie TriageResponse).
    assert summary["zone"] is None
    assert summary["net_expected_benefit_eur"] is None
    assert summary["composite_total"] is None
    assert summary["hours_per_year"] is None


async def test_list_cases_stays_a_bare_list() -> None:
    # Abwaertskompatibilitaet: Response bleibt eine Liste, kein Envelope-Objekt.
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        await client.post("/triage", json=_PASSING_PAYLOAD, headers=_AUTH)
        listed = await client.get("/cases", headers=_AUTH)

    assert listed.status_code == 200
    assert isinstance(listed.json(), list)

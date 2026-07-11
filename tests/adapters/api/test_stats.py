"""Integrations-Tests fuer GET /stats (Portfolio-Kennzahlen, V4-P7).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage + Status-/Decision-Wechsel
und der nachfolgende GET /stats denselben Zustand sehen -- analog
test_list_cases.py.

Prueft die Funnel-Semantik: eingereicht (alle), bewertet (Vorfilter bestanden),
umgesetzt (Status IMPLEMENTED) und die Netto-Nutzen-Summe ueber APPROVED +
IMPLEMENTED.
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

# Winziger Nutzen -> Vorfilter faellt durch (analog test_list_cases._FAILING_PAYLOAD).
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


async def test_stats_is_public() -> None:
    # Kein API-Key -> die Startseite muss die Kennzahlen ohne Login lesen koennen.
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.get("/stats")

    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "eingereicht": 0,
        "bewertet": 0,
        "umgesetzt": 0,
        "netto_nutzen_freigegeben_eur": 0.0,
    }


async def test_stats_funnel_and_released_net_benefit() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        # Zwei bestandene + ein durchgefallener Case: eingereicht=3, bewertet=2.
        approved = await client.post("/triage", json=_PASSING_PAYLOAD, headers=_AUTH)
        assert approved.json()["passed_vorfilter"] is True
        approved_id = approved.json()["id"]
        approved_net = approved.json()["roi"]["net_expected_benefit_eur"]

        implemented = await client.post(
            "/triage",
            json={**_PASSING_PAYLOAD, "title": "Zweiter tragfaehiger Use Case"},
            headers=_AUTH,
        )
        implemented_id = implemented.json()["id"]
        implemented_net = implemented.json()["roi"]["net_expected_benefit_eur"]

        failing = await client.post("/triage", json=_FAILING_PAYLOAD, headers=_AUTH)
        assert failing.json()["passed_vorfilter"] is False

        # Einen Case freigeben (APPROVED), einen umsetzen (IMPLEMENTED).
        await client.post(
            f"/cases/{approved_id}/decision",
            json={"decision": "approved", "note": None},
            headers=_AUTH,
        )
        await client.post(
            f"/cases/{implemented_id}/status",
            json={"status": "implemented"},
            headers=_AUTH,
        )

        stats = await client.get("/stats")

    assert stats.status_code == 200
    body = stats.json()
    assert body["eingereicht"] == 3
    assert body["bewertet"] == 2
    assert body["umgesetzt"] == 1
    # Netto-Nutzen-Summe = freigegebener + umgesetzter Case (der durchgefallene
    # zaehlt nicht, sein Status bleibt SUBMITTED).
    assert body["netto_nutzen_freigegeben_eur"] == approved_net + implemented_net

"""Integrations-Tests fuer GET /stats (Portfolio-Kennzahlen, V4-P7).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage + Status-/Decision-Wechsel
und der nachfolgende GET /stats denselben Zustand sehen -- analog
test_list_cases.py.

Prueft die Funnel-Semantik: eingereicht (alle), bewertet (Board-Entscheidung,
ReviewerDecision != PENDING), umgesetzt (Status IMPLEMENTED) und die Netto-
Nutzen-Summe ueber APPROVED + IMPLEMENTED.
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
    # Szenario trennt die drei Zaehler bewusst: "bewertet" folgt der
    # Board-Entscheidung (ReviewerDecision != PENDING), "umgesetzt" dem Status.
    #   A: /decision approved  -> decision=approved, status=approved
    #   B: /status implemented -> decision=PENDING,  status=implemented
    #   C: /decision rejected  -> decision=rejected, status=rejected
    # => eingereicht=3, bewertet=2 (A,C -- B ist umgesetzt, aber unbewertet),
    #    umgesetzt=1 (B), netto ueber status approved+implemented (A,B).
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        a = await client.post("/triage", json=_PASSING_PAYLOAD, headers=_AUTH)
        a_id = a.json()["id"]
        a_net = a.json()["roi"]["net_expected_benefit_eur"]

        b = await client.post(
            "/triage",
            json={**_PASSING_PAYLOAD, "title": "Zweiter tragfaehiger Use Case"},
            headers=_AUTH,
        )
        b_id = b.json()["id"]
        b_net = b.json()["roi"]["net_expected_benefit_eur"]

        c = await client.post(
            "/triage",
            json={**_PASSING_PAYLOAD, "title": "Dritter tragfaehiger Use Case"},
            headers=_AUTH,
        )
        c_id = c.json()["id"]

        await client.post(
            f"/cases/{a_id}/decision",
            json={"decision": "approved", "note": None},
            headers=_AUTH,
        )
        await client.post(
            f"/cases/{b_id}/status",
            json={"status": "implemented"},
            headers=_AUTH,
        )
        await client.post(
            f"/cases/{c_id}/decision",
            json={"decision": "rejected", "note": None},
            headers=_AUTH,
        )

        stats = await client.get("/stats")

    assert stats.status_code == 200
    body = stats.json()
    assert body["eingereicht"] == 3
    # A (approved) + C (rejected) sind vom Board entschieden; B (nur implemented,
    # ohne Decision) zaehlt NICHT als bewertet.
    assert body["bewertet"] == 2
    assert body["umgesetzt"] == 1
    # Netto ueber Status approved (A) + implemented (B); rejected (C) faellt raus.
    assert body["netto_nutzen_freigegeben_eur"] == a_net + b_net

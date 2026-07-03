"""Integrations-Tests fuer POST /cases/{case_id}/compliance-hints."""

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
    "time_savings_hours_per_case": 0.2,
    "frequency_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "mandatory",
    "implementation_approach": "standard_product",
    "implementation_complexity": 2,
    "data_classification": "no_personal_data",
}

# data_classification=sensitive_personal -> routing.risk_flags nicht leer
# (domain/routing.py: _collect_risk_flags) -> DSFA-Query laeuft zusaetzlich.
_SENSITIVE_PAYLOAD: dict = {
    **_VALID_PAYLOAD,
    "data_classification": "sensitive_personal",
}


def _make_app() -> FastAPI:
    """Repository ausserhalb der Lambda -- State muss zwischen 'Case anlegen'
    und 'Compliance-Hinweise abrufen' (zwei Requests) erhalten bleiben.
    Gleiche Begruendung wie in test_sharpen.py._make_app."""
    app = create_app()
    repository = InMemoryRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    return app


async def test_compliance_hints_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/compliance-hints")
    assert response.status_code == 401


async def test_compliance_hints_unknown_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/does-not-exist/compliance-hints",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 404


async def test_no_risk_case_has_no_hint_and_no_llm_call() -> None:
    """Kein risk_flag -> nur Transparenz-Query; MockRetriever-Corpus hat
    dafuer keinen Treffer -> kein LLM-Call, hint_text None, citations leer
    (Graceful Degradation, kein ungegruendeter Hinweis)."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_VALID_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/compliance-hints",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["hint_text"] is None
    assert data["citations"] == []


async def test_sensitive_case_triggers_dsfa_query_and_returns_citation() -> None:
    """sensitive_personal -> risk_flags nicht leer -> DSFA-Query laeuft
    zusaetzlich zur Transparenz-Query. MockRetriever-Corpus liefert fuer die
    DSFA-Query einen Treffer (mock-compliance-dsfa) -> LLM-Call + Citation."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_SENSITIVE_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/compliance-hints",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["hint_text"] is not None
    assert "[mock-response]" in data["hint_text"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["number"] == 1
    assert data["citations"][0]["source_id"] == "mock-compliance-dsfa"
    # MockRetriever liefert kein metadata -> Fallback citation == source_id
    # (ComplianceCitation, application/models.py).
    assert data["citations"][0]["citation"] == "mock-compliance-dsfa"

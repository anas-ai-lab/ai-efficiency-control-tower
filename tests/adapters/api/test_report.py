"""Integrations-Tests fuer POST /cases/{case_id}/report."""

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

_PASSING_PAYLOAD: dict = {
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

_FAILING_PAYLOAD: dict = {
    **_PASSING_PAYLOAD,
    "title": "Sehr kleiner Use Case ohne nennenswerten Nutzen",
    "time_savings_hours_per_case": 0.01,
    "frequency_per_year": 5,
    "affected_employees_count": 1,
}

_SENSITIVE_PASSING_PAYLOAD: dict = {
    **_PASSING_PAYLOAD,
    "data_classification": "sensitive_personal",
}


def _make_app() -> FastAPI:
    """Repository ausserhalb der Lambda -- State muss zwischen 'Case anlegen'
    und 'Report abrufen' (zwei Requests) erhalten bleiben. Gleiche
    Begruendung wie in test_sharpen.py._make_app."""
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


async def test_report_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/report")
    assert response.status_code == 401


async def test_report_unknown_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/does-not-exist/report",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 404


async def test_report_passing_case_has_zone_and_recommendation() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_PASSING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/report",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    business = data["business_summary"]
    technical = data["technical_detail"]

    assert data["case_id"] == case_id
    assert business["title"] == _PASSING_PAYLOAD["title"]
    assert business["zone"] is not None
    assert business["expected_benefit_eur"] is not None
    assert _PASSING_PAYLOAD["title"] in business["summary_text"]
    assert technical["passed_vorfilter"] is True
    assert technical["composite_total"] is not None
    assert technical["roi_theoretical_potential_eur"] is not None
    assert business["sharpened_text"] is None
    assert technical["proposal_text"] is None


async def test_report_failing_case_has_no_zone() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_FAILING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/report",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    business = data["business_summary"]
    technical = data["technical_detail"]

    assert business["zone"] is None
    assert business["is_actionable"] is False
    assert business["expected_benefit_eur"] is None
    assert technical["passed_vorfilter"] is False
    assert technical["vorfilter_failed_criteria"]
    assert technical["composite_total"] is None
    assert technical["roi_theoretical_potential_eur"] is None


async def test_report_passes_through_sharpened_and_proposal_text() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_PASSING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/report",
            json={
                "sharpened_text": "Geschaerfte Version: ...",
                "proposal_text": "Vorschlag: ...",
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["business_summary"]["sharpened_text"] == "Geschaerfte Version: ..."
    assert data["technical_detail"]["proposal_text"] == "Vorschlag: ..."


async def test_report_rejects_unknown_field() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_PASSING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/report",
            json={"unexpected_field": "x"},
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 422


async def test_report_uses_persisted_sharpened_text_after_sharpen_call() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_PASSING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        await client.post(
            f"/cases/{case_id}/sharpen",
            headers={"X-API-Key": TEST_API_KEY},
        )

        response = await client.post(
            f"/cases/{case_id}/report",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    sharpened = data["business_summary"]["sharpened_text"]
    assert sharpened is not None
    assert "[mock-response]" in sharpened


async def test_report_uses_persisted_proposal_text_after_propose_solution_call() -> (
    None
):
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_PASSING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        await client.post(
            f"/cases/{case_id}/propose-solution",
            headers={"X-API-Key": TEST_API_KEY},
        )

        response = await client.post(
            f"/cases/{case_id}/report",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    proposal = data["technical_detail"]["proposal_text"]
    assert proposal is not None
    assert "[mock-response]" in proposal


async def test_report_uses_persisted_compliance_hints_after_compliance_hints_call() -> (
    None
):
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage",
            json=_SENSITIVE_PASSING_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY},
        )
        case_id = created.json()["id"]

        await client.post(
            f"/cases/{case_id}/compliance-hints",
            headers={"X-API-Key": TEST_API_KEY},
        )

        response = await client.post(
            f"/cases/{case_id}/report",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    data = response.json()
    business = data["business_summary"]
    # Fail loud (CLAUDE.md): MockRetriever -> ehrliche 'nicht verfuegbar'-Antwort
    # im Report, NIE eine mock-Quelle als Citation.
    assert business["compliance_hint_text"] is not None
    assert "nicht verfuegbar" in business["compliance_hint_text"]
    assert business["compliance_citations"] == []
    # Guard: die konkrete Mock-Quelle darf nie in der Report-Response auftauchen.
    assert "mock-compliance-dsfa" not in response.text


async def test_report_without_compliance_hints_call_has_no_hint() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        created = await client.post(
            "/triage", json=_PASSING_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
        )
        case_id = created.json()["id"]

        response = await client.post(
            f"/cases/{case_id}/report",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200
    business = response.json()["business_summary"]
    assert business["compliance_hint_text"] is None
    assert business["compliance_citations"] == []

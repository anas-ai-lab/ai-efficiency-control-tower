"""Integrations-Tests fuer POST /triage.

Methode: dependency_overrides fuer Auth + frischen TriageService pro Test
(isolierter InMemoryRepository -- kein geteilter State zwischen Tests).
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
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config

TEST_API_KEY = "test-api-key-aect-2026"

# ---------------------------------------------------------------------------
# Minimaler gueltiger Payload -- besteht Vorfilter sicher
# (5000 Vorgaenge/Jahr * 0.2 h * 10 Mitarbeiter = 10.000 h/Jahr >> Schwelle 120 h)
# ---------------------------------------------------------------------------
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


def _make_triage_app() -> FastAPI:
    """App mit konfiguriertem Test-Key und isoliertem TriageService.

    get_triage_service-Override: frischer InMemoryRepository pro Test,
    damit Tests nicht gegenseitig State akkumulieren.
    """
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=InMemoryRepository(),
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
    )
    return app


# ---------------------------------------------------------------------------
# Auth-Schutz
# ---------------------------------------------------------------------------


async def test_post_triage_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post("/triage", json=_VALID_PAYLOAD)
    assert response.status_code == 401


async def test_post_triage_with_correct_key_returns_201() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=_VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Response-Struktur
# ---------------------------------------------------------------------------


async def test_response_contains_required_top_level_fields() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=_VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY},
        )
    data = response.json()
    for field in (
        "id",
        "submitted_at",
        "title",
        "passed_vorfilter",
        "is_actionable",
        "vorfilter",
        "routing",
        "feasibility",
    ):
        assert field in data, f"Pflichtfeld '{field}' fehlt in Response"


async def test_response_id_is_nonempty_string() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=_VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY},
        )
    data = response.json()
    assert isinstance(data["id"], str)
    assert len(data["id"]) > 0


async def test_high_value_case_passes_vorfilter_and_has_zone() -> None:
    """Payload mit hohem ROI besteht Vorfilter -- roi/composite/zone nicht None."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=_VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY},
        )
    data = response.json()
    assert data["passed_vorfilter"] is True
    assert data["roi"] is not None
    assert data["composite"] is not None
    assert data["zone"] is not None
    assert data["zone"]["final_zone"] in (
        "MARGINAL_GAIN",
        "CALCULATED_RISK",
        "LIKELY_WIN",
    )


async def test_low_value_case_fails_vorfilter_and_has_null_zone() -> None:
    """Minimales Volumen unterschreitet Stunden-Schwelle -- zone muss None sein."""
    low_value = {
        **_VALID_PAYLOAD,
        "frequency_per_year": 1,
        "time_savings_hours_per_case": 0.01,
    }
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=low_value,
            headers={"X-API-Key": TEST_API_KEY},
        )
    data = response.json()
    assert data["passed_vorfilter"] is False
    assert data["roi"] is None
    assert data["composite"] is None
    assert data["zone"] is None


# ---------------------------------------------------------------------------
# Validierung -- ungueltige Inputs
# ---------------------------------------------------------------------------


async def test_missing_required_field_returns_422() -> None:
    payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "title"}
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=payload,
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 422


async def test_extra_field_returns_422() -> None:
    """extra='forbid' auf UseCaseInput -- unbekannte Felder muessen 422 geben."""
    payload = {**_VALID_PAYLOAD, "unbekanntes_feld": "sollte_fehlschlagen"}
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=payload,
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 422


async def test_invalid_enum_value_returns_422() -> None:
    payload = {**_VALID_PAYLOAD, "employee_category": "nicht_existent"}
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=payload,
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 422


async def test_out_of_range_complexity_returns_422() -> None:
    payload = {**_VALID_PAYLOAD, "implementation_complexity": 10}
    async with AsyncClient(
        transport=ASGITransport(app=_make_triage_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/triage",
            json=payload,
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 422

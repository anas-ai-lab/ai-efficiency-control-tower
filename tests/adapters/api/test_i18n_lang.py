"""Endpoint-Ebene i18n (V4.1-S6): lang-Query-Param, EN-Texte, 422 bei ungueltig.

Deckt die Read-Time-Projektion ueber POST /triage ab: die Erklaerbarkeit
(management/recommendation_text) und die re-abgeleiteten Routing-Signale kommen
in der gewuenschten Sprache; Default (ohne Parameter) bleibt deutsch; ein
ungueltiger lang-Wert wird von der Literal-Validierung als 422 abgewiesen.
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

# Gueltiger Payload, der den Vorfilter sicher besteht (bewertetes Ergebnis ->
# management/berechnung/routing sind befuellt, sonst waeren die Texte None).
_VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. Dieser Prozess "
        "dauert pro Rechnung ca. 15 Minuten."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch auslesen "
        "und direkt in SAP befuellen. Ziel ist unter 2 Minuten pro Vorgang."
    ),
    "example_process": (
        "Eingehende Rechnung von Lieferant X wird manuell gescannt und Betraege "
        "haendig abgetippt."
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
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key="test-key")
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=InMemoryRepository(),
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    return app


async def _post(lang_query: str = "") -> dict:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.post(f"/triage{lang_query}", json=_VALID_PAYLOAD)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_default_without_lang_is_german() -> None:
    data = await _post()
    assert data["management"]["empfehlung_satz"].startswith("Empfehlung:")
    assert "eingesparte Stunden pro Jahr" in data["routing"]["recommendation_text"]
    assert any("Komplexität" in s for s in data["routing"]["automation_signals"])


async def test_lang_de_matches_default() -> None:
    default = await _post()
    explicit = await _post("?lang=de")
    assert explicit["management"] == default["management"]
    assert (
        explicit["routing"]["recommendation_text"]
        == default["routing"]["recommendation_text"]
    )


async def test_lang_en_returns_english_texts() -> None:
    data = await _post("?lang=en")
    assert data["management"]["empfehlung_satz"].startswith("Recommendation:")
    # Empfehlungs-Satz-Template: "...at effort {x} of 9 and {dp}."
    assert "hours saved per year" in data["routing"]["recommendation_text"]
    # Re-abgeleitete Routing-Signale in EN.
    assert any("Complexity" in s for s in data["routing"]["automation_signals"])
    # Kein deutscher Rest im Management-Satz.
    assert "Empfehlung:" not in data["management"]["empfehlung_satz"]


async def test_invalid_lang_is_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.post("/triage?lang=fr", json=_VALID_PAYLOAD)
    assert resp.status_code == 422

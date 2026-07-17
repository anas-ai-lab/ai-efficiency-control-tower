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
from aect.application.ports.retriever import RetrievedChunk, RetrieverPort
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config

TEST_API_KEY = "test-api-key-aect-2026"


class _CuratedRetriever:
    """Liefert eine echte, NICHT mock-praefigierte Quelle -- wie der Chroma-
    Adapter gegen die geseedete Wissensbasis (source_id z. B. 'dsgvo-art-35-dsfa',
    Metadata mit citation/url). Deckt den Erfolgspfad ab, ohne laufenden Chroma-
    Container. Mock-Fixtures sind ausschliesslich in Tests zulaessig (CLAUDE.md).
    """

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                text=(
                    "Eine Datenschutz-Folgenabschaetzung kann bei hohem Risiko "
                    "fuer Betroffene erforderlich sein."
                ),
                source_id="dsgvo-art-35-dsfa",
                score=1.0,
                metadata={
                    "citation": "DSGVO Art. 35",
                    "url": "https://example.test/dsgvo-art-35",
                },
            )
        ]

    async def delete_by_source_id(self, source_id: str) -> None:
        return None


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

# data_classification=sensitive_personal -> routing.risk_flags nicht leer
# (domain/routing.py: _collect_risk_flags) -> DSFA-Query laeuft zusaetzlich.
_SENSITIVE_PAYLOAD: dict = {
    **_VALID_PAYLOAD,
    "data_classification": "sensitive_personal",
}


def _make_app(retriever: RetrieverPort | None = None) -> FastAPI:
    """Repository ausserhalb der Lambda -- State muss zwischen 'Case anlegen'
    und 'Compliance-Hinweise abrufen' (zwei Requests) erhalten bleiben.
    Gleiche Begruendung wie in test_sharpen.py._make_app.

    retriever: Default MockRetriever (loest Fail-Loud aus); ein _CuratedRetriever
    simuliert die echte, geseedete Wissensbasis fuer den Erfolgspfad."""
    app = create_app()
    repository = InMemoryRepository()
    used_retriever = retriever if retriever is not None else MockRetriever()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=used_retriever,
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


async def test_sensitive_case_with_mock_retriever_fails_loud() -> None:
    """Fail loud (CLAUDE.md): sensitive_personal -> DSFA-Query trifft im Mock-
    Corpus 'mock-compliance-dsfa'. Statt diese Mock-Quelle als echte Citation zu
    rendern (frueherer Bug), liefert der Endpoint eine ehrliche 'nicht
    verfuegbar'-Antwort -- KEINE Citation, KEIN mock-Praefix in der Response."""
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
    assert "nicht verfügbar" in data["hint_text"]
    assert data["citations"] == []
    # Guard: die konkrete Mock-Quelle darf nie in der Response auftauchen.
    assert "mock-compliance-dsfa" not in response.text
    assert all(not c["source_id"].startswith("mock") for c in data["citations"])


async def test_sensitive_case_with_real_kb_returns_real_citation() -> None:
    """Erfolgspfad: gegen die echte (geseedete) Wissensbasis -- der _Curated-
    Retriever liefert eine reale Quelle (dsgvo-art-35-dsfa). LLM-Call + echte
    Citation, kein mock-Praefix."""
    app = _make_app(retriever=_CuratedRetriever())
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
    assert data["hint_text"] is not None
    assert "[mock-response]" in data["hint_text"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["number"] == 1
    assert data["citations"][0]["source_id"] == "dsgvo-art-35-dsfa"
    assert data["citations"][0]["citation"] == "DSGVO Art. 35"
    # Guard: keine mock-praefigierte Quelle (der [mock-response]-Text stammt vom
    # Test-LLM-Echo, ist keine Quellen-ID -- darum praezise auf source_id pruefen).
    assert all(not c["source_id"].startswith("mock") for c in data["citations"])

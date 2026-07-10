"""Integrations-Tests fuer GET /cases/similarity-pairs (Dedup-View, P9).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), analog test_list_cases.py. Der Test-Service hat
keinen Embedder -- POST /triage berechnet daher keine Embeddings. Die Tests
seeden die Intake-Embeddings deshalb direkt in den Repo (repo.update_field mit
JSON-String, wie im Port-Kontrakt) und pruefen dann den Read-Endpoint.

Deckt ab: Happy-Path (ein Paar), Zaehlung der Cases ohne Embedding, leere DB,
Auth-Fail sowie die Routing-Falle (die literale Route /cases/similarity-pairs
wird nicht von einer parametrisierten /cases/{case_id}-Route geschluckt).
"""

from __future__ import annotations

import json

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

_PAYLOAD: dict = {
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


def _make_app() -> tuple[FastAPI, InMemoryRepository]:
    """App mit Test-Key + EINEM geteilten TriageService; Repo zum Seeden."""
    repo = InMemoryRepository()
    service = TriageService(
        repository=repo,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: service
    return app, repo


async def _create_case(client: AsyncClient, title: str) -> str:
    """POST /triage mit angepasstem Titel, gibt die Case-ID zurueck."""
    resp = await client.post(
        "/triage", json={**_PAYLOAD, "title": title}, headers=_AUTH
    )
    assert resp.status_code == 201
    return str(resp.json()["id"])


async def test_two_matching_cases_yield_one_pair() -> None:
    app, repo = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        id_a = await _create_case(client, "Rechnungs-Automatisierung A")
        id_b = await _create_case(client, "Rechnungs-Automatisierung B")
        # Identische Embeddings -> cosine 1.0 (>= Combine-Schwelle).
        repo.update_field(id_a, "embedding", json.dumps([1.0, 0.0]))
        repo.update_field(id_b, "embedding", json.dumps([1.0, 0.0]))

        resp = await client.get("/cases/similarity-pairs", headers=_AUTH)

    assert resp.status_code == 200
    body = resp.json()
    assert body["cases_without_embedding"] == 0
    assert len(body["pairs"]) == 1
    pair = body["pairs"][0]
    assert {pair["case_a_id"], pair["case_b_id"]} == {id_a, id_b}
    assert pair["similarity_score"] == 1.0
    assert pair["suggest_combine"] is True


async def test_case_without_embedding_is_counted() -> None:
    app, repo = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        id_a = await _create_case(client, "Case A")
        id_b = await _create_case(client, "Case B")
        await _create_case(client, "Case C ohne Embedding")
        repo.update_field(id_a, "embedding", json.dumps([1.0, 0.0]))
        repo.update_field(id_b, "embedding", json.dumps([1.0, 0.0]))

        resp = await client.get("/cases/similarity-pairs", headers=_AUTH)

    assert resp.status_code == 200
    body = resp.json()
    assert body["cases_without_embedding"] == 1
    assert len(body["pairs"]) == 1


async def test_empty_db_returns_empty_pairs() -> None:
    app, _ = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/cases/similarity-pairs", headers=_AUTH)

    assert resp.status_code == 200
    assert resp.json() == {"pairs": [], "cases_without_embedding": 0}


async def test_without_api_key_returns_401() -> None:
    app, _ = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/cases/similarity-pairs")

    assert resp.status_code == 401


async def test_literal_route_not_shadowed_by_param_route() -> None:
    """Routing-Falle: GET /cases/similarity-pairs matcht die literale Route,
    nicht eine parametrisierte /cases/{case_id}-Route. Zugleich bleibt eine
    echte parametrisierte GET-Route (/cases/{id}/monitoring) erreichbar --
    beide koexistieren kollisionsfrei."""
    app, _repo = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        real_id = await _create_case(client, "Realer Case")

        # Literale Route: liefert das Pairs-Objekt (nicht als case_id gedeutet).
        literal = await client.get("/cases/similarity-pairs", headers=_AUTH)
        assert literal.status_code == 200
        assert "pairs" in literal.json()
        assert "cases_without_embedding" in literal.json()

        # Parametrisierte GET-Route mit einer echten case_id funktioniert weiter.
        monitoring = await client.get(f"/cases/{real_id}/monitoring", headers=_AUTH)
        assert monitoring.status_code == 200
        assert isinstance(monitoring.json(), list)

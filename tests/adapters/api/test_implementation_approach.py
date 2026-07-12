"""Integrations-Tests fuer den optionalen Implementierungsansatz + Nachtragen
(V4.1, ADR-0050).

Deckt ab:
  (a) POST /triage OHNE implementation_approach -> 201, Vor-Bewertungs-Zustand
      (evaluation_pending), kein Composite/Zone/Routing, kein 5xx.
  (b) POST /cases/{id}/implementation-approach -> volle Neubewertung; die
      Scores sind identisch zu einem Case, der den Ansatz von Anfang an hatte.
  Plus: deutsche 422-Feldtexte fuer die Pflichtfelder, Admin-Auth, 409 fuer
  bewertungsabhaengige Endpoints im Vor-Bewertungs-Zustand.

Methode wie test_status.py: EIN geteilter TriageService (gemeinsamer Repo),
damit POST /triage und Folge-Calls denselben Zustand sehen.
"""

from __future__ import annotations

from typing import Any

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

_APPROACH = "development_on_existing"

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
    "time_per_case_hours_current": 0.2,
    "time_per_case_hours_with_ai": 0.0,
    "occurrences_per_employee_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "fixed_process_step",
    "evidence_level": "pure_estimate",
    "implementation_approach": _APPROACH,
    "data_classification": "no_personal_data",
}


def _without(*keys: str) -> dict:
    return {k: v for k, v in _VALID_PAYLOAD.items() if k not in keys}


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


# --- (a) Einreichung ohne Ansatz -> Vor-Bewertungs-Zustand ------------------


async def test_submit_without_approach_is_pending_and_no_5xx() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.post("/triage", json=_without("implementation_approach"))

    assert resp.status_code == 201
    body = resp.json()
    assert body["evaluation_pending"] is True
    assert body["passed_vorfilter"] is False
    assert body["is_actionable"] is False
    # Kein Composite/Zone/Routing/Vorfilter/Feasibility im Vor-Bewertungs-Zustand.
    for field in ("roi", "composite", "zone", "vorfilter", "routing", "feasibility"):
        assert body[field] is None, f"{field} sollte None sein"
    assert body["score_breakdown"] is None


async def test_submit_with_approach_is_not_pending() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.post("/triage", json=_VALID_PAYLOAD)

    assert resp.status_code == 201
    body = resp.json()
    assert body["evaluation_pending"] is False
    assert body["routing"] is not None
    assert body["composite"] is not None


# --- (b) Nachtragen -> volle Neubewertung, Scores identisch -----------------


def _score_relevant(body: dict[str, Any]) -> dict[str, Any]:
    """Bewertungs-relevante Felder ohne id/submitted_at (die zwangslaeufig
    abweichen)."""
    return {k: v for k, v in body.items() if k not in ("id", "submitted_at")}


async def test_reeval_after_nachtragen_matches_case_with_approach_from_start() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        # Case A: Ansatz von Anfang an.
        a = await client.post("/triage", json=_VALID_PAYLOAD)
        assert a.status_code == 201
        a_body = a.json()

        # Case B: ohne Ansatz -> pending -> Ansatz nachtragen.
        b = await client.post("/triage", json=_without("implementation_approach"))
        assert b.status_code == 201
        b_id = b.json()["id"]

        reeval = await client.post(
            f"/cases/{b_id}/implementation-approach",
            json={"implementation_approach": _APPROACH},
            headers=_AUTH,
        )

    assert reeval.status_code == 200
    reeval_body = reeval.json()
    assert reeval_body["evaluation_pending"] is False
    # Die bewertungs-relevanten Felder muessen identisch sein -- gleicher
    # use_case -> gleiche Regel-Pipeline (ADR-0050).
    assert _score_relevant(reeval_body) == _score_relevant(a_body)


async def test_nachtragen_requires_admin() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        b = await client.post("/triage", json=_without("implementation_approach"))
        b_id = b.json()["id"]
        # Ohne API-Key -> 401 (require_admin).
        resp = await client.post(
            f"/cases/{b_id}/implementation-approach",
            json={"implementation_approach": _APPROACH},
        )
    assert resp.status_code == 401


async def test_nachtragen_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/cases/does-not-exist/implementation-approach",
            json={"implementation_approach": _APPROACH},
            headers=_AUTH,
        )
    assert resp.status_code == 404


# --- Deutsche 422-Feldtexte fuer die Pflichtfelder --------------------------


async def test_missing_required_fields_return_422_with_german_field_text() -> None:
    cases = {
        "evidence_level": "Evidenzlevel",
        "data_classification": "Datenschutzklasse",
        "adoption_type": "Verbindlichkeit der Nutzung",
    }
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        for field, needle in cases.items():
            resp = await client.post("/triage", json=_without(field))
            assert resp.status_code == 422, field
            detail = resp.json()["detail"]
            entry = next(e for e in detail if e["loc"][-1] == field)
            assert needle in entry["msg"], (field, entry["msg"])


async def test_missing_approach_does_not_trigger_422() -> None:
    # Gegenprobe: der Ansatz ist optional -> Weglassen ist KEIN Validierungsfehler.
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        resp = await client.post("/triage", json=_without("implementation_approach"))
    assert resp.status_code == 201


# --- Bewertungsabhaengige Endpoints im Vor-Bewertungs-Zustand -> 409 --------


async def test_report_on_pending_case_returns_409() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        b = await client.post("/triage", json=_without("implementation_approach"))
        b_id = b.json()["id"]
        resp = await client.post(f"/cases/{b_id}/report", headers=_AUTH)
    assert resp.status_code == 409


async def test_compliance_hints_on_pending_case_returns_409() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        b = await client.post("/triage", json=_without("implementation_approach"))
        b_id = b.json()["id"]
        resp = await client.post(f"/cases/{b_id}/compliance-hints", headers=_AUTH)
    assert resp.status_code == 409


# --- Case-Detail eines Vor-Bewertungs-Case ----------------------------------


async def test_case_detail_pending_flags_state_and_hides_triage() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        b = await client.post("/triage", json=_without("implementation_approach"))
        b_id = b.json()["id"]
        # Auch als Admin: keine Bewertung, aber expliziter Zustand.
        detail = await client.get(f"/cases/{b_id}", headers=_AUTH)

    assert detail.status_code == 200
    body = detail.json()
    assert body["evaluation_pending"] is True
    assert body["triage"] is None
    assert body["report"] is None


async def test_case_summary_lists_pending_flag() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        await client.post("/triage", json=_without("implementation_approach"))
        listing = await client.get("/cases", headers=_AUTH)

    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]["evaluation_pending"] is True
    assert rows[0]["zone"] is None

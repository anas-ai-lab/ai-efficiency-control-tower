"""Integrations-Tests fuer den zweistufigen Loeschpfad (ADR-0057, ADR-0038).

Stufe eins: POST /cases/{id}/trash (Papierkorb), POST /cases/{id}/restore,
GET /cases/trash. Stufe zwei: DELETE /cases/{id} -- unveraendert in Pfad,
Methode und Statuscode, aber nur noch aus dem Papierkorb heraus (sonst 409).

Methode: dependency_overrides mit EINEM gemeinsam genutzten TriageService
(geteilter InMemoryRepository), damit POST /triage und das nachfolgende DELETE
denselben Zustand sehen.
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


async def test_delete_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.delete("/cases/some-id")
    assert response.status_code == 401


async def test_delete_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.delete("/cases/does-not-exist", headers=_AUTH)
    assert response.status_code == 404


async def test_delete_existing_case_returns_204_and_removes_it() -> None:
    """Testfall 5 (Route-Haelfte): trash -> DELETE -> 204, Case ist weg."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
        assert created.status_code == 201
        case_id = created.json()["id"]

        trashed = await client.post(f"/cases/{case_id}/trash", headers=_AUTH)
        assert trashed.status_code == 204

        deleted = await client.delete(f"/cases/{case_id}", headers=_AUTH)
        assert deleted.status_code == 204

        # Die Zeile ist physisch weg -> GET /cases/{id} findet nichts mehr.
        gone = await client.get(f"/cases/{case_id}", headers=_AUTH)
        assert gone.status_code == 404


# ---------------------------------------------------------------------------
# Zweistufiges Loeschen -- Papierkorb (ADR-0057)
# ---------------------------------------------------------------------------


async def _create_case(client: AsyncClient) -> str:
    created = await client.post("/triage", json=_VALID_PAYLOAD, headers=_AUTH)
    assert created.status_code == 201
    case_id: str = created.json()["id"]
    return case_id


async def test_trash_endpoint_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/trash")
    assert response.status_code == 401


async def test_restore_endpoint_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/restore")
    assert response.status_code == 401


async def test_list_trash_without_key_returns_401() -> None:
    """Testfall 8: GET /cases/trash ist admin-only, kein Public-Zweig."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases/trash")
    assert response.status_code == 401


async def test_trash_route_is_not_swallowed_by_case_id_route() -> None:
    """ "/cases/trash" darf NICHT als case_id="trash" in der Detailroute landen
    (Registrierungs-Reihenfolge, siehe Kommentar in routes/cases.py)."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases/trash", headers=_AUTH)
    assert response.status_code == 200
    assert response.json() == []


async def test_trashed_case_disappears_from_list_and_appears_in_trash() -> None:
    """Testfall 1 (Route-Haelfte) + Papierkorb-Sicht mit deleted_at."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)

        trashed = await client.post(f"/cases/{case_id}/trash", headers=_AUTH)
        assert trashed.status_code == 204

        listed = await client.get("/cases", headers=_AUTH)
        assert [c["id"] for c in listed.json()] == []

        trash = await client.get("/cases/trash", headers=_AUTH)
        assert trash.status_code == 200
        rows = trash.json()
        assert [r["id"] for r in rows] == [case_id]
        assert rows[0]["deleted_at"] is not None


async def test_trashed_case_still_reachable_by_id() -> None:
    """Testfall 2 (Route-Haelfte): nur aus den Listen weg, nicht aus der DB."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await client.post(f"/cases/{case_id}/trash", headers=_AUTH)

        detail = await client.get(f"/cases/{case_id}", headers=_AUTH)
    assert detail.status_code == 200
    assert detail.json()["id"] == case_id


async def test_restore_brings_case_back_into_list() -> None:
    """Testfall 3 (Route-Haelfte)."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await client.post(f"/cases/{case_id}/trash", headers=_AUTH)

        restored = await client.post(f"/cases/{case_id}/restore", headers=_AUTH)
        assert restored.status_code == 204

        listed = await client.get("/cases", headers=_AUTH)
        assert [c["id"] for c in listed.json()] == [case_id]

        trash = await client.get("/cases/trash", headers=_AUTH)
        assert trash.json() == []


async def test_delete_without_trash_returns_409_and_keeps_case() -> None:
    """Testfall 4 (Route-Haelfte): Stufe zwei ohne Stufe eins -> 409."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)

        response = await client.delete(f"/cases/{case_id}", headers=_AUTH)
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "case_not_in_trash"

        # Der Case existiert unveraendert weiter.
        detail = await client.get(f"/cases/{case_id}", headers=_AUTH)
        assert detail.status_code == 200
        listed = await client.get("/cases", headers=_AUTH)
        assert [c["id"] for c in listed.json()] == [case_id]


async def test_restore_of_active_case_returns_409() -> None:
    """Testfall 6 (Route-Haelfte)."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)

        response = await client.post(f"/cases/{case_id}/restore", headers=_AUTH)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "case_not_in_trash"


async def test_restore_message_follows_lang_query() -> None:
    """Der code bleibt stabil, nur der anzeigbare Text folgt lang."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(f"/cases/{case_id}/restore?lang=en", headers=_AUTH)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "case_not_in_trash"
    assert "not in the trash" in response.json()["detail"]["message"]


async def test_trash_twice_returns_204_both_times() -> None:
    """Testfall 7 (Route-Haelfte): idempotent, kein 409 beim zweiten Aufruf."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)

        first = await client.post(f"/cases/{case_id}/trash", headers=_AUTH)
        second = await client.post(f"/cases/{case_id}/trash", headers=_AUTH)
        assert first.status_code == 204
        assert second.status_code == 204

        trash = await client.get("/cases/trash", headers=_AUTH)
        assert len(trash.json()) == 1


async def test_trash_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/does-not-exist/trash", headers=_AUTH)
    assert response.status_code == 404


async def test_restore_nonexistent_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/does-not-exist/restore", headers=_AUTH)
    assert response.status_code == 404

"""Tests fuer die Auth-Routen-Matrix (V4-P-Auth) und den globalen Exception-Handler.

Zwei Zugriffsstufen (SDR-0003): anonym (Einreichung, Ideen-Assistent,
Ideenliste, Case-Detail read-only) und admin (alles). require_admin akzeptiert
eine gueltige Session ODER den bestehenden X-API-Key -- dieser File deckt den
API-Key-Zweig und die Public/Admin-Trennung ab; die Session-Mechanik liegt in
test_auth_session.py.

Methode: app.dependency_overrides[get_settings] injiziert einen bekannten
Test-Key -- kein Env-Variable-Patching. create_app() pro Test: isolierte
FastAPI-Instanz ohne geteilten State.
"""

from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_retriever_port, get_settings
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.retriever import MockRetriever

TEST_API_KEY = "test-api-key-aect-2026"

# Ein Admin-Endpoint ohne Body/Case-Voraussetzung: die literale Read-Route
# /cases/similarity-pairs verlangt require_admin und braucht keinen angelegten
# Case (leere Liste bei leerem Repository) -- ideal fuer die Auth-Pruefung.
ADMIN_ENDPOINT = "/cases/similarity-pairs"

# Ein valider Einreichungs-Payload (V4-Schema) fuer den Public-Pfad POST /triage.
VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. Der Prozess "
        "bindet erhebliche Kapazitaet im Finance-Team."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch "
        "auslesen, Pflichtfelder erkennen und direkt in SAP befuellen. Ziel "
        "ist eine Reduktion der manuellen Bearbeitungszeit pro Vorgang."
    ),
    "example_process": (
        "Eingehende Rechnung von Lieferant X wird manuell gescannt und "
        "Betraege sowie Kostenstellen haendig abgetippt."
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


def _use_mock_retriever(app: FastAPI) -> None:
    """Expliziter Mock-Retriever-Pfad (V4-P2): resolve_retriever ist fail-loud
    und faellt nicht mehr still auf MockRetriever -- diese Auth-Tests brauchen
    keine echte Wissensbasis, also wird MockRetriever direkt injiziert."""
    app.dependency_overrides[get_retriever_port] = lambda: MockRetriever()


def _make_auth_app() -> FastAPI:
    """App mit konfiguriertem Test-API-Key (kein Admin-Passwort noetig fuer den
    API-Key-Zweig)."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key=TEST_API_KEY, chroma_host=""
    )
    _use_mock_retriever(app)
    return app


# ---------------------------------------------------------------------------
# Public-Routen: ohne Auth erreichbar
# ---------------------------------------------------------------------------


async def test_public_list_cases_without_auth_returns_200() -> None:
    """GET /cases (Ideenliste) ist public -- ohne X-API-Key 200."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases")
    assert response.status_code == 200
    assert response.json() == []


async def test_public_submit_triage_without_auth_returns_201() -> None:
    """POST /triage (Einreichung) ist public -- ohne X-API-Key 201."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.post("/triage", json=VALID_PAYLOAD)
    assert response.status_code == 201


async def test_public_auth_me_without_auth_returns_unauthenticated() -> None:
    """GET /auth/me ist public und meldet ohne Session/Key authenticated=false."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


# ---------------------------------------------------------------------------
# Admin-Routen: require_admin ueber den API-Key-Zweig
# ---------------------------------------------------------------------------


async def test_admin_endpoint_without_credentials_returns_401() -> None:
    """Admin-Route ohne Session UND ohne API-Key -> 401."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT)
    assert response.status_code == 401


async def test_admin_endpoint_with_wrong_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get(
            ADMIN_ENDPOINT, headers={"X-API-Key": "falscher-key"}
        )
    assert response.status_code == 401


async def test_admin_endpoint_with_correct_key_returns_200() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200


async def test_health_is_exempt_from_auth() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Auth: Response-Inhalt (kein Info-Leak)
# ---------------------------------------------------------------------------


async def test_401_response_has_detail_field() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT)
    assert "detail" in response.json()


async def test_401_response_does_not_leak_server_key() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": "wrong"})
    assert TEST_API_KEY not in response.text


# ---------------------------------------------------------------------------
# Auth: Server-seitig nicht konfiguriert (weder Key noch Passwort-Hash)
# ---------------------------------------------------------------------------


async def test_unconfigured_server_returns_503() -> None:
    """Weder AECT_API_KEY noch AECT_ADMIN_PASSWORD_HASH konfiguriert -> die
    Admin-Flaeche ist gar nicht eingerichtet: 503 (ehrliches "nicht
    betriebsbereit"), nicht 401."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="", admin_password_hash="", chroma_host=""
    )
    _use_mock_retriever(app)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": "irgendwas"})
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# Globaler Exception-Handler
# ---------------------------------------------------------------------------


async def test_global_exception_handler_returns_500_with_request_id() -> None:
    """Unbehandelte RuntimeError gibt 500 + request_id zurueck."""
    app = _make_auth_app()

    @app.get("/test-error", include_in_schema=False)
    async def _broken_route() -> dict[str, str]:
        raise RuntimeError("deliberater Testfehler")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/test-error")

    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Internal error"
    assert "request_id" in data
    assert isinstance(data["request_id"], str)


async def test_global_exception_handler_hides_error_details() -> None:
    """500-Response enthaelt weder Fehlermeldung noch Traceback."""
    app = _make_auth_app()

    @app.get("/test-leak", include_in_schema=False)
    async def _leaky_route() -> dict[str, str]:
        raise ValueError("interner Geheimwert")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/test-leak")

    assert "interner Geheimwert" not in response.text
    assert "Traceback" not in response.text
    assert "ValueError" not in response.text


# ---------------------------------------------------------------------------
# Auth: Key-Rotation (Phase G) -- weiterhin ueber require_admin
# ---------------------------------------------------------------------------

NEXT_API_KEY = "next-api-key-aect-2026"


def _make_rotation_app() -> FastAPI:
    """App mit zwei gleichzeitig gueltigen Keys (Rotation im Gange)."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key=TEST_API_KEY, api_key_next=NEXT_API_KEY, chroma_host=""
    )
    _use_mock_retriever(app)
    return app


async def test_rotation_accepts_primary_key() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_rotation_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200


async def test_rotation_accepts_next_key() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_rotation_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": NEXT_API_KEY})
    assert response.status_code == 200


async def test_rotation_rejects_key_matching_neither() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_rotation_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": "weder-noch"})
    assert response.status_code == 401


async def test_next_key_rejected_when_rotation_not_active() -> None:
    """Ohne AECT_API_KEY_NEXT (Default-App) ist NEXT_API_KEY kein gueltiger Key."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get(ADMIN_ENDPOINT, headers={"X-API-Key": NEXT_API_KEY})
    assert response.status_code == 401

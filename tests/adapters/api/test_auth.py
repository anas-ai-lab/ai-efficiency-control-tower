"""Tests fuer API-Key-Auth (require_api_key) und globalen Exception-Handler.

Methode: app.dependency_overrides[get_settings] injiziert einen bekannten
Test-Key -- kein Env-Variable-Patching, kein Monkeypatching.
create_app() pro Test: isolierte FastAPI-Instanz ohne geteilten State.
"""

from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings
from aect.adapters.api.settings import Settings

TEST_API_KEY = "test-api-key-aect-2026"


def _make_auth_app() -> FastAPI:
    """Erstellt App mit konfiguriertem Test-API-Key."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    return app


# ---------------------------------------------------------------------------
# Auth: Basis-Schutz
# ---------------------------------------------------------------------------


async def test_protected_endpoint_without_key_returns_401() -> None:
    """GET /cases ohne X-API-Key gibt 401 zurueck."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases")
    assert response.status_code == 401


async def test_protected_endpoint_with_wrong_key_returns_401() -> None:
    """GET /cases mit falschem X-API-Key gibt 401 zurueck."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": "falscher-key"})
    assert response.status_code == 401


async def test_protected_endpoint_with_correct_key_returns_200() -> None:
    """GET /cases mit korrektem X-API-Key gibt 200 zurueck."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200


async def test_health_is_exempt_from_auth() -> None:
    """/health ist auch ohne X-API-Key erreichbar."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Auth: Response-Inhalt
# ---------------------------------------------------------------------------


async def test_401_response_has_detail_field() -> None:
    """401-Response enthaelt 'detail'-Feld."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases")
    assert "detail" in response.json()


async def test_401_response_does_not_leak_server_key() -> None:
    """401-Response enthaelt nicht den echten API-Key."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": "wrong"})
    assert TEST_API_KEY not in response.text


async def test_valid_auth_returns_empty_list_initially() -> None:
    """GET /cases gibt leere Liste zurueck wenn keine Cases vorhanden."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": TEST_API_KEY})
    assert response.json() == []


async def test_cases_response_content_type_is_json() -> None:
    """GET /cases gibt application/json zurueck."""
    async with AsyncClient(
        transport=ASGITransport(app=_make_auth_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": TEST_API_KEY})
    assert "application/json" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Auth: Server-seitig nicht konfiguriert
# ---------------------------------------------------------------------------


async def test_unconfigured_server_returns_503() -> None:
    """Server ohne konfigurierten API-Key antwortet 503 (nicht betriebsbereit).

    Vorher 500: liess einen fehlenden AECT_API_KEY (kein .env, Fresh Clone)
    wie einen Server-Crash aussehen. 503 benennt die Ursache ehrlich --
    Service nicht konfiguriert, kein Fehler im Request und kein Bug.
    """
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key="")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": "irgendwas"})
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

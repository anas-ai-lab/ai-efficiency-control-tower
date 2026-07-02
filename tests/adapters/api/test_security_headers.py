"""Tests fuer SecurityHeadersMiddleware (F-026)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings
from aect.adapters.api.settings import Settings


async def test_api_routes_get_strict_security_headers() -> None:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")

    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    csp = resp.headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


async def test_docs_get_minimal_swagger_csp() -> None:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/docs")

    assert resp.status_code == 200
    csp = resp.headers["Content-Security-Policy"]
    assert "https://cdn.jsdelivr.net" in csp
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


async def test_error_responses_carry_security_headers() -> None:
    """Auch 401-Antworten tragen die Header (Middleware, nicht Route).

    Settings werden wie in allen anderen API-Tests ueberschrieben -- ohne
    Override haengt das Ergebnis von der Umgebung ab (kein .env -> 503
    statt 401, genau der Fresh-Clone-/CI-Fund vom 02.07.2026).
    """
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="test-api-key-aect-2026"
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/cases")  # ohne X-API-Key -> 401

    assert resp.status_code == 401
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


async def test_unconfigured_api_key_returns_503_with_security_headers() -> None:
    """Fehlende Server-Konfiguration -> bewusstes 503, kein 500.

    Settings(api_key="") erzwingt den Unkonfiguriert-Pfad unabhaengig davon,
    ob die Umgebung ein .env hat -- deterministisch lokal wie im CI.
    """
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key="")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/cases")

    assert resp.status_code == 503
    assert resp.json()["detail"] == "API key not configured on server"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"

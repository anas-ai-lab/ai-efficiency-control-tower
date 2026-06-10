"""Tests fuer GET /health.

ASGITransport: Requests werden in-process an die ASGI-App geleitet.
Kein Netzwerk, kein Server-Start, deterministisch.
create_app() statt globaler `app`: jeder Test bekommt eine frische Instanz
ohne geteilten Middleware- oder Router-State.
"""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app


async def test_health_returns_200() -> None:
    """GET /health gibt HTTP 200 zurueck."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


async def test_health_response_schema() -> None:
    """Response enthaelt status='ok' und version."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["version"], str)


async def test_health_content_type_is_json() -> None:
    """Response hat Content-Type application/json."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert "application/json" in response.headers["content-type"]


async def test_unknown_route_returns_404() -> None:
    """Unbekannte Route gibt 404, keinen 500."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/nonexistent")
    assert response.status_code == 404

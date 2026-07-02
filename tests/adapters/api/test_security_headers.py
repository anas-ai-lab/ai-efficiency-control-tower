"""Tests fuer SecurityHeadersMiddleware (F-026)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app


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
    """Auch 401/404-Antworten tragen die Header (Middleware, nicht Route)."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/cases")  # ohne X-API-Key -> 401/403

    assert resp.status_code in (401, 403, 422)
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"

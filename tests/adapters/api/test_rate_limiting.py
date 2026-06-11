"""Tests fuer Rate Limiting (slowapi) und Correlation-ID-Middleware.

Rate-Limit-Tests nutzen eindeutige API-Keys pro Test (uuid4).
Isolation: der Limiter zaehlt pro Key -- verschiedene Keys haben
getrennte Zaehler im In-Memory-Storage, kein Test-Interferenz.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from starlette.responses import Response

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings, get_triage_service
from aect.adapters.api.rate_limit import limiter
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config


def _make_app(api_key: str) -> FastAPI:
    """Hilfsfunktion: isolierte App mit gegebenem API-Key."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=api_key)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=InMemoryRepository(),
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
    )
    return app


# ---------------------------------------------------------------------------
# Correlation-ID-Middleware
# ---------------------------------------------------------------------------


async def test_response_contains_x_request_id_header() -> None:
    """Jeder Response enthaelt einen X-Request-ID-Header."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


async def test_x_request_id_is_unique_per_request() -> None:
    """Zwei Requests erhalten verschiedene request_ids."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        r1 = await client.get("/health")
        r2 = await client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


async def test_500_response_contains_request_id_from_context() -> None:
    """request_id in 500-Response stammt aus dem structlog-Kontext (nicht neuem UUID).

    Prueft dass CorrelationIDMiddleware und global_exception_handler
    dieselbe request_id verwenden -- sie muss im X-Request-ID-Header
    und im Response-Body identisch sein.
    """
    key = f"ctx-test-{uuid.uuid4()}"
    app = _make_app(key)

    @app.get("/test-ctx-error", include_in_schema=False)
    async def _broken() -> dict[str, str]:
        raise RuntimeError("kontext-test")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/test-ctx-error")

    data = response.json()
    assert response.status_code == 500
    assert "x-request-id" in response.headers
    assert data["request_id"] == response.headers["x-request-id"]


# ---------------------------------------------------------------------------
# Rate-Limit-Header
# ---------------------------------------------------------------------------


async def test_successful_cases_request_has_ratelimit_headers() -> None:
    """GET /cases mit gueltigem Key enthaelt X-RateLimit-Header."""
    key = f"rl-header-{uuid.uuid4()}"
    async with AsyncClient(
        transport=ASGITransport(app=_make_app(key)), base_url="http://test"
    ) as client:
        response = await client.get("/cases", headers={"X-API-Key": key})
    assert response.status_code == 200
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers


# ---------------------------------------------------------------------------
# 429 Too Many Requests
# ---------------------------------------------------------------------------


async def test_rate_limit_returns_429_after_limit_exceeded() -> None:
    """Mehr Requests als erlaubt gibt 429 zurueck.

    Test-Endpoint mit Limit 2/minute:
      Request 1 + 2: 200
      Request 3:     429
    Eindeutiger Key verhindert Zaehler-Interferenz mit anderen Tests.
    """
    key = f"rl-429-{uuid.uuid4()}"
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=key)

    @app.get("/test-rl-exceeded", include_in_schema=False)
    @limiter.limit("2/minute")
    async def _limited(request: Request, response: Response) -> dict[str, str]:
        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r1 = await client.get("/test-rl-exceeded", headers={"X-API-Key": key})
        r2 = await client.get("/test-rl-exceeded", headers={"X-API-Key": key})
        r3 = await client.get("/test-rl-exceeded", headers={"X-API-Key": key})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429


async def test_429_response_contains_retry_after_header() -> None:
    """429-Response enthaelt Retry-After-Header."""
    key = f"rl-retry-{uuid.uuid4()}"
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=key)

    @app.get("/test-rl-retry", include_in_schema=False)
    @limiter.limit("1/minute")
    async def _one_per_min(request: Request, response: Response) -> dict[str, str]:
        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/test-rl-retry", headers={"X-API-Key": key})
        response = await client.get("/test-rl-retry", headers={"X-API-Key": key})

    assert response.status_code == 429
    assert "retry-after" in response.headers

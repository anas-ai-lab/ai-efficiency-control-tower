"""Tests fuer GET /health, /health/live, /health/ready.

ASGITransport: Requests werden in-process an die ASGI-App geleitet.
Kein Netzwerk, kein Server-Start, deterministisch.
create_app() statt globaler `app`: jeder Test bekommt eine frische Instanz
ohne geteilten Middleware- oder Router-State.

Settings-Override-Pattern (app.dependency_overrides[get_settings]):
identisch zum 503-Fix (Commit b44b016) -- Settings(api_key="") erzwingt den
unkonfigurierten Pfad umgebungsunabhaengig, egal ob lokal ein .env liegt
oder nicht (Fresh-Clone-/CI-Determinismus).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings
from aect.adapters.api.settings import Settings


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


# ---------------------------------------------------------------------------
# /health/live -- identisch zu /health, aber ohne Alias-Umweg direkt getestet
# ---------------------------------------------------------------------------


async def test_health_live_returns_200() -> None:
    """GET /health/live gibt HTTP 200 zurueck, ohne jede Dependency-Pruefung."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["version"], str)


async def test_health_is_alias_for_health_live() -> None:
    """/health liefert dieselbe Antwort wie /health/live (Abwaertskompatibilitaet)."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        legacy = await client.get("/health")
        live = await client.get("/health/live")
    assert legacy.status_code == live.status_code == 200
    assert legacy.json() == live.json()


# ---------------------------------------------------------------------------
# /health/ready -- prueft API-Key, SQLite, ChromaDB
# ---------------------------------------------------------------------------


async def test_health_ready_returns_200_when_all_checks_pass() -> None:
    """Mock-Modus (kein AECT_DB_PATH, kein AECT_CHROMA_HOST) + gesetzter
    API-Key -> alle drei Checks trivial erfuellt -> 200."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="test-key", db_path="", chroma_host=""
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_ready_returns_503_when_api_key_unconfigured() -> None:
    """Settings(api_key="") -- identisches Pattern wie der 503-Fix-Test fuer
    require_api_key (test_auth.py::test_unconfigured_server_returns_503)."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="", db_path="", chroma_host=""
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"not_ready": ["api_key"]}


async def test_health_ready_returns_503_when_sqlite_unreachable(
    tmp_path: Path,
) -> None:
    """db_path zeigt auf ein nicht existierendes Verzeichnis -> sqlite3.connect()
    kann die Datei nicht anlegen -> OperationalError -> "sqlite" in not_ready."""
    unreachable_path = str(tmp_path / "does-not-exist" / "aect.db")
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="test-key", db_path=unreachable_path, chroma_host=""
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"not_ready": ["sqlite"]}


async def test_health_ready_returns_503_when_chromadb_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AECT_CHROMA_HOST gesetzt, aber kein Server erreichbar (Heartbeat
    schlaegt fehl) -> "chromadb" in not_ready. _check_chromadb wird gefakt
    statt echten Netzwerk-Timeout abzuwarten (Determinismus/Geschwindigkeit,
    analog dem gemockten Live-Pfad in test_dependencies.py)."""
    import aect.adapters.api.routes.health as health_module

    async def _fake_unreachable(host: str, port: int) -> bool:
        return False

    monkeypatch.setattr(health_module, "_check_chromadb", _fake_unreachable)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="test-key", db_path="", chroma_host="127.0.0.1", chroma_port=8001
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"not_ready": ["chromadb"]}


async def test_health_ready_lists_multiple_missing_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mehrere fehlgeschlagene Checks landen alle in not_ready (nicht nur der
    erste) -- api_key UND sqlite UND chromadb gleichzeitig kaputt."""
    import aect.adapters.api.routes.health as health_module

    async def _fake_unreachable(host: str, port: int) -> bool:
        return False

    monkeypatch.setattr(health_module, "_check_chromadb", _fake_unreachable)

    unreachable_path = str(tmp_path / "does-not-exist" / "aect.db")
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="",
        db_path=unreachable_path,
        chroma_host="127.0.0.1",
        chroma_port=8001,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert set(response.json()["not_ready"]) == {"api_key", "sqlite", "chromadb"}

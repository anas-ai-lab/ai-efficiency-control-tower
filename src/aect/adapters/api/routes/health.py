"""Health-Check-Endpoints fuer AECT.

Kein Auth -- Monitoring-Systeme muessen ohne API-Key pruefen koennen.

Liveness/Readiness-Split (Phase G Security-Haertung): Kubernetes/Container-
Apps-Semantik trennt zwei Fragen. "Laeuft der Prozess?" (Liveness) darf
NIEMALS von Abhaengigkeiten abhaengen -- sonst killt/restarted die
Orchestrierung einen gesunden Prozess nur weil z.B. Chroma kurz weg ist
(Restart-Loop-Falle). "Ist der Prozess bereit, Traffic zu bekommen?"
(Readiness) prueft genau das: fehlende Konfiguration oder unerreichbare
Abhaengigkeiten nehmen die Instanz aus dem Load-Balancer-Pool, ohne sie
neu zu starten.

/health bleibt als Alias auf /health/live bestehen (Breaking-Change-
Vermeidung -- bestehende Monitoring-Configs/Tests zeigen weiterhin dorthin).
"""

from __future__ import annotations

import sqlite3
from asyncio import to_thread
from pathlib import Path

import httpx
import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from aect.adapters.api.dependencies import get_settings
from aect.adapters.api.settings import Settings
from aect.adapters.sqlite.connection import connect

router = APIRouter(tags=["ops"])

logger = structlog.get_logger(__name__)

_VERSION = "1.2.0"

# Timeout fuer den Chroma-Heartbeat-Call: Readiness-Checks muessen schnell
# antworten (Orchestrierung pollt im Sekundentakt) -- ein haengender Chroma-
# Server soll den Check als "nicht bereit" beenden, nicht blockieren.
_CHROMA_HEARTBEAT_TIMEOUT_S = 2.0


class HealthResponse(BaseModel):
    """Response-Schema fuer GET /health und /health/live."""

    status: str
    version: str


@router.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    """Liveness: HTTP 200 solange der Prozess laeuft. Keine Dependency-Checks."""
    return HealthResponse(status="ok", version=_VERSION)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Alias auf /health/live (Abwaertskompatibilitaet, bestehende Configs)."""
    return await health_live()


def _check_sqlite_sync(db_path: str) -> bool:
    """Blockierender SELECT-1-Ping. Kein AECT_DB_PATH -> InMemoryRepository,
    keine SQLite-Abhaengigkeit zu pruefen -> trivial bereit."""
    if not db_path:
        return True
    try:
        with connect(Path(db_path)) as conn:
            conn.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False


async def _check_chromadb(chroma_host: str, chroma_port: int) -> bool:
    """Heartbeat-GET gegen die Chroma-REST-API. Kein AECT_CHROMA_HOST ->
    MockRetriever-Modus, kein Chroma-Server erwartet -> trivial bereit.

    Direkter httpx-Call statt chromadb.HttpClient(): haelt src/ im Mock-Pfad
    weiterhin chromadb-frei (Konvention aus dependencies.py) und ist der
    guenstigste moegliche Erreichbarkeits-Check.
    """
    if not chroma_host:
        return True
    url = f"http://{chroma_host}:{chroma_port}/api/v2/heartbeat"
    try:
        async with httpx.AsyncClient(timeout=_CHROMA_HEARTBEAT_TIMEOUT_S) as client:
            response = await client.get(url)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@router.get("/health/ready")
async def health_ready(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> JSONResponse:
    """Readiness: prueft API-Key-Konfiguration, SQLite- und ChromaDB-
    Erreichbarkeit. 200 wenn alle Checks bestehen, sonst 503 mit
    {"not_ready": [...]} -- listet explizit WAS fehlt, nicht nur "not ready"
    (macht den Zustand ohne Log-Zugriff diagnostizierbar).
    """
    checks = {
        "api_key": bool(settings.api_key),
        "sqlite": await to_thread(_check_sqlite_sync, settings.db_path),
        "chromadb": await _check_chromadb(settings.chroma_host, settings.chroma_port),
    }
    not_ready = [name for name, ok in checks.items() if not ok]
    if not_ready:
        logger.warning("readiness_check_failed", not_ready=not_ready)
        return JSONResponse(status_code=503, content={"not_ready": not_ready})
    return JSONResponse(status_code=200, content={"status": "ok"})

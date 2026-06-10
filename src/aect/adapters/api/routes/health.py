"""Health-Check-Endpoint fuer AECT.

Kein Auth -- Monitoring-Systeme muessen ohne API-Key pruefen koennen.
Phase B: DB-Ping ergaenzen, sobald SQLiteRepository existiert.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["ops"])


class HealthResponse(BaseModel):
    """Response-Schema fuer GET /health."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Gibt HTTP 200 zurueck, solange der Prozess laeuft."""
    return HealthResponse(status="ok", version="0.1.0")

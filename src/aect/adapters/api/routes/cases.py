"""Cases-Endpoint -- listet eingereichte Use Cases.

Security (aect-security-checklist v2.1, Phase B):
  Auth: require_api_key (X-API-Key-Header).
  Rate Limiting: 60/minute pro API-Key (lesender Zugriff, grosszuegiger).
  Schichttrennung: CaseSummary-Schema serialisiert nur was der Client braucht.

Phase C: GET /cases/{id} fuer Detail-Ansicht ergaenzen.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from starlette.responses import Response

from aect.adapters.api.dependencies import get_triage_service, require_api_key
from aect.adapters.api.rate_limit import limiter
from aect.application.service import TriageService

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseSummary(BaseModel):
    """Komprimiertes Case-Ergebnis fuer die Listansicht."""

    id: str
    submitted_at: datetime
    title: str


@router.get("", response_model=list[CaseSummary])
@limiter.limit("60/minute")
async def list_cases(
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_api_key),
) -> list[CaseSummary]:
    """Gibt alle eingereichten Use Cases als komprimierte Liste zurueck.

    request: Request -- von slowapi benoetigt fuer Rate-Limit-Key-Extraktion.
    response: Response -- von slowapi benoetigt fuer Header-Injektion.
    Auth: X-API-Key-Header (require_api_key).
    Rate Limit: 60 Requests/Minute pro API-Key.
    """
    return [
        CaseSummary(
            id=case.id,
            submitted_at=case.submitted_at,
            title=case.use_case.title,
        )
        for case in service.list_cases()
    ]

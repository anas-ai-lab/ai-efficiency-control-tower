"""Cases-Endpoint -- listet eingereichte Use Cases.

Alle Endpunkte dieses Moduls sind durch API-Key-Auth geschuetzt
(Depends(require_api_key)).

Separate CaseSummary-Schema: Domain-Modelle werden nicht direkt
serialisiert (Schichttrennung). Nur was der Client braucht.

Phase C: GET /cases/{id} fuer Detail-Ansicht ergaenzen.
Phase C: POST /triage kommt in routes/triage.py.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from aect.adapters.api.dependencies import get_triage_service, require_api_key
from aect.application.service import TriageService

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseSummary(BaseModel):
    """Komprimiertes Case-Ergebnis fuer die Listansicht."""

    id: str
    submitted_at: datetime
    title: str


@router.get("", response_model=list[CaseSummary])
async def list_cases(
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_api_key),
) -> list[CaseSummary]:
    """Gibt alle eingereichten Use Cases als komprimierte Liste zurueck.

    Auth: X-API-Key-Header erforderlich (require_api_key).
    Leere Liste wenn noch keine Cases eingereicht wurden.
    """
    return [
        CaseSummary(
            id=case.id,
            submitted_at=case.submitted_at,
            title=case.use_case.title,
        )
        for case in service.list_cases()
    ]

"""Cases-Endpoint -- listet eingereichte Use Cases.

Security (aect-security-checklist v2.1, Phase B):
  Auth: require_api_key (X-API-Key-Header).
  Rate Limiting: 60/minute pro API-Key (lesender Zugriff, grosszuegiger).
  Schichttrennung: CaseSummary-Schema serialisiert nur was der Client braucht.

Phase C: GET /cases/{id} fuer Detail-Ansicht ergaenzen.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
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


class SharpenedCaseResponse(BaseModel):
    """Original + geschaerfte Version eines Use Cases."""

    case_id: str
    original_title: str
    original_current_state: str
    original_desired_state: str
    sharpened_text: str
    prompt_version: str


@router.post("/{case_id}/sharpen", response_model=SharpenedCaseResponse)
@limiter.limit("10/minute")
async def sharpen_case(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_api_key),
) -> SharpenedCaseResponse:
    """Schaerft die Use-Case-Beschreibung eines bestehenden Cases via LLM.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: X-API-Key-Header (require_api_key).
    Rate Limit: 10/Minute -- enger als list_cases (60/min), da LLM-Endpoint
    (aect-security-checklist v2.1, Phase B: "LLM-Endpoints strenger").

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    sharpened = await service.sharpen_case(case_id)
    if sharpened is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return SharpenedCaseResponse(
        case_id=sharpened.case_id,
        original_title=sharpened.original_title,
        original_current_state=sharpened.original_current_state,
        original_desired_state=sharpened.original_desired_state,
        sharpened_text=sharpened.sharpened_text,
        prompt_version=sharpened.prompt_version,
    )

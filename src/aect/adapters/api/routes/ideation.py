"""POST /ideation -- erzeugt AI-Use-Case-Entwuerfe aus einer Problembeschreibung.

Ephemer (D16, ADR-0048): kein Case, keine Persistenz -- die Entwuerfe leben
nur in der Response. Anders als die /cases/{id}/*-LLM-Endpoints operiert dieser
Pfad nicht auf einem gespeicherten Case, sondern nimmt die Problembeschreibung
direkt im Body entgegen.

Security (aect-security-checklist v2.1):
  Auth: PUBLIC (V4-P-Auth) -- der Ideen-Assistent ist eine anonyme Kern-
    Faehigkeit der unteren Zugriffsstufe (SDR-0003), kein require_admin.
  Rate Limit: 10/minute -- so streng wie die uebrigen LLM-Endpoints
    (/sharpen, /propose-solution, /compliance-hints), da echter LLM-Call.
  Injection-Sanitization: flag-not-block (D21) im Service -- flagged_input
    macht das Ergebnis sichtbar, ohne die Anfrage abzulehnen.
  LLM-Output als untrusted: der Service validiert gegen IdeationResult; eine
    kaputte Antwort wird auf 502 gemappt (kein 500-Stack-Trace, OWASP LLM02).

Kein require_token_budget: dieser Endpoint hat keinen case_id-Pfadparameter
(die Token-Budget-Dependency schaetzt Tokens ueber einen persistierten Case).
Das 10/min-Rate-Limit ist die Mengengrenze fuer diesen ephemeren Pfad.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from aect.adapters.api.dependencies import get_triage_service
from aect.adapters.api.rate_limit import limiter
from aect.application.service import TriageService
from aect.application.structured_output import IdeationDraft, InvalidLLMOutputError

router = APIRouter(prefix="/ideation", tags=["ideation"])


class IdeationRequest(BaseModel):
    """Problembeschreibung fuer die Entwurfs-Generierung (P10).

    problem_description: min 20 (Substanz), max 2000 (Token-Flooding-Schutz,
    LLM10) -- konsistent mit den gebundenen Freitextfeldern von UseCaseInput.
    extra="forbid": kein unerwarteter Input (LLM10).
    """

    model_config = ConfigDict(extra="forbid")

    problem_description: str = Field(min_length=20, max_length=2000)


class IdeationResponse(BaseModel):
    """1-3 Use-Case-Entwuerfe + Injection-Flag (P10, ADR-0048).

    drafts: die Entwuerfe (IdeationDraft aus der Application-Schicht direkt
    wiederverwendet -- schon JSON-serialisierbar, analog SimilarityWarning in
    TriageResponse). flagged_input: True, wenn im Input ein Injection-Muster
    erkannt wurde (flag-not-block, D21) -- der Client sieht den Befund, die
    Antwort ist trotzdem valide.
    """

    drafts: list[IdeationDraft]
    flagged_input: bool


@router.post("", response_model=IdeationResponse)
@limiter.limit("10/minute")
async def generate_ideation(
    request: Request,
    response: Response,
    body: IdeationRequest,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
) -> IdeationResponse:
    """Erzeugt AI-Use-Case-Entwuerfe aus einer Problembeschreibung.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: PUBLIC (V4-P-Auth) -- anonymer Ideen-Assistent, kein require_admin.
    Rate Limit: 10/Minute -- LLM-Endpoint, analog /sharpen.

    Ephemer: kein Case wird angelegt (D16). extra='forbid' + Laengen-Bounds auf
    IdeationRequest -> 422 bei zu kurzem/langem/unbekanntem Input.

    Fehler-Mapping (kein Stack-Trace an den Client, OWASP LLM02):
    - LLM nach Retries nicht erreichbar (Connection/Timeout) -> 503.
    - LLM liefert kein valides Schema (InvalidLLMOutputError) -> 502.

    Raises:
        HTTPException 502: KI-Antwort war nicht verwertbar.
        HTTPException 503: KI-Dienst nicht erreichbar.
    """
    try:
        result, flagged = await service.ideate(body.problem_description)
    except InvalidLLMOutputError as exc:
        raise HTTPException(
            status_code=502,
            detail="KI-Antwort war nicht verwertbar -- bitte erneut versuchen.",
        ) from exc
    except (ConnectionError, TimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "KI-Dienst derzeit nicht erreichbar -- bitte spaeter erneut versuchen."
            ),
        ) from exc

    return IdeationResponse(drafts=list(result.drafts), flagged_input=flagged)

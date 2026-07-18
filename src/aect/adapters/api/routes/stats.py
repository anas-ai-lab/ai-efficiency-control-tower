"""GET /stats -- oeffentliche Portfolio-Kennzahlen fuer die Startseite (V4-P7).

Security (aect-security-checklist v2.1, V4-P-Auth):
  Auth: PUBLIC -- die Startseite ist ohne Login begehbar (SDR-0003). Die
  Kennzahlen sind bewusst aggregiert (nur Zaehler + eine Summe), keine
  Freitexte, keine Einzel-Case-Details -- kein Informations-Leck ueber das
  hinaus, was GET /cases ohnehin oeffentlich zeigt.
  Rate Limit: 60/Minute -- lesender Zugriff, analog GET /cases.

Kein LLM-Call, keine Persistenz-Aenderung: ein einziger Aggregations-Durchlauf
ueber die persistierten Cases (service.compute_stats()).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from starlette.responses import Response

from aect.adapters.api.dependencies import get_triage_service
from aect.adapters.api.rate_limit import limiter
from aect.application.service import TriageService

router = APIRouter(tags=["ops"])


class StatsResponse(BaseModel):
    """Aggregierte Portfolio-Kennzahlen (V4-P7).

    eingereicht/bewertet/umgesetzt: Funnel-Zaehler (siehe PortfolioStats).
    freigegeben: Cases mit Status APPROVED (freigegeben, aber noch nicht
    umgesetzt) -- eigener Zwischenschritt-Zaehler, unabhaengig von
    netto_nutzen_freigegeben_eur.
    netto_nutzen_freigegeben_eur: Summe der Netto-Nutzen ueber freigegebene
    (APPROVED) und umgesetzte (IMPLEMENTED) Cases. Decimal -> float, konsistent
    mit ROIResponse (JSON-Serialisierbarkeit).
    """

    model_config = ConfigDict(extra="forbid")

    eingereicht: int
    bewertet: int
    freigegeben: int
    umgesetzt: int
    netto_nutzen_freigegeben_eur: float


@router.get("/stats", response_model=StatsResponse)
@limiter.limit("60/minute")
async def get_stats(
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
) -> StatsResponse:
    """Gibt die aggregierten Portfolio-Kennzahlen fuer die Startseite zurueck.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: PUBLIC (V4-P-Auth). Rate Limit: 60/Minute (lesend, analog GET /cases).
    """
    stats = service.compute_stats()
    return StatsResponse(
        eingereicht=stats.eingereicht,
        bewertet=stats.bewertet,
        freigegeben=stats.freigegeben,
        umgesetzt=stats.umgesetzt,
        netto_nutzen_freigegeben_eur=float(stats.netto_nutzen_freigegeben_eur),
    )

"""POST /triage -- Use-Case-Einreichung und sofortige Triage.

Adapter-Schicht: UseCaseInput (Domain) wird direkt als Request-Body
verwendet -- adapter --> domain ist in Hexagonal erlaubt.
Response-Schemas (TriageResponse + Sub-Modelle) sind adapter-lokal:
Sie mappen Domain-Objekte auf JSON-serialisierbare Typen
(float statt Decimal, list statt tuple, str statt StrEnum).

Security (aect-security-checklist v2.1, Phase B):
  extra='forbid' auf UseCaseInput: kein unerwarteter Input (OWASP LLM10).
  max_length auf Freitextfeldern: Token-Flooding-Schutz (Phase A).
  Auth: require_api_key (X-API-Key-Header).
  Rate Limiting: 30/minute pro API-Key (limiter aus rate_limit.py).
  Response: keine Domain-Exceptions geleakt (globaler Handler in app.py).

Idempotency (aect-security-checklist v2.1, Phase B):
  Optionaler Header 'Idempotency-Key' (max. 200 Zeichen, Token-Flooding-
  Schutz). Bei wiederholtem Request mit demselben Key wird das urspruengliche
  Ergebnis zurueckgegeben (Status 200, Header 'Idempotent-Replay: true')
  statt den Use Case erneut zu verarbeiten. Ohne Header: unveraendertes
  Verhalten (Status 201, jeder Request erzeugt einen neuen Case).

  Grenze (bewusst, ADR-005): der Key wird nicht gegen den Payload validiert.
  Ein wiederverwendeter Key mit geaendertem Body liefert das alte Ergebnis,
  nicht 409/422.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel
from starlette.responses import Response

from aect.adapters.api.dependencies import (
    get_idempotency_store,
    get_triage_service,
    require_api_key,
)
from aect.adapters.api.rate_limit import limiter
from aect.application.models import SubmittedCase
from aect.application.ports.idempotency_store import IdempotencyStorePort
from aect.application.service import TriageService
from aect.domain.models import UseCaseInput

router = APIRouter(prefix="/triage", tags=["triage"])


# ---------------------------------------------------------------------------
# Response-Schemas (adapter-lokal)
# ---------------------------------------------------------------------------


class VorfilterResponse(BaseModel):
    passes: bool
    failed_criteria: list[str]
    details: dict[str, bool]


class ROIResponse(BaseModel):
    theoretical_potential_eur: float
    expected_benefit_eur: float
    net_expected_benefit_eur: float
    hours_per_year: float
    usage_factor: float
    evidence_factor: float
    license_cost_annual_eur: float
    passes_prefilter: bool
    prefilter_fail_reason: str | None


class RoutingResponse(BaseModel):
    recommendation: str
    confidence: str
    automation_signals: list[str]
    ai_signals: list[str]
    risk_flags: list[str]
    requires_human_review: bool


class FeasibilityResponse(BaseModel):
    is_feasible: bool
    flags: list[str]
    recommendation: str | None


class CompositeScoreResponse(BaseModel):
    complexity_score: int
    cost_score: int
    data_protection_score: int
    total: int
    effort_label: str


class ZoneResponse(BaseModel):
    base_zone: str
    final_zone: str
    handlungsdruck_elevated: bool
    reason: str


class TriageResponse(BaseModel):
    """Vollstaendiges Triage-Ergebnis fuer einen eingereichten Use Case.

    roi, composite und zone sind None wenn passed_vorfilter False ist.
    """

    id: str
    submitted_at: datetime
    title: str
    passed_vorfilter: bool
    is_actionable: bool
    vorfilter: VorfilterResponse
    routing: RoutingResponse
    feasibility: FeasibilityResponse
    roi: ROIResponse | None
    composite: CompositeScoreResponse | None
    zone: ZoneResponse | None


# ---------------------------------------------------------------------------
# Mapper: Domain -> Response-Schema
# ---------------------------------------------------------------------------


def _to_triage_response(case: SubmittedCase) -> TriageResponse:
    """Mappt SubmittedCase auf TriageResponse.

    Decimal -> float: JSON-Serialisierbarkeit.
    tuple[str, ...] -> list[str]: JSON-Serialisierbarkeit.
    StrEnum -> .value: explizite String-Darstellung.
    """
    r = case.result
    return TriageResponse(
        id=case.id,
        submitted_at=case.submitted_at,
        title=r.title,
        passed_vorfilter=r.passed_vorfilter,
        is_actionable=r.is_actionable,
        vorfilter=VorfilterResponse(
            passes=r.vorfilter.passes,
            failed_criteria=r.vorfilter.failed_criteria,
            details=r.vorfilter.details,
        ),
        routing=RoutingResponse(
            recommendation=r.routing.recommendation.value,
            confidence=r.routing.confidence,
            automation_signals=list(r.routing.automation_signals),
            ai_signals=list(r.routing.ai_signals),
            risk_flags=list(r.routing.risk_flags),
            requires_human_review=r.routing.requires_human_review,
        ),
        feasibility=FeasibilityResponse(
            is_feasible=r.feasibility.is_feasible,
            flags=[f.value for f in r.feasibility.flags],
            recommendation=r.feasibility.recommendation,
        ),
        roi=ROIResponse(
            theoretical_potential_eur=float(r.roi.theoretical_potential_eur),
            expected_benefit_eur=float(r.roi.expected_benefit_eur),
            net_expected_benefit_eur=float(r.roi.net_expected_benefit_eur),
            hours_per_year=r.roi.hours_per_year,
            usage_factor=r.roi.usage_factor,
            evidence_factor=r.roi.evidence_factor,
            license_cost_annual_eur=float(r.roi.license_cost_annual_eur),
            passes_prefilter=r.roi.passes_prefilter,
            prefilter_fail_reason=r.roi.prefilter_fail_reason,
        )
        if r.roi is not None
        else None,
        composite=CompositeScoreResponse(
            complexity_score=r.composite.complexity_score,
            cost_score=r.composite.cost_score,
            data_protection_score=r.composite.data_protection_score,
            total=r.composite.total,
            effort_label=r.composite.effort_label,
        )
        if r.composite is not None
        else None,
        zone=ZoneResponse(
            base_zone=r.zone.base_zone.value,
            final_zone=r.zone.final_zone.value,
            handlungsdruck_elevated=r.zone.handlungsdruck_elevated,
            reason=r.zone.reason,
        )
        if r.zone is not None
        else None,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("", response_model=TriageResponse, status_code=201)
@limiter.limit("30/minute")
async def submit_use_case(
    request: Request,
    response: Response,
    body: UseCaseInput,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    idempotency_store: IdempotencyStorePort = Depends(get_idempotency_store),  # noqa: B008
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", max_length=200
    ),
    _: str = Depends(require_api_key),
) -> TriageResponse:
    """Reicht einen Use Case ein und gibt das vollstaendige Triage-Ergebnis zurueck.

    request: Request -- von slowapi benoetigt fuer Rate-Limit-Key-Extraktion.
    Auth: X-API-Key-Header (require_api_key).
    Rate Limit: 30 Requests/Minute pro API-Key.
    Validation: extra='forbid' auf UseCaseInput -- unbekannte Felder -> 422.

    Idempotency: siehe Modul-Docstring. Bei Replay wird response.status_code
    auf 200 gesetzt und der Header 'Idempotent-Replay: true' ergaenzt.
    """
    if idempotency_key is not None:
        existing_case_id = idempotency_store.get(idempotency_key)
        if existing_case_id is not None:
            existing_case = service.get_case(existing_case_id)
            if existing_case is not None:
                response.status_code = 200
                response.headers["Idempotent-Replay"] = "true"
                return _to_triage_response(existing_case)

    case = service.submit_use_case(body)

    if idempotency_key is not None:
        idempotency_store.set(idempotency_key, case.id)

    return _to_triage_response(case)

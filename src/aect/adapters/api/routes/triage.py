"""POST /triage -- Use-Case-Einreichung und sofortige Triage.

Adapter-Schicht: UseCaseInput (Domain) wird direkt als Request-Body
verwendet -- adapter --> domain ist in Hexagonal erlaubt.
Response-Schemas (TriageResponse + Sub-Modelle) sind adapter-lokal:
Sie mappen Domain-Objekte auf JSON-serialisierbare Typen
(float statt Decimal, list statt tuple, str statt StrEnum).

Security (aect-security-checklist v2.1, Phase B):
  extra='forbid' auf UseCaseInput: kein unerwarteter Input (OWASP LLM10).
  max_length auf Freitextfeldern: Token-Flooding-Schutz (Phase A).
  Auth: PUBLIC (V4-P-Auth) -- anonyme Einreichung, kein require_admin.
  Rate Limiting: 30/minute pro Aufrufer (limiter aus rate_limit.py).
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

  Claim-then-fill (F-010): der Key wird atomar reserviert (claim), bevor
  verarbeitet wird -- get -> verarbeiten -> set war nicht atomar. Trifft ein
  Request auf einen reservierten, noch ungefuellten Key (paralleler Request
  in Arbeit), antwortet er 409 Conflict; der Client wiederholt spaeter und
  bekommt dann den Replay.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import Response

from aect.adapters.api.dependencies import (
    get_idempotency_store,
    get_triage_service,
)
from aect.adapters.api.rate_limit import limiter
from aect.application.models import SimilarityWarning, SubmittedCase
from aect.application.ports.idempotency_store import IdempotencyStorePort
from aect.application.service import TriageService
from aect.domain.explainability import TriageExplanation
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
    # Ersparnis pro Vorgang (Zeit_ist - Zeit_ai, V4). Kann <= 0 sein (eine Idee
    # darf auch Zeit kosten -- der Vorfilter meldet das dann mit Klartext-Grund).
    time_saved_per_case_hours: float
    usage_factor: float
    evidence_factor: float
    license_cost_annual_eur: float
    passes_prefilter: bool
    prefilter_fail_reason: str | None


class RoutingResponse(BaseModel):
    recommendation: str
    # Empfehlung als deutscher Satz (V4-P6) -- das Enum bleibt maschinenlesbar
    # daneben. Feste Argument-Reihenfolge: Stunden/Jahr -> Netto -> Aufwand ->
    # Datenschutzlage; Vorfilter-Fail nennt den Klartext-Grund.
    recommendation_text: str
    confidence: str
    automation_signals: list[str]
    ai_signals: list[str]
    risk_flags: list[str]
    requires_human_review: bool


class ScoreComponentResponse(BaseModel):
    """Eine Aufwandscore-Komponente mit deterministischer Begruendung (V4-P6)."""

    key: str
    label: str
    wert: int
    max: int
    begruendung: str


class ScoreBreakdownResponse(BaseModel):
    """Herkunft des Aufwandscores (V4-P6) -- Komponenten + Gesamtzeile + Machbarkeit.

    feasibility_score = 10 - total; feasibility_definition ist der zentrale
    Definitions-String (ueberall referenziert, auch in den Board-Daten).
    """

    components: list[ScoreComponentResponse]
    total: int
    max_total: int
    effort_label: str
    total_line: str
    feasibility_score: int
    feasibility_definition: str


class ConfidenceReasoningResponse(BaseModel):
    """Konfidenz als Begruendung statt Zahl (V4-P6): level + gruende."""

    level: str
    gruende: list[str]


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
    # Additiver Konfidenz-Score (ADR-0036): Abstand des composite_score zur
    # naechsten Zonengrenze. Aendert die Zonen-Entscheidung nicht, macht nur
    # die Grenzfall-Naehe sichtbar (known_limitations #2). Bleibt fuer
    # Rueckwaertskompatibilitaet erhalten; die menschenlesbare Fassung ist
    # confidence_reasoning (V4-P6).
    confidence_score: float
    confidence_label: str
    # Konfidenz als Begruendung (V4-P6): level + deterministische Gruende
    # (Evidenzlage, Zonengrenz-Naehe mit Kipp-Hebel).
    confidence_reasoning: ConfidenceReasoningResponse


class TriageResponse(BaseModel):
    """Vollstaendiges Triage-Ergebnis fuer einen eingereichten Use Case.

    roi, composite und zone sind None wenn passed_vorfilter False ist.

    evaluation_pending (V4.1, ADR-0050): der Case wurde ohne
    implementation_approach eingereicht -- er ist noch nicht bewertet. Dann sind
    vorfilter/routing/feasibility/roi/composite/zone/score_breakdown ALLE None
    und passed_vorfilter/is_actionable False. Die UI behandelt das wie den
    Vorfilter-Fail-Zustand ("noch nicht bewertet"). Ein Admin traegt den Ansatz
    ueber POST /cases/{id}/implementation-approach nach.
    """

    id: str
    submitted_at: datetime
    title: str
    evaluation_pending: bool = False
    passed_vorfilter: bool
    is_actionable: bool
    vorfilter: VorfilterResponse | None
    routing: RoutingResponse | None
    feasibility: FeasibilityResponse | None
    roi: ROIResponse | None
    composite: CompositeScoreResponse | None
    zone: ZoneResponse | None
    # Score-Herkunft (V4-P6): deterministische Begruendung je Aufwandscore-
    # Komponente + Machbarkeit. None bei Vorfilter-Fail (kein Composite).
    score_breakdown: ScoreBreakdownResponse | None
    # Dedup-Hinweis (L-3, ADR-0039) -- None, wenn kein aehnlicher Case existiert
    # oder die Pruefung uebersprungen wurde (Mock-Modus, erster Case).
    similarity_warning: SimilarityWarning | None = None


# ---------------------------------------------------------------------------
# Mapper: Domain -> Response-Schema
# ---------------------------------------------------------------------------


def _to_score_breakdown_response(
    explanation: TriageExplanation,
) -> ScoreBreakdownResponse | None:
    """Mappt die Score-Herkunft auf das API-Schema (None bei Vorfilter-Fail)."""
    breakdown = explanation.score_breakdown
    if breakdown is None:
        return None
    return ScoreBreakdownResponse(
        components=[
            ScoreComponentResponse(
                key=c.key,
                label=c.label,
                wert=c.wert,
                max=c.max,
                begruendung=c.begruendung,
            )
            for c in breakdown.components
        ],
        total=breakdown.total,
        max_total=breakdown.max_total,
        effort_label=breakdown.effort_label,
        total_line=breakdown.total_line,
        feasibility_score=breakdown.feasibility_score,
        feasibility_definition=breakdown.feasibility_definition,
    )


def _to_triage_response(
    case: SubmittedCase,
    explanation: TriageExplanation,
    similarity_warning: SimilarityWarning | None = None,
) -> TriageResponse:
    """Mappt SubmittedCase + Erklaerbarkeit auf TriageResponse.

    Decimal -> float: JSON-Serialisierbarkeit.
    tuple[str, ...] -> list[str]: JSON-Serialisierbarkeit.
    StrEnum -> .value: explizite String-Darstellung.
    explanation: deterministische Erklaerbarkeit (recommendation_text,
    score_breakdown, confidence) -- reine Read-Time-Projektion, kein LLM.
    similarity_warning: optionaler Dedup-Hinweis (ADR-0039), nur beim
    Erst-Intake gesetzt, nicht beim Idempotency-Replay.
    """
    r = case.result
    # Vor-Bewertungs-Zustand (ADR-0050): kein Umsetzungsansatz -> keine Regel-
    # Pipeline. Alle evaluativen Schichten None -- die UI zeigt "noch nicht
    # bewertet" (wie Vorfilter-Fail). Kein Zugriff auf r.vorfilter/r.routing/
    # r.feasibility (die hier None sind).
    if r.evaluation_pending:
        return TriageResponse(
            id=case.id,
            submitted_at=case.submitted_at,
            title=r.title,
            evaluation_pending=True,
            passed_vorfilter=False,
            is_actionable=False,
            vorfilter=None,
            routing=None,
            feasibility=None,
            roi=None,
            composite=None,
            zone=None,
            score_breakdown=None,
            similarity_warning=similarity_warning,
        )
    # Nicht-pending: die drei Schichten sind garantiert befuellt (evaluate_use_case
    # setzt sie immer, sobald ein Ansatz vorliegt) -- Invariante fuer mypy.
    assert r.vorfilter is not None
    assert r.routing is not None
    assert r.feasibility is not None
    confidence = explanation.confidence
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
            recommendation_text=explanation.recommendation_text,
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
            time_saved_per_case_hours=r.roi.time_saved_per_case_hours,
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
            confidence_score=r.zone.confidence_score,
            confidence_label=r.zone.confidence_label,
            confidence_reasoning=ConfidenceReasoningResponse(
                level=confidence.level,
                gruende=list(confidence.gruende),
            ),
        )
        if r.zone is not None and confidence is not None
        else None,
        score_breakdown=_to_score_breakdown_response(explanation),
        similarity_warning=similarity_warning,
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
) -> TriageResponse:
    """Reicht einen Use Case ein und gibt das vollstaendige Triage-Ergebnis zurueck.

    request: Request -- von slowapi benoetigt fuer Rate-Limit-Key-Extraktion.
    Auth: PUBLIC (V4-P-Auth) -- anonyme Einreichung ist eine Kern-Faehigkeit der
    unteren Zugriffsstufe (SDR-0003). Kein require_admin hier.
    Rate Limit: 30 Requests/Minute pro Aufrufer.
    Validation: extra='forbid' auf UseCaseInput -- unbekannte Felder -> 422.

    Idempotency: siehe Modul-Docstring. Bei Replay wird response.status_code
    auf 200 gesetzt und der Header 'Idempotent-Replay: true' ergaenzt.
    """
    if idempotency_key is not None:
        # Claim-then-fill (F-010): claim() reserviert den Key atomar, BEVOR
        # verarbeitet wird. Das fruehere get -> verarbeiten -> set war nicht
        # atomar: zwei parallele Requests mit demselben Key lasen beide
        # "kein Eintrag" (der erste await liegt vor dem set) und erzeugten
        # zwei Cases.
        claimed, existing_case_id = idempotency_store.claim(idempotency_key)
        if not claimed:
            if existing_case_id is None:
                # Platzhalter: ein paralleler Request mit demselben Key
                # verarbeitet gerade noch.
                raise HTTPException(
                    status_code=409,
                    detail="Request with this Idempotency-Key is already in progress",
                )
            existing_case = service.get_case(existing_case_id)
            if existing_case is not None:
                response.status_code = 200
                response.headers["Idempotent-Replay"] = "true"
                return _to_triage_response(
                    existing_case, service.explain_case(existing_case)
                )
            # Key gefuellt, aber Case geloescht (DSGVO Art. 17, ADR-0038):
            # neu verarbeiten; set() unten ueberschreibt mit der neuen ID.

    try:
        case = service.submit_use_case(body)
        # Dedup-Aehnlichkeitspruefung (L-3, ADR-0039) -- additiv, scheitert
        # nie hart.
        similarity_warning = await service.check_similarity(case)
    except BaseException:
        # Auch CancelledError (Client-Abbruch): der Platzhalter muss weg,
        # sonst antwortet jeder kuenftige Request mit diesem Key 409.
        if idempotency_key is not None:
            idempotency_store.release(idempotency_key)
        raise

    if idempotency_key is not None:
        idempotency_store.set(idempotency_key, case.id)

    return _to_triage_response(case, service.explain_case(case), similarity_warning)

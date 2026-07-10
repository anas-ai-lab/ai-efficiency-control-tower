"""Cases-Endpoint -- listet eingereichte Use Cases.

Security (aect-security-checklist v2.1, Phase B; V4-P-Auth):
  Auth-Matrix: PUBLIC sind GET /cases (Liste/Ideenliste) und GET /cases/{id}
  (vollstaendiger read-only Bewertungsstand -- E9/SDR-0003: der anonyme
  Einreicher liest den gespeicherten Stand seines Case, ohne etwas auszuloesen).
  Alle uebrigen Routen dieses Moduls verlangen require_admin (Session-Cookie
  ODER X-API-Key) -- inkl. der lesenden Admin-Sichten (similarity-pairs,
  monitoring, architecture-sketch GET) und aller POST-Trigger.
  Schichttrennung: CaseSummary (Liste) serialisiert nur Uebersichtsfelder;
  CaseDetailResponse (Detail) buendelt Triage-Ergebnis + Report read-only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from aect.adapters.api.dependencies import (
    get_triage_service,
    require_admin,
    require_token_budget,
)
from aect.adapters.api.rate_limit import limiter
from aect.adapters.api.routes.triage import TriageResponse, _to_triage_response
from aect.application.models import ArchitectureSketchResult, ReportResult
from aect.application.service import (
    CaseNotFoundError,
    NoProposalForSketchError,
    NoSharpeningDraftError,
    SharpeningNumberViolationError,
    TriageService,
)
from aect.application.structured_output import InvalidLLMOutputError
from aect.domain import CaseStatus, ReviewerDecision

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseSummary(BaseModel):
    """Komprimiertes Case-Ergebnis fuer die Portfolio-Listansicht.

    Genug Felder fuer eine Uebersichts-/Filter-Ansicht im Frontend, ohne den
    vollen Report je Case zu laden. zone/net_expected_benefit_eur/
    composite_total/hours_per_year sind None, wenn der Vorfilter nicht bestanden
    wurde -- exakt dieselbe None-Semantik wie TriageResponse (roi/composite/zone
    None bei Vorfilter-Fail, siehe routes/triage.py _to_triage_response).

    Filter und Sortierung sind bewusst Frontend-Konzern: die Datenmenge eines
    privaten Portfolio-Builds braucht keine serverseitige Pagination (v3).
    """

    id: str
    submitted_at: datetime
    title: str
    department: str
    status: str
    zone: str | None
    net_expected_benefit_eur: float | None
    composite_total: int | None
    hours_per_year: float | None
    is_actionable: bool


@router.get("", response_model=list[CaseSummary])
@limiter.limit("60/minute")
async def list_cases(
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
) -> list[CaseSummary]:
    """Gibt alle eingereichten Use Cases als komprimierte Liste zurueck.

    request: Request -- von slowapi benoetigt fuer Rate-Limit-Key-Extraktion.
    response: Response -- von slowapi benoetigt fuer Header-Injektion.
    Auth: PUBLIC (V4-P-Auth) -- die Ideenliste ist read-only fuer die untere
    Zugriffsstufe sichtbar (SDR-0003). CaseSummary serialisiert bewusst nur
    Uebersichtsfelder, keine Freitexte/Reports. Kein require_admin hier.
    Rate Limit: 60 Requests/Minute pro Aufrufer.

    Mapping-Muster identisch zu TriageResponse (routes/triage.py): Decimal ->
    float, StrEnum -> .value, None bei Vorfilter-Fail. Response bleibt eine
    Liste (kein Envelope) -- Abwaertskompatibilitaet.
    """
    summaries: list[CaseSummary] = []
    for case in service.list_cases():
        r = case.result
        summaries.append(
            CaseSummary(
                id=case.id,
                submitted_at=case.submitted_at,
                title=case.use_case.title,
                department=case.use_case.department,
                status=case.status.value,
                zone=r.zone.final_zone.value if r.zone is not None else None,
                net_expected_benefit_eur=(
                    float(r.roi.net_expected_benefit_eur) if r.roi is not None else None
                ),
                composite_total=(
                    r.composite.total if r.composite is not None else None
                ),
                hours_per_year=r.roi.hours_per_year if r.roi is not None else None,
                is_actionable=r.is_actionable,
            )
        )
    return summaries


class SimilarityPairResponse(BaseModel):
    """Ein Paar aehnlicher Cases fuer die Dedup-View (P9, ADR-0039).

    case_a/case_b sind deterministisch nach id sortiert (case_a_id < case_b_id).
    similarity_score: Cosinus-Aehnlichkeit [0.0, 1.0], 4 Nachkommastellen.
    suggest_combine: True ab der hoeheren Schwelle (>= 0.90).
    extra="forbid": strikter Vertrag (Paragraph 3.5), konsistent mit den
    uebrigen Schemas dieses Moduls.
    """

    model_config = ConfigDict(extra="forbid")

    case_a_id: str
    case_a_title: str
    case_b_id: str
    case_b_title: str
    similarity_score: float
    suggest_combine: bool


class SimilarityPairsResponse(BaseModel):
    """Aggregierte Dedup-Beziehungen ueber alle Cases (P9).

    pairs: absteigend nach score (deterministisch). cases_without_embedding:
    Anzahl Cases ohne Embedding (Embedder beim Intake nicht verfuegbar) --
    fliessen nicht in die Paarbildung ein, der Zaehler macht die Luecke sichtbar.
    """

    model_config = ConfigDict(extra="forbid")

    pairs: list[SimilarityPairResponse]
    cases_without_embedding: int


# Routing-Reihenfolge (FastAPI matcht in Registrierungs-Reihenfolge): die
# literale Route "/cases/similarity-pairs" steht bewusst VOR der parametrisierten
# GET "/cases/{case_id}"-Detailroute (unten), sonst wuerde "/similarity-pairs"
# als case_id="similarity-pairs" dort landen.
@router.get("/similarity-pairs", response_model=SimilarityPairsResponse)
@limiter.limit("60/minute")
async def list_similarity_pairs(
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> SimilarityPairsResponse:
    """Gibt alle Dedup-Beziehungen zwischen persistierten Cases zurueck (P9).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 60/Minute -- lesender Zugriff, analog GET /cases und
    GET /cases/{id}/monitoring.

    Read-only: kein Schreiben, kein LLM-Call. Nutzt dieselbe Cosinus-/Schwellen-
    Logik wie die Intake-Dedup-Pruefung (application/service.py).
    """
    result = await service.list_similarity_pairs()
    return SimilarityPairsResponse(
        pairs=[
            SimilarityPairResponse(
                case_a_id=pair.case_a_id,
                case_a_title=pair.case_a_title,
                case_b_id=pair.case_b_id,
                case_b_title=pair.case_b_title,
                similarity_score=pair.similarity_score,
                suggest_combine=pair.suggest_combine,
            )
            for pair in result.pairs
        ],
        cases_without_embedding=result.cases_without_embedding,
    )


@router.delete("/{case_id}", status_code=204)
@limiter.limit("10/minute")
async def delete_case(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> Response:
    """Loescht einen Case kaskadiert (DSGVO Art. 17, ADR-0038).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- schreibender/loeschender Zugriff, analog den
    LLM-Endpoints streng gehalten.

    204 No Content bei Erfolg. CaseNotFoundError aus dem Service wird auf 404
    gemappt (HTTP-Exceptions in der Adapter-Schicht, ADR-0004).

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    try:
        await service.delete_case(case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    return Response(status_code=204)


class DecisionRequest(BaseModel):
    """Freigabe-/Ablehnungsentscheidung fuer einen Case (Human-in-the-Loop,
    minimaler Decision-Record -- ADR-0043, bewusst kein Multi-User-Reviewer-
    Workflow mit Rollen).

    decision: nur "approved"/"rejected" ueber diesen Endpoint setzbar --
    PENDING ist ausschliesslich der Ausgangszustand vor jeder Entscheidung,
    kein gueltiger Request-Wert (kein Zurueck-auf-PENDING via API).
    note: optionale Begruendung. extra="forbid" + max_length konsistent mit
    den uebrigen Freitextfeldern (Token-Flooding-Schutz, aect-security-
    checklist v2.1 Phase A).
    """

    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=2000)


class DecisionResponse(BaseModel):
    """Aktueller Entscheidungs-Zustand eines Case nach POST /decision."""

    case_id: str
    reviewer_decision: str
    reviewer_note: str | None
    decided_at: datetime | None


@router.post("/{case_id}/decision", response_model=DecisionResponse)
@limiter.limit("10/minute")
async def record_decision(
    case_id: str,
    body: DecisionRequest,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> DecisionResponse:
    """Setzt eine Freigabe-/Ablehnungsentscheidung fuer einen bestehenden Case.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key, inkl. Key-Rotation).
    Rate Limit: 10/Minute -- schreibender Zugriff, analog DELETE /cases/{id}.

    Ueberschreiben einer bestehenden Entscheidung ist erlaubt (Korrektur-Fall,
    kein Bug) -- decided_at wird bei jedem Aufruf aktualisiert.

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    case = await service.record_decision(
        case_id, ReviewerDecision(body.decision), body.note
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return DecisionResponse(
        case_id=case.id,
        reviewer_decision=case.reviewer_decision.value,
        reviewer_note=case.reviewer_note,
        decided_at=case.decided_at,
    )


class StatusUpdateRequest(BaseModel):
    """Neuer Lifecycle-Status fuer einen Case (Lifecycle-ADR).

    status: einer der sieben CaseStatus-Werte. Bewusst keine Transitions-Matrix
    -- jeder Zustand ist aus jedem setzbar (menschliche Autoritaet in einem
    Single-User-Build). APPROVED/REJECTED sind hier ebenfalls setzbar, werden
    aber zusaetzlich durch POST /decision gesetzt (Kopplung an ReviewerDecision,
    ADR-0043).
    extra="forbid": konsistent mit DecisionRequest (Eingabe-Disziplin, aect-
    security-checklist v2.1 Phase A).
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "submitted",
        "in_review",
        "approved",
        "already_exists",
        "integrated",
        "rejected",
        "implemented",
    ]


class StatusUpdateResponse(BaseModel):
    """Aktueller Lifecycle-Status eines Case nach POST /status."""

    case_id: str
    status: str
    updated_at: datetime | None


@router.post("/{case_id}/status", response_model=StatusUpdateResponse)
@limiter.limit("10/minute")
async def update_status(
    case_id: str,
    body: StatusUpdateRequest,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> StatusUpdateResponse:
    """Setzt den Lifecycle-Status eines bestehenden Cases (Lifecycle-ADR).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- schreibender Zugriff, analog POST /decision und
    DELETE /cases/{id}.

    Kein LLM-Call -- Token-Budget wird hier nicht geprueft (analog /decision).

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    case = await service.update_status(case_id, CaseStatus(body.status))
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return StatusUpdateResponse(
        case_id=case.id,
        status=case.status.value,
        updated_at=case.status_updated_at,
    )


class MonitoringNoteRequest(BaseModel):
    """Neue Monitoring-Notiz fuer die Zeitleiste eines Case (Monitoring-ADR).

    note: Pflicht-Freitext (min 1, max 2000 -- Substanz + Token-Flooding-Schutz,
    aect-security-checklist v2.1 Phase A). extra="forbid" konsistent mit den
    uebrigen Request-Schemas.
    """

    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=1, max_length=2000)


class MonitoringEntryResponse(BaseModel):
    """Ein append-only Monitoring-Eintrag (Monitoring-ADR).

    status_snapshot: der Case-Status zum Zeitpunkt des Eintrags (Momentaufnahme,
    kein Live-Verweis).
    """

    id: str
    case_id: str
    created_at: datetime
    note: str
    status_snapshot: str


@router.post(
    "/{case_id}/monitoring",
    response_model=MonitoringEntryResponse,
    status_code=201,
)
@limiter.limit("10/minute")
async def add_monitoring_note(
    case_id: str,
    body: MonitoringNoteRequest,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> MonitoringEntryResponse:
    """Haengt eine Monitoring-Notiz an die Zeitleiste eines bestehenden Cases.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- schreibender Zugriff, analog POST /decision und
    /status.

    201 Created bei Erfolg (ein neuer Eintrag entsteht). Kein LLM-Call.

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    entry = await service.add_monitoring_note(case_id, body.note)
    if entry is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return MonitoringEntryResponse(
        id=entry.id,
        case_id=entry.case_id,
        created_at=entry.created_at,
        note=entry.note,
        status_snapshot=entry.status_snapshot,
    )


@router.get(
    "/{case_id}/monitoring",
    response_model=list[MonitoringEntryResponse],
)
@limiter.limit("60/minute")
async def list_monitoring(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> list[MonitoringEntryResponse]:
    """Gibt die Monitoring-Zeitleiste eines Case zurueck (chronologisch aufsteigend).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 60/Minute -- lesender Zugriff, analog GET /cases.

    Leere Liste, wenn der Case existiert aber keine Eintraege hat. 404, wenn der
    Case selbst nicht existiert (Service unterscheidet beide Faelle).

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    entries = await service.list_monitoring(case_id)
    if entries is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return [
        MonitoringEntryResponse(
            id=entry.id,
            case_id=entry.case_id,
            created_at=entry.created_at,
            note=entry.note,
            status_snapshot=entry.status_snapshot,
        )
        for entry in entries
    ]


class SharpenSuggestionResponse(BaseModel):
    """Ein Verbesserungsvorschlag mit Feldbezug und Hebel (V4).

    bezugsfeld: Name des Case-Feldes (CaseField.value), auf das der Vorschlag
    zielt -- das Frontend (V4-P7) verlinkt daran das Formularfeld.
    hebel: welche Bewertungsgroesse sich wie veraendert.
    """

    bezugsfeld: str
    vorschlag: str
    hebel: str


class SharpenedCaseResponse(BaseModel):
    """Original + geschaerfte Fassung eines Use Cases (V4, Draft/Accept-Flow).

    Das Ergebnis ist ein Entwurf (sharpening_draft) -- es ueberschreibt nichts
    am Case. Der Client baut daraus die Diff-Ansicht (Original feldweise neben
    der geschaerften Fassung) und uebernimmt/verwirft via /sharpen/accept bzw.
    /sharpen/reject. Erfindet die KI Zahlen oder verletzt sie das Schema (auch
    nach einem Retry), antwortet die Route mit 422 -- es gibt keine
    Teil-/Degradations-Antwort mehr.
    """

    case_id: str
    original_title: str
    original_current_state: str
    original_desired_state: str
    sharpened_title: str
    sharpened_current_state: str
    sharpened_desired_state: str
    improvement_suggestions: list[SharpenSuggestionResponse]
    prompt_version: str


class SharpeningActionResponse(BaseModel):
    """Bestaetigung fuer accept/reject eines Schaerfungs-Drafts (V4)."""

    case_id: str
    status: str


@router.post("/{case_id}/sharpen", response_model=SharpenedCaseResponse)
@limiter.limit("10/minute")
async def sharpen_case(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
    __: None = Depends(require_token_budget),
) -> SharpenedCaseResponse:
    """Erzeugt einen Schaerfungs-Entwurf fuer einen bestehenden Case via LLM.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- enger als list_cases (60/min), da LLM-Endpoint
    (aect-security-checklist v2.1, Phase B: "LLM-Endpoints strenger").
    Token-Budget: require_token_budget prueft VOR dem LLM-Call das
    stuendliche Token-Budget des API-Keys (Phase G).

    Draft: das Ergebnis wird als sharpening_draft persistiert, ueberschreibt
    NICHTS am Case. Uebernahme via /sharpen/accept.

    Fehler-Mapping (kein Stack-Trace an den Client, OWASP LLM02):
    - Case fehlt -> 404.
    - KI erfindet Zahlen (auch nach Retry) -> 422 mit Violation-Liste.
    - KI-Antwort verletzt das Schaerfungs-Schema (auch nach Retry) -> 422.

    Raises:
        HTTPException 404: case_id existiert nicht.
        HTTPException 422: KI-Antwort erfindet Zahlen oder verletzt das Schema.
        HTTPException 429: Token-Budget des API-Keys erschoepft.
    """
    try:
        sharpened = await service.sharpen_case(case_id)
    except SharpeningNumberViolationError as exc:
        # Die KI hat Zahlen erfunden, die nicht im Original stehen -- auch der
        # Retry hat sie nicht entfernt. 422 (der LLM-Call gelang, der Inhalt ist
        # unverwertbar), die Violation-Liste hilft dem Nutzer beim Nachjustieren.
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "invented_numbers",
                "message": (
                    "Die Schaerfung enthielt Zahlen, die nicht im Original "
                    "stehen, auch nach einem Korrektur-Versuch."
                ),
                "violations": exc.violations,
            },
        ) from exc
    except InvalidLLMOutputError as exc:
        # Schema-Verstoss (z. B. fehlendes bezugsfeld/hebel), auch nach Retry.
        # str(exc) traegt nur loc+type je Fehler (H-031), nie LLM-Rohtext.
        raise HTTPException(
            status_code=422,
            detail=f"KI-Antwort verletzt das Schaerfungs-Schema: {exc}",
        ) from exc

    if sharpened is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return SharpenedCaseResponse(
        case_id=sharpened.case_id,
        original_title=sharpened.original_title,
        original_current_state=sharpened.original_current_state,
        original_desired_state=sharpened.original_desired_state,
        sharpened_title=sharpened.sharpened_title,
        sharpened_current_state=sharpened.sharpened_current_state,
        sharpened_desired_state=sharpened.sharpened_desired_state,
        improvement_suggestions=[
            SharpenSuggestionResponse(
                bezugsfeld=s.bezugsfeld.value, vorschlag=s.vorschlag, hebel=s.hebel
            )
            for s in sharpened.improvement_suggestions
        ],
        prompt_version=sharpened.prompt_version,
    )


@router.post("/{case_id}/sharpen/accept", response_model=SharpeningActionResponse)
@limiter.limit("10/minute")
async def accept_sharpening(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> SharpeningActionResponse:
    """Uebernimmt den offenen Schaerfungs-Draft in die regulaeren Felder (V4).

    Kein LLM-Call (nur Persistenz) -> kein Token-Budget noetig.
    Auth: require_admin (Session ODER X-API-Key). Rate Limit: 10/Minute (Schreib-Endpoint).

    Raises:
        HTTPException 404: case_id existiert nicht.
        HTTPException 409: kein offener Draft (nichts zu uebernehmen).
    """
    try:
        updated = await service.accept_sharpening(case_id)
    except NoSharpeningDraftError as exc:
        raise HTTPException(
            status_code=409,
            detail="Kein offener Schaerfungs-Entwurf fuer diesen Case.",
        ) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return SharpeningActionResponse(case_id=case_id, status="accepted")


@router.post("/{case_id}/sharpen/reject", response_model=SharpeningActionResponse)
@limiter.limit("10/minute")
async def reject_sharpening(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> SharpeningActionResponse:
    """Verwirft den offenen Schaerfungs-Draft (V4) -- leert sharpening_draft.

    Kein LLM-Call -> kein Token-Budget noetig.
    Auth: require_admin (Session ODER X-API-Key). Rate Limit: 10/Minute (Schreib-Endpoint).

    Raises:
        HTTPException 404: case_id existiert nicht.
        HTTPException 409: kein offener Draft (nichts zu verwerfen).
    """
    try:
        updated = await service.reject_sharpening(case_id)
    except NoSharpeningDraftError as exc:
        raise HTTPException(
            status_code=409,
            detail="Kein offener Schaerfungs-Entwurf fuer diesen Case.",
        ) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return SharpeningActionResponse(case_id=case_id, status="rejected")


class SolutionProposalResponse(BaseModel):
    """Stack-passender Loesungsvorschlag fuer einen Use Case (Skeleton)."""

    case_id: str
    proposal_text: str
    prompt_version: str


@router.post("/{case_id}/propose-solution", response_model=SolutionProposalResponse)
@limiter.limit("10/minute")
async def propose_solution(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
    __: None = Depends(require_token_budget),
) -> SolutionProposalResponse:
    """Skizziert einen Loesungsansatz fuer einen bestehenden Case via LLM.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- LLM-Endpoint, analog /sharpen
    (aect-security-checklist v2.1, Phase B: "LLM-Endpoints strenger").
    Token-Budget: require_token_budget prueft VOR dem LLM-Call das
    stuendliche Token-Budget des API-Keys (Phase G).

    Skeleton (Tag 36, Phase C): v1-Prompt nennt bewusst keine konkreten
    Zielplattformen -- Stack-Grounding via RAG folgt Phase D.

    Raises:
        HTTPException 404: case_id existiert nicht.
        HTTPException 429: Token-Budget des API-Keys erschoepft.
    """
    proposal = await service.propose_solution(case_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return SolutionProposalResponse(
        case_id=proposal.case_id,
        proposal_text=proposal.proposal_text,
        prompt_version=proposal.prompt_version,
    )


class ComplianceCitationResponse(BaseModel):
    """Eine einzelne Quellenangabe -- Compliance-Hinweis-Endpoint UND
    /report (ADR-0026). Vor BusinessSummaryResponse definiert, damit
    letztere sie referenzieren kann."""

    number: int
    source_id: str
    citation: str
    url: str | None


class ReportRequest(BaseModel):
    """Optionale LLM-Narrative fuer den Report -- Override der Persistenz.

    Tag 42 (ADR-0012): generate_report() liest sharpened_text/proposal_text
    standardmaessig aus dem persistierten SubmittedCase (gefuellt durch
    /sharpen bzw. /propose-solution). Felder hier ueberschreiben den
    persistierten Wert, z. B. fuer eine Vorschau ohne erneuten Persist.
    extra="forbid" + max_length: aect-security-checklist v2.1 Phase A
    (Token-Flooding-Schutz, LLM10) -- gilt als generelle Eingabe-Disziplin
    auch fuer Felder ohne direkten LLM-Call.

    Kein Override-Feld fuer Compliance-Hinweise (ADR-0026) -- siehe
    application/service.py generate_report()-Docstring.
    """

    model_config = ConfigDict(extra="forbid")

    sharpened_text: str | None = Field(default=None, max_length=5000)
    proposal_text: str | None = Field(default=None, max_length=5000)


class BusinessSummaryResponse(BaseModel):
    """Entscheider-Schicht des Reports.

    compliance_hint_text/compliance_citations (ADR-0026): aus dem
    persistierten compliance_hints_json gelesen, kein Override moeglich
    (siehe ReportRequest-Docstring).

    reviewer_decision/reviewer_note/decided_at (ADR-0043): aktueller
    Human-in-the-Loop-Entscheidungs-Zustand, macht POST /decision-Ergebnisse
    sichtbar, ohne einen zweiten Endpoint abzufragen.
    """

    title: str
    zone: str | None
    is_actionable: bool
    recommendation: str
    expected_benefit_eur: float | None
    summary_text: str
    sharpened_text: str | None
    compliance_hint_text: str | None
    compliance_citations: list[ComplianceCitationResponse]
    reviewer_decision: str
    reviewer_note: str | None
    decided_at: datetime | None


class TechnicalDetailResponse(BaseModel):
    """Reviewer-Schicht des Reports."""

    passed_vorfilter: bool
    vorfilter_failed_criteria: list[str]
    composite_total: int | None
    composite_effort_label: str | None
    feasibility_flags: list[str]
    feasibility_recommendation: str | None
    automation_signals: list[str]
    ai_signals: list[str]
    risk_flags: list[str]
    requires_human_review: bool
    roi_theoretical_potential_eur: float | None
    roi_net_expected_benefit_eur: float | None
    proposal_text: str | None


class ReportResponse(BaseModel):
    """Zweischichtiger Report -- striktes JSON (Projekt-Anforderung)."""

    case_id: str
    business_summary: BusinessSummaryResponse
    technical_detail: TechnicalDetailResponse


def _to_report_response(report: ReportResult) -> ReportResponse:
    """Mappt das Application-ReportResult auf das API-Schema.

    Reine Serialisierung (Decimal->float via Application-Schicht, StrEnum->str)
    -- kein Berechnungs- oder LLM-Pfad. Von POST /report (Trigger-Kompatibilitaet)
    UND vom public GET /cases/{id} (read-only) wiederverwendet.
    """
    return ReportResponse(
        case_id=report.case_id,
        business_summary=BusinessSummaryResponse(
            title=report.business_summary.title,
            zone=report.business_summary.zone,
            is_actionable=report.business_summary.is_actionable,
            recommendation=report.business_summary.recommendation,
            expected_benefit_eur=report.business_summary.expected_benefit_eur,
            summary_text=report.business_summary.summary_text,
            sharpened_text=report.business_summary.sharpened_text,
            compliance_hint_text=report.business_summary.compliance_hint_text,
            compliance_citations=[
                ComplianceCitationResponse(
                    number=c.number,
                    source_id=c.source_id,
                    citation=c.citation,
                    url=c.url,
                )
                for c in report.business_summary.compliance_citations
            ],
            reviewer_decision=report.business_summary.reviewer_decision,
            reviewer_note=report.business_summary.reviewer_note,
            decided_at=report.business_summary.decided_at,
        ),
        technical_detail=TechnicalDetailResponse(
            passed_vorfilter=report.technical_detail.passed_vorfilter,
            vorfilter_failed_criteria=report.technical_detail.vorfilter_failed_criteria,
            composite_total=report.technical_detail.composite_total,
            composite_effort_label=report.technical_detail.composite_effort_label,
            feasibility_flags=report.technical_detail.feasibility_flags,
            feasibility_recommendation=report.technical_detail.feasibility_recommendation,
            automation_signals=report.technical_detail.automation_signals,
            ai_signals=report.technical_detail.ai_signals,
            risk_flags=report.technical_detail.risk_flags,
            requires_human_review=report.technical_detail.requires_human_review,
            roi_theoretical_potential_eur=report.technical_detail.roi_theoretical_potential_eur,
            roi_net_expected_benefit_eur=report.technical_detail.roi_net_expected_benefit_eur,
            proposal_text=report.technical_detail.proposal_text,
        ),
    )


@router.post("/{case_id}/report", response_model=ReportResponse)
@limiter.limit("30/minute")
async def get_report(
    case_id: str,
    request: Request,
    response: Response,
    body: ReportRequest | None = None,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> ReportResponse:
    """Erstellt den zweischichtigen Report fuer einen bestehenden Case.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 30/Minute -- kein LLM-Call (Regel-Schicht), aber Request-Body
    -- zwischen list_cases (60/min, lesend) und /sharpen (10/min, LLM).

    body: optional. Ohne Body (oder mit None-Feldern) werden die
    persistierten Werte aus /sharpen bzw. /propose-solution verwendet
    (Tag 42, ADR-0012). Ein gesetztes Feld ueberschreibt den persistierten
    Wert fuer diese Antwort, ohne ihn zu aendern. compliance_hint_text/
    compliance_citations kommen immer aus der Persistenz (ADR-0026), kein
    Override.

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    sharpened_text = body.sharpened_text if body is not None else None
    proposal_text = body.proposal_text if body is not None else None

    report = service.generate_report(
        case_id, sharpened_text=sharpened_text, proposal_text=proposal_text
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return _to_report_response(report)


class ComplianceHintsResponse(BaseModel):
    """RAG-gegruendete Compliance-Hinweise (Master-Plan v3.1 Phase D, ADR-0024).

    hint_text: None wenn das Retrieval keine Treffer lieferte (Graceful
    Degradation, kein ungegruendeter Hinweis -- kein LLM-Call in diesem Fall).
    citations: leer wenn hint_text None ist, sonst 1-basiert nummeriert,
    identisch zu den [N]-Referenzen in hint_text.
    """

    case_id: str
    hint_text: str | None
    citations: list[ComplianceCitationResponse]
    prompt_version: str


@router.post("/{case_id}/compliance-hints", response_model=ComplianceHintsResponse)
@limiter.limit("10/minute")
async def compliance_hints(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
    __: None = Depends(require_token_budget),
) -> ComplianceHintsResponse:
    """Erstellt RAG-gegruendete Compliance-Hinweise fuer einen bestehenden Case.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- LLM-Endpoint, analog /sharpen und
    /propose-solution (aect-security-checklist v2.1, Phase B: "LLM-Endpoints
    strenger").
    Token-Budget: require_token_budget prueft VOR dem LLM-Call das
    stuendliche Token-Budget des API-Keys (Phase G).

    Raises:
        HTTPException 404: case_id existiert nicht.
        HTTPException 429: Token-Budget des API-Keys erschoepft.
    """
    result = await service.generate_compliance_hints(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return ComplianceHintsResponse(
        case_id=result.case_id,
        hint_text=result.hint_text,
        citations=[
            ComplianceCitationResponse(
                number=citation.number,
                source_id=citation.source_id,
                citation=citation.citation,
                url=citation.url,
            )
            for citation in result.citations
        ],
        prompt_version=result.prompt_version,
    )


class SketchNodeResponse(BaseModel):
    """Ein Knoten der Architektur-Skizze (P11, ADR-0049).

    kind: einer der fuenf generischen Bausteintypen (user/system/ai_service/
    data_store/external) -- als String serialisiert (StrEnum.value).
    """

    id: str
    label: str
    kind: str


class SketchEdgeResponse(BaseModel):
    """Eine gerichtete Kante der Architektur-Skizze (P11)."""

    source: str
    target: str
    label: str | None


class ArchitectureSketchResponse(BaseModel):
    """On-Demand-Architektur-Skizze eines Case (P11, ADR-0049).

    nodes/edges: das schema-validierte Graph-JSON. mermaid_source: die vom
    deterministischen Builder daraus erzeugte Mermaid-Zeichenkette (das LLM
    emittiert nie Mermaid, nur den Graphen -- D18). generated_at aendert sich bei
    jedem Regenerieren (abgeleitetes Artefakt, kein Verlauf).
    """

    case_id: str
    nodes: list[SketchNodeResponse]
    edges: list[SketchEdgeResponse]
    mermaid_source: str
    generated_at: datetime
    prompt_version: str


class ArchitectureSketchEnvelope(BaseModel):
    """Read-Antwort fuer GET architecture-sketch (P11).

    sketch ist None, wenn der Case existiert, aber nie eine Skizze erzeugt wurde
    (200 {"sketch": null}) -- unterschieden vom 404 fuer einen fehlenden Case.
    """

    sketch: ArchitectureSketchResponse | None


def _to_sketch_response(result: ArchitectureSketchResult) -> ArchitectureSketchResponse:
    """Mappt das Application-Ergebnis auf das API-Schema (StrEnum -> .value)."""
    return ArchitectureSketchResponse(
        case_id=result.case_id,
        nodes=[
            SketchNodeResponse(id=node.id, label=node.label, kind=node.kind.value)
            for node in result.graph.nodes
        ],
        edges=[
            SketchEdgeResponse(source=edge.source, target=edge.target, label=edge.label)
            for edge in result.graph.edges
        ],
        mermaid_source=result.mermaid_source,
        generated_at=result.generated_at,
        prompt_version=result.prompt_version,
    )


@router.post(
    "/{case_id}/architecture-sketch", response_model=ArchitectureSketchResponse
)
@limiter.limit("10/minute")
async def generate_architecture_sketch(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
    __: None = Depends(require_token_budget),
) -> ArchitectureSketchResponse:
    """Erzeugt eine On-Demand-Architektur-Skizze fuer einen Case (P11, ADR-0049).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 10/Minute -- LLM-Endpoint, analog /sharpen und /ideation.
    Token-Budget: require_token_budget prueft VOR dem LLM-Call das stuendliche
    Token-Budget des API-Keys (Phase G), analog den uebrigen /cases/{id}/*-
    LLM-Endpoints.

    On-Demand -- KEIN Pipeline-Schritt: Intake-Kosten/-Latenz bleiben unveraendert.

    Fehler-Mapping (kein Stack-Trace an den Client, OWASP LLM02):
    - Case fehlt -> 404.
    - kein Loesungsvorschlag -> 409 (NoProposalForSketchError).
    - LLM-Antwort verletzt das Graph-Schema -> 422 (InvalidLLMOutputError),
      mit der praezisen, verletzten Schema-Regel als Begruendung. Bewusst NICHT
      502: der LLM-Call selbst gelang, nur der Inhalt ist unverwertbar -- ein
      502 wuerde faelschlich einen Gateway-/Infrastrukturfehler suggerieren.
    - LLM nach Retries nicht erreichbar -> 503.
    - interner Fehler HINTER dem LLM-Call (Mermaid-Builder/Persistenz) -> 500,
      strukturiert geloggt (sketch_generation_failed), Detail generisch.

    Raises:
        HTTPException 404: case_id existiert nicht.
        HTTPException 409: Case hat keinen Loesungsvorschlag.
        HTTPException 422: KI-Antwort verletzt das Skizzen-Schema.
        HTTPException 429: Token-Budget des API-Keys erschoepft.
        HTTPException 500: interner Builder-/Persistenzfehler.
        HTTPException 503: KI-Dienst nicht erreichbar.
    """
    try:
        result = await service.generate_sketch(case_id)
    except NoProposalForSketchError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "Fuer diesen Use Case liegt kein Loesungsvorschlag vor -- "
                "Skizze nicht moeglich."
            ),
        ) from exc
    except InvalidLLMOutputError as exc:
        # Die KI-Antwort verletzt das Graph-Schema (ArchitectureSketch). Der
        # LLM-Call gelang -- der Inhalt ist unverwertbar, kein Gateway-Fehler.
        # Darum 422 (nicht 502) und die praezise, verletzte Schema-Regel in der
        # Begruendung. str(exc) traegt nur loc+type je Fehler (H-031,
        # structured_output.py), nie LLM-Rohtext -- kein PII-Leak.
        raise HTTPException(
            status_code=422,
            detail=f"KI-Antwort verletzt das Skizzen-Schema: {exc}",
        ) from exc
    except (ConnectionError, TimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "KI-Dienst derzeit nicht erreichbar -- bitte spaeter erneut versuchen."
            ),
        ) from exc
    except Exception as exc:
        # Interner Fehler HINTER dem gelungenen LLM-Call: der deterministische
        # Mermaid-Builder oder die Persistenz. Bleibt 500, aber mit
        # strukturiertem Log statt nacktem Stack-Trace -- Detail generisch, kein
        # internes Leck an den Client (OWASP LLM02).
        structlog.get_logger().error(
            "sketch_generation_failed",
            case_id=case_id,
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Interner Fehler bei der Skizzen-Erzeugung.",
        ) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return _to_sketch_response(result)


@router.get("/{case_id}/architecture-sketch", response_model=ArchitectureSketchEnvelope)
@limiter.limit("60/minute")
async def get_architecture_sketch(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_admin),
) -> ArchitectureSketchEnvelope:
    """Gibt die persistierte Architektur-Skizze eines Case zurueck (P11, ADR-0049).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: require_admin (Session-Cookie ODER X-API-Key).
    Rate Limit: 60/Minute -- lesender Zugriff, analog GET /cases.

    200 {"sketch": null}, wenn der Case existiert, aber nie eine Skizze erzeugt
    wurde. 404, wenn der Case selbst nicht existiert (Service unterscheidet beide
    Faelle ueber CaseNotFoundError vs. None).

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    try:
        result = await service.get_sketch(case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc

    return ArchitectureSketchEnvelope(
        sketch=_to_sketch_response(result) if result is not None else None
    )


class CaseDetailResponse(BaseModel):
    """Vollstaendiger, read-only Bewertungsstand eines Case (E9, SDR-0003).

    Public GET-Gegenstueck zu den Admin-POST-Triggern: liefert, was der Admin
    bereits ausgeloest und persistiert hat -- KEIN neuer Berechnungs-/LLM-Pfad,
    kein Trigger. Ein anonymer Einreicher sieht damit den kompletten Stand
    seines eigenen Case.

    triage: das beim Intake berechnete Ergebnis -- Composite-Score inkl.
    Subscores, Zonen-Konfidenz, ROI, Routing, Machbarkeit, Vorfilter.
    report: der zweischichtige Report (deterministische Regel-Schicht ueber den
    persistierten Feldern) -- Entscheider-Sicht (gerenderte akzeptierte
    Schaerfung, Compliance-Hinweise + Quellen, Empfehlung, Entscheidung) und
    technische Sicht (Loesungsvorschlag, Composite, ROI, Signale). Fuer noch
    nicht ausgeloeste Schritte stehen die jeweiligen Felder auf null.

    Die Architektur-Skizze bleibt bewusst AUSSEN vor -- sie ist eine
    Admin-Ansicht (GET wie POST require_admin), nicht Teil des public Read.
    """

    id: str
    submitted_at: datetime
    status: str
    triage: TriageResponse
    report: ReportResponse


# Routing-Reihenfolge: dieser parametrisierte GET /cases/{case_id} steht bewusst
# NACH der literalen GET /cases/similarity-pairs (oben registriert), sonst wuerde
# "/cases/similarity-pairs" als case_id="similarity-pairs" hier landen. Die
# zwei-segmentigen /cases/{case_id}/... -Routen sind unabhaengig (andere
# Pfadtiefe, kein Shadowing).
@router.get("/{case_id}", response_model=CaseDetailResponse)
@limiter.limit("60/minute")
async def get_case_detail(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
) -> CaseDetailResponse:
    """Gibt den vollstaendigen, read-only Bewertungsstand eines Case zurueck.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: PUBLIC (V4-P-Auth, E9/SDR-0003) -- der anonyme Einreicher muss den
    kompletten gespeicherten Stand seines Case lesen koennen (Composite inkl.
    Subscores, Konfidenz, akzeptierte Schaerfung, Loesung, Compliance, Report).
    Nur LESEN dessen, was der Admin bereits ausgeloest hat: kein Trigger, kein
    LLM-Call (generate_report ist reine Regel-Schicht ueber persistierten Feldern).
    Rate Limit: 60/Minute -- lesender Zugriff, analog GET /cases.

    Raises:
        HTTPException 404: case_id existiert nicht.
    """
    case = service.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    # Kein Override -> die persistierten Werte (sharpened_content_json/
    # proposal_text/compliance_hints_json + result) werden gelesen und
    # zusammengesetzt. get_case lieferte den Case, daher ist report hier nicht
    # None -- der Guard bleibt als defensiver Fail-loud stehen.
    report = service.generate_report(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseDetailResponse(
        id=case.id,
        submitted_at=case.submitted_at,
        status=case.status.value,
        triage=_to_triage_response(case),
        report=_to_report_response(report),
    )

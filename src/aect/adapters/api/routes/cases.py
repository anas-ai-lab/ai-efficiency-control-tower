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
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from aect.adapters.api.dependencies import get_triage_service, require_api_key
from aect.adapters.api.rate_limit import limiter
from aect.application.service import CaseNotFoundError, TriageService

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


@router.delete("/{case_id}", status_code=204)
@limiter.limit("10/minute")
async def delete_case(
    case_id: str,
    request: Request,
    response: Response,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_api_key),
) -> Response:
    """Loescht einen Case kaskadiert (DSGVO Art. 17, ADR-0038).

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: X-API-Key-Header (require_api_key).
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


class SharpenedCaseResponse(BaseModel):
    """Original + geschaerfte Version eines Use Cases (ADR-0013 Teil 2).

    Erfolg: sharpened_title/current_state/desired_state gesetzt,
    improvement_suggestions hat 1-10 Eintraege, raw_text ist None.
    Graceful Degradation: die drei sharpened_*-Felder sind None,
    improvement_suggestions ist leer, raw_text enthaelt die rohe
    LLM-Antwort (aect-security-checklist v2.1: LLM-Output als untrusted,
    kein Crash bei Format-Verstoss).
    """

    case_id: str
    original_title: str
    original_current_state: str
    original_desired_state: str
    sharpened_title: str | None
    sharpened_current_state: str | None
    sharpened_desired_state: str | None
    improvement_suggestions: list[str]
    raw_text: str | None
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
        sharpened_title=sharpened.sharpened_title,
        sharpened_current_state=sharpened.sharpened_current_state,
        sharpened_desired_state=sharpened.sharpened_desired_state,
        improvement_suggestions=list(sharpened.improvement_suggestions),
        raw_text=sharpened.raw_text,
        prompt_version=sharpened.prompt_version,
    )


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
    _: str = Depends(require_api_key),
) -> SolutionProposalResponse:
    """Skizziert einen Loesungsansatz fuer einen bestehenden Case via LLM.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: X-API-Key-Header (require_api_key).
    Rate Limit: 10/Minute -- LLM-Endpoint, analog /sharpen
    (aect-security-checklist v2.1, Phase B: "LLM-Endpoints strenger").

    Skeleton (Tag 36, Phase C): v1-Prompt nennt bewusst keine konkreten
    Zielplattformen -- Stack-Grounding via RAG folgt Phase D.

    Raises:
        HTTPException 404: case_id existiert nicht.
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
    """Zweischichtiger Report -- striktes JSON (interne Referenz (entfernt) SS3.1, Punkt 6)."""

    case_id: str
    business_summary: BusinessSummaryResponse
    technical_detail: TechnicalDetailResponse


@router.post("/{case_id}/report", response_model=ReportResponse)
@limiter.limit("30/minute")
async def get_report(
    case_id: str,
    request: Request,
    response: Response,
    body: ReportRequest | None = None,
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    _: str = Depends(require_api_key),
) -> ReportResponse:
    """Erstellt den zweischichtigen Report fuer einen bestehenden Case.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: X-API-Key-Header (require_api_key).
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
    _: str = Depends(require_api_key),
) -> ComplianceHintsResponse:
    """Erstellt RAG-gegruendete Compliance-Hinweise fuer einen bestehenden Case.

    request/response: von slowapi benoetigt (Rate-Limit-Key, Header-Injektion).
    Auth: X-API-Key-Header (require_api_key).
    Rate Limit: 10/Minute -- LLM-Endpoint, analog /sharpen und
    /propose-solution (aect-security-checklist v2.1, Phase B: "LLM-Endpoints
    strenger").

    Raises:
        HTTPException 404: case_id existiert nicht.
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

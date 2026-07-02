"""Application-layer Data Transfer Object fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine Schichtverletzung.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from aect.domain import ReviewerDecision, TriageResult, UseCaseInput


class SimilarityWarning(BaseModel):
    """Hinweis auf einen aehnlichen, bereits eingereichten Case (L-3, ADR-0039).

    Wird bei Intake (POST /triage) erzeugt, wenn die Embedding-Cosinus-
    Aehnlichkeit des neuen Cases zu einem bestehenden Case eine Schwelle
    ueberschreitet. Rein additiv -- veraendert die Triage-Entscheidung nicht.

    similarity_score: Cosinus-Aehnlichkeit [0.0, 1.0] zum aehnlichsten Case.
    suggest_combine: True ab der hoeheren Schwelle (>= 0.90) -- "wahrscheinlich
    derselbe Use Case, zusammenlegen?". False im Awareness-Bereich
    ([0.75, 0.90)) -- "es gibt etwas Aehnliches, bitte pruefen".
    """

    similar_case_id: str
    similar_case_title: str
    similarity_score: float
    suggest_combine: bool


@dataclass
class SubmittedCase:
    """Persistiertes Ergebnis einer Use-Case-Einreichung.

    Verbindet Input (UseCaseInput), Ergebnis (TriageResult), Zeitstempel und ID.

    sharpened_content_json/proposal_text: optional persistierte LLM-Narrative
    aus sharpen_case() bzw. propose_solution() (Tag 42 ADR-0012, Spalte
    umbenannt ADR-0013 Teil 2). None, solange der jeweilige Endpoint fuer
    diesen Case noch nicht aufgerufen wurde. Werden bei jedem erneuten
    Aufruf ueberschrieben (kein Verlauf, keine Versionierung -- letzter
    Aufruf gewinnt).

    sharpened_content_json ist ein JSON-String: entweder ein valides
    SharpenedContentV2-Ergebnis (strukturierte Felder) oder ein
    Graceful-Degradation-Objekt (raw_text gesetzt). generate_report()
    rendert daraus den Anzeigetext (_render_sharpened_content, service.py)
    -- das /report-Schema (BusinessSummary.sharpened_text: str | None)
    bleibt dabei unveraendert.

    compliance_hints_json (ADR-0026): optional persistiertes Ergebnis von
    generate_compliance_hints() -- JSON-Objekt mit hint_text (str | None)
    und citations (Liste von Citation-Dicts). None, solange der Endpoint
    fuer diesen Case noch nicht aufgerufen wurde. Wird bei jedem erneuten
    Aufruf ueberschrieben, analog zu sharpened_content_json/proposal_text.
    generate_report() rendert daraus hint_text + citations (
    _render_compliance_hints, service.py) in BusinessSummary.

    Kein frozen=True: TriageResult enthaelt verschachtelte Typen die nicht
    zwingend hashbar sind (list-Felder in FeasibilityResult). Immutabilitaet
    nach Konvention -- nach dem Speichern nicht mehr mutieren, ausser fuer
    sharpened_content_json/proposal_text/compliance_hints_json via
    TriageService (s. service.py).

    reviewer_decision/reviewer_note/decided_at (Human-in-the-Loop, minimaler
    Decision-Record statt vollem Reviewer-Workflow -- ADR-0043): gesetzt ueber
    TriageService.record_decision() / POST /cases/{id}/decision. PENDING +
    None ist der Zustand vor jeder manuellen Entscheidung. Ueberschreiben ist
    erlaubt (Korrektur-Fall) -- decided_at wird bei jedem Aufruf aktualisiert.

    IP-Trennung (vertraglich bedingt): enthaelt keine firmenspezifischen Werte.
    Diese liegen ausschliesslich in roi_config.toml / zone_thresholds.yaml.
    """

    id: str
    submitted_at: datetime
    use_case: UseCaseInput
    result: TriageResult
    sharpened_content_json: str | None = None
    proposal_text: str | None = None
    compliance_hints_json: str | None = None
    # Intake-Embedding fuer Dedup-Aehnlichkeitspruefung (L-3, ADR-0039).
    # None, solange kein Embedding berechnet wurde (Mock-Modus, erster Case,
    # oder Case aus einer aelteren DB-Version). Persistiert als JSON-Float-Liste.
    embedding: list[float] | None = None
    reviewer_decision: ReviewerDecision = ReviewerDecision.PENDING
    reviewer_note: str | None = None
    decided_at: datetime | None = None


@dataclass(frozen=True)
class SharpenedUseCase:
    """Ergebnis der Use-Case-Schaerfung -- Original + geschaerfte Version.

    Original-Felder werden nie ueberschrieben (Projekt-Anforderung):
    case_id verweist auf den persistierten SubmittedCase, original_*
    sind die unveraenderten Eingabefelder.

    Strukturierte Ausgabe (ADR-0013 Teil 2): die LLM-Antwort wird gegen
    SharpenedContentV2 validiert (application.structured_output). Zwei
    sich gegenseitig ausschliessende Formen:

    - Erfolg: sharpened_title/sharpened_current_state/
      sharpened_desired_state sind str, improvement_suggestions hat 1-10
      Eintraege, raw_text ist None.
    - Graceful Degradation (LLM-Output erfuellt das Schema nicht --
      kaputtes JSON, fehlendes Feld, Laengenverstoss): die drei
      sharpened_*-Felder sind None, improvement_suggestions ist leer,
      raw_text enthaelt die rohe LLM-Antwort. Validierungsfehler werden
      geloggt (structured_output_validation_failed), der Aufruf schlaegt
      nicht fehl (aect-security-checklist v2.1: Graceful Degradation).

    prompt_version macht nachvollziehbar, welche Prompt-Version dieses
    Ergebnis erzeugt hat (aect.application.prompts.load_prompt). Default
    seit ADR-0013 Teil 2: "v2" (JSON-Output-Anweisung). v1 (Fliesstext)
    bleibt fuer Rollback erhalten.

    frozen=True: Schaerfungs-Ergebnis ist nach Erstellung unveraenderlich,
    analog zu UseCaseInput.
    """

    case_id: str
    original_title: str
    original_current_state: str
    original_desired_state: str
    sharpened_title: str | None
    sharpened_current_state: str | None
    sharpened_desired_state: str | None
    improvement_suggestions: tuple[str, ...]
    raw_text: str | None
    prompt_version: str


@dataclass(frozen=True)
class SolutionProposal:
    """Ergebnis des Stack-passenden Loesungsvorschlags (Phase C, Skeleton).

    Mock-First-Skeleton (Tag 36) analog SharpenedUseCase: proposal_text ist
    die rohe LLM-Antwort als str -- strukturierte Validierung (Plattform,
    Begruendung, Alternativen als separate Felder) folgt, sobald ein
    Provider strukturierte Antworten liefert (gleicher offener Punkt wie
    SharpenedUseCase, siehe ADR-0006).

    v1-Prompt (prompts/propose_solution/v1/) nennt bewusst keine konkreten
    Zielplattformen -- Stack-Grounding via RAG folgt Phase D (Master-Plan
    v3.1). case_id verweist auf den persistierten SubmittedCase.

    frozen=True: analog SharpenedUseCase, Ergebnis ist nach Erstellung
    unveraenderlich.
    """

    case_id: str
    proposal_text: str
    prompt_version: str


@dataclass(frozen=True)
class ComplianceCitation:
    """Eine einzelne Quellenangabe zu einem Compliance-Hinweis (ADR-0024).

    number: 1-basierte Position, identisch zur [N]-Referenz im hint_text.
    citation: menschenlesbares Zitat (z. B. "DSGVO Art. 35"), aus
    RetrievedChunk.metadata['citation'] -- Fallback auf source_id, falls
    eine Quelle (noch) kein Front-Matter-citation-Feld liefert (z. B.
    MockRetriever, dessen Treffer kein metadata fuehren).
    url: optional, aus RetrievedChunk.metadata.get('url').

    Deterministisch aus dem Retrieval gebaut, NICHT aus der LLM-Antwort
    geparst (ADR-0024) -- verhindert halluzinierte Artikel-Nummern
    strukturell statt durch Prompt-Disziplin allein.
    """

    number: int
    source_id: str
    citation: str
    url: str | None


@dataclass(frozen=True)
class BusinessSummary:
    """Entscheider-Schicht des zweischichtigen Reports (Projekt-Anforderung).

    Enthaelt nur, was fuer eine Go/No-Go-Einschaetzung noetig ist -- keine
    Rohwerte aus Vorfilter/Composite (siehe TechnicalDetail).

    sharpened_text: LLM-Schaerfung des Cases. Default ist der persistierte
    Wert aus sharpen_case() (Tag 42, ADR-0012); ein im Request-Body
    uebergebener Wert ueberschreibt den persistierten (z. B. fuer Tests oder
    Re-Sharpening ohne erneuten Persist). None, wenn weder persistiert noch
    uebergeben. Als untrusted LLM-Output unveraendert weitergereicht
    (aect-security-checklist v2.1).

    compliance_hint_text/compliance_citations (ADR-0026): aus dem
    persistierten compliance_hints_json gelesen (generate_compliance_hints()).
    Bewusst KEIN Request-Body-Override (anders als sharpened_text/
    proposal_text): hint_text referenziert seine Quellen ueber [N]-Marker,
    die exakt zur citations-Liste passen muessen -- ein freier Text-Override
    ohne passende Citation-Liste wuerde diese Kopplung brechen. Beide Felder
    sind None bzw. leer, wenn generate_compliance_hints() fuer diesen Case
    nie lief ODER lief, aber das Retrieval keine Treffer hatte (Graceful
    Degradation, ADR-0024) -- fuer den Report-Konsumenten aequivalent: kein
    Hinweis anzuzeigen.

    reviewer_decision/reviewer_note/decided_at (ADR-0043, minimaler
    Decision-Record): aktueller Entscheidungs-Zustand des Case, direkt aus
    SubmittedCase uebernommen -- macht den Human-in-the-Loop-Status im
    Report sichtbar, ohne einen zweiten Endpoint abzufragen.
    """

    title: str
    zone: str | None
    is_actionable: bool
    recommendation: str
    expected_benefit_eur: float | None
    summary_text: str
    sharpened_text: str | None
    compliance_hint_text: str | None
    compliance_citations: tuple[ComplianceCitation, ...]
    reviewer_decision: str
    reviewer_note: str | None
    decided_at: datetime | None


@dataclass(frozen=True)
class TechnicalDetail:
    """Reviewer-Schicht des zweischichtigen Reports (Projekt-Anforderung).

    Rohwerte aus Vorfilter, Composite-Score, Feasibility und Routing fuer
    Personen, die die Bewertung nachvollziehen wollen.

    proposal_text: Loesungsvorschlag des Cases, analog sharpened_text in
    BusinessSummary (persistiert via propose_solution(), Tag 42, ADR-0012;
    Request-Body-Wert ueberschreibt den persistierten).
    """

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


@dataclass(frozen=True)
class ReportResult:
    """Zweischichtiger Report fuer einen persistierten Case (Master-Plan v3.1,
    Phase C: "Zweischichtiger Report-Renderer").

    Reine Regel-Schicht: business_summary und technical_detail werden
    deterministisch aus TriageResult abgeleitet (_build_business_summary /
    _build_technical_detail in application/service.py). Kein LLM-Call.
    """

    case_id: str
    business_summary: BusinessSummary
    technical_detail: TechnicalDetail


@dataclass(frozen=True)
class ComplianceHintsResult:
    """Ergebnis der RAG-gegruendeten Compliance-Hinweise (Master-Plan v3.1
    Phase D, ADR-0024).

    hint_text: LLM-formulierter Fliesstext mit [N]-Referenzen, oder None
    wenn das Retrieval keinerlei Treffer lieferte -- in diesem Fall findet
    KEIN LLM-Call statt (Graceful Degradation, kein ungegruendeter Hinweis).
    citations: 1-basiert nummerierte Quellenliste, Reihenfolge identisch zu
    den [N]-Referenzen im hint_text. Leer wenn hint_text None ist.

    frozen=True: analog SharpenedUseCase/SolutionProposal.
    """

    case_id: str
    hint_text: str | None
    citations: tuple[ComplianceCitation, ...]
    prompt_version: str

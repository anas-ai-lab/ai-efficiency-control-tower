"""Application-layer Data Transfer Object fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine Schichtverletzung.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from aect.application.structured_output import ArchitectureSketch, ImprovementSuggestion
from aect.domain import CaseStatus, ReviewerDecision, TriageResult, UseCaseInput


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


class SimilarityPair(BaseModel):
    """Ein Paar aehnlicher, bereits eingereichter Cases (Dedup-View, P9).

    Dieselbe Cosinus-/Schwellen-Logik wie SimilarityWarning beim Intake
    (_cosine_similarity + _DEDUP_THRESHOLD_* in service.py), nur aggregiert:
    statt "neuer Case vs. bestehende" hier "alle bestehenden paarweise".

    case_a/case_b: deterministisch nach id sortiert (case_a.id < case_b.id) --
    ein Paar hat unabhaengig von der Iterationsreihenfolge dieselbe Gestalt.
    similarity_score: Cosinus-Aehnlichkeit [0.0, 1.0], auf 4 Nachkommastellen
    gerundet (analog SimilarityWarning). suggest_combine: True ab der hoeheren
    Schwelle (>= 0.90) -- "wahrscheinlich derselbe Use Case".
    """

    case_a_id: str
    case_a_title: str
    case_b_id: str
    case_b_title: str
    similarity_score: float
    suggest_combine: bool


class SimilarityPairsResult(BaseModel):
    """Aggregierte Dedup-Beziehungen ueber alle persistierten Cases (P9).

    pairs: alle Case-Paare mit Cosinus-Aehnlichkeit >= Awareness-Schwelle
    (>= 0.75), absteigend nach score sortiert (deterministisch, Sekundaer-
    schluessel case_a_id/case_b_id). Leer, wenn kein Paar die Schwelle erreicht.
    cases_without_embedding: Anzahl Cases ohne persistiertes Embedding -- der
    Embedder war beim Intake nicht verfuegbar (Mock-/Testbetrieb) oder der Case
    stammt aus einer aelteren DB-Version. Sie fliessen nicht in die Paarbildung
    ein; der Zaehler macht diese Luecke im UI transparent.
    """

    pairs: list[SimilarityPair]
    cases_without_embedding: int


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

    architecture_sketch (P11, ADR-0049): optional persistiertes Ergebnis von
    generate_sketch() -- JSON-Objekt mit graph (ArchitectureSketch),
    mermaid_source (str), generated_at (ISO) und prompt_version. None, solange
    generate_sketch() fuer diesen Case nie lief. Ein abgeleitetes Artefakt (D20):
    Regenerieren ueberschreibt, kein Verlauf. Wird bei einem Case-Delete
    automatisch mit-geloescht (DSGVO-Kaskade, liegt in der Case-Zeile).

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

    status/status_updated_at (Case-Lifecycle, siehe Lifecycle-ADR): wo der Case
    im Bearbeitungsfluss steht und wann der Zustand zuletzt wechselte. SUBMITTED
    + None direkt nach Einreichung (noch kein expliziter Wechsel), danach ueber
    POST /cases/{id}/status setzbar (TriageService.update_status()). status_
    updated_at ist der Zeitstempel des letzten Wechsels -- analog decided_at zur
    reviewer_decision, wird bei jedem Wechsel aktualisiert. Zusaetzlich koppelt
    record_decision() den Lifecycle an ReviewerDecision: APPROVED bzw. REJECTED
    wird ueber denselben Persistenz-Pfad mitgesetzt (status + status_updated_at)
    -- der Freigabe-Akt darf einen manuell gesetzten Status ueberschreiben
    (Lifecycle-ADR).

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
    architecture_sketch: str | None = None
    # sharpening_draft (V4, Draft/Accept-Flow): geschaerfte Fassung + Vorschlaege,
    # die POST /cases/{id}/sharpen erzeugt hat, BEVOR ein Mensch sie uebernimmt.
    # Ueberschreibt nichts am Case; accept traegt den Draft in
    # sharpened_content_json, reject leert ihn. None, solange kein Draft offen
    # ist. JSON-Objekt (original/sharpened/improvement_suggestions/metadaten).
    sharpening_draft: str | None = None
    # Intake-Embedding fuer Dedup-Aehnlichkeitspruefung (L-3, ADR-0039).
    # None, solange kein Embedding berechnet wurde (Mock-Modus, erster Case,
    # oder Case aus einer aelteren DB-Version). Persistiert als JSON-Float-Liste.
    embedding: list[float] | None = None
    reviewer_decision: ReviewerDecision = ReviewerDecision.PENDING
    reviewer_note: str | None = None
    decided_at: datetime | None = None
    status: CaseStatus = CaseStatus.SUBMITTED
    status_updated_at: datetime | None = None


@dataclass(frozen=True)
class MonitoringEntry:
    """Ein append-only Monitoring-Eintrag in der Zeitleiste eines Case
    (Monitoring-ADR).

    Manuelle Beobachtungsnotiz zu einem Case (z. B. "Pilot gestartet",
    "Nutzer-Feedback eingeholt"). Append-only: einmal geschrieben, nie
    veraendert oder einzeln geloescht -- der Audit-Charakter der Zeitleiste
    verlangt Unveraenderlichkeit (analog zum submitted_at-Audit-Trail). Die
    einzige Loeschung ist die DSGVO-Kaskade (Art. 17, ADR-0038): stirbt der
    Case, sterben seine Eintraege mit.

    status_snapshot: der case.status zum Zeitpunkt des Eintrags, als String
    festgehalten. Bewusst eine Momentaufnahme, kein Live-Verweis -- ein
    spaeterer Statuswechsel des Case aendert alte Eintraege nicht (sonst
    verloere die Zeitleiste ihren historischen Wert).

    frozen=True: analog UseCaseInput/SharpenedUseCase -- nach Erstellung
    unveraenderlich.
    """

    id: str
    case_id: str
    created_at: datetime
    note: str
    status_snapshot: str


@dataclass(frozen=True)
class SharpenedUseCase:
    """Ergebnis der Use-Case-Schaerfung -- Original + geschaerfte Version.

    Original-Felder werden nie ueberschrieben (Projekt-Anforderung):
    case_id verweist auf den persistierten SubmittedCase, original_*
    sind die unveraenderten Eingabefelder.

    Strukturierte Ausgabe (ADR-0013 Teil 2, verschaerft V4): die LLM-Antwort
    wird gegen SharpenedContentV2 validiert UND ein deterministischer
    Zahlen-Guard (domain/sharpening_guard) prueft, dass die geschaerften
    Beschreibungs-Felder keine im Original fehlenden Zahlen erfinden. Bei
    Schema- oder Zahlen-Verstoss laeuft genau EIN Retry; scheitert auch der,
    wirft sharpen_case() (Fail loud, kein Graceful-Degradation-Fallback mehr).
    In der Erfolgs-Form sind alle drei sharpened_*-Felder gesetzt und
    improvement_suggestions traegt 1-3 ImprovementSuggestion (bezugsfeld/
    vorschlag/hebel).

    prompt_version macht nachvollziehbar, welche Prompt-Version dieses
    Ergebnis erzeugt hat (aect.application.prompts.load_prompt). Default seit
    V4: "v3" (Zahlen-Verbot + Hebel-Pflicht). v2/v1 bleiben fuer Rollback.

    frozen=True: Schaerfungs-Ergebnis ist nach Erstellung unveraenderlich,
    analog zu UseCaseInput.
    """

    case_id: str
    original_title: str
    original_current_state: str
    original_desired_state: str
    sharpened_title: str
    sharpened_current_state: str
    sharpened_desired_state: str
    improvement_suggestions: tuple[ImprovementSuggestion, ...]
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


@dataclass(frozen=True)
class ArchitectureSketchResult:
    """On-Demand-Architektur-Skizze eines Case (P11, ADR-0049).

    graph: das schema-validierte Graph-JSON (ArchitectureSketch) -- das LLM
    emittiert nur dieses, nie Mermaid (D18). mermaid_source: die vom
    deterministischen Builder (application/mermaid.py) daraus erzeugte
    Mermaid-Zeichenkette. generated_at: Zeitpunkt der Erzeugung (aendert sich bei
    jedem Regenerieren -- abgeleitetes Artefakt, kein Verlauf, D20).
    prompt_version: welche Prompt-Version die Skizze erzeugt hat.

    frozen=True: analog SharpenedUseCase/SolutionProposal.
    """

    case_id: str
    graph: ArchitectureSketch
    mermaid_source: str
    generated_at: datetime
    prompt_version: str

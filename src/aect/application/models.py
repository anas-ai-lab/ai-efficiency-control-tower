"""Application-layer Data Transfer Object fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine Schichtverletzung.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aect.domain import TriageResult, UseCaseInput


@dataclass
class SubmittedCase:
    """Persistiertes Ergebnis einer Use-Case-Einreichung.

    Verbindet Input (UseCaseInput), Ergebnis (TriageResult), Zeitstempel und ID.

    sharpened_text/proposal_text: optional persistierte LLM-Narrative aus
    sharpen_case() bzw. propose_solution() (Tag 42, ADR-0012). None, solange
    der jeweilige Endpoint fuer diesen Case noch nicht aufgerufen wurde.
    Werden bei jedem erneuten Aufruf ueberschrieben (kein Verlauf, keine
    Versionierung -- letzter Aufruf gewinnt).

    Kein frozen=True: TriageResult enthaelt verschachtelte Typen die nicht
    zwingend hashbar sind (list-Felder in FeasibilityResult). Immutabilitaet
    nach Konvention -- nach dem Speichern nicht mehr mutieren, ausser fuer
    sharpened_text/proposal_text via TriageService (s. service.py).

    IP-Trennung (interne Referenz (entfernt) SS5): enthaelt keine firmenspezifischen Werte.
    Diese liegen ausschliesslich in roi_config.toml / zone_thresholds.yaml.
    """

    id: str
    submitted_at: datetime
    use_case: UseCaseInput
    result: TriageResult
    sharpened_text: str | None = None
    proposal_text: str | None = None


@dataclass(frozen=True)
class SharpenedUseCase:
    """Ergebnis der Use-Case-Schaerfung -- Original + geschaerfte Version.

    Original-Felder werden nie ueberschrieben (interne Referenz (entfernt) §3.1, Punkt 1):
    case_id verweist auf den persistierten SubmittedCase, original_*
    sind die unveraenderten Eingabefelder, sharpened_text ist die
    LLM-Ausgabe.

    Output-Validation (aect-security-checklist v2.1, Phase C): sharpened_text
    ist str -- die LLM-Antwort wird als Text behandelt, nicht als
    strukturierte Daten geparst. Strikte Pydantic-Validierung der LLM-Antwort
    folgt, sobald ein Provider strukturierte (z. B. JSON-)Antworten liefert
    (siehe ADR-0006, offener Punkt).

    prompt_version macht nachvollziehbar, welche Prompt-Version dieses
    Ergebnis erzeugt hat (aect.application.prompts.load_prompt).

    frozen=True: Schaerfungs-Ergebnis ist nach Erstellung unveraenderlich,
    analog zu UseCaseInput.
    """

    case_id: str
    original_title: str
    original_current_state: str
    original_desired_state: str
    sharpened_text: str
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
class BusinessSummary:
    """Entscheider-Schicht des zweischichtigen Reports (interne Referenz (entfernt) SS3.1, Punkt 6).

    Enthaelt nur, was fuer eine Go/No-Go-Einschaetzung noetig ist -- keine
    Rohwerte aus Vorfilter/Composite (siehe TechnicalDetail).

    sharpened_text: LLM-Schaerfung des Cases. Default ist der persistierte
    Wert aus sharpen_case() (Tag 42, ADR-0012); ein im Request-Body
    uebergebener Wert ueberschreibt den persistierten (z. B. fuer Tests oder
    Re-Sharpening ohne erneuten Persist). None, wenn weder persistiert noch
    uebergeben. Als untrusted LLM-Output unveraendert weitergereicht
    (aect-security-checklist v2.1).
    """

    title: str
    zone: str | None
    is_actionable: bool
    recommendation: str
    expected_benefit_eur: float | None
    summary_text: str
    sharpened_text: str | None


@dataclass(frozen=True)
class TechnicalDetail:
    """Reviewer-Schicht des zweischichtigen Reports (interne Referenz (entfernt) SS3.1, Punkt 6).

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

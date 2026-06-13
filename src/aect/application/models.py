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

    Kein frozen=True: TriageResult enthaelt verschachtelte Typen die nicht
    zwingend hashbar sind (list-Felder in FeasibilityResult). Immutabilitaet
    nach Konvention -- nach dem Speichern nicht mehr mutieren.

    IP-Trennung (interne Referenz (entfernt) SS5): enthaelt keine firmenspezifischen Werte.
    Diese liegen ausschliesslich in roi_config.toml / zone_thresholds.yaml.
    """

    id: str
    submitted_at: datetime
    use_case: UseCaseInput
    result: TriageResult


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

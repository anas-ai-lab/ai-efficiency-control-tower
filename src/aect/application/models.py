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

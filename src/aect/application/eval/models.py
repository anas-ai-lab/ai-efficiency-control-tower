"""Eval-Case-Schema fuer die Phase-E-Evaluierung (Master-Plan v3.1 Phase E, ADR-0029).

Ein EvalCase buendelt einen validierten UseCaseInput mit einem optionalen
Experten-Label (expected_zone). Golden-Cases (von Hand kuratiert, kleine
Menge, hohe Vertrauenswuerdigkeit) und Synthetic-Cases (groessere generierte
Menge, fuer Volumen im spaeteren Eval-Runner) teilen sich dieses Schema --
der Unterschied liegt im Speicherort (evals/golden/ vs. evals/synthetic/),
nicht im Format.

expected_zone ist None, solange noch kein Experten-Urteil vorliegt (reiner
Konsistenz-Eval moeglich, kein Soll-Wert noetig). Sobald ein Wert gesetzt
ist, kann derselbe Case auch fuer den Experten-Abgleich verwendet werden.

Schicht: application -- importiert aus aect.domain (erlaubt), nicht aus
aect.adapters.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from aect.domain import TriageZone, UseCaseInput


class EvalCase(BaseModel):
    """Ein einzelner Eval-Case: Input + optionales Experten-Label.

    case_id: eindeutiger, sprechender Bezeichner (z. B. "golden-001") --
        identifiziert den Case in Reports und Logs, OHNE den use_case-
        Inhalt zu loggen (Logging-Allowlist, aect-security-checklist v2.1).
    use_case: vollstaendig validiertes UseCaseInput -- dieselbe Validierung
        wie produktiver Intake (extra='forbid', alle Constraints aktiv).
    expected_zone: Experten-Label fuer den Experten-Abgleich. None = nur
        fuer Konsistenz-Eval nutzbar.
    notes: Freitext-Begruendung des Labels. Nie an ein LLM weitergereicht --
        reine Dokumentation fuer Menschen.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1, max_length=100)
    use_case: UseCaseInput
    expected_zone: TriageZone | None = None
    notes: str = Field(default="", max_length=1000)

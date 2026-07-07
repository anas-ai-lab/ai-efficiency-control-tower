"""Feasibility check for AECT use-case triage.

Checks whether a submission is concrete enough for meaningful evaluation.
This is structural quality control — orthogonal to business value.

Rules (deterministic, no LLM):
1. Ist- and Soll-Zustand must be described concretely (minimum length).
2. A concrete process example must be provided.
3. Time saving per occurrence must be positive.
4. The process must be recurring (occurrences_per_month > 0; fractional
   values are valid -- callers with annual counts pass count/12 untruncated,
   so 1-11 occurrences/year still count as recurring, F-008).

The minimum lengths here are descriptive quality thresholds, NOT business
thresholds — they do not belong in zone_thresholds.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

_MIN_SITUATION_LEN: int = 50  # minimum chars for a "concrete" situation description
_MIN_EXAMPLE_LEN: int = 30  # minimum chars for a process example


class FeasibilityFlag(StrEnum):
    """Specific reasons why a submission is considered infeasible.

    NO_TIME_SAVING/NOT_RECURRING sind nur bei Direktnutzung des Checkers
    erreichbar: der Pipeline-Pfad speist Pydantic-validierten UseCaseInput ein
    (time/occurrences > 0 erzwungen), sodass diese beiden Flags dort nie
    triggern. Sie bleiben fuer den direkten Checker-Aufruf (Tests, kuenftige
    ungefilterte Quellen) definiert.
    """

    DESCRIPTION_TOO_VAGUE = "DESCRIPTION_TOO_VAGUE"
    MISSING_EXAMPLE = "MISSING_EXAMPLE"
    NO_TIME_SAVING = "NO_TIME_SAVING"
    NOT_RECURRING = "NOT_RECURRING"


@dataclass(frozen=True)
class FeasibilityResult:
    """Immutable result of the feasibility check.

    Attributes:
        is_feasible: True if no flags were raised.
        flags: Specific issues found (empty tuple if feasible).
        recommendation: German-language guidance for the submitter,
                        or None if the submission is feasible.
    """

    is_feasible: bool
    flags: tuple[FeasibilityFlag, ...]
    recommendation: str | None = None

    def has_flag(self, flag: FeasibilityFlag) -> bool:
        """Check for a specific flag without iterating."""
        return flag in self.flags


class FeasibilityChecker:
    """Checks structural completeness of a use-case submission.

    Does NOT assess business value — that is the ROI engine and zone classifier.
    Only answers: is this submission concrete enough to evaluate at all?

    This class has no configuration (thresholds are descriptive minimums, not
    business parameters) and no external dependencies.

    Usage:
        checker = FeasibilityChecker()
        result = checker.check(
            current_situation="Aktuell werden Rechnungen manuell...",
            target_situation="Zukünftig soll ein KI-System...",
            example_process="Eine Rechnung von Lieferant X...",
            time_saved_minutes_per_occurrence=Decimal("25"),
            occurrences_per_month=200,
        )
    """

    def check(
        self,
        current_situation: str,
        target_situation: str,
        example_process: str,
        time_saved_minutes_per_occurrence: Decimal,
        occurrences_per_month: float,
    ) -> FeasibilityResult:
        """Run all feasibility checks and return the combined result.

        Args:
            current_situation: Description of the current process/problem.
            target_situation: Description of the desired future state.
            example_process: One concrete process occurrence as an example.
            time_saved_minutes_per_occurrence: Minutes saved per single occurrence.
            occurrences_per_month: How often the process occurs per month.
                Fractional values are valid (e.g. 0.5 = every two months);
                anything > 0 counts as recurring (F-008).

        Returns:
            FeasibilityResult with flags and an optional recommendation.
        """
        flags: list[FeasibilityFlag] = []

        # Check 1: Both situation descriptions must be concrete
        if (
            len(current_situation.strip()) < _MIN_SITUATION_LEN
            or len(target_situation.strip()) < _MIN_SITUATION_LEN
        ):
            flags.append(FeasibilityFlag.DESCRIPTION_TOO_VAGUE)

        # Check 2: A process example must be present
        if len(example_process.strip()) < _MIN_EXAMPLE_LEN:
            flags.append(FeasibilityFlag.MISSING_EXAMPLE)

        # Check 3: Time saving must be positive
        if time_saved_minutes_per_occurrence <= Decimal("0"):
            flags.append(FeasibilityFlag.NO_TIME_SAVING)

        # Check 4: Process must be recurring
        if occurrences_per_month <= 0:
            flags.append(FeasibilityFlag.NOT_RECURRING)

        is_feasible = len(flags) == 0
        return FeasibilityResult(
            is_feasible=is_feasible,
            flags=tuple(flags),
            recommendation=_build_recommendation(flags) if flags else None,
        )


def _build_recommendation(flags: list[FeasibilityFlag]) -> str:
    """Build a German-language recommendation string from active flags."""
    parts: list[str] = []
    if FeasibilityFlag.DESCRIPTION_TOO_VAGUE in flags:
        parts.append(
            f"Ist- und Soll-Zustand ausführlicher beschreiben "
            f"(mind. {_MIN_SITUATION_LEN} Zeichen je Feld)."
        )
    if FeasibilityFlag.MISSING_EXAMPLE in flags:
        parts.append("Konkreten Beispielvorgang ergänzen.")
    if FeasibilityFlag.NO_TIME_SAVING in flags:
        parts.append("Zeitersparnis pro Vorgang muss größer 0 sein.")
    if FeasibilityFlag.NOT_RECURRING in flags:
        parts.append("Vorgangshäufigkeit (pro Monat) muss angegeben und größer 0 sein.")
    return " ".join(parts)

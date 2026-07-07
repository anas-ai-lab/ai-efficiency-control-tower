"""
Composite-Aufwand-Score einer Use-Case-Einreichung.

Score = Komplexität (1-5) + Implementierungskosten (1-3) + Datenschutz-Stufe (0-2)
Wertebereich: 2–10. Je höher, desto aufwändiger/riskanter.
"""

from __future__ import annotations

from dataclasses import dataclass

from aect.domain.types import DataClassification

# ---------------------------------------------------------------------------
# Mapping DataClassification → Datenschutz-Punkte (0-2)
# ---------------------------------------------------------------------------
DATA_CLASSIFICATION_TO_SCORE: dict[DataClassification, int] = {
    DataClassification.NO_PERSONAL_DATA: 0,  # Rein operative / anonyme Daten
    DataClassification.PSEUDONYMOUS: 1,  # Pseudonymisiert (Art. 4 Nr. 5 DSGVO)
    DataClassification.PERSONAL: 2,  # Personenbezogen (Art. 4 Nr. 1 DSGVO)
    DataClassification.SENSITIVE_PERSONAL: 2,  # Besondere Kategorien (Art. 9 DSGVO)
}


# ---------------------------------------------------------------------------
# Ergebnis-Typ
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CompositeScore:
    """Aufwand-Score einer Use-Case-Einreichung.

    Attributes:
        complexity_score: Technische Komplexität, 1-5.
        cost_score: Implementierungskosten-Stufe, 1-3.
        data_protection_score: Datenschutz-Aufwand, 0-2.
        total: Summe der drei Dimensionen (Wertebereich: 2–10).
    """

    complexity_score: int
    cost_score: int
    data_protection_score: int
    total: int

    def __post_init__(self) -> None:
        if not (1 <= self.complexity_score <= 5):
            raise ValueError(
                f"complexity_score muss 1-5 sein, ist {self.complexity_score}"
            )
        if not (1 <= self.cost_score <= 3):
            raise ValueError(f"cost_score muss 1-3 sein, ist {self.cost_score}")
        if not (0 <= self.data_protection_score <= 2):
            raise ValueError(
                f"data_protection_score muss 0-2 sein, ist {self.data_protection_score}"
            )
        expected = self.complexity_score + self.cost_score + self.data_protection_score
        if self.total != expected:
            raise ValueError(
                f"total ({self.total}) stimmt nicht mit Summe ({expected}) überein"
            )

    @property
    def effort_label(self) -> str:
        """Textuelle Einstufung: NIEDRIG / MITTEL / HOCH."""
        if self.total <= 4:
            return "NIEDRIG"
        if self.total <= 7:
            return "MITTEL"
        return "HOCH"


# ---------------------------------------------------------------------------
# Berechnungsfunktion
# ---------------------------------------------------------------------------
def compute_composite_score(
    complexity: int,
    cost: int,
    data_classification: DataClassification,
) -> CompositeScore:
    """Berechnet den Composite-Aufwand-Score.

    Args:
        complexity: Technische Komplexität, 1-5 (1 = trivial, 5 = sehr komplex).
        cost: Implementierungskosten-Stufe, 1-3 (1 = gering, 3 = hoch).
        data_classification: Datenschutz-Klassifizierung des Use Cases.

    Returns:
        CompositeScore mit total und effort_label.

    Raises:
        ValueError: Wenn complexity oder cost außerhalb des Wertebereichs.
        KeyError: Wenn data_classification nicht im Mapping hinterlegt ist.
    """
    if not (1 <= complexity <= 5):
        raise ValueError(f"complexity muss 1-5 sein, ist {complexity}")
    if not (1 <= cost <= 3):
        raise ValueError(f"cost muss 1-3 sein, ist {cost}")

    data_score = DATA_CLASSIFICATION_TO_SCORE[data_classification]
    total = complexity + cost + data_score

    return CompositeScore(
        complexity_score=complexity,
        cost_score=cost,
        data_protection_score=data_score,
        total=total,
    )

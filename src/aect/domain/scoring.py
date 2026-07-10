"""
Composite-Aufwand-Score einer Use-Case-Einreichung (V4-Modell, SDR-0003).

Score = Komplexität (1-5) + Kostenpunkte (0-2) + Datenschutz-Stufe (0-2)
Wertebereich: 1–9. Je höher, desto aufwändiger/riskanter.

Fachliche Definitionen (Komplexität aus Umsetzungsansatz, DSGVO-Mapping) stehen
im Code — es sind Methodik-Entscheidungen, keine Firmenzahlen. Die zwei
Kostenschwellen dagegen liegen in config/roi_config.toml ([effort_cost_points]).
"""

from __future__ import annotations

from dataclasses import dataclass

from aect.domain.types import DataClassification, ImplementationApproach

# ---------------------------------------------------------------------------
# Mapping ImplementationApproach → Komplexitäts-Punkte (1-5)
# Ordinal, aufsteigende Komplexität (SDR-0003 Entscheidung 4). Fachliche
# Definition, keine Firmenzahl → im Code, nicht in Config.
# ---------------------------------------------------------------------------
COMPLEXITY_BY_APPROACH: dict[ImplementationApproach, int] = {
    ImplementationApproach.SIMPLE_INTEGRATION: 1,  # einfache Implementierung, Bestand
    ImplementationApproach.DEVELOPMENT_ON_EXISTING: 2,  # Entwicklung auf Bestand
    ImplementationApproach.API_INTEGRATION: 3,  # API-Anbindung in Bestand
    ImplementationApproach.CUSTOM_DEVELOPMENT: 4,  # eigene Entwicklung
    ImplementationApproach.NEW_TOOL: 5,  # Einfuehrung neues Tool
}

# ---------------------------------------------------------------------------
# Mapping DataClassification → Datenschutz-Punkte (0-2)
# PERSONAL == PSEUDONYMOUS == 1: pseudonymisierte Daten bleiben personenbezogen
# i. S. d. DSGVO (Art. 4 Nr. 5), daher gleicher Aufwand. Nur besondere
# Kategorien (Art. 9) heben den Score auf 2.
# ---------------------------------------------------------------------------
DATA_CLASSIFICATION_TO_SCORE: dict[DataClassification, int] = {
    DataClassification.NO_PERSONAL_DATA: 0,  # Rein operative / anonyme Daten
    DataClassification.PSEUDONYMOUS: 1,  # Pseudonymisiert bleibt personenbezogen
    DataClassification.PERSONAL: 1,  # Personenbezogen (Art. 4 Nr. 1 DSGVO)
    DataClassification.SENSITIVE_PERSONAL: 2,  # Besondere Kategorien (Art. 9 DSGVO)
}

# Default-Schwellen fuer die Kostenpunkte (fallen zurueck, wenn ein Aufrufer sie
# nicht explizit setzt). Der Live-Pfad (pipeline) reicht die Config-Werte durch;
# der Default haelt compute_composite_score direkt testbar (SDR-0003 Abschnitt 3).
_DEFAULT_COST_POINT_MIN_EUR = 10_000.0


# ---------------------------------------------------------------------------
# Ergebnis-Typ
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CompositeScore:
    """Aufwand-Score einer Use-Case-Einreichung (V4, Wertebereich 1–9).

    Attributes:
        complexity_score: Komplexität aus dem Umsetzungsansatz, 1-5.
        cost_score: Kostenpunkte (Impl.- + Lizenzschwelle), 0-2.
        data_protection_score: Datenschutz-Aufwand, 0-2.
        total: Summe der drei Dimensionen (Wertebereich: 1–9).
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
        if not (0 <= self.cost_score <= 2):
            raise ValueError(f"cost_score muss 0-2 sein, ist {self.cost_score}")
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
        """Textuelle Einstufung: NIEDRIG / MITTEL / HOCH (Range 1–9)."""
        if self.total <= 3:
            return "NIEDRIG"
        if self.total <= 6:
            return "MITTEL"
        return "HOCH"


# ---------------------------------------------------------------------------
# Berechnungsfunktion
# ---------------------------------------------------------------------------
def compute_composite_score(
    approach: ImplementationApproach,
    implementation_cost_eur: float,
    license_cost_eur: float,
    data_classification: DataClassification,
    *,
    impl_cost_point_min_eur: float = _DEFAULT_COST_POINT_MIN_EUR,
    license_cost_point_min_eur: float = _DEFAULT_COST_POINT_MIN_EUR,
) -> CompositeScore:
    """Berechnet den Composite-Aufwand-Score (V4-Modell, Range 1–9).

    Args:
        approach: Geplanter Umsetzungsansatz → Komplexität 1-5 (COMPLEXITY_BY_APPROACH).
        implementation_cost_eur: Einmalige Implementierungskosten in EUR.
        license_cost_eur: Jährliche Lizenzkosten in EUR.
        data_classification: Datenschutz-Klassifizierung des Use Cases.
        impl_cost_point_min_eur: Schwelle für den Impl.-Kostenpunkt (Config).
        license_cost_point_min_eur: Schwelle für den Lizenz-Kostenpunkt (Config).

    Returns:
        CompositeScore mit total und effort_label.

    Raises:
        KeyError: Wenn approach oder data_classification nicht im Mapping stehen.
    """
    complexity = COMPLEXITY_BY_APPROACH[approach]

    cost_score = 0
    if implementation_cost_eur >= impl_cost_point_min_eur:
        cost_score += 1
    if license_cost_eur >= license_cost_point_min_eur:
        cost_score += 1

    data_score = DATA_CLASSIFICATION_TO_SCORE[data_classification]
    total = complexity + cost_score + data_score

    return CompositeScore(
        complexity_score=complexity,
        cost_score=cost_score,
        data_protection_score=data_score,
        total=total,
    )

"""
Vorfilter — drei Mindestkriterien für AI-Use-Case-Einreichungen.

Schwellenwerte sind konfigurierbar über Funktionsparameter. Die Defaults hier
sind Platzhalter für Dev/Test; in Phase B kommen sie aus einer Settings-Klasse
(IP-Trennung: firmenspezifische Werte gehören nicht in dieses Modul).
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Default-Schwellenwerte (Phase B: aus Settings laden)
# ---------------------------------------------------------------------------
DEFAULT_MIN_THEORETICAL_POTENTIAL_EUR: float = 20_000.0
DEFAULT_MIN_HOURS_PER_YEAR: float = 120.0
DEFAULT_MIN_NET_BENEFIT_EUR: float = 5_000.0


# ---------------------------------------------------------------------------
# Ergebnis-Typ
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FilterResult:
    """Ergebnis des Vorfilters.

    Attributes:
        passes: True wenn alle drei Kriterien erfüllt sind.
        failed_criteria: Namen der nicht erfüllten Kriterien (leer wenn passes=True).
        details: Mapping Kriterium → bool für Audit-Trail.
    """

    passes: bool
    failed_criteria: list[str]
    details: dict[str, bool]

    def __post_init__(self) -> None:
        if self.passes and self.failed_criteria:
            raise ValueError("passes=True, aber failed_criteria nicht leer")
        if not self.passes and not self.failed_criteria:
            raise ValueError("passes=False, aber keine failed_criteria angegeben")


# ---------------------------------------------------------------------------
# Vorfilter
# ---------------------------------------------------------------------------
def apply_prefilter(
    theoretical_potential_eur: float,
    hours_per_year: float,
    net_benefit_eur: float,
    *,
    min_potential: float = DEFAULT_MIN_THEORETICAL_POTENTIAL_EUR,
    min_hours: float = DEFAULT_MIN_HOURS_PER_YEAR,
    min_net_benefit: float = DEFAULT_MIN_NET_BENEFIT_EUR,
) -> FilterResult:
    """Prüft drei Mindestkriterien für eine Use-Case-Einreichung.

    Args:
        theoretical_potential_eur: Theoretisches Jahrespotenzial in EUR.
        hours_per_year: Erwartete Stundeneinsparung pro Jahr.
        net_benefit_eur: Nettonutzen nach Kosten in EUR.
        min_potential: Mindestschwelle theoretisches Potenzial.
        min_hours: Mindestschwelle Stundeneinsparung.
        min_net_benefit: Mindestschwelle Nettonutzen.

    Returns:
        FilterResult mit passes=True wenn alle Kriterien erfüllt.
    """
    criteria: dict[str, bool] = {
        "Theoretisches Potenzial": theoretical_potential_eur >= min_potential,
        "Stundeneinsparung": hours_per_year >= min_hours,
        "Nettonutzen": net_benefit_eur >= min_net_benefit,
    }
    failed = [name for name, passed in criteria.items() if not passed]
    return FilterResult(
        passes=len(failed) == 0,
        failed_criteria=failed,
        details=criteria,
    )

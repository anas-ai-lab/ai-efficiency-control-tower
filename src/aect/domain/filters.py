"""
Vorfilter — drei Mindestkriterien für AI-Use-Case-Einreichungen.

Schwellenwerte kommen verpflichtend vom Aufrufer (F-001: `evaluate_use_case()`
reicht die ROIConfig-Werte aus config/roi_config.toml durch). Keine Defaults
in diesem Modul — die frühere Duplikation (Python-Defaults hier UND
TOML-Config) machte Config-Änderungen zu einem stillen No-op und war als
Limitation #14 dokumentiert.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    min_potential: float,
    min_hours: float,
    min_net_benefit: float,
) -> FilterResult:
    """Prüft drei Mindestkriterien für eine Use-Case-Einreichung.

    Args:
        theoretical_potential_eur: Theoretisches Jahrespotenzial in EUR.
        hours_per_year: Erwartete Stundeneinsparung pro Jahr.
        net_benefit_eur: Nettonutzen nach Kosten in EUR.
        min_potential: Mindestschwelle theoretisches Potenzial (ROIConfig).
        min_hours: Mindestschwelle Stundeneinsparung (ROIConfig).
        min_net_benefit: Mindestschwelle Nettonutzen (ROIConfig).

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

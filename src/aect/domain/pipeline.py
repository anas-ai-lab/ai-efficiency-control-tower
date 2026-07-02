"""Domain pipeline — deterministic Phase A triage orchestrator.

EXECUTION ORDER (von apply_prefilter() erzwungen):
    1. calculate_roi()        -- liefert Werte die Vorfilter braucht
    2. apply_prefilter()      -- prueft theoretical_potential, hours_per_year, net_benefit
    3. route_use_case()       -- immer, unabhaengig vom Vorfilter
    4. FeasibilityChecker     -- immer, unabhaengig vom Vorfilter
    5. compute_composite_score() + classify() -- nur wenn vorfilter.passes

Dependency rule: nur Imports aus aect.domain.* -- niemals adapters/ oder application/.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aect.domain.feasibility import FeasibilityChecker, FeasibilityResult
from aect.domain.filters import FilterResult, apply_prefilter
from aect.domain.models import UseCaseInput
from aect.domain.roi import ROIConfig, ROIResult, calculate_roi
from aect.domain.routing import RoutingResult, route_use_case
from aect.domain.scoring import CompositeScore, compute_composite_score
from aect.domain.zones import ZoneResult, load_zone_classifier


@dataclass(frozen=True)
class TriageResult:
    """Immutable snapshot aller Phase-A-Evaluierungen fuer einen Use Case.

    roi, composite, zone sind None wenn passed_vorfilter False ist.
    routing und feasibility sind immer befuellt.
    """

    title: str
    passed_vorfilter: bool
    vorfilter: FilterResult
    routing: RoutingResult
    feasibility: FeasibilityResult
    roi: ROIResult | None
    composite: CompositeScore | None
    zone: ZoneResult | None

    @property
    def is_actionable(self) -> bool:
        """True iff Vorfilter bestanden und final_zone in {LIKELY_WIN, CALCULATED_RISK}."""
        if not self.passed_vorfilter or self.zone is None:
            return False
        return self.zone.final_zone.value in {"LIKELY_WIN", "CALCULATED_RISK"}


_feasibility_checker = FeasibilityChecker()


def handlungsdruck_score(use_case: UseCaseInput) -> int:
    """1-4 Handlungsdruck-Score aus drei Boolean-Feldern (Shift +1 fuer 1-Basis).

    Oeffentlich seit Tag 65 (ADR-0031) -- wird neben evaluate_use_case() auch
    von application/eval/breakdown.py genutzt, um den Score-Breakdown ohne
    Verdopplung der Pipeline-Logik zu bauen.
    """
    return (
        1
        + int(use_case.regulatory_pressure)
        + int(use_case.competitive_pressure)
        + int(use_case.strategic_priority)
    )


def _cost_tier(license_cost_eur: float) -> int:
    """Mappt Lizenzkosten EUR auf Kostenstufe 1-3 fuer compute_composite_score.

    Proxy bis ein dediziertes implementation_cost_level-Feld in UseCaseInput
    ergaenzt wird. Schwellen: DACH-typische SaaS-Kostenbänder.
    """
    if license_cost_eur < 5_000:
        return 1
    if license_cost_eur < 25_000:
        return 2
    return 3


def evaluate_use_case(
    use_case: UseCaseInput,
    roi_config: ROIConfig,
    country: str = "DE",
) -> TriageResult:
    """Fuehrt die vollstaendige Phase-A-Regel-Pipeline aus.

    Args:
        use_case:   Validiertes UseCaseInput (extra='forbid' garantiert).
        roi_config: ROI-Konfiguration aus load_roi_config().
        country:    ISO-Laendercode fuer Stundensatz-Lookup (Default: DE).

    Returns:
        TriageResult -- vollstaendig immutabel. roi/composite/zone sind None
        wenn passed_vorfilter False ist.
    """
    # 1. ROI -- muss zuerst laufen; Vorfilter braucht die berechneten Werte
    roi = calculate_roi(use_case, roi_config, country=country)

    # 2. Vorfilter -- verwendet ROI-Ergebnisse fuer Schwellwert-Pruefung.
    # Schwellen kommen aus der ROIConfig (F-001): frueher galten hier
    # hartcodierte Modul-Defaults, Aenderungen an roi_config.toml waren
    # fuer diese Pruefung ein stiller No-op.
    vorfilter = apply_prefilter(
        theoretical_potential_eur=float(roi.theoretical_potential_eur),
        hours_per_year=roi.hours_per_year,
        net_benefit_eur=float(roi.net_expected_benefit_eur),
        min_potential=float(roi_config.min_potential_eur),
        min_hours=roi_config.min_hours_per_year,
        min_net_benefit=float(roi_config.min_expected_benefit_eur),
    )

    # 3. Routing -- laeuft immer, unabhaengig vom Vorfilter
    routing = route_use_case(use_case)

    # 4. Feasibility -- laeuft immer, unabhaengig vom Vorfilter
    feasibility = _feasibility_checker.check(
        current_situation=use_case.current_state,
        target_situation=use_case.desired_state,
        example_process=use_case.example_process,
        time_saved_minutes_per_occurrence=Decimal(
            str(use_case.time_savings_hours_per_case * 60)
        ),
        occurrences_per_month=int(use_case.frequency_per_year / 12),
    )

    # 5-6. Composite + Zone -- nur wenn Vorfilter bestanden
    composite: CompositeScore | None = None
    zone: ZoneResult | None = None

    if vorfilter.passes:
        composite = compute_composite_score(
            complexity=use_case.implementation_complexity,
            cost=_cost_tier(use_case.estimated_license_cost_eur),
            data_classification=use_case.data_classification,
        )
        zone = load_zone_classifier().classify(
            expected_benefit_eur=roi.expected_benefit_eur,
            composite_score=composite.total,
            handlungsdruck_score=handlungsdruck_score(use_case),
        )

    return TriageResult(
        title=use_case.title,
        passed_vorfilter=vorfilter.passes,
        vorfilter=vorfilter,
        routing=routing,
        feasibility=feasibility,
        roi=roi if vorfilter.passes else None,
        composite=composite,
        zone=zone,
    )

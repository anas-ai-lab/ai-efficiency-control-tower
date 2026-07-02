"""Snapshot tests for the Phase A domain pipeline.

10 parametrised use cases: LIKELY_WIN (2), CALCULATED_RISK (3),
MARGINAL_GAIN (2), FAILS VORFILTER (3).

Tag 21 Ergaenzung: _cost_tier-Baender + is_actionable alle Zweige.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from pathlib import Path

import pytest

from aect.domain.feasibility import FeasibilityResult
from aect.domain.filters import FilterResult
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import (
    TriageResult,
    _cost_tier,
    evaluate_use_case,
    handlungsdruck_score,
)
from aect.domain.roi import ROIConfig, ROIResult, load_roi_config
from aect.domain.routing import RoutingRecommendation, RoutingResult
from aect.domain.scoring import CompositeScore
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    TriageZone,
)
from aect.domain.zones import ZoneResult


@pytest.fixture(scope="module")
def roi_config() -> ROIConfig:
    config_path = Path(__file__).parents[2] / "config" / "roi_config.toml"
    return load_roi_config(config_path)


def _make_use_case(
    *,
    title: str = "Test Use Case",
    submitter: str = "Test User",
    department: str = "IT",
    current_state: str = "Manuelle Verarbeitung kostet taeglich mehrere Stunden.",
    desired_state: str = "Automatisierte Extraktion relevanter Informationen.",
    example_process: str = "Eingangsbeleg pruefen, Daten extrahieren, in System uebertragen.",
    employee_category: EmployeeCategory = EmployeeCategory.PROFESSIONAL,
    time_savings_hours_per_case: float = 2.0,
    frequency_per_year: int = 200,
    affected_employees_count: int = 1,
    estimated_license_cost_eur: float = 0.0,
    evidence_level: EvidenceLevel = EvidenceLevel.PURE_ESTIMATE,
    adoption_type: AdoptionType = AdoptionType.VOLUNTARY,
    implementation_approach: ImplementationApproach = ImplementationApproach.STANDARD_PRODUCT,
    data_classification: DataClassification = DataClassification.NO_PERSONAL_DATA,
    contains_pii: bool = False,
    implementation_complexity: int = 2,
    regulatory_pressure: bool = False,
    competitive_pressure: bool = False,
    strategic_priority: bool = False,
) -> UseCaseInput:
    return UseCaseInput(
        title=title,
        submitter=submitter,
        department=department,
        current_state=current_state,
        desired_state=desired_state,
        example_process=example_process,
        employee_category=employee_category,
        time_savings_hours_per_case=time_savings_hours_per_case,
        frequency_per_year=frequency_per_year,
        affected_employees_count=affected_employees_count,
        estimated_license_cost_eur=estimated_license_cost_eur,
        evidence_level=evidence_level,
        adoption_type=adoption_type,
        implementation_approach=implementation_approach,
        data_classification=data_classification,
        contains_pii=contains_pii,
        implementation_complexity=implementation_complexity,
        regulatory_pressure=regulatory_pressure,
        competitive_pressure=competitive_pressure,
        strategic_priority=strategic_priority,
    )


def _zone_str(result: TriageResult) -> str | None:
    if result.zone is None:
        return None
    return result.zone.final_zone.value


# ---------------------------------------------------------------------------
# 10 Use Cases
# hours = time_savings_hours_per_case * frequency_per_year * affected_employees_count
# ---------------------------------------------------------------------------

_UC_LW_1 = _make_use_case(
    title="Rechnungsextraktion -- Buchhaltung",
    time_savings_hours_per_case=3.0,
    frequency_per_year=100,
    affected_employees_count=10,  # 3 000 h/Jahr
    evidence_level=EvidenceLevel.TESTED_PILOTED,
    adoption_type=AdoptionType.MANDATORY,
    implementation_complexity=2,
)

_UC_LW_2 = _make_use_case(
    title="Compliance-Reporting -- Legal",
    time_savings_hours_per_case=4.0,
    frequency_per_year=80,
    affected_employees_count=8,  # 2 560 h/Jahr
    evidence_level=EvidenceLevel.TESTED_PILOTED,
    adoption_type=AdoptionType.MANDATORY,
    implementation_complexity=2,
    data_classification=DataClassification.PSEUDONYMOUS,
)

_UC_CR_1 = _make_use_case(
    title="Vertragsanalyse -- Einkauf",
    time_savings_hours_per_case=2.0,
    frequency_per_year=100,
    affected_employees_count=5,  # 1 000 h/Jahr
    evidence_level=EvidenceLevel.SIMILAR_PROJECT,
    adoption_type=AdoptionType.VOLUNTARY,
    implementation_complexity=3,
)

_UC_CR_2 = _make_use_case(
    title="Support-Ticket-Routing -- Personenbezug",
    time_savings_hours_per_case=1.5,
    frequency_per_year=150,
    affected_employees_count=4,  # 900 h/Jahr
    evidence_level=EvidenceLevel.SIMILAR_PROJECT,
    adoption_type=AdoptionType.VOLUNTARY,
    implementation_complexity=3,
    data_classification=DataClassification.PERSONAL,
    contains_pii=True,
)

_UC_CR_3 = _make_use_case(
    title="Preisindikation -- Angebotserstellung",
    time_savings_hours_per_case=2.5,
    frequency_per_year=80,
    affected_employees_count=3,  # 600 h/Jahr
    evidence_level=EvidenceLevel.SIMILAR_PROJECT,
    adoption_type=AdoptionType.MANDATORY,
    implementation_complexity=3,
)

_UC_MG_1 = _make_use_case(
    title="E-Mail-Kategorisierung -- geringe Auswirkung",
    time_savings_hours_per_case=0.5,
    frequency_per_year=300,
    affected_employees_count=8,  # 1 200 h/Jahr
    adoption_type=AdoptionType.VOLUNTARY,
    implementation_complexity=4,
)

_UC_MG_2 = _make_use_case(
    title="Statusbericht-Zusammenfassung -- sensitive Daten",
    time_savings_hours_per_case=1.0,
    frequency_per_year=130,
    affected_employees_count=5,  # 650 h/Jahr
    adoption_type=AdoptionType.VOLUNTARY,
    implementation_complexity=4,
    data_classification=DataClassification.SENSITIVE_PERSONAL,
    contains_pii=True,
)

_UC_FAIL_1 = _make_use_case(
    title="Kleines Nischenprojekt",
    time_savings_hours_per_case=0.5,
    frequency_per_year=50,
    affected_employees_count=1,  # 25 h -- unter Schwelle
)

_UC_FAIL_2 = _make_use_case(
    title="Einmaliger Report",
    time_savings_hours_per_case=1.0,
    frequency_per_year=80,
    affected_employees_count=1,  # 80 h -- unter Schwelle
)

_UC_FAIL_3 = _make_use_case(
    title="Winzige Nische",
    time_savings_hours_per_case=0.25,
    frequency_per_year=100,
    affected_employees_count=1,  # 25 h -- unter Schwelle
)

_ALL_10 = [
    _UC_LW_1,
    _UC_LW_2,
    _UC_CR_1,
    _UC_CR_2,
    _UC_CR_3,
    _UC_MG_1,
    _UC_MG_2,
    _UC_FAIL_1,
    _UC_FAIL_2,
    _UC_FAIL_3,
]
_PASSING = [_UC_LW_1, _UC_LW_2, _UC_CR_1, _UC_CR_2, _UC_CR_3, _UC_MG_1, _UC_MG_2]
_FAILING = [_UC_FAIL_1, _UC_FAIL_2, _UC_FAIL_3]


# ---------------------------------------------------------------------------
# Snapshot-Tests (Phase A, Tag 20)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("use_case", _FAILING)
def test_vorfilter_fails_below_threshold(
    use_case: UseCaseInput,
    roi_config: ROIConfig,
) -> None:
    result = evaluate_use_case(use_case, roi_config)
    hours = (
        use_case.time_savings_hours_per_case
        * use_case.frequency_per_year
        * use_case.affected_employees_count
    )
    assert not result.passed_vorfilter, (
        f"{use_case.title}: expected fail (hours={hours:.0f}), got pass."
    )


@pytest.mark.parametrize("use_case", _FAILING)
def test_failed_vorfilter_produces_null_value_fields(
    use_case: UseCaseInput,
    roi_config: ROIConfig,
) -> None:
    result = evaluate_use_case(use_case, roi_config)
    assert result.roi is None
    assert result.composite is None
    assert result.zone is None


@pytest.mark.parametrize("use_case", _PASSING)
def test_passing_vorfilter_produces_full_result(
    use_case: UseCaseInput,
    roi_config: ROIConfig,
) -> None:
    result = evaluate_use_case(use_case, roi_config)
    assert result.passed_vorfilter
    assert result.roi is not None, f"{use_case.title}: roi is None"
    assert result.composite is not None, f"{use_case.title}: composite is None"
    assert result.zone is not None, f"{use_case.title}: zone is None"


@pytest.mark.parametrize("use_case", _ALL_10)
def test_routing_and_feasibility_always_populated(
    use_case: UseCaseInput,
    roi_config: ROIConfig,
) -> None:
    result = evaluate_use_case(use_case, roi_config)
    assert result.routing is not None
    assert result.feasibility is not None


@pytest.mark.parametrize("use_case", [_UC_LW_1, _UC_LW_2])
def test_strong_cases_are_actionable(
    use_case: UseCaseInput,
    roi_config: ROIConfig,
) -> None:
    result = evaluate_use_case(use_case, roi_config)
    assert result.is_actionable, (
        f"{use_case.title} should be actionable. "
        f"Zone: {_zone_str(result)}, ROI: {result.roi}"
    )


def test_triage_result_is_immutable(roi_config: ROIConfig) -> None:
    result = evaluate_use_case(_UC_LW_1, roi_config)
    with pytest.raises(AttributeError):
        result.passed_vorfilter = False


def test_pipeline_is_deterministic(roi_config: ROIConfig) -> None:
    result_a = evaluate_use_case(_UC_CR_1, roi_config)
    result_b = evaluate_use_case(_UC_CR_1, roi_config)
    assert result_a == result_b


def test_title_propagated_to_result(roi_config: ROIConfig) -> None:
    for uc in _ALL_10:
        result = evaluate_use_case(uc, roi_config)
        assert result.title == uc.title


# ---------------------------------------------------------------------------
# Coverage-Ergaenzung Tag 21: _cost_tier + is_actionable
# ---------------------------------------------------------------------------


def test_cost_tier_all_bands() -> None:
    """_cost_tier mappt Lizenzkosten korrekt auf Kostenstufe 1-3."""
    assert _cost_tier(0.0) == 1
    assert _cost_tier(4_999.99) == 1
    assert _cost_tier(5_000.0) == 2
    assert _cost_tier(24_999.99) == 2
    assert _cost_tier(25_000.0) == 3
    assert _cost_tier(100_000.0) == 3


def _minimal_triage(*, passed: bool, zone: TriageZone | None) -> TriageResult:
    """Baut minimales TriageResult fuer is_actionable-Tests."""
    vorfilter = FilterResult(
        passes=passed,
        failed_criteria=[] if passed else ["Theoretisches Potenzial"],
        details={"Theoretisches Potenzial": passed},
    )
    routing = RoutingResult(
        recommendation=RoutingRecommendation.BORDERLINE,
        confidence="LOW",
        automation_signals=(),
        ai_signals=(),
        risk_flags=(),
    )
    feasibility = FeasibilityResult(is_feasible=True, flags=())

    roi: ROIResult | None = None
    composite: CompositeScore | None = None
    zone_result: ZoneResult | None = None

    if zone is not None:
        roi = ROIResult(
            theoretical_potential_eur=Decimal("60000.00"),
            usage_factor=1.0,
            evidence_factor=1.0,
            expected_benefit_eur=Decimal("60000.00"),
            license_cost_annual_eur=Decimal("0.00"),
            net_expected_benefit_eur=Decimal("60000.00"),
            hours_per_year=500.0,
            passes_prefilter=True,
            prefilter_fail_reason=None,
        )
        composite = CompositeScore(
            complexity_score=2, cost_score=1, data_protection_score=0, total=3
        )
        zone_result = ZoneResult(
            base_zone=zone,
            final_zone=zone,
            handlungsdruck_elevated=False,
            reason="Test",
            confidence_score=1.0,
            confidence_label="hoch",
        )

    return TriageResult(
        title="Test-Actionable",
        passed_vorfilter=passed,
        vorfilter=vorfilter,
        routing=routing,
        feasibility=feasibility,
        roi=roi,
        composite=composite,
        zone=zone_result,
    )


@pytest.mark.parametrize(
    "passed,zone,expected",
    [
        (False, None, False),
        (True, TriageZone.MARGINAL_GAIN, False),
        (True, TriageZone.CALCULATED_RISK, True),
        (True, TriageZone.LIKELY_WIN, True),
    ],
)
def test_is_actionable_all_branches(
    passed: bool,
    zone: TriageZone | None,
    expected: bool,
) -> None:
    """is_actionable ist True genau fuer LIKELY_WIN und CALCULATED_RISK."""
    result = _minimal_triage(passed=passed, zone=zone)
    assert result.is_actionable == expected


def test_handlungsdruck_score_counts_active_flags() -> None:
    """1 Basis-Punkt + 1 pro aktivem Flag, Wertebereich 1-4."""
    base = _make_use_case()
    assert handlungsdruck_score(base) == 1

    all_flags = _make_use_case(
        regulatory_pressure=True,
        competitive_pressure=True,
        strategic_priority=True,
    )
    assert handlungsdruck_score(all_flags) == 4


# ---------------------------------------------------------------------------
# F-001: Vorfilter-Schwellen kommen aus der ROIConfig, nicht aus Modul-Defaults
# ---------------------------------------------------------------------------


def test_prefilter_uses_config_thresholds_not_module_defaults(
    roi_config: ROIConfig,
) -> None:
    """Eine geaenderte Config-Schwelle MUSS das Vorfilter-Ergebnis aendern.

    Vor F-001 nutzte evaluate_use_case() hartcodierte Defaults in filters.py --
    dieselbe Case-Eingabe bestand den Vorfilter unabhaengig von der TOML-Config
    (Config-Edit = stiller No-op, dokumentiert als Limitation #14).
    """
    use_case = _make_use_case(
        time_savings_hours_per_case=2.0,
        frequency_per_year=500,
        affected_employees_count=5,
        adoption_type=AdoptionType.MANDATORY,
        evidence_level=EvidenceLevel.TESTED_PILOTED,
    )
    baseline = evaluate_use_case(use_case, roi_config)
    assert baseline.passed_vorfilter is True

    strict_config = dataclasses.replace(
        roi_config,
        min_potential_eur=baseline.roi.theoretical_potential_eur * 2,  # type: ignore[union-attr]
    )
    strict = evaluate_use_case(use_case, strict_config)
    assert strict.passed_vorfilter is False
    assert "Theoretisches Potenzial" in strict.vorfilter.failed_criteria

    # Konsistenz beider Pfade: FilterResult (Pipeline) und passes_prefilter
    # (ROI-Engine) urteilen jetzt gegen dieselben Config-Schwellen.
    strict_roi = evaluate_use_case(use_case, strict_config)
    assert strict_roi.vorfilter.passes is False

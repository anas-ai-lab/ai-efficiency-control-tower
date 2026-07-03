"""Tests fuer Score-Breakdown-Diagnostik (Tag 65, Master-Plan v3.1 Phase E,
ADR-0031)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aect.application.eval import (
    EvalCase,
    build_score_breakdown,
    load_eval_cases,
)
from aect.domain import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    ROIConfig,
    TriageZone,
    UseCaseInput,
    ZoneClassifier,
    load_roi_config,
    load_zone_classifier,
)

GOLDEN_CASES_PATH = Path("evals/golden/use_cases.jsonl")


@pytest.fixture(scope="module")
def roi_config() -> ROIConfig:
    config_path = Path(__file__).parents[3] / "config" / "roi_config.toml"
    return load_roi_config(config_path)


@pytest.fixture(scope="module")
def classifier() -> ZoneClassifier:
    config_path = Path(__file__).parents[3] / "config" / "zone_thresholds.yaml"
    return load_zone_classifier(config_path)


@pytest.fixture(scope="module")
def golden_cases_by_id() -> dict[str, EvalCase]:
    return {c.case_id: c for c in load_eval_cases(GOLDEN_CASES_PATH)}


def _make_use_case(**overrides: object) -> UseCaseInput:
    defaults: dict[str, object] = {
        "title": "Test Use Case fuer Breakdown",
        "submitter": "Test User",
        "department": "IT",
        "country": "de",
        "current_state": "Manuelle Verarbeitung kostet taeglich mehrere Stunden.",
        "desired_state": "Automatisierte Extraktion relevanter Informationen.",
        "example_process": (
            "Eingangsbeleg pruefen, Daten extrahieren, in System uebertragen."
        ),
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "time_savings_hours_per_case": 2.0,
        "frequency_per_year": 200,
        "affected_employees_count": 10,
        "estimated_license_cost_eur": 0.0,
        "evidence_level": EvidenceLevel.TESTED_PILOTED,
        "adoption_type": AdoptionType.MANDATORY,
        "implementation_approach": ImplementationApproach.STANDARD_PRODUCT,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
        "contains_pii": False,
        "implementation_complexity": 2,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
    }
    defaults.update(overrides)
    return UseCaseInput(**defaults)  # type: ignore[arg-type]


class TestBuildScoreBreakdown:
    def test_failed_vorfilter_case_has_none_fields(
        self, roi_config: ROIConfig, classifier: ZoneClassifier
    ) -> None:
        case = EvalCase(
            case_id="tiny",
            use_case=_make_use_case(
                time_savings_hours_per_case=0.5,
                frequency_per_year=50,
                affected_employees_count=1,
            ),
        )
        result = build_score_breakdown(case, roi_config, classifier)
        assert result.passed_vorfilter is False
        assert result.predicted_zone is None
        assert result.composite_total is None
        assert "Vorfilter nicht bestanden" in result.explanation

    def test_likely_win_case_explanation_mentions_basis_zone(
        self, roi_config: ROIConfig, classifier: ZoneClassifier
    ) -> None:
        case = EvalCase(
            case_id="strong",
            use_case=_make_use_case(
                time_savings_hours_per_case=4.0,
                frequency_per_year=200,
                affected_employees_count=15,
                evidence_level=EvidenceLevel.TESTED_PILOTED,
                adoption_type=AdoptionType.MANDATORY,
                implementation_complexity=2,
            ),
        )
        result = build_score_breakdown(case, roi_config, classifier)
        assert result.predicted_zone == TriageZone.LIKELY_WIN
        assert "Basis-Zone LIKELY_WIN" in result.explanation

    def test_golden_001_breakdown_matches_known_values(
        self,
        roi_config: ROIConfig,
        classifier: ZoneClassifier,
        golden_cases_by_id: dict[str, EvalCase],
    ) -> None:
        """Regression-Anker: golden-001 weicht ab, weil Composite (6) ueber der
        LIKELY_WIN-Obergrenze (4) liegt, obwohl der Nutzen die Schwelle reisst."""
        result = build_score_breakdown(
            golden_cases_by_id["golden-001"], roi_config, classifier
        )
        assert result.composite_total == 6
        assert result.handlungsdruck_score == 1
        assert result.predicted_zone == TriageZone.CALCULATED_RISK
        assert result.expected_zone == TriageZone.LIKELY_WIN
        assert result.is_match is False

    def test_golden_003_breakdown_matches_known_values(
        self,
        roi_config: ROIConfig,
        classifier: ZoneClassifier,
        golden_cases_by_id: dict[str, EvalCase],
    ) -> None:
        """Regression-Anker: golden-003 landet in MARGINAL_GAIN, weil Composite
        (8) auch die CALCULATED_RISK-Obergrenze (7) reisst; Handlungsdruck (3)
        liegt knapp unter der Hochstufungs-Schwelle (4)."""
        result = build_score_breakdown(
            golden_cases_by_id["golden-003"], roi_config, classifier
        )
        assert result.composite_total == 8
        assert result.handlungsdruck_score == 3
        assert result.predicted_zone == TriageZone.MARGINAL_GAIN
        assert result.expected_zone == TriageZone.CALCULATED_RISK
        assert result.is_match is False

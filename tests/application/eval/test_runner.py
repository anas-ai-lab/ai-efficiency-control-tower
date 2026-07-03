"""Tests fuer den Eval-Runner (Master-Plan v3.1 Phase E, ADR-0030).

_make_use_case()-Defaults entsprechen exakt _UC_LW_1 aus tests/domain/test_pipeline.py
(verifiziert: besteht Vorfilter, ist actionable) bzw. _UC_FAIL_1 fuer den
Vorfilter-Fail-Fall -- keine neu erfundenen Zahlen, sondern bereits bewiesene
Snapshot-Faelle.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aect.application.eval import (
    EvalCase,
    EvalCaseResult,
    load_eval_cases,
    run_eval,
    write_report,
)
from aect.domain import (
    AdoptionType,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    ROIConfig,
    TriageZone,
    UseCaseInput,
    load_roi_config,
)

GOLDEN_CASES_PATH = Path("evals/golden/use_cases.jsonl")

SYNTHETIC_CASES_PATH = Path("evals/synthetic/use_cases.jsonl")


@pytest.fixture(scope="module")
def roi_config() -> ROIConfig:
    config_path = Path(__file__).parents[3] / "config" / "roi_config.toml"
    return load_roi_config(config_path)


def _make_use_case(
    *,
    title: str = "Test Use Case fuer Eval-Runner",
    time_savings_hours_per_case: float = 3.0,
    frequency_per_year: int = 100,
    affected_employees_count: int = 10,
) -> UseCaseInput:
    return UseCaseInput(
        title=title,
        submitter="Test User",
        department="IT",
        country=Country.DE,
        current_state="Manuelle Verarbeitung kostet taeglich mehrere Stunden.",
        desired_state="Automatisierte Extraktion relevanter Informationen.",
        example_process="Eingangsbeleg pruefen, Daten extrahieren, in System uebertragen.",
        employee_category=EmployeeCategory.PROFESSIONAL,
        time_savings_hours_per_case=time_savings_hours_per_case,
        frequency_per_year=frequency_per_year,
        affected_employees_count=affected_employees_count,
        estimated_license_cost_eur=0.0,
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        adoption_type=AdoptionType.MANDATORY,
        implementation_approach=ImplementationApproach.STANDARD_PRODUCT,
        data_classification=DataClassification.NO_PERSONAL_DATA,
        contains_pii=False,
        implementation_complexity=2,
        regulatory_pressure=False,
        competitive_pressure=False,
        strategic_priority=False,
    )


class TestRunEval:
    def test_returns_one_result_per_case(self, roi_config: ROIConfig) -> None:
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        results = run_eval(cases, roi_config)
        assert len(results) == 25
        assert all(isinstance(r, EvalCaseResult) for r in results)

    def test_only_golden_004_has_none_match(self, roi_config: ROIConfig) -> None:
        """Seit Tag 64 tragen golden-001 bis golden-003 ein Experten-Label;
        nur golden-004 (Vorfilter-Grenzfall, bewusst unlabeled) hat kein
        Vergleichsergebnis. Ob die drei gelabelten Cases tatsaechlich
        uebereinstimmen (is_match True oder False), ist das Eval-Ergebnis --
        keine Testvoraussetzung."""
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        results = run_eval(cases, roi_config)
        by_id = {r.case_id: r for r in results}

        assert by_id["golden-004"].is_match is None
        for case_id in ("golden-001", "golden-002", "golden-003"):
            assert by_id[case_id].is_match is not None

    def test_predicted_zone_is_consistent_with_pipeline(
        self, roi_config: ROIConfig
    ) -> None:
        """Konsistenz-Eval: gleicher Use Case -> gleiches predicted_zone (Eval-Methodik)."""
        case = EvalCase(case_id="consistency-check", use_case=_make_use_case())
        result_a = run_eval([case], roi_config)[0]
        result_b = run_eval([case], roi_config)[0]
        assert result_a.predicted_zone == result_b.predicted_zone

    def test_failed_vorfilter_case_has_none_predicted_zone(
        self, roi_config: ROIConfig
    ) -> None:
        tiny_case = EvalCase(
            case_id="below-threshold",
            use_case=_make_use_case(
                time_savings_hours_per_case=0.5,
                frequency_per_year=50,
                affected_employees_count=1,
            ),
        )
        result = run_eval([tiny_case], roi_config)[0]
        assert result.passed_vorfilter is False
        assert result.predicted_zone is None

    def test_correct_label_produces_match_true(self, roi_config: ROIConfig) -> None:
        unlabeled = EvalCase(case_id="probe", use_case=_make_use_case())
        actual_zone = run_eval([unlabeled], roi_config)[0].predicted_zone
        assert actual_zone is not None  # Testfall muss Vorfilter bestehen

        labeled = EvalCase(
            case_id="probe-labeled",
            use_case=_make_use_case(),
            expected_zone=actual_zone,
        )
        result = run_eval([labeled], roi_config)[0]
        assert result.is_match is True

    def test_wrong_label_produces_match_false(self, roi_config: ROIConfig) -> None:
        unlabeled = EvalCase(case_id="probe", use_case=_make_use_case())
        actual_zone = run_eval([unlabeled], roi_config)[0].predicted_zone
        assert actual_zone is not None

        wrong_zone = next(z for z in TriageZone if z != actual_zone)
        labeled = EvalCase(
            case_id="probe-wrong-label",
            use_case=_make_use_case(),
            expected_zone=wrong_zone,
        )
        result = run_eval([labeled], roi_config)[0]
        assert result.is_match is False


class TestWriteReport:
    def test_report_structure_for_golden_cases(
        self, roi_config: ROIConfig, tmp_path: Path
    ) -> None:
        """Seit Tag 64: golden-004 bleibt bewusst unlabeled (Vorfilter-Grenzfall,
        siehe test_only_golden_004_has_none_match). Auf 25 Cases erweitert: 24
        gelabelt, weiterhin nur golden-004 ohne Label."""
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        results = run_eval(cases, roi_config)
        report_path = tmp_path / "report.json"

        write_report(results, report_path)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["total_cases"] == 25
        assert report["labeled_cases"] == 24
        assert report["agreement_count"] <= 24
        assert report["agreement_rate"] is not None
        assert len(report["results"]) == 25

    def test_agreement_rate_computed_over_labeled_cases_only(
        self, roi_config: ROIConfig, tmp_path: Path
    ) -> None:
        unlabeled = EvalCase(case_id="probe", use_case=_make_use_case())
        actual_zone = run_eval([unlabeled], roi_config)[0].predicted_zone
        assert actual_zone is not None
        wrong_zone = next(z for z in TriageZone if z != actual_zone)

        cases = [
            EvalCase(
                case_id="match", use_case=_make_use_case(), expected_zone=actual_zone
            ),
            EvalCase(
                case_id="mismatch", use_case=_make_use_case(), expected_zone=wrong_zone
            ),
            EvalCase(case_id="unlabeled", use_case=_make_use_case()),
        ]
        results = run_eval(cases, roi_config)
        report_path = tmp_path / "report.json"
        write_report(results, report_path)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["total_cases"] == 3
        assert report["labeled_cases"] == 2
        assert report["agreement_count"] == 1
        assert report["agreement_rate"] == pytest.approx(0.5)

    def test_creates_parent_directories(
        self, roi_config: ROIConfig, tmp_path: Path
    ) -> None:
        cases = load_eval_cases(GOLDEN_CASES_PATH)
        results = run_eval(cases, roi_config)
        nested_path = tmp_path / "reports" / "nested" / "report.json"

        write_report(results, nested_path)

        assert nested_path.exists()


class TestRunEvalOnSyntheticCases:
    """Tag 66: operationalisiert das Gate-E->F-Kriterium aus
    session-protocol v3 SS2 (>= 30 Cases ohne Crash) als pytest-Regression
    statt als einmaligen Skript-Lauf."""

    def test_runs_without_crash_on_all_synthetic_cases(
        self, roi_config: ROIConfig
    ) -> None:
        cases = load_eval_cases(SYNTHETIC_CASES_PATH)
        assert len(cases) >= 30
        results = run_eval(cases, roi_config)
        assert len(results) == len(cases)

    def test_report_has_no_labeled_cases(
        self, roi_config: ROIConfig, tmp_path: Path
    ) -> None:
        """Synthetic-Cases sind unlabeled -- agreement_rate ist strukturell
        None, kein Fehlerfall (siehe write_report())."""
        cases = load_eval_cases(SYNTHETIC_CASES_PATH)
        results = run_eval(cases, roi_config)
        report_path = tmp_path / "synthetic_report.json"
        write_report(results, report_path)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["labeled_cases"] == 0
        assert report["agreement_rate"] is None

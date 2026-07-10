"""Tests für src/aect/domain/scoring.py (V4-Modell, Range 1–9)."""

import pytest

from aect.domain.scoring import (
    COMPLEXITY_BY_APPROACH,
    CompositeScore,
    compute_composite_score,
)
from aect.domain.types import DataClassification, ImplementationApproach


class TestCompositeScoreInvarianten:
    def test_minimaler_score_valid(self) -> None:
        score = CompositeScore(
            complexity_score=1, cost_score=0, data_protection_score=0, total=1
        )
        assert score.total == 1

    def test_maximaler_score_valid(self) -> None:
        score = CompositeScore(
            complexity_score=5, cost_score=2, data_protection_score=2, total=9
        )
        assert score.total == 9

    def test_total_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="total"):
            CompositeScore(
                complexity_score=1, cost_score=0, data_protection_score=0, total=99
            )

    def test_complexity_zu_hoch_raises(self) -> None:
        with pytest.raises(ValueError, match="complexity_score"):
            CompositeScore(
                complexity_score=6, cost_score=1, data_protection_score=0, total=7
            )

    def test_cost_zu_hoch_raises(self) -> None:
        with pytest.raises(ValueError, match="cost_score"):
            CompositeScore(
                complexity_score=1, cost_score=3, data_protection_score=0, total=4
            )


class TestEffortLabel:
    def test_niedrig(self) -> None:
        score = CompositeScore(
            complexity_score=1, cost_score=0, data_protection_score=0, total=1
        )
        assert score.effort_label == "NIEDRIG"

    def test_niedrig_obere_grenze(self) -> None:
        # total == 3 ist die obere NIEDRIG-Grenze.
        score = CompositeScore(
            complexity_score=1, cost_score=1, data_protection_score=1, total=3
        )
        assert score.effort_label == "NIEDRIG"

    def test_mittel(self) -> None:
        score = CompositeScore(
            complexity_score=3, cost_score=2, data_protection_score=0, total=5
        )
        assert score.effort_label == "MITTEL"

    def test_mittel_obere_grenze(self) -> None:
        # total == 6 ist die obere MITTEL-Grenze.
        score = CompositeScore(
            complexity_score=4, cost_score=2, data_protection_score=0, total=6
        )
        assert score.effort_label == "MITTEL"

    def test_hoch(self) -> None:
        # total == 7 ist bereits HOCH (> 6).
        score = CompositeScore(
            complexity_score=5, cost_score=0, data_protection_score=2, total=7
        )
        assert score.effort_label == "HOCH"

    def test_hoch_maximal(self) -> None:
        score = CompositeScore(
            complexity_score=5, cost_score=2, data_protection_score=2, total=9
        )
        assert score.effort_label == "HOCH"


class TestComplexityByApproach:
    @pytest.mark.parametrize(
        "approach,expected",
        [
            (ImplementationApproach.SIMPLE_INTEGRATION, 1),
            (ImplementationApproach.DEVELOPMENT_ON_EXISTING, 2),
            (ImplementationApproach.API_INTEGRATION, 3),
            (ImplementationApproach.CUSTOM_DEVELOPMENT, 4),
            (ImplementationApproach.NEW_TOOL, 5),
        ],
    )
    def test_mapping_is_ordinal_1_to_5(
        self, approach: ImplementationApproach, expected: int
    ) -> None:
        assert COMPLEXITY_BY_APPROACH[approach] == expected

    def test_every_approach_is_mapped(self) -> None:
        # Jeder Enum-Wert braucht einen Komplexitaets-Punkt (sonst KeyError im Score).
        assert set(COMPLEXITY_BY_APPROACH) == set(ImplementationApproach)


class TestComputeCompositeScoreComplexity:
    def test_complexity_from_approach(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.NEW_TOOL,
            implementation_cost_eur=0.0,
            license_cost_eur=0.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
        )
        assert score.complexity_score == 5
        assert score.total == 5


class TestCostPoints:
    def test_below_both_thresholds_zero_points(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=9_999.99,
            license_cost_eur=9_999.99,
            data_classification=DataClassification.NO_PERSONAL_DATA,
            impl_cost_point_min_eur=10_000.0,
            license_cost_point_min_eur=10_000.0,
        )
        assert score.cost_score == 0

    def test_impl_cost_at_threshold_one_point(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=10_000.0,
            license_cost_eur=0.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
            impl_cost_point_min_eur=10_000.0,
            license_cost_point_min_eur=10_000.0,
        )
        assert score.cost_score == 1

    def test_license_cost_at_threshold_one_point(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=0.0,
            license_cost_eur=10_000.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
            impl_cost_point_min_eur=10_000.0,
            license_cost_point_min_eur=10_000.0,
        )
        assert score.cost_score == 1

    def test_both_at_threshold_two_points(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=10_000.0,
            license_cost_eur=50_000.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
            impl_cost_point_min_eur=10_000.0,
            license_cost_point_min_eur=10_000.0,
        )
        assert score.cost_score == 2

    def test_default_threshold_is_10000(self) -> None:
        # Ohne explizite Schwellen gilt der Default 10 000.
        below = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=9_999.99,
            license_cost_eur=0.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
        )
        at = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=10_000.0,
            license_cost_eur=0.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
        )
        assert below.cost_score == 0
        assert at.cost_score == 1


class TestDataProtectionMapping:
    @pytest.mark.parametrize(
        "classification,expected",
        [
            (DataClassification.NO_PERSONAL_DATA, 0),
            (DataClassification.PSEUDONYMOUS, 1),
            (DataClassification.PERSONAL, 1),
            (DataClassification.SENSITIVE_PERSONAL, 2),
        ],
    )
    def test_dsgvo_mapping(
        self, classification: DataClassification, expected: int
    ) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=0.0,
            license_cost_eur=0.0,
            data_classification=classification,
        )
        assert score.data_protection_score == expected

    def test_personal_equals_pseudonymous(self) -> None:
        """Pseudonymisiert bleibt personenbezogen (Art. 4 Nr. 5 DSGVO) → Score 1,
        gleich PERSONAL."""
        pseudo = compute_composite_score(
            approach=ImplementationApproach.API_INTEGRATION,
            implementation_cost_eur=0.0,
            license_cost_eur=0.0,
            data_classification=DataClassification.PSEUDONYMOUS,
        )
        personal = compute_composite_score(
            approach=ImplementationApproach.API_INTEGRATION,
            implementation_cost_eur=0.0,
            license_cost_eur=0.0,
            data_classification=DataClassification.PERSONAL,
        )
        assert pseudo.data_protection_score == personal.data_protection_score == 1


class TestComputeCompositeScoreRange:
    def test_minimal(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.SIMPLE_INTEGRATION,
            implementation_cost_eur=0.0,
            license_cost_eur=0.0,
            data_classification=DataClassification.NO_PERSONAL_DATA,
        )
        assert score.total == 1
        assert score.effort_label == "NIEDRIG"

    def test_maximal(self) -> None:
        score = compute_composite_score(
            approach=ImplementationApproach.NEW_TOOL,
            implementation_cost_eur=50_000.0,
            license_cost_eur=50_000.0,
            data_classification=DataClassification.SENSITIVE_PERSONAL,
        )
        assert score.total == 9
        assert score.effort_label == "HOCH"

    @pytest.mark.parametrize(
        "approach,impl_cost,license_cost,classification",
        [
            (
                ImplementationApproach.SIMPLE_INTEGRATION,
                0.0,
                0.0,
                DataClassification.NO_PERSONAL_DATA,
            ),
            (
                ImplementationApproach.API_INTEGRATION,
                10_000.0,
                0.0,
                DataClassification.PSEUDONYMOUS,
            ),
            (
                ImplementationApproach.NEW_TOOL,
                50_000.0,
                50_000.0,
                DataClassification.SENSITIVE_PERSONAL,
            ),
            (
                ImplementationApproach.DEVELOPMENT_ON_EXISTING,
                0.0,
                20_000.0,
                DataClassification.PERSONAL,
            ),
        ],
    )
    def test_total_immer_in_range_1_bis_9(
        self,
        approach: ImplementationApproach,
        impl_cost: float,
        license_cost: float,
        classification: DataClassification,
    ) -> None:
        score = compute_composite_score(
            approach=approach,
            implementation_cost_eur=impl_cost,
            license_cost_eur=license_cost,
            data_classification=classification,
        )
        assert 1 <= score.total <= 9, f"total={score.total} außerhalb [1, 9]"

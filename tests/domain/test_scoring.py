"""Tests für src/aect/domain/scoring.py"""

import pytest

from aect.domain.scoring import CompositeScore, compute_composite_score
from aect.domain.types import DataClassification


class TestCompositeScoreInvarianten:
    def test_minimaler_score_valid(self) -> None:
        score = CompositeScore(
            complexity_score=1, cost_score=1, data_protection_score=0, total=2
        )
        assert score.total == 2

    def test_maximaler_score_valid(self) -> None:
        score = CompositeScore(
            complexity_score=5, cost_score=3, data_protection_score=2, total=10
        )
        assert score.total == 10

    def test_total_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="total"):
            CompositeScore(
                complexity_score=1, cost_score=1, data_protection_score=0, total=99
            )

    def test_complexity_zu_hoch_raises(self) -> None:
        with pytest.raises(ValueError, match="complexity_score"):
            CompositeScore(
                complexity_score=6, cost_score=1, data_protection_score=0, total=7
            )

    def test_cost_zu_hoch_raises(self) -> None:
        with pytest.raises(ValueError, match="cost_score"):
            CompositeScore(
                complexity_score=1, cost_score=4, data_protection_score=0, total=5
            )


class TestEffortLabel:
    def test_niedrig(self) -> None:
        score = CompositeScore(
            complexity_score=1, cost_score=1, data_protection_score=0, total=2
        )
        assert score.effort_label == "NIEDRIG"

    def test_niedrig_obere_grenze(self) -> None:
        score = CompositeScore(
            complexity_score=2, cost_score=1, data_protection_score=1, total=4
        )
        assert score.effort_label == "NIEDRIG"

    def test_mittel(self) -> None:
        score = CompositeScore(
            complexity_score=3, cost_score=2, data_protection_score=0, total=5
        )
        assert score.effort_label == "MITTEL"

    def test_hoch(self) -> None:
        score = CompositeScore(
            complexity_score=5, cost_score=3, data_protection_score=2, total=10
        )
        assert score.effort_label == "HOCH"


class TestComputeCompositeScore:
    def test_keine_personendaten_minimal(self) -> None:
        score = compute_composite_score(
            complexity=1,
            cost=1,
            data_classification=DataClassification.NO_PERSONAL_DATA,
        )
        assert score.total == 2
        assert score.data_protection_score == 0
        assert score.effort_label == "NIEDRIG"

    def test_sensitive_personal_maximal(self) -> None:
        score = compute_composite_score(
            complexity=5,
            cost=3,
            data_classification=DataClassification.SENSITIVE_PERSONAL,
        )
        assert score.total == 10
        assert score.data_protection_score == 2
        assert score.effort_label == "HOCH"

    def test_personal_gleich_sensitive_personal_score(self) -> None:
        """PERSONAL und SENSITIVE_PERSONAL ergeben denselben Datenschutz-Score (2).
        Beide Art. 4 / Art. 9 DSGVO — gleich hoher Aufwand im Composite."""
        personal = compute_composite_score(3, 2, DataClassification.PERSONAL)
        sensitive = compute_composite_score(3, 2, DataClassification.SENSITIVE_PERSONAL)
        assert personal.data_protection_score == sensitive.data_protection_score == 2

    def test_pseudonymous_mittelwert(self) -> None:
        score = compute_composite_score(
            complexity=3,
            cost=2,
            data_classification=DataClassification.PSEUDONYMOUS,
        )
        assert score.data_protection_score == 1
        assert score.total == 6

    def test_complexity_null_raises(self) -> None:
        with pytest.raises(ValueError, match="complexity"):
            compute_composite_score(
                complexity=0,
                cost=1,
                data_classification=DataClassification.NO_PERSONAL_DATA,
            )

    def test_cost_zu_hoch_raises(self) -> None:
        with pytest.raises(ValueError, match="cost"):
            compute_composite_score(
                complexity=1,
                cost=4,
                data_classification=DataClassification.NO_PERSONAL_DATA,
            )

    @pytest.mark.parametrize(
        "complexity,cost,classification",
        [
            (1, 1, DataClassification.NO_PERSONAL_DATA),
            (3, 2, DataClassification.PSEUDONYMOUS),
            (5, 3, DataClassification.SENSITIVE_PERSONAL),
            (2, 1, DataClassification.NO_PERSONAL_DATA),
            (4, 3, DataClassification.PERSONAL),
        ],
    )
    def test_total_immer_in_range_2_bis_10(
        self,
        complexity: int,
        cost: int,
        classification: DataClassification,
    ) -> None:
        score = compute_composite_score(complexity, cost, classification)
        assert 2 <= score.total <= 10, f"total={score.total} außerhalb [2, 10]"

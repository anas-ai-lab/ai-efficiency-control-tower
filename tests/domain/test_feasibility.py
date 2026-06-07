"""Tests for FeasibilityChecker.

Each flag is tested in isolation and in combination.
Boundary conditions for string lengths and numeric thresholds are covered.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from aect.domain.feasibility import FeasibilityChecker, FeasibilityFlag

# Helpers
_LONG_TEXT = "x" * 60  # clearly above _MIN_SITUATION_LEN (50)
_SHORT_TEXT = "x" * 20  # clearly below
_LONG_EXAMPLE = "x" * 35  # above _MIN_EXAMPLE_LEN (30)
_SHORT_EXAMPLE = "x" * 10  # below


@pytest.fixture
def checker() -> FeasibilityChecker:
    return FeasibilityChecker()


class TestFeasibleCase:
    def test_all_checks_pass(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=100,
        )
        assert r.is_feasible
        assert r.flags == ()
        assert r.recommendation is None

    def test_has_flag_returns_false_when_feasible(
        self, checker: FeasibilityChecker
    ) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("1"),
            occurrences_per_month=1,
        )
        assert not r.has_flag(FeasibilityFlag.DESCRIPTION_TOO_VAGUE)


class TestIndividualFlags:
    def test_description_too_vague_current_short(
        self, checker: FeasibilityChecker
    ) -> None:
        r = checker.check(
            current_situation=_SHORT_TEXT,  # too short
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=50,
        )
        assert r.has_flag(FeasibilityFlag.DESCRIPTION_TOO_VAGUE)
        assert not r.is_feasible

    def test_description_too_vague_target_short(
        self, checker: FeasibilityChecker
    ) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_SHORT_TEXT,  # too short
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=50,
        )
        assert r.has_flag(FeasibilityFlag.DESCRIPTION_TOO_VAGUE)

    def test_missing_example(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_SHORT_EXAMPLE,  # too short
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=50,
        )
        assert r.has_flag(FeasibilityFlag.MISSING_EXAMPLE)

    def test_missing_example_empty_string(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process="",
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=50,
        )
        assert r.has_flag(FeasibilityFlag.MISSING_EXAMPLE)

    def test_no_time_saving_zero(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("0"),  # zero
            occurrences_per_month=50,
        )
        assert r.has_flag(FeasibilityFlag.NO_TIME_SAVING)

    def test_no_time_saving_negative(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("-5"),
            occurrences_per_month=50,
        )
        assert r.has_flag(FeasibilityFlag.NO_TIME_SAVING)

    def test_not_recurring_zero(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=0,  # not recurring
        )
        assert r.has_flag(FeasibilityFlag.NOT_RECURRING)


class TestMultipleFlagsAndRecommendation:
    def test_all_flags_at_once(self, checker: FeasibilityChecker) -> None:
        r = checker.check(
            current_situation=_SHORT_TEXT,
            target_situation=_SHORT_TEXT,
            example_process=_SHORT_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("0"),
            occurrences_per_month=0,
        )
        assert not r.is_feasible
        assert len(r.flags) == 4
        assert r.has_flag(FeasibilityFlag.DESCRIPTION_TOO_VAGUE)
        assert r.has_flag(FeasibilityFlag.MISSING_EXAMPLE)
        assert r.has_flag(FeasibilityFlag.NO_TIME_SAVING)
        assert r.has_flag(FeasibilityFlag.NOT_RECURRING)

    def test_recommendation_present_when_infeasible(
        self, checker: FeasibilityChecker
    ) -> None:
        r = checker.check(
            current_situation=_SHORT_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=50,
        )
        assert not r.is_feasible
        assert r.recommendation is not None
        assert len(r.recommendation) > 0

    def test_recommendation_none_when_feasible(
        self, checker: FeasibilityChecker
    ) -> None:
        r = checker.check(
            current_situation=_LONG_TEXT,
            target_situation=_LONG_TEXT,
            example_process=_LONG_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("30"),
            occurrences_per_month=100,
        )
        assert r.recommendation is None

    def test_recommendation_mentions_all_active_flags(
        self, checker: FeasibilityChecker
    ) -> None:
        r = checker.check(
            current_situation=_SHORT_TEXT,
            target_situation=_SHORT_TEXT,
            example_process=_SHORT_EXAMPLE,
            time_saved_minutes_per_occurrence=Decimal("0"),
            occurrences_per_month=0,
        )
        assert r.recommendation is not None
        # Each flag should result in actionable text
        assert "Ist" in r.recommendation or "Soll" in r.recommendation
        assert "Beispiel" in r.recommendation
        assert "Zeitersparnis" in r.recommendation
        assert "Monat" in r.recommendation

"""Tests for ZoneClassifier and Handlungsdruck elevation.

Unit tests cover all three base zones, boundary conditions, elevation
in both directions, and the no-op case. Property-based tests verify
two invariants: (1) elevation never lowers a zone, (2) higher benefit
produces same or better base zone (monotonicity in benefit dimension).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from aect.domain.types import TriageZone
from aect.domain.zones import ZoneClassifier, load_zone_classifier

# ---------------------------------------------------------------------------
# Test fixture — fixed thresholds, independent of config file
# ---------------------------------------------------------------------------

_LW_MIN = Decimal("50000")
_LW_MAX_C = 4
_CR_MIN = Decimal("5000")
_CR_MAX_C = 7
_HD_THRESHOLD = 4


@pytest.fixture
def clf() -> ZoneClassifier:
    return ZoneClassifier(
        likely_win_min_benefit=_LW_MIN,
        likely_win_max_composite=_LW_MAX_C,
        calculated_risk_min_benefit=_CR_MIN,
        calculated_risk_max_composite=_CR_MAX_C,
        handlungsdruck_elevation_threshold=_HD_THRESHOLD,
    )


# ---------------------------------------------------------------------------
# Base zone classification
# ---------------------------------------------------------------------------


class TestBaseZone:
    def test_likely_win_high_benefit_low_composite(self, clf: ZoneClassifier) -> None:
        r = clf.classify(Decimal("75000"), composite_score=2, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.LIKELY_WIN
        assert r.final_zone == TriageZone.LIKELY_WIN
        assert not r.handlungsdruck_elevated

    def test_likely_win_at_exact_boundary(self, clf: ZoneClassifier) -> None:
        r = clf.classify(_LW_MIN, composite_score=_LW_MAX_C, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.LIKELY_WIN

    def test_calculated_risk_composite_exceeds_lw_limit(
        self, clf: ZoneClassifier
    ) -> None:
        # Benefit qualifies for LW, but composite is too high → CALCULATED_RISK
        r = clf.classify(Decimal("75000"), composite_score=5, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.CALCULATED_RISK

    def test_calculated_risk_benefit_below_lw_threshold(
        self, clf: ZoneClassifier
    ) -> None:
        r = clf.classify(Decimal("20000"), composite_score=3, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.CALCULATED_RISK

    def test_marginal_gain_low_benefit(self, clf: ZoneClassifier) -> None:
        r = clf.classify(Decimal("1000"), composite_score=3, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.MARGINAL_GAIN

    def test_marginal_gain_zero_benefit(self, clf: ZoneClassifier) -> None:
        r = clf.classify(Decimal("0"), composite_score=2, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.MARGINAL_GAIN

    def test_marginal_gain_composite_too_high(self, clf: ZoneClassifier) -> None:
        # High benefit but composite above both limits → MARGINAL_GAIN
        r = clf.classify(Decimal("100000"), composite_score=8, handlungsdruck_score=1)
        assert r.base_zone == TriageZone.MARGINAL_GAIN


# ---------------------------------------------------------------------------
# Handlungsdruck elevation
# ---------------------------------------------------------------------------


class TestHandlungsdruckElevation:
    def test_elevates_marginal_to_calculated(self, clf: ZoneClassifier) -> None:
        r = clf.classify(
            Decimal("1000"), composite_score=5, handlungsdruck_score=_HD_THRESHOLD
        )
        assert r.base_zone == TriageZone.MARGINAL_GAIN
        assert r.final_zone == TriageZone.CALCULATED_RISK
        assert r.handlungsdruck_elevated

    def test_elevates_calculated_to_likely_win(self, clf: ZoneClassifier) -> None:
        r = clf.classify(Decimal("20000"), composite_score=3, handlungsdruck_score=5)
        assert r.base_zone == TriageZone.CALCULATED_RISK
        assert r.final_zone == TriageZone.LIKELY_WIN
        assert r.handlungsdruck_elevated

    def test_likely_win_stays_when_handlungsdruck_high(
        self, clf: ZoneClassifier
    ) -> None:
        r = clf.classify(Decimal("75000"), composite_score=2, handlungsdruck_score=5)
        assert r.final_zone == TriageZone.LIKELY_WIN
        assert not r.handlungsdruck_elevated  # no actual change, no flag

    def test_no_elevation_one_below_threshold(self, clf: ZoneClassifier) -> None:
        r = clf.classify(
            Decimal("1000"),
            composite_score=5,
            handlungsdruck_score=_HD_THRESHOLD - 1,
        )
        assert r.final_zone == TriageZone.MARGINAL_GAIN
        assert not r.handlungsdruck_elevated

    def test_reason_mentions_elevation_when_elevated(self, clf: ZoneClassifier) -> None:
        r = clf.classify(Decimal("1000"), composite_score=5, handlungsdruck_score=5)
        assert r.handlungsdruck_elevated
        assert "hochgestuft" in r.reason

    def test_reason_contains_benefit_and_composite(self, clf: ZoneClassifier) -> None:
        r = clf.classify(Decimal("75000"), composite_score=3, handlungsdruck_score=1)
        assert "75" in r.reason
        assert "3" in r.reason


class TestThresholdProperties:
    def test_exposes_configured_thresholds(self, clf: ZoneClassifier) -> None:
        assert clf.likely_win_min_benefit == _LW_MIN
        assert clf.likely_win_max_composite == _LW_MAX_C
        assert clf.calculated_risk_min_benefit == _CR_MIN
        assert clf.calculated_risk_max_composite == _CR_MAX_C
        assert clf.handlungsdruck_elevation_threshold == _HD_THRESHOLD


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

_BENEFIT = st.integers(min_value=0, max_value=1_000_000).map(lambda x: Decimal(str(x)))
_COMPOSITE = st.integers(min_value=0, max_value=10)
_HD = st.integers(min_value=1, max_value=5)
_ZONE_ORDER = {
    TriageZone.MARGINAL_GAIN: 0,
    TriageZone.CALCULATED_RISK: 1,
    TriageZone.LIKELY_WIN: 2,
}


@given(benefit=_BENEFIT, composite=_COMPOSITE, hd=_HD)
@settings(max_examples=300, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_final_zone_gte_base_zone(
    clf: ZoneClassifier, benefit: Decimal, composite: int, hd: int
) -> None:
    """Invariant: elevation never lowers a zone."""
    r = clf.classify(benefit, composite, hd)
    assert _ZONE_ORDER[r.final_zone] >= _ZONE_ORDER[r.base_zone]


@given(b1=_BENEFIT, b2=_BENEFIT, composite=_COMPOSITE, hd=_HD)
@settings(max_examples=300, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_higher_benefit_same_or_better_base_zone(
    clf: ZoneClassifier,
    b1: Decimal,
    b2: Decimal,
    composite: int,
    hd: int,
) -> None:
    """Invariant: higher expected benefit → same or better base zone."""
    low, high = min(b1, b2), max(b1, b2)
    r_low = clf.classify(low, composite, hd)
    r_high = clf.classify(high, composite, hd)
    assert _ZONE_ORDER[r_high.base_zone] >= _ZONE_ORDER[r_low.base_zone]


# ---------------------------------------------------------------------------
# Config loader smoke test
# ---------------------------------------------------------------------------


def test_load_zone_classifier_from_config() -> None:
    config_path = Path(__file__).parents[2] / "config" / "zone_thresholds.yaml"
    classifier = load_zone_classifier(config_path)
    # A very high-benefit, low-complexity case must be LIKELY_WIN
    r = classifier.classify(
        expected_benefit_eur=Decimal("500000"),
        composite_score=1,
        handlungsdruck_score=1,
    )
    assert r.final_zone == TriageZone.LIKELY_WIN

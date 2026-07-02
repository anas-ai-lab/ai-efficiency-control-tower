"""Tests für src/aect/domain/filters.py"""

import pytest

from aect.domain.filters import (
    FilterResult,
    apply_prefilter,
)

# Referenz-Schwellen fuer die Tests -- entsprechen den generischen
# Platzhalter-Werten aus config/roi_config.toml. Seit F-001 gibt es im
# Vorfilter keine eigenen Defaults mehr (Schwellen kommen verpflichtend
# aus der ROIConfig).
MIN_POTENTIAL: float = 20_000.0
MIN_HOURS: float = 120.0
MIN_NET_BENEFIT: float = 5_000.0

_THRESHOLDS = {
    "min_potential": MIN_POTENTIAL,
    "min_hours": MIN_HOURS,
    "min_net_benefit": MIN_NET_BENEFIT,
}


class TestFilterResultInvarianten:
    def test_valid_passes_true(self) -> None:
        result = FilterResult(passes=True, failed_criteria=[], details={})
        assert result.passes is True

    def test_passes_true_mit_failed_criteria_raises(self) -> None:
        with pytest.raises(ValueError, match="passes=True"):
            FilterResult(passes=True, failed_criteria=["X"], details={})

    def test_passes_false_ohne_failed_criteria_raises(self) -> None:
        with pytest.raises(ValueError, match="passes=False"):
            FilterResult(passes=False, failed_criteria=[], details={})


class TestApplyPrefilter:
    def test_alle_kriterien_erfuellt(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=25_000.0,
            hours_per_year=150.0,
            net_benefit_eur=8_000.0,
            **_THRESHOLDS,
        )
        assert result.passes is True
        assert result.failed_criteria == []

    def test_potenzial_zu_niedrig(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=19_999.0,
            hours_per_year=150.0,
            net_benefit_eur=8_000.0,
            **_THRESHOLDS,
        )
        assert result.passes is False
        assert "Theoretisches Potenzial" in result.failed_criteria

    def test_stunden_zu_niedrig(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=25_000.0,
            hours_per_year=119.9,
            net_benefit_eur=8_000.0,
            **_THRESHOLDS,
        )
        assert result.passes is False
        assert "Stundeneinsparung" in result.failed_criteria

    def test_nettonutzen_zu_niedrig(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=25_000.0,
            hours_per_year=150.0,
            net_benefit_eur=4_999.0,
            **_THRESHOLDS,
        )
        assert result.passes is False
        assert "Nettonutzen" in result.failed_criteria

    def test_alle_drei_scheitern(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=0.0,
            hours_per_year=0.0,
            net_benefit_eur=0.0,
            **_THRESHOLDS,
        )
        assert result.passes is False
        assert len(result.failed_criteria) == 3

    def test_genau_an_schwelle_besteht(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=MIN_POTENTIAL,
            hours_per_year=MIN_HOURS,
            net_benefit_eur=MIN_NET_BENEFIT,
            **_THRESHOLDS,
        )
        assert result.passes is True

    def test_knapp_unter_schwelle_scheitert(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=MIN_POTENTIAL - 0.01,
            hours_per_year=MIN_HOURS,
            net_benefit_eur=MIN_NET_BENEFIT,
            **_THRESHOLDS,
        )
        assert result.passes is False

    def test_custom_schwellen_werden_verwendet(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=5_000.0,
            hours_per_year=50.0,
            net_benefit_eur=1_000.0,
            min_potential=5_000.0,
            min_hours=50.0,
            min_net_benefit=1_000.0,
        )
        assert result.passes is True

    def test_details_enthalten_alle_drei_kriterien(self) -> None:
        result = apply_prefilter(
            theoretical_potential_eur=25_000.0,
            hours_per_year=150.0,
            net_benefit_eur=8_000.0,
            **_THRESHOLDS,
        )
        assert len(result.details) == 3
        assert all(isinstance(v, bool) for v in result.details.values())

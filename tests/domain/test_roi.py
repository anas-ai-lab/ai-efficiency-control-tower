"""Tests für ROI/Value-Engine (V4-Modell, SDR-0003).

Strategie:
  - _check_prefilter direkt testen (isoliert, kein UseCaseInput)
  - _calculate_roi_values für End-to-End-Berechnung (person-basierte Semantik)
  - Kein-Zeitgewinn (Ersparnis <= 0) -> Vorfilter-Fail mit Klartext-Grund
  - Config-Layering (roi_config.local.toml über Platzhalter)
  - Hypothesis: Invariante expected_benefit <= theoretical_potential für alle
    Faktoren in [0.0, 1.0] (bei Ersparnis >= 0)

Felder-Abhängigkeit: Diese Tests haben KEINE Abhängigkeit zu UseCaseInput-Feldnamen.
"""

from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from aect.domain.roi import (
    ROIConfig,
    _calculate_roi_values,
    _check_prefilter,
    load_roi_config,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config() -> ROIConfig:
    """Test-Config mit bekannten Werten — kein TOML-Dateisystem-Zugriff."""
    return ROIConfig(
        hourly_rates={
            "DE": {
                "ASSOCIATE": Decimal("60"),
                "PROFESSIONAL": Decimal("80"),
                "SENIOR": Decimal("100"),
                "MANAGER": Decimal("130"),
            }
        },
        evidence_factors={"LOW": 0.5, "MEDIUM": 0.75, "HIGH": 1.0},
        adoption_factors={"NONE": 0.1, "LOW": 0.3, "MEDIUM": 0.6, "HIGH": 1.0},
        min_potential_eur=Decimal("20000"),
        min_hours_per_year=120.0,
        min_expected_benefit_eur=Decimal("5000"),
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )


# ---------------------------------------------------------------------------
# _check_prefilter (direkt, mit expliziten Werten — kein Umweg über calculate)
# ---------------------------------------------------------------------------


def test_prefilter_passes_all_thresholds(config: ROIConfig) -> None:
    passes, reason = _check_prefilter(
        theoretical_potential=Decimal("50000"),
        hours_per_year=200.0,
        net_expected_benefit=Decimal("30000"),
        config=config,
    )
    assert passes is True
    assert reason is None


def test_prefilter_fails_on_potential(config: ROIConfig) -> None:
    passes, reason = _check_prefilter(
        theoretical_potential=Decimal("15000"),  # < 20000 Schwelle
        hours_per_year=200.0,
        net_expected_benefit=Decimal("10000"),
        config=config,
    )
    assert passes is False
    assert reason is not None
    assert "Potenzial" in reason


def test_prefilter_fails_on_hours(config: ROIConfig) -> None:
    passes, reason = _check_prefilter(
        theoretical_potential=Decimal("50000"),  # > 20000 → OK
        hours_per_year=80.0,  # < 120.0 → schlägt fehl
        net_expected_benefit=Decimal("40000"),
        config=config,
    )
    assert passes is False
    assert reason is not None
    assert "Stunden" in reason


def test_prefilter_fails_on_net_benefit(config: ROIConfig) -> None:
    passes, reason = _check_prefilter(
        theoretical_potential=Decimal("50000"),
        hours_per_year=200.0,
        net_expected_benefit=Decimal("2000"),  # < 5000 Schwelle
        config=config,
    )
    assert passes is False
    assert reason is not None
    assert "Netto" in reason


def test_prefilter_order_potential_before_hours(config: ROIConfig) -> None:
    """Potenzial-Fail hat Vorrang vor Stunden-Fail (Reihenfolge ist deterministisch)."""
    passes, reason = _check_prefilter(
        theoretical_potential=Decimal("100"),  # schlägt als Erstes fehl
        hours_per_year=10.0,  # würde auch fehlschlagen
        net_expected_benefit=Decimal("50"),
        config=config,
    )
    assert passes is False
    assert reason is not None
    assert "Potenzial" in reason  # nicht "Stunden"


# ---------------------------------------------------------------------------
# _calculate_roi_values — End-to-End (person-basierte Häufigkeit)
# ---------------------------------------------------------------------------


def test_theoretical_potential_calculation(config: ROIConfig) -> None:
    """Theoretisches Potenzial = Gesamtstunden × Stundensatz.

    Ersparnis 2h/Vorgang (current 2.0 - with_ai 0.0) × 520 Vorgaenge/MA/Jahr
    × 5 Mitarbeiter = 5200h gesamt; × 80€/h (PROFESSIONAL, DE) = 416.000€.
    """
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=2.0,
        time_per_case_with_ai_hours=0.0,
        occurrences_per_employee_per_year=520.0,
        employees_affected=5,
        license_cost_annual_eur=0.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.theoretical_potential_eur == Decimal("416000.00")
    assert result.hours_per_year == pytest.approx(5200.0)
    assert result.time_saved_per_case_hours == pytest.approx(2.0)
    assert result.passes_prefilter is True


def test_both_factors_applied_to_potential(config: ROIConfig) -> None:
    """Erwarteter Nutzen = Potenzial × Nutzungsfaktor × Evidenzfaktor."""
    # Potenzial = 5200h × 80€ = 416.000€
    # Nutzung=MEDIUM (0.6) × Evidenz=LOW (0.5) = 0.3 → 416000 × 0.3 = 124.800€
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=2.0,
        time_per_case_with_ai_hours=0.0,
        occurrences_per_employee_per_year=520.0,
        employees_affected=5,
        license_cost_annual_eur=0.0,
        adoption_type_value="MEDIUM",
        evidence_level_value="LOW",
        config=config,
    )
    assert result.usage_factor == pytest.approx(0.6)
    assert result.evidence_factor == pytest.approx(0.5)
    assert result.expected_benefit_eur == Decimal("124800.00")


def test_license_cost_subtracted_from_expected(config: ROIConfig) -> None:
    """Netto-Nutzen = Erwarteter Nutzen − Lizenzkosten."""
    # Potenzial = 416.000€, Faktoren=HIGH/HIGH → expected=416.000€
    # Lizenz = 50.000€ → Netto = 366.000€
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=2.0,
        time_per_case_with_ai_hours=0.0,
        occurrences_per_employee_per_year=520.0,
        employees_affected=5,
        license_cost_annual_eur=50_000.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.net_expected_benefit_eur == Decimal("366000.00")


def test_unknown_country_yields_zero_potential(config: ROIConfig) -> None:
    """Unbekanntes Land → Stundensatz 0 → Potenzial 0 → Vorfilter schlägt fehl."""
    result = _calculate_roi_values(
        employee_country="XX",  # nicht in config
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=5.0,
        time_per_case_with_ai_hours=0.0,
        occurrences_per_employee_per_year=520.0,
        employees_affected=10,
        license_cost_annual_eur=0.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.theoretical_potential_eur == Decimal("0.00")
    assert result.passes_prefilter is False


def test_high_license_cost_can_make_net_negative(config: ROIConfig) -> None:
    """Lizenzkosten > Nutzen → negativer Netto-Nutzen → Vorfilter schlägt fehl."""
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="ASSOCIATE",
        time_per_case_current_hours=0.5,
        time_per_case_with_ai_hours=0.0,
        occurrences_per_employee_per_year=24.0,
        employees_affected=3,
        license_cost_annual_eur=100_000.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.net_expected_benefit_eur < Decimal("0")
    assert result.passes_prefilter is False


# ---------------------------------------------------------------------------
# Kein Zeitgewinn (Ersparnis <= 0) -> Vorfilter-Fail mit Klartext-Grund
# ---------------------------------------------------------------------------


def test_zero_time_delta_fails_prefilter_with_reason(config: ROIConfig) -> None:
    """Ersparnis == 0 → Vorfilter-Fail, Klartext-Grund, kein Clamping."""
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=1.0,
        time_per_case_with_ai_hours=1.0,
        occurrences_per_employee_per_year=520.0,
        employees_affected=5,
        license_cost_annual_eur=0.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.passes_prefilter is False
    assert result.prefilter_fail_reason is not None
    assert "Kein Zeitgewinn" in result.prefilter_fail_reason
    assert result.time_saved_per_case_hours == pytest.approx(0.0)
    assert result.theoretical_potential_eur <= Decimal("0")


def test_negative_time_delta_fails_prefilter_with_reason(config: ROIConfig) -> None:
    """Ersparnis < 0 (KI langsamer) → Vorfilter-Fail, negatives Potenzial gemeldet."""
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=1.0,
        time_per_case_with_ai_hours=2.0,
        occurrences_per_employee_per_year=520.0,
        employees_affected=5,
        license_cost_annual_eur=0.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.passes_prefilter is False
    assert result.prefilter_fail_reason is not None
    assert "Kein Zeitgewinn" in result.prefilter_fail_reason
    assert result.time_saved_per_case_hours == pytest.approx(-1.0)
    assert result.theoretical_potential_eur < Decimal("0")


def test_zero_delta_reason_names_both_times(config: ROIConfig) -> None:
    """Der Klartext-Grund nennt beide Zeiten (mit KI und heute)."""
    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="PROFESSIONAL",
        time_per_case_current_hours=0.4,
        time_per_case_with_ai_hours=0.4,
        occurrences_per_employee_per_year=520.0,
        employees_affected=5,
        license_cost_annual_eur=0.0,
        adoption_type_value="HIGH",
        evidence_level_value="HIGH",
        config=config,
    )
    assert result.prefilter_fail_reason is not None
    assert "0.4" in result.prefilter_fail_reason


# ---------------------------------------------------------------------------
# Config-Layering (roi_config.local.toml über Platzhalter, V4 SDR-0003 §5)
# Die echte roi_config.local.toml wird bewusst NICHT referenziert.
# ---------------------------------------------------------------------------

_BASE_TOML = """\
[thresholds]
min_potential_eur        = 20000.0
min_hours_per_year       = 120.0
min_expected_benefit_eur = 5000.0

[hourly_rates.de]
junior       = 10.0
professional = 20.0
consultant   = 30.0
senior       = 40.0
management   = 50.0

[effort_cost_points]
impl_cost_point_min_eur    = 10000.0
license_cost_point_min_eur = 10000.0

[evidence_factors]
pure_estimate   = 0.40
similar_project = 0.55
tested_piloted  = 0.90

[adoption_factors]
voluntary            = 0.50
recommended_standard = 0.70
fixed_process_step   = 0.90
"""

_LOCAL_TOML = """\
[hourly_rates.de]
junior       = 99.0
professional = 199.0
consultant   = 299.0
senior       = 399.0
management   = 499.0

[hourly_rates.zz]
junior       = 1.0
professional = 2.0
consultant   = 3.0
senior       = 4.0
management   = 5.0
"""


def test_layering_local_overrides_de_and_adds_country(tmp_path: Path) -> None:
    base = tmp_path / "roi_config.toml"
    base.write_text(_BASE_TOML, encoding="utf-8")
    (tmp_path / "roi_config.local.toml").write_text(_LOCAL_TOML, encoding="utf-8")

    cfg = load_roi_config(base)

    # local überschreibt die de-Rate länderweise ...
    assert cfg.hourly_rates["de"]["professional"] == Decimal("199.0")
    # ... und ergänzt ein neues Land, das nur in local steht.
    assert cfg.hourly_rates["zz"]["management"] == Decimal("5.0")


def test_layering_without_local_uses_placeholders(tmp_path: Path) -> None:
    base = tmp_path / "roi_config.toml"
    base.write_text(_BASE_TOML, encoding="utf-8")
    # KEINE local-Datei angelegt.

    cfg = load_roi_config(base)

    assert cfg.hourly_rates["de"]["professional"] == Decimal("20.0")
    assert "zz" not in cfg.hourly_rates


def test_layering_keeps_untouched_sections(tmp_path: Path) -> None:
    """local ohne factors/thresholds lässt die Platzhalter-Werte unangetastet."""
    base = tmp_path / "roi_config.toml"
    base.write_text(_BASE_TOML, encoding="utf-8")
    (tmp_path / "roi_config.local.toml").write_text(_LOCAL_TOML, encoding="utf-8")

    cfg = load_roi_config(base)

    assert cfg.evidence_factors["pure_estimate"] == pytest.approx(0.40)
    assert cfg.adoption_factors["fixed_process_step"] == pytest.approx(0.90)


# ---------------------------------------------------------------------------
# Faktor-Werte aus der getrackten TOML (V4-Kalibrierung)
# ---------------------------------------------------------------------------


def test_tracked_factor_values(tmp_path: Path) -> None:
    """Die getrackten V4-Faktoren stimmen exakt (kein Layering im tmp-Base)."""
    base = tmp_path / "roi_config.toml"
    base.write_text(_BASE_TOML, encoding="utf-8")
    cfg = load_roi_config(base)

    assert cfg.evidence_factors == {
        "pure_estimate": pytest.approx(0.40),
        "similar_project": pytest.approx(0.55),
        "tested_piloted": pytest.approx(0.90),
    }
    assert cfg.adoption_factors == {
        "voluntary": pytest.approx(0.50),
        "recommended_standard": pytest.approx(0.70),
        "fixed_process_step": pytest.approx(0.90),
    }
    assert cfg.impl_cost_point_min_eur == pytest.approx(10_000.0)
    assert cfg.license_cost_point_min_eur == pytest.approx(10_000.0)


# ---------------------------------------------------------------------------
# Property-Based Test: Kern-Invariante (Projekt-Prinzip "Regeln vor LLM", Master-Plan v3 Phase A)
# ---------------------------------------------------------------------------


@given(
    usage_factor=st.floats(
        min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
    ),
    evidence_factor=st.floats(
        min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
    ),
)
@settings(max_examples=300)
def test_invariant_expected_benefit_never_exceeds_potential(
    usage_factor: float,
    evidence_factor: float,
) -> None:
    """Invariante: expected_benefit_eur <= theoretical_potential_eur.

    Gilt für alle Faktoren in [0.0, 1.0] bei nicht-negativer Ersparnis —
    unabhängig von Lizenzkosten (Lizenz senkt nur den Netto-Nutzen, nicht den
    erwarteten Brutto-Nutzen).
    """
    test_config = ROIConfig(
        hourly_rates={"DE": {"SENIOR": Decimal("100")}},
        evidence_factors={"T": evidence_factor},
        adoption_factors={"T": usage_factor},
        min_potential_eur=Decimal("0"),  # Schwellen deaktiviert für diesen Test
        min_hours_per_year=0.0,
        min_expected_benefit_eur=Decimal("-999999"),
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )

    result = _calculate_roi_values(
        employee_country="DE",
        employee_category_value="SENIOR",
        time_per_case_current_hours=2.0,
        time_per_case_with_ai_hours=0.0,
        occurrences_per_employee_per_year=260.0,
        employees_affected=10,
        license_cost_annual_eur=0.0,
        adoption_type_value="T",
        evidence_level_value="T",
        config=test_config,
    )

    # KERN-INVARIANTE: Faktoren ∈ [0,1] → erw. Nutzen ≤ theor. Potenzial
    assert result.expected_benefit_eur <= result.theoretical_potential_eur

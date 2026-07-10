"""Integrations-Test fuer calculate_roi() Adapter (Tag 19).

Prueft den Adapter end-to-end mit load_roi_config() -- verifiziert damit
gleichzeitig, dass die TOML-Keys mit den StrEnum-Values uebereinstimmen.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from aect.domain.models import UseCaseInput
from aect.domain.roi import ROIConfig, calculate_roi, load_roi_config
from aect.domain.types import (
    AdoptionType,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)

_CONFIG = load_roi_config()


def _use_case(**overrides: object) -> UseCaseInput:
    defaults: dict[str, object] = {
        "title": "ROI Adapter Integrationstest",
        "submitter": "Tester",
        "department": "IT",
        "country": Country.DE,
        "current_state": (
            "Aktuell wird der Prozess manuell durchgefuehrt und erfordert viel Zeit."
            " Es gibt keine technische Unterstuetzung."
        ),
        "desired_state": (
            "Nach AI-Unterstuetzung soll der Prozess automatisiert ablaufen."
        ),
        "example_process": "Ein einzelner Vorgang dauert 30 Minuten.",
        "time_per_case_hours_current": 0.5,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 1000,
        "affected_employees_count": 5,
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "evidence_level": EvidenceLevel.TESTED_PILOTED,
        "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
        "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
        "estimated_license_cost_eur": 5000.0,
        "contains_pii": False,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
    }
    defaults.update(overrides)
    return UseCaseInput.model_validate(defaults)


@pytest.mark.unit
def test_calculate_roi_kein_not_implemented_error() -> None:
    """calculate_roi() darf keine NotImplementedError werfen."""
    result = calculate_roi(_use_case(), _CONFIG)
    assert result is not None


@pytest.mark.unit
def test_calculate_roi_invariante_expected_le_potential() -> None:
    """Kernige Invariante: expected_benefit <= theoretical_potential."""
    result = calculate_roi(_use_case(), _CONFIG)
    assert result.expected_benefit_eur <= result.theoretical_potential_eur


@pytest.mark.unit
def test_calculate_roi_potential_positiv_fuer_valide_eingabe() -> None:
    """Reale Eingabe mit bekanntem Land und Kategorie liefert Potenzial > 0."""
    result = calculate_roi(_use_case(country=Country.DE), _CONFIG)
    assert result.theoretical_potential_eur > Decimal("0")


@pytest.mark.unit
def test_calculate_roi_ch_nutzt_hoehere_ch_saetze() -> None:
    """country=ch nutzt die CH-Section -> hoeheres Potenzial als DE (CH-Saetze
    liegen ueber den DE-Saetzen fuer dasselbe Level)."""
    de = calculate_roi(_use_case(country=Country.DE), _CONFIG)
    ch = calculate_roi(_use_case(country=Country.CH), _CONFIG)
    assert ch.theoretical_potential_eur > de.theoretical_potential_eur


@pytest.mark.unit
def test_calculate_roi_land_ohne_config_section_liefert_null_und_vorfilter_fail() -> (
    None
):
    """Gueltiges Country-Enum ohne [hourly_rates.<land>]-Section -> Stundensatz 0
    -> Potenzial 0 -> Vorfilter schlaegt fehl. Dokumentiert das Fallback-Verhalten.

    Bewusst mit einer expliziten Platzhalter-Config (nur 'de'), nicht mit der
    Default-Config: durch das V4-Config-Layering pflegt roi_config.local.toml
    (gitignored, lokal vorhanden) alle Laender -> der Default hat lokal keinen
    Null-Satz-Fall. Diese Config macht den Test deterministisch (lokal wie CI)."""
    placeholder_config = ROIConfig(
        hourly_rates={"de": {"professional": Decimal("65")}},
        evidence_factors={"tested_piloted": 0.90},
        adoption_factors={"fixed_process_step": 0.90},
        min_potential_eur=Decimal("20000"),
        min_hours_per_year=120.0,
        min_expected_benefit_eur=Decimal("5000"),
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    result = calculate_roi(_use_case(country=Country.NO), placeholder_config)
    assert result.theoretical_potential_eur == Decimal("0.00")
    assert result.passes_prefilter is False
    assert result.prefilter_fail_reason is not None


@pytest.mark.unit
def test_calculate_roi_alle_employee_categories_laufen_ohne_keyerror() -> None:
    """Alle EmployeeCategory-Werte muessen in roi_config.toml vorhanden sein."""
    for category in EmployeeCategory:
        use_case = _use_case(employee_category=category, country=Country.DE)
        result = calculate_roi(use_case, _CONFIG)
        assert result.theoretical_potential_eur > Decimal("0")


@pytest.mark.unit
def test_calculate_roi_alle_evidence_levels_laufen_ohne_keyerror() -> None:
    """Alle EvidenceLevel-Werte muessen in roi_config.toml vorhanden sein."""
    for level in EvidenceLevel:
        use_case = _use_case(evidence_level=level)
        result = calculate_roi(use_case, _CONFIG)
        assert result.expected_benefit_eur <= result.theoretical_potential_eur


@pytest.mark.unit
def test_calculate_roi_alle_adoption_types_laufen_ohne_keyerror() -> None:
    """Alle AdoptionType-Werte muessen in roi_config.toml vorhanden sein."""
    for adoption in AdoptionType:
        use_case = _use_case(adoption_type=adoption)
        result = calculate_roi(use_case, _CONFIG)
        assert result.expected_benefit_eur >= Decimal("0")

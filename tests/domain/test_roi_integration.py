"""Integrations-Test fuer calculate_roi() Adapter (Tag 19).

Prueft den Adapter end-to-end mit load_roi_config() -- verifiziert damit
gleichzeitig, dass die TOML-Keys mit den StrEnum-Values uebereinstimmen.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from aect.domain.models import UseCaseInput
from aect.domain.roi import calculate_roi, load_roi_config
from aect.domain.types import (
    AdoptionType,
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
        "current_state": (
            "Aktuell wird der Prozess manuell durchgefuehrt und erfordert viel Zeit."
            " Es gibt keine technische Unterstuetzung."
        ),
        "desired_state": (
            "Nach AI-Unterstuetzung soll der Prozess automatisiert ablaufen."
        ),
        "example_process": "Ein einzelner Vorgang dauert 30 Minuten.",
        "time_savings_hours_per_case": 0.5,
        "frequency_per_year": 1000,
        "affected_employees_count": 5,
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "evidence_level": EvidenceLevel.TESTED_PILOTED,
        "adoption_type": AdoptionType.MANDATORY,
        "implementation_approach": ImplementationApproach.STANDARD_PRODUCT,
        "estimated_license_cost_eur": 5000.0,
        "implementation_complexity": 2,
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
    result = calculate_roi(_use_case(), _CONFIG, country="DE")
    assert result.theoretical_potential_eur > Decimal("0")


@pytest.mark.unit
def test_calculate_roi_unbekanntes_land_liefert_null_potential() -> None:
    """Unbekanntes Land-Kuerzel -> hourly rate = 0 -> Potenzial = 0."""
    result = calculate_roi(_use_case(), _CONFIG, country="XX")
    assert result.theoretical_potential_eur == Decimal("0.00")


@pytest.mark.unit
def test_calculate_roi_alle_employee_categories_laufen_ohne_keyerror() -> None:
    """Alle EmployeeCategory-Werte muessen in roi_config.toml vorhanden sein."""
    for category in EmployeeCategory:
        use_case = _use_case(employee_category=category)
        result = calculate_roi(use_case, _CONFIG, country="DE")
        assert result.theoretical_potential_eur >= Decimal("0")


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

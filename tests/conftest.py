# tests/conftest.py
"""Shared pytest fixtures and configuration."""

from __future__ import annotations

import pytest

from aect.domain import UseCaseInput, load_roi_config
from aect.domain.roi import ROIConfig
from aect.domain.types import (
    AdoptionType,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)


# ---------------------------------------------------------------------------
# Custom markers
# ---------------------------------------------------------------------------
def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may be slow)"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")


# ---------------------------------------------------------------------------
# Shared fixtures (Phase B+)
# ---------------------------------------------------------------------------
@pytest.fixture
def roi_config() -> ROIConfig:
    """ROIConfig aus config/roi_config.toml -- fuer alle Test-Module verfuegbar."""
    return load_roi_config()


@pytest.fixture
def sample_use_case() -> UseCaseInput:
    """Valides UseCaseInput fuer Tests -- DACH-typischer Finanz-Use-Case.

    Alle Pflichtfelder gesetzt. Wird in Phase B/C/D/E-Tests wiederverwendet.
    """
    return UseCaseInput(
        title="Automatische Rechnungspruefung",
        submitter="Max Muster",
        department="Finanzen",
        country=Country.DE,
        current_state=(
            "Sachbearbeiter pruefen eingehende Rechnungen manuell auf Korrektheit. "
            "Jede Rechnung wird mit dem Auftrag in SAP abgeglichen."
        ),
        desired_state=(
            "Ein AI-System prueft Rechnungen automatisch und markiert Abweichungen "
            "fuer die manuelle Nachbearbeitung durch den Sachbearbeiter."
        ),
        example_process=(
            "Rechnung per E-Mail empfangen, geoeffnet, Betrag und "
            "Lieferant gegen SAP-Auftrag geprueft."
        ),
        time_per_case_hours_current=0.5,
        time_per_case_hours_with_ai=0.3,
        occurrences_per_employee_per_year=5000,
        affected_employees_count=10,
        employee_category=EmployeeCategory.PROFESSIONAL,
        evidence_level=EvidenceLevel.SIMILAR_PROJECT,
        adoption_type=AdoptionType.FIXED_PROCESS_STEP,
        implementation_approach=ImplementationApproach.API_INTEGRATION,
        estimated_license_cost_eur=15000.0,
        contains_pii=False,
        data_classification=DataClassification.NO_PERSONAL_DATA,
        regulatory_pressure=False,
        competitive_pressure=True,
        strategic_priority=False,
    )

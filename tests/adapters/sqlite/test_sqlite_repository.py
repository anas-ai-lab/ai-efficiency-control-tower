"""Tests fuer SQLiteRepository.

Strategie: echte UseCaseInput + evaluate_use_case() -> SubmittedCase.
Testet Serialisierungs-Roundtrip fuer alle kritischen Typen:
  - Decimal-Praezision (ROIResult)
  - StrEnum-Rekonstruktion (TriageZone, RoutingRecommendation, FeasibilityFlag)
  - tuple-Rekonstruktion (automation_signals, flags etc.)
  - None-Felder (roi/composite/zone wenn Vorfilter schlaegt fehl)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aect.adapters.sqlite.repository import SQLiteRepository
from aect.application.models import SubmittedCase
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import evaluate_use_case
from aect.domain.roi import load_roi_config
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_aect.db"


@pytest.fixture
def repo(db_path: Path) -> SQLiteRepository:
    return SQLiteRepository(db_path)


@pytest.fixture
def sample_use_case() -> UseCaseInput:
    return UseCaseInput(
        title="Automatische Rechnungsverarbeitung fuer Finanzen",
        submitter="Max Muster",
        department="Finanzen",
        current_state=(
            "Rechnungen werden manuell von Buchhaltern geprueft, "
            "klassifiziert und in SAP erfasst. Pro Rechnung dauert das 30 Minuten. "
            "Bei 3000 Rechnungen jaehrlich bindet das erhebliche Kapazitaet im Team."
        ),
        desired_state=(
            "Ein KI-System erkennt Rechnungsfelder automatisch, klassifiziert "
            "nach Kostenstelle und schlaegt die SAP-Buchung vor. "
            "Der Buchhalter prueft und bestaetigt nur noch. "
            "Ziel: Bearbeitungszeit auf 5 Minuten pro Rechnung senken."
        ),
        example_process=(
            "Lieferantenrechnung von XYZ GmbH: Buchhalter oeffnet PDF, "
            "extrahiert Positionen manuell und erfasst in SAP."
        ),
        time_savings_hours_per_case=0.4,
        frequency_per_year=3000,
        affected_employees_count=5,
        employee_category=EmployeeCategory.PROFESSIONAL,
        evidence_level=EvidenceLevel.SIMILAR_PROJECT,
        adoption_type=AdoptionType.MANDATORY,
        implementation_approach=ImplementationApproach.VENDOR_SOLUTION,
        estimated_license_cost_eur=12000.0,
        implementation_complexity=3,
        contains_pii=False,
        data_classification=DataClassification.NO_PERSONAL_DATA,
    )


@pytest.fixture
def sample_case(sample_use_case: UseCaseInput) -> SubmittedCase:
    roi_config = load_roi_config()
    result = evaluate_use_case(sample_use_case, roi_config)
    return SubmittedCase(
        id="test-case-001",
        submitted_at=datetime(2026, 6, 11, 10, 0, 0, tzinfo=UTC),
        use_case=sample_use_case,
        result=result,
    )


@pytest.fixture
def vorfilter_fail_case() -> SubmittedCase:
    """Case bei dem der Vorfilter schlaegt fehl -> roi/composite/zone sind None."""
    use_case = UseCaseInput(
        title="Minimaler Use Case der den Vorfilter nicht besteht",
        submitter="Test User",
        department="Test Abteilung",
        current_state=(
            "Aktuell machen wir einen einzigen Vorgang manuell. "
            "Ein Mitarbeiter verbringt wenige Minuten damit."
        ),
        desired_state=(
            "Zukuenftig soll ein System das automatisch erledigen "
            "und dem Mitarbeiter Zeit sparen."
        ),
        example_process="Ein Vorgang dauert 1 Minute und kommt einmal vor.",
        time_savings_hours_per_case=0.01,  # extrem gering -> Vorfilter schlaegt fehl
        frequency_per_year=1,
        affected_employees_count=1,
        employee_category=EmployeeCategory.JUNIOR,
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        adoption_type=AdoptionType.VOLUNTARY,
        implementation_approach=ImplementationApproach.STANDARD_PRODUCT,
        estimated_license_cost_eur=0.0,
        implementation_complexity=1,
        contains_pii=False,
        data_classification=DataClassification.NO_PERSONAL_DATA,
    )
    roi_config = load_roi_config()
    result = evaluate_use_case(use_case, roi_config)
    return SubmittedCase(
        id="vorfilter-fail-001",
        submitted_at=datetime(2026, 6, 11, 12, 0, 0, tzinfo=UTC),
        use_case=use_case,
        result=result,
    )


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


class TestSQLiteRepositoryInit:
    def test_creates_db_file(self, db_path: Path, repo: SQLiteRepository) -> None:
        assert db_path.exists()

    def test_idempotent_init(self, db_path: Path) -> None:
        SQLiteRepository(db_path)
        SQLiteRepository(db_path)  # CREATE TABLE IF NOT EXISTS -- kein Fehler

    def test_empty_list(self, repo: SQLiteRepository) -> None:
        assert repo.list_all() == []

    def test_get_unknown_returns_none(self, repo: SQLiteRepository) -> None:
        assert repo.get("nonexistent") is None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestSQLiteRepositoryCRUD:
    def test_save_and_get_by_id(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.id == sample_case.id

    def test_save_overwrites_duplicate(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        repo.save(sample_case)
        assert len(repo.list_all()) == 1

    def test_list_all_returns_all(
        self,
        repo: SQLiteRepository,
        sample_case: SubmittedCase,
        vorfilter_fail_case: SubmittedCase,
    ) -> None:
        repo.save(sample_case)
        repo.save(vorfilter_fail_case)
        cases = repo.list_all()
        assert len(cases) == 2
        assert {c.id for c in cases} == {"test-case-001", "vorfilter-fail-001"}


# ---------------------------------------------------------------------------
# Serialisierungs-Roundtrip
# ---------------------------------------------------------------------------


class TestRoundtrip:
    def test_use_case_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.use_case == sample_case.use_case

    def test_submitted_at_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.submitted_at == sample_case.submitted_at

    def test_result_title_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.result.title == sample_case.result.title

    def test_decimal_precision_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        """Decimal-Felder in ROIResult behalten Praezision nach Roundtrip."""
        assert sample_case.result.roi is not None, "Fixture muss Vorfilter bestehen"
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.result.roi is not None
        assert (
            retrieved.result.roi.theoretical_potential_eur
            == sample_case.result.roi.theoretical_potential_eur
        )
        assert (
            retrieved.result.roi.net_expected_benefit_eur
            == sample_case.result.roi.net_expected_benefit_eur
        )

    def test_triage_zone_enum_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        """TriageZone (StrEnum) wird korrekt rekonstruiert."""
        assert sample_case.result.zone is not None, "Fixture muss Vorfilter bestehen"
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.result.zone is not None
        assert retrieved.result.zone.final_zone == sample_case.result.zone.final_zone
        assert retrieved.result.zone.base_zone == sample_case.result.zone.base_zone

    def test_routing_recommendation_enum_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        """RoutingRecommendation (StrEnum) wird korrekt rekonstruiert."""
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert (
            retrieved.result.routing.recommendation
            == sample_case.result.routing.recommendation
        )

    def test_tuple_fields_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        """tuple-Felder (asdict konvertiert zu list) werden als tuple rekonstruiert."""
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert (
            retrieved.result.routing.automation_signals
            == sample_case.result.routing.automation_signals
        )
        assert isinstance(retrieved.result.routing.automation_signals, tuple)

    def test_feasibility_flags_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        """FeasibilityFlag-Enums in tuple korrekt rekonstruiert."""
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert (
            retrieved.result.feasibility.flags == sample_case.result.feasibility.flags
        )

    def test_none_fields_when_vorfilter_fails(
        self, repo: SQLiteRepository, vorfilter_fail_case: SubmittedCase
    ) -> None:
        """roi/composite/zone sind None nach Vorfilter-Fail -- Roundtrip korrekt."""
        assert not vorfilter_fail_case.result.passed_vorfilter
        repo.save(vorfilter_fail_case)
        retrieved = repo.get(vorfilter_fail_case.id)
        assert retrieved is not None
        assert retrieved.result.roi is None
        assert retrieved.result.composite is None
        assert retrieved.result.zone is None


class TestLLMNarrativePersistence:
    """Belegt ADR-0012 (Persistenz) + ADR-0013 Teil 2 (Spalte umbenannt
    sharpened_text -> sharpened_content_json, JSON statt Fliesstext):
    sharpened_content_json/proposal_text werden korrekt persistiert, geladen
    und ueberschrieben. Der konkrete JSON-Inhalt ist Sache von
    application/service.py -- hier nur Roundtrip-Verhalten der Spalte
    (TEXT, beliebiger String)."""

    def test_fields_default_to_none(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.sharpened_content_json is None
        assert retrieved.proposal_text is None

    def test_fields_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.sharpened_content_json = json.dumps(
            {
                "sharpened_title": None,
                "sharpened_current_state": None,
                "sharpened_desired_state": None,
                "improvement_suggestions": [],
                "raw_text": "Geschaerfte Version: ...",
            }
        )
        sample_case.proposal_text = "Vorschlag: ..."
        repo.save(sample_case)

        retrieved = repo.get(sample_case.id)

        assert retrieved is not None
        assert retrieved.sharpened_content_json == sample_case.sharpened_content_json
        assert retrieved.proposal_text == "Vorschlag: ..."

    def test_resave_overwrites_narrative(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)

        sample_case.sharpened_content_json = json.dumps({"raw_text": "Erste Version"})
        repo.save(sample_case)

        sample_case.sharpened_content_json = json.dumps({"raw_text": "Zweite Version"})
        repo.save(sample_case)

        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.sharpened_content_json == json.dumps(
            {"raw_text": "Zweite Version"}
        )

    def test_list_all_includes_narrative_fields(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.proposal_text = "Vorschlag fuer Liste"
        repo.save(sample_case)

        cases = repo.list_all()

        assert len(cases) == 1
        assert cases[0].proposal_text == "Vorschlag fuer Liste"

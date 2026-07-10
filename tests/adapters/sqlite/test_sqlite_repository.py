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
from aect.application.models import MonitoringEntry, SubmittedCase
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import evaluate_use_case
from aect.domain.roi import load_roi_config
from aect.domain.types import (
    AdoptionType,
    CaseStatus,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    ReviewerDecision,
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
        country=Country.DE,
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
        country=Country.DE,
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


class TestComplianceHintsPersistence:
    """Belegt ADR-0026: compliance_hints_json roundtrippt wie
    sharpened_content_json/proposal_text (ADR-0012)."""

    def test_field_defaults_to_none(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.compliance_hints_json is None

    def test_field_roundtrips(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.compliance_hints_json = json.dumps(
            {
                "hint_text": "Hinweis Text [1]",
                "citations": [
                    {
                        "number": 1,
                        "source_id": "dsgvo-art-35",
                        "citation": "DSGVO Art. 35",
                        "url": None,
                    }
                ],
            }
        )
        repo.save(sample_case)

        retrieved = repo.get(sample_case.id)

        assert retrieved is not None
        assert retrieved.compliance_hints_json == sample_case.compliance_hints_json

    def test_resave_overwrites_compliance_hints(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)

        sample_case.compliance_hints_json = json.dumps(
            {"hint_text": "Erste Version", "citations": []}
        )
        repo.save(sample_case)

        sample_case.compliance_hints_json = json.dumps(
            {"hint_text": "Zweite Version", "citations": []}
        )
        repo.save(sample_case)

        retrieved = repo.get(sample_case.id)
        assert retrieved is not None
        assert retrieved.compliance_hints_json == json.dumps(
            {"hint_text": "Zweite Version", "citations": []}
        )

    def test_list_all_includes_compliance_hints_field(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.compliance_hints_json = json.dumps(
            {"hint_text": "x", "citations": []}
        )
        repo.save(sample_case)

        cases = repo.list_all()

        assert len(cases) == 1
        assert cases[0].compliance_hints_json == sample_case.compliance_hints_json


# ---------------------------------------------------------------------------
# Async-Wrapper (AUDIT-001, ADR-0037): to_thread-Roundtrip
# asyncio_mode=auto (pyproject) -> async-Tests laufen ohne Marker.
# ---------------------------------------------------------------------------


class TestAsyncWrappers:
    async def test_save_get_list_async_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        # save_async persistiert, get_async/list_all_async lesen identisch zu sync.
        await repo.save_async(sample_case)

        retrieved = await repo.get_async(sample_case.id)
        assert retrieved is not None
        assert retrieved.id == sample_case.id
        assert retrieved.result == sample_case.result

        cases = await repo.list_all_async()
        assert [c.id for c in cases] == [sample_case.id]

    async def test_get_async_returns_none_for_missing(
        self, repo: SQLiteRepository
    ) -> None:
        assert await repo.get_async("does-not-exist") is None

    async def test_delete_async_removes_case(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        await repo.save_async(sample_case)
        await repo.delete_async(sample_case.id)
        assert await repo.get_async(sample_case.id) is None

    def test_delete_is_idempotent(self, repo: SQLiteRepository) -> None:
        # DELETE auf nicht existierende ID ist ein No-op, kein Fehler (ADR-0038).
        repo.delete("never-existed")


# ---------------------------------------------------------------------------
# embedding-Spalte (L-3 Dedup, ADR-0039)
# ---------------------------------------------------------------------------


class TestEmbeddingColumn:
    def test_embedding_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.embedding = [0.1, 0.2, 0.3, 0.4]
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.embedding == [0.1, 0.2, 0.3, 0.4]

    def test_embedding_defaults_to_none(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)  # ohne embedding gesetzt
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.embedding is None

    def test_migration_adds_column_to_legacy_table(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        """Eine Tabelle ohne embedding-Spalte (alte Version) wird beim Init
        migriert -- ALTER TABLE ADD COLUMN ergaenzt die Spalte."""
        import sqlite3

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                "CREATE TABLE submitted_cases ("
                "id TEXT PRIMARY KEY, submitted_at TEXT NOT NULL, "
                "use_case_json TEXT NOT NULL, result_json TEXT NOT NULL, "
                "sharpened_content_json TEXT, proposal_text TEXT, "
                "compliance_hints_json TEXT)"
            )

        repo = SQLiteRepository(db_path)  # _init_db migriert die Spalte
        sample_case.embedding = [1.0, 2.0]
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.embedding == [1.0, 2.0]


# ---------------------------------------------------------------------------
# reviewer_decision/reviewer_note/decided_at (Human-in-the-Loop, ADR-0043)
# ---------------------------------------------------------------------------


class TestReviewerDecisionColumns:
    def test_defaults_to_pending_on_save(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.reviewer_decision == ReviewerDecision.PENDING
        assert loaded.reviewer_note is None
        assert loaded.decided_at is None

    def test_record_decision_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        decided_at = datetime(2026, 6, 12, 8, 30, 0, tzinfo=UTC)

        repo.record_decision(
            sample_case.id, ReviewerDecision.APPROVED, "Passt", decided_at
        )

        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.reviewer_decision == ReviewerDecision.APPROVED
        assert loaded.reviewer_note == "Passt"
        assert loaded.decided_at == decided_at

    def test_record_decision_overwrites_previous_decision(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        first_time = datetime(2026, 6, 12, 8, 30, 0, tzinfo=UTC)
        second_time = datetime(2026, 6, 13, 9, 0, 0, tzinfo=UTC)

        repo.record_decision(
            sample_case.id, ReviewerDecision.APPROVED, "ok", first_time
        )
        repo.record_decision(
            sample_case.id, ReviewerDecision.REJECTED, "doch nicht", second_time
        )

        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.reviewer_decision == ReviewerDecision.REJECTED
        assert loaded.reviewer_note == "doch nicht"
        assert loaded.decided_at == second_time

    def test_record_decision_is_noop_for_unknown_case_id(
        self, repo: SQLiteRepository
    ) -> None:
        # Analog delete/update_field: kein Fehler bei unbekannter case_id.
        repo.record_decision(
            "never-existed", ReviewerDecision.APPROVED, None, datetime.now(UTC)
        )

    def test_record_decision_does_not_touch_other_fields(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.proposal_text = "Bestehender Vorschlag"
        repo.save(sample_case)

        repo.record_decision(
            sample_case.id, ReviewerDecision.APPROVED, None, datetime.now(UTC)
        )

        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.proposal_text == "Bestehender Vorschlag"

    def test_migration_adds_columns_to_legacy_table(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        """Eine Tabelle ohne reviewer_decision/reviewer_note/decided_at
        (Version vor ADR-0043) wird beim Init migriert -- ALTER TABLE ADD
        COLUMN ergaenzt die drei Spalten (analog test_migration_adds_column_
        to_legacy_table fuer embedding)."""
        import sqlite3

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                "CREATE TABLE submitted_cases ("
                "id TEXT PRIMARY KEY, submitted_at TEXT NOT NULL, "
                "use_case_json TEXT NOT NULL, result_json TEXT NOT NULL, "
                "sharpened_content_json TEXT, proposal_text TEXT, "
                "compliance_hints_json TEXT, embedding TEXT)"
            )

        repo = SQLiteRepository(db_path)  # _init_db migriert die Spalten
        decided_at = datetime(2026, 6, 12, 8, 30, 0, tzinfo=UTC)
        repo.save(sample_case)
        repo.record_decision(
            sample_case.id, ReviewerDecision.APPROVED, "nachtraeglich", decided_at
        )

        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.reviewer_decision == ReviewerDecision.APPROVED
        assert loaded.reviewer_note == "nachtraeglich"
        assert loaded.decided_at == decided_at


# ---------------------------------------------------------------------------
# Case-Lifecycle-Status (Lifecycle-ADR)
# ---------------------------------------------------------------------------


class TestCaseStatusColumn:
    def test_defaults_to_submitted_on_save(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.status == CaseStatus.SUBMITTED
        assert loaded.status_updated_at is None

    def test_update_status_survives_reload(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        # Persistiert + ueberlebt Reload: eine zweite Repository-Instanz auf
        # derselben DB-Datei liest den geaenderten Status.
        repo = SQLiteRepository(db_path)
        repo.save(sample_case)
        updated_at = datetime(2026, 6, 14, 7, 15, 0, tzinfo=UTC)

        repo.update_status(sample_case.id, CaseStatus.INTEGRATED, updated_at)

        reloaded = SQLiteRepository(db_path).get(sample_case.id)
        assert reloaded is not None
        assert reloaded.status == CaseStatus.INTEGRATED
        assert reloaded.status_updated_at == updated_at

    def test_update_status_is_noop_for_unknown_case_id(
        self, repo: SQLiteRepository
    ) -> None:
        # Analog delete/update_field/record_decision: kein Fehler.
        repo.update_status("never-existed", CaseStatus.IN_REVIEW, datetime.now(UTC))

    def test_update_status_does_not_touch_other_fields(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        sample_case.proposal_text = "Bestehender Vorschlag"
        repo.save(sample_case)

        repo.update_status(sample_case.id, CaseStatus.IMPLEMENTED, datetime.now(UTC))

        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.proposal_text == "Bestehender Vorschlag"
        assert loaded.reviewer_decision == ReviewerDecision.PENDING

    def test_migration_adds_columns_to_legacy_table(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        """Eine Tabelle ohne status/status_updated_at (Version vor dem
        Lifecycle-ADR) wird beim Init migriert -- ALTER TABLE ADD COLUMN
        ergaenzt beide Spalten (analog embedding/reviewer_decision)."""
        import sqlite3

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                "CREATE TABLE submitted_cases ("
                "id TEXT PRIMARY KEY, submitted_at TEXT NOT NULL, "
                "use_case_json TEXT NOT NULL, result_json TEXT NOT NULL, "
                "sharpened_content_json TEXT, proposal_text TEXT, "
                "compliance_hints_json TEXT, embedding TEXT, "
                "reviewer_decision TEXT NOT NULL DEFAULT 'pending', "
                "reviewer_note TEXT, decided_at TEXT)"
            )

        repo = SQLiteRepository(db_path)  # _init_db migriert die Spalten
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.status == CaseStatus.SUBMITTED
        assert loaded.status_updated_at is None


# ---------------------------------------------------------------------------
# Monitoring-Zeitleiste (append-only, Monitoring-ADR)
# ---------------------------------------------------------------------------


def _entry(entry_id: str, case_id: str, created_at: datetime) -> MonitoringEntry:
    return MonitoringEntry(
        id=entry_id,
        case_id=case_id,
        created_at=created_at,
        note=f"note-{entry_id}",
        status_snapshot="submitted",
    )


class TestMonitoringEntries:
    def test_add_and_list_roundtrip(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        created_at = datetime(2026, 6, 12, 8, 30, 0, tzinfo=UTC)
        repo.add_monitoring_entry(_entry("m-1", sample_case.id, created_at))

        entries = repo.list_monitoring_entries(sample_case.id)
        assert len(entries) == 1
        assert entries[0].id == "m-1"
        assert entries[0].case_id == sample_case.id
        assert entries[0].created_at == created_at
        assert entries[0].note == "note-m-1"
        assert entries[0].status_snapshot == "submitted"

    def test_entries_survive_reload(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        repo = SQLiteRepository(db_path)
        repo.save(sample_case)
        repo.add_monitoring_entry(
            _entry("m-1", sample_case.id, datetime(2026, 6, 12, 8, 0, 0, tzinfo=UTC))
        )

        reloaded = SQLiteRepository(db_path).list_monitoring_entries(sample_case.id)
        assert [e.id for e in reloaded] == ["m-1"]

    def test_list_orders_by_created_at_then_id(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        early = datetime(2026, 6, 12, 8, 0, 0, tzinfo=UTC)
        late = datetime(2026, 6, 12, 9, 0, 0, tzinfo=UTC)
        # Bewusst in nicht-chronologischer Reihenfolge eingefuegt.
        repo.add_monitoring_entry(_entry("m-late", sample_case.id, late))
        repo.add_monitoring_entry(_entry("m-early", sample_case.id, early))
        # Zwei Eintraege in derselben Sekunde -> Sekundaerschluessel id entscheidet.
        repo.add_monitoring_entry(_entry("m-a", sample_case.id, early))

        entries = repo.list_monitoring_entries(sample_case.id)
        assert [e.id for e in entries] == ["m-a", "m-early", "m-late"]

    def test_list_only_returns_entries_of_that_case(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        created_at = datetime(2026, 6, 12, 8, 0, 0, tzinfo=UTC)
        repo.add_monitoring_entry(_entry("m-1", sample_case.id, created_at))
        repo.add_monitoring_entry(_entry("m-2", "other-case", created_at))

        entries = repo.list_monitoring_entries(sample_case.id)
        assert [e.id for e in entries] == ["m-1"]

    def test_delete_case_cascades_to_monitoring_entries(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        created_at = datetime(2026, 6, 12, 8, 0, 0, tzinfo=UTC)
        repo.add_monitoring_entry(_entry("m-1", sample_case.id, created_at))
        repo.add_monitoring_entry(_entry("m-2", sample_case.id, created_at))

        repo.delete(sample_case.id)

        # DSGVO-Kaskade (Art. 17, ADR-0038): kein verwaister Eintrag.
        assert repo.list_monitoring_entries(sample_case.id) == []


class TestArchitectureSketchColumn:
    """P11 (ADR-0049): architecture_sketch als nullable Spalte am Case."""

    def test_update_field_persists_and_survives_reload(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        repo = SQLiteRepository(db_path)
        repo.save(sample_case)
        sketch_json = json.dumps(
            {
                "graph": {"nodes": [], "edges": []},
                "mermaid_source": "flowchart LR",
                "generated_at": "2026-07-05T10:00:00+00:00",
                "prompt_version": "v1",
            }
        )
        repo.update_field(sample_case.id, "architecture_sketch", sketch_json)

        reloaded = SQLiteRepository(db_path).get(sample_case.id)
        assert reloaded is not None
        assert reloaded.architecture_sketch == sketch_json

    def test_default_is_none(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.architecture_sketch is None

    def test_delete_removes_sketch(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        repo.update_field(sample_case.id, "architecture_sketch", '{"x": 1}')

        repo.delete(sample_case.id)

        # DSGVO-Kaskade: die Skizze liegt in der Case-Zeile und stirbt mit ihr.
        assert repo.get(sample_case.id) is None

    def test_migration_adds_column_to_old_table(self, db_path: Path) -> None:
        """Alte DB ohne architecture_sketch-Spalte -> _init_db ergaenzt sie."""
        from aect.adapters.sqlite.connection import connect

        with connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE submitted_cases ("
                "id TEXT PRIMARY KEY, submitted_at TEXT NOT NULL, "
                "use_case_json TEXT NOT NULL, result_json TEXT NOT NULL)"
            )

        # Konstruktion triggert _init_db() -> PRAGMA-gestuetzte Migration.
        SQLiteRepository(db_path)

        with connect(db_path) as conn:
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(submitted_cases)")
            }
        assert "architecture_sketch" in columns


class TestSharpeningDraftColumn:
    """V4 (Draft/Accept-Flow): sharpening_draft als nullable Spalte am Case."""

    def test_update_field_persists_and_survives_reload(
        self, db_path: Path, sample_case: SubmittedCase
    ) -> None:
        repo = SQLiteRepository(db_path)
        repo.save(sample_case)
        draft_json = json.dumps(
            {
                "original": {"title": "x", "current_state": "y", "desired_state": "z"},
                "sharpened": {
                    "sharpened_title": "s",
                    "sharpened_current_state": "sc",
                    "sharpened_desired_state": "sd",
                },
                "improvement_suggestions": [],
                "prompt_version": "v3",
                "created_at": "2026-07-10T10:00:00+00:00",
            }
        )
        repo.update_field(sample_case.id, "sharpening_draft", draft_json)

        reloaded = SQLiteRepository(db_path).get(sample_case.id)
        assert reloaded is not None
        assert reloaded.sharpening_draft == draft_json

    def test_default_is_none(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.sharpening_draft is None

    def test_clearing_draft_sets_none(
        self, repo: SQLiteRepository, sample_case: SubmittedCase
    ) -> None:
        repo.save(sample_case)
        repo.update_field(sample_case.id, "sharpening_draft", '{"x": 1}')
        repo.update_field(sample_case.id, "sharpening_draft", None)

        loaded = repo.get(sample_case.id)
        assert loaded is not None
        assert loaded.sharpening_draft is None

    def test_migration_adds_column_to_old_table(self, db_path: Path) -> None:
        """Alte DB ohne sharpening_draft-Spalte -> _init_db ergaenzt sie."""
        from aect.adapters.sqlite.connection import connect

        with connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE submitted_cases ("
                "id TEXT PRIMARY KEY, submitted_at TEXT NOT NULL, "
                "use_case_json TEXT NOT NULL, result_json TEXT NOT NULL)"
            )

        SQLiteRepository(db_path)

        with connect(db_path) as conn:
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(submitted_cases)")
            }
        assert "sharpening_draft" in columns

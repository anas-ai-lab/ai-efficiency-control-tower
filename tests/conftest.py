# tests/conftest.py
"""Shared pytest fixtures and configuration."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from aect.adapters.api.settings import Settings
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
# Test-Isolation gegen die lokale .env
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True, scope="session")
def _isolate_settings_from_local_env() -> Iterator[None]:
    """Kappt die .env-Datei als Settings-Quelle fuer den gesamten Testlauf.

    WARUM (belegter Befund, nicht vorsorglich):
    Settings (pydantic-settings) liest ``.env`` ueber model_config; die
    Prioritaet ist Konstruktor-Kwargs > Key Vault > Env > .env. Die Suite baut
    ihre Settings mit Kwargs (z. B. ``Settings(api_key=TEST_API_KEY)``) -- alle
    NICHT genannten Felder fallen aber weiter auf die lokale .env durch. Ein
    dort gesetztes ``AECT_DB_PATH=data/aect.db`` (die echte Entwickler-DB)
    schlug damit auf zwei Wegen in die Tests durch:

      1. get_triage_service() -> SQLiteRepository auf jener DB. GET /cases
         lieferte deren echte Cases statt ``[]`` -- und schlimmer: die Suite
         SCHRIEB ihre Testfaelle dort hinein (kumulativ, Lauf fuer Lauf).
      2. get_token_budget_store() -> SQLiteTokenBudgetStore auf derselben DB.
         Der Token-Verbrauch der Budget-Tests ueberlebte den Prozess: im selben
         Stundenfenster startete der naechste Lauf mit erschoepftem Budget und
         bekam 429 statt 200. Der autouse-Reset in tests/adapters/api/conftest.py
         leert nur den In-Memory-Store und lief dagegen ins Leere.

    Beide Symptome hatten also EINE Ursache, aber zwei Mechanismen.

    WARUM SO:
    ``db_path=""`` (= In-Memory-Adapter) ist der dokumentierte Default und exakt
    der Zustand, den CI faehrt: dort existiert keine .env (gitignored) und der
    pytest-Job setzt keine AECT_-Variablen -- deshalb war CI immer gruen und nur
    lokal rot. Der Fix stellt lokal denselben Zustand her, statt eine
    Temp-SQLite-Datei zu erfinden, die keine der beiden Umgebungen nutzt.

    ``AECT_DB_PATH`` wird zusaetzlich aus os.environ entfernt: sonst reichte ein
    exportiertes ``AECT_DB_PATH=... uv run pytest``, um dieselbe Falle ueber die
    Env-Quelle wieder aufzureissen.

    NICHT GEKAPPT: die Env-Quelle als solche bleibt aktiv --
    test_keyvault_settings.py setzt AECT_API_KEY/AECT_AZURE_KEY_VAULT_URL per
    monkeypatch und prueft genau deren Vorrang. Nur die Datei-Quelle faellt weg.

    Session-Scope genuegt: get_settings() hat bewusst keinen lru_cache und es
    gibt keine modul-globale Settings()-Instanz zur Importzeit -- jede Instanz
    entsteht erst zur Request-/Aufrufzeit, also lange nach dieser Fixture.
    """
    mp = pytest.MonkeyPatch()
    mp.setitem(Settings.model_config, "env_file", None)
    mp.delenv("AECT_DB_PATH", raising=False)
    yield
    mp.undo()


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

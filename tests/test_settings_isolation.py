"""Regressionsschutz fuer die Test-Isolation gegen lokale Settings-Quellen.

Hintergrund: die lokale .env setzte ``AECT_DB_PATH`` auf die echte Entwickler-DB.
Weil die Suite ihre Settings mit Kwargs baut (nicht genannte Felder fallen auf
.env durch), lief sie damit gegen jene DB -- vier Tests schlugen ueber Sessions
hinweg fehl und die Suite schrieb ihre Faelle in die DB. CI merkte davon nie
etwas: dort existiert keine .env. Details in der Fixture
``_isolate_settings_from_local_env`` (tests/conftest.py).

Diese Tests halten den Fix fest -- inklusive des Falls, den ein blosses
Assert auf ``Settings().db_path`` NICHT abdeckt: in CI (ohne .env) wuerde ein
solches Assert auch ohne Fixture gruen sein. Der Subprozess-Test unten baut die
Falle daher selbst nach und ist damit auch in CI aussagekraeftig.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from aect.adapters.api.settings import Settings
from aect.adapters.sqlite.repository import SQLiteRepository
from aect.application.models import SubmittedCase
from aect.domain import UseCaseInput, evaluate_use_case, load_roi_config

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Die vier Tests, die an der undichten Settings-Quelle scheiterten: einer ueber
# das Repository (echte Cases statt []), drei ueber den persistenten
# SQLiteTokenBudgetStore (verbrauchtes Stundenbudget -> 429 statt 200).
_PREVIOUSLY_FAILING = [
    "tests/adapters/api/test_auth.py::test_public_list_cases_without_auth_returns_200",
    "tests/adapters/api/test_token_budget.py",
]


def test_local_dotenv_does_not_reach_settings_in_tests() -> None:
    """Im Testlauf ist die .env-Datei keine Settings-Quelle mehr.

    Ohne die Fixture liefert Settings().db_path lokal 'data/aect.db' (aus .env)
    -- und damit SQLiteRepository + SQLiteTokenBudgetStore auf der echten DB.
    """
    assert Settings.model_config["env_file"] is None
    assert Settings().db_path == ""


def test_suite_stays_isolated_when_aect_db_path_points_at_populated_db(
    tmp_path: Path,
    sample_use_case: UseCaseInput,
) -> None:
    """Gegenbeweis: selbst mit AECT_DB_PATH auf einer BEFUELLTEN DB laufen die
    zuvor scheiternden Tests gruen -- und die DB bleibt unberuehrt.

    Simuliert exakt die reale Falle (befuellte DB + gesetzte Variable) in einem
    Subprozess, weil die Isolation beim Start der Session greift und sich im
    laufenden Prozess nicht mehr glaubwuerdig herstellen laesst.
    """
    # 1. Befuellte DB anlegen -- ein echter Case, wie ihn die Entwickler-DB traegt.
    db_path = tmp_path / "populated.db"
    repo = SQLiteRepository(db_path)
    repo.save(
        SubmittedCase(
            id="isolation-probe-001",
            submitted_at=datetime(2026, 7, 17, 10, 0, 0, tzinfo=UTC),
            use_case=sample_use_case,
            result=evaluate_use_case(sample_use_case, load_roi_config()),
        )
    )
    rows_before = len(repo.list_all())
    assert rows_before == 1

    # 2. Die frueher scheiternden Tests mit genau dieser DB in der Umgebung
    #    laufen lassen -- cwd = Repo-Root, die lokale .env ist also ebenfalls
    #    in Reichweite. --no-cov: die addopts-Coverage des Aussenlaufs wuerde
    #    im Subprozess kollidieren.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *_PREVIOUSLY_FAILING,
            "-q",
            "--no-cov",
            "-p",
            "no:cacheprovider",
        ],
        cwd=_REPO_ROOT,
        env={**os.environ, "AECT_DB_PATH": str(db_path)},
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Tests scheitern, sobald AECT_DB_PATH auf eine befuellte DB zeigt -- "
        f"die Isolation greift nicht.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    # 3. Kein Schreibzugriff: die Suite darf fremde DBs nicht veraendern (genau
    #    das tat sie -- die Entwickler-DB wuchs mit jedem Lauf).
    assert len(SQLiteRepository(db_path).list_all()) == rows_before

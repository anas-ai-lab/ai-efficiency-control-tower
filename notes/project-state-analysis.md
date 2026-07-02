# Project State Analysis — 2026-06-07

Erstellt: 2026-06-07 | Zweck: vollständige Bestandsaufnahme für neuen Chat-Kontext

---

## ABSCHNITT 1: System & Toolchain

```
uname -m:  arm64
uname -r:  25.5.0
uv:        uv 0.11.11 (ed7b06001 2026-05-06 aarch64-apple-darwin)
Python:    Python 3.12.13
git:       git version 2.50.1 (Apple Git-155)
```

**Hinweis:** `uv run python --version` löste einen Rebuild aus:
```
Building aect @ file:///Users/01000101nes/Desktop/Claude/ai-efficiency-control-tower
Built aect @ file:///Users/01000101nes/Desktop/Claude/ai-efficiency-control-tower
Uninstalled 1 package in 0.98ms
Installed 1 package in 1ms
Python 3.12.13
```

---

## ABSCHNITT 2: Git-Stand

### git log --oneline -30

```
243c6b4 docs(day-18): daily note + learning-log Zonen-Klassifikation + Machbarkeitscheck
ed626c7 feat(domain): zone classifier, Handlungsdruck elevation, feasibility checker
758af69 docs(day-17): daily note + learning-log Vorfilter + Composite-Score + src-Layout-Fix
d9a8ada feat(domain): Vorfilter + Composite-Aufwand-Score mit Tests
f9679f2 docs(day-16): daily note + learning-log ROI-Engine + build-system fix
743ef0e feat(domain): ROI/Value-Engine mit Vorfilter, Config-TOML, property-based Tests
f1bcda2 docs(day-15): daily note and learning-log entry
044a119 feat(domain): UseCaseInput schema, typed enums, pytest suite
0504e1c docs(day-14): daily note, learning-log — Pydantic V2 schema + TDD
eb8b0b9 feat(domain): UseCaseInput schema + EvidenceQuality enum, TDD suite green
630c55d docs(day-13): daily note + learning-log ADRs, pre-commit two-round behavior
f1fee5c docs: add Makefile, ADR template, and foundational ADRs 0001-0003 (toolchain, hexagonal arch, LLM strategy)
886de0c docs(day-12): daily note + learning-log CI setup, CVE-fix, Node24 learnings
c06e88f fix(deps): upgrade idna to 3.15 (CVE-2026-45409)
3729c25 chore: remove accidental tmp file
025f30e ci: add quality/security/secrets workflow, SHA-pinned actions
7411253 docs: add day 11 daily note and learning log entry
6e19052 chore: add pre-commit hooks (ruff, mypy, standard checks)
21ed987 update
026e7bf docs: add day 10 daily note and learning log entry
4c5df99 chore: update lockfile after adding pytest, pytest-cov, coverage
ac267a6 test: add pytest config, conftest, smoke tests, coverage setup
1efd72b docs: daily note day 09 + learning-log update
284b72d angepasst str
72eac19 chore: configure ruff strict + mypy strict, add Makefile targets
b08f919 docs: add day 08 daily note and learning log entry
6edb553 feat: init uv project with src-layout and Python 3.12
c34a8b4 docs: Architektur
5a3fc42 docs: tag 7 — daily note und learning-log wochenabschluss
cb2de84 docs: add day 6 daily note and learning log entry
```

### git status

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   src/aect.egg-info/SOURCES.txt
	modified:   src/aect.egg-info/dependency_links.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

---

## ABSCHNITT 3: Vollständige Dateistruktur (git ls-files)

```
.coverage 2
.coverage 3
.github/workflows/ci.yml
.gitignore
.pre-commit-config.yaml
.python-version
CLAUDE.md
Makefile
README.md
architecture.md
assets/.gitkeep
config/roi_config.toml
config/zone_thresholds.yaml
data/.gitkeep
docs/.gitkeep
docs/adr/0001-toolchain-und-project-setup.md
docs/adr/0002-hexagonale-architektur.md
docs/adr/0003-llm-strategie-und-provider.md
docs/adr/template.md
docs/adrs/.gitkeep
docs/ai-decision-framework.md
docs/ai_vs_automation_matrix.md
docs/architecture.md
evals/.gitkeep
knowledge_base/.gitkeep
learning-log.md
mypy.ini
notes/daily/2026-05-05-day-01.md
notes/daily/2026-05-05-day-18.md
notes/daily/2026-05-06-day-02.md
notes/daily/2026-05-06-day-04.md
notes/daily/2026-05-06-day-05.md
notes/daily/2026-05-07-day-03.md
notes/daily/2026-05-07-day-06.md
notes/daily/2026-05-07-day-07.md
notes/daily/2026-05-08-day-08.md
notes/daily/2026-05-08-day-09.md
notes/daily/2026-05-08-day-10.md
notes/daily/2026-05-08-day-11.md
notes/daily/2026-06-05-day-12.md
notes/daily/2026-06-05-day-13.md
notes/daily/2026-06-05-day-14.md
notes/daily/2026-06-05-day-15.md
notes/daily/2026-06-05-day-16.md
notes/daily/2026-06-05-day-17.md
notes/decisions/.gitkeep
notes/index.md
notes/reviews/.gitkeep
prompts/.gitkeep
pyproject.toml
sample_reports/.gitkeep
setup_notes.md
src/.gitkeep
src/aect.egg-info/PKG-INFO
src/aect.egg-info/SOURCES.txt
src/aect.egg-info/dependency_links.txt
src/aect.egg-info/requires.txt
src/aect.egg-info/top_level.txt
src/aect/__init__.py
src/aect/domain/__init__.py
src/aect/domain/feasibility.py
src/aect/domain/filters.py
src/aect/domain/models.py
src/aect/domain/roi.py
src/aect/domain/scoring.py
src/aect/domain/types.py
src/aect/domain/zones.py
src/aect/py.typed
tests/.gitkeep
tests/__init__.py
tests/conftest.py
tests/domain/__init__.py
tests/domain/test_feasibility.py
tests/domain/test_filters.py
tests/domain/test_roi.py
tests/domain/test_scoring.py
tests/domain/test_use_case_input.py
tests/domain/test_zones.py
tests/test_smoke.py
uv.lock
workflows/.gitkeep
```

---

## ABSCHNITT 4: Vollständige Dateiinhalte

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.hatch.build.targets.wheel]
packages = ["src/aect"]

[tool.hatch.build.targets.editable]
packages = ["src/aect"]

[project]
name = "aect"
version = "0.1.0"
description = "AI Efficiency Control Tower — AI Use Case Intake & Triage Assistant"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "idna>=3.15",
    "pydantic>=2.13.4",
    "pyyaml>=6.0.3",
]

[dependency-groups]
dev = [
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
    "pytest>=9.0.3",
    "pytest-cov>=7.1.0",
    "coverage>=7.13.5",
    "bandit[toml]>=1.8",
    "pip-audit>=2.7",
    "hypothesis>=6.152.4",
    "types-pyyaml>=6.0.12.20260518",
]
test = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "coverage[toml]>=7.5.0",
    "hypothesis>=6.100.0",
    "httpx>=0.27.0",
]

[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "UP",   # pyupgrade
    "RUF",  # ruff-specific rules
    "SIM",  # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "RUF002",  # Unicode-Mathesymbole (x, -) in Docstrings erlaubt
    "RUF003",  # Unicode-Mathesymbole (x, -) in Kommentaren erlaubt
]

[tool.ruff.lint.isort]
known-first-party = ["aect"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--tb=short",
    "--cov=src/aect",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
]
pythonpath = ["src"]

[tool.coverage.run]
source = ["src/aect"]
branch = true
omit = ["*/tests/*", "*/conftest.py"]

[tool.coverage.report]
show_missing = true
fail_under = 0
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "\\.\\.\\.\\s*$",
]

[tool.bandit]
exclude_dirs = ["tests", ".venv"]
```

---

### .pre-commit-config.yaml

```yaml
# .pre-commit-config.yaml
# Versionen werden via `pre-commit autoupdate` aktuell gehalten

repos:
  # Ruff: Linting + Formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.12
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Mypy: Type Checking via lokale Umgebung (kennt alle Projekt-Deps)
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false
        args: [src/]

  # Standard-Checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: debug-statements
      - id: check-merge-conflict
```

---

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

# Minimale Berechtigungen auf Workflow-Ebene (Security Checklist)
permissions:
  contents: read

jobs:
  # ─── Job 1: Lint · Typecheck · Test ────────────────────────────────────────
  quality:
    name: Lint · Typecheck · Test
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2            # SHA: Schritt 5

      - name: Set up uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b  # v8.1.0
        with:
          enable-cache: true
          python-version: "3.12"

      - name: Install dependencies (frozen)
        run: uv sync --frozen

      - name: Lint — ruff check
        run: uv run ruff check src/ tests/

      - name: Format check — ruff format
        run: uv run ruff format --check src/ tests/

      - name: Type check — mypy
        run: uv run mypy src/

      - name: Test + Coverage — pytest
        run: uv run pytest --cov=src/aect --cov-report=term-missing -q

  # ─── Job 2: SAST · Dependency CVE ──────────────────────────────────────────
  security:
    name: SAST · Deps
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2            # SHA: Schritt 5

      - name: Set up uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b  # v8.1.0
        with:
          enable-cache: true
          python-version: "3.12"

      - name: Install dependencies (frozen)
        run: uv sync --frozen

      - name: SAST — bandit (MEDIUM+)
        run: uv run bandit -r src/ -ll

      - name: Dependency CVE scan — pip-audit
        run: uv run pip-audit

  # ─── Job 3: Secret scan ─────────────────────────────────────────────────────
  secrets:
    name: Secret scan
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Checkout (full history)
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd  # v6.0.2            # SHA: Schritt 5
        with:
          fetch-depth: 0

      - name: Gitleaks
        uses: gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e  # v3   # SHA: Schritt 5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Kein GITLEAKS_LICENSE nötig: privates Repo auf persönlichem Account
```

---

### Makefile

```makefile
# Makefile — AECT Development Commands
# Alle Befehle laufen über `uv run` — kein globales Pip nötig

.PHONY: help lint format typecheck test check clean

help:  ## Verfügbare Befehle anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

lint:  ## Ruff linter ausführen
	uv run ruff check src/ tests/

format:  ## Ruff formatter ausführen
	uv run ruff format src/ tests/

typecheck:  ## mypy type checker ausführen (strict)
	uv run mypy src/

test:  ## pytest mit Coverage ausführen
	uv run pytest --cov=src/aect --cov-report=term-missing -q

check:  ## Vollständiger Pre-Commit-Check (vor jedem Commit)
	uv run pre-commit run --all-files
	uv run pytest -q
	uv run mypy src/

clean:  ## Cache-Verzeichnisse entfernen
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
```

---

### src/aect/__init__.py

```python
"""AI Efficiency Control Tower — AI Use Case Intake & Triage Assistant."""

__version__: str = "0.1.0"
__author__: str = "anas-ai-lab"
```

---

### src/aect/domain/__init__.py

```python
"""AECT Domain-Schicht — öffentliche API.

Hexagonal Architecture: Die Domain-Schicht ist die innerste Schicht.
Erlaubte Imports: Standard-Library, Pydantic.
Verbotene Imports: aect.adapters, aect.application (würde Dependency
Inversion verletzen).
"""

from aect.domain.feasibility import (
    FeasibilityChecker,
    FeasibilityFlag,
    FeasibilityResult,
)
from aect.domain.filters import FilterResult, apply_prefilter
from aect.domain.models import UseCaseInput
from aect.domain.roi import ROIConfig, ROIResult, calculate_roi, load_roi_config
from aect.domain.scoring import CompositeScore, compute_composite_score
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    FrequencyUnit,
    ImplementationApproach,
    TriageZone,
)
from aect.domain.zones import ZoneClassifier, ZoneResult, load_zone_classifier

__all__ = [
    # types
    "AdoptionType",
    # scoring
    "CompositeScore",
    "DataClassification",
    "EmployeeCategory",
    "EvidenceLevel",
    # feasibility
    "FeasibilityChecker",
    "FeasibilityFlag",
    "FeasibilityResult",
    # filters
    "FilterResult",
    "FrequencyUnit",
    "ImplementationApproach",
    # roi
    "ROIConfig",
    "ROIResult",
    "TriageZone",
    # models
    "UseCaseInput",
    # zones
    "ZoneClassifier",
    "ZoneResult",
    "apply_prefilter",
    "calculate_roi",
    "compute_composite_score",
    "load_roi_config",
    "load_zone_classifier",
]
```

---

### src/aect/domain/types.py

```python
"""Domain-Typen für AECT — kontrollierte Vokabular-Enums.

Alle Enum-Werte sind snake_case (StrEnum — direktes Parsen aus JSON/Form-Daten,
kein manuelles .value-Mapping nötig).

IP-Trennung (vertraglich bedingt): Faktor-Mappings (Stundensätze, Score-Gewichte,
Vorfilter-Schwellen) liegen in config/roi_config.yaml — nicht hier.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceLevel(StrEnum):
    """Qualität der Zeitersparnis-Schätzung.

    Beeinflusst den Evidenzfaktor im ROI-Modell (aufsteigend nach Verlässlichkeit).
    Konkretes Faktor-Mapping (z. B. 0.5 / 0.75 / 0.95) liegt in config/roi_config.yaml.
    """

    PURE_ESTIMATE = "pure_estimate"  # Bauchgefühl / Expertenmeinung ohne Datenbasis
    SIMILAR_PROJECT = "similar_project"  # Analogie zu vergleichbarem Vorhaben
    TESTED_PILOTED = "tested_piloted"  # Gemessen oder in Pilotprojekt validiert


class AdoptionType(StrEnum):
    """Verbindlichkeit der Nutzung — beeinflusst den Nutzungsfaktor im ROI-Modell."""

    MANDATORY = "mandatory"  # Pflichtnutzung (regulatorisch oder Prozessanweisung)
    VOLUNTARY = "voluntary"  # Freiwillig / opt-in


class ImplementationApproach(StrEnum):
    """Geplante Umsetzungsstrategie."""

    STANDARD_PRODUCT = "standard_product"  # COTS / Out-of-the-box-Lösung
    CUSTOM_BUILD = "custom_build"  # Eigenentwicklung
    VENDOR_SOLUTION = "vendor_solution"  # Drittanbieter mit Customizing


class DataClassification(StrEnum):
    """Datenschutz-Einstufung der verarbeiteten Daten.

    Beeinflusst den Datenschutz-Anteil im Composite-Aufwand-Score (aufsteigend).
    Score-Mapping: NO_PERSONAL_DATA=0, PSEUDONYMOUS=1, PERSONAL=1, SENSITIVE_PERSONAL=2.
    Mapping liegt in config, nicht hier.
    """

    NO_PERSONAL_DATA = "no_personal_data"  # Rein operative / anonyme Daten
    PSEUDONYMOUS = "pseudonymous"  # Pseudonymisiert (Art. 4 Nr. 5 DSGVO)
    PERSONAL = "personal"  # Personenbezogen (Art. 4 Nr. 1 DSGVO)
    SENSITIVE_PERSONAL = "sensitive_personal"  # Besondere Kategorien (Art. 9 DSGVO)


class FrequencyUnit(StrEnum):
    """Bezugszeitraum für instances_per_period."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class EmployeeCategory(StrEnum):
    """Grobe Seniorität der betroffenen Mitarbeiter.

    Konkretes Stundensatz-Mapping (je Land x Stufe) liegt in config/roi_config.yaml.
    Dieses Enum ist der IP-saubere Anker — keine Firmenzahlen im Code.
    """

    JUNIOR = "junior"  # Einsteiger / Analyst / Junior Developer
    PROFESSIONAL = "professional"  # Erfahrener Berater / Fachexperte
    SENIOR = "senior"  # Senior / Manager / Principal Expert
    MIXED = "mixed"  # Heterogenes Team — Config nutzt konfigurierten Mittelwert


class TriageZone(StrEnum):
    """Outcome zone for AECT use-case triage.

    MARGINAL_GAIN: insufficient benefit or excessive complexity.
    CALCULATED_RISK: viable with caveats — proceed with caution.
    LIKELY_WIN: high benefit, manageable complexity.
    """

    MARGINAL_GAIN = "MARGINAL_GAIN"
    CALCULATED_RISK = "CALCULATED_RISK"
    LIKELY_WIN = "LIKELY_WIN"
```

---

### src/aect/domain/models.py

```python
"""Domain-Modelle für AECT.

Schicht: domain — kein Import aus adapters/, application/ oder externen
Infrastruktur-Libraries (kein FastAPI, kein SQLAlchemy, kein httpx).
Erlaubt: pydantic, Python stdlib, eigene domain-interne Module.

Security by Design:
  extra='forbid'          → kein unerwarteter Input umgeht die Validierung (OWASP LLM10)
  max_length auf ALLEN Freitextfeldern → Schutz gegen Token-Flooding in Phase C
  frozen=True             → Domain-Eingabeobjekte sind nach Erstellung unveränderlich

Anreicherung durch den Application-Layer passiert in separaten Ausgabeobjekten
(TriageResult — wird in Phase B/C eingeführt), nicht durch Mutation dieses Objekts.

IP-Trennung (vertraglich bedingt): Stundensätze, Faktor-Mappings, Vorfilter-Schwellen
liegen in config/roi_config.yaml — nie in diesem Modell.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)


class UseCaseInput(BaseModel):
    """Eingabe-Schema für einen AI-Use-Case-Antrag.

    Entspricht den Feldern des v5-Bewertungsmodells:
    Stammdaten / Ist-Soll / Mengen / Zeit / Evidenz / Verbindlichkeit /
    Kosten / Datenschutz / Handlungsdruck.

    Alle Freitextfelder: min_length + max_length (Substanz + Token-Budget).
    Alle Enum-Felder: StrEnum — parst direkt aus JSON-Strings.
    Die Rule Engine (Phase A) liest ausschließlich dieses Objekt.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )

    # ── Stammdaten ────────────────────────────────────────────────────────────
    title: str = Field(
        min_length=5,
        max_length=200,
        description="Kurzer, sprechender Name des Use Case",
    )
    submitter: str = Field(
        min_length=1,
        max_length=100,
        description="Name der einreichenden Person",
    )
    department: str = Field(
        min_length=1,
        max_length=100,
        description="Abteilung / Organisationseinheit",
    )

    # ── Ist / Soll / Beispiel ─────────────────────────────────────────────────
    current_state: str = Field(
        min_length=30,
        max_length=2000,
        description="Beschreibung des aktuellen Prozesses (Ist-Zustand)",
    )
    desired_state: str = Field(
        min_length=30,
        max_length=2000,
        description="Beschreibung des gewünschten Zustands nach AI-Einsatz",
    )
    example_process: str = Field(
        min_length=20,
        max_length=2000,
        description="Konkretes Beispiel eines einzelnen Vorgangs (nicht Gesamtvolumen)",
    )

    # ── Quantitative Felder (required — ohne diese keine ROI-Berechnung) ─────
    time_savings_hours_per_case: float = Field(
        gt=0.0,
        le=8.0,
        description="Geschätzte Zeitersparnis pro Vorgang in Stunden (max = 8 h)",
    )
    frequency_per_year: int = Field(
        gt=0,
        le=1_000_000,
        description="Anzahl Vorgänge pro Jahr",
    )
    affected_employees_count: int = Field(
        gt=0,
        le=50_000,
        description="Anzahl Mitarbeiter, die diesen Prozess heute manuell durchführen",
    )
    employee_category: EmployeeCategory = Field(
        description="Grobe Seniorität der betroffenen Mitarbeiter (→ Stundensatz aus Config)",
    )

    # ── Evidenz & Verbindlichkeit ─────────────────────────────────────────────
    evidence_level: EvidenceLevel = Field(
        default=EvidenceLevel.PURE_ESTIMATE,
        description="Qualität der Grundlage für die Zeitersparnis-Schätzung",
    )
    adoption_type: AdoptionType = Field(
        description="Pflicht- oder Freiwillignutzung (beeinflusst Nutzungsfaktor)",
    )
    implementation_approach: ImplementationApproach = Field(
        description="Geplante Umsetzungsstrategie",
    )

    # ── Kosten ────────────────────────────────────────────────────────────────
    estimated_license_cost_eur: float = Field(
        default=0.0,
        ge=0.0,
        le=10_000_000.0,
        description="Geschätzte Lizenzkosten p.a. in EUR (0 = open-source oder intern gebaut)",
    )
    implementation_complexity: int = Field(
        ge=1,
        le=5,
        description="Technische Komplexität: 1 = trivial, 3 = mittel, 5 = sehr hoch",
    )

    # ── Datenschutz ───────────────────────────────────────────────────────────
    contains_pii: bool = Field(
        default=False,
        description="Werden personenbezogene Daten verarbeitet? (Schnellcheck)",
    )
    data_classification: DataClassification = Field(
        description=(
            "Datenschutz-Einstufung der verarbeiteten Daten. "
            "SENSITIVE_PERSONAL → Datenschutz-Score 2 im Composite-Aufwand-Score."
        ),
    )

    # ── Handlungsdruck (für Zonen-Hochstufung) ───────────────────────────────
    regulatory_pressure: bool = Field(
        default=False,
        description="Regulatorischer Druck (Compliance-Anforderung, Audit-Finding)?",
    )
    competitive_pressure: bool = Field(
        default=False,
        description="Wettbewerbsdruck (Branche setzt AI bereits ein)?",
    )
    strategic_priority: bool = Field(
        default=False,
        description="Explizit strategische Priorität von Vorstand oder Management?",
    )
```

---

### src/aect/domain/roi.py

```python
"""ROI / Value-Engine — deterministisch, ohne LLM-Calls.

Implementiert das v5-Bewertungsmodell:
  Theoretisches Potenzial  = Stundenwert × Zeit_pro_Vorgang × Jahres-Multiplikator
                             × Mitarbeiterzahl
  Erwarteter Nutzen        = Potenzial × Nutzungsfaktor × Evidenzfaktor
  Netto-Nutzen             = Erwarteter Nutzen − Lizenzkosten
  Vorfilter                = 3 Schwellenwerte (Potenzial, Stunden, Netto-Nutzen)

Alle firmenspezifischen Parameter kommen per ROIConfig rein (vertraglich bedingte IP-Trennung).
Kein Hardcoding von Stundensätzen oder Schwellen im Code.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from aect.domain.models import UseCaseInput

# ---------------------------------------------------------------------------
# Frequenz → Jahres-Multiplikator
# Keys = FrequencyUnit.value aus src/aect/domain/types.py
# Nach Schritt 0: prüfen ob die Enum-Werte stimmen, ggf. Keys anpassen.
# ---------------------------------------------------------------------------
_FREQUENCY_TO_ANNUAL: Final[dict[str, int]] = {
    "DAILY": 250,  # Arbeitstage pro Jahr
    "WEEKLY": 52,
    "BIWEEKLY": 26,
    "MONTHLY": 12,
    "QUARTERLY": 4,
    "ANNUALLY": 1,
}

_TWO_PLACES: Final[Decimal] = Decimal("0.01")


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ROIConfig:
    """Alle numerischen Parameter des ROI-Modells.

    Wird per load_roi_config() befüllt — nie inline konstruieren (außer in Tests).
    IP-Trennung: Stundensätze und Schwellen in TOML, nie im Code (vertraglich bedingte IP-Trennung).

    hourly_rates:     {"DE": {"PROFESSIONAL": Decimal("65"), ...}, ...}
    evidence_factors: {"HIGH": 1.0, "MEDIUM": 0.75, ...}  — Keys = EvidenceLevel.value
    adoption_factors: {"HIGH": 1.0, "MEDIUM": 0.60, ...}  — Keys = AdoptionType.value
    """

    hourly_rates: dict[str, dict[str, Decimal]]
    evidence_factors: dict[str, float]
    adoption_factors: dict[str, float]
    min_potential_eur: Decimal
    min_hours_per_year: float
    min_expected_benefit_eur: Decimal


def load_roi_config(path: Path | None = None) -> ROIConfig:
    """Lädt ROIConfig aus config/roi_config.toml (Repo-Root).

    Sucht standardmäßig 3 Ebenen über diesem Modul (src/aect/domain/ → Repo-Root).
    Für Tests ROIConfig direkt konstruieren — kein Dateisystem-Zugriff nötig.
    """
    if path is None:
        # src/aect/domain/roi.py → parents[0]=domain, [1]=aect, [2]=src, [3]=repo_root
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / "config" / "roi_config.toml"

    with path.open("rb") as f:
        raw = tomllib.load(f)

    return ROIConfig(
        hourly_rates={
            country: {lvl: Decimal(str(rate)) for lvl, rate in rates.items()}
            for country, rates in raw["hourly_rates"].items()
        },
        evidence_factors={k: float(v) for k, v in raw["evidence_factors"].items()},
        adoption_factors={k: float(v) for k, v in raw["adoption_factors"].items()},
        min_potential_eur=Decimal(str(raw["thresholds"]["min_potential_eur"])),
        min_hours_per_year=float(raw["thresholds"]["min_hours_per_year"]),
        min_expected_benefit_eur=Decimal(
            str(raw["thresholds"]["min_expected_benefit_eur"])
        ),
    )


# ---------------------------------------------------------------------------
# Ergebnis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ROIResult:
    """Unveränderliches Berechnungsergebnis.

    Alle monetären Werte in EUR, auf 2 Dezimalstellen gerundet.
    Invariante (property-based getestet): expected_benefit_eur <= theoretical_potential_eur.
    hours_per_year = Gesamtstunden Organisation (Einzelersparnis × Mitarbeiterzahl).
    """

    theoretical_potential_eur: Decimal  # Stundenwert × Gesamtstunden
    usage_factor: float  # Nutzungsfaktor (aus AdoptionType)
    evidence_factor: float  # Evidenzfaktor (aus EvidenceLevel)
    expected_benefit_eur: Decimal  # Potenzial × Nutzung × Evidenz (vor Lizenz)
    license_cost_annual_eur: Decimal  # Jährliche Lizenzkosten
    net_expected_benefit_eur: Decimal  # expected − license (kann negativ sein)
    hours_per_year: float  # Gesamtstunden Organisation pro Jahr
    passes_prefilter: bool
    prefilter_fail_reason: str | None  # None wenn passes_prefilter is True


# ---------------------------------------------------------------------------
# Hilfsfunktionen — direkt testbar, ohne UseCaseInput
# ---------------------------------------------------------------------------


def _to_annual_hours(
    time_per_occurrence: float,
    occurrences_per_period: float,
    frequency_unit_value: str,
) -> float:
    """Rechnet Häufigkeit in jährliche Stunden (pro Person) um."""
    multiplier = _FREQUENCY_TO_ANNUAL.get(frequency_unit_value)
    if multiplier is None:
        msg = (
            f"Unbekannte FrequencyUnit: {frequency_unit_value!r}. "
            f"Gültige Werte: {sorted(_FREQUENCY_TO_ANNUAL)}"
        )
        raise ValueError(msg)
    return time_per_occurrence * occurrences_per_period * multiplier


def _check_prefilter(
    theoretical_potential: Decimal,
    hours_per_year: float,
    net_expected_benefit: Decimal,
    config: ROIConfig,
) -> tuple[bool, str | None]:
    """Prüft die drei Vorfilter-Bedingungen in fester Reihenfolge."""
    if theoretical_potential < config.min_potential_eur:
        return False, (
            f"Theoretisches Potenzial {theoretical_potential} EUR "
            f"< Schwelle {config.min_potential_eur} EUR"
        )
    if hours_per_year < config.min_hours_per_year:
        return False, (
            f"Jährliche Stunden {hours_per_year:.1f} "
            f"< Schwelle {config.min_hours_per_year:.1f}"
        )
    if net_expected_benefit < config.min_expected_benefit_eur:
        return False, (
            f"Netto-Nutzen {net_expected_benefit} EUR "
            f"< Schwelle {config.min_expected_benefit_eur} EUR"
        )
    return True, None


def _calculate_roi_values(
    *,
    employee_country: str,
    employee_category_value: str,
    time_saved_per_occurrence_hours: float,
    occurrences_per_period: float,
    frequency_unit_value: str,
    employees_affected: int,
    license_cost_annual_eur: float,
    adoption_type_value: str,
    evidence_level_value: str,
    config: ROIConfig,
) -> ROIResult:
    """Kernberechnung — seiteneffektfrei, deterministisch."""
    rate: Decimal = config.hourly_rates.get(employee_country, {}).get(
        employee_category_value, Decimal("0")
    )
    hours_per_person = _to_annual_hours(
        time_per_occurrence=time_saved_per_occurrence_hours,
        occurrences_per_period=occurrences_per_period,
        frequency_unit_value=frequency_unit_value,
    )
    total_hours = hours_per_person * employees_affected
    potential = (Decimal(str(total_hours)) * rate).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )
    usage = config.adoption_factors.get(adoption_type_value, 0.0)
    evidence = config.evidence_factors.get(evidence_level_value, 0.0)
    expected = (potential * Decimal(str(usage)) * Decimal(str(evidence))).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )
    license_cost = Decimal(str(license_cost_annual_eur)).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )
    net = (expected - license_cost).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    passes, reason = _check_prefilter(
        theoretical_potential=potential,
        hours_per_year=total_hours,
        net_expected_benefit=net,
        config=config,
    )
    return ROIResult(
        theoretical_potential_eur=potential,
        usage_factor=usage,
        evidence_factor=evidence,
        expected_benefit_eur=expected,
        license_cost_annual_eur=license_cost,
        net_expected_benefit_eur=net,
        hours_per_year=total_hours,
        passes_prefilter=passes,
        prefilter_fail_reason=reason,
    )


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def calculate_roi(input: UseCaseInput, config: ROIConfig) -> ROIResult:
    """Öffentlicher Einstiegspunkt: UseCaseInput → ROIResult.

    TODO: Adapter-Implementierung nach Schritt 0 (Feldnamen aus models.py verifizieren).
    NotImplementedError entfernen und Feldnamen eintragen sobald verifiziert.
    """
    raise NotImplementedError(
        "calculate_roi-Adapter: Feldnamen aus models.py in Schritt 0 prüfen, "
        "dann _calculate_roi_values(...) mit den echten Feldnamen aufrufen."
    )
```

---

### src/aect/domain/filters.py

```python
"""
Vorfilter — drei Mindestkriterien für AI-Use-Case-Einreichungen.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MIN_THEORETICAL_POTENTIAL_EUR: float = 20_000.0
DEFAULT_MIN_HOURS_PER_YEAR: float = 120.0
DEFAULT_MIN_NET_BENEFIT_EUR: float = 5_000.0


@dataclass(frozen=True)
class FilterResult:
    passes: bool
    failed_criteria: list[str]
    details: dict[str, bool]

    def __post_init__(self) -> None:
        if self.passes and self.failed_criteria:
            raise ValueError("passes=True, aber failed_criteria nicht leer")
        if not self.passes and not self.failed_criteria:
            raise ValueError("passes=False, aber keine failed_criteria angegeben")


def apply_prefilter(
    theoretical_potential_eur: float,
    hours_per_year: float,
    net_benefit_eur: float,
    *,
    min_potential: float = DEFAULT_MIN_THEORETICAL_POTENTIAL_EUR,
    min_hours: float = DEFAULT_MIN_HOURS_PER_YEAR,
    min_net_benefit: float = DEFAULT_MIN_NET_BENEFIT_EUR,
) -> FilterResult:
    criteria: dict[str, bool] = {
        "Theoretisches Potenzial": theoretical_potential_eur >= min_potential,
        "Stundeneinsparung": hours_per_year >= min_hours,
        "Nettonutzen": net_benefit_eur >= min_net_benefit,
    }
    failed = [name for name, passed in criteria.items() if not passed]
    return FilterResult(
        passes=len(failed) == 0,
        failed_criteria=failed,
        details=criteria,
    )
```

---

### src/aect/domain/scoring.py

```python
"""
Composite-Aufwand-Score einer Use-Case-Einreichung.

Score = Komplexität (1-5) + Implementierungskosten (1-3) + Datenschutz-Stufe (0-2)
Wertebereich: 2–10. Je höher, desto aufwändiger/riskanter.
"""

from __future__ import annotations

from dataclasses import dataclass

from aect.domain.types import DataClassification

DATA_CLASSIFICATION_TO_SCORE: dict[DataClassification, int] = {
    DataClassification.NO_PERSONAL_DATA: 0,
    DataClassification.PSEUDONYMOUS: 1,
    DataClassification.PERSONAL: 2,
    DataClassification.SENSITIVE_PERSONAL: 2,
}


@dataclass(frozen=True)
class CompositeScore:
    complexity_score: int
    cost_score: int
    data_protection_score: int
    total: int

    def __post_init__(self) -> None:
        if not (1 <= self.complexity_score <= 5):
            raise ValueError(f"complexity_score muss 1-5 sein, ist {self.complexity_score}")
        if not (1 <= self.cost_score <= 3):
            raise ValueError(f"cost_score muss 1-3 sein, ist {self.cost_score}")
        if not (0 <= self.data_protection_score <= 2):
            raise ValueError(f"data_protection_score muss 0-2 sein, ist {self.data_protection_score}")
        expected = self.complexity_score + self.cost_score + self.data_protection_score
        if self.total != expected:
            raise ValueError(f"total ({self.total}) stimmt nicht mit Summe ({expected}) überein")

    @property
    def effort_label(self) -> str:
        if self.total <= 4:
            return "NIEDRIG"
        if self.total <= 7:
            return "MITTEL"
        return "HOCH"


def compute_composite_score(
    complexity: int,
    cost: int,
    data_classification: DataClassification,
) -> CompositeScore:
    if not (1 <= complexity <= 5):
        raise ValueError(f"complexity muss 1-5 sein, ist {complexity}")
    if not (1 <= cost <= 3):
        raise ValueError(f"cost muss 1-3 sein, ist {cost}")
    data_score = DATA_CLASSIFICATION_TO_SCORE[data_classification]
    total = complexity + cost + data_score
    return CompositeScore(
        complexity_score=complexity,
        cost_score=cost,
        data_protection_score=data_score,
        total=total,
    )
```

---

### src/aect/domain/zones.py

```python
"""Deterministic zone classification for AECT use-case triage."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import yaml

from aect.domain.types import TriageZone


@dataclass(frozen=True)
class ZoneResult:
    base_zone: TriageZone
    final_zone: TriageZone
    handlungsdruck_elevated: bool
    reason: str


class ZoneClassifier:
    _ELEVATION: ClassVar[dict[TriageZone, TriageZone]] = {
        TriageZone.MARGINAL_GAIN: TriageZone.CALCULATED_RISK,
        TriageZone.CALCULATED_RISK: TriageZone.LIKELY_WIN,
        TriageZone.LIKELY_WIN: TriageZone.LIKELY_WIN,
    }

    def __init__(
        self,
        likely_win_min_benefit: Decimal,
        likely_win_max_composite: int,
        calculated_risk_min_benefit: Decimal,
        calculated_risk_max_composite: int,
        handlungsdruck_elevation_threshold: int,
    ) -> None:
        self._lw_min = likely_win_min_benefit
        self._lw_max_c = likely_win_max_composite
        self._cr_min = calculated_risk_min_benefit
        self._cr_max_c = calculated_risk_max_composite
        self._hd_threshold = handlungsdruck_elevation_threshold

    def classify(
        self,
        expected_benefit_eur: Decimal,
        composite_score: int,
        handlungsdruck_score: int,
    ) -> ZoneResult:
        base = self._base_zone(expected_benefit_eur, composite_score)
        elevated, final = self._apply_handlungsdruck(base, handlungsdruck_score)
        reason = _build_reason(
            base=base, final=final, elevated=elevated,
            benefit=expected_benefit_eur, composite=composite_score,
            handlungsdruck=handlungsdruck_score,
        )
        return ZoneResult(base_zone=base, final_zone=final, handlungsdruck_elevated=elevated, reason=reason)

    def _base_zone(self, benefit: Decimal, composite: int) -> TriageZone:
        if benefit >= self._lw_min and composite <= self._lw_max_c:
            return TriageZone.LIKELY_WIN
        if benefit >= self._cr_min and composite <= self._cr_max_c:
            return TriageZone.CALCULATED_RISK
        return TriageZone.MARGINAL_GAIN

    def _apply_handlungsdruck(self, base: TriageZone, score: int) -> tuple[bool, TriageZone]:
        if score < self._hd_threshold:
            return False, base
        elevated = self._ELEVATION[base]
        return elevated != base, elevated


def _build_reason(base, final, elevated, benefit, composite, handlungsdruck) -> str:
    parts = [
        f"Erwarteter Nutzen: {benefit:,.0f} EUR.",
        f"Composite-Score: {composite}.",
        f"Basis-Zone: {base.value}.",
    ]
    if elevated:
        parts.append(
            f"Handlungsdruck {handlungsdruck}/5 → Zone hochgestuft: "
            f"{base.value} → {final.value}."
        )
    return " ".join(parts)


_DEFAULT_CONFIG_PATH: Path = (
    Path(__file__).parents[3] / "config" / "zone_thresholds.yaml"
)


def load_zone_classifier(config_path: Path = _DEFAULT_CONFIG_PATH) -> ZoneClassifier:
    with config_path.open(encoding="utf-8") as f:
        cfg: dict[str, Any] = yaml.safe_load(f)
    zone = cfg["zone"]
    hd = cfg["handlungsdruck"]
    return ZoneClassifier(
        likely_win_min_benefit=Decimal(str(zone["likely_win"]["min_expected_benefit_eur"])),
        likely_win_max_composite=int(zone["likely_win"]["max_composite_score"]),
        calculated_risk_min_benefit=Decimal(str(zone["calculated_risk"]["min_expected_benefit_eur"])),
        calculated_risk_max_composite=int(zone["calculated_risk"]["max_composite_score"]),
        handlungsdruck_elevation_threshold=int(hd["elevation_threshold"]),
    )
```

---

### src/aect/domain/feasibility.py

```python
"""Feasibility check for AECT use-case triage."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

_MIN_SITUATION_LEN: int = 50
_MIN_EXAMPLE_LEN: int = 30


class FeasibilityFlag(StrEnum):
    DESCRIPTION_TOO_VAGUE = "DESCRIPTION_TOO_VAGUE"
    MISSING_EXAMPLE = "MISSING_EXAMPLE"
    NO_TIME_SAVING = "NO_TIME_SAVING"
    NOT_RECURRING = "NOT_RECURRING"


@dataclass(frozen=True)
class FeasibilityResult:
    is_feasible: bool
    flags: tuple[FeasibilityFlag, ...]
    recommendation: str | None = None

    def has_flag(self, flag: FeasibilityFlag) -> bool:
        return flag in self.flags


class FeasibilityChecker:
    def check(
        self,
        current_situation: str,
        target_situation: str,
        example_process: str,
        time_saved_minutes_per_occurrence: Decimal,
        occurrences_per_month: int,
    ) -> FeasibilityResult:
        flags: list[FeasibilityFlag] = []
        if (
            len(current_situation.strip()) < _MIN_SITUATION_LEN
            or len(target_situation.strip()) < _MIN_SITUATION_LEN
        ):
            flags.append(FeasibilityFlag.DESCRIPTION_TOO_VAGUE)
        if len(example_process.strip()) < _MIN_EXAMPLE_LEN:
            flags.append(FeasibilityFlag.MISSING_EXAMPLE)
        if time_saved_minutes_per_occurrence <= Decimal("0"):
            flags.append(FeasibilityFlag.NO_TIME_SAVING)
        if occurrences_per_month <= 0:
            flags.append(FeasibilityFlag.NOT_RECURRING)
        is_feasible = len(flags) == 0
        return FeasibilityResult(
            is_feasible=is_feasible,
            flags=tuple(flags),
            recommendation=_build_recommendation(flags) if flags else None,
        )


def _build_recommendation(flags: list[FeasibilityFlag]) -> str:
    parts: list[str] = []
    if FeasibilityFlag.DESCRIPTION_TOO_VAGUE in flags:
        parts.append(f"Ist- und Soll-Zustand ausführlicher beschreiben (mind. {_MIN_SITUATION_LEN} Zeichen je Feld).")
    if FeasibilityFlag.MISSING_EXAMPLE in flags:
        parts.append("Konkreten Beispielvorgang ergänzen.")
    if FeasibilityFlag.NO_TIME_SAVING in flags:
        parts.append("Zeitersparnis pro Vorgang muss größer 0 sein.")
    if FeasibilityFlag.NOT_RECURRING in flags:
        parts.append("Vorgangshäufigkeit (pro Monat) muss angegeben und größer 0 sein.")
    return " ".join(parts)
```

---

### src/aect/py.typed

```
(empty marker file — PEP 561, signals typed package)
```

---

### config/roi_config.toml

```toml
# AECT ROI-Konfiguration — GENERISCHE PLATZHALTER
#
# IP-Trennung (vertraglich bedingt): KEINE echten Firmenwerte hier eintragen.
# Echte Stundensätze → config/roi_config.local.toml (gitignored)

[thresholds]
min_potential_eur        = 20000.0
min_hours_per_year       = 120.0
min_expected_benefit_eur = 5000.0

[hourly_rates.DE]
ASSOCIATE    = 45.0
PROFESSIONAL = 65.0
SENIOR       = 90.0
MANAGER      = 120.0

[hourly_rates.AT]
ASSOCIATE    = 42.0
PROFESSIONAL = 60.0
SENIOR       = 85.0
MANAGER      = 115.0

[hourly_rates.CH]
ASSOCIATE    = 55.0
PROFESSIONAL = 80.0
SENIOR       = 110.0
MANAGER      = 145.0

[evidence_factors]
LOW    = 0.50
MEDIUM = 0.75
HIGH   = 1.00

[adoption_factors]
NONE   = 0.10
LOW    = 0.30
MEDIUM = 0.60
HIGH   = 1.00
```

---

### config/zone_thresholds.yaml

```yaml
zone:
  likely_win:
    min_expected_benefit_eur: 50000.0
    max_composite_score: 4

  calculated_risk:
    min_expected_benefit_eur: 5000.0
    max_composite_score: 7

handlungsdruck:
  elevation_threshold: 4
```

---

### tests/conftest.py

```python
# tests/conftest.py
"""Shared pytest fixtures and configuration."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may be slow)"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
```

---

### tests/__init__.py

```python
"""Test suite for AECT."""
```

---

### tests/test_smoke.py

```python
# tests/test_smoke.py
"""Smoke tests — verifies the package is importable and structurally sound."""

import pytest

import aect


@pytest.mark.unit
def test_package_importable() -> None:
    assert aect is not None


@pytest.mark.unit
def test_version_is_string() -> None:
    assert isinstance(aect.__version__, str)
    assert len(aect.__version__) > 0


@pytest.mark.unit
def test_version_format() -> None:
    parts = aect.__version__.split(".")
    assert len(parts) == 3, f"Expected semver, got: {aect.__version__}"
    assert all(part.isdigit() for part in parts), (
        f"Non-numeric version part in: {aect.__version__}"
    )
```

---

### tests/domain/__init__.py

```
(empty)
```

---

### tests/domain/test_use_case_input.py

(vollständiger Inhalt — 143 Zeilen, enthält Klassen:
TestUseCaseInputValideEingaben, TestUseCaseInputValidierung,
TestUseCaseInputImmutability, TestUseCaseInputModelValidate)

Testanzahl: 13 Tests

---

### tests/domain/test_roi.py

(vollständiger Inhalt — 296 Zeilen, enthält:
- test_annual_hours_* (5 Tests)
- test_prefilter_* (5 Tests)
- test_theoretical_potential_calculation
- test_both_factors_applied_to_potential
- test_license_cost_subtracted_from_expected
- test_unknown_country_yields_zero_potential
- test_high_license_cost_can_make_net_negative
- test_invariant_expected_benefit_never_exceeds_potential [Hypothesis, 300 Beispiele])

Testanzahl: 11 Tests (+ 300 Hypothesis-Beispiele)

---

### tests/domain/test_filters.py

(vollständiger Inhalt — 109 Zeilen, enthält:
TestFilterResultInvarianten (3 Tests),
TestApplyPrefilter (9 Tests))

Testanzahl: 12 Tests

---

### tests/domain/test_scoring.py

(vollständiger Inhalt — 138 Zeilen, enthält:
TestCompositeScoreInvarianten (5 Tests),
TestEffortLabel (4 Tests),
TestComputeCompositeScore (8 Tests inkl. parametrize))

Testanzahl: 17 Tests

---

### tests/domain/test_zones.py

(vollständiger Inhalt — 188 Zeilen, enthält:
TestBaseZone (7 Tests),
TestHandlungsdruckElevation (6 Tests),
test_property_final_zone_gte_base_zone [Hypothesis, 300 Beispiele],
test_property_higher_benefit_same_or_better_base_zone [Hypothesis, 300 Beispiele],
test_load_zone_classifier_from_config)

Testanzahl: 15 Tests (+ 600 Hypothesis-Beispiele)

---

### tests/domain/test_feasibility.py

(vollständiger Inhalt — 188 Zeilen, enthält:
TestFeasibleCase (2 Tests),
TestIndividualFlags (7 Tests),
TestMultipleFlagsAndRecommendation (4 Tests))

Testanzahl: 13 Tests

---

## ABSCHNITT 5: Test-Ausgabe

### uv run pytest -v

```
FEHLER — pytest bricht beim Import ab:

Traceback (most recent call last):
  File ".venv/bin/pytest", line 4, in <module>
    from pytest import console_main
  File ".venv/lib/python3.12/site-packages/pytest/__init__.py", line 8, in <module>
    from _pytest._code import ExceptionInfo
  File ".venv/lib/python3.12/site-packages/_pytest/_code/__init__.py", line 5, in <module>
    from .code import Code
  File ".venv/lib/python3.12/site-packages/_pytest/_code/code.py", line 43, in <module>
    from _pytest._io import TerminalWriter
  File ".venv/lib/python3.12/site-packages/_pytest/_io/__init__.py", line 3, in <module>
    from .terminalwriter import get_terminal_width
  File ".venv/lib/python3.12/site-packages/_pytest/_io/terminalwriter.py", line 19, in <module>
    from ..compat import assert_never
  File ".venv/lib/python3.12/site-packages/_pytest/compat.py", line 19, in <module>
    import py
ModuleNotFoundError: No module named 'py'
```

**Status: Alle Tests NICHT ausführbar. pytest ist broken.**

### uv run pytest --cov=src/aect --cov-report=term-missing -q

```
(identischer Fehler wie oben)
ModuleNotFoundError: No module named 'py'
```

---

## ABSCHNITT 6: Import-Bug exakt dokumentiert

### uv run python -c "import aect; print(aect.__file__)"

```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'aect'
```

### uv run python -c "import sys; print('\n'.join(sys.path))"

```
/Users/01000101nes/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip
/Users/01000101nes/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12
/Users/01000101nes/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload
/Users/01000101nes/Desktop/Claude/ai-efficiency-control-tower/.venv/lib/python3.12/site-packages
```

**Beobachtung:** `src/` ist NICHT in sys.path — das `__editable__` .pth wird nicht wirksam.

### find .venv -name "*.pth"

```
.venv/lib/python3.12 2/site-packages/_virtualenv.pth
.venv/lib/python3.12 2/site-packages/__editable__.aect-0.1.0.pth
.venv/lib/python3.12 2/site-packages/a1_coverage.pth
.venv/lib/python3.12/site-packages/__editable__.aect-0.1.0.pth
```

**Beobachtung:** Zwei `.venv/lib/` Verzeichnisse:
- `.venv/lib/python3.12/` (normal, kein Leerzeichen) — von `uv run python` verwendet
- `.venv/lib/python3.12 2/` (mit Leerzeichen) — warum existiert dieses?

### cat .venv/lib/python3.12/site-packages/__editable__.aect-0.1.0.pth

```
/Users/01000101nes/Desktop/Claude/ai-efficiency-control-tower/src
```

**Beobachtung:** Inhalt korrekt, aber `src` erscheint NICHT in `sys.path`. Das `.pth` file wird nicht verarbeitet.

### cat .venv/lib/python3.12 2/site-packages/__editable__.aect-0.1.0.pth

```
/Users/01000101nes/Desktop/Claude/ai-efficiency-control-tower/src
```

### uv run python -c "import site; print(site.getusersitepackages())"

```
/Users/01000101nes/.local/lib/python3.12/site-packages
```

### uv run python -c "import site; print(site.ENABLE_USER_SITE)"

```
False
```

---

## ABSCHNITT 7: Coverage-Report

```
NICHT verfügbar — pytest bricht wegen `ModuleNotFoundError: No module named 'py'` ab.
Coverage kann nicht ermittelt werden.
```

---

## Zusammenfassung bekannter Bugs (Stand 2026-06-07)

### Bug 1: pytest nicht ausführbar — `No module named 'py'`

- **Ursache:** Das `py`-Paket fehlt in `.venv/lib/python3.12/site-packages/`.
- **Symptom:** `uv run pytest` bricht sofort beim Import von `pytest` ab.
- **Wahrscheinliche Ursache:** Inkompatible pytest-Version (>=9.0.3 laut pyproject.toml) oder korrupte venv-Installation.
- **Fix:** `uv add py` oder `uv sync --reinstall` oder pytest-Version prüfen.

### Bug 2: `import aect` schlägt fehl — `No module named 'aect'`

- **Ursache:** `src/` erscheint nicht in `sys.path`, obwohl `.pth`-Datei in `.venv/lib/python3.12/site-packages/` korrekt auf `src` zeigt.
- **Symptom:** `uv run python -c "import aect"` → `ModuleNotFoundError`.
- **Merkwürdigkeit:** Zwei Verzeichnisse `.venv/lib/python3.12/` und `.venv/lib/python3.12 2/` (mit Leerzeichen) — vermutlich durch macOS-Finder-Umbenennung oder doppelten `uv sync`-Lauf entstanden.
- **Fix:** `uv sync --reinstall` oder `.venv` löschen und neu aufbauen.

### Bug 3: `calculate_roi()` — NotImplementedError

- **Ort:** `src/aect/domain/roi.py:271`
- **Status:** Absichtlich — Adapter-Implementierung wurde als TODO markiert.
- **Details:** `_calculate_roi_values()` ist fertig und getestet; nur der Wrapper `calculate_roi(input, config)` fehlt noch (Feldnamen-Mapping UseCaseInput → _calculate_roi_values).

### Enum-Mismatch-Risiko (noch nicht getestet)

- **roi.py** `_FREQUENCY_TO_ANNUAL` Keys: `"DAILY"`, `"WEEKLY"`, `"MONTHLY"` etc. (UPPERCASE)
- **types.py** `FrequencyUnit` Werte: `"daily"`, `"weekly"`, `"monthly"` (lowercase StrEnum)
- **roi_config.toml** `[hourly_rates.DE]` Keys: `ASSOCIATE`, `PROFESSIONAL`, `SENIOR`, `MANAGER`
- **types.py** `EmployeeCategory` Werte: `"junior"`, `"professional"`, `"senior"`, `"mixed"` (lowercase)
- **roi_config.toml** `[evidence_factors]` Keys: `LOW`, `MEDIUM`, `HIGH`
- **types.py** `EvidenceLevel` Werte: `"pure_estimate"`, `"similar_project"`, `"tested_piloted"`
- **Fazit:** Keys in TOML und `_FREQUENCY_TO_ANNUAL` stimmen NICHT mit StrEnum-Werten überein. Dies wird beim Verbinden von `calculate_roi()` zu Laufzeitfehlern führen.

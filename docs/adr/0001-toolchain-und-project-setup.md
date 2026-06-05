# ADR-0001: Python-Toolchain und Projekt-Setup

**Status:** Accepted
**Datum:** 2026-06-05
**Autor:** Anas

## Kontext

AECT ist ein privates Karriere-Portfolio-Projekt für einen AI-Engineer-Pfad im
DACH-Markt. Die Toolchain muss drei Dinge leisten: (1) Development Experience schnell
halten, (2) Code-Qualität erzwingen ohne manuelle Disziplin, (3) CI-fähig sein ohne
komplexen Setup-Prozess.

Das Projekt nutzt Python 3.12 mit einem modernen src-Layout (`src/aect/`).

## Entscheidung

Wir verwenden folgende Toolchain:

| Rolle | Tool |
|---|---|
| Package Manager | `uv` (Astral) |
| Build-Backend | `hatchling` via `pyproject.toml` |
| Linter + Formatter | `ruff` (strict) |
| Type Checker | `mypy` (strict) |
| Testing | `pytest` + `pytest-cov` |
| Pre-Commit | 10 Hooks; mypy als `local` Hook via `uv run mypy src/` |
| Python Version | 3.12 |
| Lock File | `uv.lock` (committed) |

## Begründung

**uv statt pip/poetry/pip-tools:** Signifikant schneller bei Dependency-Resolution und
Lock-File-Management. `uv sync --frozen` in CI ist deterministisch und schnell.
`uv.lock` wird committed — kein „works on my machine".

**ruff statt black + isort + flake8:** Ein Tool ersetzt drei. Kompatibel mit
Black-Formatierung. Signifikant schneller als pylint, weniger Konfigurationsaufwand.

**mypy strict statt kein Typecheck:** In einem System das Pydantic V2-Schemas,
LLM-Outputs und eine deterministische Regel-Engine kombiniert, findet strict typing
echte Bugs vor Laufzeit. Der Annotations-Overhead amortisiert sich ab dem ersten
Pydantic-Schema.

**mypy als `local` Hook (nicht `mirrors-mypy`):** Benötigt Zugriff auf das virtuelle
Environment für Third-Party-Stubs (pydantic, fastapi). `uv run mypy src/` löst das
ohne globale Installation. `py.typed` Marker in `src/aect/` ist dafür Pflicht.

| Alternative | Warum verworfen |
|---|---|
| poetry | Langsamer als uv; kein nennenswerter Vorteil für dieses Projekt |
| black + isort + flake8 | Drei Tools für eine Funktion; ruff leistet dasselbe mit weniger Konfiguration |
| pylint | Sehr verbose, langsam, konfigurationsintensiv |
| mypy ohne strict | Halbe Type Safety — der Overhead von strict lohnt sich ab dem ersten Pydantic-Schema |
| mirrors-mypy als Hook | Kein Zugriff auf venv-Stubs; falsche Negativmeldungen für pydantic/fastapi |

## Konsequenzen

**Positiv:**
- CI-Setup minimal: `uv sync --frozen` + `uv run pre-commit run --all-files`
- Commits blockiert bis ruff + mypy + pytest grün
- Lock-File garantiert reproduzierbare Builds in CI und auf anderen Maschinen

**Negativ / Trade-offs:**
- mypy strict bedeutet mehr Annotation-Arbeit zu Beginn
- `uv` ist neueres Tooling; bei unbekannten Bugs → Fallback auf pip möglich, aber bisher
  nicht notwendig

**Neutral:**
- `py.typed` Marker in `src/aect/` ist Pflicht für mypy in CI (bereits vorhanden)
- Pre-Commit-Reihenfolge ist nicht verhandelbar: `uv run pre-commit run --all-files`
  → `git add -A` → `git commit`. Nie umgekehrt.

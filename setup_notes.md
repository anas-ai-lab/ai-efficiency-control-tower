# Setup Notes

## Project

Project name: AI Efficiency Control Tower
Project focus: AI Use Case Intake & Triage Assistant
Project folder: `~/Desktop/Claude/ai-efficiency-control-tower`
Resolved path: `/Users/01000101nes/Desktop/Claude/ai-efficiency-control-tower`
Editor: VS Code
Operating system: macOS

## Day 2 Goal

Set up VS Code as the main working environment for the AI Engineering learning plan.

## Installed VS Code Extensions

- Python
- Pylance
- GitLens
- Markdown All in One
- Error Lens

## Terminal Checks

Run these commands in the VS Code terminal:

```bash
pwd
python3 --version
git --version
```

## Results

* Project folder opened in VS Code: yes
* Integrated terminal works: yes
* Python available in terminal: yes
* Git available in terminal: yes
* Python interpreter selected in VS Code: yes

## Notes

This project uses VS Code as the default IDE. IntelliJ is not used for this learning plan unless explicitly needed later.

## Next Step

Day 3: Create or connect the GitHub repository for `ai-efficiency-control-tower`.

## Day 3 Status

- GitHub repository created: yes
- Remote connected: yes
- First commit pushed: yes

## Day 4 Status

- Project folder structure created: yes
- .gitkeep files in all folders: yes
- .gitignore updated with ChromaDB and coverage entries: yes
- Committed and pushed: yes

## Next Step

Day 5: Write README v0 with problem statement, goal, and non-goals.

## Pre-commit Hooks (Tag 11)

### Setup

```bash
uv add --dev pre-commit
uv run pre-commit install
uv run pre-commit autoupdate
```

### Aktive Hooks

| Hook | Zweck |
|---|---|
| ruff | Linting mit auto-fix |
| ruff-format | Code-Formatierung |
| mypy | Type-Checking (strict, via local venv) |
| end-of-file-fixer | Newline am Dateiende |
| trailing-whitespace | Keine Leerzeichen am Zeilenende |
| check-yaml | YAML-Syntax |
| check-json | JSON-Syntax |
| check-toml | TOML-Syntax |
| debug-statements | Kein versehentliches `breakpoint()` |
| check-merge-conflict | Keine Merge-Marker |

### Wichtig: mypy läuft via `local` repo

Grund: mirrors-mypy kennt Projekt-Dependencies nicht → falsche Fehler.
Lösung: `uv run mypy src/` nutzt lokale venv mit allen installierten Packages.

### Manuelle Nutzung

```bash
# Alle Dateien prüfen
uv run pre-commit run --all-files

# Nur einen Hook
uv run pre-commit run mypy

# Versions aktualisieren
uv run pre-commit autoupdate
```

### Bekannte Edge Cases

- Nach `uv add` neuer Packages: `uv sync` dann `pre-commit run mypy`
- Bei CI: `pre-commit run --all-files` im ci.yml (Tag 12)

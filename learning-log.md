# Learning Log

## Day 1 – Project Setup

### What I did

- Created the project repository.
- Created the base folder structure.
- Added initial documentation files.
- Added `.gitignore`.
- Added Claude Code project context.
- Added Obsidian-compatible note structure.

### What I understood

- This project will be built incrementally.
- Day 1 is only about structure, not features.
- A clean repository is the foundation for all later implementation work.
- Obsidian is used as a Markdown knowledge base.
- Claude Code should use short routing files instead of loading all notes.

### What exists now

- `README.md`
- `CLAUDE.md`
- `learning-log.md`
- `architecture.md`
- `.gitignore`
- `notes/index.md`
- `notes/daily/2026-05-05-day-01.md`
- Base project folders

### Open questions

- None.

---

## Tag 2 – VS Code Setup

**Datum:** 2026-05-06
**Phase:** Phase 0 – Setup, Arbeitsweise und Projektidentität
**Woche:** Woche 1
**Fokus:** VS Code Setup und lokale Arbeitsumgebung

### Was ich heute gemacht habe

- Bestehenden Projektordner in VS Code geöffnet.
- VS Code als Standard-IDE für den Lernplan bestätigt.
- Integriertes VS-Code-Terminal verwendet.
- Projektpfad geprüft.
- Python im Terminal geprüft.
- Git im Terminal geprüft.
- `setup_notes.md` erstellt.
- Setup-Ergebnisse dokumentiert.
- Erste Git-Änderung für das Setup vorbereitet bzw. committed.

### Sichtbarer Output

- `setup_notes.md`
- Aktualisierter Projektstatus im Lernlog
- Funktionierendes VS-Code-Terminal
- Verifizierte Python- und Git-Installation

### Wichtige Erkenntnis

Markdown-Inhalte gehören in `.md`-Dateien. Terminal-Befehle gehören ins Terminal.

### Technischer Check

- Projektordner korrekt geöffnet: ja
- Terminal im richtigen Projektpfad: ja
- Python verfügbar: ja
- Git verfügbar: ja
- VS Code als Haupteditor gesetzt: ja

### Offene Punkte

- GitHub-Repo an Tag 3 prüfen oder verbinden.
- Sicherstellen, dass der Arbeitsbaum sauber ist.

### Nächster Schritt

An Tag 3 wird das GitHub-Repository `ai-efficiency-control-tower` erstellt oder mit dem bestehenden lokalen Projekt verbunden.

---

## Tag 3 – GitHub Repo Setup

**Datum:** 2026-05-07
**Phase:** Phase 0 – Setup, Arbeitsweise und Projektidentität
**Woche:** Woche 1
**Fokus:** Git-Initialisierung, GitHub-Verbindung, erster Push

### Was ich heute gemacht habe

- Git Remote zu GitHub verknüpft.
- Authentifizierung mit Personal Access Token gelöst.
- 32 Objekte erfolgreich nach GitHub gepusht.
- README auf echten Projektfokus korrigiert.
- Repo auf public gestellt.
- `.gitignore` vor dem public Stellen geprüft.

### Sichtbarer Output

- Öffentliches GitHub Repo `ai-efficiency-control-tower` live.
- Erster Commit auf GitHub sichtbar.
- `README.md` mit korrektem Projektfokus.

### Wichtige Erkenntnisse

- `git init` auf bestehendem Repo ist harmlos – initialisiert nur neu ohne Datenverlust.
- GitHub akzeptiert kein Passwort mehr über HTTPS → Personal Access Token ist Pflicht.
- `git remote remove` / `git remote add` für Fehlerkorrektur bei falsch gesetztem Remote.
- `.gitignore` muss vor dem public Stellen sauber sein – Secrets dürfen nie ins Repo.
- README ist das Erste, was Recruiter und Tech Leads sehen. Falscher Fokus beschädigt das Portfolio.

### Fehler und Korrekturen

- README beschrieb ursprünglich ein anderes Projekt. Früh korrigiert – verhindert, dass sich ein Fehler über Wochen aufbaut.

### Technischer Check

- Git lokal initialisiert: ja
- Remote `origin` korrekt gesetzt: ja
- Erster Push erfolgreich: ja
- Repo public: ja
- README Fokus korrekt: ja

### Offene Punkte

- Keine.

### Nächster Schritt

An Tag 4 wird die vollständige Projektordnerstruktur angelegt: `src/`, `tests/`, `docs/`, `prompts/`, `evals/`, `workflows/`.

---

## Tag 04 – 2026-05-06

**Fokus:** Projektstruktur vervollständigen
**Output:** Vollständige Ordnerstruktur, .gitignore mit ChromaDB/Coverage-Einträgen
**Wichtigste Erkenntnis:** Leere Ordner brauchen `.gitkeep`. .gitignore vor dem ersten echten Code sauber aufsetzen spart spätere Fehler.
**Status:** ✅ Abgeschlossen

---

## Tag 05 – 2026-05-06

**Fokus:** README v0
**Output:** README auf korrekten Projektfokus umgestellt
**Wichtigste Erkenntnis:** README ist das erste was Recruiter und Tech Leads sehen. Problem Statement, Ziel und Nicht-Ziele fehlen noch.
**Status:** ⚠️ Teilweise – Catch-up an Tag 06

## Tag 6 — AI Decision Framework & Matrix (2026-05-07)

**Fokus:** Konzeptioneller Kern des Triage-Systems — wann AI, wann nicht.

**Was wirklich gelernt wurde:**
- DSGVO Art. 22 ist enger als gedacht: greift nur bei rein automatisierten Entscheidungen mit erheblicher Wirkung auf Personen. „Personenbezug" allein reicht nicht.
- EU AI Act ist kein theoretisches Zukunftsprojekt: Recruiting-AI ist heute bereits Hochrisiko (Annex III), Bußgelder bis €35M, Pflichten ab August 2026.
- Classical ML existiert als Kategorie zwischen Regel und LLM — strukturierte Zeitreihendaten (Anomalie, Fraud) gehören dort hin, nicht zu LLM.
- Business Value ist nur dann vor einem Internes Gremium verteidigbar wenn er berechnet ist, nicht geschätzt. Formel: Zeitersparnis × Volumen × Stundensatz × Evidenzfaktor × Adoptionsfaktor.
- Ein RAG-System auf veralteter oder inkonsistenter Wissensbasis produziert schlechtere Outputs als gar kein RAG. KB-Qualität ist Voraussetzung, nicht Nachgedanke.

**Engineering-Relevanz:**
- Diese Kriterien werden direkt zu `domain/triage_engine.py` (Woche 5) und `domain/ai_vs_automation.py` (Woche 6).
- Der Business-Value-Score wird als `computed_field` in Pydantic V2 abgebildet.

### Tag 7 — Wochenabschluss

- architecture.md: Systemskizze mit Mermaid-Diagramm fertiggestellt
- Prozessfluss macht Architekturentscheidungen sichtbar:
  regelbasierter Kern, LLM optional, Human Review bei high risk
- Woche 1 vollständig dokumentiert und committed
- Erkenntnis: Dokumentation ist kein Anhang — sie zwingt zu
  klarerem Denken über Systemgrenzen

---

## Woche 1 — Review (Tag 1–7)

**Datum:** 2026-05-07

### Was in Woche 1 wirklich abgeschlossen wurde
- Repo-Struktur: vollständig angelegt
- README v0: vorhanden
- .gitignore: solide
- docs/ai-decision-framework.md v2: vollständig
- docs/ai_vs_automation_matrix.md v2: vollständig
- docs/architecture.md: 1-Seiten-Skizze mit Mermaid
- Daily Notes Tag 1–6: vorhanden
- learning-log.md: laufend gepflegt

### Was zu trivial war (kein Engineering-Substanz)
- Passt bisher

### Was echte Engineering-Substanz hatte
- ai-decision-framework.md: Zwang zur Formalisierung von Entscheidungslogik
- architecture.md: erstes Systemdenken, Komponentengrenzen definiert

### Wichtigste Erkenntnis der Woche
- Noch keine

### Was ab Woche 2 anders sein muss
- Weniger Setup, mehr Code
- Jeder Tag liefert ein Code-Artefakt
- Engineering-Disziplin von Tag 1: ruff, mypy, pytest

### Selbstbewertung Woche 1
- Pace: 6
- Output-Qualität: 7
- Fokus: 5

## Woche 2 — Tag 8 (2026-05-08)

### Thema
uv, pyproject.toml, src-Layout, Python 3.12 Projekt-Setup

### Was ich gebaut habe
Projektfundament mit uv als Package Manager: pyproject.toml mit
src-Layout, zwei Dependency-Groups (dev/test), Python 3.12 gepinnt,
Package-Struktur `src/aect/` aufgesetzt, uv sync erfolgreich.

### Was ich heute noch nicht verstanden habe
- Das Zusammenspiel von uv / pip / venv / pyproject.toml
- Warum src-Layout (nicht direkt im Root)
- Was dependency-groups vs. requirements.txt bringt
- Was hatchling ist und warum build-backend

### Was ich das nächste Mal nachschlagen will
- uv Dokumentation: https://docs.astral.sh/uv/
- Python Packaging Guide (pyproject.toml): https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

### Engineering-Erkenntnis
Ein einziges `uv sync` nach dem Klonen reicht — keine manuelle
venv-Erstellung, keine requirements.txt pflegen, exakt reproduzierbar.
Das ist der Unterschied zwischen Tutorial-Code und einem echten Repo.

### Offene Fragen
- Wann brauche ich `uv add` vs. direkt in pyproject.toml eintragen?
- Was passiert wenn jemand ohne uv am Projekt arbeiten will?

---

## Woche 2 — Tag 09 (2026-05-08)

**Thema:** Ruff + mypy strict Konfiguration

**Erledigt:**
- ruff installiert und konfiguriert (strict ruleset)
- mypy.ini mit strict mode angelegt
- Makefile mit make check
- make check läuft grün

**Ehrliche Einschätzung:**
Tooling mechanisch eingerichtet, aber inhaltliches Verständnis fehlt.
Die Konfigurationsoptionen wurden kopiert, nicht verstanden.
Das ist ein echtes Problem — wer mypy.ini nicht lesen kann,
kann Fehlerausgaben nicht interpretieren und Optionen nicht bewusst anpassen.

**Offene Lücken:**
- ruff Regelcodes: was prüft E, F, B, UP, SIM, RUF konkret?
- mypy strict: was kommt zu default dazu?
- no_implicit_reexport: was bedeutet das praktisch?
- warn_return_any: wann schlägt das an?

**Aktion für Tag 10:**
Vor pytest: 15 Min Lektüre ruff-Doku (Regelübersicht) + mypy strict-Changelog.
Ziel: Ich kann die 5 Fragen oben beantworten ohne nachzuschauen.

## Tag 10 — 2026-05-08

**Thema:** pytest-Konfiguration, Smoke Tests, Coverage

**Was ich heute wirklich gelernt habe:**

TOML erlaubt keine doppelten Sektions-Keys. Wenn `[tool.pytest.ini_options]`
zweimal in `pyproject.toml` steht, bricht das gesamte Tool-Ökosystem
(uv, mypy, ruff) mit einem Parse-Error ab — nicht nur pytest selbst.
Lesson: Vor dem Einfügen neuer Sektionen immer prüfen ob sie schon existieren.

Die `--strict-markers`-Option in pytest ist bewusst gesetzt: Sie erzwingt,
dass jeder verwendete Marker in `conftest.py` registriert ist. Das verhindert
Tipp-Fehler in Marker-Namen die sonst still ignoriert würden.

`branch = true` in Coverage bedeutet: nicht nur Zeilen werden gezählt,
sondern auch ob beide Zweige eines `if`-Statements getestet wurden.
Das ist strenger und sinnvoller für echte Qualitätsmessung.

**Was trivial war:**
Die 3 Smoke-Tests selbst — aber sie sind nicht wegen ihrer Komplexität
wertvoll, sondern weil sie beweisen dass das Package-Setup korrekt ist.
Ein grüner Smoke-Test nach frischem Clone ist ein echtes Signal.

**Was Engineering-Substanz hatte:**
Die `pyproject.toml`-Bereinigung. Zu verstehen warum TOML-Duplikate
das gesamte Tool-Ökosystem betreffen (nicht nur ein Tool) ist wichtig
für jedes Python-Projekt das `pyproject.toml` als Single Source of Truth nutzt.

**Offene Fragen:**
- Wann macht `fail_under > 0`

## Tag 11 — Pre-commit Hooks (2026-05-08)

**Thema:** Code Quality Enforcement — pre-commit

**Was neu war:**
- mypy als `local` Hook konfigurieren: entscheidend damit mypy Projekt-Dependencies kennt
- pre-commit Commit-Verhalten: Hook modifiziert Datei → Commit bricht ab →
  das ist kein Fehler, sondern Schutzverhalten. Fix: `git add -A` + erneut committen
- `autoupdate` für deprecated stage names

**Was bestätigt wurde:**
- Hooks laufen nur auf gestagten Dateien bei Commits (korrekt)
- `--all-files` für manuellen vollständigen Run

**Technische Entscheidung:**
mypy via `local` repo statt `mirrors-mypy` — notiert in `setup_notes.md`

**Output:** `.pre-commit-config.yaml` aktiv, Repo sauber, CI-Vorbereitung abgeschlossen

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
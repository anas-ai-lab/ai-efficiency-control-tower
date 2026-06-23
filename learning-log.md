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

## Tag 12 — 2026-06-05 — GitHub Actions CI + Security Scanning

### Was neu war

**Node-24-Transition ist live.** GitHub hat am 2. Juni 2026 auf Node 24
umgestellt. Das bedeutet konkret: `actions/checkout@v4` und
`gitleaks-action@v2` laufen mit Deprecation-Warnings oder brechen bald.
Wer heute eine neue CI aufsetzt, muss `@v6` / `@v3` verwenden.

**SHA-Pinning in der Praxis.** `git ls-remote <repo> refs/tags/<tag>`
gibt den Commit-SHA einer Action zurück. Das ist die einzige sichere
Methode — Tags sind mutable, ein kompromittierter Maintainer kann `@v4`
auf bösartigen Code umzeigen ohne dass der Consumer es merkt.

**pip-audit findet echte CVEs.** Heute an Tag 1: `idna 3.13` mit
CVE-2026-45409, Fix in 3.15. Nicht hypothetisch, nicht ein Test —
ein realer CVE in einer Dependency, die über requests transitiv
reingekommen ist. `uv add "idna>=3.15"` hat es in einem Befehl gefixt.

**macOS vs GNU Coreutils.** `head -n -3` funktioniert auf macOS nicht
(BSD head, kein negatives Zeilenargument). macOS-kompatibler Weg:
`sed -i '' 'X,$d' file` für "ab Zeile X alles löschen".

**GitHub Free Plan + Branch Protection auf privaten Repos.** Status-
Checks als Merge-Gate sind auf private Repos ohne Team-Plan nicht
durchsetzbar. Das ist eine Bezahlschranke, kein Konfigurationsfehler.
Für Solo-Builds ohne PRs nicht relevant — die CI läuft trotzdem.

**PAT braucht `workflow` Scope für `.github/workflows/`.** GitHub
verweigert Pushes in das workflows-Verzeichnis ohne diesen Scope,
auch wenn `repo` vorhanden ist.

### Was noch unklar ist / offen

- `mypy.ini` Zeile 16: Parse-Fehler `']\n'`. mypy läuft durch aber
  ignoriert die ini. Müssen prüfen ob strict-Einstellungen tatsächlich
  aktiv sind oder ob mypy mit Defaults läuft.

### Pattern

Security-Scanning in CI von Anfang an — nicht als Audit nachträglich.
pip-audit hat heute bewiesen warum: reale CVEs kommen über transitive
Dependencies, nicht über direkte Imports.

## Tag 13 — 2026-06-05

### Was sind ADRs und warum schreibt man sie?

ADR steht für Architecture Decision Record — ein kurzes Dokument, das festhält,
warum eine technische Entscheidung so getroffen wurde wie sie getroffen wurde.
Nicht nur was entschieden wurde, sondern: welches Problem war vorher da, welche
Alternativen wurden erwogen, und warum wurden sie verworfen.

Der Grund dafür ist praktisch: In drei Monaten weiß man nicht mehr, warum man
damals Azure OpenAI statt einem anderen Anbieter genommen hat. Im Interview weiß
man es auch nicht, wenn man es nie aufgeschrieben hat. ADRs machen aus einem
Zufallsergebnis eine verteidigbare Entscheidung.

Heute entstanden drei: eine für die Toolchain (warum uv, ruff, mypy), eine für die
Architektur (warum Hexagonal), eine für den LLM-Ansatz (warum Azure, warum Mock-First).
Jede hat eine Tabelle mit verworfenen Alternativen — das ist der wichtigste Teil.

### Was heute mit pre-commit passiert ist — und warum es normal ist

pre-commit lief heute zweimal und schlug beide Male fehl. Das klingt nach einem Problem,
ist aber das korrekte Verhalten.

Was passiert ist: Die ADR-Dateien fehlten am Ende ein Zeilenumbruch (`end-of-file-fixer`)
und hatten trailing whitespace (Leerzeichen am Zeilenende). pre-commit hat beides
automatisch korrigiert — aber damit hat es die Dateien verändert, während sie schon
für den Commit vorgemerkt waren.

Das führt zu einem scheinbar widersprüchlichen git-Status: die Datei erscheint
gleichzeitig als "staged" (alte Version, vorgemerkt) und "unstaged" (neue Version,
von pre-commit korrigiert). Der Commit schlägt fehl weil git nur die ursprüngliche,
noch nicht bereinigte Version committen würde.

Lösung: `git add -A` auf den aktuellen Stand (die von pre-commit bereinigten Dateien),
dann erst committen. Beim zweiten Anlauf findet pre-commit nichts mehr zu fixen.

Das ist kein Fehler im Setup — es ist die Absicht. pre-commit ist ein Qualitätsfilter,
der Probleme automatisch behebt statt sie durchzulassen. Der Preis dafür ist ein
zweistufiger Workflow wenn Hooks Dateien anfassen.

**Konsequenz für das Projekt:** In jedem Tagesabschluss-Commit: wenn pre-commit
Dateien modifiziert hat, immer nochmal `git add -A` bevor `git commit`.
Das ist keine Ausnahme — das ist der Normalfall.

### Was der "modified: Makefile" in git status bedeutet

git status zeigte heute "modified: Makefile" statt "new file: Makefile". Das bedeutet:
die Datei existierte bereits im Repository. Tag 12 (GitHub Actions CI) war also
tatsächlich schon erledigt — der Tracker-Hinweis "planned, not executed" war zu
pessimistisch. `git log` und `git ls-files` sind die einzige verlässliche Quelle
für den echten Projekt-Stand — nicht Notizen, nicht Erinnerungen.

### Was als nächstes kommt

Tag 14 startet Phase A: die Domain-Schicht und die Regel-Engine. Das ist der
wertvollste Teil des Projekts — das Bewertungsmodell deterministisch in Code übersetzen.
Vor dem ersten Phase-A-Guide gibt es einen Pflicht-Check: `git ls-files src/` und
`uv run pytest -q`. Erst wenn der Stand verifiziert ist, kommt der Guide.

## 2026-06-05 — Day 14: Pydantic V2 Input-Schema, TDD, StrEnum

### Was ist Pydantic V2 und warum extra="forbid"?

Pydantic ist eine Python-Library die Datenvalidierung über normale
Python-Klassen macht. Du definierst Felder mit Typen und Regeln —
Pydantic prüft bei der Erstellung ob die Daten passen, und wirft einen
ValidationError wenn nicht.

`extra="forbid"` ist ein Security-Setting: wenn ein JSON-Payload Felder
enthält die das Schema nicht kennt, schlägt die Validierung fehl statt
die Felder still zu ignorieren. Das klingt pingelig — ist es aber nicht.
Ein Angreifer könnte versuchen, über unbekannte Felder Daten ins System
zu schleusen die am Ende ins LLM wandern. `extra="forbid"` schneidet
das am Eingang ab (OWASP LLM10: Unbounded Consumption).

### Was ist `max_length` bei Textfeldern?

Token-Flooding: wenn jemand ein Textfeld mit 50.000 Zeichen befüllt
und dieser Text ans LLM geht, kostet das Geld und verlangsamt das
System. `max_length=2000` setzt eine harte Grenze. Das ist kein UX-
Feature — es ist Budget-Schutz und Security.

### Was ist `StrEnum`?

Vor Python 3.11: `class MyEnum(str, Enum)` — zwei Basisklassen, der
String-Aspekt musste explizit hinzugefügt werden.
Ab Python 3.11: `class MyEnum(StrEnum)` — eingebaut, sauberer.

Der Unterschied im Verhalten: beide erzeugen Enum-Werte die gleichzeitig
Strings sind (`EvidenceQuality.ESTIMATE == "estimate"` ist True). Der
Unterschied ist nur Schreibweise und Modernität. Ruff flaggt die alte Form
mit UP042 — ein Hinweis dass der Code auf eine neuere Python-Version
aktualisiert werden kann.

### Was ist TDD in der Praxis hier?

Test-Driven Development heißt: zuerst einen Test schreiben der beschreibt
was der Code können soll, dann den Code so schreiben dass der Test grün
wird. Der Vorteil: man denkt über das Interface nach bevor man die
Implementation baut. Heute: Tests haben zuerst mit ImportError versagt
(Model existierte nicht), dann mit ValidationError-Erwartungen die noch
nicht erfüllt waren — dann Schritt für Schritt das Schema gebaut bis
alle 9 Tests grün waren.

## Tag 15 — 2026-06-05 | Pydantic V2 Domain-Modell

### Was gebaut wurde

Das Eingabemodell für eine Use-Case-Einreichung. Stell es dir wie ein
ausgefülltes Formular vor: Wer reicht ein, welcher Prozess soll automatisiert
werden, wie viel Zeit spart das pro Vorgang, wie oft passiert das pro Jahr,
werden persönliche Daten verarbeitet? Das Modell prüft jede Antwort auf
Plausibilität — bevor irgendetwas berechnet wird.

### Was Pydantic V2 hier konkret macht

Pydantic ist eine Python-Library, die Datenstrukturen validiert. Wenn ein
Formular-Feld sagt "Zeitersparnis: -5 Stunden", wirft Pydantic einen Fehler —
bevor das in die Berechnung geht. Das ist kein manueller if-else-Code, sondern
deklarativ: ich beschreibe welche Felder erlaubt sind und welche Grenzen gelten,
Pydantic erzwingt das automatisch.

Drei konkrete Einstellungen die heute wichtig waren:

**`extra="forbid"`:** Wenn jemand ein Feld schickt, das im Schema nicht
existiert, wird die Anfrage abgelehnt. Schutz: in Phase C werden diese Felder
an ein KI-Modell weitergegeben. Ohne diese Regel könnte ein Angreifer beliebige
Texte einschleusen und den Verbrauch explodieren lassen (Token-Flooding).

**`frozen=True`:** Nach der Erstellung kann das Objekt nicht mehr verändert
werden. Grund: Das Eingabe-Objekt repräsentiert was eingereicht wurde. Was das
System daraus berechnet (ROI, Risiko-Zone), kommt in ein separates
Ergebnis-Objekt. Würde man das Eingabe-Objekt mit Berechnungen befüllen,
vermischt man zwei verschiedene Konzepte — schwer zu testen, schwer zu warten.

**`max_length` auf Freitextfeldern:** Jedes Beschreibungsfeld hat ein Zeichen-
Limit. In Phase C (LLM-Integration) werden diese Texte an Azure OpenAI
geschickt — jedes Zeichen kostet Geld und Zeit. Ohne Limit könnte eine
50.000-Zeichen-Beschreibung den Betrieb zum Stillstand bringen.

### Was heute schiefgelaufen ist (und was ich daraus mitgenommen habe)

Drei separate Probleme hintereinander: Namenskonflikt zwischen `EvidenceQuality`
(alter Name) und `EvidenceLevel` (neuer Name), korruptes Python-Environment
durch eine doppelte Installations-Datei, und ein Unicode-Zeichen (`×`) das ruff
nicht akzeptiert.

Das wichtigste Muster: Wenn etwas nicht importiert werden kann, zuerst das
Environment prüfen — nicht sofort den Code. Der Code war korrekt, das
Environment war kaputt.

### Warum das für AECT wichtig ist

`UseCaseInput` ist das Eingangstor des gesamten Systems. Was dieses Modell
nicht akzeptiert, kommt nie in die Rule Engine, nie in den LLM-Call, nie in
den Report. Jede Validierungsregel hier spart Debugging-Zeit in allen
späteren Phasen.

### Offene Frage (vor Tag 16 zu beantworten)

Was ist der konkrete Unterschied zwischen `UseCaseInput.model_validate(dict)`
und `UseCaseInput(**dict)` in Pydantic V2 — und wann schlägt eines fehl,
obwohl das andere durchgeht?

## Tag 16 — 06.06.2026

### ROI-Engine: Warum eine Berechnung "pure" sein sollte

Eine "pure function" klingt technisch, ist aber eine einfache Idee: gleiche
Eingaben → immer gleiche Ausgabe, ohne versteckte Abhängigkeiten. Die
ROI-Berechnung ist so gebaut — sie braucht weder eine Datenbankverbindung
noch einen globalen Zustand, nur die Zahlen die man ihr gibt. Warum wichtig?
Weil man sie dann in Tests beliebig oft mit beliebigen Werten aufrufen kann,
ohne Setup-Overhead. Und weil sie deterministisch ist: kein "manchmal passt
das Ergebnis, manchmal nicht".

### property-based Testing: Eigenschaften statt Beispiele prüfen

Klassische Tests prüfen konkrete Fälle: "bei diesen Eingaben erwarte ich
genau diesen Wert." property-based Tests prüfen eine mathematische Eigenschaft
für alle möglichen Eingaben: "egal welche Faktoren zwischen 0 und 1 ich wähle,
der erwartete Nutzen darf das theoretische Potenzial nie übersteigen."

Das Werkzeug `hypothesis` generiert automatisch hunderte Kombinationen und
sucht aktiv nach Gegenbeispielen. Der Vorteil: man prüft nicht nur die Fälle,
an die man beim Schreiben gedacht hat, sondern systematisch den Rand des
Möglichen. Invarianten wie "Nutzen ≤ Potenzial" sind exakt die Art von
Regel, die in komplexen Berechnungen schleichend gebrochen werden kann.

### IP-Trennung durch Config-Injektion

Die Stundensätze in diesem Projekt sind firmeneigene Zahlen — sie dürfen
nicht in ein öffentliches Repo. Die Lösung ist architektonisch: `ROIConfig`
ist ein unveränderliches Objekt, das von außen befüllt wird. Die Berechnung
selbst enthält keine Zahlen, nur die Formel. Echte Werte kommen aus einer
gitignorierten lokalen Datei, Platzhalter aus einer committed generischen
Datei.

Das ist kein Disziplin-Merkmal ("man sollte das so machen") sondern eine
Architektur-Eigenschaft: wer keine Config übergibt, kann die Funktion nicht
aufrufen. Der Fehler ist strukturell unmöglich, nicht nur unwahrscheinlich.

### Was das hatchling/uv-Problem zeigt

Das Build-Backend (das Werkzeug, das Python-Pakete für die Entwicklungsumgebung
installierbar macht) hat einen stillen Fehler produziert: `uv run pytest`
lief grün, `uv run python` schlug fehl. Das war möglich, weil pytest eine
eigene Pfad-Einstellung hatte, die den Fehler maskierte. Fazit: ein Testlauf
allein ist kein Beweis, dass das Paket korrekt installiert ist. Nach jedem
Package-Manager-Lauf (uv sync, uv add) den Import auch direkt prüfen,
nicht nur über pytest.

Das Build-Backend wurde auf setuptools gewechselt — weniger modern als
hatchling, aber in dieser Kombination zuverlässiger. Für ein Portfolio-Projekt
zählt Stabilität mehr als technische Aktualität des Build-Systems.

# Learning-Log — Tag 17
**Datum:** 2026-06-07
**Thema:** Vorfilter, Composite-Score, src-Layout-Falle

---

## Was heute gelernt wurde

### 1. Warum ein installiertes Paket trotzdem nicht importierbar ist

Das klingt paradox: `uv pip list` zeigt das Paket als installiert an — aber `import aect` schlägt mit `ModuleNotFoundError` fehl. Wie geht das?

Bei einem "src-Layout" liegt der Code nicht direkt im Projektordner, sondern in einem Unterordner namens `src/`. Das ist eine bewusste Designentscheidung: es verhindert, dass man versehentlich den lokalen Code importiert, anstatt das wirklich installierte Paket.

Das Problem entsteht bei der Installation: Python erstellt eine kleine Textdatei (`.pth`-Datei) im `site-packages`-Ordner, die Python sagt "schau auch in diesem Verzeichnis nach". Wenn der Build-Backend (hier: hatchling) nicht explizit weiß, dass der Code in `src/` liegt, schreibt er den Pfad zum Projekt-Root in diese Datei — zum Beispiel `/Users/.../ai-efficiency-control-tower`. Python sucht dann nach einem Ordner namens `aect` direkt darin. Der existiert aber nicht — der Ordner heißt `src`, und `aect` liegt darin.

**Fix:** In `pyproject.toml` unter `[tool.hatch.build.targets.wheel]` den Eintrag `packages = ["src/aect"]` ergänzen. Damit weiß hatchling: der Code für das Paket liegt in `src/aect/`, nicht im Root.

**Warum pytest das Problem nie gesehen hat:** pytest hat in seiner Konfiguration (`pyproject.toml` unter `[tool.pytest.ini_options]`) die Zeile `pythonpath = ["src"]` — das fügt `src/` automatisch zum Python-Suchpfad hinzu, bevor die Tests laufen. Deshalb funktionieren Tests, aber `python -c "import aect"` nicht. Pytest hat das Problem also verdeckt.

**Was das für Phase B bedeutet:** Wenn FastAPI gestartet wird, braucht es das gleiche Paket. Ohne diesen Fix wäre der Server-Start in Phase B mit dem gleichen Fehler gescheitert. Besser jetzt als dann.

---

### 2. Warum Vorfilter und Composite-Score getrennte Module sind — obwohl beide "Regeln" sind

Beide sind deterministisch und beide stehen in Phase A. Trotzdem sind sie getrennt, weil sie unterschiedliche Fragen beantworten:

Der **Vorfilter** ist ein binäres Gate: pass oder fail. Wenn ein Use Case die Mindesthürden nicht nimmt, ist die Bewertung vorbei — alles andere wäre Zeitverschwendung. Das ist eine ja/nein-Entscheidung.

Der **Composite-Score** ist eine kontinuierliche Einschätzung: wie aufwändig ist dieser Use Case in der Umsetzung, auf einer Skala von 2 bis 10? Das ist keine Ja/Nein-Frage, sondern eine Einordnung.

Beide in eine Funktion zu packen wäre technisch möglich — aber dann hätte die Funktion zwei verschiedene Verantwortlichkeiten. Eine Funktion, eine Verantwortlichkeit ist ein Grundprinzip sauberer Software. Separate Module lassen sich außerdem separat testen, separat erweitern, und separat erklären.

---

### 3. RUF001 — En-Dash vs. Hyphen (zum zweiten Mal)

Das `–`-Zeichen (En-Dash, Unicode U+2013) sieht im Code aus wie ein Bindestrich, ist aber keiner. Ruff fängt das mit RUF001 ab, weil es in Code-Kontexten nahezu immer ein versehentlich eingefügtes falsches Zeichen ist.

Das Muster tritt bei Texten wie `"Wert muss 1–5 sein"` auf — schreibt man den Bereich mit einem echten Bindestrich `-`, wäre es `"Wert muss 1-5 sein"`. Kleiner Unterschied, aber Ruff blockiert den Commit konsequent. Fix ist trivial (`sed` ersetzt alle Vorkommen), aber es wäre besser, es von Anfang an richtig zu schreiben.

---

## Interview-taugliche Formulierung

**Frage:** "Was ist der Unterschied zwischen einem installierten Python-Paket und einem importierbaren?"

**Antwort:** Bei einem `src`-Layout muss der Build-Backend explizit konfiguriert sein, damit er weiß, wo im Projektverzeichnis der Code liegt. Ohne diese Konfiguration erstellt die editable Installation eine `.pth`-Datei, die auf den falschen Pfad zeigt. Das Paket gilt als installiert, ist aber nicht auffindbar. pytest verdeckt das Problem durch seine eigene `pythonpath`-Konfiguration — weshalb Tests grün sind, während `python -c "import paket"` scheitert.

## Tag 18 — 2026-06-07: Wie ein System aus Zahlen ein Urteil macht

### Was gebaut wurde

Das System kann jetzt aus den berechneten ROI-Zahlen automatisch entscheiden,
in welche von drei Kategorien ein Use Case fällt: kaum lohnenswert,
vertretbar mit Risiken, oder klarer Gewinner. Diese Entscheidung heißt
Zonen-Klassifikation.

Zusätzlich gibt es jetzt eine Qualitätsprüfung: Bevor das System überhaupt
rechnet, schaut es nach ob die Beschreibung konkret genug ist. Wer nur
„wir wollen effizienter werden" einreicht, bekommt keine Bewertung —
sondern einen konkreten Hinweis was fehlt.

### Das Wichtigste: Regeln vor KI

Das klingt banal, ist es aber nicht. Die meisten KI-Projekte lassen das
Modell entscheiden was gut oder schlecht ist. Hier ist es umgekehrt:
Die Entscheidung LIKELY_WIN oder MARGINAL_GAIN trifft reiner Code —
keine KI, keine Zufälligkeit, kein Halluzinieren. Das hat drei Vorteile:

1. **Reproduzierbar.** Gleiche Zahlen → immer gleiche Zone. Das kann man
   in einem Interview vorführen und verteidigen.
2. **Testbar.** Man kann beweisen dass das System korrekt funktioniert —
   nicht nur hoffen.
3. **Vertrauenswürdig.** Wenn die KI später einen Lösungsvorschlag macht,
   hat das System bereits eine überprüfte Grundlage — die KI-Ausgabe wird
   gegen die Regel-Ausgabe gemessen, nicht umgekehrt.

### Property-based Testing — warum normale Tests nicht reichen

Normale Tests prüfen handverlesene Beispiele: „Wenn Nutzen 75.000 EUR und
Score 2, dann LIKELY_WIN." Das ist wichtig. Aber es beweist nicht ob die
Logik *immer* korrekt ist.

Property-based Tests (mit dem Tool Hypothesis) generieren automatisch
Hunderte von zufälligen Eingaben und prüfen ob eine mathematische Eigenschaft
immer gilt. Heute wurden zwei solche Eigenschaften bewiesen:

- Handlungsdruck kann eine Zone nur verbessern, nie verschlechtern.
- Mehr erwarteter Nutzen ergibt immer die gleiche oder eine bessere Zone
  (nie eine schlechtere).

Das ist der Unterschied zwischen „es funktioniert in meinen Beispielen"
und „es funktioniert immer".

### Konfiguration statt Hartkodierung — warum das rechtlich relevant ist

Die Schwellenwerte (ab welchem Nutzen ist ein Use Case LIKELY_WIN?) stehen
nicht im Code, sondern in einer separaten Konfigurationsdatei. Das ist keine
technische Spielerei — es ist eine rechtliche Absicherung. Der Code ist
generisch und zeigbar; die firmenspezifischen Werte bleiben intern.
(Hintergrund: interne Referenz (entfernt), vertragliche Verpflichtung.)

### Bugs die heute aufgetaucht sind

Der schlimmste war wieder der Editable-Install-Bug: Nach jedem
`uv add` (Paket installieren) verliert das Venv (die Python-Umgebung)
den Verweis auf das eigene Projekt. Fix ist immer gleich:
`uv pip install -e . --reinstall`. Das wird in den Standard-Ablauf
für Tag 19 eingebaut.

## Tag 19 — 07.06.2026 — AI-vs-Automation-Router + Umgebungsreparatur

### Was heute passiert ist

Das System hat heute eine Weiche bekommen. Vorher konnte es Use Cases bewerten
(Nutzen, Kosten, Risiko). Jetzt kann es auch entscheiden, *welche Technologie*
für einen Use Case geeignet ist: klassische Automatisierung (wenn der Prozess
einfach und gleichförmig ist), KI (wenn er komplex und mehrdeutig ist), oder
menschliche Prüfung (wenn Datenschutzrisiken im Spiel sind).

Diese Entscheidung passiert ohne KI-Modell — durch klare, testbare Regeln.
Nur wenn das System zu keinem klaren Ergebnis kommt (BORDERLINE), kommt in
einer späteren Phase ein KI-Modell zur Verfeinerung.

### Was gelernt wurde — und warum es wichtig ist

**Lesson 1 — Präzise Fehlertypen beim Testen.**
Frozen Dataclasses (Objekte die nach der Erstellung nicht mehr verändert werden
dürfen) schützen sich über einen speziellen Fehlertyp: `FrozenInstanceError`.
Ein Test der nur auf "irgendeinen Fehler" wartet (`Exception`) prüft nicht wirklich
ob das Objekt unveränderlich ist — er besteht selbst dann, wenn kein Fehler
ausgelöst wird. Lesson: Im Test immer den *spezifischen* Fehler nennen den man
erwartet, nie den allgemeinen.

**Lesson 2 — TOML-Keys müssen exakt mit Code-Konstanten übereinstimmen.**
Die Konfigurationsdatei hatte Schlüssel in Großbuchstaben (`PROFESSIONAL`),
der Code aber erwartete Kleinbuchstaben (`professional`). Da Python bei fehlenden
Schlüsseln einen Standard-Wert zurückgibt statt zu werfen, lief die Berechnung
stillschweigend falsch (Stundensatz = 0, Potenzial = 0). Solche "silent failures"
sind gefährlicher als Abstürze — sie sehen von außen korrekt aus. Lesson: Enum-
Werte und Config-Keys von Anfang an auf denselben Standard festlegen.

**Lesson 3 — Umgebungsdiagnose vor Code-Diagnose.**
Zwei Stunden wurden (in einer früheren Session) damit verbracht, den falschen
Schuldigen zu suchen (setuptools vs. hatchling), während das eigentliche Problem
ein doppeltes Verzeichnis im `.venv` war. Lesson: Wenn Python-Imports schweigen,
erst die Umgebung prüfen (`find .venv -name "*.pth"`, `ls .venv/lib/`) — bevor
man den Build-Mechanismus verdächtigt.

### Zahlen
- 120 Tests grün
- 98% Coverage über alle Domain-Module
- 7 von 7 Phase-A-Modulen gebaut
- 1 Umgebungsfehler diagnostiziert + behoben


## Tag 20 — 09. Juni 2026 — Domain Pipeline + Phase A Gate

### Was gebaut wurde
Der letzte Baustein von Phase A: eine zentrale Funktion, die alle
bisherigen Regelmodule in der richtigen Reihenfolge aufruft.

Stell dir vor, du hast in den letzten Wochen einzelne Maschinen gebaut:
eine die ROI berechnet, eine die filtert, eine die Zonen klassifiziert.
Heute wurde die Fertigungsstraße gebaut, die all diese Maschinen
nacheinander bedient und am Ende einen vollständigen Befund ausspuckt.

### Die wichtigste technische Erkenntnis
Die Reihenfolge der Schritte ist nicht egal. Der Vorfilter prüft:
"Lohnt sich das Potenzial überhaupt?" — aber um das zu wissen, braucht
er die ROI-Berechnung. Also muss ROI zuerst laufen, Vorfilter danach.
Das klingt offensichtlich, war aber im Code nicht klar dokumentiert —
und hat mehrere Fehlerschleifen produziert.

### Was das für das Projekt bedeutet
Phase A ist jetzt vollständig und verteidigbar:
- Das deterministische Bewertungsmodell läuft von Anfang bis Ende durch
- 10 realistische Testfälle prüfen automatisch ob alles noch stimmt
- 98% Code-Abdeckung bedeutet: fast jede Zeile wurde durch Tests ausgeführt

### Die ehrliche Rückmeldung
Tag 20 hat doppelt so lange gedauert wie geplant. Ursache: Ich habe
Funktions-Signaturen geraten statt nachgeschaut. Jede Funktion hat
bestimmte Erwartungen an den Typ und Namen ihrer Parameter — wenn man
das nicht kennt, scheitert der erste Aufruf mit einem Fehler, dann
passt man an, scheitert wieder, und so weiter.

Die Lektion: erst lesen, dann schreiben. Auch wenn es sich langsamer
anfühlt — es ist schneller.

### Was als nächstes kommt
Tag 21: Dokumentation der Architektur-Entscheidungen (warum Regeln vor
LLM, warum drei Zonen, warum Routing als separater Schritt). Das ist
kein Overhead — das ist der Unterschied zwischen "Code der läuft" und
"System das jemand anderes verstehen und weiterentwickeln kann".

## Tag 21 — 10. Juni 2026 — ADRs, Phase-A-Review, ruff E402

### Was heute passiert ist

Phase A ist jetzt wirklich fertig — nicht nur der Code, sondern auch
die Dokumentation der Entscheidungen dahinter. Drei ADRs und ein Review-Dokument.

### Was ein ADR ist

ADR steht für Architecture Decision Record — auf Deutsch: ein kurzes Dokument,
das festhält warum eine technische Entscheidung so getroffen wurde wie sie
getroffen wurde. Nicht nur "wir haben X gebaut", sondern "wir haben X gebaut,
weil Y und Z — und A und B haben wir bewusst verworfen, weil...".

Der Wert entsteht sechs Monate später, wenn jemand fragt: "Warum ist das so?"
Statt aus dem Gedächtnis zu raten, gibt es eine Antwort mit Begründung.

Heute entstanden drei:

**ADR-001: ROI-Modell.** Warum alle Geldwerte mit Decimal statt float gerechnet
werden. (Decimal ist eine Rechenart, die z.B. 0.1 + 0.2 korrekt als 0.3 ausgibt
statt als 0.30000000000000004 — das ist bei Geldbeträgen nicht verhandelbar.)
Warum das Modell keine Ausnahme wirft wenn ein unbekanntes Land eingeht,
sondern stattdessen 0 zurückgibt und am Vorfilter scheitert. Warum alle
Parameter dieser Funktion als benannte Argumente übergeben werden müssen —
bei sieben Zahlen hintereinander ist die falsche Reihenfolge eine sichere
Fehlerquelle ohne benannte Labels.

**ADR-002: Zonen-Logik.** Warum der ZoneClassifier Zahlen bekommt und nicht
das vollständige Eingabeobjekt. (Weil er dann unabhängig vom Rest testbar ist
und bei Änderungen am Eingabeformat nicht angefasst werden muss.) Warum
Handlungsdruck maximal eine Zone hochstuft — keine Überklassifikation.

**ADR-003: AI-vs-Automation.** Warum BORDERLINE eine eigene Ausgabe ist
statt einer Tie-Breaker-Heuristik. (Weil Phase C — die LLM-Schicht — das
besser lösen kann als weitere Regeln. "Ich weiß es nicht" ist ehrlicher als
eine geratene Empfehlung.)

### Phase-A-Review: Technical Debt explizit benennen

Das Review-Dokument enthält eine Tabelle mit offenen Schwachstellen,
die bewusst nicht sofort behoben werden. Das klingt nach schlechter Praxis,
ist aber das Gegenteil: wer Technical Debt nicht benennt, vergisst ihn.
Wer ihn benennt, hat Kontrolle.

Ein konkretes Beispiel aus heute: `_cost_tier()` in der Pipeline ist eine
Hilfsfunktion, die Lizenzkosten in EUR auf eine Kostenstufe 1-3 abbildet.
Das ist eine Schätzfunktion, kein echtes Eingabefeld — ein späteres
`implementation_cost_level`-Feld im Eingabeschema wäre sauberer.
Heute nicht gebaut, aber als Debt dokumentiert mit Priorität "niedrig"
und Zeitpunkt "Post-v1".

### Der Fehler heute: E402

ruff ist das Tool das Code-Stilregeln prüft — wie ein automatischer Lektor
für Programmiercode. Eine seiner Regeln ist E402: alle Import-Anweisungen
(das sind die Zeilen am Anfang einer Python-Datei, die andere Bausteine
einbinden) müssen oben in der Datei stehen — vor jeglichem anderen Code.

Beim Anfügen der neuen Tests wurden auch die dazugehörigen Imports
ans Ende der Datei geschrieben. Das bricht diese Regel.

Fix: die komplette Testdatei neu geschrieben mit allen Imports am Anfang,
alle Aliase (künstliche Umbenennungen mit Unterstrich) entfernt, direkte
Namen überall. Das Ergebnis ist kürzer und lesbarer als das Original.

### Zahlen

153 Tests grün. pipeline.py jetzt 100% Coverage — die zwei offenen Stellen
aus Tag 20 (die `_cost_tier`-Bänder und die `is_actionable`-Zweige)
sind geschlossen. Phase A: fertig.

## Tag 22 — Hexagonal Architecture: Ports, Adapter, Application Service

**Was heute gebaut wurde:** Das Projekt hat jetzt drei Schichten mit klaren Grenzen.
Die Domain-Schicht aus Phase A bleibt unverändert. Darüber kommt eine
Application-Schicht, die orchestriert. Darunter hängen Adapter, die Infrastruktur
liefern.

**Port:** Ein Port ist ein Vertrag in Form von Code — er sagt "ich brauche etwas,
das eine `now()`-Methode hat", ohne festzulegen, wer das liefert. Im echten Betrieb
liefert es die Systemuhr, im Test eine Fake-Uhr mit fixer Zeit.

**Adapter:** Ein Adapter ist die konkrete Umsetzung eines Vertrags. `InMemoryRepository`
ist ein Adapter — er speichert Daten in einem Python-Dictionary im RAM, bis das
Programm beendet wird. Später kommt ein SQLite-Adapter, der dieselbe Schnittstelle
bedient aber dauerhaft speichert. Der Service bemerkt den Unterschied nicht.

**Dependency Inversion:** Normalerweise hängt der "Chef-Code" (Service) am
"Helfer-Code" (Datenbank). Dependency Inversion dreht das um: der Service kennt
nur den Vertrag (Port), nicht den Helfer. Der Helfer passt sich an den Vertrag an,
nicht umgekehrt. Konkreter verletzte Import wäre gewesen:
`from aect.adapters.in_memory.repository import InMemoryRepository` direkt im Service.

**Strukturelles Subtyping:** Python prüft bei `typing.Protocol` nicht ob ein Objekt
explizit "ich bin ein Repository" deklariert hat — es prüft nur ob es die richtigen
Methoden hat. `InMemoryRepository` erbt von nichts, hat aber `save/get/list_all` →
mypy akzeptiert es als RepositoryPort. Wie ein Vertrag ohne Unterschrift, der nur
durch tatsächliches Verhalten gilt.

**SubmittedCase:** Ein Container-Objekt, das Input (was wurde eingereicht), Ergebnis
(was hat die Regel-Engine berechnet), Zeitstempel und ID zusammenhält. Der Empfangsschein
einer Einreichung.

**Heute aufgetretene Fallen:**
- `grep` ohne `--include="*.py"` durchsucht auch kompilierten Bytecode → immer mit Flag.
- Datei ersetzen heisst: zuerst löschen, dann einfügen — nicht drüber schreiben.

## Tag 23 — 2026-06-10 — FastAPI-Grundstruktur

**Was heute entstanden ist:** Die API-Schicht hat ihren ersten Endpoint.
Ein HTTP-Request auf `/health` bekommt jetzt eine Antwort — der erste
beobachtbare Beweis, dass das System von außen erreichbar ist.

**App-Factory:** Statt einer einzelnen globalen App-Variable gibt es eine
Funktion `create_app()`, die bei jedem Aufruf eine frische App-Instanz baut.
Tests rufen diese Funktion direkt auf — so beeinflusst kein Test den nächsten
(kein geteilter Zustand, auf Englisch: "no shared state").

**ASGI / ASGITransport:** ASGI ist der Standard, über den Python-Webapps
HTTP-Anfragen empfangen. ASGITransport leitet Test-Requests direkt in die App
weiter — kein echter Server, kein Netzwerk, trotzdem echter HTTP-Code.

**CORS:** Cross-Origin Resource Sharing — Browser-Sicherheitsregel, die
festlegt, welche anderen Webseiten die API aufrufen dürfen. Leere Liste
heute = niemand darf von außen. Phase F öffnet das gezielt.

**debug=False:** Im Debug-Modus zeigt FastAPI den vollständigen Fehlerstack
in der HTTP-Antwort. Das ist nützlich beim Entwickeln, aber ein
Sicherheitsproblem in Produktion — interne Strukturen werden sichtbar.
Deshalb: von Anfang an ausgeschaltet.

**Comprehension Gate (Vertiefung):** `create_app()` statt `app` in Tests:
Wenn alle Tests dieselbe globale Instanz teilen, könnte Test A Middleware-
oder Router-Zustand hinterlassen, den Test B dann vorfindet. Das führt zu
Tests, die einzeln grün sind, aber in Kombination zufällig fehlschlagen —
der schlimmste Debugging-Fall. Factory = jeder Test startet sauber.

**venv-Korruption (zweimal):** Das virtuelle Environment (die isolierte
Python-Installation für dieses Projekt) wurde nach Paket-Installationen
inkonsistent. Symptom: Fehler beim Pytest-Start, obwohl Pakete installiert
sein sollten. Fix: Environment komplett neu aufbauen (`rm -rf .venv && uv sync`).
Ursache ist ein bekanntes macOS-Muster dieses Projekts.

## Tag 24 — API-Key-Auth, Exception-Handler, GET /cases (2026-06-10)

**Was heute gebaut wurde:** Jeder Endpoint ausser /health verlangt jetzt
einen geheimen Schluessel im HTTP-Header. Wer den Schluessel nicht kennt,
bekommt 401 — Zugriff verweigert. Und wenn intern etwas schieflaeuft,
bekommt der Aufrufer eine generische Fehlermeldung statt dem kompletten
internen Fehlertext.

**FastAPI Dependency Injection:** FastAPI hat ein System, bei dem man einer
Funktion sagt "bevor du laeuft, hol dir das hier" — zum Beispiel "pruefe
zuerst den API-Key". Das nennt sich Dependency. Der Vorteil: Die Auth-Logik
sitzt an einem Ort, nicht in jedem Endpoint einzeln.

**APIKeyHeader:** Ein fertiger FastAPI-Baustein, der den X-API-Key-Header aus
dem HTTP-Request liest. auto_error=False bedeutet: wenn der Header fehlt, gibt
er None zurueck statt automatisch einen Fehler zu werfen — wir werfen dann
selbst einen 401, damit der Fehler einheitlich aussieht.

**dependency_overrides:** In Tests kann man FastAPI sagen "wenn jemand
get_settings() aufruft, gib stattdessen das hier zurueck". So muss kein echter
API-Key in der Testumgebung konfiguriert sein — der Test injiziert einen
bekannten Testwert. Das funktioniert nur weil get_settings kein lru_cache hat;
ein gecachter Wert wuerde das Override ignorieren.

**Globaler Exception-Handler:** Eine Funktion, die FastAPI aufruft wenn irgendwo
eine unbehandelte Exception auftritt. Sicherheitsregel: der Aufrufer erhaelt
nie den internen Fehlertext (koennte interne Details leaken). Er bekommt nur
"Internal error" plus eine request_id — die request_id steht auch im Server-Log,
so kann man den Fehler intern nachverfolgen ohne aussen etwas preiszugeben.

**Starlette Re-raise:** Starlette (das Framework unter FastAPI) sendet die
500-Response und wirft dann die Exception nochmal — damit Server wie uvicorn
sie ebenfalls loggen koennen. Im Test bedeutet das: der Handler hat korrekt
funktioniert, aber der Test-HTTP-Client sieht trotzdem die Exception.
Loesung: raise_app_exceptions=False sagt dem Test-Client "lass Starlette
die Exception re-raisen ohne sie in den Test durchzureichen".

**pydantic-settings:** Eine Bibliothek, die Konfigurationswerte automatisch
aus Umgebungsvariablen oder einer .env-Datei liest. Mit Prefix AECT_ wird
aus AECT_API_KEY automatisch das Feld api_key. extra="ignore" war noetig,
weil PYTHONPATH in der .env stand — ohne diese Einstellung haette pydantic
das als unbekanntes Feld abgelehnt.

**Coverage-Lernpunkt:** 0% Coverage auf dependencies.py bedeutete nicht,
dass der Code nicht lief — er lief, aber pytest hat ihn nie direkt getestet.
Erst mit dedizierten Auth-Tests ist die Luecke geschlossen. Rote Coverage-
Zeilen in einem Security-kritischen Modul sind kein kosmetisches Problem.

## Tag 25 — POST /triage: Der Kern von Phase B

Heute haben wir den wichtigsten Endpunkt gebaut: Man schickt einen
Use-Case-Antrag rein, das System bewertet ihn vollständig und schickt
das Ergebnis sofort zurück.

**Was ist ein Endpunkt?**
Eine Adresse im System, an die man Daten schicken kann und eine
Antwort zurückbekommt — wie ein Schalter in einer Behörde.

**Warum brauchen wir separate Response-Schemas?**
Die Domain-Objekte (das "Innenleben" des Systems) verwenden Typen,
die JSON nicht kennt — zum Beispiel `Decimal` für exakte Geldbeträge
und `tuple` für unveränderliche Listen. JSON kennt nur einfache Zahlen
und Arrays. Die Response-Schemas übersetzen diese internen Typen in
etwas, das jeder Client versteht. Außerdem entscheiden wir bewusst,
was nach außen sichtbar ist — nicht alles was intern existiert gehört
in die API-Antwort.

**Was macht die Mapper-Funktion?**
Sie ist der Übersetzer zwischen den zwei Welten: nimmt ein
Domain-Objekt entgegen und baut daraus das Response-Schema zusammen.
Ein Satz Arbeit, einmal geschrieben, überall konsistent.

**Was haben die Tests geprüft?**
Ob Auth funktioniert (kein Key = kein Zugriff), ob ein guter
Use Case tatsächlich bewertet wird (zone nicht leer), ob ein
schwacher Use Case den Vorfilter nicht besteht (zone bleibt leer),
und ob das System auf kaputte Eingaben sauber mit einem Fehler
antwortet statt zu crashen.

**Warum machen wir den venv-Rebuild?**
macOS kann unter bestimmten Bedingungen die Python-Umgebung
duplizieren, sodass das Paket nicht mehr gefunden wird. Rebuild
ist der saubere Fix — kein Symptombekämpfen.

## Tag 26 — Rate Limiting und Structured Logging

**Rate Limiting** bedeutet: jeder darf nur eine bestimmte Anzahl Anfragen pro Minute stellen. Wie ein Türsteher, der sagt "du warst schon dreimal drin, warte kurz." Wir haben festgelegt: POST /triage maximal 30 Mal pro Minute pro API-Key, GET /cases 60 Mal. Wer drüber kommt, bekommt eine 429-Antwort — das ist der HTTP-Code für "zu viele Anfragen, versuch's später nochmal."

**Structured Logging** heißt: statt rohem Text schreibt der Server jede Meldung als strukturiertes JSON-Objekt. Statt "Fehler bei Request" steht dann `{"event": "Unhandled exception", "request_id": "abc123", "route": "/triage", "timestamp": "..."}`. Damit kann man Logs später maschinell auswerten und filtern.

**Correlation-ID** ist eine zufällige ID die bei jedem Request neu erzeugt wird und durch alle Log-Einträge dieses Requests durchläuft. Wenn ein Fehler passiert, kann man anhand der ID alle zugehörigen Log-Zeilen finden — wie eine Bestellnummer die man durch den ganzen Prozess mitschleppt.

**Das iCloud-Problem:** macOS synchronisiert den Desktop automatisch mit iCloud. Wenn wir neue Pakete installieren, schreibt uv und iCloud gleichzeitig in dieselben Dateien — das korruptiert die Umgebung. Lösung ist das Projekt in einen Ordner zu verschieben, der nicht von iCloud erfasst wird.

**Warum `# type: ignore`?** mypy prüft ob alle Datentypen im Code zusammenpassen. Manchmal hat eine externe Bibliothek (hier: slowapi) eine Typ-Angabe die nicht ganz stimmt — nicht unser Fehler. Der Kommentar sagt mypy: "diese eine Zeile absichtlich ignorieren, wir wissen was wir tun." Der Code selbst ändert sich nicht.

## Day 27 — Wie AECT Daten dauerhaft speichert (SQLite)

**Was war das Problem?**
Bisher landeten alle eingereichten Use Cases nur im Arbeitsspeicher
(InMemoryRepository). Arbeitsspeicher ist wie ein Notizzettel -- sobald der
Server neu startet, ist alles weg. Heute kam SQLite dazu: eine kleine
Datenbank, die als einzelne Datei auf der Festplatte liegt und Daten ueber
einen Neustart hinweg behaelt.

**Was ist eine "Datenbank-Tabelle" hier konkret?**
Eine Tabelle ist wie eine Excel-Tabelle mit festen Spalten. Unsere Tabelle
`submitted_cases` hat vier Spalten: eine eindeutige ID, den Zeitpunkt der
Einreichung, und zwei Spalten mit dem kompletten Inhalt als Text (siehe
naechster Punkt).

**Was bedeutet "Serialisierung"?**
Die Bewertungsergebnisse in AECT sind komplexe, verschachtelte Python-
Objekte (Zahlen, Kategorien, verschachtelte Unter-Ergebnisse). Eine
Datenbank-Spalte kann aber nur Text oder einfache Zahlen speichern.
Serialisierung heisst: das komplexe Objekt wird in einen Text (JSON-Format,
das auch Webseiten benutzen) umgewandelt, bevor es gespeichert wird. Beim
Auslesen passiert das Gleiche umgekehrt -- "Deserialisierung" -- der Text
wird wieder in das urspruengliche Objekt zurueckverwandelt.

**Warum war das nicht einfach "ein Befehl"?**
Drei Eigenheiten mussten beim Zurueckverwandeln extra behandelt werden:

1. **Geld-Betraege (Decimal):** Python kennt einen speziellen Zahlentyp fuer
   exakte Geldbetraege (Decimal), der Rundungsfehler vermeidet, wie sie bei
   normalen Kommazahlen (Float) passieren koennen. JSON kennt diesen Typ
   nicht -- also wird er als Text gespeichert ("1234.56") und beim Zurueck-
   lesen wieder in Decimal umgewandelt.

2. **Feste Auswahlkategorien (Enums):** Felder wie "Zone: LIKELY_WIN" sind
   keine freien Texte, sondern eine von wenigen erlaubten Optionen (eine
   Art Dropdown-Menue im Code). JSON speichert das einfach als Text
   "LIKELY_WIN" -- beim Zurueckholen muss explizit gesagt werden "das ist
   wieder eine Zonen-Kategorie, nicht irgendein Text".

3. **Reihenfolgen, die sich nicht aendern duerfen (Tuples vs. Listen):**
   In Python gibt es Listen (koennen sich aendern) und Tuples (fix, koennen
   sich nicht aendern). JSON kennt nur Listen. Beim Zurueckholen mussten wir
   also wieder explizit sagen "das soll ein Tuple sein".

**Was ist ein "Roundtrip-Test"?**
Ein Test, der prueft: Objekt speichern -> aus der Datenbank wieder auslesen
-> ist es noch exakt dasselbe? 9 solche Tests wurden heute geschrieben, je
einer fuer Geldbetraege, Kategorien, Listen/Tuples und den Fall "manche
Felder sind leer (None), weil der Use Case den Vorfilter nicht bestanden
hat".

**Was war der Fehler bei der Code-Pruefung?**
Zwei automatische Pruef-Werkzeuge (ruff = Stil-Pruefer, mypy = Typ-Pruefer)
haben den ersten Entwurf abgelehnt:
- ruff wollte eine kuerzere Schreibweise fuer eine if/else-Entscheidung
  (sogenannter "ternary operator" -- eine Ein-Zeilen-Variante von if/else).
- mypy hat gemeldet: "diese Variable kann zwei verschiedene Typen haben,
  aber

## Day 28 — Idempotency-Keys: Doppel-Klicks unschädlich machen

**Was ist passiert, in Alltagssprache:**
Stell dir vor, du füllst online ein Formular aus und klickst auf
"Absenden". Die Seite lädt lange, du bist unsicher ob's geklappt hat,
und klickst nochmal. Ohne Schutz hättest du jetzt zwei identische
Einträge in der Datenbank.

Heute habe ich einen Schutz dagegen eingebaut: Der Client (später das
Frontend) kann beim Absenden eine eindeutige "Quittungsnummer"
(`Idempotency-Key`) mitschicken. Beim ersten Absenden merkt sich das
System: "Diese Quittungsnummer gehört zu diesem Ergebnis." Kommt
dieselbe Quittungsnummer nochmal an, gibt das System einfach das alte
Ergebnis zurück — ohne den Use Case ein zweites Mal zu bewerten oder
zu speichern.

**Begriffe geerdet:**
- *Idempotency-Key* = die "Quittungsnummer" — eine vom Client
  erzeugte ID für genau diese eine Aktion.
- *Replay* = "Wiederholung" — das System gibt das vorherige Ergebnis
  noch einmal aus, statt neu zu rechnen.
- *Port* = eine Schnittstellen-Beschreibung ("was kann gespeichert und
  gelesen werden"), ohne festzulegen, *wie* — heute gibt es zwei
  Umsetzungen: im Arbeitsspeicher (für Tests) und in der Datenbank
  (für echten Betrieb).

**Stolperstein des Tages:**
In den Tests hatte ich zwei "Gedächtnisse" (Speicher + Quittungsbuch),
die sich versehentlich bei jeder Anfrage neu erschaffen haben — wie ein
Kellner, der nach jedem Schritt sein Notizbuch wegwirft und ein neues
holt. Der zweite Request konnte sich dadurch nie an den ersten
"erinnern". Fix: beide Gedächtnisse einmal anlegen und für alle
Anfragen wiederverwenden.

**Verständnislücke (für mich, ehrlich notiert):**
Ich habe die Frage "warum reicht der Key allein, ohne den Inhalt zu
vergleichen" nicht ganz sauber beantwortet — kurzer Nachtrag morgen.

## Tag 29 — Warum ein "Schluessel" und eine "Datei" statt eines Passworts und einer Mega-Datenbank

**API-Key (X-API-Key):** Stell dir vor, AECT ist ein Haus mit einer Tuer.
Statt fuer jeden Besucher einen eigenen Hausschluessel mit Namen drauf zu
machen (das waere JWT/Login-System), gibt es genau EINEN Schluessel fuer
die Tuer. Wer den Schluessel hat, kommt rein. Fuer ein System, das nur eine
Person nutzt, reicht das voellig -- ein Mehrpersonen-Schluesselsystem waere
Aufwand fuer niemanden.

Eine Ausnahme: `/health` (der "ist das Haus ueberhaupt an"-Knopf) braucht
keinen Schluessel -- sonst koennte man nicht mal pruefen, ob der Server
laeuft, ohne den Schluessel zu kennen.

**SQLite-Persistenz:** Bisher hat AECT alle eingereichten Faelle nur im
Arbeitsspeicher behalten -- wie ein Notizzettel, der beim Ausschalten des
Rechners verschwindet. SQLite ist eine einzelne Datei auf der Festplatte,
in der die Faelle dauerhaft stehen. Kein Datenbank-Server im Hintergrund,
keine laufenden Kosten -- einfach eine Datei, die man kopieren oder
loeschen kann. Fuer ein Projekt mit einer Person als Nutzer ist das genug;
ein "echtes" Firmensystem mit vielen gleichzeitigen Nutzern bräuchte mehr,
aber das ist hier nicht das Ziel.

**Heutiger Check:** Server kurz gestartet, zwei Web-Adressen abgefragt
(`/health` und `/cases`) -- einmal kam "alles ok" ohne Schluessel, einmal
"kein Zugang" ohne Schluessel. Genau wie geplant. Das war der letzte
formale Pruefpunkt fuer diesen Bauabschnitt (Phase B) -- der ist damit fertig.

## Tag 30 — Was ist ein "Port", und warum kann man das LLM später austauschen?

Heute haben wir einen "Anschluss" (Port) für eine KI gebaut — aber noch
keine echte KI angeschlossen, sondern einen Platzhalter (Mock).

**Was ist ein Port?**
Ein Port ist wie eine Steckdosen-Norm: er legt fest, *wie* man etwas
anschließt (z.B. "schick eine Frage rein, bekomm eine Antwort raus"),
aber nicht, *was* dahintersteckt. Heute steckt ein Platzhalter dahinter,
der immer dieselbe simple Antwort gibt. Später (Phase C, weitere Tage)
steckt da die echte Azure-KI dahinter.

**Warum ist das gut?**
Weil der Rest des Systems (z.B. die Schärfungs-Logik, die wir bald bauen)
nur mit dem Port redet — nicht direkt mit der KI. Wenn wir später die
echte Azure-KI anschließen, ändert sich für den Rest des Systems nichts.
Wie wenn man ein Gerät an eine Steckdose anschließt: die Steckdose ist
gleich, egal ob eine Lampe oder ein Toaster dranhängt.

**Warum erstmal ein Platzhalter statt der echten KI?**
1. Kostenlos und sofort — kein Warten auf Azure, keine Kosten.
2. Vorhersagbar — der Platzhalter gibt immer dieselbe Antwort zurück,
   dadurch können wir testen "kommt beim System das an, was wir erwarten?"
   Mit einer echten KI wäre die Antwort jedes Mal anders, und Tests
   könnten nicht zuverlässig prüfen, ob alles richtig funktioniert.
3. Alle zukünftigen Tests für die KI-Funktionen (Tag 31+) bauen auf diesem
   Platzhalter auf — sie laufen damit schnell, offline und gratis.
## Tag 31 — Die KI bekommt eine erste Aufgabe (noch als Platzhalter)

Heute haben wir den ersten Baustein gebaut, bei dem eine KI mitspielt — bisher
hat das System nur Zahlen ausgerechnet und Fälle eingestuft.

**Was ist ein "Prompt"?** Eine Anweisung an die KI, in einer eigenen Textdatei
statt im Programmcode. Vorteil: Wenn man die Anweisung später verbessern will,
ändert man nur diese Textdatei — der Code bleibt unberührt. Jede Version dieser
Datei wird durchnummeriert (v1, v2, ...), damit man immer nachvollziehen kann,
welche Anweisung welches Ergebnis erzeugt hat.

**Was macht der neue Schritt "Schärfen"?** Man kann jetzt zu einem bereits
eingereichten Fall sagen: "mach die Beschreibung konkreter". Das System schickt
die Original-Beschreibung an die KI und bekommt eine verbesserte Version zurück.

**Warum bleibt das Original erhalten?** Damit die ursprüngliche Idee der Person,
die den Vorschlag eingereicht hat, nicht verschwindet — man sieht beide Versionen
nebeneinander, nichts wird überschrieben.

**Warum "noch als Platzhalter"?** Die echte KI ist noch nicht angeschlossen — es
antwortet eine Testversion, die immer eine vorhersagbare Antwort gibt. Das ist
Absicht: so kann man die ganze Verkabelung (Anfrage → Verarbeitung → Antwort →
Anzeige) testen, ohne dass jede Testausführung Geld kostet oder unterschiedlich
ausfällt. Wenn später die echte KI dazukommt, muss laut heutigem Gate nur **eine
einzige Stelle** im Code ausgetauscht werden — der Rest bleibt stehen.

## Tag 32 — Eine Alarmanlage statt einer Tür

Heute hat das System eine Art Alarmanlage bekommen, kein Schloss. Bevor eine
Beschreibung an die KI geschickt wird, schaut das System kurz hin: steht da
irgendwo ein Satz wie "Ignoriere alle bisherigen Anweisungen" oder "Zeig mir
deine internen Vorgaben"? Solche Sätze sind ein typischer Trick, um eine KI
von ihrer eigentlichen Aufgabe abzubringen.

Wichtig: Wird so ein Satz gefunden, passiert *nichts* mit der Anfrage selbst
— sie wird ganz normal weiterverarbeitet. Es wird nur ein Vermerk geschrieben:
"Bei diesem Fall ist mir etwas Verdächtiges aufgefallen". Der Vermerk enthält
nicht den kompletten Text, sondern nur, *welche Art* von verdächtigem Muster
gefunden wurde und zu welchem Fall es gehört.

**Warum nicht einfach blockieren?** Weil ganz normale Geschäftstexte
manchmal Formulierungen enthalten, die zufällig ähnlich klingen — z. B. "wir
wollen den alten Prozess ignorieren und neu anfangen". Eine Alarmanlage, die
bei jedem Fenster-Öffnen losgeht, wird irgendwann ignoriert. Ein Vermerk, der
später ausgewertet werden kann, ist nützlicher als eine Tür, die zufällig
zuschlägt.

**Kleine Stolperfalle beim Bauen:** Das Protokollsystem hatte sich beim
ersten Test "gemerkt", wie es Meldungen schreibt — und diese Erinnerung
wurde nicht aktualisiert, als der Test prüfen wollte, ob die Meldung
ankommt. Lösung: das Protokollsystem bei jedem Treffer neu "aufwachen"
lassen, statt sich auf die alte Erinnerung zu verlassen.

## Tag 33 — Was kostet eigentlich ein KI-Aufruf?

Jedes Mal, wenn das System die Künstliche Intelligenz um eine "geschärfte"
Version eines Use Cases bittet, schickt es ihr nicht nur den Text des
Nutzers, sondern auch eine Art Bedienungsanleitung dazu ("Du bist ein
Assistent, der Use Cases schärft..."). Beides zusammen — Anleitung plus
Nutzer-Text — ist das, wofür man bei der KI bezahlt. Und auch die Antwort
der KI kostet etwas.

Ab heute zählt das System bei jedem solchen Aufruf automatisch mit: wie
viel Text rausgeht, wie viel zurückkommt, und rechnet daraus eine
geschätzte Kosten-Zahl in Euro aus. Diese Zahl landet in einem
Protokoll im Hintergrund — sie taucht nicht in der eigentlichen Antwort
auf, die der Nutzer sieht.

**Warum das wichtig ist:** Bevor das System echte Anfragen an die
kostenpflichtige KI von Microsoft (Azure) schickt, soll genau
nachvollziehbar sein, wie teuer das wird. Das verhindert böse
Überraschungen auf der Rechnung.

**Die Zähl-Methode heißt "Tokens".** Ein Token ist ungefähr ein
Wortbruchstück — kein ganzes Wort, aber auch nicht nur ein Buchstabe.
Die Zählung läuft über eine Bibliothek namens `tiktoken`, die genau so
zählt, wie es die KI-Anbieter intern auch tun — sonst würde die Schätzung
nicht zur echten Rechnung passen.

## Tag 34 — Was tun, wenn die KI mal nicht antwortet?

Heute ging es darum: Was passiert, wenn der Aufruf an die KI fehlschlägt --
zum Beispiel weil das Netzwerk kurz hakt oder die Antwort zu lange dauert?

**Vorher:** Ein einzelner Fehlschlag hätte den ganzen Vorgang sofort
abbrechen lassen.

**Jetzt:** Das System merkt sich "das war wahrscheinlich nur kurzfristig"
und versucht es automatisch noch zweimal, mit kurzer Pause dazwischen, die
mit jedem Versuch etwas länger wird (sogenannter "Backoff" -- man gibt dem
Problem Zeit, sich von selbst zu lösen, statt sofort wieder draufzuhauen).
Klappt es immer noch nicht, gibt das System den ursprünglichen Fehler
weiter -- nicht irgendeinen generischen "irgendwas ist schiefgegangen".

Außerdem gibt es eine harte Zeitgrenze pro Versuch: Wenn die KI sich
"aufhängt" und gar nicht mehr antwortet, wird der Versuch nach einer
festgelegten Zeit abgebrochen, statt ewig zu warten.

**Wichtigste Erkenntnis:** Die normale Bewertung eines Use Cases (Zahlen,
Regeln, Zonen-Einstufung) braucht die KI gar nicht. Das heißt: Selbst wenn
die KI komplett ausfällt, kann man Use Cases weiterhin einreichen und
bewertet bekommen -- nur die "Schärfung" der Beschreibung (der Teil, der die
KI braucht) wäre betroffen. Das ist heute mit einem Test abgesichert, der
das System sofort scheitern lässt, falls sich das jemals ändert.

**Begriff geklärt:** "Resilience" (Widerstandsfähigkeit) heißt hier konkret:
automatische Wiederholversuche + Zeitlimits + "der Rest läuft trotzdem
weiter".

## Tag 35 — Das Sicherheitsnetz wird eingeschaltet

Gestern haben wir ein Sicherheitsnetz gebaut: automatische Wiederholversuche
und eine Zeitgrenze für Anfragen an die KI. Heute haben wir es tatsächlich
eingeschaltet — und zwar an genau einer Stelle im Code.

**Warum reicht eine Stelle?** Die Bewertungslogik fragt nie "gib mir die
Test-KI" oder "gib mir die echte KI" — sie fragt nur "gib mir irgendeine KI,
die auf meine Frage antworten kann" (das ist der "Anschluss"/Port aus Tag 30).
Heute haben wir an dieser einen zentralen Stelle gesagt: "und zwar mit
Sicherheitsnetz drumherum". Die Bewertungslogik selbst musste dafür nicht
geändert werden — sie merkt nichts vom Netz, sie bekommt einfach eine
Antwort, so oder so.

**Was wurde konkret getestet?** Ein neuer Test ruft genau diese eine Stelle
auf und prüft zwei Dinge: kommt das Sicherheitsnetz tatsächlich mit
("ist es eingepackt?") und funktioniert die Anfrage durch das Netz hindurch
trotzdem normal ("kommt eine Antwort an?").

**Offener Punkt für mich (Claude):** Eine der heutigen Verständnisfragen war
schlecht gestellt — sie verlangte Wissen aus dem Code, das du nicht hast,
weil du die Guides blind abarbeitest. Lehre für künftige Tage: Fragen müssen
aus dem kurzen Kontext-Absatz beantwortbar sein, nicht aus dem Code selbst.

## Day 36 — Die KI bekommt eine zweite Aufgabe: einen ersten Lösungsvorschlag skizzieren

Gestern und vorgestern haben wir die "Schärfung" gebaut -- die KI nimmt
eine unscharfe Use-Case-Beschreibung und formuliert sie konkreter. Heute
kam ein zweiter Knopf dazu: die KI bekommt die gleiche Beschreibung und
skizziert einen ersten technischen Lösungsansatz dazu.

**Warum war das heute so schnell gebaut?**
Weil es technisch fast eine Kopie von vorher war. Alles, was wir in den
letzten Tagen gebaut haben -- die Prüfung auf verdächtige Eingaben
("Sicherheitscheck"), das Sicherheitsnetz mit automatischen
Wiederholversuchen, die Kostenmessung pro KI-Anfrage -- gilt automatisch
auch für die neue Fähigkeit, ohne dass dafür etwas extra gebaut werden
musste. Nur die Frage an die KI ist neu ("schlage eine Lösung vor" statt
"formuliere schärfer"), dazu kommt ein neuer Knopf (Endpoint).

**Was kann das System jetzt noch nicht?**
Der heutige Lösungsvorschlag ist bewusst ein Platzhalter. Die KI weiß noch
nichts über die konkreten Werkzeuge/Plattformen, die tatsächlich zur Auswahl
stehen. Das ist Absicht: dieses Wissen kommt erst in einer späteren Phase,
wenn die KI Zugriff auf eine kuratierte Wissensbasis bekommt ("RAG" -- die
KI kann dann in echten Dokumenten nachschlagen, statt zu raten). Heute ging
es nur darum, die Leitung dafür zu legen.

**Tests:** 262 von 262 automatischen Tests laufen durch, davon 4 neu für
die heutige Funktion.

## Tag 37 (2026-06-13) — Der Assistent kann jetzt "nachfragen"

Heute ging es darum, dem AI-Assistenten eine Art Telefonliste zu geben,
die er bei Bedarf konsultieren kann -- statt sich auf sein Wissen aus dem
Training zu verlassen, das veralten oder unvollstaendig sein kann.

**"Function-Calling"** heisst: Der Assistent kann mitten in seiner Antwort
sagen "ich brauche Info X", der Code liefert X aus einer festen Quelle
(heute: einer Konfigurationsdatei mit den fuenf moeglichen
Ziel-Plattformen fuer einen Loesungsvorschlag), und der Assistent baut das
Ergebnis in seine finale Antwort ein.

Heute wurde nur das **Fundament** gebaut: die "Telefonliste" (ein Eintrag:
"zeig mir die Plattform-Optionen") und eine Testumgebung, die so tut, als
wuerde der Assistent diese Liste anfragen -- ohne echten KI-Aufruf, also
kostenlos und reproduzierbar.

Eine wichtige Absicherung: Fragt der Assistent nach etwas, das nicht auf
der Liste steht, lehnt der Code das explizit ab (`UnknownToolError`) --
er kann also nicht "frei improvisieren" und irgendeine Funktion aufrufen,
die es gar nicht gibt.

Was noch fehlt (kommt Tag 38): Der eigentliche "Frage-Antwort-Tanz" --
Assistent fragt nach der Liste, bekommt sie, formuliert damit seine finale
Antwort. Heute steht nur die Liste und die Tuer-Sicherung bereit, die Tuer
selbst geht morgen auf.

cat >> learning-log.md << 'EOF'

## Tag 38 (2026-06-13) — Die Tuer geht auf: der Frage-Antwort-Tanz

Gestern stand die "Telefonliste" und die Tuersicherung bereit. Heute wurde
sie tatsaechlich genutzt: Der Assistent bekommt die Aufgabe, einen
Loesungsvorschlag zu skizzieren, und kann dabei sagen "zeig mir erst die
Plattform-Optionen". Der Code holt die Liste aus der Konfigurationsdatei,
gibt sie zurueck, und der Assistent baut sie in seine Antwort ein.

Wichtig dabei: Dieser "Tanz" hat eine feste Anzahl Schritte -- maximal zwei.
Der Assistent fragt einmal, bekommt einmal eine Antwort, fertig. Kein
endloses Hin und Her. Das ist eine bewusste Sicherheitsgrenze (sonst koennte
ein fehlerhafter Assistent theoretisch unbegrenzt weiter nachfragen und
Kosten verursachen).

Zweite Absicherung: Was, wenn der Assistent nach etwas Nicht-Existierendem
fragt? Der Code bricht die ganze Anfrage nicht ab -- er sagt dem Assistenten
nur "das gibt es nicht" und der Assistent formuliert trotzdem eine Antwort,
so gut es ohne diese Info geht. Das nennt man "graceful degradation" --
sanftes Nachgeben statt komplettem Absturz.

Ausserdem wurde die Anleitung an den Assistenten ("System-Prompt") erweitert:
er weiss jetzt, dass die Plattform-Liste existiert, aber auch, dass die
Beschreibungen darin noch vorlaeufig sind und noch nicht durch echte Quellen
belegt wurden (das kommt in einer spaeteren Phase). Deshalb soll er
vorsichtig formulieren ("koennte passen") statt bestimmt ("ist die richtige
Wahl").
EOF

## Tag 39 — Der dritte Fall, den niemand getestet hatte

Seit ein paar Tagen kann die KI bei einem bestimmten Schritt ("Lösungsvorschlag
machen") auf eine Liste von Hilfsmitteln zugreifen — aktuell genau eines: eine
Liste mit möglichen Zielplattformen. Die KI kann dieses Hilfsmittel nutzen,
muss es aber nicht.

Bisher waren zwei Reaktionen der KI getestet: "ich nutze das Hilfsmittel" und
"ich versuche, ein Hilfsmittel zu nutzen, das es gar nicht gibt" (dafür gibt es
eine Sicherheitsabfangung, die verhindert, dass das System abstürzt).

Die dritte Reaktion fehlte: "ich brauche kein Hilfsmittel, ich antworte
einfach direkt." Das ist der häufigste und harmloseste Fall — aber auch der
musste nachgewiesen werden, sonst weiß man nicht sicher, ob der Code damit
wirklich richtig umgeht.

Heute kam ein Test dafür dazu: ein Fake-Modell, das immer direkt antwortet,
egal welche Hilfsmittel angeboten werden. Der Test prüft zwei Dinge: dass eine
normale Antwort zurückkommt, und dass dabei nur **ein** Eintrag in der
Kosten-Buchhaltung entsteht — beim Hilfsmittel-Pfad sind es zwei (einmal für
"was will die KI tun", einmal für "hier ist die finale Antwort").

Mit diesem Test ist die "Kosten- und Verhaltensabdeckung" für diesen Teil des
Systems jetzt vollständig: alle drei möglichen Reaktionen der KI sind
nachgewiesen, nicht nur die zwei auffälligeren.

**Neu ab heute:** Die Frage-Antwort-Runde am Ende jeder Anleitung (das
"Verständnis-Check") wird jetzt direkt in die Daily Note geschrieben. So ist
beim nächsten Tag sofort sichtbar, ob die Frage vom Vortag beantwortet wurde —
ohne dass im Chat-Verlauf gesucht werden muss.

## Tag 40 — Echter KI-Anbieter angeschlossen, ohne den Rest anzufassen

Bisher hat das System mit einer "Test-Attrappe" gesprochen: einer simulierten
KI, die immer dieselbe vorhersehbare Antwort gibt, ohne echte Kosten oder
Internet-Verbindung. Heute kam die echte Verbindung zu Azure (Microsofts
Cloud-KI-Dienst) dazu — als zweite Möglichkeit neben der Attrappe.

**Wie die Umschaltung funktioniert:** Eine einzige Stelle im Code prüft, ob
Zugangsdaten für Azure hinterlegt sind. Sind sie da, nutzt das System die
echte KI. Sind sie nicht da (wie heute — noch keine Zugangsdaten in der
Konfiguration), läuft die Attrappe weiter. Der große Rest des Systems — die
Bewertungslogik, die Use-Case-Schärfung, die API-Endpunkte — bekommt davon
nichts mit. Für die ist es einfach "die KI", egal welche dahintersteckt.

**Warum das wichtig ist:** Wenn in einem Jahr ein anderer KI-Anbieter
genutzt werden soll (oder ein günstigerer, oder ein besserer), muss nur ein
neuer "Übersetzer" für diesen Anbieter gebaut und an derselben einen Stelle
eingehängt werden. Der Rest des Systems bleibt unberührt — keine
Kettenreaktion durch den ganzen Code.

**Technisches Detail, das Kopfschmerzen machen könnte, wenn man's nicht
weiß:** Die echte KI liefert ihre Antworten in einem anderen Format als die
Attrappe — z. B. werden "Werkzeug-Aufrufe" (wenn die KI um zusätzliche Daten
bittet) als Text-Zeichenketten zurückgegeben, die erst noch in "richtige"
Daten umgewandelt werden müssen. Der neue Übersetzer macht genau diese
Umwandlung in beide Richtungen.

**Heute kein echter Test mit der echten KI** — dafür fehlen noch die
Zugangsdaten (Passwort + Adresse für den Azure-Dienst). Das ist geplant und
kein Fehler: der Übersetzer ist fertig gebaut und durchgetestet (mit einer
simulierten Verbindung), der scharfe Test mit echten Kosten kommt als
eigener kleiner Schritt, sobald die Zugangsdaten eingerichtet sind.

**Tests:** 289 grün (14 neu dazugekommen).

cat >> learning-log.md << 'EOF'

## Tag 41 — Zweischichtiger Report

Heute hat das Projekt einen "Report"-Knopf bekommen: man gibt eine
Use-Case-ID an und bekommt zwei Ansichten auf dasselbe Ergebnis zurueck.

Die erste Ansicht ist fuer jemanden, der schnell entscheiden muss: eine
Ampel-Zone (Gewinn-wahrscheinlich / mit Vorsicht / eher nicht), eine
Empfehlung und ein kurzer erklaerender Satz. Die zweite Ansicht ist fuer
jemanden, der jede Zahl pruefen will: alle Einzelwerte aus der Bewertung
(Geldbetrag, Aufwands-Score, Risiko-Flags usw.).

Wichtig: nichts davon wird neu berechnet. Beide Ansichten sind nur zwei
verschiedene Zusammenstellungen aus dem Ergebnis, das ohnehin schon
existiert -- aehnlich wie eine Kurzfassung und eine ausfuehrliche Fassung
desselben Berichts.

Ein kleiner Stolperstein: beim Schreiben ist eine neue Funktion versehentlich
"ausserhalb" der zustaendigen Code-Einheit gelandet (eine Frage von
Leerzeichen am Zeilenanfang in Python -- das entscheidet, wozu ein Code-Block
gehoert). Die automatische Typ-Pruefung (mypy) hat das sofort gemeldet, bevor
es ueberhaupt zu Tests kam. Klassisches Beispiel dafuer, warum diese
Pruef-Schritte vor jedem Commit laufen.
EOF

cat >> learning-log.md << 'EOF'

## Tag 42 — KI-Texte werden gespeichert statt nur durchgereicht

Bisher hat das System die beiden KI-generierten Texte -- die geschärfte
Aufgabenbeschreibung und den Lösungsvorschlag -- nur kurz angezeigt und
dann vergessen. Wer den zusammenfassenden Report später sehen wollte,
musste diese Texte jedes Mal erneut mitschicken, als hätte das System sie
nie gesehen.

Heute haben wir das geändert: Beide Texte werden jetzt zusammen mit dem
restlichen Fall abgespeichert -- egal ob der Fall aktuell im
Arbeitsspeicher liegt (für Tests) oder in der Datei-Datenbank (für den
echten Betrieb). Wenn man danach den Report abruft, ohne etwas erneut
mitzuschicken, tauchen die Texte trotzdem auf.

**Warum das wenig am Rest des Programms ändert:** Das Programm spricht mit
dem Speicherort nie direkt, sondern nur über eine Art Vertrag ("speichere
das", "hol das wieder"). Diesen Vertrag mussten wir nicht ändern --
speichern bedeutet schon immer "überschreibe den alten Stand". Wir mussten
also nur an zwei Stellen ein zusätzliches "speichere das jetzt mit ab"
einfügen, plus zwei neue, leere Spalten in der Datei-Datenbank für die
neuen Informationen.

**Was offen bleibt:** Falls man die Datei-Datenbank von vor heute noch
hat, fehlen ihr diese zwei Spalten -- die müsste man löschen, dann wird sie
beim nächsten Start automatisch neu mit den richtigen Spalten angelegt.
Für ein privates Projekt ohne echte Nutzerdaten ist das kein Problem.
EOF

## Tag 43 — Eine Pruef-Schablone, die noch niemand benutzt

Heute kam kein neuer Knopf dazu, mit dem man etwas anklicken kann. Stattdessen
haben wir eine Art Formular-Vorlage gebaut: Wenn die KI in Zukunft eine
geschaerfte Use-Case-Beschreibung liefert, soll die Antwort einem festen
Aufbau folgen -- Titel, Ist-Zustand, Soll-Zustand, und eine Liste mit
konkreten Verbesserungsvorschlaegen (maximal zehn).

Dazu kam eine Pruef-Funktion: sie nimmt eine KI-Antwort, haelt sie gegen
dieses Formular und sagt entweder "passt" oder "passt nicht, und zwar
genau deswegen". Getestet wurde das mit acht verschiedenen kaputten
Varianten -- von "das ist gar kein gueltiges JSON" bis "der Titel ist viel
zu lang" bis "da sind elf Vorschlaege statt maximal zehn".

**Wichtig:** Diese Pruef-Schablone wird heute von nichts im laufenden System
benutzt. Der Schaerfungs-Knopf von vorher funktioniert exakt wie gestern.
Das ist Absicht -- die Schablone an den Schaerfungs-Knopf anzuschliessen,
ist ein eigener, groesserer Schritt (er aendert, was gespeichert wird und
was die API zurueckgibt), und der bekommt einen eigenen Tag mit eigener
Pruefung.

**Kleine Nebenreparatur:** Beim Speichern von Faellen in der Datei-Datenbank
gab es eine automatische Warnung von einem Sicherheits-Pruefwerkzeug --
nicht weil etwas falsch war, sondern weil das Werkzeug eine bestimmte
Code-Schreibweise generell verdaechtig findet, auch wenn sie hier
ungefaehrlich war. Die Schreibweise wurde umgestellt, damit die Warnung
verschwindet, ohne dass sich am Verhalten etwas aendert.

## Tag 43.1 — Aufräumen und die Prüf-Schablone anschließen

Zwei Dinge an einem Tag, beide eher "fertigmachen" als "Neues bauen".

**Teil 1 — liegengebliebene Hausaufgaben aus dem großen Rückblick.** Beim
letzten großen Check ist aufgefallen: ein Abschlussbericht zu einem
früheren Bauabschnitt (Phase B) wurde nie geschrieben, zwei
Entscheidungsprotokolle hatten offene Enden ("das machen wir später,
sobald..."), und eine Datei hatte einen Tippfehler im Namen. Alles
nachgeholt — reine Dokumentation, kein Verhalten geändert.

**Teil 2 — die Prüf-Schablone von gestern ans System angeschlossen.** Die
Schärfungs-Funktion (aus einer unscharfen Beschreibung eine konkretere
machen) liefert jetzt nicht mehr nur einen langen Text, sondern vier
einzelne Teile: geschärften Titel, geschärften Ist-Zustand, geschärften
Soll-Zustand, und eine Liste mit Verbesserungsvorschlägen.

**Was passiert, wenn die Antwort der KI nicht ins erwartete Format passt?**
Genau dafür war die Prüf-Schablone von gestern da: Sie merkt es, schreibt
einen Vermerk ins Hintergrund-Protokoll ("Format hat nicht gepasst"), und
zeigt stattdessen die komplette rohe Antwort. Niemand bekommt eine
Fehlermeldung oder einen Absturz — nur manchmal "vier ordentliche Teile",
manchmal "ein Textblock".

**Wichtig für heute:** Die Test-Attrappe, mit der wir aktuell arbeiten,
antwortet immer mit einem festen Echo-Satz, nie im neuen Format. Heute
siehst du also immer den "Textblock"-Fall — der "vier Teile"-Fall wird erst
sichtbar, wenn später eine echte KI im richtigen Format antwortet.

**Eine kleine Verschiebung im Hintergrund:** Die Spalte in der
Datei-Datenbank, in der die geschärfte Version gespeichert wird, heißt jetzt
anders und enthält jetzt ein kleines Datenpaket statt nur einem Text. Der
"Report"-Knopf merkt davon nichts — er bekommt weiterhin denselben
Anzeigetext, nur die Übersetzung dazwischen ist neu.

## Tag 44 — Budget-Sentinel: warum wir Kosten messen, bevor wir weiterbauen

Ein "Budget-Sentinel" ist kein Stueck Software, sondern ein Pruefschritt: bevor
man der KI viele Aufgaben gibt, schickt man ihr eine einzige kleine Frage und
schaut sich genau an, was das tatsaechlich gekostet hat -- nicht geschaetzt,
sondern echt gemessen.

Warum das wichtig ist: das System schaetzt Kosten bisher nur rechnerisch
(es zaehlt, wie viele "Wortstuecke" -- Tokens -- eine Anfrage und eine Antwort
haben, und multipliziert das mit einem bekannten Preis pro Wortstueck). Das
ist eine Annahme, kein Beweis. Ob die Anfrage beim echten Anbieter (Azure)
tatsaechlich so viel kostet wie geschaetzt, weiss man erst nach dem ersten
echten Versuch.

Der Plan war, diesen einen echten Versuch heute zu machen. Das ging nicht,
weil noch kein Azure-Konto existiert -- das wird zuerst eingerichtet (eigener
Schritt, kein technisches Problem, eher Papierkram: Konto, Region waehlen,
Modell "buchen", Kosten-Alarm einstellen).

Der Grund, warum wir das vor dem naechsten grossen Baustein (RAG -- das
System, das spaeter Gesetzestexte und Anleitungen nachschlaegt) erledigen
wollen: RAG bedeutet automatisch mehr KI-Aufrufe pro Anfrage, nicht nur einen.
Wenn die Kostenschaetzung daneben liegt, soll das auffallen, solange es nur
um einen einzigen Aufruf geht -- nicht erst, wenn sich der Fehler schon
hundertfach vervielfacht hat.

## Tag 45 — Wenn die Aussenwelt das Modell unter dir wegzieht

Heute ging es weniger um neuen Code, mehr um die echte Cloud-Welt --
und genau die hat zwei Ueberraschungen gebracht, die zeigen, warum gute
Architektur sich lohnt, bevor man sie braucht.

**Ueberraschung 1 -- Konto-Wirrwarr.** Bevor irgendwas mit KI passieren
konnte, musste erst ein eigenes Microsoft-Cloud-Konto her, das niemandem
ausser uns gehoert. Zweimal ist das schiefgelaufen: einmal, weil ein altes
Uni-Konto im Weg stand (das gehoert technisch der Uni, nicht uns -- wie
ein Firmenhandy, das man nicht privat nutzen darf). Einmal, weil ein
brandneues Konto erst noch eine Art "Hausnummer" in der Cloud braucht,
bevor es richtig funktioniert -- die bekommt man nur, wenn man den
offiziellen Anmelde-Weg nimmt, nicht den direkten Login.

**Ueberraschung 2 -- das geplante KI-Modell gab es gar nicht mehr.**
Cloud-Anbieter mustern KI-Modelle regelmaessig aus, so wie ein
Smartphone-Hersteller irgendwann ein altes Modell nicht mehr verkauft.
Genau das war hier passiert: das urspruenglich vorgesehene Modell war
fuer neue Kunden nicht mehr verfuegbar. Das ist normalerweise ein Problem
-- bei uns war es nur eine kurze Entscheidung (welches Modell stattdessen),
weil unser Programm das Modell nie als festen Teil von sich selbst
behandelt, sondern nur als austauschbaren Namen, den man in einer
Einstellungs-Datei eintraegt. Stell dir ein Steckdosen-Geraet vor, das
mit jedem Stecker funktioniert, solange die Spannung passt -- man tauscht
das Geraet nicht aus, nur das Kabel.

**Eine versteckte Preisfrage.** Die neueste, "denkfaehigere" Generation
von KI-Modellen braucht eine andere technische Einstellung dafuer, wie
lang eine Antwort maximal sein darf, als die aeltere Generation. Verwendet
man die falsche Einstellung, lehnt das Modell die Anfrage komplett ab.
Wir haben deshalb bewusst noch das aeltere, aber voll kompatible Modell
genommen und den Umstieg auf die neuere Generation als eigenen,
spaeteren Schritt vorgemerkt -- nicht aus Sparsamkeit, sondern weil ein
Modellwechsel und ein technischer Umbau nicht gleichzeitig passieren
sollten.

**Der eigentliche Test des Tages.** Bisher hat das System nur *geschaetzt*,
was ein KI-Aufruf kostet (gezaehlte Wortstuecke mal bekannter Preis).
Heute kam der erste *echte* Aufruf beim Anbieter, mit echter Rechnung
dahinter: 0,000005 Euro. Praktisch nichts -- aber wichtig war nicht die
Zahl, sondern dass wir jetzt wissen, dass die Schaetzmethode stimmt,
bevor wir sie auf viele Aufrufe gleichzeitig hochskalieren.

**Ein Pruef-Code, der sich selbst belogen hat.** Ein automatischer Test
sollte pruefen: "ohne Cloud-Zugangsdaten benutzt das System die
Test-Attrappe." Der Test hat aber nie wirklich dafuer gesorgt, dass keine
Zugangsdaten da sind -- er hat sich einfach drauf verlassen, dass die
lokale Geheimnis-Datei zufaellig leer war. Sobald da heute echte
Zugangsdaten drinstanden, hat derselbe Test das Gegenteil von dem
gepruefte, was er sollte. Lehre: ein Test muss seine eigenen
Voraussetzungen selbst herstellen, nicht einfach hoffen, dass die Umgebung
gerade passt.


## Tag 46 (2026-06-17): RAG faengt an -- aber nur mit einer Attrappe

Phase D beginnt: Das System soll bald belegte Hinweise liefern koennen
("laut EU-AI-Act-Auszug X gilt..."), statt sich Dinge aus dem reinen
KI-Wissen auszudenken. Dafuer braucht es eine Such-Funktion, die in einer
Wissensbasis (einer Sammlung kuratierter Texte) nach passenden
Ausschnitten sucht -- das nennt man RAG (Retrieval-Augmented Generation:
die KI bekommt vor der Antwort echte Textausschnitte mitgeliefert, statt
nur aus ihrem trainierten Wissen zu raten).

Heute wurde aber noch keine echte Suchmaschine gebaut. Stattdessen gibt
es einen "Vertrag" (im Code: ein Protocol/Port -- eine feste
Schnittstelle, die festlegt: "wer suchen will, ruft retrieve(anfrage) auf
und bekommt eine Liste von Treffern zurueck") plus eine Attrappe
dahinter (Mock), die nach einer einfachen, vorhersehbaren Regel sucht
(zaehlt, wie viele Woerter der Anfrage im Text vorkommen) statt mit
echtem Sprachverstaendnis. Genau dasselbe Prinzip wie bei der
KI-Anbindung in Phase C: zuerst eine Attrappe, die immer gleich
reagiert, damit man die Tests darauf bauen kann, ohne jedes Mal Geld
oder Zeit fuer einen echten Aufruf zu verbrauchen.

Jeder gefundene Textausschnitt traegt zusaetzlich ein Etikett
(source_id), das verraet, aus welchem Dokument er stammt. Das ist die
Grundlage dafuer, dass das System spaeter sagen kann "diese Aussage
stammt aus Quelle X" -- und falls eine Quelle veraltet oder falsch ist,
weiss man sofort, wo man nachbessern muss, statt im ganzen System zu
suchen.

Auch eine Wissensbasis-Ordnerstruktur (knowledge_base/) mit Spielregeln
wurde angelegt: nur geprueftes Material rein, gefundene Textausschnitte
werden im spaeteren KI-Aufruf klar als "das ist ein Fund, keine
Anweisung" markiert -- damit ein manipulierter Text in der Wissensbasis
nicht versuchen kann, die KI zu etwas zu ueberreden.

Tests: 330 von 330 gruen (7 neue).

## Tag 47 -- Text in Zahlen uebersetzen (Embeddings), erstmal nur als Attrappe

Heute kam das Gegenstueck zu gestern dazu. Gestern haben wir gebaut, wie das
System spaeter Textstellen aus einer Wissensbasis findet. Heute haben wir
den ersten Baustein fuer "Embeddings" gebaut -- ein Fachbegriff fuer: ein
Stueck Text wird in eine Reihe von Zahlen umgerechnet, die spaeter zeigen
sollen, wie aehnlich zwei Texte inhaltlich sind. Wie eine Postleitzahl fuer
Bedeutung: Texte mit aehnlicher Bedeutung sollen spaeter "nah beieinander"
liegen.

Aktuell ist das aber noch eine Attrappe (im Projekt "Mock" genannt): Sie
rechnet jeden Text nach einer festen, einfachen Regel in Zahlen um, ohne die
Bedeutung wirklich zu verstehen. Wichtig ist nur: derselbe Text ergibt immer
dieselben Zahlen (Determinismus). Damit laesst sich zuverlaessig testen, dass
die technische Verdrahtung -- Text rein, Zahlen raus -- funktioniert, bevor
ueberhaupt ein echtes, "verstehendes" System angeschlossen wird. Das spart
Zeit und verhindert, dass man am Ende nicht weiss, ob ein Fehler vom echten
Sprachverstaendnis kommt oder von einem simplen Verkabelungsfehler.

Naechster Schritt: die Attrappe durch ein echtes, kostenloses Modell
ersetzen (laeuft lokal auf dem eigenen Rechner, keine Cloud-Kosten), das
Texte tatsaechlich inhaltlich versteht.

## Tag 48 — Der echte Bedeutungs-Uebersetzer: vom Zahlen-Platzhalter zum lernenden Modell

Seit Tag 47 gibt es ein Bauteil, das Text in eine Reihe von Zahlen
umwandelt ("Embedding" -- der englische Begriff dafuer, dass ein Text in
einen mathematischen Raum "eingebettet" wird). Bisher war das nur ein
Platzhalter: er hat aus jedem Text nach einer festen Rechenregel (einem
"Hash", einer Art digitalem Fingerabdruck) Zahlen erzeugt. Verschiedene
Texte ergaben verschiedene Zahlen -- aber ohne jeden Bezug zur Bedeutung.
"Hund" und "Katze" waeren dabei genauso weit voneinander entfernt gewesen
wie "Hund" und "Steuererklaerung".

Heute wurde der Platzhalter durch ein echtes, vortrainiertes Sprachmodell
ersetzt (Name: "all-MiniLM-L6-v2" -- eine kleine, schnelle Version eines
Sprachverstehens-Modells, das komplett ohne Internetverbindung auf dem
eigenen Rechner laeuft). Der entscheidende Unterschied: Texte mit
aehnlicher Bedeutung landen jetzt auch zahlenmaessig nah beieinander, selbst
wenn sie unterschiedlich formuliert sind. "Wie senke ich meine Kosten?" und
"Wege zur Effizienzsteigerung" wuerden vom Modell als inhaltlich verwandt
erkannt -- der Platzhalter haette das nie gekonnt.

Kostenpunkt: Dieses Modell laeuft lokal, kostenlos, beliebig oft. Keine
Cloud, kein Aufruf, kein Cent. Im Gegensatz dazu die Cloud-Alternative
(Azure), die zwar auch sehr guenstig ist, aber jeden einzelnen Aufruf gegen
ein Budget zaehlt.

Eine technische Randnotiz von heute: schickt man denselben Text zweimal
durch das Modell, kommen nicht exakt dieselben Zahlen heraus -- ein
winziger Unterschied weit hinter dem Komma. Grund: das Modell verteilt
seine Rechenarbeit auf mehrere Prozessorkerne gleichzeitig, und bei
paralleler Rechenarbeit kann sich die Reihenfolge, in der kleine
Zwischenergebnisse addiert werden, leicht unterscheiden -- bei
Kommazahlen-Rechnungen aendert eine andere Reihenfolge manchmal das
Ergebnis im allerkleinsten Massstab. Das ist normal und fuer die spaetere
Nutzung (Aehnlichkeit von Texten finden) bedeutungslos -- wichtig war, das
zu erkennen, statt einen Fehler im Code zu vermuten, der gar nicht da war.

Damit ist der erste echte Baustein fuer die spaetere "intelligente Suche"
fertig: ein Bauteil, das Bedeutung in Zahlen uebersetzt. Als naechstes
kommt das Bauteil, das laengere Texte (z. B. ganze Gesetzestexte oder
Dokumentationen) in sinnvolle, kleinere Stuecke zerteilt, bevor sie
eingebettet werden.

## Tag 49: Was ist Chunking, und warum darf ein Stueck Text nicht zu gross und nicht zu klein sein?

Bevor ein Computer einen Text "versteht" (also in eine Reihe von Zahlen
umwandelt, die seine Bedeutung einfangen -- das war der Embedder von
gestern), muss der Text in mundgerechte Stuecke geschnitten werden. Dieses
Zerschneiden heisst Chunking, und jedes einzelne Stueck ist ein "Chunk".

Warum nicht einfach den ganzen Text auf einmal nehmen? Wenn ein Stueck zu
gross ist, vermischen sich darin zu viele unterschiedliche Themen -- die
Zahlen-Darstellung wird dadurch verwaschen und ungenau, fast so, als wuerde
man ein ganzes Buch in einem einzigen Wort zusammenfassen wollen. Und wenn
ein Stueck zu klein ist, fehlt der Zusammenhang -- ein einzelner halber
Satz ohne sein Umfeld sagt oft wenig aus.

Heute haben wir eine Funktion gebaut, die einen Text moeglichst an
natuerlichen Absatzgrenzen in passend grosse Stuecke teilt -- nicht stur
nach Zeichenanzahl, sondern entlang der Stellen, an denen ein Gedanke
ohnehin zu Ende ist. Falls ein einzelner Absatz selbst schon zu lang ist
(kommt selten vor), wird er notfalls trotzdem hart durchgeschnitten, damit
nichts verloren geht.

Zusaetzlich gibt es eine optionale Funktion namens Overlap: ein Stueck vom
Ende des vorherigen Chunks wird in den Anfang des naechsten kopiert. Das
verhindert, dass ein wichtiger Gedanke, der genau an einer Stueck-Grenze
beginnt, spaeter bei der Suche "verschwindet", weil er auf zwei Stuecke
verteilt war und keines der beiden Stuecke ihn vollstaendig enthielt.

## Tag 50 — 2026-06-18: Docker + ChromaDB-Container

**Docker** ist ein Programm, das andere Programme in abgeschotteten
Boxen (Containern) ausfuehren kann -- jede Box hat nur das, was sie
braucht, und sieht den Rest des Rechners nicht. Heute haben wir Docker
zum ersten Mal installiert und benutzt.

**Container sind wegwerfbar.** Das ist Absicht, kein Fehler. Wenn man
eine Box loescht und neu erstellt, sind alle Daten, die in der Box
selbst lagen, weg. Deshalb speichert man wichtige Daten immer in einem
Ordner *ausserhalb* der Box, der beim Neustart einfach wieder
eingehaengt wird -- wie ein USB-Stick, den man in eine neue Box steckt.

**127.0.0.1 statt 0.0.0.0.** Jeder Dienst auf einem Rechner kann
entscheiden, fuer wen er erreichbar ist. 0.0.0.0 heisst "alle im
Netzwerk duerfen". 127.0.0.1 heisst "nur dieser Rechner selbst". Fuer
ein lokales Entwicklungs-Tool wie unsere Vektordatenbank reicht das --
und ein Angreifer im gleichen WLAN kommt nicht ran.

**Versionspinning.** Wir haben das Image nicht als "latest" geladen,
sondern als "1.5.3". Damit stellen wir sicher, dass das System in sechs
Monaten genauso startet wie heute -- egal ob die Macher der Software
zwischendurch etwas geaendert haben.

**Persistenz-Nachweis.** Container runterfahren, schauen ob die Daten
noch da sind, wieder hochfahren -- das war der einfachste und
ehrlichste Test, ob das Konzept "Daten ausserhalb der Box" wirklich
funktioniert. Hat funktioniert.

## Tag 51 — Echte Suche statt Suchen-Attrappe

Bisher hat das System Texte nur nach gleichen Woertern durchsucht (wie
Strg+F). Heute kam die echte Variante dazu: Fragen und gespeicherte Texte
werden zuerst in lange Zahlenreihen uebersetzt ("Embeddings" -- eine Art
Bedeutungs-Fingerabdruck). Aehnliche Bedeutung erzeugt aehnliche Zahlenreihen,
auch wenn andere Woerter benutzt wurden. Die Datenbank (ChromaDB, laeuft in
einer eigenen Box) sucht dann nicht nach Woertern, sondern nach den
naechstgelegenen Zahlenreihen.

Wichtige Regel dabei: Frage und gespeicherte Texte muessen mit demselben
Uebersetzer in Zahlen verwandelt werden. Sonst sprechen beide Seiten
unterschiedliche "Zahlen-Sprachen" und der Vergleich wird bedeutungslos --
die Suche findet dann zufaellige statt passende Treffer, ohne dass es
auffaellt.

Getestet wurde das auf zwei Wegen: einmal mit einer Fake-Datenbank (schnell,
ohne die echte Box), einmal scharf gegen die echte Box -- danach wieder
abgeschaltet, damit nichts unnoetig laeuft und Geld kostet.

## Tag 52 — Rechts-Check statt Code

Heute kein Code. Stattdessen: geprueft, was sich bei der neuen EU-KI-Regel
(genannt "AI Act") gerade tut, und das Ergebnis schriftlich festgehalten.

Hintergrund: Die EU hatte beschlossen, dass strenge Regeln fuer "riskante"
KI-Systeme (z.B. KI, die ueber Menschen entscheidet — Bewerbungen, Kredite)
ab August 2026 gelten. Inzwischen hat sich die EU darauf geeinigt, diese
Regeln spaeter greifen zu lassen — fuer die meisten Faelle erst Ende 2027.
Aber: Das ist bisher nur eine politische Absprache. Damit sie wirklich
gilt, muss sie noch offiziell im "Amtsblatt" (so etwas wie das offizielle
Gesetzblatt der EU) veroeffentlicht werden. Bis das passiert, gilt
rechtlich noch der alte, fruehere Termin.

Was bedeutet das fuer unser Projekt (AECT)? Eigentlich nichts. AECT
bewertet keine Menschen — es bewertet Projekt-Ideen ("sollten wir KI fuer
Aufgabe X einsetzen?"). Die strengen EU-Regeln greifen nur, wenn ein
KI-System ueber Menschen entscheidet (Einstellung, Kredit, Bildung). Weil
AECT das nicht tut, faellt es gar nicht in die strenge Kategorie —
unabhaengig davon, wann sich die Fristen am Ende verschieben.

Der Stand ist jetzt mit Datum und Quellen in einer Entscheidungs-Datei
(ADR — ein begruendetes Protokoll einer wichtigen Festlegung) im Projekt
gespeichert. Naechster Schritt baut direkt darauf auf: Texte ueber
Datenschutz- und KI-Recht schreiben, die das System spaeter automatisch
zitieren kann, wenn jemand eine KI-Projektidee einreicht.

## Tag 53 — Woher weiß das System, wo ein Fakt herkommt?

Heute ging es darum, der Wissensbasis ein Gedächtnis für ihre eigene Herkunft
zu geben. Bisher gab es zwei Gesetzestext-Auszüge als reine Markdown-Dateien —
aber nichts, was maschinenlesbar festhält, woher ein einzelner Satz stammt,
wenn er später aus dem Text herausgelöst und in einer Antwort zitiert wird.

Die Lösung: Jede Quelldatei bekommt am Anfang einen kleinen "Steckbrief" —
welcher Artikel das ist, wie er offiziell heißt, wo man ihn online nachlesen
kann. Wenn ein langer Text später in kleinere Häppchen zerschnitten wird
(nötig, weil die KI nicht beliebig lange Texte auf einmal verarbeiten kann),
bekommt jedes einzelne Häppchen diesen Steckbrief mit auf den Weg — nicht nur
der Text als Ganzes. Sonst würde ein gefundenes Häppchen später isoliert
dastehen, ohne dass jemand — Mensch oder System — noch sagen könnte, aus
welchem Gesetz es stammt.

Dazu kam ein kleiner Baustein, der diese Steckbrief-Information zuverlässig
aus den Dateien herausliest und mit jedem Text-Häppchen verknüpft — sozusagen
ein Adressaufkleber, der bei jedem Paket draufbleibt, egal wie das Paket
später aufgeteilt wird.

Ein Stolperstein hat es kurz erwischt: Im selben Ordner liegt auch eine
Übersichts-Datei, die den Ordner selbst erklärt (kein Gesetzestext, sondern
eine Art Inhaltsverzeichnis). Das System wollte versehentlich auch aus dieser
Übersichts-Datei einen "Adressaufkleber" lesen — was nicht ging, weil sie
gar keinen hat. Kleiner, schnell behobener Fehler: Die Übersichts-Datei wird
jetzt bewusst übersprungen.

**Bewusst nicht gemacht:** Persönliche Daten aus den Texten herausfiltern
("Schwärzen"). Die beiden heutigen Quellen sind öffentliche Gesetzestexte
ohne Personenbezug — das Filtern wird erst relevant, sobald echte
Nutzereingaben verarbeitet werden, und kommt dann als eigener Schritt.

## Tag 54 — Wie ein Gesetzestext durchsuchbar wird

Heute wurde der letzte fehlende Baustein fertig, um Gesetzestexte (DSGVO,
EU-KI-Verordnung) tatsaechlich durchsuchbar zu machen -- nicht nur per
Stichwort, sondern per Bedeutung.

**Was ist ein Embedding?** Ein Computer kann mit Worten nicht direkt
"rechnen". Stattdessen wird jeder Textabschnitt in eine lange Reihe von
Zahlen uebersetzt -- man kann sich das wie einen Fingerabdruck der Bedeutung
vorstellen. Texte mit aehnlicher Bedeutung bekommen rechnerisch aehnliche
Zahlenreihen, auch wenn sie ganz unterschiedliche Woerter benutzen.

**Warum heute zum ersten Mal "echt"?** Bisher gab es fuer diesen Schritt nur
einen Platzhalter, der aus jedem Text einfach eine zufaellige, aber
wiederholbare Zahlenreihe gemacht hat -- nuetzlich zum Testen, aber ohne
echtes Sprachverstaendnis. Heute kam zum ersten Mal ein echtes,
kostenloses, lokal laufendes Sprachmodell (MiniLM) zum Einsatz, das diese
Uebersetzung tatsaechlich auf Basis von Bedeutung macht.

**Was war die eigentliche Aufgabe?** Die kuratierten Gesetzestext-Auszuege
liegen bereits vorbereitet vor (von Tag 53). Heute wurden sie zum ersten Mal
wirklich eingebettet (also in Zahlen uebersetzt) und in eine durchsuchbare
Datenbank geschrieben (ChromaDB, laeuft lokal im Hintergrund). Ein Test hat
danach eine echte Frage gestellt ("Wann ist eine
Datenschutz-Folgenabschaetzung noetig?") und tatsaechlich den passenden
DSGVO-Auszug zurueckbekommen -- der erste echte Beweis, dass die Suche
funktioniert.

**Eine wichtige Regel dabei:** Die Suchfrage muss mit demselben Verfahren
in Zahlen uebersetzt werden wie die gespeicherten Texte. Wuerde man fuer
die Frage ein anderes Uebersetzungsverfahren benutzen als fuer die
gespeicherten Texte, waeren die Zahlenreihen nicht miteinander vergleichbar
-- die Suche wuerde dann scheinbar funktionieren (kein Absturz, kein
Fehler), aber inhaltlich Zufallstreffer liefern, ohne dass das auffaellt.

**Und ein Detail mit Weitblick:** Beim Speichern wurde zu jedem Textstueck
gleich mit hinterlegt, aus welchem Gesetzestext es stammt (z. B. "DSGVO
Art. 35") -- auch wenn die Suche dieses Etikett heute beim Antworten noch
gar nicht herausgibt. Grund: Wuerde man das Etikett erst spaeter ergaenzen
wollen, muesste man entweder alles nochmal neu einbetten oder mit einer
fehleranfaelligen Zweit-Liste arbeiten, die Text und Quelle wieder
zusammensucht. Einmal richtig mitspeichern ist guenstiger als spaeter
nachruesten.

## Tag 55 — Woher kommt die Information eigentlich?

Letzte Woche haben wir beim Einspeichern der Wissens-Häppchen schon ein
Herkunfts-Etikett mitgespeichert (z. B. "DSGVO Art. 35"). Aber beim
Abfragen kam bisher nur der reine Text zurück, das Etikett ging verloren --
so, als würde man in einem Buch eine wichtige Stelle finden, aber nicht mehr
sagen können, aus welchem Buch sie stammt.

Heute wurde das repariert: Jeder Suchtreffer bringt sein Etikett jetzt
automatisch mit zurück. Das ist die Grundlage dafür, dass ein späterer
Bericht nicht nur sagt "hier ist ein Datenschutz-Hinweis", sondern "hier ist
ein Datenschutz-Hinweis, Quelle: DSGVO Art. 35" -- nachprüfbar statt
behauptet.

Wichtig dabei: weil das Etikett schon beim Einspeichern mit abgelegt wurde,
musste heute nichts neu eingespeichert werden -- nur die Abfrage wurde
erweitert, damit sie das, was sowieso schon da liegt, auch mitnimmt. Hätte
man das Etikett erst heute "erfinden" wollen, hätte man die ganze
Wissensbasis noch einmal komplett neu verarbeiten müssen.

## Tag 56 — Belegte Hinweise statt geratener Antworten

Heute kann das System selbst erkennen, wann ein eingereichter Vorschlag mit sensiblen Daten zu tun hat — und holt sich dann automatisch passende Gesetzesauszüge aus einer kleinen, selbst zusammengestellten Sammlung, um daraus einen vorsichtigen Prüfhinweis zu formulieren.

Das Prinzip dahinter: Die KI darf den Hinweis nicht einfach aus ihrem eigenen "Gedächtnis" erfinden. Eine KI kann nämlich überzeugend klingen und trotzdem inhaltlich danebenliegen — das nennt man Halluzination. Deshalb läuft es heute in zwei getrennten Schritten: Erst durchsucht das System seine Sammlung kurzer Gesetzestexte (Wissensbasis genannt) und sucht die passendsten Treffer heraus. Erst danach bekommt die KI diese Treffer vorgelegt und darf nur noch daraus einen lesbaren Hinweis formulieren.

Eine wichtige Entscheidung von heute: Die Quellenangabe ("diese Aussage kommt aus DSGVO Artikel 35") wird nicht von der KI selbst aufgeschrieben, sondern vom Programmcode automatisch zusammengebaut, bevor die KI überhaupt gefragt wird. Die KI verweist im Text nur noch auf eine Nummer wie "[1]". Das ist sicherer, als der KI zu vertrauen, dass sie die Quelle korrekt abschreibt — eine feste, vom Programm verwaltete Liste kann nichts verwechseln, eine frei formulierte Quellenangabe schon.

Zweite Entscheidung: Findet die Wissensbasis zu einem Vorschlag gar nichts Passendes, wird die KI heute erst gar nicht gefragt. Lieber gibt das System dann gar keinen Hinweis aus, als einen Hinweis ohne echte Grundlage zu erzeugen. Das spart außerdem unnötige Kosten, weil kein KI-Aufruf passiert, wenn ohnehin nichts zum Belegen da ist.

Technischer Nebeneffekt: Ein Werkzeug, das schon seit Wochen bereitlag (die Suchfunktion in der Wissensbasis), wurde heute zum ersten Mal tatsächlich benutzt. Vorher war es wie ein angeschlossenes, aber nie eingeschaltetes Gerät — der Anschluss war vorbereitet, aber niemand hat den Stecker reingesteckt.

## Tag 57 — Echte Suche statt Test-Beispiele

Bisher hat das System beim Beantworten von "was sagt das Gesetz dazu" nur in einer winzigen, selbst erfundenen Beispiel-Sammlung mit drei Sätzen nachgeschaut. Heute wurde umgeschaltet: Das System sucht jetzt in zwei echten, sorgfältig ausgewählten Dokumenten (Datenschutz- und KI-Gesetzestext).

Die Umschaltung läuft über einen einfachen Schalter (eine Einstellung: "gesetzt" oder "nicht gesetzt") — nicht darüber, ob der Such-Server gerade läuft. Das ist wichtig: Wenn der Schalter auf "echt" steht, aber der Server nicht erreichbar ist, meldet das System einen Fehler, statt heimlich auf die alten Test-Beispiele zurückzufallen. Ein stiller Rückfall würde bedeuten, dass man einen Fehler im System gar nicht bemerkt — der Fehler ist also gewollt, kein Bug.

Für die echte Suche braucht das System ein kleines KI-Modell, das Texte in Zahlenreihen ("Vektoren") übersetzt, damit ähnliche Bedeutungen nah beieinander liegen. Dieses Modell zu laden dauert ein paar Sekunden. Würde man es bei jeder einzelnen Anfrage neu laden, wäre jede Anfrage spürbar langsam. Deshalb wird es nur einmal geladen, beim ersten Gebrauch, und danach für alle weiteren Anfragen wiederverwendet — ähnlich wie man einen Wasserkocher nicht für jede Tasse Tee neu kauft, sondern einmal anschafft und immer wieder benutzt.

Ein kleines technisches Skript ("Saatgut"-Skript) füllt die echten Dokumente einmalig in die Such-Datenbank ein. Das lief heute zum ersten Mal durch und hat 5 Textabschnitte erfolgreich eingetragen.

## Tag 58 — Das System merkt sich jetzt auch die Datenschutz-Hinweise

Bisher war es so: Wenn man fuer einen eingereichten Vorschlag die
Datenschutz-Hinweise abgerufen hat (zum Beispiel "hier solltest du eine
Datenschutz-Folgenabschaetzung pruefen lassen, Quelle: DSGVO Artikel 35"),
wurden diese nicht gespeichert. Beim naechsten Abrufen des Gesamtberichts
("Report") fuer denselben Fall waren sie wieder weg.

Heute wurde das nachgeholt — genau nach dem Muster, das schon fuer zwei
aehnliche Funktionen existierte (die "geschaerfte" Version eines Use Cases
und der Loesungsvorschlag werden seit laengerem gespeichert). Jetzt merkt
sich das System auch den Datenschutz-Hinweis und zeigt ihn automatisch im
Report mit an, ohne dass man ihn erneut anfordern muss.

Eine technische Besonderheit dabei: Der Hinweistext und seine Quellenangabe
gehoeren untrennbar zusammen — der Text sagt zum Beispiel "siehe Quelle [1]",
und Quelle 1 ist eine konkrete Gesetzesstelle. Wuerde man nur den Text
speichern, aber nicht garantiert die passende Quelle dazu, koennte spaeter
ein falscher Verweis entstehen. Deshalb werden Text und Quellen immer
zusammen gespeichert und nie getrennt voneinander veraendert.

**Fachbegriff geerdet — "Persistieren":** Bedeutet einfach "dauerhaft
speichern", im Gegensatz zu Daten, die nur kurz im Arbeitsspeicher liegen
und beim naechsten Abruf wieder weg sind.

**Fachbegriff geerdet — "Spalte" (in der Datenbank):** Eine Datenbank-Tabelle
ist wie eine Excel-Tabelle mit festen Spaltenkoepfen. Heute kam eine dritte
neue Spalte fuer die Datenschutz-Hinweise dazu — zusaetzlich zu den beiden,
die es schon fuer die anderen zwei gespeicherten Texte gab.

## Tag 59 — Zwei Suchmethoden kombiniert (Hybrid Search)

Bisher hat das System Fragen an seine Wissensbasis nur über
"Bedeutungssuche" beantwortet: ein Modell wandelt Text in Zahlenreihen um
(Embeddings) und vergleicht, welche Texte sich ähnlich "anfühlen". Das
Problem: wenn jemand exakt nach "Art. 35" fragt, kann es passieren, dass
das Bedeutungs-Modell andere Formulierungen für ähnlicher hält als den Text,
der die Antwort tatsächlich enthält.

Heute kam eine zweite, klassische Suchmethode dazu: Stichwortsuche
(BM25 — ein seit Jahrzehnten bewährter Algorithmus, den auch klassische
Suchmaschinen nutzen). Sie zählt, wie oft und wie selten ein gesuchtes Wort
in einem Text vorkommt, und bevorzugt seltene, treffsichere Begriffe
gegenüber häufigen, austauschbaren.

Beide Suchmethoden laufen jetzt parallel und liefern je eine eigene
Rangliste. Diese zwei Listen werden anschließend zu einer einzigen
zusammengeführt (genannt "Reciprocal Rank Fusion") — nicht über die rohen
Punktzahlen (die sind bei den zwei Methoden nicht vergleichbar), sondern
über die *Platzierung*: ein Dokument, das in beiden Listen weit vorne
steht, gewinnt gegenüber einem, das nur in einer Liste ganz oben war.

Ergebnis: Treffer aus reiner Bedeutungsähnlichkeit UND aus exakter
Stichwortübereinstimmung fließen jetzt in dieselbe Antwort ein.

Technische Randnotiz, falls sie irgendwo auftaucht: der Stichwort-Algorithmus
wurde selbst geschrieben statt eine fertige Bibliothek einzubinden — bei
einer so kleinen, klar abgegrenzten Aufgabe ist das hier bewusst die
einfachere und kontrollierbarere Lösung.

## Tag 60 — Eine zweite Prüfung für die Suchtreffer

Seit gestern findet das System Antworten über zwei verschiedene Suchwege gleichzeitig — einen, der nach Bedeutung sucht, und einen, der nach exakten Wörtern sucht. Beide Listen wurden zu einer gemeinsamen Rangliste verschmolzen.

Heute kam ein dritter Schritt dazu: ein "Cross-Encoder". Der Name klingt technisch, das Prinzip ist einfach. Die ersten beiden Suchverfahren schauen sich Frage und Textstelle getrennt an und vergleichen sie danach — wie wenn man zwei Personen unabhängig voneinander nach ihrer Meinung fragt und die Antworten erst danach abgleicht. Der Cross-Encoder schaut sich Frage und Textstelle direkt gemeinsam an, bevor er ein Urteil fällt — wie ein Gutachter, der beide Dokumente nebeneinanderlegt statt sie nacheinander zu lesen. Das ist genauer, aber auch aufwendiger — deshalb läuft es nicht über die ganze Wissensbasis, sondern nur über die besten Kandidaten, die die ersten beiden Suchverfahren bereits eingegrenzt haben.

Das fertige Modell dafür kam mit einer bereits installierten Programmbibliothek mit (`sentence-transformers`) — keine neue Installation nötig.

## Tag 61 — Hat das System wirklich verstanden, was es gefunden hat?

Bisher hatte das Projekt drei Suchschritte gebaut, aber nie live ausprobiert, ob sie
zusammen tatsaechlich funktionieren. Heute war der Tag, an dem genau das geprueft
wurde — mit echten Beispiel-Faellen, nicht nur mit automatischen Tests.

**Was getestet wurde:** Ein Fall mit sensiblen persoenlichen Daten (eine KI, die
Bewerbungen vorsortiert) und ein harmloser Fall (automatische Raumbuchung) wurden
durch das System geschickt. Bei beiden wurde geprueft: Findet das System die richtigen
Gesetzestexte, und gibt es im Antworttext die Quelle korrekt an?

**Das wichtigste Ergebnis:** Es hat funktioniert, und zwar auf eine Art, die besonders
vertrauenswuerdig ist. Die Quellenangabe im Text (zum Beispiel "[1]" fuer einen
bestimmten Paragrafen) wird nicht von der KI selbst erfunden. Stattdessen sucht das
System zuerst die passende Textstelle, vergibt ihr eine Nummer, und die KI darf in
ihrem Text nur auf diese vorgegebene Nummer zeigen. Die KI kann also keine falsche
Gesetzes-Nummer erfinden — sie kann nur auf etwas zeigen, das wirklich gefunden wurde.

**Ein Nebenfund:** Bei einer Suchanfrage, die absichtlich nichts mit dem Thema zu tun
hatte ("Mittagessen Kantine"), hat das System trotzdem zwei Treffer zurueckgegeben —
nur eben mit erkennbar schlechten Bewertungen. Das System sagt also nicht von selbst
"dazu habe ich nichts gefunden", es liefert immer etwas. Für den jetzigen Einsatz ist
das unproblematisch, weil das System nur mit fest vorgegebenen Suchanfragen arbeitet,
nie mit freiem Nutzertext — aber es ist ein Punkt, den man im Hinterkopf behalten muss,
falls sich das spaeter aendert.

**Eine technische Lektion am Rande:** Mitten im Testen ist die Programmierumgebung kurz
kaputt gegangen — ein bekanntes, bereits dokumentiertes Problem auf macOS, bei dem
Systemdateien doppelt angelegt werden koennen. Der bekannte Reparaturschritt hat sofort
funktioniert. Gut zu sehen, dass die eigene Dokumentation aus frueheren Taegen im
Ernstfall tatsaechlich greift.

**Naechster Schritt:** Phase D (die Such- und Beleg-Funktion) ist damit fertig. Als
naechstes kommt Phase E — dort wird systematisch geprueft, wie gut das Gesamtsystem
ueber viele Testfaelle hinweg wirklich ist, nicht nur in einzelnen Stichproben wie heute.

## Tag 62 — Testfaelle fuer die spaetere Qualitaetspruefung

Heute habe ich keine neue Funktion fuer die Bewertung selbst gebaut, sondern die
Grundlage dafuer, wie ich spaeter pruefe, ob die Bewertung gut funktioniert.

Stell dir vor, du willst testen, ob ein Pruefer faire Noten vergibt. Dafuer brauchst
du Beispielarbeiten mit bekannten "richtigen" Noten, gegen die du den Pruefer laufen
laesst. Genau das sind die "Eval-Cases": vier erfundene Beispiel-Antraege (z. B. ein
HR-Onboarding-Prozess, ein IT-Support-Ticket), die genauso aussehen wie ein echter
Antrag, aber komplett ausgedacht sind -- keine echten Firmendaten.

Jeder dieser Beispiel-Faelle hat ein Feld fuer eine "erwartete Bewertung" -- aber das
Feld ist heute bewusst leer gelassen. Der Grund: Wenn das System selbst seine eigene
Bewertung als "erwartete" Antwort eintraegt, vergleicht man am Ende das System nur mit
sich selbst. Das stimmt dann immer ueberein, beweist aber gar nichts -- so wie ein
Schueler, der seine eigene Klausur korrigiert, immer eine Eins bekommt. Die "erwartete
Bewertung" muss spaeter von einem Menschen (mir) unabhaengig eingetragen werden, damit
der Vergleich ueberhaupt aussagekraeftig ist.

Zusaetzlich habe ich ein Format festgelegt, in dem diese Testfaelle gespeichert werden
(eine Zeile pro Fall, statt einer grossen Liste) -- das macht es einfacher, einzelne
Faelle hinzuzufuegen oder zu vergleichen, ohne die ganze Datei neu zu schreiben.

## Tag 63 — Der Pruefer fuer das System

Heute hat das Projekt einen "Pruefer" bekommen, der die vier Beispiel-Faelle aus dem
letzten Tag nimmt und durch dieselbe Berechnung schickt, die spaeter jede echte
Einreichung durchlaeuft. Stell dir das vor wie eine Pruefung, bei der man die
Musterloesung schon hat, aber dem Pruefer absichtlich erstmal keine verraet -- er
rechnet trotzdem, kann sein Ergebnis nur noch nicht mit einem menschlichen Urteil
abgleichen.

Genau deshalb sagt der heutige Bericht bei allen vier Faellen "kein Vergleich
moeglich" und nicht "richtig" oder "falsch". Das ist kein Fehler, sondern Absicht:
Solange niemand von Hand gesagt hat, welche Einstufung ein Fall eigentlich verdient
haette, darf das System das nicht selbst behaupten -- sonst wuerde man am Ende nur
pruefen, ob das System sich selbst zustimmt. Das waere wie ein Schueler, der seine
eigene Klausur korrigiert.

Wichtig fuer spaeter: Sobald jemand (aktuell: ich selbst als Experte) bei einem Fall
ein eigenes Urteil eintraegt, vergleicht der Pruefer ab sofort genau bei diesem einen
Fall "hat die Maschine richtig gelegen oder nicht" -- die anderen, noch unbeurteilten
Faelle bleiben davon komplett unberuehrt. Jeder Fall wird einzeln behandelt, keiner
beeinflusst den anderen.

Technischer Begriff dahinter, einfach erklaert: Es gibt nicht nur "stimmt ueberein"
und "stimmt nicht ueberein", sondern noch einen dritten Zustand "kann (noch) nicht
verglichen werden" -- und der wird bewusst nicht mit "stimmt nicht ueberein"
verwechselt, weil das ein falsches Signal waere.

## Tag 64 (21. Juni 2026): Wenn Mensch und Maschine sich nicht einig sind

Heute ist zum ersten Mal getestet worden, ob das System und ein echter Mensch zu
denselben Einschaetzungen kommen. Dafuer hat Anas drei Beispiel-Faelle gelesen und
sich selbst ein Urteil gebildet ("lohnt sich das?") — bevor er wusste, was die
Berechnung im Hintergrund sagen wuerde. Erst danach wurden beide Urteile
verglichen.

Ergebnis: bei einem von drei Faellen stimmten Mensch und System ueberein, bei
zwei nicht. Das ist kein schlechtes Ergebnis fuer den ersten Versuch — es zeigt
vor allem, dass die Vergleichsmethode funktioniert. Ob das System grundsaetzlich
zu vorsichtig oder zu optimistisch rechnet, laesst sich aus drei Faellen noch
nicht sagen.

Ein Nebenbefund war wichtiger als die Zahl selbst: Bei der Beschreibung eines
Falls wurde Anas versehentlich eine falsche Information genannt (zu viele
"Dringlichkeits-Gruende" fuer den Fall). Nachdem das korrigiert wurde, blieb sein
Urteil trotzdem gleich. Das zeigt zweierlei — zum einen, dass sein Urteil nicht
einfach an Details haengt, zum anderen aber auch eine wichtige Lehre: Wie ein
Fall einem Menschen vorgestellt wird, kann das Ergebnis eines Vergleichstests
selbst beeinflussen. Das muss man im Hinterkopf behalten, sobald mehr Faelle auf
diese Weise getestet werden.

## Tag 65 -- Warum stimmt die Maschine nicht mit dem Experten ueberein?

Gestern hatte das System bei zwei von drei Testfaellen ein anderes Urteil
gefaellt als ich selbst. Heute ging es darum, herauszufinden, woran das
genau liegt -- nicht nur "es stimmt nicht ueberein", sondern "an dieser
einen Stelle kippt die Entscheidung".

Das System bewertet jeden Fall ueber mehrere Zwischenwerte: wie viel Nutzen
er bringt, wie aufwaendig/riskant er ist (ein Punktwert aus Komplexitaet,
Kosten und Datenschutz-Einstufung zusammengesetzt), und wie dringend er ist.
Aus diesen Zwischenwerten ergibt sich am Ende eine von drei Kategorien:
"lohnt sich klar", "lohnt sich mit Vorsicht" oder "lohnt sich eher nicht".
Bisher sah man nur das Endergebnis, nicht die Zwischenwerte.

Heute habe ich diese Zwischenwerte sichtbar gemacht. Ergebnis: bei beiden
abweichenden Faellen lag der Aufwand-Punktwert nur knapp ueber der Grenze
zur naechstbesseren Kategorie -- bei einem Fall fehlte sogar nur ein
einziger zusaetzlicher Dringlichkeits-Grund, um automatisch hochgestuft zu
werden.

Das klingt erstmal beruhigend ("nur knapp daneben"), ist es aber nicht
unbedingt. Es bedeutet: die Grenzen zwischen den drei Kategorien sind harte
Kanten. Ein einziger Punkt mehr oder weniger entscheidet ueber eine ganz
andere Einstufung, obwohl der zugrunde liegende Fall sich kaum veraendert
hat. Mit nur drei Testfaellen kann ich nicht sagen, ob das System die
Grenzen richtig gezogen hat und meine drei Faelle zufaellig nah dran liegen,
oder ob die Grenzen grundsaetzlich zu scharf gezogen sind. Das ist ein
ehrlich offener Punkt, kein geloestes Problem.

## Tag 66 — Warum eine Maschine sich nicht selbst benoten kann

Das Problem war ein bekanntes: der Eval-Runner hatte vier haendisch
kuratierte Testfaelle, aber das Gate zum naechsten Projektabschnitt
verlangte mindestens dreissig. Dreissig Cases von Hand erstellen waere
Fleissarbeit ohne Erkenntnisgewinn -- also ein Generator, der per
Raster arbeitet: fuenf verschiedene Abteilungen (HR, IT, Finanzen,
Recht, Einkauf) als Prozess-Vorlagen, sechs quantitative Muster
(winziges Volumen, mittleres Risikoprofil, alle Dringlichkeits-Flags
gleichzeitig, hohe Frequenz bei kleiner Zeitersparnis pro Fall), plus
sechs Grenzwert-Faelle an den Enden der erlaubten Eingabebereiche.
Ergebnis: 36 Cases, die systematisch verschiedene Bereiche der
Bewertungslogik abdecken.

Die entscheidende Entwurfsfrage war, ob diese Cases ein "richtiges
Ergebnis" bekommen sollten. Man haette einfach die Pipeline laufen
lassen und das Ergebnis als Soll-Wert speichern koennen. Das waere so
als wuerde ein Schueler seine eigene Pruefung korrigieren: er besteht
garantiert, weil die Loesung per Definition mit dem uebereinstimmt,
was er aufgeschrieben hat. Gemessen waere dann nur, ob der Code sich
morgen noch genauso verhaelt wie heute -- Selbstkonsistenz, keine
Korrektheit. Die vier Golden-Cases aus Tag 64 koennen als Massstab
dienen, weil die Experten-Labels gesetzt wurden bevor die Pipeline
ueberhaupt lief: unabhaengiges Urteil, das der Maschine gegenueber
gestellt werden kann. Fuer die synthetischen Cases fehlt diese
Unabhaengigkeit -- also bekommen sie bewusst kein Label.

Was die 36 Cases stattdessen leisten: sie stellen sicher, dass die
Pipeline bei breiterem Eingabe-Spektrum nicht abschmiert, und sie
machen das Gate-Kriterium (dreissig Cases ohne Crash) zu einem
dauerhaft laufenden CI-Test statt zu einem einmaligen Handcheck. Ohne
diese Trennung -- Golden-Cases fuer Korrektheit, Synthetic-Cases fuer
Robustheit -- haette man entweder wenig Vertrauen in die Stabilitaet
oder Zahlen produziert, die wie Guete-Beweis aussehen aber keiner sind.

## Tag 67 — Ein Schalter der nichts umschaltet ist keiner

Im Gate-Dokument stand ein Befehl, der das Eval-System mit einem
Provider-Flag aufrufen sollte: mock oder azure. Das Problem -- der Befehl
existierte nicht, und der Wrapper haette auch nichts gebracht. Der
Eval-Runner schickt Use Cases durch Rechenregeln, nicht durch ein
KI-Modell. Ob du mock oder azure einstellst, das Ergebnis waere dasselbe
gewesen -- wie ein Lichtschalter, der an beiden Stellungen dasselbe Licht
anmacht.

Die Entscheidung war: Wrapper bauen oder Protokoll korrigieren. Bauen
haette ein Interface erzeugt das von aussen eine Auswahl verspricht die
innen nicht existiert. Das ist teurer als es klingt -- wer das System
spaeter betrachtet, wuerde einen Provider-Schalter sehen und annehmen,
dass mock und azure sich im Eval unterschiedlich verhalten. Tun sie nicht.
Falsches Interface, falsches Verstaendnis.

Also: Protokoll korrigieren, ADR schreiben, erklaeren warum kein Wrapper.
Dieselbe Logik steckt in der limitations.md, die heute ebenfalls entstand.
Sie sagt nicht "das System funktioniert", sie sagt was das System beweist
und was nicht. Agreement-Rate 1/3 klingt schlecht -- ist es nicht, wenn
man weiss dass die zwei Mismatches Grenzwert-Faelle sind, keine groben
Fehlurteile. Und praediktive Validitaet, also ob die ROI-Schaetzung
hinterher gestimmt hat, laesst sich im privaten Build strukturell nicht
messen, weil kein einziger Use Case je produktiv umgesetzt wird und
Ergebnisse zurueckfliessen.

Ohne limitations.md wuerde jemand die Agreement-Rate lesen und ein
Urteil faellen ohne Kontext. Mit ihr faellt dasselbe Urteil informiert.
Das ist der Unterschied zwischen einem Ergebnis das sich selbst erklaert
und einem das interpretiert werden muss ohne Schluessel.

## Tag 68 — Warum sich ein System nicht selbst pruefen darf

In Phase E haben wir am Ende keine neue Funktion gebaut, sondern aufgeschrieben
was wir herausgefunden haben -- und wo die Grenzen des Herausgefundenen liegen.
Das klingt nach Verwaltungsarbeit, ist aber der Punkt an dem Bauen und Denken
sich trennen.

Die interessante Frage war: Wir haben 36 Faelle automatisch erzeugt und durch
das System geschickt. Warum koennen diese Faelle kein erwartetes Urteil bekommen?
Der Rechenkern ist deterministisch -- gleiche Eingabe, gleiches Ergebnis, immer.
Man koennte also das System einmal laufen lassen, das Ergebnis als "erwartet"
eintragen, und beim naechsten Lauf pruefen ob es noch stimmt.

Das Problem: Man wuerde nur messen ob das System sich selbst treu bleibt.
Nicht ob es recht hat. Stell dir vor, eine Waage kalibriert sich dadurch, dass
sie heute ihr eigenes Ergebnis als Eichgewicht nimmt. Sie bleibt danach konsistent
-- aber wer sagt, dass sie beim ersten Mal richtig lag?

Deshalb gibt es zwei getrennte Dinge: 36 Faelle die pruefen ob das System unter
verschiedenen Eingaben stabil laeuft, ohne je eine rote Zahl zu werfen. Und 4
Goldene Cases, bei denen ein Mensch unabhaengig geurteilt hat -- "diesen Fall
wuerde ich als LIKELY WIN einschaetzen" -- und das System sich daran messen lassen
muss. Die 36 belegen Robustheit. Die 4 belegen Richtigkeit. Beides braucht man,
keines ersetzt das andere.

Was heute noch dazukam: der Phase-F-Kickoff. Drei Bloecke -- zuerst Dokumentation
(die Architektur-Entscheidungen die bewusst nicht gebaut wurden kommen in
schriftliche ADRs), dann das Frontend, dann Haertung und Karriere-Assets. Der
Reihe nach, nicht parallel -- weil ein Frontend auf einem nicht-erklaeerten System
das schwaecher ist, nicht staerker.

## Tag 69 — Warum ein dokumentiertes "Nein" mehr wert ist als Schweigen

Heute haben wir drei Dinge nicht gebaut — und genau das dokumentiert.
Das klingt zuerst sinnlos, ist aber ein konkretes Portfolio-Problem:
Wer von aussen auf ein GitHub-Repo schaut, sieht nur was drin ist.
Was bewusst weggelassen wurde, ist unsichtbar — ausser wenn es ein
Dokument gibt, das erklaert warum.

Das ist dasselbe Problem wie bei einem Arzt, der keine Operation
durchfuehrt. Der Befund ohne Dokumentation lautet: "hat nichts gemacht."
Mit Dokumentation: "hat Alternativen geprueft, Risiken abgewaegt,
entschieden dass konservative Behandlung ueberlegen ist." Gleiche
Entscheidung, voellig andere Aussenwirkung.

Konkret: Distributed Tracing via OpenTelemetry waere technisch trivial
gewesen — die Bibliotheken sind bereits als transitive Abhaengigkeit
installiert, ein Jaeger-Container waere eine Zeile Docker. Die
Entscheidung dagegen (Single-Service, kein Microservice-Verbund, kein
Problem das Tracing loest) steht jetzt im ADR mit Design-Skizze.
Dasselbe fuer Semantic Caching (PII wuerde im Cache landen und kaskadierte
Loeschung bei Datenschutzanfragen erzwingen) und fuer den Azure-Deploy
(IP-Klaerung ausstehend, Demo via localhost vollstaendig, Teardown-Pflicht
fuer laufende Cloud-Ressourcen unverhältнismaessig).

Was waere ohne diese Dokumente gewesen? Drei Luecken, die wie drei
Wissensmangel aussehen. Mit Dokumentation: drei Abwaegungen, die
zeigen dass Scope-Disziplin eine Entscheidung ist, kein Versaehen.

## Tag 70 — Wann ein ⚠️ kein Fehler ist

Ein Threat Model das nur gruene Haekchen zeigt luegt. Nicht weil
alle Bedrohungen mitigiert waeren -- sondern weil jedes System
Risiken hat die man akzeptiert, und der Unterschied zwischen
"akzeptiert" und "uebersehen" nur durch Dokumentation sichtbar wird.

Heute war das konkrete Problem: ChromaDB, die Vektor-Datenbank, hat
keine Authentifizierung. Wer weiss wo der Port liegt, kann lesen.
Das klingt nach Luecke. Ist es aber nicht -- weil der Port nur
innerhalb von Docker erreichbar ist, genau ein Mensch das System
bedient, und kein oeffentlicher Server dahintersteht. Ein WARN
bedeutet: "das wuerde sich aendern muessen, wenn der Kontext sich
aendert." Wer das nicht dokumentiert, kann den Unterschied zwischen
bewusster Entscheidung und schlampiger Ausfuehrung von aussen nicht
zeigen. Ein Interviewer sieht beides gleich aus -- ausser wenn ein
STRIDE-Dokument auf dem Tisch liegt das erklaert warum der Kontext
die Einschaetzung bestimmt.

Dasselbe Prinzip in der README: Ein "Was dieses System nicht ist"-
Abschnitt klingt defensiv. Ist es nicht. Er verhindert dass jemand
das System mit dem falschen Massstab bewertet. Ein Compliance-
Verantwortlicher der liest "keine Rechtsberatung, nur belegte
Hinweise zur eigenen Pruefung" stellt eine andere Frage als jemand
der das ueberspringt und dann fragt warum das Tool keinen DSB
ersetzt. Den Rahmen zu setzen bevor jemand den falschen anlegt ist
keine Schwaeche -- es ist Kontrolle ueber das Gespraech.

Ohne diese Dokumentation haette das System denselben Code, aber
weniger Verteidigbarkeit. Die Bedrohungsanalyse waere im Kopf,
nicht auf Papier. Ein Interview-Fragesteller der "Wie habt ihr
euer System abgesichert?" fragt bekommt dann eine Antwort die
klingt wie eine Aufzaehlung -- statt einer die zeigt, dass jede
Entscheidung einen Kontext und eine Begruendung hat.

## Tag 71 -- Warum "PARTIAL" ehrlicher ist als "MITIGATED"

Das System hat Citations-before-LLM. Das LLM erfindet keine Artikel-Nummern
mehr, weil die Belege aus der Wissensbasis kommen, bevor das LLM formuliert.
Das ist ein struktureller Schutz, kein bloss promptbasierter. Trotzdem steht
LLM09 auf PARTIAL, nicht MITIGATED.

Der Grund: Citations loesen nur das Problem der erfundenen Quelle. Was sie
nicht loesen ist die Frage, ob der vorhergesagte Nutzen -- sagen wir 80.000 EUR
Jahreseinsparung -- tatsaechlich eintritt. Das koennte man nur pruefen, wenn
das System echte Use Cases bewertet hat, diese tatsaechlich umgesetzt wurden,
und ein Jahr spaeter jemand nachschaut. Diesen Kreislauf gibt es im privaten
Build nicht. Wer das verschweigt und trotzdem MITIGATED schreibt, beluegt den
naechsten Leser der Checkliste.

Dasselbe Prinzip galt fuer das Dockerfile. Der Non-root-User ist kein
Selbstzweck: wenn ein Angreifer einen Weg in den Container findet, kann er
ohne Root-Rechte nur den Prozess beschaedigen, nicht das Host-System darunter.
Das ist keine Garantie, nur eine Huerde mehr -- und eine Huerde die nichts
kostet ausser einer Zeile `USER aect` am richtigen Ort.

Ohne diese Unterscheidung zwischen "strukturell geloest" und "nicht messbar
unter diesen Bedingungen" waere die Checkliste ein Dokument das gut aussieht
und nichts sagt. Mit ihr ist sie ein Dokument das verteidigt werden kann.

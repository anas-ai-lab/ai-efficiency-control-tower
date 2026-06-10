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

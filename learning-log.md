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

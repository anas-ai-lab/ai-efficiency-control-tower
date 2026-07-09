# AECT Engineering Constitution

Dieses Dokument ist die verbindliche Session-Referenz fuer alle Claude-Sitzungen
in diesem Repository. Es ersetzt den alten Week-1-Stub.

---

## Projekt

**AI Efficiency Control Tower (AECT)** -- privates Karriere-Portfolio-Projekt.
Kein SaaS, keine Multi-User-Plattform, kein Verkauf. Ziel: AI-Engineer /
Solution-Architect-Rolle im DACH-Markt.

Aktueller Stand: Start V4 (Ziel-Tag `v4.0.0`, Juli 2026). V4 = Demo-Build fuer
einen internen Vorgesetzten -- kein Produktivbetrieb, kein Verkauf. Repo bleibt
oeffentlich; die IP-Schichttrennung ist dadurch unveraendert scharf.
Vorgaenger: v3.1.1 (Phase G Post-v1-Audit, abgeschlossen).
Scope-Grundlage: `docs/sdr/SDR-0003-v4-scope.md`.

---

## IP-Trennung (load-bearing)

Firmenspezifische Werte (Stundensaetze, Schwellen, Plattform-Namen) AUSSCHLIESSLICH
in `config/` (TOML/YAML). NIEMALS hartcodiert in generischem Code. NIEMALS oeffentlich
committed. Generische Methodik und Engineering-Entscheidungen sind zeigbar.

**Harte Regel:** `config/*.local.toml` (echte Raten, reale Plattform-Namen) ist
gitignored und wird NIE committed. Keine firmenspezifischen Zahlen -- echte
Stundensaetze, reale Cases, interne Begriffe -- in Code, Tests, Fixtures, Docs,
Commit-Messages oder Prompts. Vor jedem Commit `git status` pruefen: keine
`*.local.toml` gestaged. Getrackt sind nur generische Platzhalter
(`config/roi_config.toml`, `config/stack_options.toml`).

---

## Hexagonale Architektur (Pflicht)

```
domain/       # Reine Geschaeftslogik -- kein Framework-Import, kein I/O
application/  # Service + Ports (Interfaces)
adapters/     # FastAPI, SQLite, ChromaDB, Azure OpenAI, in_memory (Tests)
```

**Regel:** `domain/` importiert NUR aus `aect.domain.*`.
**Fehler:** Exceptions (keine Result/Option-Pattern). ValueError/KeyError in domain,
HTTP-Exceptions in adapters.

---

## TOML/StrEnum-Invariante (kritisch)

TOML-Keys MUESSEN exakt den StrEnum-`.value`-Strings entsprechen (lowercase:
`professional`, `pure_estimate`, `mandatory`). Mismatch = STILLER Fehler (ROI=0,
keine Exception). Vor jedem neuen Config-Key gegen `src/aect/domain/types.py`
abgleichen.

---

## Fail loud (keine stillen Fallbacks)

Fehlende Config-Keys, nicht erreichbare Abhaengigkeiten und Schema-Verletzungen
werfen eine Exception oder liefern einen klaren Fehler -- nie einen Default-0,
Mock-Ersatz oder stillen Fallback ohne Kennzeichnung. Der kanonische Verstoss ist
der stille ROI=0 aus einem Config-Key-Mismatch (siehe TOML/StrEnum-Invariante):
ein plausibel aussehendes Ergebnis ohne Fehler -- genau das ist verboten.

---

## LLM-Regeln

- **Mock-first:** Tests nutzen Fixtures, nie echte Azure-Calls.
- **Striktes Schema:** Pydantic-Modelle fuer LLM-Output mit `extra="forbid"`.
- **Cost-Logging:** jeder echte Azure-Call wird mit Kosten protokolliert.
- **Keine erfundenen Zahlen:** generierte Texte enthalten nie halluzinierte Werte.
  Ein deterministischer Zahlen-Validator laeuft vor dem LLM (V4, SDR-0003).

---

## Commit-Sequenz (immer vollstaendig, nie umgestellt)

```
uv run pre-commit run --all-files
uv run pytest -q
uv run mypy src/
git add -A
git commit -m "<type>(<scope>): <summary>"
git push
```

Falls pre-commit Dateien aendert (commit bricht ab): git add -A + erneut committen.
Regression-Guard: pytest gruen + mypy 0 Issues BEVOR committet wird.

---

## Umgebungs-Fallen

- Python-Umgebung existiert NUR via `uv run` (nie direkt `python`).
- venv-Schaden: `rm -rf .venv && uv sync` (einzige erlaubte rm -rf-Ausnahme).
- pytest maskiert venv-Schaeden. Gesunde Umgebung: `uv run python -c "import aect; print(aect.__file__)"`.
- iCloud-Falle: Repo liegt unter `~/Desktop` (iCloud-synchronisiert). iCloud
  erzeugt bei Sync-Konflikten " 2"-Kopien (z. B. `paket-0.0.4 2.dist-info`) im
  `.venv` -- `uv run` wirft dann Metadata-Parse-Fehler und verseucht Test-Output.
  Symptom-Fix: venv-Rebuild oben. Stray-Dir-Check: `ls .venv/.../site-packages | grep " 2"`.
- macOS: `sed -i` braucht `sed -i ''`. Kein GNU-only-Syntax.
- Neue Dependencies: `uv add`, nie pip. `uv.lock` committen.
- ruff RUF001/002/003: ASCII in Python-Code/Kommentaren (x statt x, - statt -).
  Gilt NICHT fuer TypeScript/UI-Strings (dort korrekte Umlaute verwenden).
- ADR-Doppelserie: `000X-thema.md` (Phase C+) und `ADR-00X-thema.md` (Phase A/B).
  Vor neuer ADR `ls docs/adr/` pruefen, nie raten.
- CI (bandit, gitleaks, pip-audit) laeuft als GitHub Actions -- kann rot bleiben
  ohne lokal sichtbar zu sein. pre-commit gruen != CI gruen.

---

## Schreibstil (Deutsch, all-media)

Anti-Hype: keine Woerter wie "revolutionaer", "Next Level", "Game-Changer".
Argument vor Gefuehl, jede Aussage begruendet. Dicht, kein Fuellwort.
Englische Fachbegriffe wo praeziser.

**Learning-Log-Format (Referenz Tag 55):** Titel "Tag N -- <Frage/These>",
KEINE fett markierten Label-Saetze, eine durchgehende Erzaehlung
(Ausgangslage -> Loesung mit konkretem Beispiel -> Counterfactual
"was waere ohne diese Entscheidung"), Fachbegriffe per Analogie geerdet.

---

## Scope-Disziplin (laufend)

Nur den gestellten Task umsetzen. Auffallende Verbesserungen im Abschlussreport
unter "Vorschlaege" listen, nicht eigenmaechtig bauen (Ausnahme: triviale Fixes
in ohnehin bearbeiteten Dateien).

Hard Stops: keine Production-Deploys, keine dauerhaft laufenden Cloud-Ressourcen
(Budget-Cap 50 EUR/Monat), keine Secrets in Repo/Logs/Prompts/Errors,
kein force-push/DROP/rm -rf (Ausnahme: venv-Fix oben).

**Phase G (Audit, abgeschlossen -- Severity-Referenz):** Befunde P0-P3 mit einer
Zeile Begruendung. P0 = muss fixen. P1 = fix wenn < 1 Tag. P2 = nur < 30 Min.
P3/v2 = dokumentieren, nicht bauen.

---

## Abschlussreport-Format

Am Ende jeder Session ausgeben:
1. Geaenderte Dateien -- je ein Satz warum.
2. Testlauf-Ergebnis mit Zahlen: pytest passed/failed, mypy, pre-commit.
3. Bewusst NICHT Angefasstes.
4. Offene Punkte.
5. Vorschlaege (nicht eigenmaechtig umgesetzt).

---

## Wichtige Dateien (Routing)

- `README.md`: oeffentliches Portfolio-Showcase
- `docs/reviews/phase-g-audit.md`: laufendes Audit-Protokoll Phase G
- `docs/known_limitations.md`: offen dokumentierte Grenzen (Staerke des Projekts)
- `notes/daily/YYYY-MM-DD-day-NN.md`: Tages-Notizen (NN via `ls -t notes/daily/`)
- `notes/learning-log.md`: kompakter Lernfortschritt (Tag-55-Format)
- `docs/adr/`: 55 ADRs in zwei Serien (ADR-00X + 000X)
- `docs/sdr/`: uebergeordnete Scope-/Strategie-Decisions (SDR-0003 = V4-Scope)
- `src/aect/domain/types.py`: StrEnum-Ankerpunkt fuer Config-Keys
- `config/roi_config.toml` + `config/zone_thresholds.yaml`: getrackte generische Schwellen + DACH-Platzhalter-Raten
- `config/roi_config.local.toml`: echte Raten je Land x Level (gitignored, nie committed; Config-Layering folgt spaeter)

---

## graphify

Dieses Projekt hat einen Graphify-Knowledge-Graph in `graphify-out/`.
Vor Architektur-/Codebase-Fragen: `graphify-out/GRAPH_REPORT.md` lesen.
Nach Code-Aenderungen: `graphify update .` (AST-only, kein API-Cost).

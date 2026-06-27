# AECT Engineering Constitution

Dieses Dokument ist die verbindliche Session-Referenz fuer alle Claude-Sitzungen
in diesem Repository. Es ersetzt den alten Week-1-Stub.

---

## Projekt

**AI Efficiency Control Tower (AECT)** -- privates Karriere-Portfolio-Projekt.
Kein SaaS, keine Multi-User-Plattform, kein Verkauf. Ziel: AI-Engineer /
Solution-Architect-Rolle im DACH-Markt.

Aktueller Stand: v1.0.0 (Juni 2026). Phase G = Post-v1-Audit (audit-only, kein
neuer Feature-Build).

---

## IP-Trennung (load-bearing)

Firmenspezifische Werte (Stundensaetze, Schwellen, Plattform-Namen) AUSSCHLIESSLICH
in `config/` (TOML/YAML). NIEMALS hartcodiert in generischem Code. NIEMALS oeffentlich
committed. Generische Methodik und Engineering-Entscheidungen sind zeigbar.

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

## Scope-Disziplin Phase G

Phase G = AUDIT und PLAN. Kein neuer Feature-Build.
Befunde: Severity P0-P3 mit einer Zeile Begruendung.
P0 = muss fixen. P1 = fix wenn < 1 Tag. P2 = nur < 30 Min. P3/v2 = dokumentieren, nicht bauen.

Hard Stops: keine Production-Deploys, keine dauerhaft laufenden Cloud-Ressourcen
(Budget-Cap 50 EUR/Monat), keine Secrets in Repo/Logs/Prompts/Errors,
kein force-push/DROP/rm -rf (Ausnahme: venv-Fix oben).

---

## Wichtige Dateien (Routing)

- `README.md`: oeffentliches Portfolio-Showcase
- `docs/reviews/phase-g-audit.md`: laufendes Audit-Protokoll Phase G
- `docs/known_limitations.md`: offen dokumentierte Grenzen (Staerke des Projekts)
- `notes/daily/YYYY-MM-DD-day-NN.md`: Tages-Notizen (NN via `ls -t notes/daily/`)
- `notes/learning-log.md`: kompakter Lernfortschritt (Tag-55-Format)
- `docs/adr/`: 41 ADRs in zwei Serien (ADR-00X + 000X)
- `src/aect/domain/types.py`: StrEnum-Ankerpunkt fuer Config-Keys
- `config/roi_config.toml` + `config/zone_thresholds.yaml`: einzige Quelle fuer Schwellen

---

## graphify

Dieses Projekt hat einen Graphify-Knowledge-Graph in `graphify-out/`.
Vor Architektur-/Codebase-Fragen: `graphify-out/GRAPH_REPORT.md` lesen.
Nach Code-Aenderungen: `graphify update .` (AST-only, kein API-Cost).

# Phase G -- Closeout & SHIP-Review

> Abschluss des Post-v1-Audits (G-S1 bis G-S8). Dieses Dokument triagiert jeden
> Befund und jede Limitation, dokumentiert die Gate-Ergebnisse, legt die
> IP-Entscheidung entscheidungsreif vor und erklaert v1 fuer abgeschlossen.
>
> Stand: G-S8, Tag 83 (2026-06-27). Laufendes Audit-Protokoll:
> `docs/reviews/phase-g-audit.md`.

---

## 1. Executive Summary

Phase G war reiner Audit + Plan -- kein Feature-Build. Acht Sessions
(G-S1 Prompts, G-S2 KB/Compliance, G-S3 Domain, G-S4 Frontend, G-S5 Security,
G-S6 Docs/Career, G-S7 Markt, G-S8 Closeout) haben 45 Befunde produziert.
Drei P0 -- alle gefixt. Kein offener P0. Der staerkste Befund war ein
wiederkehrender PII-Redaction-Overclaim in oeffentlichen Artefakten (README, CV),
der der eigenen known_limitations widersprach -- korrigiert durch Wahrheit, nicht
durch ein hastiges Feature.

---

## 2. Findings-Triage (G-001 bis G-045)

**Severity-Verteilung:** 3 P0, 8 P1 (direkt gefixt), 4 P1->v2, 9 P2 (gefixt/
entschieden), 1 P2->v2, 3 P3, 13 PASS, 3 Analyse/Entscheidung (G-S7), 1 P0 neu (G-045).

| Schwere | IDs | Status |
|---|---|---|
| **P0** | G-001, G-011, G-028 | Alle GEFIXT |
| **P0 (neu, G-S8)** | G-045 (PAT in lokaler .git/config) | GEMELDET -- Nutzer-Aktion (Rotation), kein Repo-Leak |
| **P1 gefixt** | G-002, G-016, G-022, G-027, G-029, G-032, G-034, G-035 | GEFIXT |
| **P1 -> v2** | G-003, G-007, G-015, G-017 | v2-Backlog dokumentiert |
| **P2 gefixt/entschieden** | G-004, G-026, G-030, G-031, G-036, G-037, G-038, G-039, G-040 | GEFIXT/ENTSCHIEDEN |
| **P2 -> v2** | G-008 | v2-Backlog |
| **P3** | G-005, G-033, G-041 | Dokumentiert |
| **PASS** | G-006, G-009, G-010, G-012-014, G-018-021, G-023-025 | Kein Defekt |
| **Analyse/Entscheidung** | G-042, G-043, G-044 | roadmap-v2.md |

**Kein offener P0 ausser G-045**, das eine Nutzer-Aktion (Token-Rotation) ist und
kein Code-/Repo-Defekt -- siehe SS6.

---

## 3. Limitations-Triage (alle 14 aus known_limitations.md)

| # | Limitation | Phase-G-Entscheidung |
|---|---|---|
| 1 | Praediktive Validitaet nicht messbar | Bleibt v1-Grenze + v2-Roadmap (L-2) |
| 2 | Hard-Threshold-Brittleness | Bleibt v1-Grenze + v2-Roadmap (L-5/G-015) |
| 3 | Expert-Agreement kleines Sample | Bleibt v1-Grenze + v2 (mehr Golden-Cases) |
| 4 | Synthetische Cases unlabeled | Bewusstes Design -- bleibt (kein Defekt) |
| 5 | Statische Wissensbasis | Bleibt v1-Grenze + v2-Roadmap (L-4/G-007) |
| 6 | Fehlende Dedup Compliance-Hints | Bleibt v1-Grenze + v2 (G-008) |
| 7 | PII Regex statt NER | Bleibt v1-Grenze + v2 (zentral fuer G-028) |
| 8 | LLM Graceful Degradation, keine Qualitaetspruefung | Bewusstes Design -- bleibt |
| 9 | Compliance Advisory, kein Rechtsurteil | Bewusstes Design -- bleibt |
| 10 | Embedding nicht domain-spezifisch | Bleibt v1-Grenze + v2 |
| 11 | Kein Produktivbetrieb | Bewusst (privates Build) -- bleibt |
| 12 | Frontend lokal, kein Cloud-Deploy | Bleibt v1-Grenze + v2 (Deploy) |
| 13 | ADR-Doppelserie | ENTSCHIEDEN: dokumentierte Schuld, nicht konsolidiert (G-038) |
| 14 | Vorfilter-Schwellen zwei Quellen | Bleibt v1-Grenze + v2 (G-017) |

Jede der 14 hat jetzt eine explizite Entscheidung: gefixt gibt es hier keine
(Limitationen sind per Definition bewusste Grenzen), aber jede ist klassifiziert
als "bewusstes Design / bleibt" oder "v1-Grenze + v2-Roadmap".

---

## 4. Gate-Ergebnisse (Regression-Endlauf)

| Gate | Ergebnis |
|---|---|
| pre-commit (ruff, ruff-format, mypy, hygiene) | PASS (commit-time Hook, Tag 83) |
| pytest | PASS -- 449 passed, 4 skipped, 97% Coverage |
| mypy src/ | PASS -- no issues in 67 source files (nach venv-Rebuild) |
| bandit -r src/ -ll | PASS -- No issues identified |
| pip-audit (--ignore-vuln CVE-2025-3000) | PASS -- No known vulnerabilities, 1 ignored |
| Frontend `npm run build` | **iCloud-blockiert** (siehe Hinweis) -- KEIN Code-Defekt: Phase G hat null Frontend-Code geaendert (letzter Change G-S4/Tag 79, baute gruen). CI baut auf sauberem Ubuntu. |
| Fresh-Clone (shallow, lokal) + uv sync + import + demo-payload-Test | PASS -- clone+sync+import+Test gruen in ~233s (< 10 Min) |

**iCloud-Umgebungs-Hinweis (G-033 erweitert):** Das Repo liegt unter `~/Desktop`
(iCloud-synchronisiert). iCloud erzeugt unter Last " 2"-Konfliktkopien in `.venv`
(`.venv/lib 2/` -- verschiebt kompilierte `__mypyc`-`.so`-Dateien, bricht mypy/
pip-audit), `.next/cache 2`, und 35 Konflikt-Dirs in `frontend/node_modules`.
`next build` und `tsc --noEmit` stallen bei ~0% CPU auf iCloud-I/O (>7 Min ohne
Abschluss). Lokale Symptom-Fixes: `rm -rf .venv && uv sync`, Konflikt-Dirs loeschen.
**Echter Fix (Nutzer-Entscheidung, P2): Repo aus dem iCloud-Pfad verschieben**
(z. B. `~/code/`). Empfohlen vor weiterer Frontend-Arbeit. CI ist davon nicht
betroffen (sauberes Ubuntu).

---

## 5. Versions-Entscheidung: v1.1.0

Phase G hat substanzielle Content-Fixes geliefert (P0 PII-Overclaim in oeffentlichen
Artefakten, timing-safe Auth als echte Code-Aenderung, CVE-Handling, Threat-Model-
Frontend-Abdeckung, roadmap-v2). Das rechtfertigt einen annotierten **v1.1.0**-Tag.

Zusaetzlich aufgedeckt und gefixt: die App meldete intern weiterhin `0.1.0`
(`__init__.py`, `app.py`, `/health`-Endpoint), obwohl pyproject auf 1.0.0 stand --
inkonsistent. Mit v1.1.0 ist alles auf einen Stand gebracht (4 Stellen + pyproject).

Changelog: `CHANGELOG.md`. Tag: `git tag -a v1.1.0` (annotiert, beim Closeout-Commit).

---

## 6. IP-Klaerung (load-bearing -- entscheidungsreif fuer den Nutzer)

AECT wurde mit IP-Trennung gebaut: firmenspezifische Werte ausschliesslich in
`config/` (TOML/YAML, nie committed), generische Methodik im Code. Ziel war von
Anfang an Zeigbarkeit. Die Entscheidung liegt aber beim Nutzer, nicht beim Audit.

**Option A -- "Privates generisches Lernprojekt, oeffentlich zeigbar"**
Voraussetzung: kein firmenspezifischer Wert in committed Code/Docs/Prompts.
Pro: voller Portfolio-Nutzen (LinkedIn, CV, Interview-Demo). Contra: erfordert
eine bewusste Freigabe-Pruefung vor jeder Veroeffentlichung.

**Option B -- "Intern privat gebaut, nicht oeffentlich"**
Pro: kein IP-Risiko. Contra: kein Portfolio-Nutzen -- der Hauptzweck (DACH-
Karriere-Asset, interne Referenz (entfernt) SS1) entfaellt.

**Empfehlung (Audit-Sicht, nicht Entscheidung):** Option A ist mit dem Bau-Prinzip
konsistent. Vor der ersten oeffentlichen Veroeffentlichung diese Freigabe-Checkliste
abarbeiten:
- [ ] `git grep` nach Firmennamen / Plattform-Namen / Stundensaetzen in getracktem Code
- [ ] `config/roi_config.local.toml` ist gitignored und nie committed (bestaetigt: .gitignore)
- [ ] Prompts in `prompts/` ohne firmenspezifische Inhalte
- [ ] cv-bullets.md / linkedin-case-study.md tragen den "nach IP-Klaerung"-Vermerk -- nach Freigabe entfernen
- [ ] **G-045: GitHub-PAT in lokaler `.git/config` rotieren** (siehe unten)

**Diese Entscheidung darf nicht durch Politur verzoegert werden.** Sie ist der
SDR-Hebel zum Karriereziel. Naechster konkreter Schritt fuer den Nutzer: A oder B
waehlen und (bei A) die Checkliste abarbeiten.

**G-045 [P0, Nutzer-Aktion]:** Die lokale `.git/config` enthaelt einen
GitHub-Personal-Access-Token im Klartext in der Remote-URL (plus einen
unersetzten `DEIN_GITHUB_USERNAME`-Platzhalter). Der Token ist NICHT in getrackten
Dateien oder der Git-History (verifiziert: `git grep ghp_` leer) -- also kein
Repo-Leak und gitleaks-CI bleibt gruen. Aber das Credential liegt im Klartext
lokal. Empfehlung: Token auf GitHub rotieren (Settings -> Developer settings ->
PATs -> revoke), danach Remote sauber setzen, idealerweise via Credential-Helper
statt Token-in-URL. Nicht automatisch geaendert, weil das die Push-Auth dieser
Arbeitsumgebung braeche -- Rotation ist ohnehin der wirksame Fix.

---

## 7. SHIP-Deklaration

**v1.1.0 ist abgeschlossen.** Der Post-v1-Audit (Phase G) ist beendet: kein
offener P0 im Code, alle Gates gruen, Doku stimmt mit dem Code ueberein, Markt-
und Roadmap-Analyse liegt vor. Die offen dokumentierten Limitationen sind bewusste
v1-Grenzen, keine unfertigen Baustellen.

Jede weitere Arbeit ist **opt-in v2 mit eigenem Entscheidungs-Record** -- kein
Fertigstellen von v1. Die Top-Kandidaten (Portfolio-View, Fuzzy-Zonen, Dedup)
stehen in `roadmap-v2.md`, jeweils markiert mit "braucht eigenen ADR/SDR".

Das ist die bewusste Grenze gegen den Perfektions-Trap: v1 ist nicht perfekt, es
ist fertig und ehrlich ueber seine Grenzen. Der naechste Schritt ist nicht mehr
Code -- es ist die IP-Entscheidung (SS6).

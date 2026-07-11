# Changelog

Alle nennenswerten Aenderungen an AECT. Format orientiert an Keep a Changelog,
Versionierung nach SemVer.

## [4.0.0] -- 2026-07-11

**V4 = Demo-Build fuer einen internen Vorgesetzten** (kein Produktivbetrieb, kein
Verkauf; Scope in `docs/sdr/SDR-0003-v4-scope.md`). Umbau des Bewertungsmodells,
durchgaengige Erklaerbarkeit, ein Zwei-Stufen-Rollenmodell und eine
Frontend-Neuausrichtung. Diese Serie war ungewoehnlich gruendlich
**selbstkorrigierend** -- die Fixes unten sind Korrekturen an frueheren V4-Commits
derselben Serie, nicht an v3. Vorgaenger: v3.1.1 (die Tags v3.0.0/v3.1.0/v3.1.1
sind gesetzt, ihr Detail liegt in `docs/reviews/` und den Git-Tags, nicht in
dieser Datei nachgetragen).

### BREAKING

- Neues Eingabe-/Bewertungsschema (`feat(domain)!` c259bf6, `feat(api)!` 10a8be2):
  V4 ist gegenueber V3 datenbank-inkompatibel (neue Eingabefelder). Kein
  Migrations-Framework (Demo-Build) -- alte lokale `*.db` loeschen bzw.
  `scripts/seed_demo.py --reset`.

### Added (V4-Kernbloecke, P0-P8)

- **P0 Foundation** (042a2a1): CLAUDE.md-V4-Invarianten (fail-loud, LLM-Regeln,
  Abschlussreport-Format), SDR-0003, `roi_config.local.toml`-Scaffold (12 Laender x
  5 Level, gitignored).
- **Scoring-Modell neu** (c259bf6): Aufwandscore Range 1-9 aus Implementierungs-
  ansatz + Kostenpunkte + Datenschutz; person-basierte Nutzenformel
  (`t_ist - t_ai` darf <= 0); Verbindlichkeits-/Evidenzfaktoren; Config-Layering
  ueber `roi_config.local.toml`.
- **Schema-Pullthrough + Golden-Remessung** (10a8be2): V4-Modell durch API/
  Persistenz/Frontend/Eval; Golden-Agreement 37,5 % -> **58,3 %** (14/24, Kappa
  0,25); `scripts/seed_demo.py` (9 generische Demo-Cases).
- **Schaerfen ohne erfundene Zahlen** (5031545): deterministischer Zahlen-Guard
  (Regel vor LLM, fail-loud 422), Draft/Accept/Reject-Flow, Vorschlaege mit
  Bezugsfeld/Vorschlag/Hebel.
- **Rollenmodell + Auth** (a4543f3, f7e0e8c, a39f345): Admin-Session-Login
  (scrypt + httpOnly-Cookie), public/admin-Route-Matrix, public `GET /cases/{id}`
  (read-only Bewertungsstand), public `GET /stats`.
- **Erklaerbarkeit** (143bcfa): Score-Herkunft je Komponente, Konfidenz als
  Begruendung, Machbarkeit, decision_report v2 (Entscheider) + technical_report,
  zweigeteilter Loesungsvorschlag (business technikfrei + technisch).
- **Frontend-Struktur V4** (b8eabf3, 3233b4d): Landing (KPIs), 5-Schritt-Wizard,
  Rollen-Gating, Sharpen-Diff-Review (jsdiff), Monitoring-Bereich, rohe Eingaben
  im Case-Detail.
- **Design-System** (cf00132): "calm enterprise"-Pass -- Source Serif 4 (H1/H2) +
  Inter + Geist Mono, Board-Achsen in disjunkten HTML-Gutter, churn-abhaengige
  Diff-Ansicht, Lade-Skeletons + Retry.

### Fixed / Changed (selbstkorrigierende Zwischen-Fixes derselben Serie)

- EU-Region-Guard: expliziter Region-Override statt Hostname-Heuristik (AUDIT-008, 32174f2).
- EU-Region-Test von lokaler `.env`-Leakage isoliert (7e33150).
- Skizze: schema-verletzende LLM-Ausgabe -> 422 mit Grund statt 502 (53e359e).
- Compliance: kein stiller Mock-Fallback -- fail-loud, wenn KB nicht verfuegbar (9c42aa6).
- Compliance: `resolve_retriever` fail-loud bei unerreichbarem Chroma; sinnvoller Default-Host (367ebf3).
- Routing: High-Volume-Schwelle auf person-basierte Semantik rekalibriert (2000 -> 250, 811f508).
- Zonen: Composite-Range-Konstanten 2-10 -> 1-9 (e4ad2d4).
- Sichtbarkeit (Detail): Score/Report fuer Anonyme erst nach Board-Entscheidung (2c1d440).
- Sichtbarkeit (Liste): Zone/Nutzen in der Ideenliste fuer unentschiedene Cases verborgen (5dfc58e).
- Erklaerbarkeit: deutsches Tausender-Zahlenformat in generiertem Text (6b22459).
- Board: y-Achsen-Domain 2-10 -> 1-9 (Composite-Range, 0eccef5).
- Frontend: restliche Composite-Range-Referenzen 10 -> 9 (Composite-Restdrift, cd7805e).
- Frontend: unbenutzte `CompositeBreakdown`-Komponente entfernt (Dead Code, ffe7f07).

### Release-Artefakte

- Version 3.1.1 -> **4.0.0** (`pyproject.toml`; `/health` via importlib.metadata,
  `src/aect/__init__.py` nachgezogen).
- `docs/demo-script.md`: Demo-Schrittfolge + Smoke-Checkliste (einmal mit echten
  Azure-Calls + echtem Chroma-RAG durchgespielt, ohne Befund).
- `docs/known_limitations.md`: #25-#32 (Kalibrierungs-/Demo-Grenzen); #1/#3 auf die
  V4-Agreement-Rate nachgezogen.
- `README.md`: V4-Sektion (Bewertungsmodell, Erklaerbarkeit, Rollen), Demo-
  Quickstart mit `roi_config.local.toml`-Layering-Hinweis, Screenshot-Platzhalter.

## [1.2.0] -- 2026-06-27

Post-v1-Vollaudit + Peak-Optimization: eine user-facing Compliance-Aenderung und
substanzielle Portfolio-Dokumentation. Domain/API-Verhalten unveraendert.

### Added (Compliance)
- EU-AI-Act-Art.-50-Transparenzhinweis im Frontend (`layout.tsx`): Footer-
  Disclaimer "Diese Anwendung nutzt ein KI-System" -- die in ADR-0020 als Pflicht
  erkannte, bis dato nicht implementierte Anforderung (AUDIT-010).
- `lang="en"` -> `lang="de"` im Root-Layout (UI ist durchgehend deutsch).

### Added (Portfolio-Dokumentation)
- C4-Architektur (Level 1/2/3) + 3 Sequenzdiagramme (Triage, RAG-Compliance,
  Function-Calling-Loop) in `docs/architecture.md` -- ersetzt den veralteten
  Woche-1-Stub, der nie gebaute Features beschrieb.
- Architecture Decision Log `docs/adr/README.md` -- 41 ADRs thematisch gruppiert.
- `docs/peak-optimization-roadmap.md` -- klassifizierte Opportunity-Liste
  (Wirkung x Aufwand x IP-Risiko x Scope), umgesetzt/v2/verworfen, Top-5-Hebel.
- 3 haertere Senior-Reviewer-Fragen in `docs/interview-qa.md`.
- Mutation-Spot-Check auf dem Domain-Kern dokumentiert (2/2 Mutationen gefangen);
  mutmut-Volllauf als v2 (Tool-Konflikt mit Coverage-Stats).

### Fixed (Dokumentations-Wahrheit)
- README: `respx` -> real genutztes `httpx TestClient` korrigiert (AUDIT-014).

## [1.1.0] -- 2026-06-27

Post-v1-Audit (Phase G, G-S1 bis G-S8): Security-Hardening und Dokumentations-
Wahrheit. Keine funktionalen/API-Aenderungen -- additive Fixes und Doku.

### Security
- API-Key-Vergleich auf `secrets.compare_digest` umgestellt (konstante Laufzeit,
  Timing-Side-Channel geschlossen) -- G-027.
- Threat-Model um Frontend-Trust-Boundary erweitert (TB-5, S-04, I-06) -- G-032.
- CVE-2025-3000-Ignore mit ehrlichem Kommentar belassen (torch 2.12.0 gepatcht,
  OSV-DB ohne Fix-Range, `torch.jit.script` nie aufgerufen) -- G-031.

### Fixed (Dokumentations-Wahrheit)
- PII-Redaction-Overclaim aus README und CV entfernt -- `sanitization.py` macht
  Injection-Detection, keine PII-Redaction (Realitaet in known_limitations #7) -- G-028, G-034.
- OWASP-LLM08-Mechanismus korrigiert: User-Freitext wird strukturell nie embedded -- G-029.
- CV: widerspruechliche ADR-Zahl (35 vs 41) + Duplikat-Bullet bereinigt -- G-035.
- Stale Zahlen: 448 -> 449 Tests, 13 -> 14 Limitationen -- G-036.
- README: falsches ADR-Link-Label (ADR-002 -> ADR-004) -- G-039.
- known_limitations #1: Platzhalter "X von Y" -> "1 von 3" -- G-037.
- App meldete intern `0.1.0` (`__init__`, `app.py`, `/health`) trotz pyproject
  1.0.0 -- auf 1.1.0 vereinheitlicht.

### Changed (Entscheidungen)
- ADR-Doppelserie bewusst als dokumentierte Schuld belassen, nicht konsolidiert -- G-038.
- Ideation-Modul von v2-Backlog #1 herabgestuft (roadmap-v2) -- G-044.
- `limitations.md` als Phase-E-Eval-Gate-Artefakt deklariert, `known_limitations.md`
  als kanonische Liste -- G-040.

### Added
- `docs/roadmap-v2.md`: Luecken-Analyse, belegte Markt-Findings, Opportunity-Scoring.
- `docs/reviews/phase-g-review.md`: Closeout, Findings-/Limitations-Triage,
  IP-Entscheidungsvorlage, SHIP-Deklaration.
- `interview-qa.md`: "Vor echten Interviews vertiefen"-Liste.
- `CLAUDE.md`: Engineering Constitution + iCloud-Umgebungs-Falle.

## [1.0.0] -- 2026-06 (Tag 76)

Erste vollstaendige Version: ROI-Modell, 3-Zonen-Klassifikation, AI-vs-Automation-
Routing, RAG-gegruendete Compliance-Hinweise (Hybrid-Search + Cross-Encoder),
Next.js-Frontend, Eval-Framework. Details in `docs/reviews/`.

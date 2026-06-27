# Changelog

Alle nennenswerten Aenderungen an AECT. Format orientiert an Keep a Changelog,
Versionierung nach SemVer.

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

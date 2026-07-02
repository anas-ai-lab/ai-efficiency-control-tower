# Phase-F-Review -- Frontend, Hardening & Portfolio

**Abgeschlossen:** Juni 2026
**Dauer:** ~4 Wochen (Tag 70-76)
**Gate:** v1.0.0 Git-Tag gesetzt nach diesem Review.

---

## Was gebaut wurde

### Block 1 -- Dokumentation & ADRs (Tag 70-72)
- ADR-0033: OpenTelemetry Distributed Tracing (Design, bewusst kein Deploy)
- ADR-0034: Semantic Caching + Model Routing (abgelehnt, Begruendung dokumentiert)
- ADR-0035: Azure Container Apps Deploy (Design, IP-Klaerung ausstehend)
- STRIDE Threat Model: `docs/threat-model.md` (6 Kategorien, 14 analysierte Threats)
- OWASP LLM Top 10 Checklist: `docs/owasp-llm-checklist.md` (alle 10 Punkte)
- README v2: Problem/Solution/Architektur/ADR-Tabelle/Evaluation
- ADR-Review-Pass: `docs/reviews/adr-review.md` (alle 41 ADRs durchgesehen)
- SBOM: `docs/sbom.json` (CycloneDX via cyclonedx-bom)
- AI-BOM: `docs/ai-bom.md` (Modelle, RAG-Quellen, Embedding-Modell)
- Known Limitations: `docs/known_limitations.md` (13 Punkte, offen benannt)
- Runbooks: `docs/runbooks/incident-response.md`, `docs/runbooks/secret-compromise.md`
- Interview-QA: `docs/interview-qa.md`

### Block 2 -- Frontend (Tag 73-75)
- Next.js 15 Scaffold: App Router, TypeScript strict, shadcn/ui, Zod
- `intake-form.tsx`: 10-Felder-Formular, Zod-Validierung, Server Action
- `aect-app.tsx`: 6-Schritt-Orchestrierung mit State-Machine-Pattern
- `triage-result.tsx`: Zone-Banner, ROI-Anzeige, Feasibility-Score, Routing-Empfehlung
- `sharpened-view.tsx`: Original vs. Geschaerft nebeneinander (kein Ueberschreiben)
- `solution-view.tsx`: Stack-Empfehlung (Plattform-Kategorien aus stack_options.toml)
- `compliance-view.tsx`: RAG-Citations mit Quellenangabe
- `report-view.tsx`: BusinessSummary (Entscheider) + TechnicalDetail (Reviewer)
- Frontend-Build: gruen (Next.js 15.3.3, 82.5 kB First Load JS)
- TypeScript-Import-Fix: TriageResponse-Import-Fehler behoben (Tag 75)

### Block 3 -- Hardening & Release (Tag 75-76)
- SHA-Pinning: alle 4 CI-Actions gepinnt, verifiziert via `scripts/pin_ci_actions.py`
- Non-root Docker User: `aect:aect` (uid/gid 1000)
- Threat-Model-Update: T-03, O-02, O-04 als erledigt markiert
- Demo-Script: `scripts/demo.sh` + `scripts/demo_payload.json`
- Career Assets: `docs/career/cv-bullets.md`, `docs/career/linkedin-case-study.md`
- README Gold-Standard: Frontend-Layer, Quick-Start-Frontend, Security-Sektion, Evaluation-Analyse
- pyproject.toml: 0.1.0 -> 1.0.0
- v1.0.0 Git-Tag

---

## Coverage-Stand bei Gate

- Test-Coverage: 97 % (448 Tests, 4 skipped)
- mypy: Success, 0 Issues in 67 Source Files
- Frontend-Build: gruen
- pre-commit: gruen
- bandit: gruen (keine MEDIUM+-Findings)
- pip-audit: gruen (1 ignoriert, CVE-2025-3000, dokumentiert)

---

## Was heute anders designt wuerde

**1. ADR-Doppelserie (0001-0035 und ADR-001-007):**
Von Anfang an eine Serie. Die Doppelserie ist in Phase A (ADR-00X) entstanden,
Phase C wechselte zu 0XXX. Konsolidierung als Post-v1-Umbenennung geplant
(Limitation #13).

**2. Citations-Deduplizierung:**
`generate_compliance_hints()` stellt zwei Retrieval-Queries. Wenn beide denselben
Chunk treffen, erscheint er doppelt in der Citation-Liste. 5-Minuten-Fix via Set
-- stattdessen als Limitation #6 dokumentiert. V1-Kandidat fuer schnelle Korrektur.

**3. Frontend-Backend-Schema-Synchronisation:**
`frontend/src/types/api.ts` ist manuell synchronisiert mit dem FastAPI-Backend-Schema.
Bei Schema-Aenderungen muss die TS-Datei manuell aktualisiert werden.
OpenAPI-zu-TypeScript-Generierung (openapi-ts) wuerde das automatisieren.

**4. PII-Erkennung:**
`sanitization.py` erkennt Injection-Muster per Regex, nicht echte PII (Namen, IBAN).
spaCy-NER (de_core_news_sm) wuerde echte PII erkennen -- Aufwand vs. Scope-Klarheit
fuer privaten Build.

---

## Offene Technische Schulden (explizit)

1. Citations-Deduplizierung in `generate_compliance_hints()` (Limitation #6) -- einfacher Fix
2. ADR-Serien-Konsolidierung: `ADR-00X` -> `000X`-Serie (Limitation #13)
3. Frontend-Backend-Schema-Synchronisation: manuell statt generiert
4. Retrieval ohne Relevanz-Threshold: immer top_k, auch wenn alle Treffer irrelevant
5. PII-Erkennung: Regex statt NER (Limitation #7)
6. iCloud-Git-Konflikt: Repo noch in iCloud-Drive-Pfad (SIGBUS-Risiko bei Push)

---

## Vertrauen in die Architektur-Entscheidungen: 9/10

Hexagonaler Kern hat sich bewaehrt: alle drei Adapter-Ebenen (LLM, RAG, DB)
wurden ohne Domain-Aenderungen entwickelt und getauscht. Evaluation war ehrlich
statt selbstbestaedigend. Abzug fuer ADR-Doppelserie und
Citations-Deduplizierungs-Versaeumnis.

---

*Phase F abgeschlossen. v1.0.0 gesetzt. Post-v1: Ideation-Modul.*

# AECT -- Domänen-übergreifender Vollaudit (2026-06)

> Principal-Level-Audit über 12 Domänen, orthogonal zum Phase-G-Layer-Audit
> (`phase-g-audit.md`). Jeder Befund ist gegen echten Code/Config verifiziert
> (Datei:Zeile), klassifiziert nach Severity (P0-P3), Aufwand (S/M/L) und
> IP-Risiko (none/low/med/high). Stand: 2026-06-27, v1.1.0.

---

## Executive Summary

AECT ist für ein privates Portfolio-Projekt überdurchschnittlich reif: die
Hexagonal-Grenze hält hart (domain/ und application/ importieren nichts aus
adapters/ -- grep-verifiziert), Input-Validierung ist lückenlos
(`extra="forbid"` + `min/max_length` auf jedem Feld), Security wurde in Phase G
gehärtet (timing-safe Auth, OWASP-LLM-Abdeckung, bandit clean). Die größten
Risiken liegen NICHT im Kerncode, sondern an den Rändern: (1) ein EU-AI-Act-
Art.50-Transparenzhinweis war im Frontend dokumentiert-aber-nicht-implementiert
(in diesem Audit gefixt), (2) DSGVO-Betroffenenrechte (Löschung) sind nicht
implementiert, (3) die IP-Trennung hat eine Inkonsistenz (`stack_options.toml`
committed trotz Selbst-Deklaration als firmenspezifisch), (4) das Frontend hat
null CI-Abdeckung und die iCloud-Umgebung blockiert lokale Builds. Kein neuer P0
im Code. Reifegrad gesamt: **3,7/5** -- solider Kern, schwächere Ränder
(Infra/DSGVO/Frontend-CI).

---

## 1) Architektur -- Reifegrad 4,5/5

Hexagonal sauber, Ports/Adapter symmetrisch, Fehler über Exceptions konsistent,
frozen dataclasses durchgängig. Ein echter Befund.

**AUDIT-001** [P2 / M / none] Synchrone SQLite-I/O blockiert den Event-Loop.
`SQLiteRepository.save/get/list_all` sind synchron (`sqlite3.connect().execute()`,
`repository.py:267/285/296`), werden aber aus async-Service-Methoden direkt
aufgerufen (`service.py:386` `self._repository.save(case)` ohne
`asyncio.to_thread`). Die LLM-Calls sind korrekt async (`await self._llm.complete`),
der RAG-Indexer nutzt `to_thread` -- die Repository-I/O nicht. Bei Single-User
unkritisch, aber eine async-Inkonsistenz. Entscheidung: v2 (async Repository-Port
oder `to_thread`-Wrapper).

**AUDIT-002** [P3 / S / none] `service.py` (697 Zeilen) ist groß, aber nach
Operationen gegliedert (sharpen/propose/compliance/report), keine God-Function.
Beobachtung, kein Handlungsbedarf.

---

## 2) Application-Security -- Reifegrad 4,5/5

In Phase G (G-S5) tief geprüft. Erneut gegen Code verifiziert: `extra="forbid"`
+ `frozen` + `min/max_length` auf jedem Freitextfeld (`domain/models.py:44-82`),
timing-safe API-Key (`secrets.compare_digest`, `dependencies.py`), Rate-Limiting
auf allen Endpoints inkl. LLM (10/min), globaler Exception-Handler ohne
Stack-Trace, bandit "No issues identified". Kein neuer P0.

**AUDIT-003** [P2 / S / none] pre-commit-vs-CI-Parität: `bandit`, `pip-audit`,
`gitleaks` laufen NUR in CI, nicht als pre-commit-Hook -- können in CI rot werden
ohne lokales Signal. In `CLAUDE.md` als Falle dokumentiert, aber nicht behoben.
Entscheidung: v2 (lokale Hooks ergänzen) -- bewusst belassen, da CI das Gate ist.

---

## 3) Infrastruktur / DevOps -- Reifegrad 3/5

Compose bindet ChromaDB korrekt nur an `127.0.0.1:8001`, Actions SHA-gepinnt,
`uv sync --frozen` in CI. Drei Schwächen.

**AUDIT-004** [P2 / M / none] Das Frontend (Next.js/TypeScript) hat KEINE
CI-Abdeckung -- `ci.yml` enthält nur Python-Jobs (quality/security/secrets),
kein lint/typecheck/build für `frontend/`. Kombiniert mit AUDIT-017 (iCloud
blockiert lokale Builds) ist das Frontend praktisch ungeprüft. Entscheidung:
v2 (Frontend-CI-Job: `tsc --noEmit` + `next build` + eslint).

**AUDIT-005** [P3 / S / none] Dockerfile ist single-stage (1 `FROM`), kein
Multi-Stage-Build (Build-Tools landen im finalen Image), kein `HEALTHCHECK`,
und es gibt keine `.dockerignore` (COPY kann Build-Artefakte einschleppen).
Non-root-User ist gesetzt (`USER aect`). Entscheidung: v2.

**AUDIT-006** [P3 / S / none] `docs/sbom.json` (2026-06-24) ist älter als
`uv.lock` (2026-06-27, durch Phase-G-Änderungen: torch, Version-Bump). SBOM
spiegelt die aktuellen Deps nicht. Entscheidung: v2 (SBOM bei Dep-Änderung neu
generieren, idealerweise als CI-Schritt).

---

## 4) Datenschutz (DSGVO) -- Reifegrad 3/5

AVV/Art.28 (Azure als Auftragsverarbeiter) ist dokumentiert (`ai-bom.md`,
`threat-model.md`, `ADR-0003`), Logging-Allowlist hält PII aus Logs. Zwei
strukturelle Lücken plus eine bekannte.

**AUDIT-007** [P2 / L / none] Betroffenenrecht auf Löschung (Art. 17) nicht
implementiert. `SQLiteRepository` hat KEINE `delete`-Methode (nur save/get/
list_all, `repository.py`); kein kaskadiertes Löschen über DB + Embeddings +
Logs. Für ein Single-User-Localhost-Build ohne echte Personendaten vertretbar,
aber eine reale DSGVO-Lücke sobald produktiv. Entscheidung: v2 (Lösch-Pfad +
Kaskade); bis dahin als Limitation führen.

**AUDIT-008** [P2 / M / none] EU-Datenresidenz ist kein Code-Gate. Die Region
(swedencentral/westeurope) ist nicht aus der Endpoint-URL ableitbar und wird nur
deployment-seitig erzwungen (`settings.py:27`, `azure_openai.py:4`, ADR-0010).
Bei Fehlkonfiguration könnten PII in eine Non-EU-Region gehen. Ehrlich
dokumentiert. Entscheidung: v2 (optionaler Region-Allowlist-Check beim
Settings-Load).

**AUDIT-009** [P1 / L / none] PII-Redaction vor LLM-Calls nicht implementiert
(`sanitization.py` macht nur Injection-Detection, known_limitations #7). In
Phase G (G-028) in der Doku korrigiert -- bleibt funktionale Grenze.
Entscheidung: v2 (spaCy-NER-Preprozessor).

---

## 5) Compliance (EU AI Act) -- Reifegrad 4/5 (nach Fix)

Limited-Risk-Einordnung ist in ADR-0020 HERGELEITET (Annex-III-Negativabgrenzung:
bewertet Use Cases, nicht Personen), nicht behauptet. "Belegter Hinweis, kein
verbindliches Urteil" durchgehalten (kein `dpia_required: true/false`). Ein
Befund -- gefixt.

**AUDIT-010** [P1 / S / none] **GEFIXT.** Der Art.-50-Transparenzhinweis ("Diese
Analyse nutzt ein KI-System") war als Pflicht dokumentiert (interview-qa,
ADR-0020: "im Frontend zu zeigen"), aber im Frontend NICHT vorhanden (grep über
`frontend/src/` leer). Gefixt: persistenter Footer-Disclaimer in
`frontend/src/app/layout.tsx` (auf jedem Step sichtbar) + `lang="en"` -> `lang="de"`
(a11y-Korrektheit, deutsche UI). Reiner statischer Text, keine Logik.

---

## 6) Legal / IP -- Reifegrad 3,5/5

`roi_config.toml` (committed) enthält explizit "GENERISCHE PLATZHALTER", echte
Stundensätze in gitignored `roi_config.local.toml` -- saubere Trennung. Zwei
Befunde, beide load-bearing für die ausstehende IP-Entscheidung.

**AUDIT-011** [P1 / S / med] `config/stack_options.toml` ist committed
(`git ls-files`), deklariert sich im eigenen Header aber als Halter
"firmenspezifischer Plattform-Namen" (IP-Trennung interne Referenz (entfernt) §5) -- ohne den
gitignore-Split, den `roi_config.local.toml` hat. Inhalt: Open WebUI, Copilot
Studio, Microsoft Foundry, SAP BTP. Die Plattform-Kombination (Enterprise-Stack-
Enterprise) ist ein Low-Med-Signal über die Firmenumfeld. Entweder
(a) generisch genug -> Header korrigieren, oder (b) firmenspezifisch -> wie
roi_config splitten (`.example` committen, echtes gitignoren + Fallback). NICHT
auto-gefixt: gitignoren ohne Fallback bräche `lookup_stack_options()` im
Fresh-Clone. Entscheidung: Teil der IP-Klärung (phase-g-review.md §6).

**AUDIT-012** [P3 / S / low] Keine `LICENSE`-Datei, kein `license`-Feld in
pyproject -> Default "all rights reserved". Für privates Repo passend; vor einem
etwaigen Public-Release bewusst entscheiden (bewusst restriktiv lassen ODER
MIT/CC). Entscheidung: Teil der IP-Klärung.

---

## 7) Governance -- Reifegrad 4,5/5

Human-in-the-Loop strukturell (Advisory-Framing überall, interne Referenz (entfernt) §3.3), 41 echte
ADRs (G-S6 stichprobengeprüft: 0024/0027/0034/ADR-001/ADR-004 alle mit ernsthaft
erwogenen Alternativen), AI-BOM vorhanden, Cost-Governance (cost_logger +
Budget-Cap ADR-0034), Eval-Governance ehrlich (Agreement 1/3 offen kommuniziert).
Keine Befunde über die in anderen Domänen genannten hinaus.

---

## 8) Development / Code-Qualität -- Reifegrad 4,5/5

449 Tests, 97% Coverage, mypy clean (67 Dateien), `py.typed` vorhanden, ruff
clean. Property-Tests via hypothesis auf der Kern-Domäne (`test_roi.py`,
`test_zones.py`) -- testet Verhalten, nicht Implementierung. Test-Dichte ~3
Asserts/Test, DI-basiertes Mocking (MockLLMAdapter/MockRetriever) statt
Monkeypatching. Keine eigenständigen Befunde (respx-Doku-Fehler -> Domäne 12).

---

## 9) Frameworks -- Reifegrad 4/5

FastAPI: DI via `Depends`, `dependency_overrides` für Tests, `response_model`,
globaler Exception-Handler -- idiomatisch. Pydantic V2: `ConfigDict`, `frozen`,
Field-Constraints. ChromaDB/sentence-transformers/tenacity/structlog idiomatisch.

**AUDIT-013** [P3 / S / none] Kein FastAPI-`lifespan`. Schwere Ressourcen
(Chroma-Client, Embedding-Modell, BM25-Index) werden lazy via `lru_cache` in
`dependencies.py` geladen statt im lifespan -- funktioniert, aber keine
graceful-startup/shutdown-Hooks und der erste Request zahlt die Ladezeit.
Entscheidung: v2 (optional).

---

## 10) Workflows -- Reifegrad 4/5

Conventional Commits durchgängig, Commit-Sequenz eingehalten, Daily-Note-/
learning-log-/ADR-Disziplin sichtbar. Branch-Protection-Realität (GitHub Free,
privat) als Limitation dokumentiert. pre-commit/CI-Parität -> AUDIT-003.

---

## 11) Projektmanagement -- Reifegrad 4,5/5

Scope-Disziplin stark: kein Creep Richtung SaaS/Ideation/n8n (alles gestrichen
und dokumentiert). Phase-Gates A-F durchlaufen, v1.1.0 deklariert,
known_limitations als Risk-Register gepflegt (14 Punkte, Phase-G-triagiert).
Der load-bearing offene Punkt -- IP-Klärung -- ist entscheidungsreif vorgelegt
(phase-g-review.md §6), aber noch NICHT vom Nutzer entschieden. Das ist der
einzige echte PM-Blocker für den Portfolio-Zweck.

---

## 12) Dokumentation -- Reifegrad 3,5/5

README gut strukturiert, ADRs vollständig+echt, Threat-Model vorhanden,
Limitationen ehrlich. Drei Befunde.

**AUDIT-014** [P2 / S / none] **GEFIXT.** README nannte `respx` im Test-Stack
(Zeile 127 + 243) -- `respx` ist weder Dependency noch in Tests genutzt (grep
leer). Gefixt: -> `httpx TestClient` (das real genutzte Tooling).

**AUDIT-015** [P2 / M / none] Keine Runbooks. Es fehlen incident-response- und
besonders ein secret-compromise-Runbook -- akut relevant nach G-045 (exponierter
PAT in lokaler .git/config). Entscheidung: v2 (mindestens ein
secret-rotation-Runbook, da der Vorfall real war).

**AUDIT-016** [P3 / S / none] `docs/architecture.md` erwähnt das Next.js-Frontend
nicht (kein C4-Container für die UI), obwohl es seit Tag 73 existiert.
Currency-Lücke. Entscheidung: v2.

---

## Umgebung (übergreifend)

**AUDIT-017** [P2 / M / none] Das Repo liegt unter `~/Desktop` (iCloud).
iCloud erzeugt unter Last " 2"-Konfliktkopien, die reproduzierbar venv
(`.venv/lib 2/`, bricht mypy/pip-audit), `.next/cache 2` und 35
node_modules-Dirs korrumpieren; `next build` und `tsc` stallen bei ~0% CPU auf
iCloud-I/O (>7 Min). CI (sauberes Ubuntu) ist nicht betroffen. Echter Fix
(Nutzer): Repo aus dem iCloud-Pfad verschieben. Siehe phase-g-review.md.

---

## Konsolidierte Priorisierung (alle Befunde)

| ID | Domäne | Sev | Aufwand | IP | Status |
|---|---|---|---|---|---|
| AUDIT-010 | EU AI Act | P1 | S | none | **GEFIXT** (Art.50-Footer + lang=de) |
| AUDIT-014 | Doku | P2 | S | none | **GEFIXT** (respx-Claim raus) |
| AUDIT-009 | DSGVO | P1 | L | none | v2 (PII-NER) -- bekannt |
| AUDIT-011 | Legal/IP | P1 | S | med | IP-Entscheidung (stack_options committed) |
| AUDIT-001 | Architektur | P2 | M | none | v2 (async Repository) |
| AUDIT-003 | Security | P2 | S | none | v2 (lokale Security-Hooks) |
| AUDIT-004 | Infra | P2 | M | none | v2 (Frontend-CI) |
| AUDIT-007 | DSGVO | P2 | L | none | v2 (Löschung Art.17) |
| AUDIT-008 | DSGVO | P2 | M | none | v2 (Region-Gate) |
| AUDIT-015 | Doku | P2 | M | none | v2 (secret-compromise-Runbook) |
| AUDIT-017 | Umgebung | P2 | M | none | Nutzer (Repo aus iCloud) |
| AUDIT-002 | Architektur | P3 | S | none | Beobachtung |
| AUDIT-005 | Infra | P3 | S | none | v2 (Multi-Stage/HEALTHCHECK/.dockerignore) |
| AUDIT-006 | Infra | P3 | S | none | v2 (SBOM refresh) |
| AUDIT-012 | Legal/IP | P3 | S | low | IP-Entscheidung (LICENSE) |
| AUDIT-013 | Frameworks | P3 | S | none | v2 (lifespan) |
| AUDIT-016 | Doku | P3 | S | none | v2 (architecture.md Frontend) |

Kein P0 im Code. (Der einzige P0 der Gesamtlage, G-045 exponierter PAT, ist eine
Nutzer-Aktion und in phase-g-review.md §6 geführt.)

---

## Top 10 Risiken (mit Empfehlung)

1. **IP-Klärung ungelöst (G-045 + AUDIT-011 + AUDIT-012)** -- blockiert jeden
   öffentlichen Portfolio-Nutzen. *Empfehlung: zuerst Token rotieren, dann
   IP-Entscheidung A/B treffen, dann stack_options + LICENSE konsistent machen.*
2. **DSGVO-Löschung nicht implementiert (AUDIT-007)** -- echte Lücke bei
   Produktivnutzung. *Empfehlung: als Limitation führen, v2-ADR vor jedem
   echten Personendaten-Einsatz.*
3. **Frontend ohne CI + iCloud-blockierte Builds (AUDIT-004 + AUDIT-017)** --
   das Frontend ist faktisch ungeprüft. *Empfehlung: Repo aus iCloud verschieben,
   dann Frontend-CI-Job ergänzen.*
4. **PII-Redaction fehlt (AUDIT-009)** -- PII erreicht den LLM ungefiltert.
   *Empfehlung: v2 spaCy-NER; bis dahin known_limitations #7 prominent halten.*
5. **EU-Residenz ohne Code-Gate (AUDIT-008)** -- Fehlkonfiguration kann PII
   außerhalb der EU verarbeiten. *Empfehlung: Region-Allowlist im Settings-Load.*
6. **stack_options.toml committed (AUDIT-011)** -- verrät Stack-Zusammensetzung.
   *Empfehlung: vor Public-Release splitten oder Header korrigieren.*
7. **Kein secret-compromise-Runbook (AUDIT-015)** -- der G-045-Vorfall zeigte
   den Bedarf. *Empfehlung: ein knappes Rotations-Runbook schreiben.*
8. **async-Event-Loop-Blocking durch SQLite (AUDIT-001)** -- bei Mehrbenutzer
   ein Skalierungsproblem. *Empfehlung: v2 async-Repository.*
9. **SBOM/Supply-Chain-Drift (AUDIT-006)** -- SBOM spiegelt Deps nicht.
   *Empfehlung: SBOM-Generierung in CI.*
10. **Docker-Härtung unvollständig (AUDIT-005)** -- nur bei echtem Deploy
    relevant. *Empfehlung: Multi-Stage + HEALTHCHECK + .dockerignore vor Deploy.*

---

## Reifegrad je Domäne

| Domäne | Reifegrad | Kernbegründung |
|---|---|---|
| 1 Architektur | 4,5 | Hexagonal hart, nur async-SQLite-Blocking |
| 2 App-Security | 4,5 | In Phase G gehärtet, bandit clean, lückenlose Validierung |
| 3 Infrastruktur | 3,0 | Frontend-CI fehlt, Docker/SBOM unvollständig |
| 4 DSGVO | 3,0 | AVV ok, aber Löschung + PII-Redaction + Region-Gate fehlen |
| 5 EU AI Act | 4,0 | Herleitung sauber, Art.50-UI nachgezogen |
| 6 Legal/IP | 3,5 | roi_config sauber, stack_options/LICENSE offen |
| 7 Governance | 4,5 | HITL + echte ADRs + Cost-/Eval-Governance |
| 8 Code-Qualität | 4,5 | 97% sinnvoll, Property-Tests, typsicher |
| 9 Frameworks | 4,0 | idiomatisch, nur lifespan fehlt |
| 10 Workflows | 4,0 | Disziplin hoch, pre-commit/CI-Parität-Lücke |
| 11 PM | 4,5 | Scope-Disziplin vorbildlich, IP-Entscheidung pendent |
| 12 Doku | 3,5 | ehrlich+vollständig, Runbooks/Currency-Lücken |
| **Gesamt** | **3,7** | Solider Kern, schwächere Ränder (Infra/DSGVO/Frontend-CI) |

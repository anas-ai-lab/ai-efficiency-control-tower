# AI Efficiency Control Tower (AECT)

> Intelligenter Vorbewertungs- und Beratungs-Layer fuer interne AI-Use-Case-Antraege.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![CI](https://github.com/anas-ai-lab/ai-efficiency-control-tower/actions/workflows/ci.yml/badge.svg)](https://github.com/anas-ai-lab/ai-efficiency-control-tower/actions/workflows/ci.yml)
[![Coverage: 95%](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Problem

Unternehmen erhalten eine wachsende Zahl interner AI-Anfragen -- aus HR, IT, Finance,
Legal, Operations. Die meisten Organisationen haben keinen strukturierten Prozess um
diese Anfragen zu bewerten.

**Das Ergebnis:**
- AI wird eingesetzt, wo einfache Automation ausreicht
- Hochrisiko-Use-Cases umgehen Compliance-Reviews
- Kosten sind nicht planbar
- Teams verschwenden Wochen mit dem Aufbau der falschen Sache

Kein leichtgewichtiges, meinungsstarkes Triage-System bewertet AI-Anfragen ueber
Geschaeftswert, technische Machbarkeit, Kosten, Risiko und Compliance -- bevor eine
einzige Zeile Code geschrieben wird.

---

## Loesung

**AECT** ist ein produktionsorientiertes Intake- und Triage-System fuer interne AI-Use-Cases.

Es bewertet Einreichungen entlang von:

- **AI-Eignung** -- Ist AI das richtige Werkzeug, oder reicht Regelbasierung / RPA?
- **ROI-Schaetzung** -- Erwarteter Jahresnutzen minus Lizenzkosten, differenziert nach Mitarbeiterkategorie
- **Privacy & Compliance** -- Beruehrt das personenbezogene Daten? DSFA-Pflicht?
- **Technische Machbarkeit** -- Aufwandsscore, Stack-Fit, Komplexitaets-Einschaetzung
- **Loesungsvorschlag** -- Konkrete Zielplattform-Kategorie mit Begruendung (self-hosted Chat-UI, Low-Code-Agenten-Plattform, Cloud-AI-Plattform, ERP-Erweiterung)
- **Compliance-Hinweise** -- RAG-gegruendete Hinweise mit Quellenangabe (DSGVO, EU AI Act)

**Output:** Ein zweischichtiger, maschinell validierter Report -- Business-Zusammenfassung
fuer Entscheider und technische Detailebene fuer Reviewer.

---

## Was AECT nicht ist

- Kein Ersatz fuer die menschliche Entscheidung -- es liefert Entscheidungsunterstuetzung
- Keine Rechts- oder Datenschutzberatung -- nur belegte Hinweise zur eigenen Pruefung
- Kein produktives Firmensystem -- privates Portfolio-Build
- Kein Fine-tuned Model -- Regelengine + RAG + LLM-Prompting
- Kein SaaS-Produkt

---

## Architektur

```
Browser (Next.js 16, App Router)
  +-- Intake Form     (shadcn/ui + Zod, 20 Felder)
  +-- Server Actions  (actions.ts) -- API-Key server-seitig, nie im Client
  +-- Result Views    Triage | Sharpen | Solution | Compliance | Report
      |
      | HTTP (localhost:8000)
      v
FastAPI Backend (async, Python 3.12)
      |
      v
POST /triage
     |
     v
Pydantic V2 Input Validation (extra="forbid", max_length)
     |
     v
Rule Engine (deterministisch, kein LLM)
  +-- ROI / Value Model     (Lookup-Tabellen aus Config)
  +-- Vorfilter             (Potenzial >= 20k EUR, Stunden >= 120h)
  +-- AI-vs-Automation      (Entscheidungsbaum)
  +-- Composite Effort Score
  +-- 3-Zonen-Einstufung   (MARGINAL GAIN / CALCULATED RISK / LIKELY WIN)
     |
     v
LLM Layer -- Azure OpenAI gpt-4.1-mini (optional, graceful degradation)
  +-- POST /cases/{id}/sharpen           Use-Case-Schaerfung (Original + geschaerft)
  +-- POST /cases/{id}/propose-solution  Stack-passender Loesungsvorschlag
  +-- POST /cases/{id}/compliance-hints  RAG-gegruendete Compliance-Hinweise
               |
               v
          RAG Pipeline
            +-- ChromaDB (Dense Vector, all-MiniLM-L6-v2)
            +-- BM25 (hand-rolled Okapi BM25, k1=1.5, b=0.75)
            +-- Hybrid Search (Reciprocal Rank Fusion)
            +-- Cross-Encoder Reranking
     |
     v
POST /cases/{id}/report
  +-- BusinessSummary  (Entscheider-Schicht)
  +-- TechnicalDetail  (Reviewer-Schicht)
```

**Drei-Schichten-Prinzip:**
- **Regeln** fuer das Eindeutige (ROI, Zonen, Routing) -- deterministisch, getestet, nie halluziniert
- **RAG** fuer Belege (DSGVO, EU AI Act, Stack-Doku) -- jeder Hinweis mit Quelle
- **LLM** fuer Ambiguitaet und Sprache (Schaerfung, Loesungsskizze) -- entscheidet nichts ueber Compliance oder Freigabe

Vollstaendige Architektur-Dokumentation mit C4-Diagrammen (L1-L3) und
Sequenzdiagrammen (Triage, RAG-Compliance, Function-Calling): [`docs/architecture.md`](docs/architecture.md)

---

## Control-Tower-Module (v3)

Ueber den linearen Triage-Flow (Intake -> Report) legt v3 eine Portfolio- und
Lifecycle-Schicht: eingereichte Cases werden nicht nur einzeln bewertet, sondern
als Bestand gefuehrt, verglichen und ueber die Zeit begleitet.

**Ideenliste (`/cases`)** -- alle eingereichten Cases als Tabelle mit
Status-Verwaltung. Jeder Case traegt einen `CaseStatus` (7 Zustaende: SUBMITTED,
IN_REVIEW, APPROVED, ALREADY_EXISTS, INTEGRATED, REJECTED, IMPLEMENTED). Der
Status ist bewusst frei setzbar (keine erzwungene Transitions-Matrix) und an die
Reviewer-Freigabe gekoppelt -- eine Freigabe setzt zugleich den Lifecycle-Status
([ADR-0045](docs/adr/0045-case-lifecycle-status.md)).

**Board-Matrix (`/board`)** -- ein Streudiagramm (recharts), das jeden bewerteten
Case als Blase im Portfolio verortet:

- **x-Achse:** erwarteter **Nettonutzen** pro Jahr (Potenzial x Nutzungsfaktor x
  Evidenzfaktor abzueglich Lizenzkosten) -- netto, nicht das Brutto-Potenzial.
- **y-Achse:** **Machbarkeit** -- der Aufwand-Score (2-10) invertiert dargestellt:
  oben = geringer Aufwand = hohe Machbarkeit. So gilt die Lesart "gut = oben rechts".
- **Blasengroesse:** eingesparte Arbeitsstunden pro Jahr.
- **Farbe:** die Triage-Zone (LIKELY_WIN / CALCULATED_RISK / MARGINAL_GAIN).

Die gestrichelten Quadranten-Linien und die Ecklabels ("Quick Wins" etc.) sind
eine **reine Lese-Hilfe, keine Schwellen** -- statisch gesetzt, nicht aus der
Config gelesen ([ADR-0047](docs/adr/0047-portfolio-board-matrix.md),
`known_limitations.md` #17).

**Monitoring-Zeitleiste (`/monitoring`, Case-Detail)** -- pro Case eine
chronologische Liste manueller Beobachtungen ("Pilot gestartet", "Feedback
eingeholt"). Die Zeitleiste ist **manuell gepflegt und append-only**: jeder
Eintrag ist ein eigener INSERT mit Zeitstempel und einer Momentaufnahme des
damaligen Status (`status_snapshot`); es gibt bewusst keine Update- oder
Einzel-Delete-Methode. Append-only ist hier das Feature (Audit-Charakter), kein
Mangel -- eine einmal festgehaltene Notiz bleibt unveraenderlich
([ADR-0046](docs/adr/0046-monitoring-append-only-timeline.md)).

*Screenshots: `docs/screenshots/board.png`, `docs/screenshots/monitoring.png` (Platzhalter).*

Grenzen dieser Module offen dokumentiert in `docs/known_limitations.md` (#15-#17):
Monitoring ist manuell -- praediktive Validitaet bleibt unmessbar (#1); die
Status-Historie ist im Frontend nur ueber Monitoring-Snapshots sichtbar, das
vollstaendige Audit-Log liegt in structlog.

---

## Assistenz-Features (v3.1)

Ueber die Portfolio-Schicht (v3) legt v3.1 eine duenne Assistenz-Schicht: vier
Hilfsmittel, die den Bestand durchsuchbar und den Intake leichter machen, ohne
die deterministische Bewertung anzutasten. Zwei sind rein deterministisch (Dedup,
CSV), zwei nutzen das LLM streng schema-gebunden (Ideation, Skizze).

**Dedup-Sicht (`/cases/similarity-pairs`)** -- eine read-only Aggregation, die alle
persistierten Cases paarweise auf Text-Naehe vergleicht. Sie nutzt exakt dieselbe
`_cosine_similarity()` und dieselben zwei Schwellen wie die Intake-Warnung beim
Einreichen (`_DEDUP_THRESHOLD_AWARENESS` 0,75 fuer "aehnlich", `_DEDUP_THRESHOLD_COMBINE`
0,90 fuer "Zusammenlegen pruefen") -- eine Quelle im Code, keine zweite Cosinus-
Implementierung. Im Frontend erscheinen "N aehnlich"-Badges an der Ideenliste und
ein Detail-Panel pro Case. Die Aehnlichkeit misst Text-Naehe ueber Embeddings, kein
inhaltliches Urteil (`known_limitations.md` #20); der Vergleich rechnet bewusst
O(n^2) beim Lesen (#19).

**CSV-Export** -- exportiert exakt die aktuell gefilterte und sortierte Ideenliste
(die uebergebene Sicht, nicht der ganze Bestand) als CSV fuer deutsches Excel:
Semikolon als Trenner, UTF-8 mit BOM (Umlaute), CRLF-Zeilenende, Zahlen mit
Dezimal-Komma und ohne Tausenderpunkte, Datum als ISO. Client-seitig als reine
String-Erzeugung ohne Backend-Endpoint und ohne externes Paket (`frontend/src/lib/csv.ts`).

**Ideen-Assistent (`/ideation`)** -- erzeugt aus einer vagen Problembeschreibung
1-3 konkrete AI-Use-Case-Entwuerfe fuer den Intake. Kernregel: **der Assistent
erzeugt Entwuerfe OHNE Zahlen -- die Zahlen liefert der Mensch.** Die Entwuerfe sind
rein qualitativ (Ist-Zustand, Soll-Zustand, Beispielvorgang, Begruendung); jede
quantitative Luecke wird als offene Frage formuliert, die der Einreicher beantwortet.
Der Endpoint ist ephemer (kein Case, keine Persistenz); die Uebernahme in den Intake
befuellt ueber eine Feld-Whitelist ausschliesslich die qualitativen Felder vor, die
Zahlenfelder bleiben leer ([ADR-0048](docs/adr/0048-ideation-drafts-no-invented-numbers.md)).
"Regeln vor LLM" -- die ROI-Zahlen bleiben Input der deterministischen Regel-Schicht,
nie geraten.

**Architektur-Skizze (`/cases/{id}/architecture-sketch`)** -- erzeugt on-demand zu
einem Case mit Loesungsvorschlag ein grobes Baustein-Diagramm. Das LLM emittiert
NIE Mermaid-Syntax, sondern nur ein schema-validiertes Graph-JSON (Knoten mit
id/label/kind, Kanten mit source/target/label, max. 10 Knoten, 5 Bausteintypen);
ein deterministischer, reiner Builder (`build_mermaid`, `application/mermaid.py`)
baut daraus die Mermaid-Zeichenkette (snapshot-getestet). Das eliminiert die
Syntaxfehler-Klasse strukturell und reduziert die Injection-Flaeche der Kette
LLM->LLM (die Eingabe enthaelt `proposal_text`, selbst LLM-Output) auf escapte
Labels ([ADR-0049](docs/adr/0049-architecture-sketch-structured-graph.md)). Die
Skizze ist ein abgeleitetes "zu pruefen"-Artefakt: Regenerieren ueberschreibt,
die DSGVO-Loesch-Kaskade greift automatisch.

Grenzen dieser Features offen dokumentiert in `docs/known_limitations.md` (#18-#20):
Ideation und Skizze sind NICHT durch die Golden-Eval abgedeckt -- ihre Qualitaet
ist nur durch Schema-Zwang und menschliche Pruefung gesichert (#18).

---

## Tech Stack

| Schicht | Technologie |
|---|---|
| Sprache | Python 3.12 |
| API | FastAPI (async) + Pydantic V2 |
| Datenbank | SQLite (raw, kein ORM) |
| LLM Provider | Azure OpenAI (gpt-4.1-mini, EU-Data-Zone Sweden Central) |
| Vector DB | ChromaDB 1.5.x (lokal, Docker) |
| Embedding | sentence-transformers all-MiniLM-L6-v2 (lokal, in-process) |
| PII-Redaktion | presidio-analyzer/-anonymizer + spaCy de_core_news_sm (lokal, vor Dedup-Embedding) |
| Search | BM25 (hand-rolled) + Dense Vector + RRF-Hybrid + Cross-Encoder Reranking |
| Resilience | tenacity (Retry / Backoff / Timeout) |
| Auth | API-Key (X-API-Key Header, pydantic-settings) |
| Rate Limiting | slowapi |
| Logging | structlog (JSON, Correlation-ID, PII-Allowlist) |
| Testing | pytest, pytest-asyncio, hypothesis, httpx TestClient |
| Qualitaet | ruff, mypy --strict, bandit, pip-audit |
| Package Mgmt | uv |
| CI | GitHub Actions (Node 20, gitleaks, pip-audit, bandit) |

---

## Engineering-Entscheidungen (Auswahl)

| Entscheidung | ADR | Begruendung |
|---|---|---|
| Regelengine vor LLM | [ADR-001](docs/adr/ADR-001-roi-modell.md), [ADR-003](docs/adr/ADR-003-ai-vs-automation.md) | Deterministisches Verhalten, testbar, keine Halluzinierung fuer klare Kriterien |
| Hexagonale Architektur | [ADR-004](docs/adr/ADR-004-hexagonal-architecture.md), [0002](docs/adr/0002-hexagonale-architektur.md) | Austauschbare Adapter fuer LLM, DB, Embeddings ohne Domain-Kopplung |
| Hybrid Search (BM25 + Vektor + RRF) | [0027](docs/adr/0027-hybrid-search-bm25-rrf.md) | Keyword-Treffer (BM25) + semantische Naehe ergaenzen sich; RRF robuster als Score-Fusion |
| Cross-Encoder Reranking | [0028](docs/adr/0028-cross-encoder-reranking.md) | Bi-Encoder-Recall + Cross-Encoder-Precision: hoehere Retrieval-Qualitaet fuer Compliance-Hinweise |
| Citations-before-LLM | [0024](docs/adr/0024-rag-grounded-compliance-hints.md) | Halluzinierte Gesetzesartikel strukturell verhindert: Quellen aus Retrieval-Metadaten, nicht aus Modellwissen |
| Semantic Caching / Model Routing abgelehnt | [0034](docs/adr/0034-semantic-caching-model-routing.md) | 0,003 EUR/Case, PII-in-Cache-Risiko, semantisch einzigartige Einreichungen = niedrige Hit-Rate |
| Azure Container Apps: Design, kein Deploy | [0035](docs/adr/0035-azure-container-apps-deploy.md) | IP-Klaerung ausstehend; Demo via localhost vollstaendig erfuellbar |

Alle 55 ADRs (thematischer Index): [`docs/adr/README.md`](docs/adr/README.md)

---

## Evaluation

Evaluiert auf 25 Golden Cases (manuell gelabelt, Einzel-Annotator -- siehe
`known_limitations.md` #3) + 36 synthetischen Faellen:

| Metrik | Wert |
|---|---|
| Raw Agreement Rate (Golden Cases, n=24 gelabelt) | 9/24 (37,5 %) |
| Cohen's Kappa (n=24, inkl. Vorfilter-Ablehnungen) | 0,06 (nahe Zufall) |
| Cohen's Kappa (n=21, ohne Vorfilter-Ablehnungen) | 0,13 ("leicht") |
| Identifiziertes Problem | Hard-Threshold-Brittleness + enge LIKELY_WIN-Definition (Composite <= 4) |
| Synthetic Cases (n=36) | Alle ohne Crash durchgelaufen |
| Test-Coverage | 95 % (720 Tests, 715 passed) |

**Was die Eval-Zahlen bedeuten:**
Das urspruengliche Sample (4 Cases, 3 gelabelt, Agreement 1/3) war zu klein fuer eine
belastbare Aussage. Mit 24 gelabelten Cases liegt die Agreement-Rate bei 37,5 % -- und
genau diese Divergenz ist der Wert der Evaluation, nicht ihr Defekt. Das dominante Muster:
Die Engine vergibt LIKELY_WIN nur bei `composite_total <= 4`, das menschliche Urteil
"klarer High-Value-Fall" ist breiter -- viele Faelle mit Composite 5-7 landen darum als
CALCULATED_RISK statt LIKELY_WIN. Daneben fallen drei Cases (golden-005/006/016) am
Vorfilter durch (predicted=None), wurden vom Experten aber dennoch gelabelt -- der
Vorfilter und das menschliche Relevanzempfinden ziehen die Grenze unterschiedlich.
Die urspruenglich beobachteten Off-by-one-Effekte an Zonengrenzen (golden-001, golden-003)
bleiben sichtbar; sie sind jetzt ein Spezialfall des breiteren Schwellen-Befunds.
Ein LLM-Zweitannotator im Blind-Protokoll (kein menschlicher Experte) erreicht 14/24
(58,3 %, Kappa 0,33) gegen die Autor-Labels und liegt zwischen konservativer Engine und
optimistischem Autor -- Details und Grenzen in `evals/golden/inter_annotator_report.md`.
Vertiefte Ursachenanalyse (Composite-Schwellen-Mechanik, Zweitannotator-Einordnung,
MARGINAL_GAIN-Empfehlung) in `docs/analysis/rule-engine-vs-human-judgment.md`.

Das ist keine Aussage ueber Systemfehler -- es ist eine Aussage ueber das Design.
Fuzzy-Zonen mit Konfidenz-Intervallen waeren robuster. Dokumentiert als v2-Kandidat
in `docs/known_limitations.md` (Limitation #2).

Die 36 synthetischen Cases beweisen Robustheit (kein Crash, deterministisch) --
nicht inhaltliche Korrektheit. Zwei verschiedene Dinge, absichtlich nicht vermischt.

Bekannte Limitation: praeiktive Validitaet (Plan-Nutzen vs. realisierter Nutzen) nicht
messbar im privaten Build -- dokumentiert in `docs/limitations.md`.

---

## Quick Start

**Voraussetzungen:** Python 3.12, uv, Docker

```bash
git clone https://github.com/anas-ai-lab/ai-efficiency-control-tower.git
cd ai-efficiency-control-tower

uv sync
docker compose up -d          # ChromaDB starten
uv run python scripts/seed_knowledge_base.py
uv run uvicorn aect.adapters.api.app:app --reload --no-server-header
uv run pytest -q
```

API-Dokumentation nach Start: http://localhost:8000/docs

**Frontend starten** (zweites Terminal, parallel zum uvicorn-Prozess):

```bash
cd frontend
npm install        # einmalig
npm run dev
```

UI nach Start: http://localhost:3000

**Ohne Azure- und Chroma-Konfiguration** (Mock-Modus): Triage-Formular und Zone-Anzeige funktionieren,
LLM-Schärfung und Compliance-Hints geben Platzhalter zurück.

**Umgebungsvariablen** (`.env`, nicht committed):

```
AECT_API_KEY=<beliebiger-string>
AECT_API_KEY_NEXT=<optional, nur waehrend Rotation gesetzt>
AECT_DB_PATH=aect.db

# Leer lassen -> Mock-LLM-Adapter (Rule Engine laeuft vollstaendig)
AECT_AZURE_OPENAI_ENDPOINT=https://...
AECT_AZURE_OPENAI_API_KEY=<key>
AECT_AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini

# Leer lassen -> Mock-Retriever (Compliance-Hinweise als Platzhalter)
AECT_CHROMA_HOST=127.0.0.1
AECT_CHROMA_PORT=8001
```

Ohne Azure- und Chroma-Konfiguration laeuft das System vollstaendig mit Mock-Adaptern --
Rule Engine, ROI-Modell, Zonen-Einstufung und Triage-Report funktionieren, LLM-Schaerfung
und RAG-Hinweise liefern Platzhalter-Antworten.

**API-Key-Rotation** (ohne Downtime): `AECT_API_KEY` und optional `AECT_API_KEY_NEXT`
sind waehrend einer Rotation gleichzeitig gueltig -- `require_api_key` prueft eingehende
Requests gegen beide. Ablauf: (1) neuen Key als `AECT_API_KEY_NEXT` setzen und den Server
neu starten (beide Keys jetzt gueltig), (2) Clients auf den neuen Key umstellen, (3) in
den Logs pruefen, dass nur noch die kid (kurzer sha256-Fingerprint, nie der Klartext-Key)
des neuen Keys unter dem Event `api_key_authenticated` erscheint -- das zeigt, dass kein
Client mehr den alten Key nutzt, (4) `AECT_API_KEY_NEXT` -> `AECT_API_KEY` uebernehmen und
den alten Wert entfernen.

---

## Repository-Struktur

```
src/aect/
  domain/        # Regelengine, ROI-Modell, Zonen-Logik (kein Framework-Import)
  application/   # Application Service, Ports (LLM, RAG, Repo), Eval-Runner
  adapters/
    api/         # FastAPI-Routen, Auth, Rate-Limiting, Middleware
    llm/         # Azure-OpenAI-Adapter, Resilience-Wrapper
    rag/         # Chunker, Embedder, BM25, ChromaDB-Retriever, Hybrid, Reranker
    sqlite/      # SQLite-Repository, Idempotency-Store
    in_memory/   # Mock-Adapter fuer Tests und Offline-Betrieb
tests/           # 720 Tests (715 passed, 5 skipped), 95 % Coverage (pytest, hypothesis, httpx TestClient)
evals/
  golden/        # 25 manuell gelabelte Golden Cases (JSONL)
  synthetic/     # 36 synthetisch generierte Faelle (JSONL)
knowledge_base/  # Kuratierte Markdown-Quellen (DSGVO, EU AI Act, Stack-Doku)
prompts/         # Versionierte Prompt-Dateien (v1)
config/          # TOML/YAML-Config (ROI-Faktoren, Zonen-Schwellen, Stack-Optionen)
scripts/         # Seeder, Eval-Runner, Diagnostics, synthetische Case-Generierung
docs/
  adr/           # 55 Architecture Decision Records (zwei Serien: 000X und ADR-00X)
  reviews/       # Phasen-Reviews (A-F)
  threat-model.md
  limitations.md
  architecture.md
```

---

## Security & Privacy

| Massnahme | Status | Artefakt |
|---|---|---|
| OWASP LLM Top 10 (2025) | Abgedeckt | `docs/owasp-llm-checklist.md` |
| STRIDE Threat Model | Abgedeckt | `docs/threat-model.md` |
| Secret Scanning (gitleaks) | CI-Job, jeder Push | `.github/workflows/ci.yml` |
| SAST (bandit MEDIUM+) | CI-Job | `.github/workflows/ci.yml` |
| Dependency CVE Scan (pip-audit) | CI-Job, jeder Push | 2 begruendete Ignores: (1) CVE-2025-3000: torch gepatcht in 2.12.0, OSV-DB ohne Fix-Range, nicht exploitierbar; (2) GHSA-537c-gmf6-5ccf (cryptography 46.0.7, Fix 48.0.1): transitiv via presidio-anonymizer==2.2.363 (exakter Pin), das cryptography<47.0.0 erzwingt -- kein Upgrade-Pfad, 2.2.363 ist aktuellste PyPI-Version (Stand 2026-07-03) -- beide doc'd in CI |
| GitHub Actions SHA-Pinned | Erledigt | Alle 4 Action-Refs durch Commit-SHA |
| Prompt-Injection-Detection (LLM01) | Flag + Log vor LLM-Call (Delimiter primaer) | `application/sanitization.py` |
| Prompt-Injection-Tests | pytest Red-Team-Cases | `tests/adapters/api/test_triage.py` |
| PII in Logs | Allowlist -- kein Body/Prompt/PII | `adapters/api/logging_config.py` |
| PII-Redaction vor LLM (NER) | Bewusste v1-Grenze (Regex statt NER) | `docs/known_limitations.md` #7 |
| Azure EU-Datenpflicht | Best-Effort (Startup-Guard) | Endpoint-URL-Substring-Pruefung auf `swedencentral`/`westeurope` beim Start (`settings.py`); kein Laufzeit-Nachweis der tatsaechlichen Datenregion |
| Non-root Docker User | Dockerfile | `aect:aect` (uid/gid 1000) |
| ChromaDB-Isolation | Docker-Netz | Nur `127.0.0.1:8001`, kein Netz-Zugriff |
| SBOM | Vorhanden | `docs/sbom.json` (CycloneDX) |
| AI-BOM | Vorhanden | `docs/ai-bom.md` |

**Compliance-Philosophie:** AECT gibt ausschliesslich belegte Hinweise mit Quellenangabe aus --
kein verbindliches Rechtsurteil. Jeder Compliance-Hinweis ist explizit als "zu pruefen" markiert
(Projekt-Prinzip "Hinweis, kein Urteil"). Halluzinierte Artikel-Nummern sind durch das Citations-before-LLM-Pattern
strukturell ausgeschlossen.

## Autor

Gebaut von Anas als privates Karriere-Portfolio-Projekt (AI Engineer / Solution Architect, DACH-Markt).

GitHub: [anas-ai-lab](https://github.com/anas-ai-lab)

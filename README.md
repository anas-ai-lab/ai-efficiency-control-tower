# AI Efficiency Control Tower (AECT)

> Intelligenter Vorbewertungs- und Beratungs-Layer fuer interne AI-Use-Case-Antraege.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![CI](https://github.com/anas-ai-lab/ai-efficiency-control-tower/actions/workflows/ci.yml/badge.svg)](https://github.com/anas-ai-lab/ai-efficiency-control-tower/actions/workflows/ci.yml)
[![Coverage: 97%](https://img.shields.io/badge/coverage-97%25-brightgreen.svg)]()
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
- **Loesungsvorschlag** -- Konkrete Zielplattform mit Begruendung (Open WebUI, Copilot Studio, Foundry, SAP BTP)
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

## Tech Stack

| Schicht | Technologie |
|---|---|
| Sprache | Python 3.12 |
| API | FastAPI (async) + Pydantic V2 |
| Datenbank | SQLite (raw, kein ORM) |
| LLM Provider | Azure OpenAI (gpt-4.1-mini, EU-Data-Zone Sweden Central) |
| Vector DB | ChromaDB 1.5.x (lokal, Docker) |
| Embedding | sentence-transformers all-MiniLM-L6-v2 (lokal, in-process) |
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

Alle 41 ADRs (thematischer Index): [`docs/adr/README.md`](docs/adr/README.md)

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
| Test-Coverage | 97 % (488 Tests) |

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
tests/           # 493 Tests (488 passed, 5 skipped), 97 % Coverage (pytest, hypothesis, httpx TestClient)
evals/
  golden/        # 25 manuell gelabelte Golden Cases (JSONL)
  synthetic/     # 36 synthetisch generierte Faelle (JSONL)
knowledge_base/  # Kuratierte Markdown-Quellen (DSGVO, EU AI Act, Stack-Doku)
prompts/         # Versionierte Prompt-Dateien (v1)
config/          # TOML/YAML-Config (ROI-Faktoren, Zonen-Schwellen, Stack-Optionen)
scripts/         # Seeder, Eval-Runner, Diagnostics, synthetische Case-Generierung
docs/
  adr/           # 41 Architecture Decision Records (zwei Serien: 000X und ADR-00X)
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
| Dependency CVE Scan (pip-audit) | CI-Job, jeder Push | 1 begruendeter Ignore (CVE-2025-3000: torch gepatcht in 2.12.0, OSV-DB ohne Fix-Range, nicht exploitierbar -- doc'd in CI) |
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

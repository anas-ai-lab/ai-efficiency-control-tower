# Architecture Decision Log -- AECT

55 Architecture Decision Records, thematisch gruppiert. Jede ADR dokumentiert
Kontext, Entscheidung, ernsthaft erwogene Alternativen und Konsequenzen.

> **Zwei Namensserien (dokumentierte Schuld):** `ADR-00X` (Phase A/B) und `00XX`
> (Phase C+). Historisch gewachsen; bewusst NICHT konsolidiert (Rename aller +
> Querverweise = hohe Churn, null funktionaler Gewinn -- known_limitations #13,
> Entscheidung G-S6). Vor einer neuen ADR `ls docs/adr/` pruefen.

---

## Fundament & Architektur

| ADR | Titel |
|---|---|
| [ADR-004](ADR-004-hexagonal-architecture.md) | Hexagonal Architecture (Ports & Adapters) |
| [0002](0002-hexagonale-architektur.md) | Hexagonale Architektur (fruehe Fassung) |
| [ADR-001](ADR-001-roi-modell.md) | ROI-Modell: deterministisches v5-Bewertungsmodell |
| [ADR-002](ADR-002-zonen-logik.md) | Zonen-Logik: 3-Zonen-Modell mit Handlungsdruck-Hochstufung |
| [ADR-003](ADR-003-ai-vs-automation.md) | AI-vs-Automation-Router: regelbasierte Vorpruefung |
| [0001](0001-toolchain-und-project-setup.md) | Python-Toolchain und Projekt-Setup |

## API, Persistenz & Security

| ADR | Titel |
|---|---|
| [ADR-005](ADR-005-idempotency-keys.md) | Idempotency-Keys fuer POST /triage |
| [ADR-006](ADR-006-api-key-auth.md) | API-Key-Authentifizierung |
| [ADR-007](ADR-007-sqlite-persistence.md) | SQLite als Persistenz-Adapter |
| [0011](0011-report-renderer.md) | Zweischichtiger Report-Renderer als Regel-Schicht |
| [0012](0012-sharpened-proposal-persistence.md) | Persistenz von sharpened_text / proposal_text |
| [0040](0040-sqlite-chroma-skalierungsgrenze.md) | SQLite + lokales ChromaDB: bewusste Beibehaltung und explizite Decke |
| [0041](0041-key-vault-settings-source.md) | Key-Vault-Referenzen statt Env-Strings (Design, ohne Live-Azure verifiziert) |
| [0042](0042-retention-scheduled-job.md) | Retention-Enforcement als Scheduled Job (Design, kein Deploy) |
| [0043](0043-decision-record-statt-reviewer-workflow.md) | Human-in-the-Loop-Decision-Record statt vollem Reviewer-Workflow |
| [0044](0044-country-and-employee-level-schema-change.md) | Country- und Employee-Level-Schema-Erweiterung (5 Level, Impl.-Kosten) |

## LLM-Integration

| ADR | Titel |
|---|---|
| [ADR-0003](0003-llm-strategie-und-provider.md) | LLM-Strategie und Provider |
| [0005](0005-llm-port-messages-api.md) | LLM-Port mit Messages-API-Pattern |
| [0006](0006-prompt-loader-and-sharpening.md) | Prompt-Loader, Versionierung, Schaerfung |
| [0007](0007-llm-resilience.md) | Resilience-Decorator (Retry/Backoff/Timeout) |
| [0008](0008-function-calling-tool-layer.md) | Function-Calling-Vorbereitung: Tool-Registry |
| [0009](0009-function-calling-loop.md) | Function-Calling-Loop (max 2 Calls) |
| [0010](0010-azure-openai-adapter.md) | Azure-OpenAI-Adapter (EU Data Zone) |
| [0013](0013-structured-llm-output-schema.md) | Strukturiertes LLM-Output-Schema + Validator |
| [0034](0034-semantic-caching-model-routing.md) | Kein Semantic Caching / Model Routing in v1 |

## RAG & Compliance

| ADR | Titel |
|---|---|
| [0014](0014-rag-retrieval-kontrakt.md) | RetrieverPort + RetrievedChunk (Mock-First) |
| [0015](0015-embedding-kontrakt.md) | EmbedderPort (Mock-First) |
| [0016](0016-lokaler-embedding-adapter.md) | SentenceTransformerEmbedder |
| [0017](0017-paragraph-chunker.md) | Absatz-basierter Chunker |
| [0018](0018-chromadb-container.md) | ChromaDB als lokaler Docker-Container |
| [0019](0019-chroma-retriever.md) | ChromaRetriever (Vektor-Suche) |
| [0021](0021-knowledge-base-citation-convention.md) | KB-Citation-Konvention + Index-Records |
| [0022](0022-kb-live-indexing.md) | KB-Live-Indexing (Schreib-Pfad) |
| [0023](0023-retrieval-citation-metadata-passthrough.md) | Citation-Metadaten im Lese-Pfad |
| [0024](0024-rag-grounded-compliance-hints.md) | RAG-gegruendete Compliance-Hinweise (Citations-before-LLM) |
| [0025](0025-chroma-retriever-di-wiring.md) | ChromaRetriever-DI (Mock-vs-Real-Schalter) |
| [0026](0026-compliance-hints-persistence.md) | Persistenz / Report-Integration der Hinweise |
| [0027](0027-hybrid-search-bm25-rrf.md) | Hybrid Search: BM25 + Vektor via RRF |
| [0028](0028-cross-encoder-reranking.md) | Cross-Encoder-Reranking nach Hybrid-Retrieval |

## Evaluation

| ADR | Titel |
|---|---|
| [0029](0029-eval-case-format.md) | Eval-Case-Schema und -Format (JSONL) |
| [0030](0030-eval-runner-report-format.md) | Eval-Runner-Vergleichslogik und Report-Format |
| [0031](0031-score-breakdown-diagnostik.md) | Score-Breakdown als separate Diagnostik-Schicht |
| [0032](0032-eval-gate-mechanik.md) | Eval-Gate E->F: pytest-Regression |
| [ADR-008](ADR-008-config-layering-opt-out.md) | Abschaltbares Config-Layering (layer_local) fuer CI-reproduzierbare Eval-Artefakte |

## Control-Tower & Lifecycle (v3)

| ADR | Titel |
|---|---|
| [0045](0045-case-lifecycle-status.md) | Case-Lifecycle-Status (7 Zustaende, an ReviewerDecision gekoppelt) |
| [0046](0046-monitoring-append-only-timeline.md) | Monitoring-Zeitleiste als append-only Tabelle |
| [0047](0047-portfolio-board-matrix.md) | Portfolio-Board: Nutzen-Machbarkeits-Matrix (recharts) |

## Assistenz-Layer (v3.1)

| ADR | Titel |
|---|---|
| [0048](0048-ideation-drafts-no-invented-numbers.md) | Ideation-Entwuerfe ohne erfundene Zahlen (Regeln vor LLM) |
| [0049](0049-architecture-sketch-structured-graph.md) | Architektur-Skizze als schema-validierter Graph statt LLM-Mermaid |

## Compliance, Observability & Deployment

| ADR | Titel |
|---|---|
| [0020](0020-eu-ai-act-recheck-und-einordnung.md) | EU-AI-Act-Recheck und AECT-Einordnung (Limited Risk) |
| [0033](0033-opentelemetry-distributed-tracing.md) | Observability: structlog statt OpenTelemetry |
| [0035](0035-azure-container-apps-deploy.md) | Deployment: lokal (Docker + uvicorn) |

---

*Vorlage fuer neue ADRs: [template.md](template.md). Lesbare System-Karte:
[../architecture.md](../architecture.md).*

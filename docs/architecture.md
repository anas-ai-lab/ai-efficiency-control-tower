# Architecture Overview — AI Efficiency Control Tower (AECT)

**Version:** 1.1.0
**Stand:** Juni 2026
**Methodik:** C4-Modell (Context / Container / Component) + Sequenzdiagramme.

> Diagramme als versionierter Mermaid-Code (rendert auf GitHub). Architektur-
> Entscheidungen sind in `docs/adr/` (41 ADRs, Index: `docs/adr/README.md`)
> belegt -- dieses Dokument ist die Karte, die ADRs sind die Begruendungen.

---

## Problem

Unternehmen generieren laufend AI-Ideen aus Fachbereichen (HR, IT, Finance,
Sales, Legal). Es fehlt ein strukturiertes System, das diese Ideen vor der
Umsetzung bewertet -- nach Nutzen, Aufwand, Risiko, Datenschutz und der Frage,
ob es ueberhaupt ein AI-Problem ist. Ohne Triage landen zu viele Projekte in der
Umsetzung, oder sinnvolle Ideen werden mangels Bewertungskompetenz abgelehnt.

## Loesungsansatz

Ein Use-Case-Intake- & Triage-System nimmt interne AI-Anfragen strukturiert auf
und bewertet sie. Die Bewertung kombiniert deterministische Regel-Logik (ROI-
Modell, Composite-Score, 3-Zonen-Einstufung, AI-vs-Automation-Routing) mit
optionalem LLM-Einsatz (Schaerfung, Loesungsvorschlag) und RAG (belegte
Compliance-Hinweise). Zahlen kommen nie aus dem LLM.

**Leitprinzip:** Regeln vor LLM. AI fuer Ambiguitaet. Menschen fuer Verantwortung.

---

## C4 Level 1 -- System Context

```mermaid
flowchart TB
    user["Fachbereich / AI-Antragsteller<br/>(Mensch)"]
    reviewer["Reviewer<br/>(Mensch, Entscheider)"]
    aect["AECT<br/>AI Use Case Intake & Triage<br/>(dieses System)"]
    azure["Azure OpenAI<br/>gpt-4.1-mini, EU Data Zone<br/>(extern)"]
    chroma["ChromaDB<br/>Vektor-Store, lokal<br/>(extern, Docker)"]

    user -->|reicht Use Case ein| aect
    aect -->|Zone, ROI, Routing, belegte Hinweise| user
    aect -->|zweischichtiger Report| reviewer
    reviewer -->|finale Entscheidung| aect
    aect -->|Schaerfung / Loesung / Compliance-Formulierung| azure
    aect -->|Retrieval kuratierter Rechtstexte| chroma
```

AECT entscheidet nichts selbst: es liefert Entscheidungsunterstuetzung, der Mensch bleibt der Entscheider (Projekt-Prinzip Human-in-the-Loop).

---

## C4 Level 2 -- Container

```mermaid
flowchart TB
    subgraph client["Browser"]
        ui["Next.js 15 Frontend<br/>App Router, shadcn/ui<br/>Server Actions"]
    end
    subgraph server["AECT-Prozess (FastAPI)"]
        api["API-Adapter<br/>Routes, Auth, Rate-Limit"]
        app["Application<br/>TriageService + Ports"]
        dom["Domain<br/>ROI, Zonen, Routing, Scoring"]
    end
    db[("SQLite<br/>aect.db")]
    azure["Azure OpenAI<br/>(EU Data Zone)"]
    chroma[("ChromaDB<br/>127.0.0.1:8001")]

    ui -->|X-API-Key, serverseitig<br/>kein NEXT_PUBLIC_| api
    api --> app
    app --> dom
    app -->|RepositoryPort| db
    app -->|LLMPort| azure
    app -->|RetrieverPort| chroma
```

Der API-Key liegt ausschliesslich serverseitig (Server Actions, kein
NEXT_PUBLIC_) -- der Browser sieht ihn nie (Threat-Model TB-5).

---

## C4 Level 3 -- Component (Hexagonal)

```mermaid
flowchart TB
    subgraph adapters["adapters/ (Infrastruktur)"]
        apia["api/ (FastAPI, slowapi, dependencies)"]
        sql["sqlite/ (Repository, IdempotencyStore)"]
        llma["llm/ (AzureOpenAI, Resilient)"]
        raga["rag/ (Chroma, BM25, Hybrid, CrossEncoder, Embedder)"]
        mem["in_memory/ (Mock-Adapter fuer Tests)"]
    end
    subgraph application["application/ (Orchestrierung)"]
        svc["TriageService"]
        ports["ports/ (LLMPort, RetrieverPort,<br/>RepositoryPort, Clock, IdGenerator)"]
        san["sanitization (Injection-Detection)"]
        cost["cost_logger (tiktoken)"]
        so["structured_output (Pydantic-Validierung)"]
    end
    subgraph domain["domain/ (reine Geschaeftslogik, kein I/O)"]
        pipe["pipeline (evaluate_use_case)"]
        roi["roi"]
        zones["zones"]
        routing["routing"]
        scoring["scoring"]
        filters["filters (Vorfilter)"]
    end

    apia --> svc
    svc --> ports
    svc --> pipe
    pipe --> filters --> roi --> scoring --> zones --> routing
    sql -.implements.-> ports
    llma -.implements.-> ports
    raga -.implements.-> ports
    mem -.implements.-> ports

    classDef dom fill:#e8f5e9,stroke:#2e7d32
    class pipe,roi,zones,routing,scoring,filters dom
```

**Abhaengigkeitsregel (grep-verifiziert, CI-relevant):** `domain/` importiert nur
aus `aect.domain.*`; `application/` importiert nichts aus `adapters/`. Adapter
implementieren Ports via `typing.Protocol` (strukturelles Subtyping, kein Erben)
-- ADR-004.

---

## Sequenz 1 -- Triage (deterministisch, kein LLM)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI /triage
    participant S as TriageService
    participant D as domain.evaluate_use_case
    participant R as RepositoryPort

    C->>API: POST /triage (UseCaseInput, X-API-Key)
    API->>API: require_api_key (compare_digest), Pydantic-Validierung
    API->>S: submit_use_case(input)
    S->>D: evaluate_use_case(input, roi_config)
    D->>D: Vorfilter -> ROI -> Composite -> Zone -> Routing
    D-->>S: TriageResult (Zone, ROI, Routing)
    S->>R: save(SubmittedCase)
    S-->>API: SubmittedCase
    API-->>C: 201 TriageResponse (id, zone, roi, routing)
```

Kein LLM-Call im Triage-Pfad -- die Zahlen sind deterministisch und testbar.

---

## Sequenz 2 -- RAG-Compliance (Citations-before-LLM)

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI /compliance-hints
    participant S as TriageService
    participant RET as RetrieverPort (Hybrid+Reranker)
    participant L as LLMPort

    C->>API: POST /cases/{id}/compliance-hints
    API->>S: generate_compliance_hints(id)
    S->>S: feste Queries (Transparenz immer,<br/>DSFA wenn risk_flags) -- kein Freitext
    S->>RET: retrieve(query, top_k)
    RET-->>S: RetrievedChunks (+ Citation-Metadaten)
    alt keine Treffer
        S-->>API: hint_text=None (kein LLM-Call)
    else Treffer
        S->>S: _build_compliance_citations() DETERMINISTISCH<br/>(vor dem LLM-Call)
        S->>L: complete(nummerierte [N]-DATA-Bloecke)
        L-->>S: Fliesstext referenziert nur [N]
        S-->>API: hint_text + citations
    end
```

Die Quellenliste wird aus den Retrieval-Metadaten gebaut, BEVOR das LLM
formuliert -- halluzinierte Artikel-Nummern sind strukturell ausgeschlossen,
nicht nur durch Prompt-Disziplin (ADR-0024).

---

## Sequenz 3 -- Function-Calling-Loop (begrenzt)

```mermaid
sequenceDiagram
    participant API as FastAPI /propose-solution
    participant S as TriageService
    participant L as LLMPort
    participant T as dispatch_tool_call

    API->>S: propose_solution(id)
    S->>L: complete(messages, tools=[lookup_stack_options])
    L-->>S: response (ggf. tool_calls)
    alt tool_calls vorhanden
        S->>T: dispatch_tool_call(call)
        T-->>S: Tool-Ergebnis (Config-Lookup, read-only)
        S->>L: complete(messages + tool-result) [2. und letzter Call]
        L-->>S: finale response
    end
    S-->>API: SolutionProposal
```

Maximal zwei `complete()`-Aufrufe, kein offener ReAct-Loop (LLM10/LLM06,
ADR-0009). Das einzige Tool ist read-only (`lookup_stack_options`).

---

## Kern-Komponenten (real, v1.1.0)

| Komponente | Aufgabe | Schicht |
|---|---|---|
| `pipeline.evaluate_use_case` | Orchestriert Vorfilter -> ROI -> Composite -> Zone -> Routing | domain |
| `roi` | v5-ROI-Modell (Potenzial x Adoption x Evidenz - Lizenz) | domain |
| `zones` | 3-Zonen-Einstufung + Handlungsdruck-Elevation | domain |
| `routing` | AI-vs-Automation-Signal-Routing, Risk-Flags | domain |
| `TriageService` | Orchestrierung + Persistenz, kennt nur Ports | application |
| `sanitization` | Prompt-Injection-Pattern-Detection (Flag, nicht Block) | application |
| RAG-Stack | Hybrid (BM25+Vektor, RRF) -> Cross-Encoder-Reranking | adapters/rag |
| `AzureOpenAIAdapter` | LLMPort, EU Data Zone, via ResilientLLMAdapter | adapters/llm |

---

## Bewusste Einschraenkungen (v1)

- SQLite statt Postgres -- privates Single-User-Build, Repository-Port als Ausstieg.
- ChromaDB lokal (`127.0.0.1:8001`) statt Azure AI Search -- kostenlos, isoliert.
- Azure OpenAI nur bei echten LLM-Operationen, Mock-First in Tests.
- Kein Produktivbetrieb, kein n8n, kein SaaS (Scope-Disziplin).

Vollstaendige, ehrliche Grenzen: `docs/known_limitations.md` (14 Punkte).
v2-Kandidaten: `docs/roadmap-v2.md`.

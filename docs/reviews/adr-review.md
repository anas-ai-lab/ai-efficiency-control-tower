# ADR-Review -- Phase F

**Stand:** Juni 2026
**Zweck:** Vollstaendigkeitspruefung und Redundanzanalyse beider ADR-Serien
vor Portfolio-Abschluss.

---

## 1. Zwei ADR-Serien (historisch gewachsen, session-protocol v3 SS6.13)

Seit Tag 13 koexistieren zwei parallele Nummerierungsserien:

| Serie | Dateimuster | Entstehungsphase | Anzahl |
|---|---|---|---|
| `ADR-00X` | `ADR-001-thema.md` bis `ADR-007-thema.md` | A/B | 7 Dateien |
| `000X` | `0001-thema.md` bis `0035-thema.md` | C+ | 34 Dateien (0004 bewusste Luecke) |

Eine Zusammenfuehrung beider Serien in v1 waere ein nicht-additiver Umbau ohne
Zielprofil-Nutzen. **Entscheidung:** Beide Serien in ihrer jetzigen Form einfrieren.
Bekannte Doppelserie in README und Portfolio-Dokumentation als dokumentierte Konvention
gefuehrt -- kein offener Punkt.

---

## 2. ADR-00X-Serie (Phase A/B) -- Vollstaendigkeit

| Datei | Entscheidung | Status |
|---|---|---|
| ADR-001 | ROI-Modell (Lookup-Tabellen, Config-basiert) | aktiv |
| ADR-002 | Zonen-Logik (3 Zonen + Handlungsdruck-Hochstufung) | aktiv |
| ADR-003 | AI-vs-Automation-Entscheidungsbaum | aktiv |
| ADR-004 | Hexagonal Architecture (Ports/Adapters) | aktiv |
| ADR-005 | Idempotency-Keys | aktiv |
| ADR-006 | API-Key-Auth (kein JWT/RBAC in v1) | aktiv |
| ADR-007 | SQLite-Persistenz | aktiv |

**Luecken:** Keine. Alle 7 ADRs vollstaendig.

**Redundanz-Hinweis:** ADR-004 (Hexagonal, Phase A/B-Rahmen) und 0002 (Hexagonale
Architektur, Adapter-Port-Vertraege in Phase C) ueberschneiden sich inhaltlich.
Kein Widerspruch -- unterschiedlicher Zeitpunkt und Granularitaet. Kein
Zusammenfuerungs-Bedarf.

---

## 3. 000X-Serie (Phase C+) -- Vollstaendigkeit

| Datei | Entscheidung | Status |
|---|---|---|
| 0001 | Toolchain + Project Setup | aktiv |
| 0002 | Hexagonale Architektur (Adapter-Port-Vertraege) | aktiv |
| 0003 | LLM-Strategie + Provider (Azure OpenAI, EU-Data-Zone) | aktiv |
| 0004 | *(bewusste Luecke -- dokumentierter Gap)* | kein Inhalt, kein Handlungspunkt |
| 0005 | LLM-Port (Messages-API-Kontrakt) | aktiv |
| 0006 | Prompt-Loader + Schaerfungs-Logik | aktiv |
| 0007 | LLM-Resilience (tenacity Retry/Backoff/Timeout) | aktiv |
| 0008 | Function-Calling Tool-Layer | aktiv |
| 0009 | Function-Calling-Loop (max. 2 Iterations) | aktiv |
| 0010 | Azure-OpenAI-Adapter | aktiv |
| 0011 | Report-Renderer (zweischichtig, Regel-basiert) | aktiv |
| 0012 | Sharpened-Content + Proposal-Persistenz | aktiv |
| 0013 | Structured LLM Output Schema | aktiv |
| 0014 | RAG-Retrieval-Kontrakt | aktiv |
| 0015 | Embedding-Kontrakt | aktiv |
| 0016 | Lokaler Embedding-Adapter (sentence-transformers) | aktiv |
| 0017 | Paragraph-Chunker | aktiv |
| 0018 | ChromaDB-Container | aktiv |
| 0019 | Chroma-Retriever | aktiv |
| 0020 | EU-AI-Act-Recheck + AECT-Einordnung (Limited Risk) | aktiv |
| 0021 | Knowledge-Base-Citation-Convention | aktiv |
| 0022 | KB-Live-Indexing | aktiv |
| 0023 | Retrieval-Citation-Metadata-Passthrough | aktiv |
| 0024 | RAG-grounded Compliance Hints (Citations-before-LLM) | aktiv |
| 0025 | Chroma-Retriever DI-Wiring | aktiv |
| 0026 | Compliance-Hints-Persistenz | aktiv |
| 0027 | Hybrid Search (BM25 + Vektor + RRF) | aktiv |
| 0028 | Cross-Encoder Reranking | aktiv |
| 0029 | Eval-Case-Format (Golden Cases, JSONL) | aktiv |
| 0030 | Eval-Runner + Report-Format | aktiv |
| 0031 | ScoreBreakdown-Diagnostik | aktiv |
| 0032 | Eval-Gate-Mechanik (Phase E -> F) | aktiv |
| 0033 | OpenTelemetry / Distributed Tracing (downgraded zu structlog) | Design, nicht gebaut |
| 0034 | Semantic Caching + Model Routing (abgelehnt) | abgelehnt, begruendet |
| 0035 | Azure Container Apps Deploy (downgraded) | Design, nicht deployed |

**Luecken:** 0004 -- bewusste Luecke, kein Handlungspunkt.

---

## 4. Zusammenfassung

| Metrik | Wert |
|---|---|
| ADR-00X gesamt | 7 / 7 vollstaendig |
| 000X gesamt | 34 / 35 (0004 bewusste Luecke) |
| Aktive Entscheidungen | 38 |
| Downgraded / abgelehnt | 3 (0033, 0034, 0035) |
| Redundanzen | 1 inhaltliche Ueberschneidung (ADR-004 <-> 0002), kein Widerspruch |
| Empfehlung | Beide Serien eingefroren; Doppelserie als bekannte Konvention dokumentiert |

---

## 5. Interview-Readiness

Entscheidungen die sich in technischen Interviews bewaehren:

**"Warum Regelengine vor LLM?"**
ADR-001 + ADR-003: deterministisches Verhalten, testbar auf numerische Invarianten,
keine Halluzinierung fuer klare Rechengroessen (ROI, Zonen-Schwellen).

**"Wie funktioniert eure Hybrid-Search?"**
ADR-0027 + 0028: BM25 fuer Keyword-Treffer + Dense Vector fuer semantische Naehe,
RRF als Fusionsschicht (robuster als Score-Normalisierung), Cross-Encoder als
Reranking-Schicht (Bi-Encoder-Recall + Cross-Encoder-Precision).

**"Wie verhindert ihr halluzinierte Gesetzesartikel?"**
ADR-0024: Citations-before-LLM-Pattern -- Quellenmetadaten aus Retrieval-Ergebnis
extrahiert und vor dem LLM-Call als Faktenliste befestigt. Keine Artikel-Nummer
kommt aus dem Modellwissen.

**"Warum kein Semantic Caching?"**
ADR-0034: 0,003 EUR/Case macht Cache-Komplexitaet wirtschaftlich sinnlos;
dazu PII-in-Cache-Risiko und niedrige Hit-Rate bei semantisch einzigartigen
Einreichungen.

**"Warum kein JWT/RBAC?"**
ADR-006: Single-Tenant-Build, ein API-Key, ein Nutzer -- dokumentierte
Upgrade-Condition: Mehrbenutzerbetrieb wuerde RBAC erfordern.

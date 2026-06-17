# ADR-0016: Lokaler Embedding-Adapter -- SentenceTransformerEmbedder

**Status:** Accepted
**Datum:** 2026-06-17
**Autor:** Anas

## Kontext

EmbedderPort (ADR-0015) definiert den Embedding-Kontrakt mock-first. Heute die
erste echte Implementierung: lokale Inferenz ueber sentence-transformers. Das
ist bewusst die kostenlose, lokale Variante zuerst -- session-protocol v3 SS4
("Budget-Sentinel Embeddings: Fallback zuerst: sentence-transformers lokal.
Azure-Indexing erst danach"). Der Azure-Embedding-Adapter (EU Data Zone) ist
ein bewusster Folge-Tag.

## Entscheidung

1. Platzierung: src/aect/adapters/rag/embedder.py (neues Paket adapters/rag/).
   Echte Adapter -> eigenes Paket; Mocks bleiben in adapters/in_memory/ --
   exakt das LLM-Muster (AzureOpenAIAdapter in adapters/llm/, MockLLMAdapter in
   adapters/in_memory/). Nebeneffekt: adapters/rag/ existiert nun -> die
   Phasen-Erkennung (SS1 Schritt 2) liest endlich "Phase D" statt der
   Uebergangslage aus ADR-0014/0015.
2. Modell: all-MiniLM-L6-v2 (384-dim, ~80 MB, CPU-tauglich auf ARM).
3. Constructor DI: das Modell wird injiziert, nicht im Adapter konstruiert
   (analog AzureOpenAIAdapter-Client). Folge: src/ bleibt import-frei von
   sentence-transformers/torch -> normale Testlaeufe und mypy src/ ohne Torch.
4. Blockierende .encode() in asyncio.to_thread (EmbedderPort ist async).
5. Tests: Unit-Tests mit Fake-Encoder (torch-frei) + skipbarer Live-Test
   (AECT_RUN_EMBEDDER_LIVE=1) als einmaliger Realitaets-Check.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Adapter baut Modell selbst (from_pretrained in src/) | Wuerde torch/sentence-transformers in src/ ziehen -> jeder Testlauf + mypy src/ zahlt den Torch-Import + untyped-Import-Frage. DI haelt das draussen, konsistent mit AzureOpenAIAdapter, der seinen Client auch nicht selbst baut. |
| Echten Adapter in adapters/in_memory/ ablegen | Vermischt Mock und Real; widerspricht dem LLM-Muster. |
| Wertebereich [0,1] zusichern (wie MockEmbedder) | Falscher Kontrakt -- echte Modelle liefern beliebige Floats inkl. negativer. Der Adapter verspricht nur die Form (ein Vektor pro Text, Reihenfolge), nicht den Wertebereich. |
| DI-Verdrahtung heute | Kein Consumer (kein Indexer/Service ruft embed()). Spekulativ, YAGNI -- Verdrahtung am Indexing-/Pipeline-Tag. |
| PII-Redaction im Adapter | Falsche Schicht -- gehoert in die Indexing-Pipeline vor embed() (Single Responsibility), Indexing-Tag. |
| Exakte Gleichheit fuer Determinismus-Test im Live-Test | Falsche Annahme aus dem Mock uebernommen: torch verteilt CPU-Inferenz auf mehrere Threads, Floating-Point-Summation ist nicht assoziativ -- zwei Aufrufe desselben Texts unterscheiden sich minimal (beobachtet: ~5e-8, float32-Praezisionsgrenze). EmbedderPort verspricht Form + Reihenfolge (ADR-0015), keine Bit-Identitaet. Fix: Toleranzvergleich (math.isclose) statt ==. Bewusst kein torch.set_num_threads(1) -- globaler Seiteneffekt fuer ein Problem, das Cosine-Similarity-basiertes Retrieval nicht beruehrt. |

## Konsequenzen

**Positiv:**
- Erste echte Vektoren, kostenlos und lokal.
- src/ und der Standard-Testlauf bleiben torch-frei; Torch laeuft nur im
  scharfen Live-Lauf.
- adapters/rag/ existiert -> Phasentabelle liest endlich "Phase D".

**Negativ / Trade-offs:**
- SentenceTransformerEmbedder ist bis zur Verdrahtung unbenutzter Adapter --
  kein nutzer-sichtbarer Effekt heute.
- Echte Inferenz wird nur im skipbaren Live-Test geprueft -- die Standard-Suite
  testet den Adapter ueber den Fake (Kontrakt: Form, Reihenfolge,
  Determinismus), nicht die Modellqualitaet. Bewusst.

**Neutral / Folgeentscheidungen:**
- Azure-Embedding-Adapter (EU Data Zone, SS4 Budget-Sentinel).
- ChromaDB-Persistenz inkl. Dimensions-Fixierung pro Collection (384).
- Chunker-DTO, Hybrid Search (BM25 + Vektor + RRF), Cross-Encoder-Reranking,
  Service-Verdrahtung.
- PII-Redaction-Pipeline vor dem Embedding (LLM08) am Indexing-Tag.

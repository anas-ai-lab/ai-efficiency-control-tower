# ADR-0014: RAG-Retrieval-Kontrakt -- RetrieverPort + RetrievedChunk (Mock-First)

**Status:** Accepted
**Datum:** 2026-06-17
**Autor:** Anas

## Kontext

Phase D fuehrt belegte Hinweise ein: Compliance-/Stack-Wissen wird nicht aus
Modellwissen erzeugt, sondern aus kuratierten Quellen geholt und mit Quelle
zitiert (Projekt-Prinzip "Regeln vor LLM", Master-Plan v3.1 Phase D). Bevor echte Suche
(Embeddings, ChromaDB, BM25, Hybrid + Reranking) gebaut wird, braucht es einen
stabilen Kontrakt, gegen den der spaetere Service arbeitet -- analog dem
LLM-Port (ADR-0003/ADR-0005), der die LLM-Integration mock-first eroeffnet hat.

Das C->D-Gate ist geschlossen (Budget-Sentinel, 16.06.2026); Phase-D-Code ist
freigegeben.

## Entscheidung

Wir definieren den Retrieval-Kontrakt und einen deterministischen Mock, ohne
echte Suche und ohne bestehenden Code zu aendern:

1. application/ports/retriever.py:
   - RetrievedChunk (frozen dataclass): text, source_id, score.
   - RetrieverPort (Protocol): async def retrieve(query, top_k=5)
     -> list[RetrievedChunk]; Rueckgabe nach Relevanz absteigend, hoechstens
     top_k, leere Liste wenn nichts passt.
2. adapters/in_memory/retriever.py: MockRetriever -- feste synthetische
   Wissensbasis, deterministische Bewertung nach Query-Token-Treffern.
3. knowledge_base/ erhaelt eine README mit der Kuratierungs-/Provenienz-Policy
   (Inhalt der echten Quellen folgt als Markdown-Dateien an Folge-Tagen).

source_id ist von Anfang an Pflichtfeld -- Doppelzweck: Citation-Anker
(Phase-D-Gate verlangt [1]/[2]-Citations) und Loesch-Tag fuer gezielte
Quellen-Entfernung (aect-security-checklist v2.1, Phase D).

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Sofort echte Suche (ChromaDB/Embeddings) ohne Port-Mock | Nicht-deterministisch, Setup-/Kosten-Last am Tag 1; widerspricht Mock-First (ADR-0003) und Local-first. Erst Kontrakt + Mock gruen, dann echte Adapter. |
| Pydantic-Schema fuer RetrievedChunk statt dataclass | RetrievedChunk ist ein intern erzeugtes Wertobjekt aus kuratierten Quellen, kein aus untrusted Provider-JSON deserialisiertes Schema (anders als SharpenedContentV2, ADR-0013). Frozen dataclass ist konsistent mit LLMMessage/LLMResponse. Der Inhalt (text) bleibt trotzdem untrusted und wird beim Prompt-Aufbau via Delimiter als Daten abgegrenzt. |
| Synchroner Port | Der Service-/FastAPI-Layer ist async; ein synchroner, potenziell rechenintensiver Retrieval-Call (Embedding-Compute) wuerde den Event-Loop blockieren. async + asyncio.to_thread-Kapselung synchroner Bibliotheken im Adapter (Folge-Tag) haelt den Loop frei. |
| Getrennte Chunk- und RetrievedChunk-Typen jetzt | Kein Chunker an diesem Tag -> ein Stored-Chunk-Typ ohne Erzeuger waere spekulativ (YAGNI). RetrievedChunk (mit score) reicht fuer Port + Mock. |
| LangChain/LlamaIndex-Retriever-Abstraktion | Framework-Lock-in ohne Mehrwert; eigener Port leistet dasselbe projektspezifisch (gleiche Begruendung wie ADR-0003 fuer den LLM-Port). |

## Konsequenzen

**Positiv:**
- Additiv: kein bestehender Code geaendert, isoliert testbar ohne echte Suche.
- Service-Verdrahtung, Embedding-Provider und ChromaDB werden gegen einen
  feststehenden Kontrakt gebaut -- kleinere, fokussiertere Folge-Tage.
- Provenienz (source_id) ist ab dem ersten Tag erzwungen -> Citations und
  gezielte Loeschung sind by design, nicht nachgeruestet.

**Negativ / Trade-offs:**
- RetrieverPort ist bis zur Service-Verdrahtung unbenutzter Kontrakt -- kein
  nutzer-sichtbarer Effekt heute.
- Phase-Erkennung (session-protocol v3 SS1 Schritt 2) keyt auf adapters/rag/;
  das existiert nach diesem Tag noch nicht (Mock liegt in adapters/in_memory/,
  analog MockLLMAdapter). Die bare Tabelle meldet daher naechste Session noch
  "Phase C" -- aufzuloesen ueber das bereits geschlossene C->D-Gate + Daily
  Note, nicht ueber die Tabelle allein. Gleiche Lage wie im Mock-First-Fenster
  von Phase C.

**Neutral / Folgeentscheidungen:**
- Embedding-Provider (sentence-transformers lokal vs. Azure EU Data Zone),
  ChromaDB-Persistenz, BM25, Hybrid + RRF, Cross-Encoder-Reranking,
  Chunker-DTO, Citation-Rendering und die Service-Verdrahtung sind bewusst
  Folge-Tage.
- PII-Redaction vor dem Embedding (LLM08, aect-security-checklist v2.1 Phase D)
  ist dokumentierte Pflicht fuer den Embedding-Tag -- heute nicht relevant
  (keine Embeddings).

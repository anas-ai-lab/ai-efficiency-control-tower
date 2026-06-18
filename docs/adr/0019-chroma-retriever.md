# 0019 - ChromaRetriever (Vektor-Suche gegen den lokalen Container)

Status: Accepted
Datum: 2026-06-19
Kontext: Phase D, RetrieverPort (ADR-0014), Embedder (ADR-0015/0016),
ChromaDB-Container (ADR-0018)

## Kontext

MockRetriever (ADR-0014) liefert deterministische Treffer ueber naives
Token-Matching. Fuer belegte Compliance-/Stack-Hinweise braucht es echte
semantische Suche gegen die ChromaDB-Collection im Container.

## Entscheidung

1. **Query-Embedding ueber denselben EmbedderPort wie die Indexierung.**
   ChromaRetriever embeddet die Query selbst und ruft Chroma mit
   query_embeddings auf -- Chroma ist reiner Vektor-Store, nicht Embedding-
   Engine. Die collection-interne Embedding-Funktion bleibt ungenutzt.
   Grund: Index und Query MUESSEN dasselbe Modell verwenden, sonst sind die
   Vektoren nicht im selben Raum und die Aehnlichkeit ist bedeutungslos.
   Ein zweiter, abweichender Embedding-Pfad (Chroma-Default) waere genau diese
   Falle.

2. **Constructor DI ueber strukturelles Protokoll (ChromaCollection).**
   Collection und Embedder werden injiziert. Das Modul importiert chromadb
   nie -> normale Testlaeufe und mypy auf src/ ziehen kein chromadb (analog
   SentenceTransformerEmbedder/EncoderModel, ADR-0016). Der chromadb-Client
   wird erst beim Verdrahten bzw. im Live-Test gebaut.

3. **Score = 1 / (1 + distance).** Chroma liefert Distanzen (kleiner = naeher);
   RetrievedChunk.score ist "hoeher = relevanter". Die Transformation ist
   monoton fallend, positiv, metrik-unabhaengig (L2 oder Cosine). Nur fuer
   Anzeige/Reihenfolge, nie fuer Berechnungen (ports/retriever.py).

4. **async via asyncio.to_thread.** Der blockierende Netz-Call .query() laeuft
   im Thread, damit der Event-Loop frei bleibt (RetrieverPort ist async).

5. **Python-Paket: chromadb-client (HTTP-only) statt voll-chromadb.** Wir reden
   ausschliesslich ueber HTTP mit dem Container, nie Embedded-Mode -> der
   schlanke Client ohne Server-/onnxruntime-Deps ist der praezisere Fit.
   Voll-chromadb ist dokumentierter Fallback bei Versions-/Resolution-Problemen
   (gleicher Code).

## Konsequenzen

- Retrieval funktioniert ohne Container/Torch testbar (Fake-Collection +
  Fake-Embedder), echter Round-Trip env-gegated (AECT_RUN_CHROMA_LIVE=1).
- source_id traegt doppelt: Citation-Anker (Master-Plan Phase-D-Gate) und
  Loesch-Tag (Security-Checkliste Phase D).
- PII-Redaction vor dem Embedding ist NICHT Teil dieses Adapters -- sie gehoert
  in die Indexing-Pipeline (Folge-Tag).

## Bewusst nicht jetzt

- Verdrahtung in dependencies.py (get_retriever) + Settings.chroma_url: kein
  Konsument vorhanden (Service ruft retrieve() erst beim Compliance-
  Verdrahtungs-Tag). Premature Wiring = Scope-Verstoss.
- Hybrid-Suche (BM25 + Vektor, RRF) und Reranking: spaetere Phase-D-Tage.

# 0022 -- KB-Live-Indexing: Schreib-Pfad in die ChromaDB-Collection

**Status:** Accepted
**Datum:** 2026-06-19
**Serie:** 000X (Phase-C/D-Serie, session-protocol v3 SS6.13)
**Kontext-Quelle:** Master-Plan v3.1 Phase D; aect-security-checklist v2.1 Phase D; ADR-0015 (EmbedderPort), ADR-0016 (lokaler Embedder), ADR-0019 (ChromaRetriever, gleiches Modell Index/Query), ADR-0021 (build_index_records offline/rein)

## Kontext

Vorhanden: der Lese-Pfad (ChromaRetriever, ADR-0019), der lokale Embedder
(SentenceTransformerEmbedder, ADR-0016) und die offline Record-Vorbereitung
(build_index_records, ADR-0021). Es fehlte das Bindeglied: die vorbereiteten
IndexRecords echt einbetten und in eine laufende ChromaDB-Collection schreiben
(Tag-53-Daily-Note "Naechster Schritt": KB live in Chroma indexieren).

ADR-0021 haelt build_index_records() ausdruecklich offline und frei von
Embedding-/Chroma-Imports. Der echte Upsert darf diese Reinheit nicht brechen.

## Entscheidung

1. **Eigenes Modul adapters/rag/indexer.py** statt Erweiterung von indexing.py:
   haelt build_index_records() rein (ADR-0021), kapselt asyncio + den
   Schreib-Zugriff getrennt.
2. **index_knowledge_base(kb_dir, collection, embedder) -> int**: baut Records,
   bettet ihre Texte ueber den injizierten EmbedderPort ein, schreibt sie in
   die injizierte Collection. Gibt die Anzahl geschriebener Records zurueck.
   Leere KB -> 0, kein Upsert.
3. **upsert statt add**: idempotenter Re-Seed. Gleiche Chunk-id
   ("<source_id>:<index>", ADR-0017) ueberschreibt denselben Eintrag, statt an
   doppelten ids zu scheitern.
4. **metadatas werden jetzt schon mitgeschrieben** (citation/title/url/
   source_id/chunk_index aus IndexRecord.metadata), obwohl der Lese-Pfad sie
   noch nicht zurueckgibt (RetrievedChunk ohne metadata-Feld, ADR-0021). Der
   Citation-Lese-Pfad (Folge-Tag) aendert dann nur den Retriever, nicht den
   Index.
5. **Injizierte Collection + Embedder, kein chromadb/torch-Import in src/**:
   die reale Verdrahtung (HttpClient, MiniLM-Modell) lebt ausschliesslich im
   skipbaren Live-Test (analog test_retriever_live.py / test_embedder_live.py).
   src/ bleibt frei von schweren, untypisierten Imports; mypy auf src/ und der
   normale Testlauf ziehen weder chromadb noch torch.
6. **IndexableCollection (Protocol, nur .upsert)**: schmaler struktureller Typ,
   erfuellt von chromadb.Collection und einem Test-Fake -- analog
   ChromaCollection (.query) in retriever.py.

## Sicherheit (aect-security-checklist v2.1 Phase D)

- **PII-Redaction vor Embedding (LLM08): bewusst nicht umgesetzt.** Indexiert
  wird ausschliesslich kuratierter oeffentlicher Rechtstext (DSGVO, KI-VO),
  kein personenbezogener Inhalt (ADR-0021). Der Redactor gehoert auf den
  User-Case-/Query-Pfad (eigenes Gate-Thema "PII-Redaction"), Folge-Tag.
- **Nur kuratierte Quellen:** index_knowledge_base liest ausschliesslich
  knowledge_base/ (README uebersprungen, ADR-0021). Kein firmenspezifischer
  Inhalt (vertraglich bedingte IP-Trennung).
- **Records taggen / Provenance:** source_id im id-Prefix UND in metadata;
  citation/title/url als Metadaten mitgeschrieben.
- **127.0.0.1-only-Container (ADR-0018):** der Live-Test verbindet gegen
  127.0.0.1:8001, keine Netz-Exposition.

## Konsequenzen

- **Positiv:** voller Index->Retrieve-Round-Trip gegen den echten Container ist
  (mit Flag) belegbar; metadatas liegen ab jetzt im Store, der
  Citation-Lese-Pfad wird ein reiner Retriever-Change.
- **Negativ / Trade-off:** index_knowledge_base ist bis zur App-Verdrahtung
  ohne produktiven Aufrufer -- wie EmbedderPort/RetrieverPort vor ihrer
  Verdrahtung (ADR-0014/0015, bewusst additiv).
- **Neutral / Folge-Tage:** Citation-Lese-Pfad (RetrievedChunk.metadata +
  ChromaRetriever._parse + query-include um metadatas), persistenter
  Seed-Entrypoint mit stabilem Collection-Namen fuer die App-Verdrahtung,
  Hybrid-Suche (BM25+RRF) und Reranking.

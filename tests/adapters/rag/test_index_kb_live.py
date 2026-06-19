"""Live-Test: echtes Index -> Retrieve gegen den lokalen ChromaDB-Container.

Standardmaessig geskippt. Aktivieren mit AECT_RUN_CHROMA_LIVE=1 BEI laufendem
Container (docker compose up -d). Analog test_retriever_live.py: der einmalige
Realitaets-Check, nicht Teil des normalen Laufs -- so importiert pytest weder
chromadb noch torch. Beide Imports stehen bewusst in der Testfunktion.

Indexiert die ECHTEN knowledge_base/-Dateien (build_index_records ueber den
realen Pfad) in eine Wegwerf-Collection, fragt sie ab und raeumt sie im finally
wieder weg. Beweist den vollen Schreib- und Lese-Pfad: Datei -> Chunk ->
echtes Embedding -> upsert -> query -> zurueckgegebene Quelle.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

_RUN_LIVE = os.getenv("AECT_RUN_CHROMA_LIVE") == "1"


@pytest.mark.skipif(
    not _RUN_LIVE,
    reason="AECT_RUN_CHROMA_LIVE=1 setzen, Container muss laufen.",
)
async def test_index_real_kb_and_retrieve() -> None:
    import chromadb
    from sentence_transformers import SentenceTransformer

    from aect.adapters.rag.embedder import SentenceTransformerEmbedder
    from aect.adapters.rag.indexer import index_knowledge_base
    from aect.adapters.rag.retriever import ChromaRetriever

    kb_dir = Path(__file__).resolve().parents[3] / "knowledge_base"
    client = chromadb.HttpClient(host="127.0.0.1", port=8001)
    # Index und Query teilen sich denselben Embedder (ADR-0019).
    embedder = SentenceTransformerEmbedder(SentenceTransformer("all-MiniLM-L6-v2"))

    collection_name = f"aect-index-live-{uuid.uuid4().hex[:8]}"
    collection = client.get_or_create_collection(name=collection_name)
    try:
        count = await index_knowledge_base(kb_dir, collection, embedder)
        assert count >= 2  # mindestens die beiden kuratierten KB-Files

        retriever = ChromaRetriever(collection, embedder)
        results = await retriever.retrieve(
            "Wann ist eine Datenschutz-Folgenabschaetzung noetig?", top_k=3
        )
        assert results, "Erwartet mindestens einen Treffer"
        # source_id ist heute die Chunk-id "<source_id>:<index>"
        # (Citation-Lese-Pfad ist Folge-Tag, ADR-0021) -> Prefix pruefen.
        assert any(chunk.source_id.startswith("dsgvo-art-35-dsfa") for chunk in results)
        assert all(chunk.score > 0.0 for chunk in results)
    finally:
        client.delete_collection(name=collection_name)

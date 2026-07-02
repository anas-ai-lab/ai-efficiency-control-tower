"""Live-Test: echter Round-Trip gegen den lokalen ChromaDB-Container.

Standardmaessig geskippt. Aktivieren mit AECT_RUN_CHROMA_LIVE=1 BEI laufendem
Container (docker compose up -d). Analog test_embedder_live.py /
test_azure_openai_live.py: der einmalige Realitaets-Check, nicht Teil des
normalen Laufs -- so importiert pytest weder chromadb noch torch. Beide Imports
stehen bewusst in der Testfunktion.

Seedet eine wegwerfbare Collection mit 3 synthetischen Chunks (kein PII, keine
kuratierten Quellen -- vertraglich bedingte IP-Trennung) INKLUSIVE Provenance-
Metadaten, fragt sie ab und raeumt sie im finally wieder weg. Prueft seit
ADR-0023 zusaetzlich, dass die citation-Metadaten den Round-Trip ueberleben --
nicht nur die source_id.
"""

from __future__ import annotations

import os
import uuid

import pytest

_RUN_LIVE = os.getenv("AECT_RUN_CHROMA_LIVE") == "1"


@pytest.mark.skipif(
    not _RUN_LIVE,
    reason="AECT_RUN_CHROMA_LIVE=1 setzen, Container muss laufen.",
)
async def test_chroma_retriever_real_round_trip() -> None:
    import chromadb
    from sentence_transformers import SentenceTransformer

    from aect.adapters.rag.embedder import SentenceTransformerEmbedder
    from aect.adapters.rag.retriever import ChromaRetriever

    client = chromadb.HttpClient(host="127.0.0.1", port=8001)
    embedder = SentenceTransformerEmbedder(SentenceTransformer("all-MiniLM-L6-v2"))

    documents = [
        "Open WebUI ist eine selbst-gehostete Chatoberflaeche fuer LLMs.",
        "Eine Datenschutz-Folgenabschaetzung prueft Risiken fuer Betroffene.",
        "Reciprocal Rank Fusion kombiniert mehrere Ergebnislisten.",
    ]
    source_ids = ["live-open-webui", "live-dsfa", "live-rrf"]
    metadatas = [
        {"source_id": "live-open-webui", "citation": "Stack-Doku (synthetisch)"},
        {"source_id": "live-dsfa", "citation": "DSGVO Art. 35 (synthetisch)"},
        {"source_id": "live-rrf", "citation": "Retrieval-Doku (synthetisch)"},
    ]

    collection_name = f"aect-live-{uuid.uuid4().hex[:8]}"
    collection = client.get_or_create_collection(name=collection_name)
    try:
        vectors = await embedder.embed(documents)
        collection.add(
            ids=source_ids,
            embeddings=[list(vector) for vector in vectors],
            documents=documents,
            metadatas=metadatas,
        )

        retriever = ChromaRetriever(collection, embedder)
        results = await retriever.retrieve(
            "Wann ist eine Datenschutz-Folgenabschaetzung noetig?", top_k=2
        )

        assert results, "Erwartet mindestens einen Treffer"
        # Relevante Quelle muss in den Top-2 auftauchen (semantischer Treffer);
        # exakte Rang-1-Position waere modellabhaengig flaky.
        assert "live-dsfa" in [chunk.source_id for chunk in results]
        assert all(chunk.source_id for chunk in results)  # Citation-Anker da

        dsfa_chunk = next(c for c in results if c.source_id == "live-dsfa")
        assert dsfa_chunk.metadata["citation"] == "DSGVO Art. 35 (synthetisch)"
    finally:
        client.delete_collection(name=collection_name)

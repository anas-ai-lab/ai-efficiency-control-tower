# scripts/gate_check_phase_d.py
"""Manueller RAG-Pfad-Check fuer das Phase-D-Gate (session-protocol v3 SS2).

Fragt den echten Hybrid+Reranking-Pfad (ChromaRetriever + BM25Retriever +
HybridRetriever + CrossEncoderReranker) direkt ab, ohne Service-Schicht/
FastAPI -- mit einer bewusst themenfremden Query, die in den fixen
canonical Queries aus application/service.py (_TRANSPARENCY_QUERY/
_DSFA_QUERY) nicht vorkommt. Zweck: pruefen, ob das Retrieval eine
Relevanz-Schwelle hat oder top_k unbedingt liefert (Gate-Check Tag 61).

Voraussetzung: `docker compose up -d` + `uv run python scripts/seed_knowledge_base.py`
bereits gelaufen.

Aufruf:
    uv run python scripts/gate_check_phase_d.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

from aect.adapters.rag.bm25_retriever import BM25Retriever, build_bm25_index
from aect.adapters.rag.embedder import SentenceTransformerEmbedder
from aect.adapters.rag.hybrid_retriever import HybridRetriever
from aect.adapters.rag.indexing import build_index_records
from aect.adapters.rag.reranker import CrossEncoderReranker
from aect.adapters.rag.retriever import ChromaRetriever

_KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
_CHROMA_HOST = "127.0.0.1"
_CHROMA_PORT = 8001
_COLLECTION_NAME = "aect-knowledge-base"

_OFF_TOPIC_QUERY = "Mittagessen Kantine Speiseplan Wochenmenue"


async def main() -> None:
    client = chromadb.HttpClient(host=_CHROMA_HOST, port=_CHROMA_PORT)
    collection = client.get_or_create_collection(name=_COLLECTION_NAME)
    embedder = SentenceTransformerEmbedder(SentenceTransformer("all-MiniLM-L6-v2"))
    vector_retriever = ChromaRetriever(collection, embedder)

    records = build_index_records(_KB_DIR)
    bm25_index = build_bm25_index(records)
    bm25_retriever = BM25Retriever(bm25_index)

    hybrid = HybridRetriever(vector_retriever, bm25_retriever)
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    retriever = CrossEncoderReranker(hybrid, cross_encoder)

    results = await retriever.retrieve(_OFF_TOPIC_QUERY, top_k=2)

    print(f"Query: {_OFF_TOPIC_QUERY!r}")
    print(f"Treffer: {len(results)}")
    for chunk in results:
        print(f"  source_id={chunk.source_id} score={chunk.score:.4f}")
        print(f"  citation={chunk.metadata.get('citation')}")
        print(f"  text[:120]={chunk.text[:120]!r}")


if __name__ == "__main__":
    asyncio.run(main())

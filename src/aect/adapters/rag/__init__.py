"""RAG-Adapter (Phase D): echte Embedding-/Retrieval-Implementierungen
sowie der Chunker (deterministische Funktion ohne Port, ADR-0017), die
KB-Indexing-Vorbereitung (ADR-0021), der KB-Schreib-Pfad (ADR-0022) und
der Hybrid-Retrieval-Pfad (BM25 + Vektor + RRF, ADR-0027).

Mock-Varianten liegen weiterhin in adapters/in_memory/ (MockEmbedder,
MockRetriever); hier leben die echten Provider-Adapter -- analog dazu, dass
der echte AzureOpenAIAdapter in adapters/llm/ liegt, der MockLLMAdapter aber
in adapters/in_memory/.
"""

from aect.adapters.rag.bm25_retriever import BM25Index, BM25Retriever, build_bm25_index
from aect.adapters.rag.chunker import Chunk, chunk_document
from aect.adapters.rag.embedder import SentenceTransformerEmbedder
from aect.adapters.rag.hybrid_retriever import HybridRetriever
from aect.adapters.rag.indexer import index_knowledge_base
from aect.adapters.rag.indexing import (
    IndexRecord,
    build_index_records,
    parse_kb_document,
)
from aect.adapters.rag.retriever import ChromaRetriever

__all__ = [
    "BM25Index",
    "BM25Retriever",
    "ChromaRetriever",
    "Chunk",
    "HybridRetriever",
    "IndexRecord",
    "SentenceTransformerEmbedder",
    "build_bm25_index",
    "build_index_records",
    "chunk_document",
    "index_knowledge_base",
    "parse_kb_document",
]

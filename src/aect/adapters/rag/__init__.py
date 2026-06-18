"""RAG-Adapter (Phase D): echte Embedding-/Retrieval-Implementierungen
sowie der Chunker (deterministische Funktion ohne Port, ADR-0017).

Mock-Varianten liegen weiterhin in adapters/in_memory/ (MockEmbedder,
MockRetriever); hier leben die echten Provider-Adapter -- analog dazu, dass
der echte AzureOpenAIAdapter in adapters/llm/ liegt, der MockLLMAdapter aber
in adapters/in_memory/.
"""

from aect.adapters.rag.chunker import Chunk, chunk_document
from aect.adapters.rag.embedder import SentenceTransformerEmbedder

__all__ = ["Chunk", "SentenceTransformerEmbedder", "chunk_document"]

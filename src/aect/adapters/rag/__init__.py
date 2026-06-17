"""RAG-Adapter (Phase D): echte Embedding-/Retrieval-Implementierungen.

Mock-Varianten liegen weiterhin in adapters/in_memory/ (MockEmbedder,
MockRetriever); hier leben die echten Provider-Adapter -- analog dazu, dass
der echte AzureOpenAIAdapter in adapters/llm/ liegt, der MockLLMAdapter aber
in adapters/in_memory/.
"""

from aect.adapters.rag.embedder import SentenceTransformerEmbedder

__all__ = ["SentenceTransformerEmbedder"]

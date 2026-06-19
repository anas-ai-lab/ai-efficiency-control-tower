"""Einmaliges Seeding der echten ChromaDB-Knowledge-Base (Phase D, ADR-0025).

Liest die kuratierten Markdown-Dateien aus knowledge_base/, bettet sie ueber
das lokale sentence-transformers-Modell ein und schreibt sie in die
persistente Chroma-Collection "aect-knowledge-base" (docker-compose,
127.0.0.1:8001, ADR-0018). Idempotent: index_knowledge_base() arbeitet mit
upsert() (gleiche Chunk-id ueberschreibt denselben Eintrag) -- mehrfaches
Ausfuehren ist sicher.

Voraussetzung: `docker compose up -d` (Container muss laufen).

Aufruf:
    uv run python scripts/seed_knowledge_base.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from aect.adapters.rag.embedder import SentenceTransformerEmbedder
from aect.adapters.rag.indexer import index_knowledge_base

_KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
_CHROMA_HOST = "127.0.0.1"
_CHROMA_PORT = 8001
_COLLECTION_NAME = "aect-knowledge-base"


async def main() -> None:
    client = chromadb.HttpClient(host=_CHROMA_HOST, port=_CHROMA_PORT)
    collection = client.get_or_create_collection(name=_COLLECTION_NAME)
    embedder = SentenceTransformerEmbedder(SentenceTransformer("all-MiniLM-L6-v2"))

    count = await index_knowledge_base(_KB_DIR, collection, embedder)
    print(f"Indexiert: {count} Chunks aus {_KB_DIR} in Collection '{_COLLECTION_NAME}'")


if __name__ == "__main__":
    asyncio.run(main())

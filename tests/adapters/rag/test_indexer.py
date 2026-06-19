"""Unit-Tests fuer index_knowledge_base() -- Fake-Collection + Fake-Embedder.

Kein chromadb, kein Torch, kein Container: die Funktion haengt nur an den
strukturellen Protokollen IndexableCollection und EmbedderPort sowie am reinen
build_index_records() (ueber echte tmp_path-Dateien).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from aect.adapters.rag.indexer import index_knowledge_base

_FRONT_MATTER = (
    "---\n"
    "source_id: doc-a\n"
    "title: Test Doc A\n"
    "citation: Quelle A\n"
    "---\n"
    "\n"
    "Erster Absatz mit Inhalt.\n"
)


class _FakeEmbedder:
    """Liefert einen festen Vektor pro Text, protokolliert die Aufrufe."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        self.calls.append(list(texts))
        return [(0.1, 0.2, 0.3) for _ in texts]


class _FakeCollection:
    """Merkt sich die upsert-Argumente, schreibt nichts."""

    def __init__(self) -> None:
        self.upsert_kwargs: dict[str, object] | None = None

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[Mapping[str, str]],
    ) -> None:
        self.upsert_kwargs = {
            "ids": ids,
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas,
        }


@pytest.fixture
def embedder() -> _FakeEmbedder:
    return _FakeEmbedder()


async def test_index_writes_records_to_collection(
    tmp_path: Path, embedder: _FakeEmbedder
) -> None:
    (tmp_path / "a.md").write_text(_FRONT_MATTER, encoding="utf-8")
    collection = _FakeCollection()
    count = await index_knowledge_base(tmp_path, collection, embedder)
    assert count == 1
    assert collection.upsert_kwargs is not None
    assert collection.upsert_kwargs["ids"] == ["doc-a:0"]


async def test_index_passes_citation_metadata(
    tmp_path: Path, embedder: _FakeEmbedder
) -> None:
    (tmp_path / "a.md").write_text(_FRONT_MATTER, encoding="utf-8")
    collection = _FakeCollection()
    await index_knowledge_base(tmp_path, collection, embedder)
    assert collection.upsert_kwargs is not None
    metadatas = collection.upsert_kwargs["metadatas"]
    assert metadatas[0]["citation"] == "Quelle A"
    assert metadatas[0]["source_id"] == "doc-a"
    assert metadatas[0]["chunk_index"] == "0"


async def test_index_embeds_each_document(
    tmp_path: Path, embedder: _FakeEmbedder
) -> None:
    (tmp_path / "a.md").write_text(_FRONT_MATTER, encoding="utf-8")
    collection = _FakeCollection()
    await index_knowledge_base(tmp_path, collection, embedder)
    assert embedder.calls == [["Erster Absatz mit Inhalt."]]


async def test_index_empty_kb_skips_upsert(
    tmp_path: Path, embedder: _FakeEmbedder
) -> None:
    collection = _FakeCollection()
    count = await index_knowledge_base(tmp_path, collection, embedder)
    assert count == 0
    assert collection.upsert_kwargs is None
    assert embedder.calls == []


async def test_index_embeddings_match_document_count(
    tmp_path: Path, embedder: _FakeEmbedder
) -> None:
    body = "\n\n".join(f"Absatz Nummer {i} mit etwas Text." for i in range(60))
    text = f"---\nsource_id: big\ntitle: T\ncitation: C\n---\n\n{body}\n"
    (tmp_path / "big.md").write_text(text, encoding="utf-8")
    collection = _FakeCollection()
    count = await index_knowledge_base(tmp_path, collection, embedder)
    assert collection.upsert_kwargs is not None
    assert len(collection.upsert_kwargs["embeddings"]) == count
    assert len(collection.upsert_kwargs["documents"]) == count

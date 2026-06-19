"""Unit-Tests fuer ChromaRetriever -- mit Fake-Collection + Fake-Embedder.

Kein chromadb-Import, kein Torch, kein Container: der Adapter haengt nur an den
strukturellen Protokollen ChromaCollection und EmbedderPort.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from aect.adapters.rag.retriever import ChromaRetriever


class _FakeEmbedder:
    """Liefert einen festen Vektor pro Text, protokolliert die Aufrufe."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        self.calls.append(list(texts))
        return [(0.1, 0.2, 0.3) for _ in texts]


class _FakeCollection:
    """Gibt eine feste Chroma-query-Antwort zurueck, merkt sich die Argumente."""

    def __init__(self, response: Mapping[str, Any]) -> None:
        self._response = response
        self.last_n_results: int | None = None
        self.last_query_embeddings: list[list[float]] | None = None
        self.last_include: list[str] | None = None

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
        include: list[str],
    ) -> Mapping[str, Any]:
        self.last_n_results = n_results
        self.last_query_embeddings = query_embeddings
        self.last_include = include
        return self._response


def _response(
    ids: list[str],
    documents: list[str],
    distances: list[float],
    metadatas: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Chroma verschachtelt pro Query eine Ergebnisliste -> [[...]]."""
    response: dict[str, Any] = {
        "ids": [ids],
        "documents": [documents],
        "distances": [distances],
    }
    if metadatas is not None:
        response["metadatas"] = [metadatas]
    return response


@pytest.fixture
def embedder() -> _FakeEmbedder:
    return _FakeEmbedder()


async def test_retrieve_maps_chroma_response_to_chunks(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(
        _response(
            ids=["src-a", "src-b"],
            documents=["text a", "text b"],
            distances=[0.1, 0.4],
        )
    )
    retriever = ChromaRetriever(collection, embedder)
    results = await retriever.retrieve("query")
    assert [chunk.source_id for chunk in results] == ["src-a", "src-b"]
    assert [chunk.text for chunk in results] == ["text a", "text b"]


async def test_retrieve_embeds_query_before_search(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(_response(["s"], ["t"], [0.2]))
    retriever = ChromaRetriever(collection, embedder)
    await retriever.retrieve("open webui")
    assert embedder.calls == [["open webui"]]
    assert collection.last_query_embeddings == [[0.1, 0.2, 0.3]]


async def test_retrieve_forwards_top_k_as_n_results(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(_response(["s"], ["t"], [0.2]))
    retriever = ChromaRetriever(collection, embedder)
    await retriever.retrieve("q", top_k=3)
    assert collection.last_n_results == 3


async def test_retrieve_requests_metadatas_explicitly(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(_response(["s"], ["t"], [0.2]))
    retriever = ChromaRetriever(collection, embedder)
    await retriever.retrieve("q")
    assert collection.last_include == ["documents", "distances", "metadatas"]


async def test_retrieve_score_positive_and_decreasing(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(_response(["a", "b"], ["ta", "tb"], [0.1, 0.9]))
    retriever = ChromaRetriever(collection, embedder)
    results = await retriever.retrieve("q")
    assert results[0].score > results[1].score
    assert all(chunk.score > 0.0 for chunk in results)


async def test_retrieve_empty_query_skips_collection(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(_response(["a"], ["ta"], [0.1]))
    retriever = ChromaRetriever(collection, embedder)
    results = await retriever.retrieve("   ")
    assert results == []
    assert collection.last_n_results is None
    assert embedder.calls == []


async def test_retrieve_empty_collection_returns_empty(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection({"ids": [[]], "documents": [[]], "distances": [[]]})
    retriever = ChromaRetriever(collection, embedder)
    assert await retriever.retrieve("q") == []


async def test_retrieve_handles_none_rows(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(
        {"ids": [["a"]], "documents": None, "distances": None, "metadatas": None}
    )
    retriever = ChromaRetriever(collection, embedder)
    results = await retriever.retrieve("q")
    assert len(results) == 1
    assert results[0].source_id == "a"
    assert results[0].text == ""
    assert results[0].metadata == {}


async def test_retrieve_includes_metadata_from_chroma_response(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(
        _response(
            ids=["dsgvo-art-35:0"],
            documents=["Eine DSFA ist erforderlich, wenn..."],
            distances=[0.05],
            metadatas=[
                {
                    "source_id": "dsgvo-art-35",
                    "title": "DSGVO Art. 35",
                    "citation": "DSGVO Art. 35",
                    "chunk_index": "0",
                }
            ],
        )
    )
    retriever = ChromaRetriever(collection, embedder)
    results = await retriever.retrieve("DSFA noetig?")
    assert results[0].metadata["citation"] == "DSGVO Art. 35"
    assert results[0].metadata["source_id"] == "dsgvo-art-35"


async def test_retrieve_missing_metadata_entry_defaults_to_empty(
    embedder: _FakeEmbedder,
) -> None:
    collection = _FakeCollection(
        _response(
            ids=["a", "b"],
            documents=["ta", "tb"],
            distances=[0.1, 0.2],
            metadatas=[{"citation": "Quelle A"}],
        )
    )
    retriever = ChromaRetriever(collection, embedder)
    results = await retriever.retrieve("q")
    assert results[0].metadata == {"citation": "Quelle A"}
    assert results[1].metadata == {}

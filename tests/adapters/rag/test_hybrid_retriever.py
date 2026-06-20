"""Unit-Tests fuer HybridRetriever -- mit zwei Fake-Sub-Retrievern.

Kein Chroma, kein BM25-Index: HybridRetriever haengt nur am RetrieverPort-
Kontrakt seiner beiden Sub-Retriever.
"""

from __future__ import annotations

from aect.adapters.rag.hybrid_retriever import HybridRetriever
from aect.application.ports.retriever import RetrievedChunk


def _chunk(source_id: str, text: str = "text") -> RetrievedChunk:
    return RetrievedChunk(text=text, source_id=source_id, score=1.0)


class _FakeRetriever:
    """Liefert eine feste Trefferliste, protokolliert das angefragte top_k."""

    def __init__(self, results: list[RetrievedChunk]) -> None:
        self._results = results
        self.last_top_k: int | None = None

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        self.last_top_k = top_k
        return self._results[:top_k]


async def test_combines_results_via_rrf() -> None:
    vector = _FakeRetriever([_chunk("a"), _chunk("b")])
    bm25 = _FakeRetriever([_chunk("b"), _chunk("a")])
    hybrid = HybridRetriever(vector, bm25)
    results = await hybrid.retrieve("q", top_k=5)
    # a: Rang 1 (vektor) + Rang 2 (bm25); b: Rang 2 (vektor) + Rang 1 (bm25)
    # -> bei rrf_k=60 identische Summe, first_seen_rank entscheidet (a zuerst).
    assert [c.source_id for c in results] == ["a", "b"]


async def test_first_position_in_both_lists_ranks_highest() -> None:
    vector = _FakeRetriever([_chunk("top"), _chunk("mid"), _chunk("low")])
    bm25 = _FakeRetriever([_chunk("top"), _chunk("other")])
    hybrid = HybridRetriever(vector, bm25)
    results = await hybrid.retrieve("q", top_k=5)
    assert results[0].source_id == "top"
    assert results[0].score > results[1].score


async def test_deduplicates_by_source_id() -> None:
    vector = _FakeRetriever([_chunk("a")])
    bm25 = _FakeRetriever([_chunk("a")])
    hybrid = HybridRetriever(vector, bm25)
    results = await hybrid.retrieve("q", top_k=5)
    assert len(results) == 1
    assert results[0].source_id == "a"


async def test_respects_top_k() -> None:
    vector = _FakeRetriever([_chunk(f"v{i}") for i in range(10)])
    bm25 = _FakeRetriever([_chunk(f"b{i}") for i in range(10)])
    hybrid = HybridRetriever(vector, bm25)
    results = await hybrid.retrieve("q", top_k=3)
    assert len(results) == 3


async def test_empty_from_both_returns_empty() -> None:
    hybrid = HybridRetriever(_FakeRetriever([]), _FakeRetriever([]))
    assert await hybrid.retrieve("q") == []


async def test_only_vector_has_results() -> None:
    vector = _FakeRetriever([_chunk("a"), _chunk("b")])
    bm25 = _FakeRetriever([])
    hybrid = HybridRetriever(vector, bm25)
    results = await hybrid.retrieve("q", top_k=5)
    assert [c.source_id for c in results] == ["a", "b"]


async def test_calls_subretrievers_with_candidate_pool_not_top_k() -> None:
    vector = _FakeRetriever([_chunk(f"v{i}") for i in range(20)])
    bm25 = _FakeRetriever([_chunk(f"b{i}") for i in range(20)])
    hybrid = HybridRetriever(vector, bm25, candidate_pool=7)
    await hybrid.retrieve("q", top_k=2)
    assert vector.last_top_k == 7
    assert bm25.last_top_k == 7

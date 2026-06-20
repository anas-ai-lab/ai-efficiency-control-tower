"""Unit-Tests fuer CrossEncoderReranker -- mit Fake-Inner-Retriever + Fake-Model.

Kein sentence-transformers-Import, kein Torch: der Reranker haengt nur an
RetrieverPort (innen) und dem strukturellen CrossEncoderModel-Protokoll.
"""

from __future__ import annotations

from aect.adapters.rag.reranker import CrossEncoderReranker
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


class _FakeCrossEncoder:
    """Bewertet Paare nach einer festen Lookup-Tabelle pro Dokumenttext."""

    def __init__(self, scores_by_text: dict[str, float]) -> None:
        self._scores_by_text = scores_by_text
        self.last_pairs: list[tuple[str, str]] | None = None

    def predict(self, sentences: list[tuple[str, str]]) -> list[float]:
        self.last_pairs = sentences
        return [self._scores_by_text[doc] for _, doc in sentences]


async def test_reorders_by_cross_encoder_score() -> None:
    inner = _FakeRetriever(
        [_chunk("a", text="irrelevant"), _chunk("b", text="relevant")]
    )
    model = _FakeCrossEncoder({"irrelevant": 0.1, "relevant": 9.0})
    reranker = CrossEncoderReranker(inner, model)
    results = await reranker.retrieve("q", top_k=2)
    assert [c.source_id for c in results] == ["b", "a"]


async def test_respects_top_k_after_reranking() -> None:
    inner = _FakeRetriever([_chunk(f"c{i}", text=f"doc{i}") for i in range(5)])
    model = _FakeCrossEncoder({f"doc{i}": float(i) for i in range(5)})
    reranker = CrossEncoderReranker(inner, model)
    results = await reranker.retrieve("q", top_k=2)
    assert len(results) == 2
    assert [c.source_id for c in results] == ["c4", "c3"]


async def test_calls_inner_with_candidate_pool_not_top_k() -> None:
    inner = _FakeRetriever([_chunk(f"c{i}", text=f"doc{i}") for i in range(20)])
    model = _FakeCrossEncoder({f"doc{i}": float(i) for i in range(20)})
    reranker = CrossEncoderReranker(inner, model, candidate_pool=12)
    await reranker.retrieve("q", top_k=3)
    assert inner.last_top_k == 12


async def test_empty_inner_results_returns_empty() -> None:
    inner = _FakeRetriever([])
    model = _FakeCrossEncoder({})
    reranker = CrossEncoderReranker(inner, model)
    assert await reranker.retrieve("q") == []


async def test_score_is_replaced_by_cross_encoder_score() -> None:
    inner = _FakeRetriever([_chunk("a", text="doc")])
    model = _FakeCrossEncoder({"doc": 4.2})
    reranker = CrossEncoderReranker(inner, model)
    results = await reranker.retrieve("q", top_k=1)
    assert results[0].score == 4.2


async def test_preserves_text_and_metadata() -> None:
    chunk = RetrievedChunk(
        text="some text", source_id="x", score=1.0, metadata={"citation": "Art. 5"}
    )
    inner = _FakeRetriever([chunk])
    model = _FakeCrossEncoder({"some text": 1.0})
    reranker = CrossEncoderReranker(inner, model)
    results = await reranker.retrieve("q", top_k=1)
    assert results[0].text == "some text"
    assert results[0].metadata == {"citation": "Art. 5"}


async def test_sends_query_paired_with_each_document_text() -> None:
    inner = _FakeRetriever([_chunk("a", text="alpha"), _chunk("b", text="beta")])
    model = _FakeCrossEncoder({"alpha": 1.0, "beta": 2.0})
    reranker = CrossEncoderReranker(inner, model)
    await reranker.retrieve("my query", top_k=2)
    assert model.last_pairs == [("my query", "alpha"), ("my query", "beta")]

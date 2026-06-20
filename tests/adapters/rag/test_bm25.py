"""Unit-Tests fuer BM25Index / BM25Retriever -- keine Dateien, kein I/O."""

from __future__ import annotations

from aect.adapters.rag.bm25_retriever import (
    BM25Index,
    BM25Retriever,
    build_bm25_index,
)
from aect.adapters.rag.indexing import IndexRecord


def _record(doc_id: str, text: str, **extra_metadata: str) -> IndexRecord:
    metadata = {"source_id": doc_id, "citation": f"Quelle {doc_id}", **extra_metadata}
    return IndexRecord(id=doc_id, document=text, metadata=metadata)


def test_score_returns_only_matching_documents() -> None:
    index = build_bm25_index(
        [
            _record("a", "Open WebUI ist eine selbst gehostete Chatoberflaeche"),
            _record("b", "Reciprocal Rank Fusion kombiniert Ergebnislisten"),
        ]
    )
    results = index.score("rank fusion", top_k=5)
    assert [chunk.source_id for chunk in results] == ["b"]


def test_score_orders_by_relevance_descending() -> None:
    index = build_bm25_index(
        [
            _record("low", "datenschutz wird einmal erwaehnt"),
            _record("high", "datenschutz datenschutz datenschutz ist zentral"),
        ]
    )
    results = index.score("datenschutz", top_k=5)
    assert [chunk.source_id for chunk in results] == ["high", "low"]
    assert results[0].score > results[1].score


def test_idf_rewards_rare_terms_over_common_terms() -> None:
    # "transparenz" kommt nur in einem Dokument vor (selten -> hoher idf),
    # "system" in beiden (haeufig -> niedriger idf). Bei gleicher
    # Termfrequenz muss der seltene Begriff staerker gewichtet werden.
    index = build_bm25_index(
        [
            _record("rare", "ki system transparenz pflicht"),
            _record("common", "ki system ist wichtig"),
        ]
    )
    results = index.score("transparenz", top_k=5)
    assert [chunk.source_id for chunk in results] == ["rare"]


def test_score_respects_top_k() -> None:
    index = build_bm25_index(
        [_record(f"doc-{i}", "open webui chatoberflaeche") for i in range(5)]
    )
    results = index.score("open webui", top_k=2)
    assert len(results) == 2


def test_score_empty_query_returns_empty() -> None:
    index = build_bm25_index([_record("a", "irgendein text")])
    assert index.score("", top_k=5) == []


def test_score_no_match_returns_empty() -> None:
    index = build_bm25_index([_record("a", "open webui")])
    assert index.score("kubernetes", top_k=5) == []


def test_score_empty_corpus_returns_empty() -> None:
    index = build_bm25_index([])
    assert index.score("irgendwas", top_k=5) == []


def test_retrieved_chunk_carries_metadata_from_record() -> None:
    index = build_bm25_index([_record("a", "open webui", url="https://example.org")])
    results = index.score("open webui", top_k=5)
    assert results[0].metadata["citation"] == "Quelle a"
    assert results[0].metadata["url"] == "https://example.org"


async def test_bm25_retriever_delegates_to_index() -> None:
    index = BM25Index([_record("a", "open webui chatoberflaeche")])
    retriever = BM25Retriever(index)
    results = await retriever.retrieve("open webui", top_k=3)
    assert results[0].source_id == "a"

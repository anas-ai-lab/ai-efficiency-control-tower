"""Tests fuer MockRetriever."""

from __future__ import annotations

import pytest

from aect.adapters.in_memory.retriever import MockRetriever


@pytest.fixture
def retriever() -> MockRetriever:
    return MockRetriever()


async def test_retrieve_returns_matching_chunk(retriever: MockRetriever) -> None:
    results = await retriever.retrieve("lizenzkosten")
    assert len(results) == 1
    assert results[0].source_id == "mock-stack-open-webui"
    assert results[0].score > 0.0


async def test_retrieve_is_deterministic(retriever: MockRetriever) -> None:
    first = await retriever.retrieve("open webui datenschutz")
    second = await retriever.retrieve("open webui datenschutz")
    assert first == second


async def test_retrieve_empty_query_returns_empty(retriever: MockRetriever) -> None:
    assert await retriever.retrieve("") == []


async def test_retrieve_no_match_returns_empty(retriever: MockRetriever) -> None:
    assert await retriever.retrieve("kubernetes") == []


async def test_retrieve_orders_by_score_descending(retriever: MockRetriever) -> None:
    results = await retriever.retrieve("open webui datenschutz")
    assert [chunk.source_id for chunk in results] == [
        "mock-stack-open-webui",
        "mock-compliance-dsfa",
    ]
    assert results[0].score >= results[1].score


async def test_retrieve_respects_top_k(retriever: MockRetriever) -> None:
    results = await retriever.retrieve("open webui datenschutz", top_k=1)
    assert len(results) == 1
    assert results[0].source_id == "mock-stack-open-webui"


async def test_retrieved_chunk_carries_provenance(retriever: MockRetriever) -> None:
    results = await retriever.retrieve("lizenzkosten")
    assert results[0].source_id != ""
    assert results[0].text != ""

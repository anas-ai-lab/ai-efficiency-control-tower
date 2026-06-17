"""Tests fuer MockEmbedder."""

from __future__ import annotations

import pytest

from aect.adapters.in_memory.embedder import MockEmbedder


@pytest.fixture
def embedder() -> MockEmbedder:
    return MockEmbedder()


async def test_embed_returns_one_vector_per_text(embedder: MockEmbedder) -> None:
    results = await embedder.embed(["open webui", "datenschutz"])
    assert len(results) == 2


async def test_embed_is_deterministic(embedder: MockEmbedder) -> None:
    first = await embedder.embed(["open webui"])
    second = await embedder.embed(["open webui"])
    assert first == second


async def test_embed_empty_input_returns_empty_list(embedder: MockEmbedder) -> None:
    assert await embedder.embed([]) == []


async def test_embed_different_texts_yield_different_vectors(
    embedder: MockEmbedder,
) -> None:
    results = await embedder.embed(["open webui", "kubernetes"])
    assert results[0] != results[1]


async def test_embed_preserves_input_order(embedder: MockEmbedder) -> None:
    results = await embedder.embed(["a", "b", "c"])
    single_a = await embedder.embed(["a"])
    single_b = await embedder.embed(["b"])
    single_c = await embedder.embed(["c"])
    assert results == [single_a[0], single_b[0], single_c[0]]


async def test_embed_vectors_have_consistent_dimension(
    embedder: MockEmbedder,
) -> None:
    results = await embedder.embed(["kurz", "ein deutlich laengerer beispieltext"])
    assert len(results[0]) == len(results[1])


async def test_embed_vector_values_in_unit_range(embedder: MockEmbedder) -> None:
    results = await embedder.embed(["open webui"])
    assert all(0.0 <= value <= 1.0 for value in results[0])

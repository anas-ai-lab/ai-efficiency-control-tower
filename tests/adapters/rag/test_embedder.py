"""Unit-Tests fuer SentenceTransformerEmbedder -- mit Fake-Encoder, kein Torch."""

from __future__ import annotations

import hashlib

import pytest

from aect.adapters.rag.embedder import SentenceTransformerEmbedder


class _FakeEncoder:
    """Deterministischer Stand-in fuer SentenceTransformer.encode.

    Liefert 3-dimensionale Vektoren aus dem SHA-256-Digest -- reproduzierbar,
    fuer verschiedene Texte verschieden, ohne Modell-Download oder Torch. Gibt
    list[list[float]] zurueck (das echte Modell gibt ein numpy-Array -- der
    Adapter konvertiert beides identisch ueber float()).
    """

    def encode(self, sentences: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for sentence in sentences:
            digest = hashlib.sha256(sentence.encode("utf-8")).digest()
            out.append([byte / 255.0 for byte in digest[:3]])
        return out


@pytest.fixture
def embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(_FakeEncoder())


async def test_embed_returns_one_vector_per_text(
    embedder: SentenceTransformerEmbedder,
) -> None:
    results = await embedder.embed(["open webui", "datenschutz"])
    assert len(results) == 2


async def test_embed_is_deterministic(
    embedder: SentenceTransformerEmbedder,
) -> None:
    first = await embedder.embed(["open webui"])
    second = await embedder.embed(["open webui"])
    assert first == second


async def test_embed_empty_input_returns_empty_list(
    embedder: SentenceTransformerEmbedder,
) -> None:
    assert await embedder.embed([]) == []


async def test_embed_different_texts_yield_different_vectors(
    embedder: SentenceTransformerEmbedder,
) -> None:
    results = await embedder.embed(["open webui", "kubernetes"])
    assert results[0] != results[1]


async def test_embed_preserves_input_order(
    embedder: SentenceTransformerEmbedder,
) -> None:
    results = await embedder.embed(["a", "b", "c"])
    single_a = await embedder.embed(["a"])
    single_b = await embedder.embed(["b"])
    single_c = await embedder.embed(["c"])
    assert results == [single_a[0], single_b[0], single_c[0]]


async def test_embed_returns_tuples_of_floats(
    embedder: SentenceTransformerEmbedder,
) -> None:
    results = await embedder.embed(["open webui"])
    assert isinstance(results[0], tuple)
    assert all(isinstance(value, float) for value in results[0])

"""Unit-Tests fuer chunk_document() und Chunk."""

from __future__ import annotations

import pytest

from aect.adapters.rag.chunker import Chunk, chunk_document
from aect.application.cost_logger import count_tokens

_PARAGRAPH_A = "Open WebUI ist eine selbst gehostete Chatoberflaeche fuer LLMs."
_PARAGRAPH_B = (
    "Reciprocal Rank Fusion kombiniert mehrere Ergebnislisten zu einer "
    "gemeinsamen Rangfolge."
)
_PARAGRAPH_C = (
    "Eine Datenschutz-Folgenabschaetzung prueft das Risiko einer Verarbeitung."
)


def test_chunk_document_short_text_returns_single_chunk() -> None:
    chunks = chunk_document(_PARAGRAPH_A, source_id="doc-1")
    assert len(chunks) == 1
    assert chunks[0].text == _PARAGRAPH_A


def test_chunk_document_assigns_source_id_and_sequential_index() -> None:
    text = f"{_PARAGRAPH_A}\n\n{_PARAGRAPH_B}"
    max_tokens = count_tokens(_PARAGRAPH_A) + 1
    chunks = chunk_document(text, source_id="doc-2", max_tokens=max_tokens)
    assert len(chunks) == 2
    assert [c.source_id for c in chunks] == ["doc-2", "doc-2"]
    assert [c.chunk_index for c in chunks] == [0, 1]


def test_chunk_document_splits_at_paragraph_boundary_when_exceeding_max_tokens() -> (
    None
):
    text = f"{_PARAGRAPH_A}\n\n{_PARAGRAPH_B}"
    max_tokens = count_tokens(_PARAGRAPH_A) + 1
    chunks = chunk_document(text, source_id="doc-3", max_tokens=max_tokens)
    assert chunks[0].text == _PARAGRAPH_A
    assert chunks[1].text == _PARAGRAPH_B


def test_chunk_document_no_chunk_exceeds_max_tokens() -> None:
    text = "\n\n".join([_PARAGRAPH_A, _PARAGRAPH_B, _PARAGRAPH_C] * 3)
    max_tokens = count_tokens(_PARAGRAPH_A) + count_tokens(_PARAGRAPH_B)
    chunks = chunk_document(text, source_id="doc-4", max_tokens=max_tokens)
    assert all(count_tokens(c.text) <= max_tokens for c in chunks)


def test_chunk_document_empty_text_returns_empty_list() -> None:
    assert chunk_document("", source_id="doc-5") == []


def test_chunk_document_whitespace_only_text_returns_empty_list() -> None:
    assert chunk_document("   \n\n   ", source_id="doc-6") == []


def test_chunk_document_oversized_single_paragraph_gets_hard_split() -> None:
    long_paragraph = " ".join(["wort"] * 500)
    chunks = chunk_document(long_paragraph, source_id="doc-7", max_tokens=50)
    assert len(chunks) > 1
    assert all(count_tokens(c.text) <= 50 for c in chunks)


def test_chunk_document_overlap_repeats_trailing_paragraph_in_next_chunk() -> None:
    text = f"{_PARAGRAPH_A}\n\n{_PARAGRAPH_B}\n\n{_PARAGRAPH_C}"
    max_tokens = count_tokens(_PARAGRAPH_A) + count_tokens(_PARAGRAPH_B) + 1
    overlap = count_tokens(_PARAGRAPH_B)
    chunks = chunk_document(
        text, source_id="doc-8", max_tokens=max_tokens, overlap_tokens=overlap
    )
    assert len(chunks) == 2
    assert _PARAGRAPH_B in chunks[0].text
    assert _PARAGRAPH_B in chunks[1].text
    assert _PARAGRAPH_C in chunks[1].text


def test_chunk_document_overlap_greater_or_equal_max_tokens_raises() -> None:
    with pytest.raises(ValueError):
        chunk_document(
            "ein kurzer text", source_id="doc-9", max_tokens=10, overlap_tokens=10
        )


def test_chunk_id_combines_source_id_and_index() -> None:
    chunk = Chunk(text="x", source_id="doc-10", chunk_index=2)
    assert chunk.chunk_id == "doc-10:2"

"""Unit-Tests fuer parse_kb_document() und build_index_records().

Hermetisch: Front-Matter-Fixtures + tmp_path, kein Chroma, kein Modell. Ein
Test liest zusaetzlich das echte knowledge_base/ als Content-Guard.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aect.adapters.rag.indexing import (
    build_index_records,
    parse_kb_document,
)

_FRONT_MATTER = (
    "---\n"
    "source_id: doc-a\n"
    "title: Test Doc A\n"
    "citation: Quelle A\n"
    "---\n"
    "\n"
    "Erster Absatz mit Inhalt.\n"
)


def test_parse_returns_metadata_and_body() -> None:
    metadata, body = parse_kb_document(_FRONT_MATTER)
    assert metadata["source_id"] == "doc-a"
    assert metadata["title"] == "Test Doc A"
    assert metadata["citation"] == "Quelle A"
    assert body == "Erster Absatz mit Inhalt."


def test_parse_missing_required_key_raises() -> None:
    text = "---\nsource_id: x\ntitle: y\n---\nbody"
    with pytest.raises(ValueError):
        parse_kb_document(text)


def test_parse_without_front_matter_raises() -> None:
    with pytest.raises(ValueError):
        parse_kb_document("kein front matter, nur text")


def test_parse_unclosed_front_matter_raises() -> None:
    text = "---\nsource_id: x\ntitle: y\ncitation: z\nbody ohne ende"
    with pytest.raises(ValueError):
        parse_kb_document(text)


def test_parse_value_with_colon_keeps_remainder() -> None:
    text = (
        "---\nsource_id: x\ntitle: y\ncitation: z\n"
        "url: https://example.org/a\n---\nbody"
    )
    metadata, _ = parse_kb_document(text)
    assert metadata["url"] == "https://example.org/a"


def test_build_single_file_single_chunk(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text(_FRONT_MATTER, encoding="utf-8")
    records = build_index_records(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert record.id == "doc-a:0"
    assert record.metadata["citation"] == "Quelle A"
    assert record.metadata["chunk_index"] == "0"
    assert "Erster Absatz" in record.document


def test_build_fans_out_multiple_chunks(tmp_path: Path) -> None:
    body = "\n\n".join(f"Absatz Nummer {i} mit etwas Text." for i in range(60))
    text = f"---\nsource_id: big\ntitle: T\ncitation: C\n---\n\n{body}\n"
    (tmp_path / "big.md").write_text(text, encoding="utf-8")
    records = build_index_records(tmp_path)
    assert len(records) > 1
    assert [r.id for r in records] == [f"big:{i}" for i in range(len(records))]
    assert all(r.metadata["source_id"] == "big" for r in records)


def test_build_ignores_non_markdown(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("kein md", encoding="utf-8")
    assert build_index_records(tmp_path) == []


def test_real_knowledge_base_files_parse() -> None:
    kb_dir = Path(__file__).resolve().parents[3] / "knowledge_base"
    records = build_index_records(kb_dir)
    assert records, "knowledge_base/ liefert keine Records"
    assert all(record.metadata["citation"] for record in records)
    assert all(":" in record.id for record in records)

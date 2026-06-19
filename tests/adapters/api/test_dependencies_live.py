"""Live-Test: get_retriever_port() im echten Chroma-Pfad (Phase D, ADR-0025).

Standardmaessig geskippt. Aktivieren mit AECT_RUN_CHROMA_LIVE=1 BEI laufendem
Container UND bereits geseedeter Collection (vorher:
`uv run python scripts/seed_knowledge_base.py`). Analog
tests/adapters/rag/test_retriever_live.py / test_index_kb_live.py: der
einmalige Realitaets-Check -- hier fuer die DI-Verdrahtung selbst, nicht den
Adapter isoliert. Automatisiert den manuellen Phase-D-Gate-Check
(session-protocol v3 SS2: "3 Test-Queries liefern sinnvolle Treffer mit
Citations").
"""

from __future__ import annotations

import os

import pytest

from aect.adapters.api.dependencies import get_retriever_port
from aect.adapters.api.settings import Settings

_RUN_LIVE = os.getenv("AECT_RUN_CHROMA_LIVE") == "1"

_QUERIES = (
    "Wann ist eine Datenschutz-Folgenabschaetzung noetig?",
    "Welche Transparenzpflicht gilt fuer KI-Systeme?",
    "Muss ein Nutzer informiert werden, dass er mit einer KI interagiert?",
)


@pytest.mark.skipif(
    not _RUN_LIVE,
    reason="AECT_RUN_CHROMA_LIVE=1 setzen, Container muss laufen und geseedet sein.",
)
async def test_get_retriever_port_real_path_returns_citations() -> None:
    settings = Settings(chroma_host="127.0.0.1", chroma_port=8001)
    retriever = get_retriever_port(settings=settings)

    for query in _QUERIES:
        results = await retriever.retrieve(query, top_k=3)
        assert results, f"Kein Treffer fuer Query: {query!r}"
        assert all(chunk.source_id for chunk in results)
        assert all(not chunk.source_id.startswith("mock-") for chunk in results)
        assert any(chunk.metadata.get("citation") for chunk in results)

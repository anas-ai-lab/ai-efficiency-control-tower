"""Live-Test: echte sentence-transformers-Inferenz. Standardmaessig geskippt.

Aktivieren mit AECT_RUN_EMBEDDER_LIVE=1. Erster Lauf laedt das Modell
(all-MiniLM-L6-v2, ~80 MB, einmalig, kostenlos). Analog test_azure_openai_live.py
ist das der einmalige Realitaets-Check -- nicht Teil des normalen Testlaufs,
damit pytest kein Torch importiert. Der sentence_transformers-Import steht
bewusst in der Testfunktion (nicht im Modulkopf): so laeuft er nur im scharfen
Lauf, und mypy auf src/ sieht ihn nie.

Toleranzvergleich statt exakter Gleichheit (Fund vom 17.06.2026, siehe
ADR-0016): torch verteilt CPU-Inferenz auf mehrere Threads; Floating-Point-
Summation ist nicht assoziativ, daher unterscheiden sich zwei Aufrufe
desselben Texts minimal (hier beobachtet: ~5e-8, an der float32-Praezisions-
grenze). Das ist eine Eigenschaft echter Modell-Inferenz, keine Eigenschaft
des EmbedderPort-Kontrakts (der nur Form + Reihenfolge verspricht, ADR-0015)
und kein Fehler im Adapter.
"""

from __future__ import annotations

import math
import os

import pytest

_RUN_LIVE = os.getenv("AECT_RUN_EMBEDDER_LIVE") == "1"


@pytest.mark.skipif(
    not _RUN_LIVE,
    reason="AECT_RUN_EMBEDDER_LIVE=1 setzen, um echte Embedding-Inferenz zu testen.",
)
async def test_local_embedder_real_inference() -> None:
    from sentence_transformers import SentenceTransformer

    from aect.adapters.rag.embedder import SentenceTransformerEmbedder

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedder = SentenceTransformerEmbedder(model)

    vectors = await embedder.embed(["open webui", "datenschutz"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert all(isinstance(value, float) for value in vectors[0])

    repeat = await embedder.embed(["open webui"])
    assert len(repeat[0]) == len(vectors[0])
    assert all(
        math.isclose(a, b, rel_tol=1e-4, abs_tol=1e-5)
        for a, b in zip(repeat[0], vectors[0], strict=True)
    )

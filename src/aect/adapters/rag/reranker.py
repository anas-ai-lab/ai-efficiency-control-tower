"""CrossEncoderReranker -- zweite Retrieval-Stufe per Cross-Encoder (Phase D, ADR-0028).

Bi-Encoder (SentenceTransformerEmbedder/ChromaRetriever) und BM25 bewerten
Query und Dokument unabhaengig voneinander -- ein Cross-Encoder bewertet
das Paar gemeinsam (volle Attention zwischen Query und Dokument) und ist
dadurch praeziser, aber zu teuer fuer den gesamten Korpus. Deshalb als
zweite Stufe NACH dem (guenstigen) Hybrid-Retrieval (HybridRetriever,
ADR-0027), nicht als Ersatz dafuer -- klassisches Retrieve-then-Rerank-
Pattern.

Design (analog HybridRetriever, ADR-0027): wrappt einen beliebigen
RetrieverPort (im echten Pfad: HybridRetriever) und implementiert selbst
RetrieverPort via strukturellem Subtyping -- TriageService merkt nichts
vom Reranking-Schritt.

Blockierende .predict()-Inferenz laeuft in asyncio.to_thread, analog
SentenceTransformerEmbedder.embed() (ADR-0015).
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from aect.application.ports.retriever import RetrievedChunk, RetrieverPort

_DEFAULT_CANDIDATE_POOL = 10


class CrossEncoderModel(Protocol):
    """Minimaler struktureller Typ, den der Reranker vom Modell braucht.

    Erfuellt von sentence_transformers.CrossEncoder (dessen .predict() eine
    Liste von (query, document)-Paaren entgegennimmt) und von einem
    Test-Fake. Bewusst schmal, analog EncoderModel (embedder.py).
    """

    def predict(self, sentences: list[tuple[str, str]]) -> Any: ...


class CrossEncoderReranker:
    """RetrieverPort-Implementierung: rerankt die Treffer eines inneren
    Retrievers per Cross-Encoder.

    candidate_pool (Default 10): der innere Retriever wird mit
    top_k=candidate_pool abgefragt, nicht mit dem finalen top_k -- analog
    HybridRetriever.candidate_pool (ADR-0027). Der Cross-Encoder soll auf
    einer breiteren Kandidatenmenge sortieren, statt nur die bereits vom
    Hybrid-Schritt vorsortierten Top-top_k zu reranken.

    RetrievedChunk.score wird durch den Cross-Encoder-Score ersetzt (nicht
    der urspruengliche RRF-/BM25-/Distanz-Score) -- score ist laut Kontrakt
    (ports/retriever.py) "nur fuer Reihenfolge/Anzeige, nicht fuer
    Berechnungen", die Ersetzung ist also vertragskonform und macht die
    finale Sortierung nachvollziehbar.

    Implementiert RetrieverPort via strukturellem Subtyping, analog
    HybridRetriever/BM25Retriever/ChromaRetriever -- kein Import von
    RetrieverPort fuer die Klasse selbst noetig (nur fuer den
    Konstruktor-Parametertyp `inner`).
    """

    def __init__(
        self,
        inner: RetrieverPort,
        model: CrossEncoderModel,
        candidate_pool: int = _DEFAULT_CANDIDATE_POOL,
    ) -> None:
        self._inner = inner
        self._model = model
        self._candidate_pool = candidate_pool

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        candidates = await self._inner.retrieve(query, top_k=self._candidate_pool)
        if not candidates:
            return []

        pairs = [(query, chunk.text) for chunk in candidates]
        scores = await asyncio.to_thread(self._model.predict, pairs)

        scored = sorted(
            zip(candidates, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        return [
            RetrievedChunk(
                text=chunk.text,
                source_id=chunk.source_id,
                score=float(score),
                metadata=chunk.metadata,
            )
            for chunk, score in scored[:top_k]
        ]

    async def delete_by_source_id(self, source_id: str) -> None:
        """Delegiert an den inneren Retriever (ADR-0038) -- Reranking betrifft
        nur die Lese-Reihenfolge, nicht den Loeschpfad."""
        await self._inner.delete_by_source_id(source_id)

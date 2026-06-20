"""HybridRetriever -- kombiniert zwei RetrieverPort-Implementierungen per
Reciprocal Rank Fusion (Phase D, ADR-0027).

Master-Plan v3.1 Phase D: "Hybrid Search (BM25 + Vektor, RRF)". Vektorsuche
(ChromaRetriever) findet semantisch Aehnliches, BM25Retriever findet exakte
Begriffstreffer -- beide haben blinde Flecken, die sich gegenseitig
abdecken. RRF kombiniert die beiden Ranglisten, ohne die Scores der
Verfahren direkt vergleichen zu muessen (unterschiedliche Skalen: Distanz-
Transform vs. Okapi-Score) -- nur die Rang-Position pro Liste zaehlt.

RRF-Formel (Cormack/Clarke/Buettcher 2009): score(d) = Summe ueber alle
Listen, in denen d vorkommt, von 1 / (k + rang(d)). k=60 ist der in der
Literatur uebliche Daempfungs-Wert, verhindert dass Rang 1 eine Liste
komplett dominiert.

candidate_pool (Default 10): beide Sub-Retriever werden mit top_k=
candidate_pool abgefragt, nicht mit dem finalen top_k -- sonst koennte ein
Dokument, das in einer Liste auf Position 6 steht, nie eine Chance haben,
nach der Fusion noch in die finalen top_k=5 zu kommen.

Merge-Schluessel ist RetrievedChunk.source_id. Bei BM25Retriever ist das
IndexRecord.id ("<source_id>:<chunk_index>"), bei ChromaRetriever exakt
derselbe Wert (indexer.py schreibt record.id als Chroma-ids beim Upsert) --
beide Quellen sind also auf demselben Schluessel vergleichbar.

Implementiert RetrieverPort via strukturellem Subtyping, analog den beiden
Sub-Retrievern.
"""

from __future__ import annotations

from aect.application.ports.retriever import RetrievedChunk, RetrieverPort

_DEFAULT_CANDIDATE_POOL = 10
_DEFAULT_RRF_K = 60


class HybridRetriever:
    """RetrieverPort-Implementierung durch RRF-Fusion zweier Sub-Retriever."""

    def __init__(
        self,
        vector_retriever: RetrieverPort,
        bm25_retriever: RetrieverPort,
        candidate_pool: int = _DEFAULT_CANDIDATE_POOL,
        rrf_k: int = _DEFAULT_RRF_K,
    ) -> None:
        self._vector = vector_retriever
        self._bm25 = bm25_retriever
        self._candidate_pool = candidate_pool
        self._rrf_k = rrf_k

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        vector_results = await self._vector.retrieve(query, top_k=self._candidate_pool)
        bm25_results = await self._bm25.retrieve(query, top_k=self._candidate_pool)

        rrf_scores: dict[str, float] = {}
        chunks_by_id: dict[str, RetrievedChunk] = {}
        first_seen_rank: dict[str, int] = {}

        for rank, chunk in enumerate(vector_results, start=1):
            rrf_scores[chunk.source_id] = rrf_scores.get(chunk.source_id, 0.0) + 1.0 / (
                self._rrf_k + rank
            )
            chunks_by_id.setdefault(chunk.source_id, chunk)
            first_seen_rank.setdefault(chunk.source_id, rank)

        for rank, chunk in enumerate(bm25_results, start=1):
            rrf_scores[chunk.source_id] = rrf_scores.get(chunk.source_id, 0.0) + 1.0 / (
                self._rrf_k + rank
            )
            chunks_by_id.setdefault(chunk.source_id, chunk)
            first_seen_rank.setdefault(chunk.source_id, len(vector_results) + rank)

        ordered_ids = sorted(
            rrf_scores,
            key=lambda source_id: (
                -rrf_scores[source_id],
                first_seen_rank[source_id],
            ),
        )

        return [
            RetrievedChunk(
                text=chunks_by_id[source_id].text,
                source_id=source_id,
                score=rrf_scores[source_id],
                metadata=chunks_by_id[source_id].metadata,
            )
            for source_id in ordered_ids[:top_k]
        ]

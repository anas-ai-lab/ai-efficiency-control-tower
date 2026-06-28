"""BM25Retriever -- lexikalischer RetrieverPort-Adapter (Phase D, ADR-0027).

Zweite RetrieverPort-Implementierung im echten Hybrid-Pfad, neben
ChromaRetriever (semantische Vektorsuche). BM25 (Okapi, k1=1.5, b=0.75)
findet exakte Begriffstreffer, die eine Embedding-Aehnlichkeit verfehlen
kann -- die klassische Ergaenzung zur Vektorsuche, kombiniert per
Reciprocal Rank Fusion in hybrid_retriever.py.

Hand-rolled statt externer Bibliothek (z. B. rank_bm25): BM25 ist ein
kompakter, gut dokumentierter Algorithmus ohne I/O -- analog zur
Entscheidung, den Chunker ohne Port-Abstraktion direkt zu implementieren
(ADR-0017). Keine neue Dependency, volles mypy --strict, Begruendung in
ADR-0027.

Tokenizer: einfache [a-z0-9]+-Regex auf kleingeschriebenem Text. Die
kuratierte Wissensbasis ist ASCII-only (ADR-0021) -- kein Umlaut-Handling
noetig.

Index wird einmalig aus IndexRecords gebaut (build_bm25_index), dieselbe
Quelle wie der Chroma-Upsert (indexer.py) -- record.id ("<source_id>:
<chunk_index>") ist identisch zu den Chroma-IDs, das ist der Schluessel,
ueber den hybrid_retriever.py beide Trefferlisten zusammenfuehrt.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from aect.adapters.rag.indexing import IndexRecord
from aect.application.ports.retriever import RetrievedChunk

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_K1 = 1.5
_B = 0.75


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class _ScoredDocument:
    record: IndexRecord
    term_frequencies: Counter[str]
    length: int


class BM25Index:
    """Vorberechneter BM25-Index ueber eine feste Menge von IndexRecords.

    Konstruktion ist O(Korpusgroesse), einmalig pro Prozess (analog
    _get_chroma_collection / _get_local_embedding_model, dependencies.py).
    score() ist die eigentliche Suchfunktion, aufgerufen pro Query.
    """

    def __init__(self, records: Sequence[IndexRecord]) -> None:
        self._docs: list[_ScoredDocument] = []
        document_frequency: Counter[str] = Counter()
        total_length = 0

        for record in records:
            tokens = _tokenize(record.document)
            term_frequencies = Counter(tokens)
            self._docs.append(
                _ScoredDocument(
                    record=record,
                    term_frequencies=term_frequencies,
                    length=len(tokens),
                )
            )
            total_length += len(tokens)
            for term in term_frequencies:
                document_frequency[term] += 1

        self._n = len(self._docs)
        self._avgdl = total_length / self._n if self._n else 0.0
        self._idf: dict[str, float] = {
            term: math.log((self._n - df + 0.5) / (df + 0.5) + 1.0)
            for term, df in document_frequency.items()
        }

    def score(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Okapi-BM25-Score pro Dokument, absteigend, hoechstens top_k.

        Leerer Index, leere Query oder Korpus ohne Tokens (avgdl=0) ->
        leere Liste (Graceful Degradation, analog RetrieverPort-Kontrakt).
        Nur Dokumente mit Score > 0 (mindestens ein Query-Term trifft).
        """
        if self._n == 0 or self._avgdl == 0.0:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, int, _ScoredDocument]] = []
        for index, doc in enumerate(self._docs):
            total = 0.0
            for term in query_tokens:
                idf = self._idf.get(term)
                if idf is None:
                    continue
                freq = doc.term_frequencies.get(term, 0)
                if freq == 0:
                    continue
                denom = freq + _K1 * (1 - _B + _B * doc.length / self._avgdl)
                total += idf * (freq * (_K1 + 1)) / denom
            if total > 0.0:
                scored.append((total, index, doc))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            RetrievedChunk(
                text=doc.record.document,
                source_id=doc.record.id,
                score=total,
                metadata=doc.record.metadata,
            )
            for total, _, doc in scored[:top_k]
        ]


def build_bm25_index(records: Sequence[IndexRecord]) -> BM25Index:
    """Baut einen BM25Index aus IndexRecords (z. B. build_index_records())."""
    return BM25Index(records)


class BM25Retriever:
    """Implementiert RetrieverPort ueber einen vorberechneten BM25Index.

    Implementiert RetrieverPort via strukturellem Subtyping, analog
    MockRetriever/ChromaRetriever -- kein Import von RetrieverPort noetig.
    """

    def __init__(self, index: BM25Index) -> None:
        self._index = index

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return self._index.score(query, top_k)

    async def delete_by_source_id(self, source_id: str) -> None:
        """No-op (ADR-0038): der BM25-Index ist ein prozessgebundener In-Memory-
        Index aus der kuratierten, nicht-personenbezogenen Wissensbasis -- kein
        persistenter PII-Store. Der DSGVO-Loeschpfad zielt auf den persistenten
        Vektor-Store (ChromaRetriever); BM25 wird beim naechsten Re-Seed neu
        gebaut."""
        return None

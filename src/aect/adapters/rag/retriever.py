"""ChromaRetriever -- RetrieverPort-Adapter gegen einen ChromaDB-Server (Phase D).

Zweite RetrieverPort-Implementierung neben MockRetriever
(adapters/in_memory/retriever.py): echte Vektor-Suche gegen die lokale
ChromaDB-Collection im Container (docker-compose, 127.0.0.1:8001, ADR-0018).

Design (analog SentenceTransformerEmbedder, ADR-0016):
- Constructor DI: Collection UND Embedder werden injiziert, nicht hier
  konstruiert. Der chromadb-Client (HttpClient -> get_or_create_collection)
  wird erst beim Verdrahten bzw. im Live-Test gebaut -- dieses Modul importiert
  chromadb nie. Normale Testlaeufe und mypy auf src/ ziehen kein chromadb.
- Query-Embedding kommt aus DEM SELBEN EmbedderPort wie die Index-seitigen
  Embeddings (ADR-0019): gleiches Modell fuer Index und Query, sonst ist die
  Vektor-Aehnlichkeit nicht vergleichbar. Chroma ist hier reiner Vektor-Store,
  nicht Embedding-Engine -- die collection-interne Embedding-Funktion bleibt
  ungenutzt.
- Blockierender .query()-Netz-Call laeuft in asyncio.to_thread, damit der
  Event-Loop frei bleibt (RetrieverPort ist async, ADR-0014).

PII-Redaction vor dem Embedding (LLM08, aect-security-checklist v2.1 Phase D)
ist NICHT Aufgabe dieses Adapters -- sie gehoert in die Indexing-Pipeline vor
dem embed()-Aufruf (Single Responsibility), Folge-Tag. Hier fliessen nur
synthetische, nicht-personenbezogene Texte.

Implementiert RetrieverPort via strukturellem Subtyping (kein Import von
RetrieverPort -- analog MockRetriever).
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any, Protocol

from aect.application.ports.embedder import EmbedderPort
from aect.application.ports.retriever import RetrievedChunk


class ChromaCollection(Protocol):
    """Minimaler struktureller Typ, den der Adapter von der Collection braucht.

    Erfuellt von chromadb.Collection (dessen .query() denselben kwarg-Satz
    akzeptiert) und von einem Test-Fake. Bewusst schmal -- so kennt der Adapter
    den konkreten Provider nicht (analog EncoderModel in embedder.py).
    """

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> Mapping[str, Any]: ...


def _first_row(value: Any) -> list[Any]:
    """Chroma verschachtelt pro Query eine eigene Ergebnisliste ([[...]]).

    Wir senden genau eine Query -> nimm die erste Zeile. Robust gegen None und
    Leer (leere Collection liefert [[]] oder None, je nach Server/include).
    """
    if not value:
        return []
    first = value[0]
    if first is None:
        return []
    return list(first)


class ChromaRetriever:
    """Implementiert RetrieverPort gegen eine ChromaDB-Collection."""

    def __init__(self, collection: ChromaCollection, embedder: EmbedderPort) -> None:
        self._collection = collection
        self._embedder = embedder

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        embedded = await self._embedder.embed([query])
        if not embedded:
            return []
        query_vector = list(embedded[0])
        raw = await asyncio.to_thread(self._run_query, query_vector, top_k)
        return self._parse(raw)

    def _run_query(self, query_vector: list[float], top_k: int) -> Mapping[str, Any]:
        return self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

    @staticmethod
    def _parse(raw: Mapping[str, Any]) -> list[RetrievedChunk]:
        ids = _first_row(raw.get("ids"))
        documents = _first_row(raw.get("documents"))
        distances = _first_row(raw.get("distances"))
        chunks: list[RetrievedChunk] = []
        for index, source_id in enumerate(ids):
            text = documents[index] if index < len(documents) else ""
            distance = distances[index] if index < len(distances) else 0.0
            # Chroma liefert Distanzen (kleiner = naeher). RetrievedChunk.score
            # ist "hoeher = relevanter" -> monoton fallende, positive, metrik-
            # unabhaengige Transformation. Nur fuer Anzeige/Reihenfolge
            # (ports/retriever.py), nie fuer Berechnungen.
            score = 1.0 / (1.0 + float(distance))
            chunks.append(
                RetrievedChunk(
                    text=str(text) if text is not None else "",
                    source_id=str(source_id),
                    score=score,
                )
            )
        return chunks

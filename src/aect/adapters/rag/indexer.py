"""KB-Live-Indexing -- bettet vorbereitete Records ein und schreibt sie in eine ChromaDB-Collection (Phase D).

Schreib-Pfad-Gegenstueck zu indexing.py (build_index_records, offline/rein,
ADR-0021): nimmt die upsert-fertigen IndexRecords, bettet ihre Texte ueber
einen EmbedderPort ein und schreibt sie in eine laufende ChromaDB-Collection
(docker-compose, 127.0.0.1:8001, ADR-0018).

Bewusste Modul-Trennung von indexing.py: ADR-0021 haelt build_index_records()
ausdruecklich offline und frei von Embedding-/Chroma-Imports. Der echte Upsert
gehoert deshalb in ein eigenes Modul, nicht in dieselbe Datei.

Design (analog ChromaRetriever, ADR-0019):
- Argument-DI: Collection UND Embedder werden injiziert, nicht hier
  konstruiert. Der chromadb-Client und das sentence-transformers-Modell werden
  erst im skipbaren Live-Test gebaut -- dieses Modul importiert weder chromadb
  noch torch. Normale Testlaeufe und mypy auf src/ ziehen keines von beiden.
- upsert statt add: idempotenter Re-Seed. Gleiche Chunk-id
  ("<source_id>:<index>", ADR-0017) ueberschreibt denselben Eintrag, statt an
  doppelten ids zu scheitern.
- metadatas werden bereits jetzt mitgeschrieben (citation/title/url/source_id/
  chunk_index aus IndexRecord.metadata), obwohl der Lese-Pfad sie noch nicht
  zurueckgibt (RetrievedChunk ohne metadata-Feld, Folge-Tag laut ADR-0021).
  So muss der Citation-Lese-Pfad spaeter nur den Retriever aendern, nicht neu
  indexieren.
- Blockierender .upsert()-Netz-Call laeuft in asyncio.to_thread, damit der
  Event-Loop frei bleibt.

PII-Redaction vor dem Embedding (LLM08, aect-security-checklist v2.1 Phase D)
ist hier kein Thema: indexiert wird ausschliesslich kuratierter oeffentlicher
Rechtstext aus knowledge_base/ (DSGVO, KI-VO), kein personenbezogener Inhalt
(ADR-0021). Der Redactor gehoert auf den User-Case-/Query-Pfad, Folge-Tag.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from aect.adapters.rag.indexing import build_index_records
from aect.application.ports.embedder import EmbedderPort


class IndexableCollection(Protocol):
    """Minimaler struktureller Typ fuer den Schreib-Zugriff auf die Collection.

    Erfuellt von chromadb.Collection (dessen .upsert() denselben kwarg-Satz
    akzeptiert) und von einem Test-Fake. Bewusst schmal -- so kennt das Modul
    den konkreten Provider nicht (analog ChromaCollection in retriever.py).
    """

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[Mapping[str, str]],
    ) -> None: ...


async def index_knowledge_base(
    kb_dir: Path,
    collection: IndexableCollection,
    embedder: EmbedderPort,
) -> int:
    """Baut Records aus kb_dir, bettet sie ein und schreibt sie in collection.

    Schritte: build_index_records(kb_dir) (offline, ADR-0021) -> Texte ueber
    embedder.embed() in Vektoren -> collection.upsert(ids, embeddings,
    documents, metadatas). Gibt die Anzahl geschriebener Records zurueck.

    Index und Query MUESSEN denselben Embedder benutzen (ADR-0019), damit die
    Vektoren vergleichbar sind -- das stellt der Aufrufer sicher (derselbe
    EmbedderPort hier und im ChromaRetriever).

    Leere Wissensbasis -> 0, kein Upsert (Graceful Degradation, analog
    chunk_document/RetrieverPort).
    """
    records = build_index_records(kb_dir)
    if not records:
        return 0

    documents = [record.document for record in records]
    vectors = await embedder.embed(documents)

    await asyncio.to_thread(
        collection.upsert,
        ids=[record.id for record in records],
        embeddings=[list(vector) for vector in vectors],
        documents=documents,
        metadatas=[record.metadata for record in records],
    )
    return len(records)

"""RetrieverPort -- testbarer Kontrakt fuer Wissensbasis-Retrieval (Phase D).

Analog LLMPort (ports/llm.py): die Anwendung kennt nur diesen Kontrakt, nie
die konkrete Such-Implementierung. MockRetriever (adapters/in_memory/
retriever.py) liefert deterministische Treffer fuer Tests; spaetere Adapter
(ChromaDB-Vektorsuche, BM25, Hybrid + Reranking -- adapters/rag/, Folge-Tage)
implementieren denselben Kontrakt mit echter Suche.

Importiert NICHT aus aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    """Ein einzelner Retrieval-Treffer aus der Wissensbasis.

    text: der gefundene Textausschnitt. Wird im spaeteren Prompt-Aufbau als
    *Daten* behandelt, nie als Instruktion (aect-security-checklist v2.1,
    Phase D: kuratierte Quellen, Retrieved-Content via Delimiter abgrenzen) --
    derselbe Untrusted-Umgang wie bei LLM-Output.

    source_id: stabiler Dokument-/Chunk-Identifier. Doppelzweck:
    (1) Citation-Anker fuer den belegten Hinweis im Output (Master-Plan v3.1
    Phase-D-Gate: Antworten mit [1]/[2]-Citations) und (2) Loesch-Tag fuer
    gezielte Entfernung einzelner Quellen (aect-security-checklist v2.1,
    Phase D: "Records taggen (source_id) fuer gezielte Loeschung").

    score: Relevanz des Treffers, hoeher = relevanter. Provider-abhaengig
    skaliert (Mock: Anzahl Query-Token-Treffer; spaeter: Vektor-Distanz bzw.
    RRF-Score). Nur fuer Reihenfolge/Anzeige, nicht fuer Berechnungen.

    metadata: Provenance-Felder aus der Indexierung (ADR-0021/0022), z. B.
    citation, title, url, source_id, chunk_index -- ausschliesslich
    str-Werte, analog IndexRecord.metadata (adapters/rag/indexing.py).
    Default leer: Adapter ohne Provenance (MockRetriever) bleiben gueltig,
    ohne diesen Konstruktor-Parameter angeben zu muessen. Wie text: beim
    spaeteren Prompt-Aufbau als Daten behandeln, nie als Instruktion -- auch
    wenn die Werte heute ausschliesslich aus kuratiertem, selbst
    geschriebenem Front-Matter stammen (ADR-0021), nicht aus Nutzereingabe.

    frozen=True: Wertobjekt, nach Erstellung unveraenderlich -- analog
    LLMResponse (ports/llm.py).
    """

    text: str
    source_id: str
    score: float
    metadata: Mapping[str, str] = field(default_factory=dict)


class RetrieverPort(Protocol):
    """Kontrakt fuer Wissensbasis-Retrieval.

    Warum ein Port? Die belegten Compliance-/Stack-Hinweise (Phase D) duerfen
    nicht von einer konkreten Such-Engine abhaengen. Mock-First (analog
    ADR-0003): zuerst ein deterministischer Mock, dann echte Adapter, ohne dass
    aufrufender Code sich aendert.

    top_k: Obergrenze der zurueckgegebenen Treffer. Default 5.
    Rueckgabe: nach Relevanz absteigend sortierte Treffer, hoechstens top_k.
    Leere Liste, wenn nichts passt -- kein Fehler (Graceful Degradation:
    fehlende Belege -> Hinweis entfaellt, System laeuft weiter).

    async: konsistent mit LLMPort und damit der Service-/FastAPI-Schicht;
    haelt den Event-Loop frei, sobald echte Embedding-Berechnung bzw.
    Azure-Embedding-Calls dahinterliegen (synchrone Bibliotheken werden im
    jeweiligen Adapter via asyncio.to_thread gekapselt -- Folge-Tag).
    """

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]: ...

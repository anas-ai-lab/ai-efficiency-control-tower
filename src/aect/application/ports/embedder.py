"""EmbedderPort -- testbarer Kontrakt fuer Embedding-Provider (Phase D).

Analog LLMPort (ports/llm.py) und RetrieverPort (ports/retriever.py): die
Anwendung kennt nur diesen Kontrakt, nie die konkrete Embedding-Implementierung.
MockEmbedder (adapters/in_memory/embedder.py) liefert deterministische Vektoren
fuer Tests; spaetere Adapter (lokal: sentence-transformers, Cloud: Azure
text-embedding-3-small, EU Data Zone) implementieren denselben Kontrakt mit
echter Inferenz.

Importiert NICHT aus aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class EmbedderPort(Protocol):
    """Kontrakt fuer Embedding-Provider.

    Warum ein Port? Hybrid-Suche (Phase D, Folge-Tage) braucht Vektoren fuer
    ChromaDB-Indexierung und Query-Embedding -- beides darf nicht von einem
    konkreten Provider (lokal vs. Azure) abhaengen. Mock-First (analog
    ADR-0003, ADR-0014): zuerst ein deterministischer Mock, dann echte
    Adapter, ohne dass aufrufender Code sich aendert.

    Batch-Signatur (nicht ein Text pro Call): sowohl sentence-transformers
    .encode() als auch ChromaDB-Upserts arbeiten satzweise effizienter als
    Einzelaufrufe -- der Kontrakt erzwingt das von Anfang an, statt es als
    Adapter-Detail nachzuruesten.

    Rueckgabe: ein Vektor (tuple[float, ...]) pro Eingabetext, gleiche
    Reihenfolge wie `texts`. Leere Eingabe -> leere Rueckgabe, kein Fehler.

    async: konsistent mit LLMPort und RetrieverPort; haelt den Event-Loop
    frei, sobald echte Inferenz (lokal blockierend, Azure netzwerkgebunden)
    dahinterliegt (Folge-Tag, asyncio.to_thread bzw. nativer async-Client).
    """

    async def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]: ...

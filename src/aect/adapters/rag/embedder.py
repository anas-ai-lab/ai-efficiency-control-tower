"""SentenceTransformerEmbedder -- lokaler EmbedderPort-Adapter (Phase D).

Zweite EmbedderPort-Implementierung neben MockEmbedder
(adapters/in_memory/embedder.py): echte semantische Vektoren ueber ein lokal
laufendes sentence-transformers-Modell (all-MiniLM-L6-v2, 384 Dimensionen).
Kostenlos, kein Netz, keine Azure-Kosten -- die Local-first-Variante des
Budget-Sentinel-Embeddings (session-protocol v3 SS4: "Fallback zuerst:
sentence-transformers lokal").

Design (analog AzureOpenAIAdapter, ADR-0010):
- Constructor DI: das geladene Modell wird injiziert, nicht im Adapter
  konstruiert. Das haelt diesen Modul-Quelltext frei von einem
  sentence-transformers-/torch-Import -- normale Testlaeufe und mypy auf src/
  ziehen kein Torch. Das echte Modell wird erst beim Verdrahten (Folge-Tag)
  bzw. im skipbaren Live-Test geladen.
- Blockierende .encode()-Inferenz laeuft in asyncio.to_thread, damit der
  Event-Loop frei bleibt (EmbedderPort ist async, ADR-0015).

Kein Versprechen ueber den Wertebereich: anders als MockEmbedder (auf
[0.0, 1.0] normiert) liefert ein echtes Modell beliebige Floats inkl.
negativer Werte. Der Kontrakt ist nur: ein Vektor pro Text, gleiche
Reihenfolge, leere Eingabe -> leere Rueckgabe.

PII-Redaction vor dem Embedding (LLM08, aect-security-checklist v2.1 Phase D)
ist KEINE Aufgabe dieses Adapters -- sie gehoert in die Indexing-Pipeline vor
dem embed()-Aufruf (Single Responsibility) und wird am Indexing-Tag eingezogen.
Heute fliessen keine echten Daten.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any, Protocol


class EncoderModel(Protocol):
    """Minimaler struktureller Typ, den der Adapter vom Modell braucht.

    Erfuellt von sentence_transformers.SentenceTransformer (dessen .encode()
    eine Liste von Saetzen entgegennimmt) und von einem Test-Fake. Bewusst
    schmal gehalten, damit der Adapter den konkreten Provider nicht kennt.
    """

    def encode(self, sentences: list[str]) -> Any: ...


class SentenceTransformerEmbedder:
    """EmbedderPort-Implementierung ueber ein injiziertes Encode-Modell.

    Implementiert EmbedderPort via strukturellem Subtyping (kein Import von
    EmbedderPort noetig -- analog MockEmbedder).
    """

    def __init__(self, model: EncoderModel) -> None:
        self._model = model

    async def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._encode, list(texts))

    def _encode(self, texts: list[str]) -> list[tuple[float, ...]]:
        raw = self._model.encode(texts)
        return [tuple(float(value) for value in row) for row in raw]

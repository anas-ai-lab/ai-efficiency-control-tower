"""MockEmbedder -- deterministischer Embedder fuer Tests und lokale Entwicklung."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

_VECTOR_DIMENSION = 8


class MockEmbedder:
    """Implementiert EmbedderPort ohne echte Inferenz.

    Leitet aus jedem Text einen deterministischen Pseudo-Vektor ab (SHA-256-
    Digest der ersten _VECTOR_DIMENSION Bytes, normiert auf [0.0, 1.0]). Kein
    semantisches Verstaendnis -- zwei inhaltlich aehnliche Texte liegen NICHT
    automatisch nahe beieinander, anders als ein echtes Embedding. Macht
    Embedding-Tests reproduzierbar ohne Modell-Download, Inferenzzeit oder
    Kosten. Analog dazu, dass MockRetriever nur Token-Matching liefert und
    MockLLMAdapter nur echo't -- echte Semantik liefert erst der
    sentence-transformers- bzw. Azure-Adapter (Folge-Tag).

    Implementiert EmbedderPort via strukturellem Subtyping.
    """

    async def embed(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        return [self._vector_for(text) for text in texts]

    @staticmethod
    def _vector_for(text: str) -> tuple[float, ...]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return tuple(byte / 255.0 for byte in digest[:_VECTOR_DIMENSION])

"""PII-Redaktion-Adapter (Phase G Privacy-Haertung, B1-Spike bestaetigt).

Mock-Variante liegt in adapters/in_memory/ (NoopRedactor) -- analog dazu,
wie der echte SentenceTransformerEmbedder in adapters/rag/ liegt, der
MockEmbedder aber in adapters/in_memory/.
"""

from aect.adapters.pii.presidio_redactor import PresidioRedactor

__all__ = ["PresidioRedactor"]

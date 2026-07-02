"""PIIRedactorPort -- testbarer Kontrakt fuer PII-Redaktion vor Embedding
(Phase G Privacy-Haertung).

Analog EmbedderPort/RetrieverPort: die Anwendung kennt nur diesen Kontrakt,
nie die konkrete PII-Erkennungs-Implementierung. NoopRedactor
(adapters/in_memory/noop_redactor.py) gibt Text unveraendert zurueck
(Tests); PresidioRedactor (adapters/pii/presidio_redactor.py) nutzt
Presidio + deutsches spaCy-NER fuer echte Erkennung+Anonymisierung
(B1-Spike bestaetigt: integrieren=ja).

Importiert NICHT aus aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

from typing import Protocol


class PIIRedactorPort(Protocol):
    """Kontrakt fuer PII-Redaktion.

    redact() ersetzt erkannte PII-Entitaeten (Namen, E-Mails, IBANs, ...) in
    `text` durch generische Platzhalter (z. B. "<PERSON>"). Synchron: die
    Presidio-Inferenz ist CPU-gebunden und lokal (kein Netzwerk-I/O wie bei
    LLMPort/RetrieverPort/EmbedderPort, die deshalb async sind).
    """

    def redact(self, text: str) -> str: ...

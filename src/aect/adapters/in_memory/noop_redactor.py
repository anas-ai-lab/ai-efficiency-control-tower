"""NoopRedactor -- implementiert PIIRedactorPort als Passthrough."""

from __future__ import annotations


class NoopRedactor:
    """Gibt Text unveraendert zurueck.

    Fuer Tests, die PII-Redaktion explizit als Passthrough exercisen wollen
    (Regressionsschutz: check_similarity() mit NoopRedactor verhaelt sich
    identisch zum Verhalten vor Einfuehrung der Redaktion) -- analog
    MockLLMAdapter/MockRetriever fuer ihre jeweiligen Ports.
    """

    def redact(self, text: str) -> str:
        return text

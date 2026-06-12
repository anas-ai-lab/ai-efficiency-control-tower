"""ResilientLLMAdapter -- Decorator-Adapter: Retry (Backoff) + Timeout fuer LLMPort.

aect-security-checklist v2.1, Phase C: "Circuit Breaker (tenacity): Retry +
Backoff + harter Timeout." Dieser Adapter implementiert genau das, als
Decorator um einen beliebigen LLMPort (Mock heute, Azure-OpenAI spaeter) --
TriageService haengt weiterhin nur von LLMPort ab und merkt nichts vom
Wrapping (DI-Entscheidung folgt in dependencies.py, Tag 35).

Graceful Degradation (Checkliste, Phase C): submit_use_case() (Regel-Triage)
ruft kein LLM auf -- ein dauerhaft ausfallender LLM-Adapter blockiert die
Kernbewertung nicht, unabhaengig von diesem Adapter
(siehe tests/application/test_service.py).

Offener Punkt (siehe ADR): Die Retry-Exception-Typen (TimeoutError,
ConnectionError) sind ein generischer Platzhalter. Ein spaeterer
Azure-OpenAI-Adapter wirft providerspezifische Exceptions (z. B.
APIConnectionError, RateLimitError) -- die Retry-Bedingung muss dann erweitert
werden, sobald dieser Adapter existiert (cat-Pflicht, session-protocol v3 SS1).

IP-Trennung (interne Referenz (entfernt) SS5): keine firmenspezifischen Werte -- generischer Code.
"""

from __future__ import annotations

import asyncio

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from aect.application.ports.llm import LLMMessage, LLMPort, LLMResponse


class ResilientLLMAdapter:
    """Wrapt einen LLMPort mit Retry (exponentieller Backoff) + Timeout.

    Implementiert LLMPort via strukturellem Subtyping (Protocol).

    Retry-Policy: bis zu `max_attempts` Versuche bei TimeoutError oder
    ConnectionError, exponentieller Backoff zwischen `min_wait_seconds` und
    `max_wait_seconds`. Andere Exceptions (z. B. ValueError) propagieren
    sofort ohne Retry. Nach Erschoepfen der Versuche wird die zuletzt
    aufgetretene Exception erneut geworfen (reraise=True) -- kein
    RetryError-Wrapper, der den urspruenglichen Fehlertyp verschluckt.
    """

    def __init__(
        self,
        inner: LLMPort,
        *,
        max_attempts: int = 3,
        timeout_seconds: float = 30.0,
        min_wait_seconds: float = 1.0,
        max_wait_seconds: float = 8.0,
    ) -> None:
        self._inner = inner
        self._max_attempts = max_attempts
        self._timeout_seconds = timeout_seconds
        self._min_wait_seconds = min_wait_seconds
        self._max_wait_seconds = max_wait_seconds

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(
                min=self._min_wait_seconds, max=self._max_wait_seconds
            ),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                return await asyncio.wait_for(
                    self._inner.complete(messages),
                    timeout=self._timeout_seconds,
                )
        raise AssertionError("unreachable: AsyncRetrying always returns or raises")

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

Tag 37 (Function-Calling): `complete()` reicht den optionalen `tools`-
Parameter unveraendert an den inneren Adapter durch -- reiner Passthrough,
keine Aenderung an Retry-/Timeout-Verhalten.

Offener Punkt (siehe ADR-0007): Die Retry-Exception-Typen (TimeoutError,
ConnectionError) sind ein generischer Platzhalter. Ein spaeterer
Azure-OpenAI-Adapter wirft providerspezifische Exceptions (z. B.
APIConnectionError, RateLimitError) -- die Retry-Bedingung muss dann erweitert
werden, sobald dieser Adapter existiert (cat-Pflicht, session-protocol v3 SS1).

IP-Trennung (vertraglich bedingt): keine firmenspezifischen Werte -- generischer Code.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from aect.application.ports.llm import (
    LLMMessage,
    LLMPort,
    LLMResponse,
    ToolDefinition,
)
from aect.application.structured_output import ArchitectureSketch, IdeationResult
from aect.domain.i18n import Lang


class ResilientLLMAdapter:
    """Wrapt einen LLMPort mit Retry (exponentieller Backoff) + Timeout.

    Implementiert LLMPort via strukturellem Subtyping (Protocol).

    Retry-Policy: bis zu `max_attempts` Versuche bei TimeoutError oder
    ConnectionError, exponentieller Backoff zwischen `min_wait_seconds` und
    `max_wait_seconds`. Andere Exceptions (z. B. ValueError) propagieren
    sofort ohne Retry. Nach Erschoepfen der Versuche wird die zuletzt
    aufgetretene Exception erneut geworfen (reraise=True) -- kein
    RetryError-Wrapper, der den urspruenglichen Fehlertyp verschluckt.

    Gesamtdeadline (F-014): `overall_timeout_seconds` deckelt den KOMPLETTEN
    complete()-Aufruf inklusive aller Retries und Backoff-Wartezeiten.
    Vorher war nur jeder Einzelversuch begrenzt -- Worst Case
    max_attempts x timeout_seconds + Backoff (~101 s bei Defaults). Laeuft
    die Deadline ab, wird TimeoutError geworfen (asyncio.timeout).
    """

    def __init__(
        self,
        inner: LLMPort,
        *,
        max_attempts: int = 3,
        timeout_seconds: float = 30.0,
        min_wait_seconds: float = 1.0,
        max_wait_seconds: float = 8.0,
        overall_timeout_seconds: float = 60.0,
    ) -> None:
        self._inner = inner
        self._max_attempts = max_attempts
        self._timeout_seconds = timeout_seconds
        self._min_wait_seconds = min_wait_seconds
        self._max_wait_seconds = max_wait_seconds
        self._overall_timeout_seconds = overall_timeout_seconds

    async def _run_resilient[T](self, operation: Callable[[], Awaitable[T]]) -> T:
        """Fuehrt `operation` mit Retry (Backoff) + Einzel- und Gesamt-Timeout aus.

        Gemeinsamer Kern von complete()/generate_ideation()/
        generate_architecture_sketch() (H-042 -- eine Retry-Policy, eine Quelle
        statt drei Copy-Paste-Bloecke). `operation` MUSS bei jedem Aufruf eine
        FRISCHE Coroutine liefern (Lambda um den inner-Call), damit jeder Versuch
        neu awaitbar ist.

        Retry nur bei TimeoutError/ConnectionError; andere Exceptions (z. B.
        InvalidLLMOutputError, ValueError) propagieren sofort ohne Retry.
        Gesamtdeadline (F-014): asyncio.timeout bricht auch mitten in einer
        Backoff-Wartezeit ab und uebersetzt die Cancellation in TimeoutError.
        """
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(
                min=self._min_wait_seconds, max=self._max_wait_seconds
            ),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
            reraise=True,
        )
        async with asyncio.timeout(self._overall_timeout_seconds):
            async for attempt in retrying:
                with attempt:
                    return await asyncio.wait_for(
                        operation(), timeout=self._timeout_seconds
                    )
        raise AssertionError("unreachable: AsyncRetrying always returns or raises")

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        return await self._run_resilient(
            lambda: self._inner.complete(messages, tools=tools)
        )

    async def generate_ideation(
        self, problem_description: str, lang: Lang = "de"
    ) -> IdeationResult:
        """Wrappt inner.generate_ideation mit Retry + Backoff + Timeout (P10).

        Identisches Muster wie complete() (gemeinsamer _run_resilient-Kern): Retry
        nur bei TimeoutError/ConnectionError. Eine InvalidLLMOutputError (kaputte
        LLM-Antwort) ist KEIN transienter Verbindungsfehler und propagiert sofort
        ohne Retry -- die Route mappt sie auf einen sauberen HTTP-Fehler.
        """
        return await self._run_resilient(
            lambda: self._inner.generate_ideation(problem_description, lang)
        )

    async def generate_architecture_sketch(
        self,
        case_id: str,
        title: str,
        description: str,
        proposal_text: str,
    ) -> ArchitectureSketch:
        """Wrappt inner.generate_architecture_sketch mit Retry + Backoff + Timeout.

        Identisches Muster wie complete()/generate_ideation() (gemeinsamer
        _run_resilient-Kern): Retry nur bei TimeoutError/ConnectionError. Eine
        InvalidLLMOutputError (kaputte LLM-Antwort) ist KEIN transienter
        Verbindungsfehler und propagiert sofort ohne Retry -- die Route mappt sie
        auf einen sauberen HTTP-Fehler (502).
        """
        return await self._run_resilient(
            lambda: self._inner.generate_architecture_sketch(
                case_id, title, description, proposal_text
            )
        )

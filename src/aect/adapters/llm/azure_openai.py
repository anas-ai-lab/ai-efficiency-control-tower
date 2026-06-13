"""AzureOpenAIAdapter -- LLMPort-Implementierung fuer Azure OpenAI (EU-Data-Zone).

aect-security-checklist v2.1, Phase C:
- EU-Data-Zone (swedencentral/westeurope): Deployment-Zeit-Pflicht, kein
  Code-Gate (Region nicht aus Endpoint-URL ableitbar -- ADR-0010).
- Messages-API: System/User/Tool getrennt, kein String-Concat (ADR-0005).
- LLM-Output als untrusted: tool_calls[i].function.arguments ist JSON-String
  im Azure-Response -> json.loads() vor Uebergabe an ToolCall (LLM05).
- Max-Tokens-Cap: verhindert Unbounded Consumption (LLM10).
- Exception-Translation: openai-Exceptions -> ConnectionError/TimeoutError
  fuer ResilientLLMAdapter-Retry-Policy (ADR-0007, ADR-0010).

IP-Trennung (interne Referenz (entfernt) SS5): Endpoint, API-Key und Deployment-Name kommen
ausschliesslich aus Settings (Env-Variablen), nicht hartkodiert.
"""

from __future__ import annotations

import json
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncAzureOpenAI, RateLimitError

from aect.application.ports.llm import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)

_MAX_TOKENS_DEFAULT = 1000


class AzureOpenAIAdapter:
    """LLMPort-Implementierung via AsyncAzureOpenAI (Azure OpenAI Service).

    Client wird von aussen injiziert (Constructor DI -- get_llm_adapter()
    in dependencies.py baut AsyncAzureOpenAI und uebergibt ihn). Konsistent
    mit Hexagonal-Pattern (ADR-0002); macht Tests ohne patch() moeglich.

    deployment: Azure-Deployment-Name. Bei Azure ist `model` in
    chat.completions.create() der Deployment-Name, nicht der Modellname.

    max_tokens: harter Cap gegen LLM10 Unbounded Consumption. Default 1000
    ausreichend fuer Schaerfung + Loesungsvorschlag; bei Report-Renderer
    (laengere Outputs) als Config-Wert anpassbar.
    """

    def __init__(
        self,
        client: AsyncAzureOpenAI,
        deployment: str,
        max_tokens: int = _MAX_TOKENS_DEFAULT,
    ) -> None:
        self._client = client
        self._deployment = deployment
        self._max_tokens = max_tokens

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        """Fuehrt einen Chat-Completions-Call gegen Azure OpenAI durch.

        Exception-Translation (ADR-0007 offener Punkt, ADR-0010):
        - APITimeoutError    -> TimeoutError    (Retry in ResilientLLMAdapter)
        - APIConnectionError -> ConnectionError  (Retry in ResilientLLMAdapter)
        - RateLimitError     -> ConnectionError  (vereinfacht: Rate-Limit
          wie transiente Verbindungsstoerung; kein Retry-After-Header-Backoff.
          Bekannte Vereinfachung, in ADR-0010 dokumentiert.)
        Alle anderen Exceptions propagieren unveraendert.
        """
        az_messages = [_to_azure_message(m) for m in messages]
        az_tools = [_to_azure_tool(t) for t in tools] if tools else None

        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": az_messages,
            "max_tokens": self._max_tokens,
        }
        if az_tools:
            kwargs["tools"] = az_tools

        try:
            response = await self._client.chat.completions.create(**kwargs)
        except APITimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except (APIConnectionError, RateLimitError) as exc:
            raise ConnectionError(str(exc)) from exc

        message = response.choices[0].message
        content: str = message.content or ""

        tool_calls: list[ToolCall] | None = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    # arguments ist JSON-String im Azure-Response (LLM05):
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in message.tool_calls
            ]

        return LLMResponse(content=content, tool_calls=tool_calls)


def _to_azure_message(msg: LLMMessage) -> dict[str, Any]:
    """Konvertiert LLMMessage in Azure-Chat-Completions-Format.

    Drei Sonderfaelle gegenueber einfachem role/content:
    1. role="tool": braucht tool_call_id (Pflichtfeld im Azure-Format).
    2. role="assistant" mit tool_calls: Aufrufe als Liste mit
       type="function" + arguments als JSON-String (Umkehrung von
       json.loads() beim Deserialisieren der Response).
    3. Alle anderen: {"role": ..., "content": ...}.
    """
    if msg.role == "tool":
        return {
            "role": "tool",
            "tool_call_id": msg.tool_call_id,
            "content": msg.content,
        }
    if msg.role == "assistant" and msg.tool_calls:
        return {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in msg.tool_calls
            ],
        }
    return {"role": msg.role, "content": msg.content}


def _to_azure_tool(tool: ToolDefinition) -> dict[str, Any]:
    """Konvertiert ToolDefinition in Azure Function-Calling-Tool-Format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }

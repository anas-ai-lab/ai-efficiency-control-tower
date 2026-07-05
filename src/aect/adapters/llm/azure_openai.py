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

IP-Trennung (vertraglich bedingt): Endpoint, API-Key und Deployment-Name kommen
ausschliesslich aus Settings (Env-Variablen), nicht hartkodiert.
"""

from __future__ import annotations

import json
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncAzureOpenAI, RateLimitError

from aect.application.cost_logger import log_llm_cost
from aect.application.ports.llm import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)
from aect.application.prompts import load_prompt
from aect.application.structured_output import (
    ArchitectureSketch,
    IdeationResult,
    parse_structured_llm_output,
)

_MAX_TOKENS_DEFAULT = 1000

# Sentinel-case_id fuer den ephemeren Ideation-Pfad (P10): generate_ideation
# persistiert nichts (kein Case), log_llm_cost erwartet aber eine case_id.
# Kein PII -- der request_id kommt ohnehin ueber structlog-contextvars dazu.
_IDEATION_LOG_ID = "ideation-ephemeral"


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

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        """Erzeugt 1-3 Use-Case-Entwuerfe aus einer Problembeschreibung (P10).

        Baut die Messages aus dem versionierten ideation-Prompt (System/User
        getrennt, kein String-Concat -- LLM01), ruft complete() (inkl.
        Exception-Translation + max_tokens-Cap, wie jeder andere Azure-Call),
        loggt die Kosten und validiert die rohe Antwort gegen IdeationResult
        (Output als untrusted, ADR-0013). Kein Function-Calling.

        Raises:
            InvalidLLMOutputError: rohe Antwort verletzt IdeationResult.
            ConnectionError/TimeoutError: aus complete() durchgereicht.
        """
        system_prompt = load_prompt("ideation", "system")
        user_template = load_prompt("ideation", "user")
        user_content = user_template.format(problem_description=problem_description)

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self.complete(messages)

        log_llm_cost(
            case_id=_IDEATION_LOG_ID,
            messages=messages,
            response=response,
            operation="generate_ideation",
        )

        return parse_structured_llm_output(response.content, IdeationResult)

    async def generate_architecture_sketch(
        self,
        case_id: str,
        title: str,
        description: str,
        proposal_text: str,
    ) -> ArchitectureSketch:
        """Erzeugt eine Architektur-Skizze als Graph-JSON (P11, ADR-0049).

        Baut die Messages aus dem versionierten architecture_sketch-Prompt
        (System/User getrennt, kein String-Concat -- LLM01), ruft complete()
        (inkl. Exception-Translation + max_tokens-Cap), loggt die Kosten unter
        der echten case_id und validiert die rohe Antwort gegen
        ArchitectureSketch (Output als untrusted, ADR-0013). Kein
        Function-Calling. Kein Mermaid -- nur das Graph-JSON (D18).

        Raises:
            InvalidLLMOutputError: rohe Antwort verletzt ArchitectureSketch.
            ConnectionError/TimeoutError: aus complete() durchgereicht.
        """
        system_prompt = load_prompt("architecture_sketch", "system")
        user_template = load_prompt("architecture_sketch", "user")
        user_content = user_template.format(
            title=title,
            description=description,
            proposal_text=proposal_text,
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self.complete(messages)

        log_llm_cost(
            case_id=case_id,
            messages=messages,
            response=response,
            operation="generate_architecture_sketch",
        )

        return parse_structured_llm_output(response.content, ArchitectureSketch)


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

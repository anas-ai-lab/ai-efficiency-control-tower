"""Tests fuer AzureOpenAIAdapter.

Kein echter Azure-Call -- AsyncAzureOpenAI-Client wird als MagicMock
per Constructor-DI uebergeben (kein patch() noetig, ADR-0010).
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APIConnectionError, APITimeoutError, RateLimitError

from aect.adapters.llm.azure_openai import AzureOpenAIAdapter
from aect.application.ports.llm import LLMMessage, ToolCall, ToolDefinition

_DEPLOYMENT = "gpt-4o-mini"
_MESSAGES = [LLMMessage(role="user", content="Hallo")]


def _make_client(
    content: str | None = "ok",
    az_tool_calls: list | None = None,
) -> MagicMock:
    """Minimaler Mock-AsyncAzureOpenAI-Client fuer Tests."""
    message = MagicMock()
    message.content = content
    message.tool_calls = az_tool_calls

    choice = MagicMock()
    choice.message = message

    completion = MagicMock()
    completion.choices = [choice]

    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=completion)
    return client


# ---------------------------------------------------------------------------
# Response-Deserialisierung
# ---------------------------------------------------------------------------


async def test_complete_returns_text_response() -> None:
    client = _make_client(content="Antwort vom Modell", az_tool_calls=None)
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    response = await adapter.complete(_MESSAGES)

    assert response.content == "Antwort vom Modell"
    assert response.tool_calls is None


async def test_complete_content_none_becomes_empty_string() -> None:
    """Azure liefert content=None wenn tool_calls vorhanden -- muss '' werden."""
    az_tc = MagicMock()
    az_tc.id = "call-1"
    az_tc.function.name = "lookup_stack_options"
    az_tc.function.arguments = "{}"
    client = _make_client(content=None, az_tool_calls=[az_tc])
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    response = await adapter.complete(_MESSAGES)

    assert response.content == ""


async def test_complete_deserializes_tool_calls_from_response() -> None:
    """tool_calls[i].function.arguments ist JSON-String -> json.loads() noetig."""
    az_tc = MagicMock()
    az_tc.id = "call-1"
    az_tc.function.name = "lookup_stack_options"
    az_tc.function.arguments = json.dumps({"key": "val"})
    client = _make_client(content="", az_tool_calls=[az_tc])
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    response = await adapter.complete(_MESSAGES)

    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    tc = response.tool_calls[0]
    assert tc.id == "call-1"
    assert tc.name == "lookup_stack_options"
    assert tc.arguments == {"key": "val"}


# ---------------------------------------------------------------------------
# Request-Serialisierung
# ---------------------------------------------------------------------------


async def test_complete_passes_deployment_as_model() -> None:
    """Bei Azure ist `model` der Deployment-Name, nicht der Modellname."""
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    await adapter.complete(_MESSAGES)

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == _DEPLOYMENT


async def test_complete_passes_max_tokens() -> None:
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT, max_tokens=500)

    await adapter.complete(_MESSAGES)

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["max_tokens"] == 500


async def test_complete_serializes_system_and_user_messages() -> None:
    messages = [
        LLMMessage(role="system", content="Du bist ein Assistent."),
        LLMMessage(role="user", content="Hallo"),
    ]
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    await adapter.complete(messages)

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["messages"] == [
        {"role": "system", "content": "Du bist ein Assistent."},
        {"role": "user", "content": "Hallo"},
    ]


async def test_complete_serializes_tool_result_message() -> None:
    messages = [
        LLMMessage(
            role="tool",
            content='{"result": "ok"}',
            tool_call_id="call-1",
        )
    ]
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    await adapter.complete(messages)

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["messages"] == [
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": '{"result": "ok"}',
        }
    ]


async def test_complete_serializes_assistant_message_with_tool_calls() -> None:
    """tool_calls[i].arguments muss als JSON-String rausgehen (Azure-Format)."""
    tool_call = ToolCall(
        id="call-1", name="lookup_stack_options", arguments={"key": "val"}
    )
    messages = [LLMMessage(role="assistant", content="", tool_calls=[tool_call])]
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    await adapter.complete(messages)

    kwargs = client.chat.completions.create.call_args.kwargs
    az_msg = kwargs["messages"][0]
    assert az_msg["role"] == "assistant"
    az_tc = az_msg["tool_calls"][0]
    assert az_tc["type"] == "function"
    assert az_tc["function"]["name"] == "lookup_stack_options"
    assert json.loads(az_tc["function"]["arguments"]) == {"key": "val"}


async def test_complete_sends_tools_in_correct_format() -> None:
    tool = ToolDefinition(
        name="lookup_stack_options",
        description="Gibt Plattformen zurueck.",
        parameters={"type": "object", "properties": {}},
    )
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    await adapter.complete(_MESSAGES, tools=[tool])

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "lookup_stack_options",
                "description": "Gibt Plattformen zurueck.",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]


async def test_complete_no_tools_omits_tools_key() -> None:
    """tools=None -> kein `tools`-Key im Request (nicht None als Wert)."""
    client = _make_client()
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    await adapter.complete(_MESSAGES, tools=None)

    kwargs = client.chat.completions.create.call_args.kwargs
    assert "tools" not in kwargs


# ---------------------------------------------------------------------------
# Exception-Translation
# ---------------------------------------------------------------------------


async def test_api_connection_error_becomes_connection_error() -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        side_effect=APIConnectionError(request=MagicMock())
    )
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    with pytest.raises(ConnectionError):
        await adapter.complete(_MESSAGES)


async def test_api_timeout_error_becomes_timeout_error() -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        side_effect=APITimeoutError(request=MagicMock())
    )
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    with pytest.raises(TimeoutError):
        await adapter.complete(_MESSAGES)


async def test_rate_limit_error_becomes_connection_error() -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        side_effect=RateLimitError(
            message="rate limited",
            response=MagicMock(),
            body={},
        )
    )
    adapter = AzureOpenAIAdapter(client=client, deployment=_DEPLOYMENT)

    with pytest.raises(ConnectionError):
        await adapter.complete(_MESSAGES)

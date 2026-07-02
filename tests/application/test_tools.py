"""Tests fuer application/tools.py -- Tool-Registry und Dispatch (Tag 37)."""

from __future__ import annotations

import pytest

from aect.application.ports.llm import ToolCall
from aect.application.tools import (
    TOOL_DEFINITIONS,
    UnknownToolError,
    dispatch_tool_call,
    lookup_stack_options,
)


def test_tool_definitions_contains_lookup_stack_options() -> None:
    names = [tool.name for tool in TOOL_DEFINITIONS]
    assert "lookup_stack_options" in names


def test_lookup_stack_options_returns_known_platform_categories() -> None:
    # Kategorien-Platzhalter (AUDIT-011) -- keine konkreten Vendor-Namen
    # in der committeten Config.
    options = lookup_stack_options()
    assert "self_hosted_chat_ui" in options
    assert "low_code_agent_platform" in options
    assert "cloud_ai_platform" in options
    assert "erp_extension_platform" in options
    assert "andere" in options


def test_lookup_stack_options_entries_have_name_and_description() -> None:
    options = lookup_stack_options()
    for entry in options.values():
        assert "name" in entry
        assert "description" in entry


def test_dispatch_tool_call_lookup_stack_options_returns_platform_data() -> None:
    call = ToolCall(id="call-1", name="lookup_stack_options", arguments={})

    result = dispatch_tool_call(call)

    assert "andere" in result


def test_dispatch_tool_call_unknown_tool_raises() -> None:
    call = ToolCall(id="call-1", name="does_not_exist", arguments={})

    with pytest.raises(UnknownToolError):
        dispatch_tool_call(call)

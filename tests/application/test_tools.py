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


def test_lookup_stack_options_returns_known_platforms() -> None:
    options = lookup_stack_options()
    assert "open_webui" in options
    assert "copilot_studio" in options
    assert "foundry" in options
    assert "sap_btp" in options
    assert "andere" in options


def test_lookup_stack_options_entries_have_name_and_description() -> None:
    options = lookup_stack_options()
    for entry in options.values():
        assert "name" in entry
        assert "description" in entry


def test_dispatch_tool_call_lookup_stack_options_returns_platform_data() -> None:
    call = ToolCall(id="call-1", name="lookup_stack_options", arguments={})

    result = dispatch_tool_call(call)

    assert "open_webui" in result


def test_dispatch_tool_call_unknown_tool_raises() -> None:
    call = ToolCall(id="call-1", name="does_not_exist", arguments={})

    with pytest.raises(UnknownToolError):
        dispatch_tool_call(call)

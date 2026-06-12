"""Tests fuer den Prompt-Loader."""

from __future__ import annotations

import pytest

from aect.application.prompts import load_prompt


def test_load_prompt_system_returns_nonempty_text() -> None:
    text = load_prompt("sharpen_use_case", "system")
    assert len(text) > 0


def test_load_prompt_user_contains_placeholders() -> None:
    text = load_prompt("sharpen_use_case", "user")
    assert "{title}" in text
    assert "{current_state}" in text
    assert "{desired_state}" in text
    assert "{example_process}" in text


def test_load_prompt_unknown_name_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("does_not_exist", "system")


def test_load_prompt_unknown_version_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("sharpen_use_case", "system", version="v99")

# tests/test_smoke.py
"""Smoke tests — verifies the package is importable and structurally sound."""

import pytest

import aect


@pytest.mark.unit
def test_package_importable() -> None:
    """Package must import without errors."""
    assert aect is not None


@pytest.mark.unit
def test_version_is_string() -> None:
    """__version__ must exist and be a non-empty string."""
    assert isinstance(aect.__version__, str)
    assert len(aect.__version__) > 0


@pytest.mark.unit
def test_version_format() -> None:
    """__version__ must follow semver pattern (MAJOR.MINOR.PATCH)."""
    parts = aect.__version__.split(".")
    assert len(parts) == 3, f"Expected semver, got: {aect.__version__}"
    assert all(part.isdigit() for part in parts), f"Non-numeric version part in: {aect.__version__}"

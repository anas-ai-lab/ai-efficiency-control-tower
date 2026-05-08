# tests/conftest.py
"""Shared pytest fixtures and configuration."""

import pytest


# ---------------------------------------------------------------------------
# Custom markers
# ---------------------------------------------------------------------------
def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may be slow)"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")

"""AI Efficiency Control Tower — AI Use Case Intake & Triage Assistant."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

# Single Source of Truth: die Paketversion aus pyproject.toml (H-044) -- keine
# zweite, driftende Konstante. Fallback nur fuer einen reinen Source-Checkout
# ohne installierte Metadaten.
try:
    __version__: str = _pkg_version("aect")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__author__: str = "anas-ai-lab"

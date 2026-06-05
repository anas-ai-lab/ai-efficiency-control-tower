# Makefile — AECT Development Commands
# Alle Befehle laufen über `uv run` — kein globales Pip nötig

.PHONY: help lint format typecheck test check clean

help:  ## Verfügbare Befehle anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

lint:  ## Ruff linter ausführen
	uv run ruff check src/ tests/

format:  ## Ruff formatter ausführen
	uv run ruff format src/ tests/

typecheck:  ## mypy type checker ausführen (strict)
	uv run mypy src/

test:  ## pytest mit Coverage ausführen
	uv run pytest --cov=src/aect --cov-report=term-missing -q

check:  ## Vollständiger Pre-Commit-Check (vor jedem Commit)
	uv run pre-commit run --all-files
	uv run pytest -q
	uv run mypy src/

clean:  ## Cache-Verzeichnisse entfernen
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

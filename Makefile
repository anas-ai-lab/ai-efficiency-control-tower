.PHONY: install lint format typecheck check clean

install:
	uv sync

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

check: lint typecheck
	@echo "All checks passed."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache
.PHONY: lock sync install test clean help

help:
	@echo "Available commands:"
	@echo "  make lock          - Update uv.lock from pyproject.toml"
	@echo "  make sync          - Sync dependencies from uv.lock"
	@echo "  make install       - Install dependencies (alias for sync)"
	@echo "  make test          - Run tests and linting"
	@echo "  make clean         - Remove generated files"

lock:
	@echo "Updating uv.lock from pyproject.toml..."
	@uv lock
	@echo "✅ uv.lock updated successfully!"

sync:
	@echo "Syncing dependencies from uv.lock..."
	@uv sync
	@echo "✅ Dependencies synced!"

install: sync

test:
	@echo "Running linting checks..."
	@uv pip install flake8 --quiet
	@uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@uv run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "✅ Linting complete!"

clean:
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .venv 2>/dev/null || true
	@echo "✅ Cleanup complete!"

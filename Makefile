.PHONY: requirements install test clean help

help:
	@echo "Available commands:"
	@echo "  make requirements  - Generate requirements.txt from pyproject.toml"
	@echo "  make install       - Install dependencies from requirements.txt"
	@echo "  make test          - Run tests and linting"
	@echo "  make clean         - Remove generated files"

requirements:
	@echo "Generating requirements.txt from pyproject.toml..."
	@python3 -m pip install pip-tools --quiet
	@python3 -m piptools compile pyproject.toml --output-file=requirements.txt --resolver=backtracking
	@echo "✅ requirements.txt generated successfully!"

install:
	@echo "Installing dependencies..."
	@python3 -m pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

test:
	@echo "Running linting checks..."
	@python3 -m pip install flake8 --quiet
	@python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "✅ Linting complete!"

clean:
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

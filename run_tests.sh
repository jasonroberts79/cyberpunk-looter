#!/bin/bash
# Script to set up and run unit tests using uv

set -e  # Exit on error

echo "Setting up test environment with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies with test extras
echo "Syncing test dependencies..."
uv sync --extra test

# Run tests
echo ""
echo "Running tests..."
echo "===================="

# Run pytest with coverage using uv
uv run pytest "$@"

echo ""
echo "Tests completed!"
echo "View coverage report: open htmlcov/index.html"

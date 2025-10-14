#!/bin/bash
# Generate requirements.txt from pyproject.toml
# This ensures dependencies stay in sync

set -e

echo "Generating requirements.txt from pyproject.toml..."

# Check if pip-tools is installed
if ! command -v pip-compile &> /dev/null; then
    echo "Installing pip-tools..."
    pip install pip-tools
fi

# Generate requirements.txt with locked versions
pip-compile pyproject.toml --output-file=requirements.txt --resolver=backtracking

echo "✅ requirements.txt generated successfully!"

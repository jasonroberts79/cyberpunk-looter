#!/bin/bash
# Wrapper script to run the LLM CLI test harness

cd "$(dirname "$0")"
uv run python src/llm_cli.py

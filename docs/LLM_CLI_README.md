# LLM CLI Test Harness

A command-line interface for testing the LLM service without needing Discord.

## Quick Start

```bash
./llm_cli.sh
```

Or directly:

```bash
uv run python src/llm_cli.py
```

## Features

- **Interactive REPL**: Chat with the LLM service just like you would in Discord
- **Natural Language**: Ask questions, add party members, get gear recommendations
- **Tool Call Confirmations**: Approve or reject actions before they execute
- **Party Management**: Add, remove, and view party members
- **Conversation Memory**: Maintains context across the conversation
- **GraphRAG Integration**: Uses the knowledge base to answer questions

## Example Usage

### Ask Questions

```
You: What are assault rifles in Cyberpunk RED?
# Agentic GraphRAG Discord Chatbot

An intelligent Discord bot powered by Graph-based Retrieval-Augmented Generation (GraphRAG) using Neo4j, with short and long-term memory capabilities.

## Features

- 🤖 **GraphRAG System**: Answers questions using Neo4j graph database with vector similarity search
- 📊 **Knowledge Graph**: Documents stored as chunk nodes with sequential relationships for context expansion
- 📄 **PDF Support**: Automatically extracts and indexes text from PDF documents
- 💭 **Short-term Memory**: Maintains conversation context within sessions (up to 10 messages)
- 🧠 **Long-term Memory**: Remembers user preferences and interaction history
- 📚 **Knowledge Base**: Easily add markdown and PDF files to expand the bot's knowledge
- 🔄 **OpenAI Compatible**: Works with any OpenAI-compatible API (OpenAI, Grok, Azure, etc.)

## Quick Start

### Prerequisites

1. **Discord Bot**: See [DISCORD_SETUP.md](DISCORD_SETUP.md) for complete setup instructions
   - **IMPORTANT**: Enable "Message Content Intent" in Bot settings
2. **API Keys**:
   - Grok (xAI): [console.x.ai](https://console.x.ai) - see [GROK_SETUP.md](GROK_SETUP.md)
   - OpenAI: [platform.openai.com](https://platform.openai.com/api-keys)
   - Or any OpenAI-compatible provider

### Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Run the bot
uv run src/bot.py
```

### Adding Knowledge

1. Add markdown (`.md`) or PDF (`.pdf`) files to `knowledge_base/`
2. Use `!reindex` command in Discord to reload the knowledge base

## Discord Commands

- `!ask <question>` - Ask a question using the knowledge base
- `!reindex` - Update knowledge graph (processes only new/modified files)
- `!reindex force` - Force rebuild entire knowledge graph
- `!clear` - Clear conversation history
- `!memory` - View interaction summary
- `!help_rag` - Show available commands

## Testing

Run tests with `uv`:

```bash
uv run pytest
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Architecture

**Core Components:**
- `src/graphrag_system.py` - Neo4j graph database, document ingestion, vector search
- `src/memory_system.py` - Short and long-term memory management
- `src/bot.py` - Discord bot logic and command handlers
- `knowledge_base/` - Your markdown and PDF documents

**GraphRAG Implementation:**
- Documents split into chunks stored as Neo4j nodes
- Vector embeddings for similarity search
- Sequential NEXT_CHUNK relationships for context expansion
- Incremental indexing tracks file modifications

## Deployment

Deploy to Google Cloud Run with Terraform and GitHub Actions.

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions including:
- GCP service account setup
- GitHub secrets configuration
- Automated CI/CD pipeline
- Monitoring and troubleshooting
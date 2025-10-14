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

1. **Discord Bot Setup**: Follow the detailed guide in [DISCORD_SETUP.md](DISCORD_SETUP.md)
   - Create a Discord application
   - **IMPORTANT**: Enable "Message Content Intent" in Bot settings
   - Get your bot token and add to server

2. **API Keys**: 
   - **For Grok (xAI)**: Get your key from [console.x.ai](https://console.x.ai) (recommended)
   - **For OpenAI**: Get your key from [OpenAI](https://platform.openai.com/api-keys)
   - Or use any OpenAI-compatible provider (Azure, local models, etc.)

### Setup

1. ⚠️ **Enable Discord Intents**: Go to your [Discord app](https://discord.com/developers/applications), navigate to Bot section, and enable **MESSAGE CONTENT INTENT**
2. Add API keys to Replit Secrets (already done)
3. Run the bot - it will automatically connect and index your knowledge base

### Adding Knowledge

1. Add your markdown (`.md`) or PDF (`.pdf`) files to the `knowledge_base/` directory
2. Use the `!reindex` command in Discord to reload the knowledge base

## Discord Commands

- `!ask <question>` - Ask a question using the knowledge base
- `!reindex` - Update knowledge graph (processes only new/modified files)
- `!reindex force` - Force rebuild entire knowledge graph
- `!clear` - Clear your conversation history
- `!memory` - View your interaction summary
- `!help_rag` - Show available commands

## Example Usage

```
!ask What is RAG?
!ask How does memory work in AI chatbots?
!memory
!clear
```

## Configuration

You can customize the bot by setting these environment variables:

**For Grok API** (see [GROK_SETUP.md](GROK_SETUP.md)):
- `GROK_API_KEY` - Your Grok API key from console.x.ai
- `OPENAI_BASE_URL` - Set to `https://api.x.ai/v1` for Grok chat
- `OPENAI_MODEL` - Chat model to use (e.g., `grok-beta` or other available Grok models)

**For other providers**:
- `OPENAI_BASE_URL` - Custom API endpoint
- `OPENAI_MODEL` - Chat model to use

## Architecture

- **graphrag_system.py**: Handles Neo4j graph database, document ingestion, and vector search
- **memory_system.py**: Manages short and long-term memory
- **bot.py**: Discord bot logic and command handlers
- **knowledge_base/**: Your markdown and PDF documents

### Neo4j GraphRAG Implementation
- Documents are split into chunks and stored as nodes in Neo4j
- Each chunk has vector embeddings for similarity search
- Sequential NEXT_CHUNK relationships connect adjacent chunks for context expansion
- Neo4j vector index enables fast similarity-based retrieval
- Incremental indexing tracks file modifications to avoid unnecessary reprocessing

# Agentic RAG Discord Chatbot

An intelligent Discord bot powered by Retrieval-Augmented Generation (RAG) with short and long-term memory capabilities.

## Features

- 🤖 **RAG System**: Answers questions based on your markdown knowledge base
- 💭 **Short-term Memory**: Maintains conversation context within sessions
- 🧠 **Long-term Memory**: Remembers user preferences across sessions
- 📚 **Knowledge Base**: Easily add markdown files to expand the bot's knowledge
- 🔄 **OpenAI Compatible**: Works with any OpenAI-compatible API

## Quick Start

### Prerequisites

1. **Discord Bot Setup**: Follow the detailed guide in [DISCORD_SETUP.md](DISCORD_SETUP.md)
   - Create a Discord application
   - **IMPORTANT**: Enable "Message Content Intent" in Bot settings
   - Get your bot token and add to server

2. **OpenAI API Key**: Get your API key from [OpenAI](https://platform.openai.com/api-keys)
   - Or use any OpenAI-compatible provider (Azure, Groq, local models, etc.)

### Setup

1. ⚠️ **Enable Discord Intents**: Go to your [Discord app](https://discord.com/developers/applications), navigate to Bot section, and enable **MESSAGE CONTENT INTENT**
2. Add API keys to Replit Secrets (already done)
3. Run the bot - it will automatically connect and index your knowledge base

### Adding Knowledge

1. Add your markdown files to the `knowledge_base/` directory
2. Use the `!reindex` command in Discord to reload the knowledge base

## Discord Commands

- `!ask <question>` - Ask a question using the knowledge base
- `!reindex` - Reload and reindex the knowledge base
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

- `OPENAI_BASE_URL` - Custom API endpoint (default: OpenAI)
- `OPENAI_MODEL` - Model to use (default: gpt-4)

## Architecture

- **rag_system.py**: Handles document ingestion and semantic search
- **memory_system.py**: Manages short and long-term memory
- **bot.py**: Discord bot logic and command handlers
- **knowledge_base/**: Your markdown documents

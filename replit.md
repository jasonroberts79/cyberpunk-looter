# Agentic RAG Discord Chatbot

## Overview
An intelligent Discord bot that uses Retrieval-Augmented Generation (RAG) with short and long-term memory capabilities. The bot answers questions based on markdown and PDF knowledge bases and maintains conversation context across sessions.

## Features
- **RAG System**: Semantic search over markdown and PDF documents using ChromaDB
- **PDF Support**: Automatically extracts and indexes text from PDF files
- **Short-term Memory**: Maintains conversation context within sessions
- **Long-term Memory**: Persists user preferences and interaction history
- **Discord Integration**: Fully functional Discord bot with command interface
- **OpenAI Compatible**: Works with any OpenAI-compatible API (OpenAI, Azure, local models, etc.)

## Architecture

### Components
1. **RAG System** (`rag_system.py`): Handles document ingestion, embedding, and retrieval
2. **Memory System** (`memory_system.py`): Manages short-term and long-term memory
3. **Discord Bot** (`bot.py`): Main bot logic and command handlers
4. **Knowledge Base** (`knowledge_base/`): Directory containing markdown and PDF documents

### Tech Stack
- Python 3.11
- discord.py - Discord bot framework
- LangChain - RAG orchestration
- ChromaDB - Vector database
- OpenAI SDK - LLM integration
- pypdf - PDF text extraction

## Commands
- `!ask <question>` - Ask a question using the knowledge base
- `!reindex` - Reload and reindex the knowledge base
- `!clear` - Clear conversation history
- `!memory` - View interaction summary
- `!help_rag` - Show available commands

## Setup
1. Set environment variables (DISCORD_BOT_TOKEN, OPENAI_API_KEY)
2. Add markdown (.md) or PDF (.pdf) files to `knowledge_base/` directory
3. Run `python bot.py`

## Recent Changes
- 2025-10-13: Initial implementation with RAG, memory systems, and Discord integration
- 2025-10-13: Fixed vector store persistence to survive restarts
- 2025-10-13: Added proper reindex functionality that prevents duplicate documents
- 2025-10-13: All core features implemented and tested
- 2025-10-13: Added PDF support for knowledge base - bot now processes both markdown and PDF files

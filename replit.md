# Agentic GraphRAG Discord Chatbot

## Overview
An intelligent Discord bot that uses Graph-based Retrieval-Augmented Generation (GraphRAG) with short and long-term memory capabilities. The bot answers questions based on markdown and PDF knowledge bases stored as a knowledge graph, enabling multi-hop reasoning and relationship-aware retrieval.

## Features
- **GraphRAG System**: Graph-based semantic search over markdown and PDF documents using Neo4j
- **Knowledge Graph**: Documents stored as connected graph nodes with sequential relationships
- **PDF Support**: Automatically extracts and indexes text from PDF files
- **Short-term Memory**: Maintains conversation context within sessions
- **Long-term Memory**: Persists user preferences and interaction history
- **Discord Integration**: Fully functional Discord bot with command interface
- **Multi-LLM Support**: Works with Grok (xAI), OpenAI, and other compatible APIs
- **Enhanced Retrieval**: Uses graph structure for context-aware document retrieval

## Architecture

### Components
1. **GraphRAG System** (`graphrag_system.py`): Builds knowledge graph, handles embedding, and graph-based retrieval
2. **Memory System** (`memory_system.py`): Manages short-term and long-term memory
3. **Discord Bot** (`bot.py`): Main bot logic and command handlers
4. **Knowledge Base** (`knowledge_base/`): Directory containing markdown and PDF documents

### Tech Stack
- Python 3.11
- discord.py - Discord bot framework
- Neo4j GraphRAG - Knowledge graph RAG orchestration
- Neo4j AuraDB - Graph database
- OpenAI SDK - LLM integration (Grok for chat, OpenAI for embeddings)
- pypdf - PDF text extraction

## Commands
- `!ask <question>` - Ask a question using the knowledge graph
- `!reindex` - Rebuild the knowledge graph from documents
- `!clear` - Clear conversation history
- `!memory` - View interaction summary
- `!help_rag` - Show available commands

## Setup
1. Set environment variables:
   - DISCORD_BOT_TOKEN
   - GROK_API_KEY (for chat)
   - OPENAI_API_KEY or OPENAI_EMBEDDINGS_KEY (for embeddings)
   - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD (Neo4j AuraDB credentials)
2. Add markdown (.md) or PDF (.pdf) files to `knowledge_base/` directory
3. Run `python bot.py`

## GraphRAG Implementation
The system stores document chunks as nodes in Neo4j with:
- **Vector embeddings** for semantic similarity search
- **Sequential relationships** (NEXT_CHUNK) connecting adjacent chunks
- **Graph-based context expansion** retrieving related chunks through relationships
- **Efficient retrieval** using Neo4j vector index for fast similarity search

## Recent Changes
- 2025-10-14: Migrated from ChromaDB to Neo4j GraphRAG architecture
- 2025-10-14: Implemented graph-based knowledge representation with chunk nodes
- 2025-10-14: Added sequential chunk relationships for context expansion
- 2025-10-14: Integrated Neo4j vector indexing for similarity search
- 2025-10-14: Updated to use graph-aware retrieval for improved responses
- 2025-10-13: Initial implementation with RAG, memory systems, and Discord integration
- 2025-10-13: Added PDF support for knowledge base

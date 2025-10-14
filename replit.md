# Agentic GraphRAG Discord Chatbot

## Overview
An intelligent Discord bot that uses Graph-based Retrieval-Augmented Generation (GraphRAG) with short and long-term memory capabilities. The bot answers questions based on markdown and PDF knowledge bases stored in a Neo4j graph database, using vector similarity search enhanced with sequential chunk relationships for improved context retrieval.

## Features
- **GraphRAG System**: Vector similarity search over markdown and PDF documents using Neo4j
- **Knowledge Graph**: Documents stored as chunk nodes with sequential NEXT_CHUNK relationships
- **PDF Support**: Automatically extracts and indexes text from PDF files  
- **Short-term Memory**: Maintains conversation context within sessions (up to 10 messages)
- **Long-term Memory**: Persists user preferences and interaction history in JSON
- **Discord Integration**: Fully functional Discord bot with command interface
- **Multi-LLM Support**: Works with Grok (xAI), OpenAI, and other OpenAI-compatible APIs
- **Graph-Enhanced Retrieval**: Uses vector search + sequential chunk expansion for better context

## Architecture

### Components
1. **GraphRAG System** (`graphrag_system.py`): Builds knowledge graph, handles embedding, and graph-based retrieval
2. **Memory System** (`memory_system.py`): Manages short-term and long-term memory
3. **Discord Bot** (`bot.py`): Main bot logic and command handlers
4. **Knowledge Base** (`knowledge_base/`): Directory containing markdown and PDF documents

### Tech Stack
- Python 3.11
- discord.py - Discord bot framework
- neo4j-graphrag - Neo4j GraphRAG library for vector retrieval
- Neo4j AuraDB - Cloud graph database
- OpenAI SDK - LLM integration (supports Grok/xAI and OpenAI)
- pypdf - PDF text extraction
- LangChain - Document processing and text splitting

## Commands
- `!ask <question>` - Ask a question using the knowledge graph
- `!reindex` - Update knowledge graph (processes only new/modified files)
- `!reindex force` - Force rebuild entire knowledge graph
- `!clear` - Clear conversation history
- `!memory` - View interaction summary
- `!help_rag` - Show available commands

## Setup
1. Set environment variables:
   - `DISCORD_BOT_TOKEN` - Discord bot authentication token
   - `GROK_API_KEY` - xAI Grok API key for chat (optional, falls back to OpenAI)
   - `OPENAI_API_KEY` or `OPENAI_EMBEDDINGS_KEY` - OpenAI key for embeddings
   - `OPENAI_BASE_URL` - API base URL (optional, defaults to OpenAI, set to https://api.x.ai/v1 for Grok chat)
   - `OPENAI_MODEL` - Chat LLM model name (optional, defaults to gpt-4, can use grok-beta or other models)
   - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` - Neo4j AuraDB credentials
2. Add markdown (.md) or PDF (.pdf) files to `knowledge_base/` directory
3. Run `python bot.py`

## GraphRAG Implementation
The system stores document chunks as nodes in Neo4j with:
- **Vector embeddings** for semantic similarity search
- **Sequential relationships** (NEXT_CHUNK) connecting adjacent chunks
- **Graph-enhanced context expansion** retrieving related chunks through relationships
- **Efficient retrieval** using Neo4j vector index for fast similarity search

The current implementation uses:
- Vector similarity search to find relevant chunks (k=10 by default)
- NEXT_CHUNK relationships to expand context with sequential chunks
- Neo4j VectorRetriever for efficient graph-based retrieval
- Incremental indexing that tracks file modifications and only processes changed files

## Recent Changes
- 2025-10-14: Updated chatbot prompt to keep responses under 2000 characters (Discord message limit)
- 2025-10-14: Fixed Neo4j MemoryPoolOutOfMemoryError by optimizing sequential relationship creation
- 2025-10-14: Added chunk_index property to chunks for efficient sequential linking
- 2025-10-14: Created composite index on (source, chunk_index) for improved query performance
- 2025-10-14: Refactored storage to use Replit Object Storage (app_storage.py) instead of file system
- 2025-10-14: Implemented incremental indexing (tracks file changes, skips unchanged files on startup)
- 2025-10-14: Aligned documentation with actual implementation (removed inflated feature claims)
- 2025-10-14: Removed deprecated rag_system.py (ChromaDB version)
- 2025-10-14: Updated help command and documentation to accurately describe capabilities
- 2025-10-14: Documented missing environment variables (OPENAI_BASE_URL, OPENAI_MODEL)
- 2025-10-14: Corrected model name documentation (grok-beta, not grok-4-fast)
- 2025-10-14: Suppressed Discord heartbeat warnings for cleaner log output
- 2025-10-14: Migrated from ChromaDB to Neo4j GraphRAG architecture
- 2025-10-14: Implemented graph-based knowledge representation with chunk nodes
- 2025-10-14: Added sequential chunk relationships for context expansion
- 2025-10-14: Integrated Neo4j vector indexing for similarity search
- 2025-10-13: Initial implementation with RAG, memory systems, and Discord integration
- 2025-10-13: Added PDF support for knowledge base

# Grok API Setup Guide

## Getting Your Grok API Key

1. Go to **[console.x.ai](https://console.x.ai)**
2. Sign in with your X (Twitter) account
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your API key

`.env` file:
```bash
OPENAI_API_KEY=your_grok_api_key
OPENAI_BASE_URL=https://api.x.ai/v1
OPENAI_MODEL=grok-4-fast
```

## Embeddings Note

Grok doesn't currently provide embeddings API. Your bot uses OpenAI embeddings for the RAG system:
- The **embedding model** still uses OpenAI (`text-embedding-3-small`)
- The **chat model** uses Grok for responses

This hybrid approach works perfectly - RAG retrieval uses OpenAI embeddings, while Grok generates the responses!
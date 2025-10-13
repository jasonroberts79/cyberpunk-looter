# Grok API Setup Guide

Your bot is already configured to work with Grok (xAI) API! Here's how to set it up.

## Getting Your Grok API Key

1. Go to **[console.x.ai](https://console.x.ai)**
2. Sign in with your X (Twitter) account
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your API key

## Configuration

### Option 1: Use Replit Secrets (Recommended)

Add these secrets in your Replit:

1. **API Key**: 
   - If you have a dedicated Grok key: Add `GROK_API_KEY` to Replit Secrets
   - Or reuse your existing `OPENAI_API_KEY` with your Grok key

2. **Base URL**: Add to Replit Secrets:
   - Key: `OPENAI_BASE_URL`
   - Value: `https://api.x.ai/v1`

3. **Model**: Add to Replit Secrets:
   - Key: `OPENAI_MODEL`
   - Value: `grok-4` (or `grok-4-mini`, `grok-code-fast-1`)

### Option 2: Use .env File

Create a `.env` file:
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_grok_api_key
OPENAI_BASE_URL=https://api.x.ai/v1
OPENAI_MODEL=grok-4
```

## Available Grok Models

| Model | Best For | Description |
|-------|----------|-------------|
| **grok-4** | General use | Flagship model with advanced reasoning |
| **grok-4-mini** | Fast responses | Lightweight model for quick tasks |
| **grok-code-fast-1** | Coding | Optimized for programming tasks |

## Grok-Specific Features

✅ **Real-time web search** - Grok can access current information  
✅ **128k context window** - Large document support  
✅ **Fast inference** - Quick response times  
✅ **OpenAI compatible** - Works with existing OpenAI SDK

## Testing

Once configured, test your bot:

```
!ask What is the latest news about AI?  (Grok can search the web!)
!ask Write a Python function to calculate fibonacci
!memory
```

## Pricing

Grok pricing varies by model. Check current rates at [docs.x.ai](https://docs.x.ai)

## Embeddings Note

Grok doesn't currently provide embeddings API. Your bot uses OpenAI embeddings for the RAG system:
- The **embedding model** still uses OpenAI (`text-embedding-3-small`)
- The **chat model** uses Grok for responses

This hybrid approach works perfectly - RAG retrieval uses OpenAI embeddings, while Grok generates the responses!

## Complete Configuration Example

```python
# Your bot automatically reads these from environment:
DISCORD_BOT_TOKEN=your_discord_token
OPENAI_API_KEY=your_grok_api_key      # Grok key here
OPENAI_BASE_URL=https://api.x.ai/v1   # Grok endpoint
OPENAI_MODEL=grok-4                    # Grok model
```

The bot will use:
- 🔹 OpenAI embeddings for document indexing (RAG)
- 🔹 Grok for chat completions and responses

Perfect combination! 🎉

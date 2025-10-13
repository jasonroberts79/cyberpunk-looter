# Discord Bot Setup Guide

## Step 1: Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name and click "Create"

## Step 2: Enable Privileged Intents (IMPORTANT!)

1. In your application, go to the **Bot** section in the left sidebar
2. Scroll down to **Privileged Gateway Intents**
3. Enable these intents:
   - ✅ **MESSAGE CONTENT INTENT** (required for reading messages)
   - ✅ **SERVER MEMBERS INTENT** (optional, for member info)
   - ✅ **PRESENCE INTENT** (optional, for presence updates)
4. Click "Save Changes"

## Step 3: Get Your Bot Token

1. Still in the **Bot** section
2. Click "Reset Token" (or "Copy" if you haven't reset it before)
3. Copy the token - you'll need to add it to Replit Secrets as `DISCORD_BOT_TOKEN`

## Step 4: Invite Bot to Your Server

1. Go to **OAuth2** > **URL Generator** in the left sidebar
2. Under **Scopes**, select:
   - ✅ `bot`
3. Under **Bot Permissions**, select:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
   - ✅ Read Message History
4. Copy the generated URL at the bottom
5. Open the URL in a new tab and select your server
6. Click "Authorize"

## Step 5: Run the Bot

The bot is ready to run! It will automatically:
- Connect to Discord
- Index your knowledge base
- Start responding to commands

## Testing

Once the bot is online, test it in your Discord server:

```
!help_rag
!ask What is RAG?
!memory
```

## Troubleshooting

**Error: "PrivilegedIntentsRequired"**
- Make sure you enabled "MESSAGE CONTENT INTENT" in the Bot settings
- Save changes and restart the bot

**Bot doesn't respond**
- Check if the bot is online in your server
- Make sure it has permission to read and send messages in the channel
- Verify your commands start with `!`

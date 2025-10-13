# Getting Started with Your Agentic RAG Discord Chatbot 🤖

## ⚠️ Important: Enable Discord Intents First!

Your bot is **fully configured and ready to run**, but Discord requires you to enable privileged intents. Follow these steps:

### Step 1: Enable Message Content Intent

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Navigate to **Bot** section (left sidebar)
4. Scroll down to **Privileged Gateway Intents**
5. ✅ Enable **MESSAGE CONTENT INTENT**
6. Click **Save Changes**

### Step 2: Invite Bot to Your Server

1. Go to **OAuth2** → **URL Generator**
2. Select scopes:
   - ✅ `bot`
3. Select permissions:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
   - ✅ Read Message History
4. Copy the generated URL and open it in a new tab
5. Select your server and authorize

### Step 3: Run the Bot

Once intents are enabled, click the **Run** button in Replit. The bot will:
- ✅ Connect to Discord
- ✅ Index your knowledge base (3 sample markdown files included)
- ✅ Start responding to commands

---

## 🎯 What Your Bot Can Do

### Core Features

- **🧠 RAG-Powered Answers**: Answers questions based on your markdown knowledge base
- **💭 Short-term Memory**: Remembers conversation context within each session
- **📚 Long-term Memory**: Saves user preferences and interaction history across sessions
- **🔄 OpenAI Compatible**: Works with any OpenAI-compatible API

### Available Commands

```
!ask <question>     - Ask a question using the knowledge base
!reindex            - Reload and reindex the knowledge base
!clear              - Clear your conversation history
!memory             - View your interaction summary
!help_rag           - Show available commands
```

---

## 📝 Customizing Your Knowledge Base

### Adding Your Own Documents

1. Add markdown files (`.md`) to the `knowledge_base/` directory
2. In Discord, type `!reindex` to load the new documents
3. Ask questions about your content with `!ask`

### Sample Knowledge Included

Your bot comes with 3 sample documents:
- **sample_doc1.md**: Introduction to RAG systems
- **sample_doc2.md**: Memory systems in AI chatbots
- **sample_doc3.md**: Discord bot development guide

---

## 🔧 Configuration

### Environment Variables

Already configured in Replit Secrets:
- ✅ `DISCORD_BOT_TOKEN` - Your Discord bot token
- ✅ `OPENAI_API_KEY` - Your OpenAI API key

### Optional Settings

You can customize these by adding to Replit Secrets:

- `OPENAI_BASE_URL` - Use a different API endpoint (Azure, Groq, local models)
- `OPENAI_MODEL` - Change the model (default: `gpt-4`)

---

## 🧪 Testing Your Bot

Once the bot is online in Discord:

```
!help_rag
!ask What is RAG?
!ask How does memory work in AI chatbots?
!memory
!clear
!ask Tell me about Discord bots
```

---

## 📂 Project Structure

```
.
├── bot.py                 # Main Discord bot logic
├── rag_system.py         # RAG implementation with ChromaDB
├── memory_system.py      # Short and long-term memory
├── knowledge_base/       # Your markdown documents
│   ├── sample_doc1.md
│   ├── sample_doc2.md
│   └── sample_doc3.md
├── chroma_db/           # Vector database (auto-created)
└── long_term_memory.json # User memory storage (auto-created)
```

---

## 🚀 Next Steps

1. **Enable Discord intents** (see Step 1 above)
2. **Invite bot to your server** (see Step 2 above)
3. **Run the bot** and test with `!help_rag`
4. **Add your own markdown files** to customize the knowledge base
5. **Share your bot** with others in your Discord server!

---

## 🐛 Troubleshooting

### Bot doesn't respond to commands
- Make sure the bot is online in your server
- Verify commands start with `!`
- Check that the bot has permission to read and send messages

### "PrivilegedIntentsRequired" error
- Enable **MESSAGE CONTENT INTENT** in Discord Developer Portal
- Save changes and restart the bot

### Knowledge base not updating
- Use `!reindex` command after adding new markdown files
- Verify files are in the `knowledge_base/` directory with `.md` extension

---

## 📚 Learn More

- **Full Setup Guide**: [DISCORD_SETUP.md](DISCORD_SETUP.md)
- **Technical Details**: [README.md](README.md)
- **Project Documentation**: [replit.md](replit.md)

Enjoy your intelligent Discord chatbot! 🎉

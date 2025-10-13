import os
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
from rag_system import RAGSystem
from memory_system import MemorySystem
from typing import Optional

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDINGS_KEY = os.getenv("OPENAI_EMBEDDINGS_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

CHAT_API_KEY = GROK_API_KEY if GROK_API_KEY else OPENAI_API_KEY
EMBEDDINGS_KEY = OPENAI_EMBEDDINGS_KEY if OPENAI_EMBEDDINGS_KEY else OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

rag_system: Optional[RAGSystem] = None
memory_system: Optional[MemorySystem] = None
openai_client: Optional[OpenAI] = None

@bot.event
async def on_ready():
    global rag_system, memory_system, openai_client
    
    print(f'{bot.user} has connected to Discord!')
    
    if not CHAT_API_KEY:
        print("ERROR: No chat API key found (GROK_API_KEY or OPENAI_API_KEY)!")
        return
    
    if not EMBEDDINGS_KEY:
        print("ERROR: No embeddings API key found (OPENAI_EMBEDDINGS_KEY or OPENAI_API_KEY)!")
        return
    
    print("Initializing RAG system...")
    print(f"Using OpenAI embeddings for RAG indexing")
    rag_system = RAGSystem(openai_api_key=EMBEDDINGS_KEY)
    
    print("Indexing knowledge base...")
    rag_system.index_documents()
    
    print("Initializing memory system...")
    memory_system = MemorySystem()
    
    print(f"Initializing chat client...")
    if GROK_API_KEY:
        print(f"Using Grok API with model: {OPENAI_MODEL}")
    else:
        print(f"Using OpenAI API with model: {OPENAI_MODEL}")
        
    if OPENAI_BASE_URL:
        openai_client = OpenAI(api_key=CHAT_API_KEY, base_url=OPENAI_BASE_URL)
    else:
        openai_client = OpenAI(api_key=CHAT_API_KEY)
    
    print("Bot is ready!")

@bot.command(name="ask", help="Ask a question using the knowledge base")
async def ask_question(ctx, *, question: str):
    if not rag_system or not memory_system or not openai_client:
        await ctx.send("Bot is still initializing. Please wait...")
        return
    
    user_id = str(ctx.author.id)
    
    async with ctx.typing():
        memory_system.update_long_term(user_id, "interaction", None)
        
        memory_system.add_to_short_term(user_id, "user", question)
        
        context = rag_system.get_context_for_query(question, k=10)
        
        short_term_context = memory_system.get_short_term_context(user_id, max_messages=4)
        user_summary = memory_system.get_user_summary(user_id)
        
        conversation_history = []
        for msg in short_term_context:
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        system_prompt = f"""You are a helpful AI assistant with access to a knowledge base. 
        
User Context: {user_summary}

Use the following context from the knowledge base to answer questions. If the answer isn't in the context, say so clearly.

Knowledge Base Context:
{context}

Be conversational, helpful, and remember details from our conversation."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": question})
        
        try:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content or "I couldn't generate a response."
            
            memory_system.add_to_short_term(user_id, "assistant", answer)
            
            if len(answer) > 2000:
                chunks = [answer[i:i+2000] for i in range(0, len(answer), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(answer)
                
        except Exception as e:
            await ctx.send(f"Error generating response: {str(e)}")
            print(f"Error: {e}")

@bot.command(name="reindex", help="Reload and reindex the knowledge base")
async def reindex(ctx):
    if not rag_system:
        await ctx.send("RAG system not initialized.")
        return
    
    async with ctx.typing():
        rag_system.index_documents()
        await ctx.send("Knowledge base reindexed successfully!")

@bot.command(name="clear", help="Clear your conversation history")
async def clear_memory(ctx):
    if not memory_system:
        await ctx.send("Memory system not initialized.")
        return
    
    user_id = str(ctx.author.id)
    memory_system.clear_short_term(user_id)
    await ctx.send("Your conversation history has been cleared!")

@bot.command(name="memory", help="View your interaction summary")
async def show_memory(ctx):
    if not memory_system:
        await ctx.send("Memory system not initialized.")
        return
    
    user_id = str(ctx.author.id)
    summary = memory_system.get_user_summary(user_id)
    await ctx.send(f"**Your Memory Summary:**\n{summary}")

@bot.command(name="help_rag", help="Show available commands")
async def help_command(ctx):
    help_text = """
**Available Commands:**

`!ask <question>` - Ask a question using the knowledge base
`!reindex` - Reload and reindex the knowledge base
`!clear` - Clear your conversation history
`!memory` - View your interaction summary
`!help_rag` - Show this help message

**Example:**
`!ask What is the main topic in the knowledge base?`
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
    else:
        bot.run(DISCORD_TOKEN)

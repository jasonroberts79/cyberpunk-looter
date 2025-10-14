import os
import io
import logging
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
from graphrag_system import GraphRAGSystem
from memory_system import MemorySystem
from typing import Optional

load_dotenv()

logging.getLogger('discord.gateway').setLevel(logging.ERROR)

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
GROK_API_KEY = os.getenv("GROK_API_KEY")

OPENAI_EMBEDDINGS_KEY = os.getenv("OPENAI_EMBEDDINGS_KEY")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

graphrag_system: Optional[GraphRAGSystem] = None
memory_system: Optional[MemorySystem] = None
openai_client: Optional[OpenAI] = None

@bot.event
async def on_ready():
    global graphrag_system, memory_system, openai_client
    
    print(f'{bot.user} has connected to Discord!')
    
    if not GROK_API_KEY:
        print("ERROR: No chat API key found (GROK_API_KEY or OPENAI_API_KEY)!")
        return
    
    if not OPENAI_EMBEDDINGS_KEY:
        print("ERROR: No embeddings API key found (OPENAI_EMBEDDINGS_KEY or OPENAI_API_KEY)!")
        return
    
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("ERROR: Neo4j credentials not found (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)!")
        return
    
    print("Initializing GraphRAG system...")
    print(f"Using Neo4j GraphRAG with OpenAI embeddings")
    graphrag_system = GraphRAGSystem(
        neo4j_uri=NEO4J_URI,
        neo4j_username=NEO4J_USERNAME,
        neo4j_password=NEO4J_PASSWORD,
        openai_api_key=OPENAI_EMBEDDINGS_KEY,
        grok_api_key=GROK_API_KEY,
        grok_model=OPENAI_MODEL
    )
    
    print("Building knowledge graph (this may take several minutes)...")
    await graphrag_system.build_knowledge_graph()
    
    print("Initializing memory system...")
    memory_system = MemorySystem()
    
    print(f"Initializing chat client...")
    print(f"Using Grok API with model: {OPENAI_MODEL}")
        
    if OPENAI_BASE_URL:
        openai_client = OpenAI(api_key=GROK_API_KEY, base_url=OPENAI_BASE_URL)
    else:
        openai_client = OpenAI(api_key=GROK_API_KEY)
    
    print("Bot is ready!")

@bot.command(name="ask", help="Ask a question using the knowledge base")
async def ask_question(ctx, *, question: str):
    if not graphrag_system or not memory_system or not openai_client:
        await ctx.send("Bot is still initializing. Please wait...")
        return
    
    user_id = str(ctx.author.id)
    
    async with ctx.typing():
        memory_system.update_long_term(user_id, "interaction", None)
        
        memory_system.add_to_short_term(user_id, "user", question)
        
        context = graphrag_system.get_context_for_query(question, k=10)
        
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

Be concise and direct.

Remember details from our conversation."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": question})
        
        try:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.6,
                max_completion_tokens=15000,
            )
            
            answer = response.choices[0].message.content or "I couldn't generate a response."
            
            memory_system.add_to_short_term(user_id, "assistant", answer)
            
            file = io.StringIO(answer)
            file.name = "answer.txt"
            await ctx.send(file=discord.File(file, filename="answer.txt"))
                
        except Exception as e:
            await ctx.send(f"Error generating response: {str(e)}")
            print(f"Error: {e}")

@bot.command(name="reindex", help="Rebuild the knowledge graph (use 'force' to rebuild all files)")
async def reindex(ctx, *, mode: str = ""):
    if not graphrag_system:
        await ctx.send("GraphRAG system not initialized.")
        return
    
    force_rebuild = mode.strip().lower() == "force"
    
    async with ctx.typing():
        if force_rebuild:
            await ctx.send("Force rebuilding knowledge graph... This will reprocess all files.")
        else:
            await ctx.send("Updating knowledge graph... Only processing new/modified files.")
        
        await graphrag_system.build_knowledge_graph(force_rebuild=force_rebuild)
        await ctx.send("Knowledge graph updated successfully!")

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

`!ask <question>` - Ask a question using the knowledge graph
`!reindex` - Update knowledge graph (processes only new/modified files)
`!reindex force` - Force rebuild entire knowledge graph
`!clear` - Clear your conversation history
`!memory` - View your interaction summary
`!help_rag` - Show this help message

**Example:**
`!ask What is the main topic in the knowledge base?`

**GraphRAG Features:**
- Vector similarity search with graph-enhanced context
- Sequential chunk relationships for context expansion
- Neo4j graph database for efficient retrieval
- Conversation memory and user preference tracking
- Incremental indexing (skips unchanged files)
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
    else:
        try:
            bot.run(DISCORD_TOKEN)
        except KeyboardInterrupt:
            print("Bot stopped by user")

import os
import io
import sys
import socket
import logging
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
from graphrag_system import GraphRAGSystem
from memory_system import MemorySystem
from typing import Optional, Any, cast

load_dotenv()

logging.getLogger("discord.gateway").setLevel(logging.ERROR)

def ensure_envvar(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print(f"ERROR: Environment variable {var_name} is missing!")
        sys.exit(1)
    return value.strip()

DISCORD_TOKEN = ensure_envvar("DISCORD_BOT_TOKEN")

OPENAI_MODEL = ensure_envvar("OPENAI_MODEL")
OPENAI_BASE_URL = ensure_envvar("OPENAI_BASE_URL")
GROK_API_KEY = ensure_envvar("GROK_API_KEY")

OPENAI_EMBEDDINGS_KEY = ensure_envvar("OPENAI_EMBEDDINGS_KEY")

NEO4J_URI = ensure_envvar("NEO4J_URI")
NEO4J_USERNAME = ensure_envvar("NEO4J_USERNAME")
NEO4J_PASSWORD = ensure_envvar("NEO4J_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

graphrag_system: Optional[GraphRAGSystem] = None
memory_system: Optional[MemorySystem] = None
openai_client: Optional[OpenAI] = None

def check_internet_connectivity():
    """Check internet connectivity by attempting to connect to google.com"""
    print("Checking internet connectivity...")
    try:
        # Try to connect to google.com on port 80
        socket.create_connection(("google.com", 80), timeout=5)
        print("✓ Internet connectivity verified")
        return True
    except (socket.timeout, socket.error) as e:
        print(f"✗ No internet connection detected: {e}")
        print("ERROR: Bot requires internet access to function. Exiting...")
        return False

@bot.event
async def on_ready():
    global graphrag_system, memory_system, openai_client

    print(f"{bot.user} has connected to Discord!")

    if not all([GROK_API_KEY, OPENAI_BASE_URL]):
        print("ERROR: Chat API key or URL missing (GROK_API_KEY or OPENAI_BASE_URL)!")
        return

    if not OPENAI_EMBEDDINGS_KEY:
        print("ERROR: No embeddings API key found (OPENAI_EMBEDDINGS_KEY)!")
        return

    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print(
            "ERROR: Neo4j credentials not found (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)!"
        )
        return

    print("Initializing GraphRAG system...")
    print("Using Neo4j GraphRAG with OpenAI embeddings")
    graphrag_system = GraphRAGSystem(
        neo4j_uri=NEO4J_URI,
        neo4j_username=NEO4J_USERNAME,
        neo4j_password=NEO4J_PASSWORD,
        openai_api_key=OPENAI_EMBEDDINGS_KEY,
        grok_api_key=GROK_API_KEY,
        grok_model=OPENAI_MODEL,
    )

    print("Building knowledge graph (this may take several minutes)...")
    await graphrag_system.build_knowledge_graph()

    print("Initializing memory system...")
    memory_system = MemorySystem()

    print("Initializing chat client...")
    print(f"Using Grok API with model: {OPENAI_MODEL}")

    openai_client = OpenAI(api_key=GROK_API_KEY, base_url=OPENAI_BASE_URL)

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

        short_term_context = memory_system.get_short_term_context(
            user_id, max_messages=4
        )
        user_summary = memory_system.get_user_summary(user_id)
        party_summary = memory_system.get_party_summary(user_id)

        conversation_history = []
        for msg in short_term_context:
            conversation_history.append(
                {"role": msg["role"], "content": msg["content"]}
            )

        system_prompt = f"""You are a helpful AI assistant with access to a knowledge base about the RPG Cyberpunk RED. 
Be careful not to make up answers or to use information about the other Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020) unless it is explicitly in the knowledge base.
    
User Context: {user_summary}

Party Context:
{party_summary}

Use the following context from the knowledge base to answer questions. If the answer isn't in the context, say so clearly.

Knowledge Base Context:
{context}

Be concise and direct. Remember details from our conversation."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": question})

        try:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=cast(Any, messages),
                temperature=0.6,
                max_completion_tokens=15000,
            )

            answer = (
                response.choices[0].message.content or "I couldn't generate a response."
            )

            memory_system.add_to_short_term(user_id, "assistant", answer)

            if len(answer) > 2000:
                file = io.BytesIO(answer.encode("utf-8"))
                file.seek(0)
                await ctx.send(file=discord.File(file, filename="answer.txt"))
            else:
                await ctx.send(answer)

        except Exception as e:
            await ctx.send(f"Error generating response: {str(e)}")
            print(f"Error: {e}")


@bot.command(
    name="reindex",
    help="Rebuild the knowledge graph (use 'force' to rebuild all files)",
)
async def reindex(ctx, *, mode: str = ""):
    if not graphrag_system:
        await ctx.send("GraphRAG system not initialized.")
        return

    force_rebuild = mode.strip().lower() == "force"

    async with ctx.typing():
        if force_rebuild:
            await ctx.send(
                "Force rebuilding knowledge graph... This will reprocess all files."
            )
        else:
            await ctx.send(
                "Updating knowledge graph... Only processing new/modified files."
            )

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


@bot.command(name="add_character", help="Add a character to the party")
async def add_character(ctx, name: str, role: str, *, gear_prefs: str = ""):
    """
    Add or update a party character.
    Usage: !add_character <name> <role> <gear_preference1, gear_preference2, ...>
    Example: !add_character "V" Solo "Assault Rifles", "Body Armor"
    """
    if not memory_system:
        await ctx.send("Memory system not initialized.")
        return

    # Parse gear preferences (comma-separated)
    gear_preferences = [pref.strip() for pref in gear_prefs.split(",") if pref.strip()]

    user_id = str(ctx.author.id)
    is_new = memory_system.add_party_character(user_id, name, role, gear_preferences)

    if is_new:
        msg = f"Character **{name}** added to your party!\n"
    else:
        msg = f"Character **{name}** updated!\n"

    msg += f"- Role: {role}\n"
    if gear_preferences:
        msg += f"- Gear Preferences: {', '.join(gear_preferences)}"
    else:
        msg += "- Gear Preferences: None specified"

    await ctx.send(msg)


@bot.command(name="view_party", help="View all party characters")
async def view_party(ctx):
    """View all registered party characters"""
    if not memory_system:
        await ctx.send("Memory system not initialized.")
        return

    user_id = str(ctx.author.id)
    characters = memory_system.list_party_characters(user_id)

    if not characters:
        await ctx.send("No characters in your party yet. Use `!add_character` to add one!")
        return

    msg = "**Your Party Members:**\n\n"
    for char in characters:
        msg += f"**{char['name']}**\n"
        msg += f"- Role: {char['role']}\n"
        if char.get("gear_preferences"):
            msg += f"- Gear Preferences: {', '.join(char['gear_preferences'])}\n"
        else:
            msg += "- Gear Preferences: None\n"
        msg += "\n"

    if len(msg) > 2000:
        file = io.BytesIO(msg.encode("utf-8"))
        file.seek(0)
        await ctx.send(file=discord.File(file, filename="party.txt"))
    else:
        await ctx.send(msg)


@bot.command(name="remove_character", help="Remove a character from the party")
async def remove_character(ctx, *, name: str):
    """Remove a character from the party"""
    if not memory_system:
        await ctx.send("Memory system not initialized.")
        return

    user_id = str(ctx.author.id)
    success = memory_system.remove_party_character(user_id, name)

    if success:
        await ctx.send(f"Character **{name}** has been removed from your party.")
    else:
        await ctx.send(f"Character **{name}** not found in your party.")


@bot.command(name="recommend_gear", help="Get gear distribution recommendations")
async def recommend_gear(ctx, *, args: str):
    """
    Recommend gear distribution for party members using AI.
    By default, considers all party members, if you want to exclude someone say so in the prompt.
    Accepts natural language descriptions of loot.

    Usage: !recommend_gear <loot description>
    Examples:
      !recommend_gear Assault Rifle, Body Armor, Neural Processor
      !recommend_gear We got a heavy pistol and some body armor from the ganger
      !recommend_gear 2 SMGs and a tech scanner
    """
    if not memory_system or not openai_client:
        await ctx.send("Bot is still initializing. Please wait...")
        return

    user_id = str(ctx.author.id)

    loot_description = args.strip()

    # Validate loot description is not empty
    if not loot_description:
        await ctx.send("Please describe the loot to distribute.")
        return

    # Get all party members
    all_chars = memory_system.list_party_characters(user_id)

    if not all_chars:
        await ctx.send(
            "You don't have any party members registered yet.\n"
            "Use `!add_character` to add party members first."
        )
        return

    async with ctx.typing():
        # Build party context for the LLM
        party_context = "Party Members:\n"
        for char in all_chars:
            party_context += f"- {char['name']} ({char['role']})"
            if char.get('gear_preferences'):
                party_context += f" - Prefers: {', '.join(char['gear_preferences'])}"
            party_context += "\n"

        # Create prompt for the LLM
        prompt = f"""You are a game master helping distribute loot fairly and strategically with access to a knowledge base about the RPG Cyberpunk RED.
Be careful not to make up answers or to use information about the other Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020) unless it is explicitly in the knowledge base.

Party Context:
{party_context}

Loot Description:
{loot_description}

Please parse the loot description to identify individual items, then recommend how to distribute them among the party members. Consider:
1. Character roles and their typical gear needs
2. Each character's stated gear preferences
3. Fair distribution when preferences conflict
4. Overall party effectiveness
5. The market value of the item if no clear preference can be determined

Provide your recommendations in this format:
**[Character Name]** ([Role])
  - [Item 1]
  - [Item 2]
  ...

"""

        try:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=cast(Any, [
                    {"role": "system", "content": "You are a knowledgeable game master who helps parties distribute loot fairly and strategically."},
                    {"role": "user", "content": prompt}
                ]),
                temperature=0.7,
                max_completion_tokens=2000,
            )

            recommendation = response.choices[0].message.content or "I couldn't generate recommendations."

            if len(recommendation) > 2000:
                file = io.BytesIO(recommendation.encode("utf-8"))
                file.seek(0)
                await ctx.send(file=discord.File(file, filename="gear_recommendations.txt"))
            else:
                await ctx.send(recommendation)

        except Exception as e:
            await ctx.send(f"Error generating recommendations: {str(e)}")
            print(f"Error: {e}")


@bot.command(name="help_rag", help="Show available commands")
async def help_command(ctx):
    help_text = """
**Available Commands:**

**Knowledge Base:**
`!ask <question>` - Ask a question using the knowledge graph
`!reindex` - Update knowledge graph (processes only new/modified files)
`!clear` - Clear your conversation history
`!memory` - View your interaction summary

**Party Management:**
`!add_character <name> <role> <gear_prefs>` - Add/update a party character
`!view_party` - View all party characters
`!remove_character <name>` - Remove a character from the party
`!recommend_gear <loot>` - Get AI gear recommendations (natural language)

`!help_rag` - Show this help message

**Examples:**
`!ask What is the main topic in the knowledge base?`
`!add_character V Solo Assault Rifles, Body Armor`
`!recommend_gear Assault Rifle, Neural Processor, Body Armor`
`!recommend_gear We got 2 SMGs and some cyberware from the ganger boss`
`!recommend_gear Heavy Pistol, Tech Scanner, and Scrambler`

**GraphRAG Features:**
- Vector similarity search with graph-enhanced context
- Sequential chunk relationships for context expansion
- Neo4j graph database for efficient retrieval
- Conversation memory and user preference tracking
- Incremental indexing (skips unchanged files)

**Party & Gear Features:**
- Store party character data (name, role, gear preferences)
- AI-powered gear distribution recommendations
- Natural language loot descriptions (e.g., "2 SMGs and body armor")
- Considers all party members by default
- Optional exclusion of specific members from distribution
- Context-aware recommendations based on roles and preferences
    """
    await ctx.send(help_text)


if __name__ == "__main__":
    # Check internet connectivity first
    if not check_internet_connectivity():
        sys.exit(1)

    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
        sys.exit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("Bot stopped by user")

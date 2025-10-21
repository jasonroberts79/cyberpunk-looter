import os
import io
import sys
import socket
import traceback
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.responses import EasyInputMessageParam, ResponseInputParam
from graphrag_system import GraphRAGSystem
from memory_system import MemorySystem
from typing import Optional, cast, List, Any
from agentic_handler import (
    pending_confirmations,
    get_pending_confirmation,
    is_timed_out,
    handle_timeout,
    handle_approval,
    handle_rejection,
    check_and_cleanup_timeouts,
    handle_tool_calls,
    get_tool_definitions,
)

load_dotenv()

game_context = "You have with access to a knowledge base about the RPG Cyberpunk RED. Be careful not to make up answers or to use information about the other Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020)."


def ensure_envvar(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None or value == "":
        print(f"ERROR: Environment variable {var_name} is missing!")
        sys.exit(1)
    assert value is not None  # Type narrowing for type checker
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


@bot.event
async def on_reaction_add(reaction, user):
    """Handle confirmation/cancellation via reactions."""
    # Skip if user is bot
    if user.bot:
        return

    # Get message_id
    message_id = str(reaction.message.id)

    # Check if message_id in pending_confirmations
    if message_id not in pending_confirmations:
        return

    # Get confirmation
    confirmation = get_pending_confirmation(message_id)
    if not confirmation:
        return

    # Only original requester can confirm
    if str(user.id) != confirmation["user_id"]:
        return

    # Check if already processed
    if confirmation.get("processed"):
        # Remove reaction and return
        await reaction.remove(user)
        return

    # Check if timed out
    if is_timed_out(confirmation):
        await handle_timeout(message_id, confirmation, bot)
        return

    # Process based on reaction
    if str(reaction.emoji) == "👍":
        await handle_approval(
            reaction.message,
            confirmation,
            memory_system,
            graphrag_system,
            openai_client,
            OPENAI_MODEL,
            bot,
        )
    elif str(reaction.emoji) == "👎":
        await handle_rejection(reaction.message, confirmation)


@bot.command(name="ai", help="Interact with the AI")
async def ask_question(ctx, *, question: str):
    if not graphrag_system or not memory_system or not openai_client:
        await ctx.send("Bot is still initializing. Please wait...")
        return

    user_id = str(ctx.author.id)

    # Check and cleanup timeouts for this user
    await check_and_cleanup_timeouts(user_id, bot)

    async with ctx.typing():
        memory_system.update_long_term(user_id, "interaction", None)

        memory_system.add_to_short_term(user_id, "user", question)

        context = graphrag_system.get_context_for_query(question, k=10)

        user_summary = memory_system.get_user_summary(user_id)
        party_summary = memory_system.get_party_summary(user_id)
        previous_response_id = memory_system.get_last_response_id(user_id)

        # Build the input based on whether we have a previous conversation
        if previous_response_id:
            # Continue existing conversation - only send new message
            input_messages = [
                EasyInputMessageParam({"role": "user", "content": question})
            ]
        else:
            # Start new conversation - send full context
            short_term_context = memory_system.get_short_term_context(
                user_id, max_messages=4
            )
            conversation_history: list[EasyInputMessageParam] = []
            for msg in short_term_context:
                conversation_history.append(
                    EasyInputMessageParam(
                        {"role": msg["role"], "content": msg["content"]}
                    )
                )

            input_messages: ResponseInputParam = [
                EasyInputMessageParam(
                    {
                        "role": "system",
                        "content": create_system_prompt(
                            context, user_summary, party_summary
                        ),
                    }
                )
            ]
            input_messages.extend(conversation_history)
            input_messages.append(
                EasyInputMessageParam({"role": "user", "content": question})
            )

        try:
            response = openai_client.responses.create(
                model=OPENAI_MODEL,
                input=input_messages,
                temperature=0.6,
                tools=get_tool_definitions(),
                tool_choice="auto",
                previous_response_id=previous_response_id,
            )
            # Handle tool calls if present
            handled = await handle_tool_calls(
                ctx,
                response,
                user_id,
                openai_client,
                memory_system,
                graphrag_system,
                OPENAI_MODEL,
                bot,
            )
            if handled:
                return

            # Save the response ID for future continuations
            memory_system.set_last_response_id(user_id, response.id)

            answer = response.output[0].content[0].text
            if not answer:
                answer = "I couldn't generate a response."

            memory_system.add_to_short_term(user_id, "assistant", answer)

            if len(answer) > 2000:
                file = io.BytesIO(answer.encode("utf-8"))
                file.seek(0)
                await ctx.send(file=discord.File(file, filename="answer.txt"))
            else:
                await ctx.send(answer)

        except Exception as e:
            error_msg = str(e)

            # Build detailed error log
            input_messages = cast(List[Any], input_messages)
            error_log = [
                "=" * 80,
                "ERROR in !ai command",
                f"User: {ctx.author.name} (ID: {user_id})",
                f"Question: {question}",
                f"Model: {OPENAI_MODEL}",
                f"Previous Response ID: {previous_response_id if previous_response_id else 'None (new conversation)'}",
                f"Error Type: {type(e).__name__}",
                f"Error Message: {error_msg}",
                "",
                "API Parameters:",
                f"  - Tools: {len(get_tool_definitions())} tool definitions",
                f"  - Input Messages: {len(input_messages)} messages",
            ]

            if previous_response_id:
                error_log.append(
                    f"  - Using previous_response_id: {previous_response_id}"
                )

            error_log.extend(["", "Full Traceback:", traceback.format_exc(), "=" * 80])

            # Log the complete error information
            print("\n".join(error_log))

            # Check if the error is due to an invalid/expired response ID
            if previous_response_id and (
                "response" in error_msg.lower() or "not found" in error_msg.lower()
            ):
                print(
                    "Identified as expired/invalid response ID error. Clearing and asking user to retry."
                )
                # Clear the invalid response ID and retry
                memory_system.set_last_response_id(user_id, "")
                await ctx.send("Previous conversation expired. Starting fresh...")
                # Retry the command would require recursion, so just inform the user
                await ctx.send("Please try your question again.")
            else:
                await ctx.send(f"Error: {error_msg}")


def create_system_prompt(context, user_summary, party_summary):
    system_prompt = f"""You are a helpful AI assistant.
{game_context}
User Context: {user_summary}
Party Context:
{party_summary}
Use the following context from the knowledge base to answer questions. If the answer isn't in the context, say so clearly.
Knowledge Base Context:
{context}
Be concise and direct. Remember details from our conversation."""

    return system_prompt


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


@bot.command(name="help_rag", help="Show available commands")
async def help_command(ctx):
    help_text = """
**Available Commands:**

**Knowledge Base:**
`!ai <question>` - Ask a question using the knowledge graph
`!reindex` - Update knowledge graph (processes only new/modified files)
`!clear` - Clear your conversation history
`!memory` - View your interaction summary
`!help_rag` - Show this help message

**Party Management:**
Use `!ai` to manage your party and get gear recommendations through natural conversation.

**Examples:**
`!ai What is the main topic in the knowledge base?`
`!ai Can you add V to my party? He's a Solo who likes assault rifles`
`!ai Please remove Johnny from the party`
`!ai Show me all my party members`
`!ai We found 2 SMGs and body armor, how should we distribute it?`
`!ai Recommend gear for the assault rifle and neural processor, but exclude V`

**GraphRAG Features:**
- Vector similarity search with graph-enhanced context
- Sequential chunk relationships for context expansion
- Neo4j graph database for efficient retrieval
- Conversation memory and user preference tracking
- Incremental indexing (skips unchanged files)

**Party & Gear Features:**
- Add, remove, and view party characters through natural language
- AI-powered gear distribution recommendations
- Stores party character data (name, role, gear preferences)
- Natural language loot descriptions
- Confirmation system for all party actions
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

"""
Discord bot for Cyberpunk RED looter functionality.

This module implements the Discord bot interface using dependency injection
from the container to eliminate global state.
"""

import io
import sys
import traceback
from anthropic.types import ToolUseBlock
import discord
from sre_compile import isstring
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from container import Container

load_dotenv()

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dependency injection container
container: Container


@bot.event
async def on_ready():
    """Initialize services when bot connects to Discord."""
    global container

    print(f"{bot.user} has connected to Discord!")
    print("Initializing services...")

    # Initialize async components
    await container.initialize()

    print("Bot is ready!")


@bot.event
async def on_reaction_add(reaction, user):
    """Handle confirmation/cancellation via reactions."""
    # Skip if user is bot
    if user.bot:
        return

    # Get reactions handler from container
    reactions_handler = container.reaction_handler
    if not reactions_handler:
        return

    # Get message_id
    message_id = str(reaction.message.id)

    # Check if message_id in pending_confirmations
    if message_id not in reactions_handler.pending_confirmations:
        return

    # Get confirmation
    confirmation = reactions_handler.get_pending_confirmation(message_id)
    if not confirmation:
        return

    # Only original requester can confirm
    if str(user.id) != confirmation.user_id:
        return

    # Check if already processed
    if confirmation.processed:
        # Remove reaction and return
        await reaction.remove(user)
        return

    # Check if timed out
    if reactions_handler.is_timed_out(confirmation):
        await reactions_handler.handle_timeout(message_id, confirmation, bot)
        return

    # Process based on reaction
    if str(reaction.emoji) == "👍":
        await reactions_handler.handle_approval(
            reaction.message,
            confirmation,
        )
    elif str(reaction.emoji) == "👎":
        await reactions_handler.handle_rejection(reaction.message, confirmation)


@bot.command(name="ai", help="Interact with the AI")
async def ask_question(ctx: Context, *, question: str):
    """Handle AI interaction command."""
    user_id = str(ctx.author.id)
    party_id = str(ctx.guild.id) if ctx.guild else user_id    

    if not container.reaction_handler:
        await ctx.send("Bot is not fully initialized. Please try again in a moment.")
        return

    # Check and cleanup timeouts for this user
    await container.reaction_handler.check_and_cleanup_timeouts(user_id, bot)

    async with ctx.typing():
        try:
            # Process the query through the LLM            
            content = container.conversation_service.process_query(user_id, party_id, question)
            for block in content:
                if block.type == "text":                
                    await _send_reply(ctx, block.text)
                elif block.type == "tool_use":            
                    await _handle_tool_calls(ctx, block)

        except Exception as e:
            error_msg = str(e)

            # Build detailed error log
            error_log = [
                "=" * 80,
                "ERROR in !ai command",
                f"User: {ctx.author.name} (ID: {user_id})",
                f"Question: {question}",
                f"Error Type: {type(e).__name__}",
                f"Error Message: {error_msg}",
                "",
                "Full Traceback:",
                traceback.format_exc(),
                "=" * 80,
            ]

            # Log the complete error information
            print("\n".join(error_log))

            await ctx.send(f"Error: {error_msg}")


@bot.command(name="clear", help="Clear your conversation history")
async def clear_memory(ctx):
    """Clear conversation history for the user."""
    if not container:
        await ctx.send("Bot is not fully initialized. Please try again in a moment.")
        return

    user_id = str(ctx.author.id)
    container.unified_memory_system.clear_messages(user_id)
    await ctx.send("Your conversation history has been cleared!")


# Helper functions
async def _handle_tool_calls(ctx: Context, tool_call: ToolUseBlock) -> None:
    user_id = str(ctx.author.id)
    party_id = str(ctx.guild.id) if ctx.guild else user_id
    if not container.tool_execution_service.requires_confirmation(tool_call.name):            
        result_message = container.tool_execution_service.execute_tool(
            tool_call.name, tool_call.input, user_id, party_id
        )
        await _send_reply(ctx, result_message)        
    else:        
        msg = container.tool_registry.generate_confirmation_message(tool_call.name, tool_call.input)
        sent_message = await _send_reply(ctx, msg)        

        # Add reaction buttons
        await sent_message.add_reaction("👍")
        await sent_message.add_reaction("👎")

        # Store pending confirmation
        container.reaction_handler.add_pending_confirmation(
            message_id=str(sent_message.id),
            user_id=str(ctx.author.id),
            party_id=party_id,
            action=tool_call.name,
            parameters=tool_call.input,
            channel_id=str(ctx.channel.id),
        )
async def _send_reply(ctx:Context, answer):
    print(f"Answer to user {ctx.author.id}: {answer}")
    if len(answer) > 2000:
        # Answer too long, send as file
        file = io.BytesIO(answer.encode("utf-8"))
        file.seek(0)
        return await ctx.send(file=discord.File(file, filename="answer.txt"))
    else:
        return await ctx.send(answer)

def _extract_answer(response) -> str | None:
    """
    Extract text answer from LLM response.

    Args:
        response: The LLM response message

    Returns:
        The text answer, or None if no text content found
    """
    text_blocks = [block for block in response.content if block.type == "text"]
    if text_blocks:
        return text_blocks[-1].text
    return None


if __name__ == "__main__":
    # Create container with all dependencies
    container = Container()
    
    DISCORD_TOKEN = container.config.discord_token
    if(not isstring(DISCORD_TOKEN)):
        print("ERROR: DISCORD_TOKEN not set")
        sys.exit(1)        

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\nBot stopped by user")

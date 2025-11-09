"""
Discord bot for Cyberpunk RED looter functionality.

This module implements the Discord bot interface using dependency injection
from the container to eliminate global state.
"""

import io
import json
import sys
import traceback
import discord
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from app_config import get_config_value
from bot_reactions import DiscordReactions
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

    # Create container with all dependencies
    container = Container()

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
    reactions_handler = _get_reactions_handler()
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

    # Get services from container
    conversation_service = container.conversation_service
    tool_execution_service = container.tool_execution_service
    reactions_handler = _get_reactions_handler()

    if not reactions_handler:
        await ctx.send("Bot is not fully initialized. Please try again in a moment.")
        return

    # Check and cleanup timeouts for this user
    await reactions_handler.check_and_cleanup_timeouts(user_id, bot)

    async with ctx.typing():
        try:
            # Process the query through the LLM
            tool_definitions = tool_execution_service.get_tool_definitions()
            response = conversation_service.process_query(
                user_id, party_id, question, tool_definitions
            )

            # Extract and handle tool calls
            tool_calls = tool_execution_service.extract_tool_calls(response)
            if tool_calls is not None and len(tool_calls) > 0:
                await _handle_tool_calls(ctx, tool_calls)
                return  # Exit after handling tool calls

            # Get the answer text from response
            answer = _extract_answer(response)
            if not answer:
                await ctx.send("I couldn't generate a response.")
                return

            # Send the answer
            print(f"Answer to user {user_id}: {answer}")
            if len(answer) > 2000:
                # Answer too long, send as file
                file = io.BytesIO(answer.encode("utf-8"))
                file.seek(0)
                await ctx.send(file=discord.File(file, filename="answer.txt"))
            else:
                await ctx.send(answer)

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

async def _handle_tool_calls(ctx: Context, tool_calls: list) -> None:
    user_id = str(ctx.author.id)
    party_id = str(ctx.guild.id) if ctx.guild else user_id
    tool_execution_service = container.tool_execution_service
    reactions_handler = _get_reactions_handler()
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_arguments = tool_call["arguments"]

        # Check if tool requires confirmation
        if not tool_execution_service.requires_confirmation(tool_name):
            # Execute the action directly
            if isinstance(tool_arguments, str):
                parameters = json.loads(tool_arguments)
            else:
                parameters = tool_arguments

            result_message = tool_execution_service.execute_tool(
                tool_name, parameters, user_id, party_id
            )
            await ctx.send(result_message)
            continue

        # Tool requires confirmation
        if isinstance(tool_arguments, str):
            parameters = json.loads(tool_arguments)
        else:
            parameters = tool_arguments

        # Send confirmation message
        confirmation_msg = tool_execution_service.generate_confirmation_message(
            tool_name, parameters
        )
        sent_message = await ctx.send(confirmation_msg)

        # Add reaction buttons
        await sent_message.add_reaction("👍")
        await sent_message.add_reaction("👎")

        # Store pending confirmation
        reactions_handler.add_pending_confirmation(
            message_id=str(sent_message.id),
            user_id=str(ctx.author.id),
            party_id=party_id,
            action=tool_name,
            parameters=parameters,
            channel_id=str(ctx.channel.id),
        )

def _get_reactions_handler() -> DiscordReactions:
    """
    Get the reactions handler from the container.

    Returns:
        DiscordReactions instance or None if not initialized
    """

    # Create reactions handler if it doesn't exist
    # Note: We'll need to add this to the container or create it here
    if not hasattr(container, '_reactions_handler'):
        handler = DiscordReactions(container.tool_execution_service)
        container._reactions_handler = handler

    return container.reactions_handler  # pyright: ignore[reportAttributeAccessIssue]


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
    # Get Discord token from environment
    try:
        DISCORD_TOKEN = get_config_value("DISCORD_BOT_TOKEN")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\nBot stopped by user")

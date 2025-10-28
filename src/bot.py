import io
import json
import sys
import traceback
import discord
import tool_system
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from memory_system import MemorySystem
from llm_service import LLMService
from app_config import get_config_value
from bot_reactions import DiscordReactions

load_dotenv()

DISCORD_TOKEN = get_config_value("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
llm_service: LLMService
memory_system = MemorySystem()
reactions: DiscordReactions


@bot.event
async def on_ready():
    global memory_system, llm_service, tool_system, reactions

    print(f"{bot.user} has connected to Discord!")

    print("Initializing LLM service...")
    llm_service = LLMService(memory_system)
    reactions = DiscordReactions(llm_service)
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
    if message_id not in reactions.pending_confirmations:
        return

    # Get confirmation
    confirmation = reactions.get_pending_confirmation(message_id)
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
    if reactions.is_timed_out(confirmation):
        await reactions.handle_timeout(message_id, confirmation, bot)
        return

    # Process based on reaction
    if str(reaction.emoji) == "👍":
        await reactions.handle_approval(
            reaction.message,
            confirmation,
        )
    elif str(reaction.emoji) == "👎":
        await reactions.handle_rejection(reaction.message, confirmation)


@bot.command(name="ai", help="Interact with the AI")
async def ask_question(ctx: Context, *, question: str):
    user_id = str(ctx.author.id)
    party_id = str(ctx.guild.id) if ctx.guild else user_id

    # Check and cleanup timeouts for this user
    await reactions.check_and_cleanup_timeouts(user_id, bot)

    async with ctx.typing():
        try:
            response = llm_service.process_query(user_id, party_id, question)
            tool_calls = llm_service.extract_tool_calls(response)
            if tool_calls is not None and len(tool_calls) > 0:
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_arguments = tool_call["arguments"]
                    if not tool_system.is_tool_confirmation_required(tool_name):
                        # Execute the action directly
                        result_message = llm_service.execute_tool_action(
                            tool_name, tool_arguments, user_id, party_id
                        )

                        await ctx.send(result_message)
                        continue

                    if isinstance(tool_arguments, str):
                        parameters = json.loads(tool_arguments)
                    else:
                        parameters = tool_arguments
                    sent_message = await ctx.send(
                        tool_system.generate_confirmation_message(tool_name, parameters)
                    )

                    # Add reactions
                    await sent_message.add_reaction("👍")
                    await sent_message.add_reaction("👎")

                    reactions.add_pending_confirmation(
                        message_id=str(sent_message.id),
                        user_id=ctx.author.id.__str__(),
                        party_id=party_id,
                        action=tool_name,
                        parameters=parameters,
                        channel_id=str(ctx.channel.id),
                    )
                return  # Exit after handling tool calls

            # Get the answer text
            answer = llm_service.get_answer(response)
            if not answer:
                await ctx.send("I couldn't generate a response.")
                return

            print(f"Answer to user {user_id}: {answer}")
            if len(answer) > 2000:
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
    if not memory_system:
        await ctx.send("Memory system not initialized.")
        return

    user_id = str(ctx.author.id)
    memory_system.clear_short_term(user_id)
    await ctx.send("Your conversation history has been cleared!")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
        sys.exit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("Bot stopped by user")

import time
import json
import discord
from discord.ext.commands import Context
from typing import Dict, List, Optional
from openai.types.responses import ToolParam, FunctionToolParam

# Global state for pending confirmations
pending_confirmations: Dict[str, Dict] = {}


def add_pending_confirmation(
    message_id: str,
    user_id: str,
    action: str,
    parameters: Dict,
    channel_id: Optional[str] = None,
) -> None:
    """Add a pending confirmation to the global state."""
    pending_confirmations[message_id] = {
        "user_id": user_id,
        "action": action,
        "parameters": parameters,
        "timestamp": time.time(),
        "processed": False,
        "channel_id": channel_id,
    }


def get_pending_confirmation(message_id: str) -> Optional[Dict]:
    """Get a pending confirmation by message ID."""
    return pending_confirmations.get(message_id)


def remove_pending_confirmation(message_id: str) -> None:
    """Remove a pending confirmation from the global state."""
    if message_id in pending_confirmations:
        del pending_confirmations[message_id]


def is_timed_out(confirmation: Dict, timeout_seconds: int = 60) -> bool:
    """Check if a confirmation has timed out."""
    current_time = time.time()
    return (current_time - confirmation["timestamp"]) > timeout_seconds


def get_tool_definitions() -> List[ToolParam]:
    """Get tool definitions for OpenAI-compatible API."""
    return [
        FunctionToolParam(
            {
                "type": "function",
                "name": "add_party_character",
                "description": "Add a new character to the party or update an existing character. Requires character name and role. Gear preferences are optional.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The character's name",
                        },
                        "role": {
                            "type": "string",
                            "description": "The character's role (e.g., Solo, Netrunner, Fixer, Rockerboy, etc.)",
                        },
                        "gear_preferences": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of gear types the character prefers (e.g., 'Assault Rifles', 'Body Armor', 'Cyberware')",
                        },
                    },
                    "required": ["name", "role"],
                },
                "strict": True,
            }
        ),
        FunctionToolParam(
            {
                "type": "function",
                "name": "remove_party_character",
                "description": "Remove a character from the party by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the character to remove",
                        }
                    },
                    "required": ["name"],
                },
                "strict": True,
            }
        ),
        FunctionToolParam(
            {
                "type": "function",
                "name": "view_party_members",
                "description": "View all current party members with their roles and gear preferences.",
                "parameters": {"type": "object", "properties": {}, "required": []},
                "strict": True,
            }
        ),
        FunctionToolParam(
            {
                "type": "function",
                "name": "recommend_gear",
                "description": "Get AI-powered gear distribution recommendations for party members based on loot description. Accepts natural language descriptions of loot items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "loot_description": {
                            "type": "string",
                            "description": "Natural language description of the loot to distribute (e.g., 'Assault Rifle, Body Armor, Neural Processor' or 'We got 2 SMGs from the ganger')",
                        },
                        "excluded_characters": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of character names to exclude from gear distribution",
                        },
                    },
                    "required": ["loot_description"],
                },
                "strict": True,
            }
        ),
    ]


def generate_confirmation_message(action: str, parameters: Dict) -> str:
    """Generate a confirmation message based on action and parameters."""
    if action == "add_party_character":
        name = parameters.get("name", "Unknown")
        role = parameters.get("role", "Unknown")
        gear_prefs = parameters.get("gear_preferences", [])

        gear_text = ", ".join(gear_prefs) if gear_prefs else "None"

        return f"""📋 **Confirmation Required**

I'll add **{name}** to your party:
• **Role:** {role}
• **Gear Preferences:** {gear_text}

👍 Confirm  👎 Cancel"""

    elif action == "remove_party_character":
        name = parameters.get("name", "Unknown")

        return f"""📋 **Confirmation Required**

I'll remove **{name}** from your party.

👍 Confirm  👎 Cancel"""

    elif action == "view_party_members":
        return """📋 **Confirmation Required**

I'll show you all party members.

👍 Confirm  👎 Cancel"""

    elif action == "recommend_gear":
        loot_desc = parameters.get("loot_description", "Unknown loot")
        excluded = parameters.get("excluded_characters", [])

        excluded_text = ""
        if excluded:
            excluded_text = f"\n• **Excluding:** {', '.join(excluded)}"

        return f"""📋 **Confirmation Required**

I'll recommend gear distribution for:
• **Loot:** {loot_desc}{excluded_text}

👍 Confirm  👎 Cancel"""

    else:
        return f"""📋 **Confirmation Required**

Action: {action}

👍 Confirm  👎 Cancel"""


def has_tool_calls(response) -> bool:
    """Check if API response contains tool calls."""
    try:
        # Check for tool_calls attribute in the response
        if hasattr(response, "tool_calls") and response.tool_calls:
            return True
        # Check in choices structure (OpenAI format)
        if hasattr(response, "choices") and response.choices:
            if hasattr(response.choices[0], "message") and hasattr(
                response.choices[0].message, "tool_calls"
            ):
                return (
                    response.choices[0].message.tool_calls is not None
                    and len(response.choices[0].message.tool_calls) > 0
                )
        return False
    except (AttributeError, IndexError):
        print("Error checking for tool calls in response.")
        return False


def extract_tool_calls(response) -> List[Dict]:
    """Extract tool calls from API response."""
    tool_calls = []
    try:
        # Try direct tool_calls attribute
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_calls.append(
                    {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    }
                )
        # Try choices structure (OpenAI format)
        elif hasattr(response, "choices") and response.choices:
            if hasattr(response.choices[0], "message") and hasattr(
                response.choices[0].message, "tool_calls"
            ):
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append(
                        {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        }
                    )
    except (AttributeError, IndexError):
        pass
    return tool_calls


async def handle_tool_calls(
    ctx: Context,
    response,
    user_id: str,
    openai_client,
    memory_system,
    graphrag_system,
    OPENAI_MODEL: str,
    bot,
) -> bool:
    """Handle tool calls from API response. Returns True if tool calls were handled."""
    # Check if response has tool calls
    if not has_tool_calls(response):
        return False

    # Extract tool calls
    tool_calls = extract_tool_calls(response)

    # Iterate through tool calls
    for tool_call in tool_calls:
        try:
            # Extract action name and parameters
            action = tool_call["name"]
            arguments_str = tool_call["arguments"]

            # Parse arguments (they come as JSON string)
            if isinstance(arguments_str, str):
                parameters = json.loads(arguments_str)
            else:
                parameters = arguments_str

            # Generate confirmation message
            confirmation_msg = generate_confirmation_message(action, parameters)

            # Send confirmation message to Discord
            sent_message = await ctx.send(confirmation_msg)

            # Add reactions
            await sent_message.add_reaction("👍")
            await sent_message.add_reaction("👎")

            # Store in pending confirmations
            add_pending_confirmation(
                message_id=str(sent_message.id),
                user_id=user_id,
                action=action,
                parameters=parameters,
                channel_id=str(ctx.channel.id),
            )

        except (KeyError, TypeError, json.JSONDecodeError) as e:
            # Log error and continue
            print(f"Error processing tool call: {e}")
            continue

    return True


async def handle_timeout(message_id: str, confirmation: Dict, bot) -> None:
    """Handle timeout for a confirmation."""
    try:
        # Get message object from Discord
        channel_id = confirmation.get("channel_id")
        if not channel_id:
            # If we don't have channel_id, we can't fetch the message
            remove_pending_confirmation(message_id)
            return

        channel = bot.get_channel(int(channel_id))
        if not channel:
            remove_pending_confirmation(message_id)
            return

        message = await channel.fetch_message(int(message_id))

        # Get original message content
        original_content = message.content

        # Apply strikethrough to all lines
        lines = original_content.split("\n")
        strikethrough_lines = [f"~~{line}~~" for line in lines]
        strikethrough_content = "\n".join(strikethrough_lines)

        # Append timeout message
        new_content = f"{strikethrough_content}\n\n⏱️ Request timed out"

        # Edit message
        await message.edit(content=new_content)

        # Remove from pending confirmations
        remove_pending_confirmation(message_id)

    except discord.NotFound:
        # Message was deleted
        remove_pending_confirmation(message_id)
    except Exception as e:
        print(f"Error handling timeout: {e}")
        remove_pending_confirmation(message_id)


async def check_and_cleanup_timeouts(user_id: str, bot) -> None:
    """Check and cleanup timed out confirmations for a user."""
    # Iterate through all pending confirmations
    for message_id, confirmation in list(pending_confirmations.items()):
        # Filter to those matching user_id
        if confirmation["user_id"] != user_id:
            continue

        # Check if timed out
        if is_timed_out(confirmation):
            # Handle timeout
            await handle_timeout(message_id, confirmation, bot)


async def execute_recommend_gear(
    user_id: str,
    loot_description: str,
    excluded_characters: List[str],
    memory_system,
    graphrag_system,
    openai_client,
    OPENAI_MODEL: str,
) -> str:
    """Execute gear recommendation and return the recommendation text."""
    game_context = "You have with access to a knowledge base about the RPG Cyberpunk RED. Be careful not to make up answers or to use information about the other Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020)."

    # Get all party members
    all_chars = memory_system.list_party_characters(user_id)

    # Handle empty party case
    if not all_chars:
        return "You don't have any party members registered yet. Please add party members first."

    # Filter out excluded characters
    if excluded_characters:
        excluded_lower = [name.lower() for name in excluded_characters]
        all_chars = [
            char for char in all_chars if char["name"].lower() not in excluded_lower
        ]

    if not all_chars:
        return "No party members available after exclusions."

    # Get GraphRAG context
    context_prompt = f"""Look up information related to this gear: {loot_description}"""
    context = graphrag_system.get_context_for_query(context_prompt, k=10)

    # Get previous response ID
    previous_response_id = memory_system.get_last_response_id(user_id)

    # Build party context for the LLM
    party_context = "Party Members:\n"
    for char in all_chars:
        party_context += f"- {char['name']} ({char['role']})"
        if char.get("gear_preferences"):
            party_context += f" - Prefers: {', '.join(char['gear_preferences'])}"
        party_context += "\n"

    # Create the user prompt
    user_prompt = f"""Please help distribute this loot among my party members.
{game_context}

Party Context:
{party_context}

Loot Description:
{loot_description}

Use the knowledge base context, if needed, to inform your recommendation:
{context}

Parse the loot description to identify individual items, then recommend how to distribute them among the party members. Consider:
1. Character roles and their typical gear needs
2. Each character's stated gear preferences
3. Fair distribution when preferences conflict
4. Overall party effectiveness
5. The market value of the item if no clear preference can be determined

Provide your recommendations in this format:
**[Character Name]** ([Role])
  - [Item 1]
  - [Item 2]
  ..."""

    # Build the input based on whether we have a previous conversation
    if previous_response_id:
        # Continue existing conversation - only send new message
        input_messages = [{"role": "user", "content": user_prompt}]
        api_params = {
            "model": OPENAI_MODEL,
            "previous_response_id": previous_response_id,
            "input": input_messages,
            "temperature": 0.7,
        }
    else:
        # Start new conversation - include system prompt
        system_prompt = "You are a knowledgeable game master who helps parties distribute loot fairly and strategically with access to a knowledge base about the RPG Cyberpunk RED. Be careful not to make up answers or to use information about the other Cyberpunk games (like Cyberpunk 2077 or Cyberpunk 2020) unless it is explicitly in the knowledge base."
        input_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        api_params = {
            "model": OPENAI_MODEL,
            "input": input_messages,
            "temperature": 0.7,
        }

    try:
        response = openai_client.responses.create(**api_params)  # type: ignore[arg-type]

        # Save the response ID for future continuations
        memory_system.set_last_response_id(user_id, response.id)

        recommendation = response.output_text
        if not recommendation:
            recommendation = "I couldn't generate recommendations."

        return recommendation

    except Exception as e:
        error_msg = str(e)
        # Check if the error is due to an invalid/expired response ID
        if previous_response_id and (
            "response" in error_msg.lower() or "not found" in error_msg.lower()
        ):
            # Clear the invalid response ID
            memory_system.set_last_response_id(user_id, "")
            return "Previous conversation expired. Please try again."
        else:
            return f"Error generating recommendations: {error_msg}"


async def execute_tool_action(
    action: str,
    parameters: Dict,
    user_id: str,
    memory_system,
    graphrag_system,
    openai_client,
    OPENAI_MODEL: str,
) -> tuple[bool, str]:
    """Execute a tool action and return (success, message)."""
    try:
        if action == "add_party_character":
            # Extract parameters
            name = parameters.get("name", "")
            role = parameters.get("role", "")
            gear_preferences = parameters.get("gear_preferences", [])

            # Call memory_system method
            is_new = memory_system.add_party_character(
                user_id, name, role, gear_preferences
            )

            # Generate success message
            if is_new:
                msg = f"✓ **{name}** has been added to your party!"
            else:
                msg = f"✓ **{name}** has been updated in your party!"

            return (True, msg)

        elif action == "remove_party_character":
            # Extract parameters
            name = parameters.get("name", "")

            # Call memory_system method
            success = memory_system.remove_party_character(user_id, name)

            # Generate message based on result
            if success:
                msg = f"✓ **{name}** has been removed from your party."
                return (True, msg)
            else:
                msg = f"Character **{name}** not found in your party."
                return (False, msg)

        elif action == "view_party_members":
            # Call memory_system method
            characters = memory_system.list_party_characters(user_id)

            # Format result
            if not characters:
                msg = "You don't have any party members yet."
                return (True, msg)

            msg = "**Your Party Members:**\n\n"
            for char in characters:
                msg += f"**{char['name']}**\n"
                msg += f"• Role: {char['role']}\n"
                if char.get("gear_preferences"):
                    msg += (
                        f"• Gear Preferences: {', '.join(char['gear_preferences'])}\n"
                    )
                else:
                    msg += "• Gear Preferences: None\n"
                msg += "\n"

            return (True, msg)

        elif action == "recommend_gear":
            # Extract parameters
            loot_description = parameters.get("loot_description", "")
            excluded_characters = parameters.get("excluded_characters", [])

            # Call execute_recommend_gear
            recommendation = await execute_recommend_gear(
                user_id,
                loot_description,
                excluded_characters,
                memory_system,
                graphrag_system,
                openai_client,
                OPENAI_MODEL,
            )

            return (True, recommendation)

        else:
            return (False, f"Unknown action: {action}")

    except Exception as e:
        return (False, f"Error executing action: {str(e)}")


async def handle_approval(
    message: discord.Message,
    confirmation: Dict,
    memory_system,
    graphrag_system,
    openai_client,
    OPENAI_MODEL: str,
    bot,
) -> None:
    """Handle approval of a confirmation."""
    try:
        # Mark confirmation as processed
        confirmation["processed"] = True

        # Extract action and parameters
        action = confirmation["action"]
        parameters = confirmation["parameters"]
        user_id = confirmation["user_id"]

        # Call execute_tool_action
        success, result_message = await execute_tool_action(
            action,
            parameters,
            user_id,
            memory_system,
            graphrag_system,
            openai_client,
            OPENAI_MODEL,
        )

        # Send success message as reply
        await message.reply(result_message)

        # Remove from pending confirmations
        remove_pending_confirmation(str(message.id))

    except Exception as e:
        # Send error message
        await message.reply(f"Error executing action: {str(e)}")
        # Remove from pending confirmations
        remove_pending_confirmation(str(message.id))


async def handle_rejection(message: discord.Message, confirmation: Dict) -> None:
    """Handle rejection of a confirmation."""
    # Mark confirmation as processed
    confirmation["processed"] = True

    # Extract action and parameters
    action = confirmation["action"]
    parameters = confirmation["parameters"]

    # Generate cancellation message based on action
    if action == "add_party_character":
        name = parameters.get("name", "Unknown")
        cancel_msg = f"Cancelled adding **{name}** to your party."
    elif action == "remove_party_character":
        name = parameters.get("name", "Unknown")
        cancel_msg = f"Cancelled removing **{name}** from your party."
    elif action == "view_party_members":
        cancel_msg = "Cancelled viewing party members."
    elif action == "recommend_gear":
        cancel_msg = "Cancelled gear recommendation."
    else:
        cancel_msg = f"Cancelled {action}."

    # Send cancellation message as reply
    await message.reply(cancel_msg)

    # Remove from pending confirmations
    remove_pending_confirmation(str(message.id))

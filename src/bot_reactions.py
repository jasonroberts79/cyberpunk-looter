import time
import discord
from typing import Dict, Optional
from llm_service import LLMService


class DiscordReactions:
    def __init__(self, llm_service: LLMService) -> None:
        self.pending_confirmations: Dict[str, Dict] = {}
        self.llm_service = llm_service

    async def handle_approval(
        self, message: discord.Message, confirmation: Dict
    ) -> None:
        """Handle approval of a confirmation."""
        try:
            # Mark confirmation as processed
            confirmation["processed"] = True

            # Extract action and parameters
            action = confirmation["action"]
            parameters = confirmation["parameters"]
            user_id = confirmation["user_id"]

            # Use LLM service to execute tool action
            if not self.llm_service:
                raise ValueError("LLM service is required for tool execution")

            result_message = self.llm_service.execute_tool_action(
                action, parameters, user_id
            )

            # Send success message as reply
            await message.reply(result_message)

            # Remove from pending confirmations
            self.remove_pending_confirmation(str(message.id))

        except Exception as e:
            # Send error message
            await message.reply(f"Error executing action: {str(e)}")
            # Remove from pending confirmations
            self.remove_pending_confirmation(str(message.id))

    async def handle_rejection(
        self, message: discord.Message, confirmation: Dict
    ) -> None:
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
        self.remove_pending_confirmation(str(message.id))

    def add_pending_confirmation(
        self,
        message_id: str,
        user_id: str,
        action: str,
        parameters: Dict,
        channel_id: Optional[str] = None,
    ) -> None:
        """Add a pending confirmation to the state."""
        self.pending_confirmations[message_id] = {
            "user_id": user_id,
            "action": action,
            "parameters": parameters,
            "timestamp": time.time(),
            "processed": False,
            "channel_id": channel_id,
        }

    def get_pending_confirmation(self, message_id: str) -> Optional[Dict]:
        """Get a pending confirmation by message ID."""
        return self.pending_confirmations.get(message_id)

    def remove_pending_confirmation(self, message_id: str) -> None:
        """Remove a pending confirmation from the state."""
        if message_id in self.pending_confirmations:
            del self.pending_confirmations[message_id]

    async def check_and_cleanup_timeouts(self, user_id: str, bot) -> None:
        """Check and cleanup timed out confirmations for a user."""
        # Iterate through all pending confirmations
        for message_id, confirmation in list(self.pending_confirmations.items()):
            # Filter to those matching user_id
            if confirmation["user_id"] != user_id:
                continue

            # Check if timed out
            if self.is_timed_out(confirmation):
                # Handle timeout
                await self.handle_timeout(message_id, confirmation, bot)

    def is_timed_out(self, confirmation: Dict, timeout_seconds: int = 60) -> bool:
        """Check if a confirmation has timed out."""
        current_time = time.time()
        return (current_time - confirmation["timestamp"]) > timeout_seconds

    async def handle_timeout(self, message_id: str, confirmation: Dict, bot) -> None:
        """Handle timeout for a confirmation."""
        try:
            # Get message object from Discord
            channel_id = confirmation.get("channel_id")
            if not channel_id:
                # If we don't have channel_id, we can't fetch the message
                self.remove_pending_confirmation(message_id)
                return

            channel = bot.get_channel(int(channel_id))
            if not channel:
                self.remove_pending_confirmation(message_id)
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
            self.remove_pending_confirmation(message_id)

        except discord.NotFound:
            # Message was deleted
            self.remove_pending_confirmation(message_id)
        except Exception as e:
            print(f"Error handling timeout: {e}")
            self.remove_pending_confirmation(message_id)

"""
Discord reaction handler for tool confirmations.

This module handles user confirmations and rejections for tool actions
via Discord reactions (emoji).
"""

import time
import discord
from typing import Dict, Optional
from models import PendingConfirmation
from config import DiscordBotConfig
from tool_execution_service import ToolExecutionService


class DiscordReactions:
    """
    Handles Discord reactions for tool action confirmations.

    This class manages pending confirmations, timeouts, and user approval/rejection
    of tool actions through Discord reaction buttons.
    """

    def __init__(
        self,
        tool_execution_service: ToolExecutionService,
        config: DiscordBotConfig = DiscordBotConfig()
    ) -> None:
        """
        Initialize the Discord reactions handler.

        Args:
            tool_execution_service: Service for executing tool actions
            config: Discord bot configuration settings
        """
        self.pending_confirmations: Dict[str, PendingConfirmation] = {}
        self.tool_execution_service = tool_execution_service
        self.config = config

    async def handle_approval(
        self,
        message: discord.Message,
        confirmation: PendingConfirmation | Dict
    ) -> None:
        """
        Handle approval of a tool action confirmation.

        Args:
            message: The Discord message containing the confirmation
            confirmation: The pending confirmation (dataclass or dict for compatibility)
        """
        try:
            # Handle both dict and dataclass for backward compatibility
            if isinstance(confirmation, dict):
                action = confirmation["action"]
                parameters = confirmation["parameters"]
                user_id = confirmation["user_id"]
                party_id = confirmation["party_id"]
                confirmation["processed"] = True
            else:
                action = confirmation.action
                parameters = confirmation.parameters
                user_id = confirmation.user_id
                party_id = confirmation.party_id
                confirmation.processed = True

            # Execute the tool action
            result_message = self.tool_execution_service.execute_tool(
                tool_name=action,
                arguments=parameters,
                user_id=user_id,
                party_id=party_id
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
        self,
        message: discord.Message,
        confirmation: PendingConfirmation | Dict
    ) -> None:
        """
        Handle rejection of a tool action confirmation.

        Args:
            message: The Discord message containing the confirmation
            confirmation: The pending confirmation (dataclass or dict for compatibility)
        """
        # Handle both dict and dataclass for backward compatibility
        if isinstance(confirmation, dict):
            action = confirmation["action"]            
            confirmation["processed"] = True
        else:
            action = confirmation.action            
            confirmation.processed = True

        # Generate cancellation message based on action
        if action == "add_party_character":            
            cancel_msg = "Cancelled adding character to your party."
        elif action == "remove_party_character":            
            cancel_msg = "Cancelled removing character from your party."
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
        party_id: str,
        action: str,
        parameters: object,
        channel_id: Optional[str] = None,
    ) -> None:
        """
        Add a pending confirmation to the state.

        Args:
            message_id: Discord message ID for the confirmation
            user_id: User who initiated the action
            party_id: Party context for the action
            action: Tool action name
            parameters: Tool parameters
            channel_id: Optional Discord channel ID
        """
        confirmation = PendingConfirmation(
            user_id=user_id,
            party_id=party_id,
            action=action,
            parameters=parameters,
            timestamp=time.time(),
            processed=False,
            channel_id=channel_id,
            message_id=message_id
        )
        self.pending_confirmations[message_id] = confirmation

    def get_pending_confirmation(
        self,
        message_id: str
    ) -> Optional[PendingConfirmation]:
        """
        Get a pending confirmation by message ID.

        Args:
            message_id: Discord message ID

        Returns:
            PendingConfirmation object or None if not found
        """
        return self.pending_confirmations.get(message_id)

    def remove_pending_confirmation(self, message_id: str) -> None:
        """Remove a pending confirmation from the state."""
        if message_id in self.pending_confirmations:
            del self.pending_confirmations[message_id]

    async def check_and_cleanup_timeouts(self, user_id: str, bot) -> None:
        """
        Check and cleanup timed out confirmations for a user.

        Args:
            user_id: The user ID to check timeouts for
            bot: The Discord bot instance
        """
        # Iterate through all pending confirmations
        work_list = list(self.pending_confirmations.items())
        for message_id, confirmation in work_list:
            # Filter to those matching user_id
            if confirmation.user_id != user_id:
                continue

            # Check if timed out
            if self.is_timed_out(confirmation):
                # Handle timeout
                await self.handle_timeout(message_id, confirmation, bot)

    def is_timed_out(
        self,
        confirmation: PendingConfirmation,
        timeout_seconds: int | None = None
    ) -> bool:
        """
        Check if a confirmation has timed out.

        Args:
            confirmation: The pending confirmation
            timeout_seconds: Timeout duration in seconds (uses config if not provided)

        Returns:
            True if timed out, False otherwise
        """
        if timeout_seconds is None:
            timeout_seconds = self.config.confirmation_timeout_seconds

        current_time = time.time()
        return (current_time - confirmation.timestamp) > timeout_seconds

    async def handle_timeout(
        self,
        message_id: str,
        confirmation: PendingConfirmation,
        bot
    ) -> None:
        """
        Handle timeout for a confirmation.

        Args:
            message_id: Discord message ID
            confirmation: The timed out confirmation
            bot: The Discord bot instance
        """
        try:
            # Get message object from Discord
            channel_id = confirmation.channel_id
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

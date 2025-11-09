"""
Conversation memory for managing short-term message history.

This module handles short-term conversation history for users,
implementing the MemoryProvider protocol.
"""

from typing import Dict, List
from collections import defaultdict
from models import ConversationMessage
from config import MemoryConfig


class ConversationMemory:
    """
    Manages short-term conversation history for users.

    This class is responsible for storing and retrieving recent
    conversation messages, with automatic trimming to limit memory usage.
    """

    def __init__(self, config: MemoryConfig = MemoryConfig()) -> None:
        """
        Initialize conversation memory.

        Args:
            config: Memory configuration settings
        """
        self.config = config
        self.conversations: Dict[str, List[ConversationMessage]] = defaultdict(list)

    def add_message(
        self,
        user_id: str,
        role: str,
        content: str | None
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            user_id: The user identifier
            role: The message role (user/assistant)
            content: The message content (may be None for tool calls)
        """
        if content is None:
            # Don't store messages with no content
            return

        message = ConversationMessage(role=role, content=content)
        self.conversations[user_id].append(message)

        # Trim history if it exceeds the limit
        self._trim_history(user_id)

    def get_messages(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        messages = self.conversations.get(user_id, [])
        return [msg.to_dict() for msg in messages]

    def get_recent_messages(
        self,
        user_id: str,
        max_messages: int | None = None
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation messages for a user.

        Args:
            user_id: The user identifier
            max_messages: Maximum number of messages to return
                         (defaults to config value)

        Returns:
            List of recent message dictionaries
        """
        if max_messages is None:
            max_messages = self.config.max_short_term_messages

        messages = self.conversations.get(user_id, [])
        recent = messages[-max_messages:] if messages else []
        return [msg.to_dict() for msg in recent]

    def clear_messages(self, user_id: str) -> None:
        """
        Clear conversation history for a user.

        Args:
            user_id: The user identifier
        """
        if user_id in self.conversations:
            del self.conversations[user_id]

    def _trim_history(self, user_id: str) -> None:
        """
        Trim conversation history to maximum size.

        Args:
            user_id: The user identifier
        """
        messages = self.conversations[user_id]
        max_messages = self.config.max_short_term_messages

        if len(messages) > max_messages:
            # Keep only the most recent messages
            self.conversations[user_id] = messages[-max_messages:]

    def get_message_count(self, user_id: str) -> int:
        """
        Get the number of messages for a user.

        Args:
            user_id: The user identifier

        Returns:
            Number of stored messages
        """
        return len(self.conversations.get(user_id, []))

    def has_conversation(self, user_id: str) -> bool:
        """
        Check if a user has any conversation history.

        Args:
            user_id: The user identifier

        Returns:
            True if the user has messages, False otherwise
        """
        return user_id in self.conversations and len(self.conversations[user_id]) > 0

"""
Message builder for constructing LLM conversation messages.

This module is responsible for building message arrays from conversation
history and new user input, ready to send to the LLM API.
"""

from typing import List, Dict, Any
from anthropic.types import MessageParam
from config import MemoryConfig


class MessageBuilder:
    """Builds message arrays for LLM API calls from conversation history."""

    def __init__(
        self,
        memory_provider: Any,  # ConversationMemory or UnifiedMemorySystem
        config: MemoryConfig = MemoryConfig()
    ) -> None:
        """
        Initialize the message builder.

        Args:
            memory_provider: Provider for accessing conversation history
            config: Memory configuration settings
        """
        self.memory_provider = memory_provider
        self.config = config

    def build_messages(
        self,
        user_prompt: str,
        user_id: str,
        max_messages: int | None = None
    ) -> List[MessageParam]:
        """
        Build a message array from conversation history and new user input.

        Args:
            user_prompt: The new user message to add
            user_id: The user identifier for retrieving history
            max_messages: Maximum number of historical messages to include
                         (defaults to config value)

        Returns:
            List of message dictionaries ready for LLM API
        """
        if max_messages is None:
            max_messages = self.config.max_short_term_messages

        # Get conversation history
        short_term_context = self.memory_provider.get_messages(user_id)

        # Build message array
        input_messages = []

        if short_term_context:
            # Convert stored messages to API format
            for m in short_term_context[-max_messages:]:
                if m.get("content") is not None:
                    input_messages.append(
                        {"role": m["role"], "content": m["content"]}
                    )

        # Add the new user message
        input_messages.append({"role": "user", "content": user_prompt})

        return input_messages

    def build_messages_with_context(
        self,
        user_prompt: str,
        user_id: str,
        additional_context: str | None = None
    ) -> List[MessageParam]:
        """
        Build messages with optional additional context prepended.

        Useful for adding system-level context or instructions
        directly into the conversation flow.

        Args:
            user_prompt: The new user message
            user_id: The user identifier
            additional_context: Optional context to prepend to user prompt

        Returns:
            List of message dictionaries ready for LLM API
        """
        if additional_context:
            enhanced_prompt = f"{additional_context}\n\n{user_prompt}"
        else:
            enhanced_prompt = user_prompt

        return self.build_messages(enhanced_prompt, user_id)

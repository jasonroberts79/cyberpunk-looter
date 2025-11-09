"""
Unified memory system that implements the MemoryProvider protocol.

This facade delegates to the specialized memory components while
providing a unified interface for backward compatibility.
"""

from typing import Dict, List, Optional, Any
from conversation_memory import ConversationMemory
from user_memory_repository import UserMemoryRepository
from config import MemoryConfig


class UnifiedMemorySystem:
    """
    Unified memory system implementing the MemoryProvider protocol.

    This class acts as a facade over the specialized memory components,
    providing a single interface for all memory operations.
    """

    def __init__(
        self,
        conversation_memory: ConversationMemory,
        user_memory_repository: UserMemoryRepository,
        config: MemoryConfig = MemoryConfig()
    ) -> None:
        """
        Initialize the unified memory system.

        Args:
            conversation_memory: Short-term conversation memory
            user_memory_repository: Long-term user memory repository
            config: Memory configuration
        """
        self.conversation_memory = conversation_memory
        self.user_memory_repository = user_memory_repository
        self.config = config

    def add_message(self, user_id: str, role: str, content: Optional[str]) -> None:
        """Add a message to short-term memory."""
        self.conversation_memory.add_message(user_id, role, content)

    def get_messages(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user."""
        return self.conversation_memory.get_messages(user_id)

    def clear_messages(self, user_id: str) -> None:
        """Clear conversation history for a user."""
        self.conversation_memory.clear_messages(user_id)

    def update_long_term(
        self, user_id: str, key: str, value: Any, category: Optional[str] = None
    ) -> None:
        """Update long-term memory for a user."""
        self.user_memory_repository.update_long_term(user_id, key, value, category)

    def get_long_term_summary(self, user_id: str) -> str:
        """Get a summary of long-term memory for a user."""
        return self.user_memory_repository.get_long_term_summary(user_id)

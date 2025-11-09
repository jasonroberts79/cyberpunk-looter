"""
User memory repository for managing long-term user data.

This module handles persistent storage of user preferences,
interaction history, and topics discussed.
"""

import json
from typing import Dict, Optional, Any
from datetime import datetime
from interfaces import Storage
from models import UserMemory
from config import MemoryConfig


class UserMemoryRepository:
    """
    Repository for managing long-term user memory.

    This class handles persistence of user preferences, interaction
    counts, and topics discussed across sessions.
    """

    def __init__(
        self,
        storage: Storage,
        config: MemoryConfig = MemoryConfig()
    ) -> None:
        """
        Initialize the user memory repository.

        Args:
            storage: Storage backend for persistence
            config: Memory configuration settings
        """
        self.storage = storage
        self.config = config
        self.user_memories: Dict[str, UserMemory] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load user memory data from storage."""
        try:
            data_str = self.storage.read_data(self.config.long_term_storage_file)
            if data_str:
                data = json.loads(data_str)
                self.user_memories = {
                    user_id: UserMemory.from_dict(user_id, user_data)
                    for user_id, user_data in data.items()
                }
                print(f"Loaded long-term memory for {len(self.user_memories)} users")
            else:
                self.user_memories = {}
        except Exception as e:
            print(f"Error loading long-term memory: {e}")
            self.user_memories = {}

    def _save_data(self) -> None:
        """Save user memory data to storage."""
        try:
            data = {
                user_id: memory.to_dict()
                for user_id, memory in self.user_memories.items()
            }
            data_str = json.dumps(data, indent=2)
            self.storage.write_data(self.config.long_term_storage_file, data_str)
        except Exception as e:
            print(f"Error saving long-term memory: {e}")

    def record_interaction(self, user_id: str) -> None:
        """
        Record a user interaction.

        Args:
            user_id: The user identifier
        """
        memory = self._ensure_user_memory(user_id)
        timestamp = datetime.now().isoformat()
        memory.interactions.append(f"Interaction at {timestamp}")
        self._save_data()

    def add_preference(self, user_id: str, preference: str) -> None:
        """
        Add a user preference.

        Args:
            user_id: The user identifier
            preference: The preference to record
        """
        memory = self._ensure_user_memory(user_id)
        if preference not in memory.preferences:
            memory.preferences.append(preference)
            self._save_data()

    def add_topic(self, user_id: str, topic: str) -> None:
        """
        Add a topic discussed with the user.

        Args:
            user_id: The user identifier
            topic: The topic to record
        """
        memory = self._ensure_user_memory(user_id)
        if topic not in memory.topics:
            memory.topics.append(topic)
            self._save_data()

    def update_long_term(
        self,
        user_id: str,
        key: str,
        value: Any,
        category: Optional[str] = None
    ) -> None:
        """
        Update long-term memory for a user.

        This method maintains compatibility with the old interface.

        Args:
            user_id: The user identifier
            key: The memory key (interaction, preference, topic)
            value: The value to store
            category: Optional category (unused, for compatibility)
        """
        if key == "interaction":
            self.record_interaction(user_id)
        elif key == "preference":
            if isinstance(value, dict):
                for pref_key, pref_value in value.items():
                    self.add_preference(user_id, f"{pref_key}: {pref_value}")
            else:
                self.add_preference(user_id, str(value))
        elif key == "topic":
            self.add_topic(user_id, str(value))

    def get_long_term_summary(self, user_id: str) -> str:
        """
        Get a formatted summary of long-term memory for a user.

        Args:
            user_id: The user identifier

        Returns:
            Formatted summary string for LLM context
        """
        memory = self.user_memories.get(user_id)

        if not memory:
            return "This is our first conversation."

        summary_parts = []

        if memory.interactions:
            summary_parts.append(
                f"We've interacted {len(memory.interactions)} times."
            )

        if memory.preferences:
            prefs = ", ".join(memory.preferences[-5:])  # Last 5 preferences
            summary_parts.append(f"Your preferences: {prefs}")

        if memory.topics:
            topics = ", ".join(memory.topics[-5:])  # Last 5 topics
            summary_parts.append(f"Topics we've discussed: {topics}")

        return " ".join(summary_parts) if summary_parts else "This is our first conversation."

    def get_user_memory(self, user_id: str) -> Optional[UserMemory]:
        """
        Get the full user memory object.

        Args:
            user_id: The user identifier

        Returns:
            UserMemory object or None if not found
        """
        return self.user_memories.get(user_id)

    def _ensure_user_memory(self, user_id: str) -> UserMemory:
        """
        Ensure a user memory exists, creating if necessary.

        Args:
            user_id: The user identifier

        Returns:
            The UserMemory object for this user
        """
        if user_id not in self.user_memories:
            self.user_memories[user_id] = UserMemory(user_id=user_id)
        return self.user_memories[user_id]

    def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all long-term memory for a user.

        Args:
            user_id: The user identifier

        Returns:
            True if memory was cleared, False if user had no memory
        """
        if user_id in self.user_memories:
            del self.user_memories[user_id]
            self._save_data()
            return True
        return False

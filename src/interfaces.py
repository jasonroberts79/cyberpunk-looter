"""
Protocol interfaces for dependency injection and abstraction.

This module defines the contracts that concrete implementations must follow,
enabling loose coupling and easier testing throughout the codebase.
"""

from typing import Protocol, Optional, Dict, List, Any
from anthropic.types import Message


class Storage(Protocol):
    """Abstract storage interface for persistence operations."""

    def write_data(self, filename: str, data: str) -> None:
        """
        Write data to storage.

        Args:
            filename: The name/path of the file to write
            data: The string data to write
        """
        ...

    def read_data(self, filename: str) -> Optional[str]:
        """
        Read data from storage.

        Args:
            filename: The name/path of the file to read

        Returns:
            The file contents as a string, or None if file doesn't exist
        """
        ...


class MemoryProvider(Protocol):
    """Abstract interface for memory operations."""

    def add_message(self, user_id: str, role: str, content: Optional[str]) -> None:
        """
        Add a message to short-term memory.

        Args:
            user_id: The user identifier
            role: The message role (user/assistant)
            content: The message content
        """
        ...

    def get_messages(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        ...

    def clear_messages(self, user_id: str) -> None:
        """
        Clear conversation history for a user.

        Args:
            user_id: The user identifier
        """
        ...

    def update_long_term(
        self, user_id: str, key: str, value: str, category: Optional[str] = None
    ) -> None:
        """
        Update long-term memory for a user.

        Args:
            user_id: The user identifier
            key: The memory key
            value: The memory value
            category: Optional category for organization
        """
        ...

    def get_long_term_summary(self, user_id: str) -> str:
        """
        Get a summary of long-term memory for a user.

        Args:
            user_id: The user identifier

        Returns:
            Formatted summary string
        """
        ...


class PartyRepository(Protocol):
    """Abstract interface for party data operations."""

    def add_party_character(
        self,
        party_id: str,
        name: str,
        role: str,
        gear_preferences: Optional[List[str]] = None
    ) -> bool:
        """
        Add or update a character in a party.

        Args:
            party_id: The party identifier
            name: Character name
            role: Character role/class
            gear_preferences: Optional list of preferred gear types

        Returns:
            True if new character added, False if existing character updated
        """
        ...

    def remove_party_character(self, party_id: str, name: str) -> bool:
        """
        Remove a character from a party.

        Args:
            party_id: The party identifier
            name: Character name to remove

        Returns:
            True if character was removed, False if not found
        """
        ...

    def get_party_summary(self, party_id: str) -> str:
        """
        Get a formatted summary of party members.

        Args:
            party_id: The party identifier

        Returns:
            Formatted party summary string
        """
        ...

    def get_party_characters(self, party_id: str) -> List[Dict[str, Any]]:
        """
        Get all characters in a party.

        Args:
            party_id: The party identifier

        Returns:
            List of character dictionaries
        """
        ...


class ContextProvider(Protocol):
    """Abstract interface for RAG context retrieval."""

    def get_relevant_context(
        self, query: str, user_id: str, party_id: str, k: int = 10
    ) -> str:
        """
        Get relevant context for a query using RAG.

        Args:
            query: The user's query
            user_id: The user identifier
            party_id: The party identifier
            k: Number of relevant documents to retrieve

        Returns:
            Formatted context string
        """
        ...

    async def build_knowledge_graph(
        self, directory: str, force_rebuild: bool = False
    ) -> None:
        """
        Build or update the knowledge graph from documents.

        Args:
            directory: Directory containing source documents
            force_rebuild: Whether to force a complete rebuild
        """
        ...


class ToolExecutor(Protocol):
    """Abstract interface for tool execution."""

    def execute_tool_action(
        self, action: str, parameters: Dict[str, Any], user_id: str, party_id: str
    ) -> str:
        """
        Execute a tool action with given parameters.

        Args:
            action: The tool action name
            parameters: Tool parameters
            user_id: The user identifier
            party_id: The party identifier

        Returns:
            Result message from tool execution
        """
        ...


class LLMClient(Protocol):
    """Abstract interface for LLM interactions."""

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Any]] = None,
        max_tokens: int = 20000,
        temperature: float = 0.6
    ) -> Message:
        """
        Create a message using the LLM.

        Args:
            messages: Conversation history
            system: System prompt
            tools: Optional tool definitions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLM response message
        """
        ...

    def process_query(
        self, user_id: str, party_id: str, question: str
    ) -> Message:
        """
        Process a user query end-to-end.

        Args:
            user_id: The user identifier
            party_id: The party identifier
            question: The user's question

        Returns:
            LLM response message
        """
        ...

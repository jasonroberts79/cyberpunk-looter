"""
Base classes and interfaces for tool handlers.

This module defines the abstract base class for all tool handlers,
implementing the Strategy pattern for tool execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from anthropic.types import ToolParam
from pydantic import BaseModel


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    """Whether the tool executed successfully."""

    message: str
    """The result message to return to the user."""

    should_update_memory: bool = True
    """Whether this result should be added to conversation memory."""

    metadata: Dict[str, Any] | None = None
    """Optional metadata about the execution."""


class ToolHandler(ABC):
    """
    Abstract base class for tool handlers.

    Each tool should implement this interface to provide its own
    execution logic while maintaining a consistent interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The unique name of this tool.

        This should match the tool name in the tool definition.
        """
        ...

    @property
    @abstractmethod
    def requires_confirmation(self) -> bool:
        """
        Whether this tool requires user confirmation before execution.

        Returns:
            True if user must confirm, False if tool can execute immediately
        """
        ...

    @abstractmethod
    def get_tool_definition(self) -> ToolParam:
        """
        Get the tool definition for the LLM API.

        Returns:
            Tool definition in the format expected by the LLM API
        """
        ...

    @abstractmethod
    def execute(
        self,
        arguments: Dict[str, Any],
        user_id: str,
        party_id: str
    ) -> ToolExecutionResult:
        """
        Execute the tool with the given arguments.

        Args:
            arguments: Tool-specific parameters from the LLM
            user_id: The user identifier
            party_id: The party identifier

        Returns:
            The result of the tool execution
        """
        ...

    def generate_confirmation_message(
        self,
        input: object
    ) -> str:
        """
        Generate a confirmation message for user approval.

        This method should be overridden by tools that require confirmation.

        Args:
            arguments: The tool arguments to confirm

        Returns:
            A human-readable confirmation message
        """
        return f"Confirm execution of {self.name}?"

    @abstractmethod
    def parse_input(
        self,
        input: object
    ) -> dict[str, Any] | ToolExecutionResult:
        ...


class ContextRetrievingToolHandler(ToolHandler):
    """
    Base class for tools that need to retrieve context from the knowledge graph.

    Provides common functionality for RAG-based tools.
    """

    def __init__(self, context_provider: Any) -> None:
        """
        Initialize with a context provider.

        Args:
            context_provider: Provider for retrieving context from knowledge graph
        """
        self.context_provider = context_provider

    def get_context(self, query: str, k: int = 10) -> str:
        """
        Retrieve relevant context for a query.

        Args:
            query: The query to search for
            k: Number of relevant documents to retrieve

        Returns:
            Formatted context string
        """
        if hasattr(self.context_provider, 'get_context_for_query'):
            return self.context_provider.get_context_for_query(query, k=k)
        return ""

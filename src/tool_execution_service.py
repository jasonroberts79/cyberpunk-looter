"""
Tool execution service for handling tool invocations.

This module provides a clean interface for executing tools using
the registry pattern, replacing the previous if/elif chain approach.
"""

from typing import Dict, Any, Optional
import json
from anthropic.types import Message
from tools.registry import ToolRegistry
from tools.base import ToolExecutionResult
from interfaces import MemoryProvider


class ToolExecutionService:
    """
    Service for executing tools through a registry.

    This class delegates tool execution to registered handlers,
    following the Open/Closed Principle.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        memory_provider: MemoryProvider
    ) -> None:
        """
        Initialize the tool execution service.

        Args:
            registry: The tool registry containing all tool handlers
            memory_provider: Provider for managing conversation memory
        """
        self.registry = registry
        self.memory_provider = memory_provider

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str,
        party_id: str
    ) -> str:
        """
        Execute a tool and return the result message.

        This method:
        1. Executes the tool through the registry
        2. Updates conversation memory if needed
        3. Returns a formatted result message

        Args:
            tool_name: The name of the tool to execute
            arguments: Tool-specific parameters
            user_id: The user identifier
            party_id: The party identifier

        Returns:
            The result message to display to the user
        """
        result = self.registry.execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            user_id=user_id,
            party_id=party_id
        )

        # Update conversation memory if the result indicates it should
        if result.should_update_memory and result.message:
            self.memory_provider.add_message(
                user_id=user_id,
                role="assistant",
                content=result.message
            )

        return result.message

    def requires_confirmation(self, tool_name: str) -> bool:
        """
        Check if a tool requires user confirmation.

        Args:
            tool_name: The name of the tool

        Returns:
            True if confirmation is required, False otherwise
        """
        return self.registry.requires_confirmation(tool_name)

    def generate_confirmation_message(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """
        Generate a confirmation message for a tool.

        Args:
            tool_name: The name of the tool
            arguments: The tool arguments

        Returns:
            A formatted confirmation message
        """
        return self.registry.generate_confirmation_message(tool_name, arguments)

    def extract_tool_calls(
        self,
        response: Message
    ) -> Optional[list[Dict[str, Any]]]:
        """
        Extract tool calls from an LLM API response.

        Args:
            response: The API response object

        Returns:
            List of tool call dictionaries, or None if no tool calls found
        """
        try:
            # Check for Anthropic content blocks format
            if hasattr(response, "content") and response.content:
                tool_calls = []

                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        # Anthropic format
                        tool_calls.append(
                            {
                                "name": block.name,
                                "arguments": json.dumps(block.input)
                                if isinstance(block.input, dict)
                                else block.input,
                            }
                        )

                return tool_calls if tool_calls else None

            return None
        except (AttributeError, IndexError) as e:
            # Log the error if we have a logger
            print(f"Tool call extraction error: {e}")
            return None

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            tool_name: The name of the tool

        Returns:
            True if the tool is registered, False otherwise
        """
        return self.registry.has_tool(tool_name)

    def list_available_tools(self) -> list[str]:
        """
        Get a list of all available tool names.

        Returns:
            List of registered tool names
        """
        return self.registry.list_tools()

    def get_tool_definitions(self) -> list:
        """
        Get tool definitions for the LLM API.

        Returns:
            List of tool definitions in the format expected by the LLM
        """
        return self.registry.get_tool_definitions()

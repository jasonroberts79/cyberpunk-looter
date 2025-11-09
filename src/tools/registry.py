"""
Tool registry for managing and dispatching tool handlers.

This module implements the registry pattern for tool management,
providing a centralized place to register and retrieve tools.
"""

from typing import Any, Dict, List, Optional
from anthropic.types import ToolParam
from tools.base import ToolHandler, ToolExecutionResult


class ToolRegistry:
    """
    Registry for managing tool handlers.

    Provides methods to register tools, retrieve tool definitions,
    and execute tools by name.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, ToolHandler] = {}

    def register(self, handler: ToolHandler) -> None:
        """
        Register a tool handler.

        Args:
            handler: The tool handler to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if handler.name in self._tools:
            raise ValueError(
                f"Tool '{handler.name}' is already registered"
            )
        self._tools[handler.name] = handler

    def register_multiple(self, handlers: List[ToolHandler]) -> None:
        """
        Register multiple tool handlers at once.

        Args:
            handlers: List of tool handlers to register
        """
        for handler in handlers:
            self.register(handler)

    def get_handler(self, tool_name: str) -> Optional[ToolHandler]:
        """
        Get a tool handler by name.

        Args:
            tool_name: The name of the tool

        Returns:
            The tool handler, or None if not found
        """
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            tool_name: The name of the tool

        Returns:
            True if the tool is registered, False otherwise
        """
        return tool_name in self._tools

    def get_tool_definitions(self) -> List[ToolParam]:
        """
        Get all tool definitions for the LLM API.

        Returns:
            List of tool definitions in the format expected by the LLM
        """
        return [
            handler.get_tool_definition()
            for handler in self._tools.values()
        ]

    def requires_confirmation(self, tool_name: str) -> bool:
        """
        Check if a tool requires user confirmation.

        Args:
            tool_name: The name of the tool

        Returns:
            True if confirmation required, False otherwise or if tool not found
        """
        handler = self.get_handler(tool_name)
        return handler.requires_confirmation if handler else False

    def generate_confirmation_message(
        self,
        tool_name: str,
        input: object
    ) -> str:
        """
        Generate a confirmation message for a tool.

        Args:
            tool_name: The name of the tool
            arguments: The tool arguments

        Returns:
            Confirmation message, or a default message if tool not found
        """
        handler = self.get_handler(tool_name)
        if handler:
            return handler.generate_confirmation_message(input)
        return f"Confirm execution of {tool_name}?"

    def execute_tool(
        self,
        tool_name: str,
        input: object,
        user_id: str,
        party_id: str
    ) -> ToolExecutionResult:
        """
        Execute a tool by name.

        Args:
            tool_name: The name of the tool to execute
            arguments: Tool-specific parameters
            user_id: The user identifier
            party_id: The party identifier

        Returns:
            The result of the tool execution
        """
        handler = self.get_handler(tool_name)

        if not handler:
            return ToolExecutionResult(
                success=False,
                message=f"Unknown tool: {tool_name}",
                should_update_memory=False
            )

        parsed_input = handler.parse_input(input)
        if(isinstance(parsed_input, ToolExecutionResult)):        
            return parsed_input        

        # Execute the tool
        try:
            return handler.execute(parsed_input, user_id, party_id) 
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                message=f"Error executing {tool_name}: {str(e)}",
                should_update_memory=False
            )

    def list_tools(self) -> List[str]:
        """
        Get a list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()

"""
Tool handlers for the cyberpunk-looter bot.

This package implements the Strategy pattern for tool execution,
making it easy to add new tools without modifying existing code.
"""

from tools.base import ToolHandler, ToolExecutionResult

__all__ = ["ToolHandler", "ToolExecutionResult"]

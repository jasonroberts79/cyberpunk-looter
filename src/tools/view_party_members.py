"""Tool handler for viewing party members."""

from typing import Dict, Any, Optional
from anthropic.types import ToolParam
from tools.base import ToolHandler, ToolExecutionResult
from interfaces import PartyRepository


class ViewPartyMembersTool(ToolHandler):
    """Handler for viewing all party members."""

    def __init__(self, party_repository: PartyRepository) -> None:
        """
        Initialize the tool handler.

        Args:
            party_repository: Repository for party data operations
        """
        self.party_repository = party_repository

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "view_party_members"

    @property
    def requires_confirmation(self) -> bool:
        """This tool does not require confirmation."""
        return False

    def get_tool_definition(self) -> ToolParam:
        """Get the tool definition for the LLM API."""
        return {
            "name": "view_party_members",
            "description": "View all current party members with their roles and gear preferences.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        }

    def parse_input(
        self,
        input: object
    ) -> dict[str, Any]:
        return {}
        
    def execute(
        self,
        arguments: Dict[str, Any],
        user_id: str,
        party_id: str
    ) -> ToolExecutionResult:
        """Execute the tool to view party members."""
        characters = self.party_repository.get_party_characters(party_id)

        if not characters or len(characters) == 0:
            message = "You don't have any party members yet."
        else:
            message = "**Your Party Members:**\n\n"
            for char in characters:
                message += f"**{char['name']}**\n"
                message += f"• Role: {char['role']}\n"
                if char.get("gear_preferences"):
                    message += (
                        f"• Gear Preferences: {', '.join(char['gear_preferences'])}\n"
                    )
                else:
                    message += "• Gear Preferences: None\n"
                message += "\n"

        return ToolExecutionResult(
            success=True,
            message=message,
            should_update_memory=True,
            metadata={"character_count": len(characters) if characters else 0}
        )

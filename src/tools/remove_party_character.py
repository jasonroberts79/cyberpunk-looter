"""Tool handler for removing party characters."""

from typing import Dict, Any
from anthropic.types import ToolParam
from tools.base import ToolHandler, ToolExecutionResult
from interfaces import PartyRepository


class RemovePartyCharacterTool(ToolHandler):
    """Handler for removing party characters."""

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
        return "remove_party_character"

    @property
    def requires_confirmation(self) -> bool:
        """This tool requires user confirmation."""
        return True

    def get_tool_definition(self) -> ToolParam:
        """Get the tool definition for the LLM API."""
        return {
            "name": "remove_party_character",
            "description": "Remove a character from the party by name.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the character to remove",
                    }
                },
                "required": ["name"],
            },
        }

    def generate_confirmation_message(self, input: object) -> str:
        """Generate a confirmation message for user approval."""
        parsed_input = self.parse_input(input)
        if isinstance(parsed_input, ToolExecutionResult):
            return "Tool call error"

        name = parsed_input["name"]

        return f"""📋 **Confirmation Required**

I'll remove **{name}** from your party.

👍 Confirm  👎 Cancel"""

    def parse_input(
        self,
        input: object
    ) -> dict[str, Any] | ToolExecutionResult:
        """Validate the tool arguments."""
        if not isinstance(input, dict):
            return ToolExecutionResult(success=False, message="Invalid input")

        name = input["name"]

        if not name or not isinstance(name, str) or not name.strip():
            return ToolExecutionResult(success=False, message="Invalid name")

        return { "name": name }

    def execute(
        self,
        arguments: Dict[str, Any],
        user_id: str,
        party_id: str
    ) -> ToolExecutionResult:
        """Execute the tool to remove a party character."""
        name = arguments.get("name", "")

        success = self.party_repository.remove_party_character(party_id, name)

        if success:
            message = f"**{name}** has been removed from your party."
        else:
            message = f"Character **{name}** not found in your party."

        return ToolExecutionResult(
            success=success,
            message=message,
            should_update_memory=True,
            metadata={"character_name": name, "was_removed": success}
        )

"""Tool handler for adding party characters."""

from typing import Dict, Any
from anthropic.types import ToolParam
from tools.base import ToolHandler, ToolExecutionResult
from interfaces import PartyRepository


class AddPartyCharacterTool(ToolHandler):
    """Handler for adding or updating party characters."""

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
        return "add_party_character"

    @property
    def requires_confirmation(self) -> bool:
        """This tool requires user confirmation."""
        return True

    def get_tool_definition(self) -> ToolParam:
        """Get the tool definition for the LLM API."""
        return {
            "name": "add_party_character",
            "description": "Add a new character to the party or update an existing character. Requires character name and role. Gear preferences are optional.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The character's name",
                    },
                    "role": {
                        "type": "string",
                        "description": "The character's role (e.g., Solo, Netrunner, Fixer, Rockerboy, etc.)",
                    },
                    "gear_preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of gear types the character prefers (e.g., 'Assault Rifles', 'Body Armor', 'Cyberware')",
                    },
                },
                "required": ["name", "role"],
            },
        }

    def generate_confirmation_message(self, input: object) -> str:
        """Generate a confirmation message for user approval."""
        parsed_input = self.parse_input(input)
        if isinstance(parsed_input, ToolExecutionResult):
            return "Tool call error"

        
        name = parsed_input["name"]
        role = parsed_input["role"]
        gear_prefs = parsed_input["gear_preferences"]

        gear_text = ", ".join(gear_prefs) if gear_prefs else "None"

        return f"""📋 **Confirmation Required**

I'll add **{name}** to your party:
• **Role:** {role}
• **Gear Preferences:** {gear_text}

👍 Confirm  👎 Cancel"""

    def parse_input(
        self,
        input: object
    ) -> dict[str, Any] | ToolExecutionResult:
        """Validate the tool arguments."""
        if not isinstance(input, dict):
            return ToolExecutionResult(success=False, message="Invalid input")

        name = input["name"]
        role = input["role"]

        if not name or not isinstance(name, str) or not name.strip():
            return ToolExecutionResult(success=False, message="Invalid name")

        if not role or not isinstance(role, str) or not role.strip():
            return ToolExecutionResult(success=False, message="Invalid role")

        gear_prefs = input["gear_preferences"]
        if gear_prefs is not None:
            if not isinstance(gear_prefs, list):
                return ToolExecutionResult(success=False, message="Invalid gear list")
            if not all(isinstance(item, str) for item in gear_prefs):
                return ToolExecutionResult(success=False, message="Invalid gear list item")

        return { "name": name, "role": role, "gear_preferences": gear_prefs }

    def execute(
        self,
        arguments: Dict[str, Any],
        user_id: str,
        party_id: str
    ) -> ToolExecutionResult:
        """Execute the tool to add or update a party character."""
        name = arguments.get("name", "")
        role = arguments.get("role", "")
        gear_preferences = arguments.get("gear_preferences", [])

        is_new = self.party_repository.add_party_character(
            party_id=party_id,
            name=name,
            role=role,
            gear_preferences=gear_preferences
        )

        if is_new:
            message = f"**{name}** has been added to your party!"
        else:
            message = f"**{name}** has been updated in your party!"

        return ToolExecutionResult(
            success=True,
            message=message,
            should_update_memory=True,
            metadata={"character_name": name, "is_new": is_new}
        )

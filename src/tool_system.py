"""Agentic handler for managing tool confirmations and execution."""

from anthropic.types import ToolParam
from typing import Dict, List

def is_tool_confirmation_required(tool_name: str) -> bool:
    """Check if a tool requires confirmation before execution."""
    tools_requiring_confirmation = {
        "add_party_character",
        "remove_party_character",            
    }
    return tool_name in tools_requiring_confirmation

def get_tool_definitions() -> List[ToolParam]:
    """Get tool definitions for OpenAI-compatible API."""
    return [
        {
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
        },
        {
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
        },
        {
            "name": "view_party_members",
            "description": "View all current party members with their roles and gear preferences.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "recommend_gear",
            "description": "Get AI-powered gear distribution recommendations for party members based on loot description. Accepts natural language descriptions of loot items.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "loot_description": {
                        "type": "string",
                        "description": "Natural language description of the loot to distribute (e.g., 'Assault Rifle, Body Armor, Neural Processor' or 'We got 2 SMGs from the ganger')",
                    },
                    "excluded_characters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of character names to exclude from gear distribution",
                    },
                },
                "required": ["loot_description"],
            },
        },
    ]

def generate_confirmation_message(action: str, parameters: Dict) -> str:
    """Generate a confirmation message based on action and parameters."""
    if action == "add_party_character":
        name = parameters.get("name", "Unknown")
        role = parameters.get("role", "Unknown")
        gear_prefs = parameters.get("gear_preferences", [])

        gear_text = ", ".join(gear_prefs) if gear_prefs else "None"

        return f"""📋 **Confirmation Required**

I'll add **{name}** to your party:
• **Role:** {role}
• **Gear Preferences:** {gear_text}

👍 Confirm  👎 Cancel"""

    elif action == "remove_party_character":
        name = parameters.get("name", "Unknown")

        return f"""📋 **Confirmation Required**

I'll remove **{name}** from your party.

👍 Confirm  👎 Cancel"""

    elif action == "view_party_members":
        return """📋 **Confirmation Required**

I'll show you all party members.

👍 Confirm  👎 Cancel"""

    elif action == "recommend_gear":
        loot_desc = parameters.get("loot_description", "Unknown loot")
        excluded = parameters.get("excluded_characters", [])

        excluded_text = ""
        if excluded:
            excluded_text = f"\n• **Excluding:** {', '.join(excluded)}"

        return f"""📋 **Confirmation Required**

I'll recommend gear distribution for:
• **Loot:** {loot_desc}{excluded_text}

👍 Confirm  👎 Cancel"""

    else:
        return f"""📋 **Confirmation Required**

Action: {action}

👍 Confirm  👎 Cancel"""

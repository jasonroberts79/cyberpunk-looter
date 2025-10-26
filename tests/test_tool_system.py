"""Unit tests for src.tool_system."""

from typing import Any, Dict, cast
import src.tool_system


class TestToolDefinitions:
    """Test tool definition retrieval."""

    def test_get_tool_definitions_returns_list(self):
        """Test that get_tool_definitions returns a list."""
        tools = src.tool_system.get_tool_definitions()

        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_get_tool_definitions_has_required_tools(self):
        """Test that all expected tools are defined."""
        tools = src.tool_system.get_tool_definitions()
        tool_names = [tool["name"] for tool in tools]

        assert "add_party_character" in tool_names
        assert "remove_party_character" in tool_names
        assert "view_party_members" in tool_names
        assert "recommend_gear" in tool_names

    def test_add_party_character_tool_structure(self):
        """Test add_party_character tool has correct structure."""
        tools = src.tool_system.get_tool_definitions()
        add_char_tool = next(t for t in tools if t["name"] == "add_party_character")

        assert "description" in add_char_tool
        assert "input_schema" in add_char_tool
        input_schema = add_char_tool["input_schema"]
        assert input_schema["type"] == "object"
        assert "properties" in input_schema
        properties = cast(Dict[str, Any], input_schema["properties"])
        assert properties is not None
        assert "name" in properties
        assert "role" in properties
        assert "gear_preferences" in properties
        assert "required" in input_schema
        assert input_schema["required"] == ["name", "role"]

    def test_remove_party_character_tool_structure(self):
        """Test remove_party_character tool has correct structure."""
        tools = src.tool_system.get_tool_definitions()
        remove_char_tool = next(t for t in tools if t["name"] == "remove_party_character")

        assert "description" in remove_char_tool
        assert "input_schema" in remove_char_tool
        input_schema = remove_char_tool["input_schema"]
        assert "properties" in input_schema
        properties = cast(Dict[str, Any], input_schema["properties"])
        assert properties is not None
        assert "name" in properties
        assert "required" in input_schema
        assert input_schema["required"] == ["name"]

    def test_view_party_members_tool_structure(self):
        """Test view_party_members tool has correct structure."""
        tools = src.tool_system.get_tool_definitions()
        view_tool = next(t for t in tools if t["name"] == "view_party_members")

        assert "description" in view_tool
        assert "input_schema" in view_tool
        input_schema = view_tool["input_schema"]
        assert "required" in input_schema
        assert input_schema["required"] == []

    def test_recommend_gear_tool_structure(self):
        """Test recommend_gear tool has correct structure."""
        tools = src.tool_system.get_tool_definitions()
        recommend_tool = next(t for t in tools if t["name"] == "recommend_gear")

        assert "description" in recommend_tool
        assert "input_schema" in recommend_tool
        input_schema = recommend_tool["input_schema"]
        assert "properties" in input_schema
        properties = cast(Dict[str, Any], input_schema["properties"])
        assert properties is not None
        assert "loot_description" in properties
        assert "excluded_characters" in properties
        assert "required" in input_schema
        assert input_schema["required"] == ["loot_description"]


class TestGenerateConfirmationMessage:
    """Test generate_confirmation_message method."""

    def test_generate_add_party_character_message(self):
        """Test confirmation message for adding party character."""
        parameters = {
            "name": "V",
            "role": "Solo",
            "gear_preferences": ["Assault Rifles", "Body Armor"],
        }

        message = src.tool_system.generate_confirmation_message("add_party_character", parameters)

        assert "V" in message
        assert "Solo" in message
        assert "Assault Rifles" in message
        assert "Body Armor" in message
        assert "👍" in message
        assert "👎" in message

    def test_generate_add_party_character_no_preferences(self):
        """Test confirmation message with no gear preferences."""
        parameters = {
            "name": "Jackie",
            "role": "Fixer",
            "gear_preferences": [],
        }

        message = src.tool_system.generate_confirmation_message("add_party_character", parameters)

        assert "Jackie" in message
        assert "Fixer" in message
        assert "None" in message

    def test_generate_remove_party_character_message(self):
        """Test confirmation message for removing party character."""
        parameters = {"name": "V"}

        message = src.tool_system.generate_confirmation_message(
            "remove_party_character", parameters
        )

        assert "V" in message
        assert "remove" in message.lower()
        assert "👍" in message
        assert "👎" in message

    def test_generate_view_party_members_message(self):
        """Test confirmation message for viewing party members."""
        parameters = {}

        message = src.tool_system.generate_confirmation_message("view_party_members", parameters)

        assert "party members" in message.lower()
        assert "👍" in message
        assert "👎" in message

    def test_generate_recommend_gear_message(self):
        """Test confirmation message for gear recommendation."""
        parameters = {
            "loot_description": "Assault Rifle, Body Armor",
            "excluded_characters": [],
        }

        message = src.tool_system.generate_confirmation_message("recommend_gear", parameters)

        assert "Assault Rifle" in message
        assert "Body Armor" in message
        assert "👍" in message
        assert "👎" in message

    def test_generate_recommend_gear_with_exclusions(self):
        """Test gear recommendation message with excluded characters."""
        parameters = {
            "loot_description": "SMG",
            "excluded_characters": ["V", "Jackie"],
        }

        message = src.tool_system.generate_confirmation_message("recommend_gear", parameters)

        assert "SMG" in message
        assert "V" in message
        assert "Jackie" in message
        assert "Excluding" in message

    def test_generate_unknown_action_message(self):
        """Test confirmation message for unknown action."""
        parameters = {}

        message = src.tool_system.generate_confirmation_message("unknown_action", parameters)

        assert "unknown_action" in message
        assert "👍" in message
        assert "👎" in message

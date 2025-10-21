import pytest
import time
from src.agentic_handler import (
    pending_confirmations,
    add_pending_confirmation,
    get_pending_confirmation,
    remove_pending_confirmation,
    is_timed_out,
    get_tool_definitions,
    generate_confirmation_message,
)


@pytest.fixture
def cleanup_confirmations():
    """Clean up pending confirmations after each test."""
    yield
    pending_confirmations.clear()


def test_add_pending_confirmation(cleanup_confirmations):
    """Test adding a confirmation to the dict with correct structure."""
    message_id = "123456789"
    user_id = "user123"
    action = "add_party_character"
    parameters = {"name": "V", "role": "Solo", "gear_preferences": ["Assault Rifles"]}
    channel_id = "987654321"

    add_pending_confirmation(message_id, user_id, action, parameters, channel_id)

    assert message_id in pending_confirmations
    confirmation = pending_confirmations[message_id]
    assert confirmation["user_id"] == user_id
    assert confirmation["action"] == action
    assert confirmation["parameters"] == parameters
    assert confirmation["channel_id"] == channel_id
    assert confirmation["processed"] is False
    assert "timestamp" in confirmation
    assert isinstance(confirmation["timestamp"], float)


def test_get_pending_confirmation(cleanup_confirmations):
    """Test retrieval of existing confirmation."""
    message_id = "123456789"
    user_id = "user123"
    action = "add_party_character"
    parameters = {"name": "V", "role": "Solo"}

    add_pending_confirmation(message_id, user_id, action, parameters)

    confirmation = get_pending_confirmation(message_id)
    assert confirmation is not None
    assert confirmation["user_id"] == user_id
    assert confirmation["action"] == action


def test_get_pending_confirmation_not_found(cleanup_confirmations):
    """Test None returned for non-existent message_id."""
    confirmation = get_pending_confirmation("nonexistent")
    assert confirmation is None


def test_remove_pending_confirmation(cleanup_confirmations):
    """Test confirmation removed from dict."""
    message_id = "123456789"
    user_id = "user123"
    action = "add_party_character"
    parameters = {"name": "V", "role": "Solo"}

    add_pending_confirmation(message_id, user_id, action, parameters)
    assert message_id in pending_confirmations

    remove_pending_confirmation(message_id)
    assert message_id not in pending_confirmations


def test_is_timed_out_not_expired(cleanup_confirmations):
    """Test returns False for recent confirmation."""
    confirmation = {
        "user_id": "user123",
        "action": "add_party_character",
        "parameters": {},
        "timestamp": time.time(),  # Current time
        "processed": False,
    }

    assert is_timed_out(confirmation) is False


def test_is_timed_out_expired(cleanup_confirmations):
    """Test returns True for old confirmation (>60 seconds)."""
    confirmation = {
        "user_id": "user123",
        "action": "add_party_character",
        "parameters": {},
        "timestamp": time.time() - 61,  # 61 seconds ago
        "processed": False,
    }

    assert is_timed_out(confirmation) is True


# Phase 17: Tool Definitions Tests


def test_get_tool_definitions_structure():
    """Test returns list of 4 dicts."""
    tools = get_tool_definitions()
    assert isinstance(tools, list)
    assert len(tools) == 4
    for tool in tools:
        assert isinstance(tool, dict)
        assert "type" in tool
        assert tool["type"] == "function"
        assert "function" in tool


def test_add_party_character_tool_schema():
    """Test correct parameters (name required, role required, gear_preferences optional)."""
    tools = get_tool_definitions()
    add_char_tool = next(
        t for t in tools if t["function"]["name"] == "add_party_character"
    )

    assert add_char_tool is not None
    function = add_char_tool["function"]
    assert function["name"] == "add_party_character"
    assert "parameters" in function

    params = function["parameters"]
    assert "name" in params["properties"]
    assert "role" in params["properties"]
    assert "gear_preferences" in params["properties"]

    assert "name" in params["required"]
    assert "role" in params["required"]
    assert "gear_preferences" not in params["required"]


def test_remove_party_character_tool_schema():
    """Test correct parameters (name required)."""
    tools = get_tool_definitions()
    remove_char_tool = next(
        t for t in tools if t["function"]["name"] == "remove_party_character"
    )

    assert remove_char_tool is not None
    function = remove_char_tool["function"]
    assert function["name"] == "remove_party_character"

    params = function["parameters"]
    assert "name" in params["properties"]
    assert "name" in params["required"]


def test_view_party_members_tool_schema():
    """Test no required parameters."""
    tools = get_tool_definitions()
    view_party_tool = next(
        t for t in tools if t["function"]["name"] == "view_party_members"
    )

    assert view_party_tool is not None
    function = view_party_tool["function"]
    assert function["name"] == "view_party_members"

    params = function["parameters"]
    assert params["required"] == []


def test_recommend_gear_tool_schema():
    """Test correct parameters (loot_description required, excluded_characters optional)."""
    tools = get_tool_definitions()
    recommend_tool = next(t for t in tools if t["function"]["name"] == "recommend_gear")

    assert recommend_tool is not None
    function = recommend_tool["function"]
    assert function["name"] == "recommend_gear"

    params = function["parameters"]
    assert "loot_description" in params["properties"]
    assert "excluded_characters" in params["properties"]

    assert "loot_description" in params["required"]
    assert "excluded_characters" not in params["required"]


# Phase 18: Confirmation Messages Tests


def test_generate_confirmation_message_add_character():
    """Test format includes name, role, gear prefs."""
    parameters = {
        "name": "V",
        "role": "Solo",
        "gear_preferences": ["Assault Rifles", "Body Armor"],
    }
    message = generate_confirmation_message("add_party_character", parameters)

    assert "V" in message
    assert "Solo" in message
    assert "Assault Rifles" in message
    assert "Body Armor" in message
    assert "👍" in message
    assert "👎" in message
    assert "Confirmation Required" in message


def test_generate_confirmation_message_remove_character():
    """Test format includes character name."""
    parameters = {"name": "Johnny"}
    message = generate_confirmation_message("remove_party_character", parameters)

    assert "Johnny" in message
    assert "remove" in message.lower()
    assert "👍" in message
    assert "👎" in message


def test_generate_confirmation_message_view_party():
    """Test simple confirmation message."""
    parameters = {}
    message = generate_confirmation_message("view_party_members", parameters)

    assert "party members" in message.lower()
    assert "👍" in message
    assert "👎" in message


def test_generate_confirmation_message_recommend_gear():
    """Test includes loot description."""
    parameters = {
        "loot_description": "2 SMGs and body armor",
        "excluded_characters": ["V"],
    }
    message = generate_confirmation_message("recommend_gear", parameters)

    assert "2 SMGs and body armor" in message
    assert "V" in message
    assert "Excluding" in message or "exclude" in message.lower()
    assert "👍" in message
    assert "👎" in message

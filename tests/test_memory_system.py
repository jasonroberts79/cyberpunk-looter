"""Unit tests for MemorySystem."""

import json
from unittest.mock import Mock, patch
from src.memory_system import MemorySystem


class TestMemorySystemInit:
    """Test MemorySystem initialization."""

    @patch("src.memory_system.AppStorage")
    def test_init_default_filename(self, mock_storage_class):
        """Test initialization with default filename."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()

        assert memory.memory_file == "long_term_memory.json"
        assert memory.storage is not None
        assert memory.short_term_memory == {}        
        assert memory.long_term_memory == {}

    @patch("src.memory_system.AppStorage")
    def test_init_custom_filename(self, mock_storage_class):
        """Test initialization with custom filename."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem(memory_file="custom_memory.json")

        assert memory.memory_file == "custom_memory.json"

    @patch("src.memory_system.AppStorage")
    def test_init_loads_existing_memory(self, mock_storage_class):
        """Test initialization loads existing long-term memory."""
        test_data = {
            "user123": {
                "user_id": "user123",
                "interaction_count": 5,
                "preferences": {"theme": "dark"},
            }
        }
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = json.dumps(test_data)
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()

        assert memory.long_term_memory == test_data
        assert "user123" in memory.long_term_memory


class TestShortTermMemory:
    """Test short-term memory operations."""

    @patch("src.memory_system.AppStorage")
    def test_add_to_short_term(self, mock_storage_class):
        """Test adding messages to short-term memory."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_to_short_term("user123", "user", "Hello!")

        assert len(memory.short_term_memory["user123"]) == 1
        assert memory.short_term_memory["user123"][0]["role"] == "user"
        assert memory.short_term_memory["user123"][0]["content"] == "Hello!"
        assert "timestamp" in memory.short_term_memory["user123"][0]

    @patch("src.memory_system.AppStorage")
    def test_short_term_memory_limit(self, mock_storage_class):
        """Test that short-term memory is limited to 10 messages."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()

        # Add 12 messages
        for i in range(12):
            memory.add_to_short_term("user123", "user", f"Message {i}")

        # Should only keep the last 10
        assert len(memory.short_term_memory["user123"]) == 10
        assert memory.short_term_memory["user123"][0]["content"] == "Message 2"
        assert memory.short_term_memory["user123"][-1]["content"] == "Message 11"

    @patch("src.memory_system.AppStorage")
    def test_get_short_term_context(self, mock_storage_class):
        """Test retrieving short-term context."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()

        # Add 8 messages
        for i in range(8):
            memory.add_to_short_term("user123", "user", f"Message {i}")

        context = memory.get_short_term_context("user123", max_messages=4)

        assert len(context) == 4
        assert context[0]["content"] == "Message 4"
        assert context[-1]["content"] == "Message 7"

    @patch("src.memory_system.AppStorage")
    def test_get_short_term_context_empty(self, mock_storage_class):
        """Test retrieving context for user with no messages."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        context = memory.get_short_term_context("new_user")

        assert context == []

    @patch("src.memory_system.AppStorage")
    def test_clear_short_term(self, mock_storage_class):
        """Test clearing short-term memory for a user."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_to_short_term("user123", "user", "Hello!")
        memory.clear_short_term("user123")

        assert "user123" not in memory.short_term_memory

class TestLongTermMemory:
    """Test long-term memory operations."""

    @patch("src.memory_system.AppStorage")
    def test_update_long_term_new_user(self, mock_storage_class):
        """Test updating long-term memory creates new user entry."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)

        assert "user123" in memory.long_term_memory
        assert memory.long_term_memory["user123"]["user_id"] == "user123"
        assert memory.long_term_memory["user123"]["interaction_count"] == 1
        assert "created_at" in memory.long_term_memory["user123"]
        mock_storage_instance.writedata.assert_called()

    @patch("src.memory_system.AppStorage")
    def test_update_long_term_interaction(self, mock_storage_class):
        """Test updating interaction count."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)
        memory.update_long_term("user123", "interaction", None)

        assert memory.long_term_memory["user123"]["interaction_count"] == 2
        assert "last_interaction" in memory.long_term_memory["user123"]

    @patch("src.memory_system.AppStorage")
    def test_update_long_term_preference(self, mock_storage_class):
        """Test updating user preferences."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)
        memory.update_long_term("user123", "preference", {"theme": "dark"})

        assert memory.long_term_memory["user123"]["preferences"]["theme"] == "dark"

    @patch("src.memory_system.AppStorage")
    def test_update_long_term_topic(self, mock_storage_class):
        """Test adding topics to long-term memory."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)
        memory.update_long_term("user123", "topic", "Cyberpunk 2077")
        memory.update_long_term("user123", "topic", "Gear Management")

        assert (
            "Cyberpunk 2077" in memory.long_term_memory["user123"]["topics_discussed"]
        )
        assert (
            "Gear Management" in memory.long_term_memory["user123"]["topics_discussed"]
        )

    @patch("src.memory_system.AppStorage")
    def test_update_long_term_topic_no_duplicates(self, mock_storage_class):
        """Test that duplicate topics are not added."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)
        memory.update_long_term("user123", "topic", "Cyberpunk")
        memory.update_long_term("user123", "topic", "Cyberpunk")

        assert (
            memory.long_term_memory["user123"]["topics_discussed"].count("Cyberpunk")
            == 1
        )

    @patch("src.memory_system.AppStorage")
    def test_get_long_term_context(self, mock_storage_class):
        """Test retrieving long-term context."""
        test_data = {
            "user123": {
                "user_id": "user123",
                "interaction_count": 5,
            }
        }
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = json.dumps(test_data)
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        context = memory.get_long_term_context("user123")

        assert context == test_data["user123"]

    @patch("src.memory_system.AppStorage")
    def test_get_user_summary_first_conversation(self, mock_storage_class):
        """Test user summary for first conversation."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        summary = memory.get_user_summary("new_user")

        assert summary == "This is our first conversation."

    @patch("src.memory_system.AppStorage")
    def test_get_user_summary_with_data(self, mock_storage_class):
        """Test user summary with existing data."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)
        memory.update_long_term("user123", "interaction", None)
        memory.update_long_term("user123", "preference", {"theme": "dark"})
        memory.update_long_term("user123", "topic", "Cyberpunk")

        summary = memory.get_user_summary("user123")

        assert "2 times" in summary
        assert "theme: dark" in summary
        assert "Cyberpunk" in summary


class TestPartyManagement:
    """Test party management functionality."""

    @patch("src.memory_system.AppStorage")
    def test_add_party_character_new(self, mock_storage_class):
        """Test adding a new party character."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        is_new = memory.add_party_character(
            "user123", "V", "Solo", ["Assault Rifles", "Body Armor"]
        )

        assert is_new is True
        assert "user123" in memory.long_term_memory
        assert "party_members" in memory.long_term_memory["user123"]
        assert "v" in memory.long_term_memory["user123"]["party_members"]

        character = memory.long_term_memory["user123"]["party_members"]["v"]
        assert character["name"] == "V"
        assert character["role"] == "Solo"
        assert character["gear_preferences"] == ["Assault Rifles", "Body Armor"]
        mock_storage_instance.writedata.assert_called()

    @patch("src.memory_system.AppStorage")
    def test_add_party_character_update(self, mock_storage_class):
        """Test updating an existing party character."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_party_character("user123", "V", "Solo", ["Guns"])
        is_new = memory.add_party_character("user123", "V", "Netrunner", ["Cyberware"])

        assert is_new is False
        character = memory.long_term_memory["user123"]["party_members"]["v"]
        assert character["role"] == "Netrunner"
        assert character["gear_preferences"] == ["Cyberware"]

    @patch("src.memory_system.AppStorage")
    def test_remove_party_character_success(self, mock_storage_class):
        """Test removing an existing party character."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_party_character("user123", "V", "Solo", [])

        result = memory.remove_party_character("user123", "V")

        assert result is True
        assert "v" not in memory.long_term_memory["user123"]["party_members"]

    @patch("src.memory_system.AppStorage")
    def test_remove_party_character_not_found(self, mock_storage_class):
        """Test removing a non-existent character."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        result = memory.remove_party_character("user123", "NonExistent")

        assert result is False

    @patch("src.memory_system.AppStorage")
    def test_get_party_character(self, mock_storage_class):
        """Test getting a specific party character."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_party_character("user123", "V", "Solo", ["Guns"])

        character = memory.get_party_character("user123", "V")

        assert character is not None
        assert character["name"] == "V"
        assert character["role"] == "Solo"

    @patch("src.memory_system.AppStorage")
    def test_get_party_character_not_found(self, mock_storage_class):
        """Test getting a non-existent character."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        character = memory.get_party_character("user123", "NonExistent")

        assert character is None

    @patch("src.memory_system.AppStorage")
    def test_list_party_characters(self, mock_storage_class):
        """Test listing all party characters."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_party_character("user123", "V", "Solo", [])
        memory.add_party_character("user123", "Jackie", "Fixer", [])

        characters = memory.list_party_characters("user123")

        assert len(characters) == 2
        names = [char["name"] for char in characters]
        assert "V" in names
        assert "Jackie" in names

    @patch("src.memory_system.AppStorage")
    def test_list_party_characters_empty(self, mock_storage_class):
        """Test listing characters when none exist."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        characters = memory.list_party_characters("user123")

        assert characters == []

    @patch("src.memory_system.AppStorage")
    def test_get_party_summary(self, mock_storage_class):
        """Test getting party summary."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.add_party_character("user123", "V", "Solo", ["Assault Rifles"])
        memory.add_party_character("user123", "Jackie", "Fixer", [])

        summary = memory.get_party_summary("user123")

        assert "V (Solo)" in summary
        assert "Jackie (Fixer)" in summary
        assert "Assault Rifles" in summary

    @patch("src.memory_system.AppStorage")
    def test_get_party_summary_empty(self, mock_storage_class):
        """Test party summary when no members exist."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        summary = memory.get_party_summary("user123")

        assert summary == "No party members registered."


class TestPersistence:
    """Test data persistence operations."""

    @patch("src.memory_system.AppStorage")
    def test_save_long_term_memory(self, mock_storage_class):
        """Test saving long-term memory."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()
        memory.update_long_term("user123", "interaction", None)

        # Should have been called by update_long_term
        assert mock_storage_instance.writedata.called
        call_args = mock_storage_instance.writedata.call_args[0]
        assert call_args[0] == "long_term_memory.json"
        # Verify JSON can be parsed
        json.loads(call_args[1])

    @patch("src.memory_system.AppStorage")
    def test_load_long_term_memory_error(self, mock_storage_class):
        """Test loading memory handles errors gracefully."""
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.side_effect = Exception("Storage error")
        mock_storage_class.return_value = mock_storage_instance

        memory = MemorySystem()

        # Should not crash, just start with empty memory
        assert memory.long_term_memory == {}

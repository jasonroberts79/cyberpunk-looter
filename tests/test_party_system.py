import pytest
from unittest.mock import Mock, patch
from src.memory_system import MemorySystem


@pytest.fixture
def mock_storage():
    """Mock AppStorage for testing"""
    with patch("src.memory_system.AppStorage") as mock:
        storage_instance = Mock()
        storage_instance.readdata.return_value = None
        mock.return_value = storage_instance
        yield storage_instance


@pytest.fixture
def memory_system(mock_storage):
    """Create a MemorySystem instance for testing"""
    return MemorySystem()


def test_memory_system_initialization(mock_storage):
    """Test that memory system initializes correctly"""
    memory_system = MemorySystem()
    assert memory_system.long_term_memory == {}
    mock_storage.readdata.assert_called_once_with("long_term_memory.json")


def test_add_character(memory_system, mock_storage):
    """Test adding a character to the party"""
    user_id = "user123"

    is_new = memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor", "Shields"],
    )

    assert is_new is True
    assert user_id in memory_system.long_term_memory
    assert "party_members" in memory_system.long_term_memory[user_id]
    assert "tank1" in memory_system.long_term_memory[user_id]["party_members"]

    char = memory_system.long_term_memory[user_id]["party_members"]["tank1"]
    assert char["name"] == "Tank1"
    assert char["role"] == "Tank"
    assert char["gear_preferences"] == ["Heavy Armor", "Shields"]
    mock_storage.writedata.assert_called()


def test_update_character(memory_system, mock_storage):
    """Test updating an existing character"""
    user_id = "user123"

    # Add character
    memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor"],
    )

    # Update character
    is_new = memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Paladin",
        gear_preferences=["Heavy Armor", "Holy Weapons"],
    )

    assert is_new is False
    char = memory_system.long_term_memory[user_id]["party_members"]["tank1"]
    assert char["role"] == "Paladin"
    assert char["gear_preferences"] == ["Heavy Armor", "Holy Weapons"]
    assert "updated_at" in char


def test_remove_character(memory_system, mock_storage):
    """Test removing a character"""
    user_id = "user123"

    memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor"],
    )

    success = memory_system.remove_party_character(user_id, "Tank1")
    assert success is True
    assert "tank1" not in memory_system.long_term_memory[user_id]["party_members"]

    # Try removing non-existent character
    success = memory_system.remove_party_character(user_id, "NonExistent")
    assert success is False


def test_get_character(memory_system, mock_storage):
    """Test getting a specific character"""
    user_id = "user123"

    memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor"],
    )

    char = memory_system.get_party_character(user_id, "Tank1")
    assert char is not None
    assert char["name"] == "Tank1"
    assert char["role"] == "Tank"

    # Test case insensitive lookup
    char = memory_system.get_party_character(user_id, "tank1")
    assert char is not None

    # Test non-existent character
    char = memory_system.get_party_character(user_id, "NonExistent")
    assert char is None


def test_list_characters(memory_system, mock_storage):
    """Test listing all characters"""
    user_id = "user123"

    memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor"],
    )
    memory_system.add_party_character(
        user_id=user_id,
        character_name="Healer1",
        role="Healer",
        gear_preferences=["Staves", "Healing"],
    )

    characters = memory_system.list_party_characters(user_id)
    assert len(characters) == 2
    assert any(char["name"] == "Tank1" for char in characters)
    assert any(char["name"] == "Healer1" for char in characters)


def test_party_summary(memory_system, mock_storage):
    """Test getting party summary for LLM context"""
    user_id = "user123"

    # Add some characters
    memory_system.add_party_character(
        user_id=user_id,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor", "Shields"],
    )
    memory_system.add_party_character(
        user_id=user_id,
        character_name="Healer1",
        role="Healer",
        gear_preferences=["Staves", "Healing"],
    )

    summary = memory_system.get_party_summary(user_id)

    assert "Tank1" in summary
    assert "Tank" in summary
    assert "Healer1" in summary
    assert "Healer" in summary
    assert "Heavy Armor" in summary or "Shields" in summary
    assert "Staves" in summary or "Healing" in summary


def test_party_summary_empty(memory_system, mock_storage):
    """Test party summary when no characters exist"""
    user_id = "user123"

    summary = memory_system.get_party_summary(user_id)
    assert summary == "No party members registered."


def test_multiple_users_separate_parties(memory_system, mock_storage):
    """Test that different users have separate party lists"""
    user1 = "user123"
    user2 = "user456"

    memory_system.add_party_character(
        user_id=user1,
        character_name="Tank1",
        role="Tank",
        gear_preferences=["Heavy Armor"],
    )
    memory_system.add_party_character(
        user_id=user2,
        character_name="Healer1",
        role="Healer",
        gear_preferences=["Staves"],
    )

    user1_chars = memory_system.list_party_characters(user1)
    user2_chars = memory_system.list_party_characters(user2)

    assert len(user1_chars) == 1
    assert len(user2_chars) == 1
    assert user1_chars[0]["name"] == "Tank1"
    assert user2_chars[0]["name"] == "Healer1"

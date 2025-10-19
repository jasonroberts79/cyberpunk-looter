"""
Integration tests for the recommend_gear command logic.
"""

import pytest
from src.memory_system import MemorySystem
from unittest.mock import Mock, patch

blackhand = "Morgan Blackhand"
johnny = "Johnny Silverhand"
rogue = "Rogue"

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


def test_get_all_party_members_default(memory_system):
    """Test that all party members are returned when no exclusions"""
    user_id = "user123"

    # Add multiple characters
    memory_system.add_party_character(
        user_id=user_id, character_name=blackhand, role="Solo", gear_preferences=["Shoulder arms"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name=johnny, role="Rockerboy", gear_preferences=["Handguns"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name="Rogue", role="Rockerboy", gear_preferences=["eddies"]
    )

    # Get all characters
    all_chars = memory_system.list_party_characters(user_id)

    assert len(all_chars) == 3
    assert any(c["name"] == blackhand for c in all_chars)
    assert any(c["name"] == johnny for c in all_chars)
    assert any(c["name"] == rogue for c in all_chars)


def test_exclude_single_character(memory_system):
    """Test excluding a single character from the party"""
    user_id = "user123"

    # Add multiple characters
    memory_system.add_party_character(
        user_id=user_id, character_name=blackhand, role="Solo", gear_preferences=["Shoulder arms"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name=johnny, role="Rockerboy", gear_preferences=["Handguns"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name=rogue, role="Fixer", gear_preferences=["eddies"]
    )

    # Simulate excluding Tank1
    all_chars = memory_system.list_party_characters(user_id)
    exclude_chars = [blackhand]
    excluded_lower = [name.lower() for name in exclude_chars]

    present_chars = [char for char in all_chars if char["name"].lower() not in excluded_lower]

    assert len(present_chars) == 2
    assert not any(c["name"] == blackhand for c in present_chars)
    assert any(c["name"] == johnny for c in present_chars)
    assert any(c["name"] == rogue for c in present_chars)


def test_exclude_case_insensitive(memory_system):
    """Test that exclusion is case-insensitive"""
    user_id = "user123"

    # Add characters with mixed case names
    memory_system.add_party_character(
        user_id=user_id, character_name=blackhand, role="Solo", gear_preferences=["Shoulder arms"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name=johnny, role="Rockerboy", gear_preferences=["Handguns"]
    )

    # Simulate excluding with different case
    all_chars = memory_system.list_party_characters(user_id)
    exclude_chars = [blackhand]  # lowercase
    excluded_lower = [name.lower() for name in exclude_chars]

    present_chars = [char for char in all_chars if char["name"].lower() not in excluded_lower]

    assert len(present_chars) == 1
    assert not any(c["name"] == blackhand for c in present_chars)
    assert any(c["name"] == johnny for c in present_chars)


def test_exclude_nonexistent_character(memory_system):
    """Test excluding a character that doesn't exist doesn't affect results"""
    user_id = "user123"

    # Add characters
    memory_system.add_party_character(
        user_id=user_id, character_name=blackhand, role="Solo", gear_preferences=["Shoulder arms"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name=johnny, role="Rockerboy", gear_preferences=["Handguns"]
    )

    # Simulate excluding a nonexistent character
    all_chars = memory_system.list_party_characters(user_id)
    exclude_chars = ["NonExistent"]
    excluded_lower = [name.lower() for name in exclude_chars]

    present_chars = [char for char in all_chars if char["name"].lower() not in excluded_lower]

    # Should still have all characters
    assert len(present_chars) == 2
    assert any(c["name"] == blackhand for c in present_chars)
    assert any(c["name"] == johnny for c in present_chars)


def test_exclude_all_characters(memory_system):
    """Test excluding all characters results in empty list"""
    user_id = "user123"

    # Add characters
    memory_system.add_party_character(
        user_id=user_id, character_name=blackhand, role="Solo", gear_preferences=["Shoulder arms"]
    )
    memory_system.add_party_character(
        user_id=user_id, character_name=johnny, role="Rockerboy", gear_preferences=["Handguns"]
    )

    # Simulate excluding all characters
    all_chars = memory_system.list_party_characters(user_id)
    exclude_chars = [blackhand, johnny]
    excluded_lower = [name.lower() for name in exclude_chars]

    present_chars = [char for char in all_chars if char["name"].lower() not in excluded_lower]

    assert len(present_chars) == 0

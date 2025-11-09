"""
Party repository for managing party character data.

This module handles persistent storage of party members
and their associated information.
"""

import json
from typing import Dict, List, Optional, Any
from interfaces import Storage
from models import PartyData, PartyCharacter
from config import MemoryConfig


class PartyRepository:
    """
    Repository for managing party data.

    This class handles persistence of party members, their roles,
    and gear preferences across sessions.
    """

    def __init__(
        self,
        storage: Storage,
        config: MemoryConfig = MemoryConfig()
    ) -> None:
        """
        Initialize the party repository.

        Args:
            storage: Storage backend for persistence
            config: Memory configuration settings
        """
        self.storage = storage
        self.config = config
        self.parties: Dict[str, PartyData] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load party data from storage."""
        try:
            data_str = self.storage.read_data(self.config.party_storage_file)
            if data_str:
                data = json.loads(data_str)
                self.parties = {
                    party_id: PartyData.from_dict(party_id, party_data)
                    for party_id, party_data in data.items()
                }
                print(f"Loaded party data for {len(self.parties)} parties")
            else:
                self.parties = {}
        except Exception as e:
            print(f"Error loading party data: {e}")
            self.parties = {}

    def _save_data(self) -> None:
        """Save party data to storage."""
        try:
            data = {
                party_id: party.to_dict()
                for party_id, party in self.parties.items()
            }
            data_str = json.dumps(data, indent=2)
            self.storage.write_data(self.config.party_storage_file, data_str)
        except Exception as e:
            print(f"Error saving party data: {e}")

    def add_party_character(
        self,
        party_id: str,
        name: str,
        role: str,
        gear_preferences: Optional[List[str]] = None
    ) -> bool:
        """
        Add or update a character in a party.

        Args:
            party_id: The party identifier
            name: Character name
            role: Character role/class
            gear_preferences: Optional list of preferred gear types

        Returns:
            True if new character added, False if existing character updated
        """
        party = self._ensure_party(party_id)

        character = PartyCharacter(
            name=name,
            role=role,
            gear_preferences=gear_preferences or []
        )

        is_new = party.add_character(character)
        self._save_data()
        return is_new

    def remove_party_character(self, party_id: str, name: str) -> bool:
        """
        Remove a character from a party.

        Args:
            party_id: The party identifier
            name: Character name to remove

        Returns:
            True if character was removed, False if not found
        """
        party = self.parties.get(party_id)
        if not party:
            return False

        was_removed = party.remove_character(name)
        if was_removed:
            self._save_data()
        return was_removed

    def get_party_character(
        self,
        party_id: str,
        name: str
    ) -> Optional[PartyCharacter]:
        """
        Get a specific character from a party.

        Args:
            party_id: The party identifier
            name: Character name

        Returns:
            PartyCharacter object or None if not found
        """
        party = self.parties.get(party_id)
        if not party:
            return None
        return party.get_character(name)

    def get_party_characters(self, party_id: str) -> List[Dict[str, Any]]:
        """
        Get all characters in a party.

        Args:
            party_id: The party identifier

        Returns:
            List of character dictionaries
        """
        party = self.parties.get(party_id)
        if not party or not party.characters:
            return []

        return [char.to_dict() for char in party.characters]

    def list_party_characters(self, party_id: str) -> List[Dict[str, Any]]:
        """
        List all party characters (alias for get_party_characters).

        This method maintains compatibility with the old interface.

        Args:
            party_id: The party identifier

        Returns:
            List of character dictionaries
        """
        return self.get_party_characters(party_id)

    def get_party_summary(self, party_id: str) -> str:
        """
        Get a formatted summary of party members.

        Args:
            party_id: The party identifier

        Returns:
            Formatted party summary string for LLM context
        """
        characters = self.get_party_characters(party_id)

        if not characters:
            return "No party members registered."

        summary = "Party Members:\n"
        for char in characters:
            summary += f"- {char['name']} ({char['role']})"
            if char.get("gear_preferences"):
                summary += f" - Prefers: {', '.join(char['gear_preferences'])}"
            summary += "\n"

        return summary.strip()

    def get_party(self, party_id: str) -> Optional[PartyData]:
        """
        Get the full party data object.

        Args:
            party_id: The party identifier

        Returns:
            PartyData object or None if not found
        """
        return self.parties.get(party_id)

    def _ensure_party(self, party_id: str) -> PartyData:
        """
        Ensure a party exists, creating if necessary.

        Args:
            party_id: The party identifier

        Returns:
            The PartyData object for this party
        """
        if party_id not in self.parties:
            self.parties[party_id] = PartyData(party_id=party_id)
        return self.parties[party_id]

    def delete_party(self, party_id: str) -> bool:
        """
        Delete all data for a party.

        Args:
            party_id: The party identifier

        Returns:
            True if party was deleted, False if party didn't exist
        """
        if party_id in self.parties:
            del self.parties[party_id]
            self._save_data()
            return True
        return False

    def get_all_parties(self) -> List[str]:
        """
        Get a list of all party IDs.

        Returns:
            List of party identifiers
        """
        return list(self.parties.keys())

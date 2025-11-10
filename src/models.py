"""
Data models for the cyberpunk-looter application.

This module defines strongly-typed classes to replace primitive types
and dictionaries throughout the codebase, improving type safety and clarity.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ConversationMessage(BaseModel):
    """Represents a single message in a conversation."""

    role: str
    """The role of the message sender (e.g., 'user', 'assistant')."""

    content: str
    """The message content."""

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    """ISO format timestamp of when the message was created."""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API compatibility."""
        return {
            "role": self.role,
            "content": self.content
        }


class PendingConfirmation(BaseModel):
    """Represents a tool action awaiting user confirmation."""

    user_id: str
    """The ID of the user who initiated the action."""

    party_id: str
    """The ID of the party context for the action."""

    action: str
    """The name of the tool action to be executed."""

    parameters: object
    """The parameters for the tool action."""

    timestamp: float
    """Unix timestamp when the confirmation was created."""

    processed: bool = False
    """Whether this confirmation has been processed (approved/rejected)."""

    channel_id: Optional[str] = None
    """Optional Discord channel ID where the confirmation was requested."""

    message_id: Optional[str] = None
    """Optional Discord message ID for the confirmation request."""


class PartyCharacter(BaseModel):
    """Represents a character in a party."""

    name: str
    """The character's name."""

    role: str
    """The character's role or class (e.g., 'Netrunner', 'Solo')."""

    gear_preferences: List[str] = Field(default_factory=list)
    """List of preferred gear types or items."""

    notes: Optional[str] = None
    """Additional notes about the character."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage."""
        return {
            "name": self.name,
            "role": self.role,
            "gear_preferences": self.gear_preferences,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartyCharacter":
        """Create a PartyCharacter from a dictionary."""
        return cls(
            name=data["name"],
            role=data["role"],
            gear_preferences=data.get("gear_preferences", []),
            notes=data.get("notes")
        )


class FileMetadata(BaseModel):
    """Metadata for a processed file in the knowledge graph."""

    file_path: str
    """The path to the file."""

    checksum: str
    """MD5 or SHA checksum of the file content."""

    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    """ISO format timestamp of when the file was processed."""

    chunk_count: int = 0
    """Number of chunks created from this file."""

    file_type: Optional[str] = None
    """The type/category of the file (e.g., 'rulebook', 'adventure')."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage."""
        return {
            "file_path": self.file_path,
            "checksum": self.checksum,
            "processed_at": self.processed_at,
            "chunk_count": self.chunk_count,
            "file_type": self.file_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        """Create FileMetadata from a dictionary."""
        return cls(
            file_path=data["file_path"],
            checksum=data["checksum"],
            processed_at=data.get("processed_at", datetime.now().isoformat()),
            chunk_count=data.get("chunk_count", 0),
            file_type=data.get("file_type")
        )


class UserMemory(BaseModel):
    """Long-term memory data for a user."""

    user_id: str
    """The user identifier."""

    interactions: List[str] = Field(default_factory=list)
    """Notable interaction patterns or behaviors."""

    preferences: List[str] = Field(default_factory=list)
    """User preferences and settings."""

    topics: List[str] = Field(default_factory=list)
    """Topics the user has shown interest in."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage."""
        return {
            "interactions": self.interactions,
            "preferences": self.preferences,
            "topics": self.topics
        }

    @classmethod
    def from_dict(cls, user_id: str, data: Dict[str, Any]) -> "UserMemory":
        """Create UserMemory from a dictionary."""
        return cls(
            user_id=user_id,
            interactions=data.get("interactions", []),
            preferences=data.get("preferences", []),
            topics=data.get("topics", [])
        )


class PartyData(BaseModel):
    """Complete data for a party including all characters."""

    party_id: str
    """The party identifier."""

    characters: List[PartyCharacter] = Field(default_factory=list)
    """List of characters in this party."""

    def add_character(self, character: PartyCharacter) -> bool:
        """
        Add or update a character in the party.

        Args:
            character: The character to add/update

        Returns:
            True if new character added, False if existing updated
        """
        for i, existing in enumerate(self.characters):
            if existing.name.lower() == character.name.lower():
                self.characters[i] = character
                return False
        self.characters.append(character)
        return True

    def remove_character(self, name: str) -> bool:
        """
        Remove a character from the party.

        Args:
            name: The character name to remove

        Returns:
            True if character was removed, False if not found
        """
        for i, character in enumerate(self.characters):
            if character.name.lower() == name.lower():
                self.characters.pop(i)
                return True
        return False

    def get_character(self, name: str) -> Optional[PartyCharacter]:
        """
        Get a character by name (case-insensitive).

        Args:
            name: The character name to find

        Returns:
            The character if found, None otherwise
        """
        for character in self.characters:
            if character.name.lower() == name.lower():
                return character
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage."""
        return {
            "characters": [char.to_dict() for char in self.characters]
        }

    @classmethod
    def from_dict(cls, party_id: str, data: Dict[str, Any]) -> "PartyData":
        """Create PartyData from a dictionary."""
        characters = [
            PartyCharacter.from_dict(char_data)
            for char_data in data.get("characters", [])
        ]
        return cls(party_id=party_id, characters=characters)

class ToolRequest:
    def __init__(self, answer: str, tool_name: str, tool_arguments: Dict[str, Any], confirmation_message: Optional[str] = None):
        self.answer = answer
        self.confirmation_message = confirmation_message        
        self.arguments = tool_arguments
        self.name = tool_name
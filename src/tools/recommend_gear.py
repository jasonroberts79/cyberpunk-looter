"""Tool handler for gear recommendations."""

from typing import Dict, Any, List
from anthropic.types import ToolParam, Message
from tools.base import ToolHandler, ToolExecutionResult
from prompt_library import (
    create_gear_recommendation_system_prompt,
    create_gear_recommendation_user_prompt,
)
from config import LLMConfig


class RecommendGearTool(ToolHandler):
    """
    Handler for AI-powered gear distribution recommendations.

    This is a complex tool that uses the LLM to generate recommendations
    based on party composition and loot description.
    """

    def __init__(
        self,
        party_repository: Any,  # PartyRepository
        context_provider: Any,  # GraphRAGSystem
        memory_provider: Any,  # UnifiedMemorySystem
        llm_client: Any,  # Anthropic
        config: LLMConfig = LLMConfig()
    ) -> None:
        """
        Initialize the tool handler.

        Args:
            party_repository: Repository for party data operations
            context_provider: Provider for RAG context retrieval
            memory_provider: Provider for conversation memory
            llm_client: LLM client for making API calls
            config: LLM configuration settings
        """
        self.party_repository = party_repository
        self.context_provider = context_provider
        self.memory_provider = memory_provider
        self.llm_client = llm_client
        self.config = config

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "recommend_gear"

    @property
    def requires_confirmation(self) -> bool:
        """This tool does not require confirmation."""
        return False

    def get_tool_definition(self) -> ToolParam:
        """Get the tool definition for the LLM API."""
        return {
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
        }

    def validate_arguments(
        self,
        arguments: Dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Validate the tool arguments."""
        loot_desc = arguments.get("loot_description")

        if not loot_desc or not isinstance(loot_desc, str) or not loot_desc.strip():
            return False, "Loot description is required and must be a non-empty string"

        excluded = arguments.get("excluded_characters")
        if excluded is not None:
            if not isinstance(excluded, list):
                return False, "Excluded characters must be a list"
            if not all(isinstance(item, str) for item in excluded):
                return False, "All excluded character names must be strings"

        return True, None

    def execute(
        self,
        arguments: Dict[str, Any],
        user_id: str,
        party_id: str
    ) -> ToolExecutionResult:
        """Execute the gear recommendation tool."""
        loot_description = arguments.get("loot_description", "")
        excluded_characters = arguments.get("excluded_characters", [])

        try:
            recommendation = self._generate_recommendation(
                user_id=user_id,
                party_id=party_id,
                loot_description=loot_description,
                excluded_characters=excluded_characters
            )

            return ToolExecutionResult(
                success=True,
                message=recommendation,
                should_update_memory=True,
                metadata={
                    "loot_description": loot_description,
                    "excluded_count": len(excluded_characters)
                }
            )

        except Exception as e:
            error_msg = str(e)
            return ToolExecutionResult(
                success=False,
                message=f"Error generating recommendations: {error_msg}",
                should_update_memory=False
            )

    def _generate_recommendation(
        self,
        user_id: str,
        party_id: str,
        loot_description: str,
        excluded_characters: List[str]
    ) -> str:
        """
        Generate gear recommendation using the LLM.

        Args:
            user_id: The user identifier
            party_id: The party identifier
            loot_description: Description of the loot
            excluded_characters: Characters to exclude

        Returns:
            The recommendation text
        """
        # Get all party members
        all_chars = self.party_repository.get_party_characters(party_id)

        # Handle empty party case
        if not all_chars:
            return (
                "You don't have any party members registered yet. "
                "Please add party members first."
            )

        # Filter out excluded characters
        if excluded_characters:
            excluded_lower = [name.lower() for name in excluded_characters]
            all_chars = [
                char for char in all_chars
                if char["name"].lower() not in excluded_lower
            ]

        if not all_chars:
            return "No party members available after exclusions."

        # Get relevant context from knowledge graph
        context = self.context_provider.get_context_for_query(
            query=f"Look up information related to this gear: {loot_description}",
            k=self.config.default_context_k
        )

        # Build party context for the LLM
        party_context = self._build_party_context(all_chars)

        # Create the user prompt
        user_prompt = create_gear_recommendation_user_prompt(
            loot_description, party_context, context
        )

        # Build messages with conversation history
        messages = self._build_messages(user_prompt, user_id)

        # Call the LLM for recommendations
        response = self.llm_client.messages.create(
            max_tokens=self.config.max_tokens,
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            system=create_gear_recommendation_system_prompt(),
        )

        # Extract the recommendation
        recommendation = self._extract_answer(response)

        if recommendation:
            self.memory_provider.add_message(user_id, "assistant", recommendation)
            return recommendation
        else:
            return "I couldn't generate recommendations."

    def _build_party_context(self, characters: List[Dict[str, Any]]) -> str:
        """Build a formatted party context string."""
        party_context = "Party Members:\n"
        for char in characters:
            party_context += f"- {char['name']} ({char['role']})"
            if char.get("gear_preferences"):
                party_context += f" - Prefers: {', '.join(char['gear_preferences'])}"
            party_context += "\n"
        return party_context

    def _build_messages(self, user_prompt: str, user_id: str) -> List[Dict[str, str]]:
        """Build message array from conversation history."""
        short_term_context = self.memory_provider.get_messages(user_id)
        messages = []

        if short_term_context:
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in short_term_context
                if m.get("content") is not None
            ]

        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _extract_answer(self, response: Message) -> str | None:
        """Extract text answer from LLM response."""
        text_answer = [r for r in response.content if r.type == "text"]
        if text_answer:
            return text_answer[-1].text
        return None

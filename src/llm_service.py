"""LLM Service - Decoupled LLM functionality for testing and reuse."""

import tool_system
from typing import Optional, List, Dict
from anthropic.types import Message, MessageParam
from graphrag_system import GraphRAGSystem
from memory_system import MemorySystem
from anthropic import Anthropic
from prompt_library import (
    GAME_CONTEXT,
    create_main_system_prompt,
    create_gear_recommendation_system_prompt,
    create_gear_recommendation_user_prompt,
)
from app_config import get_config_value


class LLMService:
    """
    Service class that encapsulates all LLM functionality.
    This class is independent of Discord and can be used for functional testing.
    """

    def __init__(self, memory_system: MemorySystem) -> None:
        """
        Initialize the LLM service with required dependencies.

        """

        llm_model = get_config_value("OPENAI_MODEL")        
        llm_api_key = get_config_value("OPENAI_API_KEY")
        self.claude = Anthropic(api_key=llm_api_key)
        self.graphrag_system = GraphRAGSystem()
        self.memory_system = memory_system
        self.model_name = llm_model
        self.game_context = GAME_CONTEXT

    async def initialize(self, force_reindex: bool = False):
        await self.graphrag_system.build_knowledge_graph(force_rebuild=force_reindex)

    def process_query(self, user_id: str, party_id: str, question: str) -> Message:
        """
        Process a user query and return the response.

        Args:
            user_id: The user ID
            party_id: The party ID
            question: The user's question

        Returns:
            - response_object: The LLM response object
        """
        # Update memory
        self.memory_system.update_long_term(user_id, "interaction", None)

        # Get context from GraphRAG
        context = self.graphrag_system.get_context_for_query(question, k=10)

        # Get user and party summaries
        user_summary = self.memory_system.get_user_summary(user_id)
        party_summary = self.memory_system.get_party_summary(party_id)

        input_messages = self.build_messages(question, user_id)
        input_messages = [m for m in input_messages if m["content"] is not None]
        # Call OpenAI API
        response = self.claude.messages.create(
            max_tokens=20000,
            model=self.model_name,
            messages=input_messages,
            temperature=0.6,
            tools=tool_system.get_tool_definitions(),
            tool_choice={"type": "auto", "disable_parallel_tool_use": False},
            system=create_main_system_prompt(context, user_summary, party_summary),
        )

        self.memory_system.add_to_short_term(user_id, "user", question)
        answer = self.get_answer(response)
        if(answer is not None):
            self.memory_system.add_to_short_term(user_id, "assistant", answer)

        return response

    def get_answer(self, response) -> Optional[str]:
        text_answer = [r for r in response.content if r.type == "text"]

        if text_answer:
            return text_answer[-1].text
        return None

    def execute_recommend_gear(
        self,
        user_id: str,
        party_id: str,
        loot_description: str,
        excluded_characters: List[str],
    ) -> str:
        """
        Execute gear recommendation and return the recommendation text.

        Args:
            user_id: The user ID
            party_id: The party ID
            loot_description: Description of the loot to distribute
            excluded_characters: List of character names to exclude

        Returns:
            The recommendation text
        """
        # Get all party members
        all_chars = self.memory_system.list_party_characters(party_id)

        # Handle empty party case
        if not all_chars:
            return (
                "You don't have any party members registered yet. Please add party members first."
            )

        # Filter out excluded characters
        if excluded_characters:
            excluded_lower = [name.lower() for name in excluded_characters]
            all_chars = [char for char in all_chars if char["name"].lower() not in excluded_lower]

        if not all_chars:
            return "No party members available after exclusions."

        context = self.graphrag_system.get_context_for_query(
            f"""Look up information related to this gear: {loot_description}""", k=10
        )

        # Build party context for the LLM
        party_context = "Party Members:\n"
        for char in all_chars:
            party_context += f"- {char['name']} ({char['role']})"
            if char.get("gear_preferences"):
                party_context += f" - Prefers: {', '.join(char['gear_preferences'])}"
            party_context += "\n"

        # Create the user prompt
        user_prompt = create_gear_recommendation_user_prompt(
            loot_description, party_context, context
        )

        input_messages = self.build_messages(user_prompt, user_id)

        try:
            response = self.claude.messages.create(
                max_tokens=20000,
                model=self.model_name,
                messages=input_messages,
                temperature=0.6,
                tools=tool_system.get_tool_definitions(),
                tool_choice={"type": "auto", "disable_parallel_tool_use": False},
                system=create_gear_recommendation_system_prompt(),
            )

            recommendation = self.get_answer(response)
            if recommendation:
                self.memory_system.add_to_short_term(user_id, "assistant", recommendation)
            else:
                recommendation = "I couldn't generate recommendations."

            return recommendation

        except Exception as e:
            error_msg = str(e)
            return f"Error generating recommendations: {error_msg}"

    def execute_tool_action(
        self, tool_name: str, tool_arguments: Dict, user_id: str, party_id: str
    ) -> str:
        """
        Execute a tool action and return the result.

        Args:
            tool_name: The action to execute (e.g., "add_party_character")
            tool_arguments: The parameters for the action
            user_id: The user ID
            party_id: The party ID

        Returns:
            The tool response
        """
        try:
            if tool_name == "add_party_character":
                tool_response = self._handle_add_party_character(
                    tool_arguments, party_id
                )
            elif tool_name == "remove_party_character":
                tool_response = self._handle_remove_party_character(
                    tool_arguments, party_id
                )
            elif tool_name == "view_party_members":
                tool_response = self._handle_view_party_members(party_id)
            elif tool_name == "recommend_gear":
                tool_response = self._handle_recommend_gear(
                    tool_arguments, user_id, party_id
                )
            else:
                tool_response = self._handle_unknown_action(tool_name)

            self.memory_system.add_to_short_term(user_id, "assistant", tool_response)
            return tool_response
        except Exception as e:
            return f"Error executing action: {str(e)}"

    def _handle_add_party_character(
        self, tool_arguments: Dict, party_id: str
    ) -> str:
        """
        Handle adding a party character.

        Args:
            tool_arguments: The parameters containing name, role, and gear_preferences
            party_id: The party ID

        Returns:
            The response message
        """
        name = tool_arguments.get("name", "")
        role = tool_arguments.get("role", "")
        gear_preferences = tool_arguments.get("gear_preferences", [])

        is_new = self.memory_system.add_party_character(
            party_id, name, role, gear_preferences
        )

        if is_new:
            return f"**{name}** has been added to your party!"
        else:
            return f"**{name}** has been updated in your party!"

    def _handle_remove_party_character(
        self, tool_arguments: Dict, party_id: str
    ) -> str:
        """
        Handle removing a party character.

        Args:
            tool_arguments: The parameters containing name
            party_id: The party ID

        Returns:
            The response message
        """
        name = tool_arguments.get("name", "")
        success = self.memory_system.remove_party_character(party_id, name)

        if success:
            return f"**{name}** has been removed from your party."
        else:
            return f"Character **{name}** not found in your party."

    def _handle_view_party_members(self, party_id: str) -> str:
        """
        Handle viewing party members.

        Args:
            party_id: The party ID

        Returns:
            The formatted list of party members
        """
        characters = self.memory_system.list_party_characters(party_id)

        if not characters or len(characters) == 0:
            return "You don't have any party members yet."

        tool_response = "**Your Party Members:**\n\n"
        for char in characters:
            tool_response += f"**{char['name']}**\n"
            tool_response += f"• Role: {char['role']}\n"
            if char.get("gear_preferences"):
                tool_response += (
                    f"• Gear Preferences: {', '.join(char['gear_preferences'])}\n"
                )
            else:
                tool_response += "• Gear Preferences: None\n"
            tool_response += "\n"

        return tool_response

    def _handle_recommend_gear(
        self, tool_arguments: Dict, user_id: str, party_id: str
    ) -> str:
        """
        Handle gear recommendation.

        Args:
            tool_arguments: The parameters containing loot_description and excluded_characters
            user_id: The user ID
            party_id: The party ID

        Returns:
            The recommendation text
        """
        loot_description = tool_arguments.get("loot_description", "")
        excluded_characters = tool_arguments.get("excluded_characters", [])

        return self.execute_recommend_gear(
            user_id, party_id, loot_description, excluded_characters
        )

    def _handle_unknown_action(self, tool_name: str) -> str:
        """
        Handle unknown tool actions.

        Args:
            tool_name: The unknown tool name

        Returns:
            Error message for unknown action
        """
        return f"Unknown action: {tool_name}"

    def build_messages(self, user_prompt, user_id) -> list[MessageParam]:
        short_term_context = self.memory_system.get_short_term_context(user_id, max_messages=10)
        input_messages: list[MessageParam] = []
        if short_term_context is not None and hasattr(short_term_context, "__iter__"):
            input_messages = [
                {"role": m["role"], "content": m["content"]} for m in short_term_context
            ]

        input_messages.append({"role": "user", "content": user_prompt})
        return input_messages

    def extract_tool_calls(self, response) -> Optional[List[Dict]]:
        """
        Extract tool calls from API response.

        Args:
            response: The API response object

        Returns:
            Tuple of (has_tool_calls, tool_calls_list)
        """
        try:
            # Check for Anthropic content blocks format
            if hasattr(response, "content") and response.content:
                tool_calls = []
                import json

                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        # Anthropic format
                        tool_calls.append(
                            {
                                "name": block.name,
                                "arguments": json.dumps(block.input)
                                if isinstance(block.input, dict)
                                else block.input,
                            }
                        )
                return tool_calls

            return None
        except (AttributeError, IndexError) as e:
            print(f"Tool call extraction error: {e}")
            return None

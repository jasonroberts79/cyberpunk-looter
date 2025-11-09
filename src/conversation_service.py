"""
Conversation service for orchestrating LLM interactions.

This module provides a clean interface for processing user queries
through the LLM, managing context, memory, and tool definitions.
"""

from typing import List, Optional, Any
from anthropic import Anthropic
from anthropic.types import Message, MessageParam
from message_builder import MessageBuilder
from prompt_library import create_main_system_prompt
from config import LLMConfig
from exceptions import LLMServiceError


class ConversationService:
    """
    Service for managing LLM conversations.

    This class orchestrates the interaction between the LLM, context providers,
    memory systems, and tool definitions to process user queries.
    """

    def __init__(
        self,
        anthropic_client: Anthropic,
        context_provider: Any,  # GraphRAGSystem
        memory_provider: Any,  # UnifiedMemorySystem
        party_repository: Any,  # PartyRepository
        message_builder: MessageBuilder,
        config: LLMConfig = LLMConfig()
    ) -> None:
        """
        Initialize the conversation service.

        Args:
            anthropic_client: Anthropic API client
            context_provider: Provider for RAG context retrieval
            memory_provider: Provider for conversation memory
            user_memory_provider: Provider for long-term user memory
            party_repository: Repository for party data
            message_builder: Builder for constructing message arrays
            config: LLM configuration settings
        """
        self.client = anthropic_client
        self.context_provider = context_provider
        self.memory_provider = memory_provider
        self.party_repository = party_repository
        self.message_builder = message_builder
        self.config = config

    def process_query(
        self,
        user_id: str,
        party_id: str,
        question: str,
        tool_definitions: Optional[List] = None
    ) -> Message:
        """
        Process a user query and return the LLM response.

        This method:
        1. Updates user interaction count
        2. Retrieves relevant context from knowledge graph
        3. Gets user and party summaries
        4. Builds message array with conversation history
        5. Calls the LLM API
        6. Stores the interaction in memory

        Args:
            user_id: The user identifier
            party_id: The party identifier
            question: The user's question
            tool_definitions: Optional list of tool definitions for the LLM

        Returns:
            The LLM response message

        Raises:
            LLMServiceError: If the LLM API call fails
        """
        # Update user interaction count
        self.memory_provider.update_long_term(user_id, "interaction", "")

        # Get context from GraphRAG
        context = self.context_provider.get_context_for_query(
            query=question,
            k=self.config.default_context_k
        )

        # Get user and party summaries
        user_summary = self.memory_provider.get_long_term_summary(user_id)
        party_summary = self.party_repository.get_party_summary(party_id)

        # Build messages with conversation history
        messages = self.message_builder.build_messages(question, user_id)

        # Create system prompt with all context
        system_prompt = create_main_system_prompt(context, user_summary, party_summary)

        try:
            # Call the LLM API
            if tool_definitions:
                response = self.client.messages.create(
                    max_tokens=self.config.max_tokens,
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    tools=tool_definitions,
                    tool_choice={"type": "auto", "disable_parallel_tool_use": False},
                    system=system_prompt,
                )
            else:
                response = self.client.messages.create(
                    max_tokens=self.config.max_tokens,
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    system=system_prompt,
                )

            # Store the interaction in memory
            self.memory_provider.add_message(user_id, "user", question)

            # Extract and store the answer if present
            answer = self._extract_answer(response)
            if answer is not None:
                self.memory_provider.add_message(user_id, "assistant", answer)

            return response

        except Exception as e:
            raise LLMServiceError(f"Failed to process query: {e}") from e

    def _extract_answer(self, response: Message) -> Optional[str]:
        """
        Extract text answer from LLM response.

        Args:
            response: The LLM response message

        Returns:
            The text answer, or None if no text content found
        """
        text_blocks = [block for block in response.content if block.type == "text"]
        if text_blocks:
            return text_blocks[-1].text
        return None

    async def initialize(self, force_reindex: bool = False) -> None:
        """
        Initialize the conversation service.

        This method performs any necessary setup, such as
        building the knowledge graph.

        Args:
            force_reindex: Whether to force a complete reindex of the knowledge graph
        """
        await self.context_provider.build_knowledge_graph(
            directory="knowledge",
            force_rebuild=force_reindex
        )

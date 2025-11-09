"""
Dependency injection container for the cyberpunk-looter application.

This module provides factory functions to create and wire up all
application dependencies, eliminating global state and tight coupling.
"""

from anthropic import Anthropic
from app_storage import AppStorage
from config import AppConfig
from conversation_memory import ConversationMemory
from user_memory_repository import UserMemoryRepository
from party_repository import PartyRepository
from unified_memory_system import UnifiedMemorySystem
from message_builder import MessageBuilder
from conversation_service import ConversationService
from tool_execution_service import ToolExecutionService
from tools.registry import ToolRegistry
from tools.add_party_character import AddPartyCharacterTool
from tools.remove_party_character import RemovePartyCharacterTool
from tools.view_party_members import ViewPartyMembersTool
from tools.recommend_gear import RecommendGearTool
from graphrag_system import GraphRAGSystem
from bot_reactions import DiscordReactions


class Container:
    """
    Dependency injection container.

    This class provides a centralized place to create and manage
    application dependencies, ensuring proper initialization order
    and dependency injection throughout the application.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """
        Initialize the container.

        Args:
            config: Application configuration (created from environment if not provided)
        """
        self.config = config or AppConfig()

        # Lazy initialization - components are created on first access
        self._storage: AppStorage | None = None
        self._conversation_memory: ConversationMemory | None = None
        self._user_memory_repository: UserMemoryRepository | None = None
        self._unified_memory_system: UnifiedMemorySystem | None = None
        self._party_repository: PartyRepository | None = None
        self._message_builder: MessageBuilder | None = None
        self._anthropic_client: Anthropic | None = None
        self._graphrag_system: GraphRAGSystem | None = None
        self._tool_registry: ToolRegistry | None = None
        self._tool_execution_service: ToolExecutionService | None = None
        self._conversation_service: ConversationService | None = None
        self._reactions_handler: "DiscordReactions | None" = None  # For Discord bot reactions

    @property
    def storage(self) -> AppStorage:
        """Get or create the storage instance."""
        if self._storage is None:
            if not self.config.gcs_bucket_name:
                raise ValueError("GCS_BUCKET_NAME not configured")
            self._storage = AppStorage(bucket_name=self.config.gcs_bucket_name)
        return self._storage

    @property
    def conversation_memory(self) -> ConversationMemory:
        """Get or create the conversation memory instance."""
        if self._conversation_memory is None:
            self._conversation_memory = ConversationMemory(
                config=self.config.memory
            )
        return self._conversation_memory

    @property
    def user_memory_repository(self) -> UserMemoryRepository:
        """Get or create the user memory repository instance."""
        if self._user_memory_repository is None:
            self._user_memory_repository = UserMemoryRepository(
                storage=self.storage,
                config=self.config.memory
            )
        return self._user_memory_repository

    @property
    def unified_memory_system(self) -> UnifiedMemorySystem:
        """Get or create the unified memory system instance."""
        if self._unified_memory_system is None:
            self._unified_memory_system = UnifiedMemorySystem(
                conversation_memory=self.conversation_memory,
                user_memory_repository=self.user_memory_repository,
                config=self.config.memory
            )
        return self._unified_memory_system

    @property
    def party_repository(self) -> PartyRepository:
        """Get or create the party repository instance."""
        if self._party_repository is None:
            self._party_repository = PartyRepository(
                storage=self.storage,
                config=self.config.memory
            )
        return self._party_repository

    @property
    def message_builder(self) -> MessageBuilder:
        """Get or create the message builder instance."""
        if self._message_builder is None:
            self._message_builder = MessageBuilder(
                memory_provider=self.conversation_memory,
                config=self.config.memory
            )
        return self._message_builder

    @property
    def anthropic_client(self) -> Anthropic:
        """Get or create the Anthropic client instance."""
        if self._anthropic_client is None:
            if not self.config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._anthropic_client = Anthropic(api_key=self.config.anthropic_api_key)
        return self._anthropic_client

    @property
    def graphrag_system(self) -> GraphRAGSystem:
        """Get or create the GraphRAG system instance."""
        if self._graphrag_system is None:
            self._graphrag_system = GraphRAGSystem(self.storage, self.config)
        return self._graphrag_system

    @property
    def tool_registry(self) -> ToolRegistry:
        """Get or create the tool registry instance with all tools registered."""
        if self._tool_registry is None:
            registry = ToolRegistry()

            # Register all tools
            registry.register(AddPartyCharacterTool(self.party_repository))
            registry.register(RemovePartyCharacterTool(self.party_repository))
            registry.register(ViewPartyMembersTool(self.party_repository))
            registry.register(RecommendGearTool(
                party_repository=self.party_repository,
                context_provider=self.graphrag_system,
                memory_provider=self.unified_memory_system,
                llm_client=self.anthropic_client,
                config=self.config.llm
            ))

            self._tool_registry = registry
        return self._tool_registry

    @property
    def tool_execution_service(self) -> ToolExecutionService:
        """Get or create the tool execution service instance."""
        if self._tool_execution_service is None:
            self._tool_execution_service = ToolExecutionService(
                registry=self.tool_registry,
                memory_provider=self.unified_memory_system
            )
        return self._tool_execution_service

    @property
    def conversation_service(self) -> ConversationService:
        """Get or create the conversation service instance."""
        if self._conversation_service is None:
            self._conversation_service = ConversationService(
                anthropic_client=self.anthropic_client,
                context_provider=self.graphrag_system,
                memory_provider=self.unified_memory_system,
                party_repository=self.party_repository,
                message_builder=self.message_builder,
                config=self.config.llm
            )
        return self._conversation_service

    @property
    def reaction_handler(self) -> DiscordReactions:
        if(self._reactions_handler is None):
            self._reactions_handler = DiscordReactions(self.tool_execution_service)
        return self._reactions_handler

    async def initialize(self, force_reindex: bool = False) -> None:
        """
        Initialize all components that require async setup.

        Args:
            force_reindex: Whether to force a complete reindex of the knowledge graph
        """
        await self.conversation_service.initialize(force_reindex=force_reindex)


# Global container instance (singleton pattern)
_container: Container | None = None


def get_container() -> Container:
    """
    Get the global container instance.

    Returns:
        The singleton container instance
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """
    Reset the global container instance.

    Useful for testing or when configuration changes.
    """
    global _container
    _container = None

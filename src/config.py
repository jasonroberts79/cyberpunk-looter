"""
Configuration for application settings.

This module centralizes all configuration values and magic numbers
that were previously scattered throughout the codebase.
"""

from pydantic import BaseModel
import os
from exceptions import ConfigurationError

class LLMConfig(BaseModel):
    """Configuration for LLM service."""

    max_tokens: int = 20000
    """Maximum tokens to generate in a single LLM call."""

    temperature: float = 0.6
    """Sampling temperature for LLM responses (0.0 = deterministic, 1.0 = creative)."""

    default_context_k: int = 10
    """Default number of relevant context documents to retrieve from RAG."""

    model: str = "claude-sonnet-4-20250514"
    """The Claude model to use for LLM calls."""


class MemoryConfig(BaseModel):
    """Configuration for memory management."""

    max_short_term_messages: int = 10
    """Maximum number of messages to keep in short-term conversation history."""

    conversation_storage_file: str = "conversations.json"
    """Filename for storing conversation history."""

    long_term_storage_file: str = "long_term_memory.json"
    """Filename for storing long-term user memory."""

    party_storage_file: str = "party_data.json"
    """Filename for storing party data."""


class GraphRAGConfig(BaseModel):
    """Configuration for Graph RAG system."""

    embeddings_model: str = "text-embedding-3-small"

    chunk_size: int = 1000
    """Size of text chunks for document processing."""

    chunk_overlap: int = 200
    """Number of overlapping characters between chunks."""

    embedding_dimensions: int = 1536
    """Dimensionality of embedding vectors."""

    default_retrieval_k: int = 10
    """Default number of documents to retrieve for a query."""

    max_retries: int = 3
    """Maximum number of retry attempts for database operations."""

    retry_delay_seconds: float = 1.0
    """Initial delay between retries (exponentially backed off)."""

    batch_size: int = 10
    """Number of chunks to process in a single batch."""

    file_tracking_file: str = "processed_files.json"
    """Filename for tracking processed files and their checksums."""

    vector_index_name: str = "document_embeddings"

    kb_path: str = "knowledge_base"
class DiscordBotConfig(BaseModel):
    """Configuration for Discord bot behavior."""

    max_message_length: int = 2000
    """Maximum length of a Discord message before splitting."""

    confirmation_timeout_seconds: int = 60
    """Timeout for tool confirmation reactions."""

    approval_emoji: str = "👍"
    """Emoji for approving tool actions."""

    rejection_emoji: str = "👎"
    """Emoji for rejecting tool actions."""

    typing_indicator: bool = True
    """Whether to show typing indicator while processing."""


class AppConfig:
    """Root application configuration."""

    def __init__(self):

        self.llm: LLMConfig = LLMConfig()
        self.memory: MemoryConfig = MemoryConfig()
        self.graphrag: GraphRAGConfig = GraphRAGConfig()
        self.discord: DiscordBotConfig = DiscordBotConfig()


        # Environment-based configuration (loaded from env vars)
        self.discord_token=self._get_config_value("DISCORD_BOT_TOKEN")
        
        self.neo4j_uri=self._get_config_value("NEO4J_URI")
        self.neo4j_username=self._get_config_value("NEO4J_USERNAME")
        self.neo4j_password=self._get_config_value("NEO4J_PASSWORD")
        
        self.anthropic_api_key=self._get_config_value("OPENAI_API_KEY")        
        self.llm_model = self._get_config_value("OPENAI_MODEL")
        self.llm_url = self._get_config_value("OPENAI_BASE_URL")

        self.embeddings_key = self._get_config_value("OPENAI_EMBEDDINGS_KEY")
        self.embeddings_url = self._get_config_value("OPENAI_EMBEDDINGS_BASE_URL")

        self.gcs_bucket_name=self._get_config_value("GCS_BUCKET_NAME")
        

    def _get_config_value(self, key: str) -> str:
        """
        Get a required configuration value from environment.

        Args:
            key: The environment variable name

        Returns:
            The configuration value (guaranteed non-empty)

        Raises:
            ConfigurationError: If the variable is missing or empty
        """
        value = os.getenv(key)
        if not value or value.strip() == "":
            raise ConfigurationError(
                f"Required environment variable '{key}' is missing or empty"
            )
        return value.strip()
# Default configuration instance for convenience
DEFAULT_CONFIG = AppConfig()

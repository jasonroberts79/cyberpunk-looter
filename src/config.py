"""
Configuration for application settings.

This module centralizes all configuration values and magic numbers
that were previously scattered throughout the codebase.
"""

from typing import Optional
from pydantic import BaseModel


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


class AppConfig(BaseModel):
    """Root application configuration."""

    llm: LLMConfig = LLMConfig()
    memory: MemoryConfig = MemoryConfig()
    graphrag: GraphRAGConfig = GraphRAGConfig()
    discord: DiscordBotConfig = DiscordBotConfig()

    # Environment-based configuration (loaded from env vars)
    discord_token: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    neo4j_uri: Optional[str] = None
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None
    gcs_bucket_name: Optional[str] = None

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """
        Create configuration from environment variables.

        Returns:
            AppConfig instance populated from environment

        Raises:
            ConfigurationError: If required environment variables are missing
        """
        from app_config import get_config_value

        return cls(
            discord_token=get_config_value("DISCORD_TOKEN"),
            anthropic_api_key=get_config_value("ANTHROPIC_API_KEY"),
            openai_api_key=get_config_value("OPENAI_API_KEY"),
            neo4j_uri=get_config_value("NEO4J_URI"),
            neo4j_username=get_config_value("NEO4J_USERNAME"),
            neo4j_password=get_config_value("NEO4J_PASSWORD"),
            gcs_bucket_name=get_config_value("GCS_BUCKET_NAME"),
        )


# Default configuration instance for convenience
DEFAULT_CONFIG = AppConfig()

"""
Custom exceptions for the cyberpunk-looter application.

This module defines application-specific exceptions for better
error handling and more meaningful error messages.
"""


class CyberpunkLooterError(Exception):
    """Base exception for all cyberpunk-looter errors."""
    pass


class ConfigurationError(CyberpunkLooterError):
    """Raised when configuration is missing or invalid."""
    pass


class StorageError(CyberpunkLooterError):
    """Raised when storage operations fail."""
    pass


class ToolExecutionError(CyberpunkLooterError):
    """Raised when tool execution fails."""
    pass


class MemoryError(CyberpunkLooterError):
    """Raised when memory operations fail."""
    pass


class GraphRAGError(CyberpunkLooterError):
    """Raised when GraphRAG operations fail."""
    pass


class LLMServiceError(CyberpunkLooterError):
    """Raised when LLM service operations fail."""
    pass


class ValidationError(CyberpunkLooterError):
    """Raised when data validation fails."""
    pass


class NotFoundException(CyberpunkLooterError):
    """Raised when a requested resource is not found."""
    pass

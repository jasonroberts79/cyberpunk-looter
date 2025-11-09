import os
from exceptions import ConfigurationError


def get_config_value(key: str) -> str:
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

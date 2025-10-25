import os
import sys


def get_config_value(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        print(f"ERROR: Environment variable {key} is missing!")
        sys.exit(1)
    assert value is not None  # Type narrowing for type checker
    return value.strip()

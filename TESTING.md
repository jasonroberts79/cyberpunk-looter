# Testing Guide

Comprehensive testing documentation for the cyberpunk-looter project.

## Overview

Test suite using **pytest** with:
- Unit tests for individual components
- Integration tests for system interactions
- Mocking for external dependencies (Neo4j, OpenAI, etc.)
- Code coverage reporting
- Async test support

## Quick Start

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_graphrag_system.py  # Tests for GraphRAGSystem
└── __init__.py              # Package initialization
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Verbose output
uv run pytest -v

# Specific test file
uv run pytest tests/test_graphrag_system.py

# Specific test class
uv run pytest tests/test_graphrag_system.py::TestConnectionManagement

# Specific test function
uv run pytest tests/test_graphrag_system.py::TestConnectionManagement::test_ensure_connection_healthy

# Using markers
uv run pytest -m unit              # Unit tests only
uv run pytest -m integration       # Integration tests only
uv run pytest -m "not slow"        # Skip slow tests

# Coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Parallel execution (faster)
uv run pytest -n auto

## Test Coverage

Our test suite covers:

### GraphRAGSystem Tests (`test_graphrag_system.py`)

1. **Initialization Tests** (`TestGraphRAGSystemInit`)
   - Successful initialization
   - Custom retry parameters
   - Connection establishment

2. **Connection Management Tests** (`TestConnectionManagement`)
   - Connection health verification
   - Retry logic with exponential backoff
   - Connection failure recovery
   - Exhausted retry attempts

3. **File Metadata Tests** (`TestFileMetadata`)
   - SHA256 checksum computation
   - New file detection
   - Unchanged file detection
   - Modified file detection

4. **File Operations Tests** (`TestFileCategorizationAndLoading`)
   - File categorization
   - Force rebuild behavior
   - PDF document loading
   - Markdown document loading

5. **Database Operations Tests** (`TestDatabaseOperations`)
   - Deleted file removal
   - Chunk node creation
   - Retriever initialization

6. **Query Methods Tests** (`TestQueryMethods`)
   - Context queries
   - Search functionality
   - Error handling

## Writing New Tests

### Test File Structure

```python
"""Module docstring explaining what is being tested."""

import pytest
from unittest.mock import Mock, patch

class TestMyFeature:
    """Test suite for MyFeature."""

    @pytest.mark.unit
    def test_basic_functionality(self, mock_fixture):
        """Test basic functionality.

        This test verifies that...
        """
        # Arrange
        expected = "result"

        # Act
        result = my_function()

        # Assert
        assert result == expected
```

### Best Practices

1. **Use descriptive names**: Test names should clearly describe what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion per test**: Keep tests focused and simple
4. **Use fixtures**: Leverage pytest fixtures for setup/teardown
5. **Mock external dependencies**: Don't rely on external services
6. **Test edge cases**: Include tests for error conditions
7. **Document tests**: Add docstrings explaining test purpose

### Available Fixtures

From `conftest.py`:

- `mock_neo4j_driver` - Mocked Neo4j driver
- `mock_embeddings` - Mocked embeddings instance
- `mock_llm` - Mocked LLM instance
- `mock_storage` - Mocked AppStorage instance
- `temp_pdf_file` - Temporary PDF file
- `temp_md_file` - Temporary Markdown file
- `temp_knowledge_base` - Temporary knowledge base directory
- `sample_documents` - Sample Document objects
- `mock_text_splitter` - Mocked text splitter

## Continuous Integration

Tests run automatically via GitHub Actions on pull requests and pushes to `main`/`develop` branches.

See `.github/workflows/app-deploy.yml` for CI configuration.

## Troubleshooting

**Import Errors:**
```bash
uv sync --extra test
```

**Mock Path Issues:**
```python
@patch('graphrag_system.GraphDatabase')  # ✓ Correct
@patch('GraphDatabase')                   # ✗ Incorrect
```

**Real Neo4j Testing:**
```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password"
uv run pytest -m integration
```

## Coverage Goals

- Overall coverage: > 80%
- Critical paths: > 90%
- New code: > 85%

```bash
uv run pytest --cov=src --cov-report=term-missing
```

## Performance Testing

```bash
# Show 10 slowest tests
uv run pytest --durations=10
```

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

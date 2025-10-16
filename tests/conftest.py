"""Pytest configuration and fixtures for unit tests."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_neo4j_driver():
    """Provide a mocked Neo4j driver."""
    mock_driver = Mock()
    mock_driver.verify_connectivity = Mock()
    mock_driver.close = Mock()

    mock_session = Mock()
    mock_session.run = Mock()
    mock_driver.session = MagicMock(return_value=mock_session)

    return mock_driver


@pytest.fixture
def mock_embeddings():
    """Provide a mocked embeddings instance."""
    mock_emb = Mock()
    mock_emb.embed_query = Mock(return_value=[0.1] * 1536)
    return mock_emb


@pytest.fixture
def mock_llm():
    """Provide a mocked LLM instance."""
    return Mock()


@pytest.fixture
def mock_storage():
    """Provide a mocked AppStorage instance."""
    mock_store = Mock()
    mock_store.readdata = Mock(return_value=None)
    mock_store.writedata = Mock()
    return mock_store


@pytest.fixture
def temp_pdf_file(tmp_path):
    """Create a temporary PDF file for testing."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\ntest content")
    return pdf_file


@pytest.fixture
def temp_md_file(tmp_path):
    """Create a temporary Markdown file for testing."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test Markdown\n\nThis is test content.")
    return md_file


@pytest.fixture
def temp_knowledge_base(tmp_path):
    """Create a temporary knowledge base directory with test files."""
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()

    # Create test PDF
    pdf_file = kb_dir / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\ntest content")

    # Create test Markdown
    md_file = kb_dir / "test.md"
    md_file.write_text("# Test Document\n\nTest content.")

    return kb_dir


@pytest.fixture
def sample_documents():
    """Provide sample Document objects for testing."""
    from langchain.schema import Document

    return [
        Document(
            page_content="This is the first chunk of text.",
            metadata={
                "source": "/test/doc1.pdf",
                "filename": "doc1.pdf",
                "type": "pdf",
            },
        ),
        Document(
            page_content="This is the second chunk of text.",
            metadata={
                "source": "/test/doc1.pdf",
                "filename": "doc1.pdf",
                "type": "pdf",
            },
        ),
        Document(
            page_content="This is a markdown chunk.",
            metadata={
                "source": "/test/doc2.md",
                "filename": "doc2.md",
                "type": "markdown",
            },
        ),
    ]


@pytest.fixture
def mock_text_splitter():
    """Provide a mocked text splitter."""
    mock_splitter = Mock()
    mock_splitter.split_documents = Mock(return_value=[])
    return mock_splitter


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests."""
    yield
    # Cleanup happens automatically with pytest


# Pytest markers for organizing tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")

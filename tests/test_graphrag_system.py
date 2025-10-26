"""Unit tests for GraphRAGSystem."""

import pytest
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, AsyncMock
from neo4j.exceptions import ServiceUnavailable
from langchain.schema import Document

from src.graphrag_system import GraphRAGSystem


class TestGraphRAGSystemInit:
    """Test GraphRAGSystem initialization."""

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_init_success(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test successful initialization of GraphRAGSystem."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        assert system.driver is not None
        assert system.neo4j_uri == "bolt://localhost:7687"
        assert system.neo4j_username == "neo4j"
        assert system.neo4j_password == "password"
        mock_driver.verify_connectivity.assert_called_once()

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_init_with_custom_retry_params(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test initialization with custom retry parameters."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            max_retry_attempts=5,
            retry_delay=2.0,
        )

        assert system.max_retry_attempts == 5
        assert system.retry_delay == 2.0


class TestConnectionManagement:
    """Test connection management and retry logic."""

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_ensure_connection_healthy(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test _ensure_connection with healthy connection."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        # Should not raise any exception
        system._ensure_connection()
        assert mock_driver.verify_connectivity.call_count >= 1

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @patch("src.graphrag_system.time.sleep")
    def test_execute_with_retry_success_on_first_attempt(
        self, mock_sleep, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test _execute_with_retry succeeds on first attempt."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        mock_operation = Mock(return_value="success")
        result = system._execute_with_retry(mock_operation, "test operation")

        assert result == "success"
        mock_operation.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @patch("src.graphrag_system.time.sleep")
    def test_execute_with_retry_success_after_failure(
        self, mock_sleep, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test _execute_with_retry succeeds after initial failure."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            max_retry_attempts=3,
            retry_delay=0.1,
        )

        # First call fails, second succeeds
        mock_operation = Mock(side_effect=[ServiceUnavailable("Connection lost"), "success"])
        result = system._execute_with_retry(mock_operation, "test operation")

        assert result == "success"
        assert mock_operation.call_count == 2
        mock_sleep.assert_called()

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @patch("src.graphrag_system.time.sleep")
    def test_execute_with_retry_exhausts_attempts(
        self, mock_sleep, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test _execute_with_retry exhausts all retry attempts."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            max_retry_attempts=2,
            retry_delay=0.1,
        )

        mock_operation = Mock(side_effect=ServiceUnavailable("Connection lost"))

        with pytest.raises(ServiceUnavailable):
            system._execute_with_retry(mock_operation, "test operation")

        assert mock_operation.call_count == 2


class TestFileMetadata:
    """Test file metadata and tracking."""

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_get_file_metadata_computes_checksum(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that _get_file_metadata computes correct checksum."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        test_content = b"test file content"
        expected_checksum = hashlib.sha256(test_content).hexdigest()

        with patch("builtins.open", mock_open(read_data=test_content)):
            metadata = system._get_file_metadata(Path("/test/file.txt"))

        assert metadata["path"] == "/test/file.txt"
        assert metadata["checksum"] == expected_checksum

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_file_needs_processing_new_file(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that new files are marked for processing."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        with patch("builtins.open", mock_open(read_data=b"content")):
            needs_processing = system._file_needs_processing(Path("/new/file.txt"))

        assert needs_processing is True

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_file_needs_processing_unchanged_file(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that unchanged files are skipped."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        test_content = b"content"
        checksum = hashlib.sha256(test_content).hexdigest()
        file_path = Path("/test/file.txt")

        system.processed_files[str(file_path)] = {
            "path": str(file_path),
            "checksum": checksum,
        }

        with patch("builtins.open", mock_open(read_data=test_content)):
            needs_processing = system._file_needs_processing(file_path)

        assert needs_processing is False

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_file_needs_processing_modified_file(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that modified files are marked for processing."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        old_content = b"old content"
        new_content = b"new content"
        file_path = Path("/test/file.txt")

        system.processed_files[str(file_path)] = {
            "path": str(file_path),
            "checksum": hashlib.sha256(old_content).hexdigest(),
        }

        with patch("builtins.open", mock_open(read_data=new_content)):
            needs_processing = system._file_needs_processing(file_path)

        assert needs_processing is True


class TestFileCategorizationAndLoading:
    """Test file categorization and loading functionality."""

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_categorize_files_all_new(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test categorizing files when all are new."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        files = [Path("/file1.pdf"), Path("/file2.md")]

        with patch.object(system, "_file_needs_processing", return_value=True):
            to_process, unchanged = system._categorize_files(files, force_rebuild=False)

        assert len(to_process) == 2
        assert len(unchanged) == 0

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_categorize_files_force_rebuild(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test force_rebuild flag processes all files."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        files = [Path("/file1.pdf"), Path("/file2.md")]

        to_process, unchanged = system._categorize_files(files, force_rebuild=True)

        assert len(to_process) == 2
        assert len(unchanged) == 0

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_load_pdf_document_success(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test loading a PDF document successfully."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content"
        mock_reader = Mock()
        mock_reader.pages = [mock_page]

        with patch("src.graphrag_system.PdfReader", return_value=mock_reader):
            doc = system._load_pdf_document(Path("/test.pdf"))

        assert doc is not None
        assert "Test content" in doc.page_content
        assert doc.metadata["filename"] == "test.pdf"
        assert doc.metadata["type"] == "pdf"

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @pytest.mark.asyncio
    async def test_load_markdown_document_success(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test loading a Markdown document successfully."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        mock_file_content = "# Test Markdown\n\nThis is test content."

        # Create async file context manager mock
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(return_value=mock_file_content)

        # Create async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__.return_value = mock_file
        async_context_manager.__aexit__.return_value = None

        with patch("aiofiles.open", return_value=async_context_manager):
            doc = await system._load_markdown_document(Path("/test.md"))

        assert doc is not None
        assert doc.page_content == mock_file_content
        assert doc.metadata["filename"] == "test.md"
        assert doc.metadata["type"] == "markdown"


class TestDatabaseOperations:
    """Test database operation helper methods."""

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_remove_deleted_files(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test removal of deleted files from knowledge graph."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        # Set up tracked files
        system.processed_files = {
            "/path/to/file1.pdf": {"checksum": "abc123"},
            "/path/to/file2.pdf": {"checksum": "def456"},
        }

        current_files = {"/path/to/file1.pdf"}  # file2 has been deleted

        system._remove_deleted_files(current_files)

        assert "/path/to/file2.pdf" not in system.processed_files
        assert "/path/to/file1.pdf" in system.processed_files

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_create_chunk_nodes(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test creation of chunk nodes in Neo4j."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query.return_value = [0.1] * 1536
        mock_embeddings.return_value = mock_embeddings_instance

        system = GraphRAGSystem()

        chunks = [
            Document(
                page_content="Chunk 1",
                metadata={"source": "test.pdf", "filename": "test.pdf"},
            ),
            Document(
                page_content="Chunk 2",
                metadata={"source": "test.pdf", "filename": "test.pdf"},
            ),
        ]

        count = system._create_chunk_nodes(chunks)

        assert count == 2

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_initialize_retriever(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test retriever initialization."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        with (
            patch("src.graphrag_system.VectorRetriever") as mock_retriever_class,
            patch("src.graphrag_system.GraphRAG") as mock_rag_class,
        ):
            system._initialize_retriever()

            mock_retriever_class.assert_called_once()
            mock_rag_class.assert_called_once()
            assert system.retriever is not None
            assert system.rag is not None


class TestQueryMethods:
    """Test search and query functionality."""

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_get_context_for_query_no_retriever(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test get_context_for_query when retriever is not initialized."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        result = system.get_context_for_query("test query")

        assert result == GraphRAGSystem.NO_DATA_MESSAGE

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_search_no_rag(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test search when RAG is not initialized."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        result = system.search("test query")

        assert "not initialized" in result.lower()

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_close_connection(self, mock_storage, mock_llm, mock_embeddings, mock_graph_db):
        """Test closing the Neo4j connection."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem()

        system.close()

        mock_driver.close.assert_called_once()

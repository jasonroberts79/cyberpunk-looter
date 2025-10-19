"""Unit tests for Neo4j connection resilience."""

import pytest
from unittest.mock import patch, Mock
from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.graphrag_system import GraphRAGSystem


class TestNeo4jConnectionResilience:
    """Unit tests for Neo4j connection resilience.

    These tests verify that the GraphRAGSystem can handle connection drops
    and automatically reconnect using mocked Neo4j connections.
    """

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_initial_connection_success(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that initial connection is established successfully."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            grok_api_key="grok-key",
            max_retry_attempts=3,
            retry_delay=0.5,
        )

        assert system.driver is not None
        assert system.neo4j_uri == "bolt://localhost:7687"
        mock_driver.verify_connectivity.assert_called()

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_connection_health_monitoring(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test connection health monitoring."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.5,
        )

        # Should not raise any exception
        system._ensure_connection()
        assert mock_driver.verify_connectivity.call_count >= 1

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_database_operation_with_retry(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test database operations with retry mechanism."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__ = Mock(return_value=1)
        mock_result.single.return_value = mock_record

        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.5,
        )

        def test_operation():
            with system.driver.session() as session:
                result = session.run("RETURN 1 AS num")
                record = result.single()
                if record is None:
                    raise ValueError("No record found")
                return record["num"]

        result = system._execute_with_retry(test_operation, "Test query")
        assert result == 1

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @patch("src.graphrag_system.time.sleep")
    def test_connection_failure_triggers_reconnect(
        self, mock_sleep, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that connection failures trigger reconnection logic."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver

        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        # Simulate connection failure then success
        mock_driver.verify_connectivity.side_effect = [
            None,  # Initial connection
            ServiceUnavailable("Connection lost"),  # First check fails
            None,  # Reconnection succeeds
        ]

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            grok_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.1,
        )

        # This should trigger reconnection logic
        system._ensure_connection()

        # Verify reconnection was attempted (initial + failed check + reconnect)
        assert mock_driver.verify_connectivity.call_count >= 2

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @patch("src.graphrag_system.time.sleep")
    def test_retry_with_exponential_backoff(
        self, mock_sleep, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that retry mechanism uses exponential backoff."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.1,
        )

        # Create operation that fails twice then succeeds
        call_count = {"count": 0}

        def failing_operation():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ServiceUnavailable("Connection lost")
            return "success"

        result = system._execute_with_retry(failing_operation, "Test operation")

        assert result == "success"
        assert call_count["count"] == 3
        # Verify exponential backoff sleep calls
        assert mock_sleep.call_count == 2  # Two retries

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    @patch("src.graphrag_system.time.sleep")
    def test_retry_exhaustion(
        self, mock_sleep, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that retries are exhausted after max attempts."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=2,
            retry_delay=0.1,
        )

        def always_failing_operation():
            raise ServiceUnavailable("Connection lost")

        with pytest.raises(ServiceUnavailable):
            system._execute_with_retry(always_failing_operation, "Test operation")

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_handles_session_expired(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that SessionExpired exceptions are handled."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.1,
        )

        # Create operation that fails with SessionExpired then succeeds
        call_count = {"count": 0}

        def session_expired_operation():
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise SessionExpired("Session expired")
            return "success"

        result = system._execute_with_retry(session_expired_operation, "Test operation")
        assert result == "success"
        assert call_count["count"] == 2

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_handles_transient_error(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that TransientError exceptions are handled."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.1,
        )

        # Create operation that fails with TransientError then succeeds
        call_count = {"count": 0}

        def transient_error_operation():
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise TransientError("Transient error")
            return "success"

        result = system._execute_with_retry(transient_error_operation, "Test operation")
        assert result == "success"
        assert call_count["count"] == 2

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_connection_cleanup(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that connections are properly closed."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=3,
            retry_delay=0.5,
        )

        # Verify driver exists
        assert system.driver is not None

        # Close and verify
        system.close()
        mock_driver.close.assert_called_once()

    @patch("src.graphrag_system.GraphDatabase")
    @patch("src.graphrag_system.OpenAIEmbeddings")
    @patch("src.graphrag_system.OpenAILLM")
    @patch("src.graphrag_system.AppStorage")
    def test_custom_retry_parameters(
        self, mock_storage, mock_llm, mock_embeddings, mock_graph_db
    ):
        """Test that custom retry parameters are properly set."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver
        mock_storage_instance = Mock()
        mock_storage_instance.readdata.return_value = None
        mock_storage.return_value = mock_storage_instance

        system = GraphRAGSystem(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
            max_retry_attempts=5,
            retry_delay=2.0,
        )

        # Verify retry parameters
        assert system.max_retry_attempts == 5
        assert system.retry_delay == 2.0

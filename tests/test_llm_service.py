"""Unit tests for LLMService."""

import pytest
from unittest.mock import Mock, patch
from src.llm_service import LLMService
from src.memory_system import MemorySystem


class TestLLMServiceInit:
    """Test LLMService initialization."""

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_init_success(self, mock_config, mock_anthropic, mock_graphrag):
        """Test successful initialization."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_anthropic_instance = Mock()
        mock_anthropic.return_value = mock_anthropic_instance
        mock_graphrag_instance = Mock()
        mock_graphrag.return_value = mock_graphrag_instance

        llm_service = LLMService(mock_memory)

        assert llm_service.memory_system == mock_memory
        assert llm_service.model_name == "claude-3-5-sonnet-20241022"
        assert llm_service.claude is not None
        assert llm_service.graphrag_system is not None

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_init_stores_dependencies(self, mock_config, mock_anthropic, mock_graphrag):
        """Test that dependencies are stored correctly."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)

        llm_service = LLMService(mock_memory)

        assert llm_service.game_context is not None


class TestProcessQuery:
    """Test process_query method."""

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_process_query(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test processing a query without tool calls."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.get_user_summary.return_value = "First conversation"
        mock_memory.get_party_summary.return_value = "No party members"
        mock_memory.get_short_term_context.return_value = []

        mock_graphrag_instance = Mock()
        mock_graphrag_instance.get_context_for_query.return_value = "Context"
        mock_graphrag.return_value = mock_graphrag_instance

        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "This is the response"

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.tool_calls = None
        mock_response.choices = []

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        llm_service = LLMService(mock_memory)

        response = llm_service.process_query(
            "user123", "party123", "What's the weather?"
        )

        assert response == mock_response
        mock_memory.add_to_short_term.assert_called()

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_process_query_updates_memory(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test that query updates memory correctly."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.get_user_summary.return_value = "First conversation"
        mock_memory.get_party_summary.return_value = "No party members"
        mock_memory.get_short_term_context.return_value = []

        mock_graphrag_instance = Mock()
        mock_graphrag_instance.get_context_for_query.return_value = "Context"
        mock_graphrag.return_value = mock_graphrag_instance

        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "Response"

        mock_response = Mock()
        mock_response.id = "response_123"
        mock_response.content = [mock_text_block]
        mock_response.tool_calls = None
        mock_response.choices = []

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        llm_service = LLMService(mock_memory)

        llm_service.process_query("user123", "party123", "Hello")

        mock_memory.update_long_term.assert_called_with("user123", "interaction", None)
        assert (
            mock_memory.add_to_short_term.call_count == 2
        )  # User message + assistant response


class TestExecuteToolAction:
    """Test execute_tool_action method."""

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_add_party_character_new(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing add_party_character for new character."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.add_party_character.return_value = True  # New character

        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "add_party_character",
            {"name": "V", "role": "Solo", "gear_preferences": []},
            "user123",
            "party123",
        )

        assert message is not None
        assert "added" in message.lower()
        assert "V" in message

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_add_party_character_update(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing add_party_character for existing character."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.add_party_character.return_value = False  # Updated character

        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "add_party_character",
            {"name": "V", "role": "Netrunner", "gear_preferences": []},
            "user123",
            "party123",
        )

        assert message is not None
        assert "updated" in message.lower()

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_remove_party_character_success(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing remove_party_character successfully."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.remove_party_character.return_value = True

        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "remove_party_character", {"name": "V"}, "user123", "party123"
        )

        assert message is not None
        assert "removed" in message.lower()
        assert "V" in message

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_remove_party_character_not_found(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing remove_party_character for non-existent character."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.remove_party_character.return_value = False

        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "remove_party_character", {"name": "NonExistent"}, "user123", "party123"
        )

        assert message is not None
        assert "not found" in message.lower()

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_view_party_members_with_members(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing view_party_members with characters."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.list_party_characters.return_value = [
            {"name": "V", "role": "Solo", "gear_preferences": ["Guns"]},
            {"name": "Jackie", "role": "Fixer", "gear_preferences": []},
        ]

        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "view_party_members", {}, "user123", "party123"
        )

        assert message is not None
        assert "V" in message
        assert "Jackie" in message
        assert "Solo" in message
        assert "Fixer" in message

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_view_party_members_empty(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing view_party_members with no characters."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.list_party_characters.return_value = []

        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "view_party_members", {}, "user123", "party123"
        )

        assert message is not None
        assert "don't have any" in message.lower()

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_unknown_action(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test executing unknown action."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        llm_service = LLMService(mock_memory)

        message = llm_service.execute_tool_action(
            "unknown_action", {}, "user123", "party123"
        )

        assert message is not None
        assert "Unknown action" in message


class TestExecuteRecommendGear:
    """Test execute_recommend_gear method."""

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")    
    def test_execute_recommend_gear_no_party(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test gear recommendation with no party members."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.list_party_characters.return_value = []

        llm_service = LLMService(mock_memory)

        result = llm_service.execute_recommend_gear(
            "user123", "party123", "Assault Rifle", []
        )

        assert "don't have any party members" in result.lower()

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_execute_recommend_gear_with_exclusions(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test gear recommendation with excluded characters."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.list_party_characters.return_value = [
            {"name": "V", "role": "Solo", "gear_preferences": []},
            {"name": "Jackie", "role": "Fixer", "gear_preferences": []},
        ]

        mock_graphrag_instance = Mock()
        mock_graphrag_instance.get_context_for_query.return_value = "Context"
        mock_graphrag.return_value = mock_graphrag_instance

        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "Recommendation text"

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.tool_calls = None
        mock_response.choices = []

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        llm_service = LLMService(mock_memory)

        result = llm_service.execute_recommend_gear("user123", "party123", "Guns", ["V"])

        # Should only recommend for Jackie
        assert result == "Recommendation text"

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    
    def test_execute_recommend_gear_all_excluded(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test gear recommendation when all members are excluded."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        mock_memory.list_party_characters.return_value = [
            {"name": "V", "role": "Solo", "gear_preferences": []},
        ]

        llm_service = LLMService(mock_memory)

        result = llm_service.execute_recommend_gear("user123", "party123", "Guns", ["V"])

        assert "no party members available" in result.lower()


class TestExtractToolCalls:
    """Test _extract_tool_calls method."""

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_extract_tool_calls_anthropic_format(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test extracting tool calls in Anthropic format."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        llm_service = LLMService(mock_memory)

        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "add_party_character"
        mock_tool_block.input = {"name": "V", "role": "Solo"}

        mock_response = Mock()
        mock_response.content = [mock_tool_block]

        calls = llm_service.extract_tool_calls(mock_response)

        assert calls is not None
        assert len(calls) == 1
        assert calls[0]["name"] == "add_party_character"

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_extract_tool_calls_no_tools(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test extracting tool calls when there are none."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        llm_service = LLMService(mock_memory)

        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "Regular response"

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.tool_calls = None
        mock_response.choices = []

        calls = llm_service.extract_tool_calls(mock_response)

        assert calls == []

    @patch("src.llm_service.GraphRAGSystem")
    @patch("src.llm_service.Anthropic")
    @patch("src.llm_service.get_config_value")
    def test_extract_tool_calls_multiple(
        self, mock_config, mock_anthropic, mock_graphrag
    ):
        """Test extracting multiple tool calls."""
        mock_config.side_effect = lambda key: {
            "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
            "OPENAI_BASE_URL": "https://api.anthropic.com",
            "OPENAI_API_KEY": "test_key",
        }[key]

        mock_memory = Mock(spec=MemorySystem)
        llm_service = LLMService(mock_memory)

        mock_tool_block1 = Mock()
        mock_tool_block1.type = "tool_use"
        mock_tool_block1.name = "add_party_character"
        mock_tool_block1.input = {"name": "V"}

        mock_tool_block2 = Mock()
        mock_tool_block2.type = "tool_use"
        mock_tool_block2.name = "view_party_members"
        mock_tool_block2.input = {}

        mock_response = Mock()
        mock_response.content = [mock_tool_block1, mock_tool_block2]

        calls = llm_service.extract_tool_calls(mock_response)

        assert calls is not None
        assert len(calls) == 2
        assert calls[0]["name"] == "add_party_character"
        assert calls[1]["name"] == "view_party_members"

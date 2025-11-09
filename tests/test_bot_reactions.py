"""Unit tests for DiscordReactions."""

import pytest
import time
import discord
from unittest.mock import Mock, AsyncMock
from src.bot_reactions import DiscordReactions

from src.interfaces import ToolExecutor
from src.models import PendingConfirmation

class TestDiscordReactionsInit:
    """Test DiscordReactions initialization."""

    def test_init_success(self):
        """Test successful initialization."""
        
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        assert reactions.pending_confirmations == {}
class TestAddPendingConfirmation:
    """Test adding pending confirmations."""

    def test_add_pending_confirmation_basic(self):
        """Test adding a basic confirmation."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={"name": "V", "role": "Solo"},
        )

        assert "123" in reactions.pending_confirmations
        assert reactions.pending_confirmations["123"].user_id == "user456"
        assert reactions.pending_confirmations["123"].party_id == "party789"
        assert reactions.pending_confirmations["123"].action == "add_party_character"
        assert reactions.pending_confirmations["123"].processed is False

    def test_add_pending_confirmation_with_channel(self):
        """Test adding confirmation with channel ID."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="view_party_members",
            parameters={},
            channel_id="channel789",
        )

        assert reactions.pending_confirmations["123"].channel_id == "channel789"

    def test_add_pending_confirmation_has_timestamp(self):
        """Test that confirmation includes timestamp."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        before_time = time.time()
        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )
        after_time = time.time()

        timestamp = reactions.pending_confirmations["123"].timestamp
        assert before_time <= timestamp <= after_time


class TestGetPendingConfirmation:
    """Test getting pending confirmations."""

    def test_get_pending_confirmation_exists(self):
        """Test getting an existing confirmation."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={"name": "V"},
        )

        result = reactions.get_pending_confirmation("123")

        assert result is not None
        assert result.user_id == "user456"

    def test_get_pending_confirmation_not_exists(self):
        """Test getting a non-existent confirmation."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        result = reactions.get_pending_confirmation("nonexistent")

        assert result is None


class TestRemovePendingConfirmation:
    """Test removing pending confirmations."""

    def test_remove_pending_confirmation_exists(self):
        """Test removing an existing confirmation."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )

        reactions.remove_pending_confirmation("123")

        assert "123" not in reactions.pending_confirmations

    def test_remove_pending_confirmation_not_exists(self):
        """Test removing a non-existent confirmation doesn't crash."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        # Should not raise an error
        reactions.remove_pending_confirmation("nonexistent")


class TestIsTimedOut:
    """Test timeout checking."""

    def test_is_timed_out_not_timed_out(self):
        """Test confirmation that hasn't timed out."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        confirmation = PendingConfirmation(user_id="user456", party_id="party789", action="add_party_character", parameters={}, timestamp=time.time())

        result = reactions.is_timed_out(confirmation, timeout_seconds=60)

        assert result is False

    def test_is_timed_out_timed_out(self):
        """Test confirmation that has timed out."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        confirmation = PendingConfirmation(user_id="user456", party_id="party789", action="add_party_character", parameters={}, timestamp=time.time() - 120)

        result = reactions.is_timed_out(confirmation, timeout_seconds=60)

        assert result is True

    def test_is_timed_out_custom_timeout(self):
        """Test with custom timeout duration."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        confirmation = PendingConfirmation(user_id="user456", party_id="party789", action="add_party_character", parameters={}, timestamp=time.time() - 15)        

        result = reactions.is_timed_out(confirmation, timeout_seconds=10)

        assert result is True


class TestHandleApproval:
    """Test handling approval reactions."""

    @pytest.mark.asyncio
    async def test_handle_approval_success(self):
        """Test successful approval handling."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        mock_tool_exec_service.execute_tool = Mock(
            return_value=(True, "Character added successfully!")
        )
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.id = 123
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "party_id": "party789",
            "action": "add_party_character",
            "parameters": {"name": "V", "role": "Solo"},
            "processed": False,
        }

        await reactions.handle_approval(mock_message, confirmation)

        mock_tool_exec_service.execute_tool.assert_called_once_with(
            tool_name="add_party_character",
            arguments={"name": "V", "role": "Solo"},
            user_id="user456",
            party_id="party789",
        )
        mock_message.reply.assert_called_once()
        assert confirmation["processed"] is True

    @pytest.mark.asyncio
    async def test_handle_approval_marks_processed(self):
        """Test that approval marks confirmation as processed."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        mock_tool_exec_service.execute_tool_action = Mock(return_value=(True, "Success"))
        reactions = DiscordReactions(mock_tool_exec_service)

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="view_party_members",
            parameters={},
        )

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.id = 123

        confirmation = reactions.get_pending_confirmation("123")
        assert confirmation is not None
        await reactions.handle_approval(mock_message, confirmation)

        assert confirmation.processed is True

    @pytest.mark.asyncio
    async def test_handle_approval_error(self):
        """Test approval handling when execution fails."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        mock_tool_exec_service.execute_tool_action = Mock(side_effect=Exception("Execution error"))
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.id = 123
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "action": "add_party_character",
            "parameters": {},
            "processed": False,
        }

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )

        await reactions.handle_approval(mock_message, confirmation)

        # Should send error message
        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args[0][0]
        assert "Error" in call_args

    @pytest.mark.asyncio
    async def test_handle_approval_missing_llm_service(self):
        """Test approval fails gracefully without LLM service."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        # Set llm_service to None after initialization
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.id = 123
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "action": "add_party_character",
            "parameters": {},
            "processed": False,
        }

        await reactions.handle_approval(mock_message, confirmation)

        # Should send error message
        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args[0][0]
        assert "Error" in call_args or "required" in call_args
        

class TestHandleRejection:
    """Test handling rejection reactions."""

    @pytest.mark.asyncio
    async def test_handle_rejection_add_character(self):
        """Test rejection for add_party_character."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.id = 123
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "action": "add_party_character",
            "parameters": {"name": "V"},
            "processed": False,
        }

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={"name": "V"},
        )

        await reactions.handle_rejection(mock_message, confirmation)

        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args[0][0]        
        assert "Cancelled" in call_args
        assert confirmation["processed"] is True
        assert "123" not in reactions.pending_confirmations

    @pytest.mark.asyncio
    async def test_handle_rejection_remove_character(self):
        """Test rejection for remove_party_character."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "action": "remove_party_character",
            "parameters": {"name": "Jackie"},
            "processed": False,
        }

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="remove_party_character",
            parameters={"name": "Jackie"},
        )

        await reactions.handle_rejection(mock_message, confirmation)

        call_args = mock_message.reply.call_args[0][0]        
        assert "Cancelled" in call_args

    @pytest.mark.asyncio
    async def test_handle_rejection_view_party(self):
        """Test rejection for view_party_members."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "action": "view_party_members",
            "parameters": {},
            "processed": False,
        }

        await reactions.handle_rejection(mock_message, confirmation)

        call_args = mock_message.reply.call_args[0][0]
        assert "party members" in call_args.lower()
        assert "Cancelled" in call_args

    @pytest.mark.asyncio
    async def test_handle_rejection_recommend_gear(self):
        """Test rejection for recommend_gear."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.reply = AsyncMock()

        confirmation = {
            "user_id": "user456",
            "action": "recommend_gear",
            "parameters": {},
            "processed": False,
        }

        await reactions.handle_rejection(mock_message, confirmation)

        call_args = mock_message.reply.call_args[0][0]
        assert "gear" in call_args.lower()
        assert "Cancelled" in call_args


class TestHandleTimeout:
    """Test handling timeouts."""

    @pytest.mark.asyncio
    async def test_handle_timeout_success(self):
        """Test successful timeout handling."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_message = AsyncMock(spec=discord.Message)
        mock_message.id = 123
        mock_message.content = "Test confirmation message"
        mock_message.edit = AsyncMock()

        mock_channel = AsyncMock()
        mock_channel.fetch_message = AsyncMock(return_value=mock_message)

        mock_bot = Mock()
        mock_bot.get_channel = Mock(return_value=mock_channel)

        confirmation = PendingConfirmation(user_id="user456", party_id="party789", action="add_party_character", parameters={}, timestamp=time.time() - 120, channel_id="789")
        
        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
            channel_id="789",
        )

        await reactions.handle_timeout("123", confirmation, mock_bot)

        mock_message.edit.assert_called_once()
        call_args = mock_message.edit.call_args
        assert "~~" in call_args[1]["content"]
        assert "timed out" in call_args[1]["content"].lower()
        assert "123" not in reactions.pending_confirmations

    @pytest.mark.asyncio
    async def test_handle_timeout_no_channel_id(self):
        """Test timeout handling without channel ID."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_bot = Mock()

        confirmation = PendingConfirmation(user_id="user456", party_id="party789", action="add_party_character", parameters={}, timestamp=time.time())

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )

        await reactions.handle_timeout("123", confirmation, mock_bot)

        # Should remove confirmation even without channel
        assert "123" not in reactions.pending_confirmations

    @pytest.mark.asyncio
    async def test_handle_timeout_message_not_found(self):
        """Test timeout handling when message is deleted."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        # Create proper discord.NotFound error
        mock_response = Mock()
        mock_response.status = 404
        mock_response.text = "Not Found"

        mock_channel = AsyncMock()
        mock_channel.fetch_message = AsyncMock(
            side_effect=discord.NotFound(mock_response, "message")
        )

        mock_bot = Mock()
        mock_bot.get_channel = Mock(return_value=mock_channel)

        confirmation = PendingConfirmation(user_id="user456", party_id="party789", action="add_party_character", parameters={}, timestamp=time.time(), channel_id="789")

        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
            channel_id="789",
        )

        await reactions.handle_timeout("123", confirmation, mock_bot)

        # Should remove confirmation gracefully
        assert "123" not in reactions.pending_confirmations


class TestCheckAndCleanupTimeouts:
    """Test checking and cleaning up timed out confirmations."""

    @pytest.mark.asyncio
    async def test_check_and_cleanup_timeouts_removes_old(self):
        """Test that old confirmations are cleaned up."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_bot = Mock()
        mock_bot.get_channel = Mock(return_value=None)

        # Add an old confirmation
        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )

        # Manually set old timestamp
        reactions.pending_confirmations["123"].timestamp = time.time() - 120

        await reactions.check_and_cleanup_timeouts("user456", mock_bot)

        # Should be removed
        assert "123" not in reactions.pending_confirmations

    @pytest.mark.asyncio
    async def test_check_and_cleanup_timeouts_keeps_recent(self):
        """Test that recent confirmations are kept."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_bot = Mock()

        # Add a recent confirmation
        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )

        await reactions.check_and_cleanup_timeouts("user456", mock_bot)

        # Should still be there
        assert "123" in reactions.pending_confirmations

    @pytest.mark.asyncio
    async def test_check_and_cleanup_timeouts_only_user(self):
        """Test that only specified user's confirmations are checked."""
        mock_tool_exec_service = Mock(spec=ToolExecutor)
        reactions = DiscordReactions(mock_tool_exec_service)

        mock_bot = Mock()
        mock_bot.get_channel = Mock(return_value=None)

        # Add old confirmations for different users
        reactions.add_pending_confirmation(
            message_id="123",
            user_id="user456",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )
        reactions.add_pending_confirmation(
            message_id="456",
            user_id="user789",
            party_id="party789",
            action="add_party_character",
            parameters={},
        )

        # Set both to old timestamps
        reactions.pending_confirmations["123"].timestamp = time.time() - 120
        reactions.pending_confirmations["456"].timestamp = time.time() - 120

        await reactions.check_and_cleanup_timeouts("user456", mock_bot)

        # Only user456's confirmation should be removed
        assert "123" not in reactions.pending_confirmations
        assert "456" in reactions.pending_confirmations


"""Tests for handler integration, authorization, and message generation."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from telegram import Update, User, Message, CallbackQuery
from telegram.ext import ContextTypes
from bot.config import Config
from bot.handlers.auth import authorized_only, myid_handler
from bot.main import create_application


@pytest.fixture
def mock_update():
    """Create a mock Telegram update with an authorized user."""
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 111111111
    user.full_name = "Alice"
    user.username = "alice_telegram"
    update.effective_user = user
    msg = AsyncMock(spec=Message)
    update.message = msg
    update.effective_message = msg
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.mark.asyncio
async def test_myid_handler(mock_update, mock_context):
    await myid_handler(mock_update, mock_context)
    mock_update.effective_message.reply_text.assert_called_once()
    args, kwargs = mock_update.effective_message.reply_text.call_args
    assert "Your Telegram Identity" in args[0]
    assert "111111111" in args[0]


@pytest.mark.asyncio
async def test_authorized_only_rejects_stranger():
    # Stranger ID not in .env
    stranger_update = MagicMock(spec=Update)
    stranger = MagicMock(spec=User)
    stranger.id = 999999999
    stranger.full_name = "Stranger"
    stranger_update.effective_user = stranger
    stranger_msg = AsyncMock(spec=Message)
    stranger_update.message = stranger_msg
    stranger_update.effective_message = stranger_msg
    stranger_update.callback_query = None

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    target_mock = AsyncMock()
    decorated = authorized_only(target_mock)

    await decorated(stranger_update, context)

    # The actual inner function should NOT be called
    target_mock.assert_not_called()
    # But a polite rejection message with their ID should be sent
    stranger_msg.reply_text.assert_called_once()
    sent_text = stranger_msg.reply_text.call_args[0][0]
    assert "exclusive couple space" in sent_text
    assert "999999999" in sent_text


def test_create_application_wiring():
    """Test that all handlers, commands, and conversation states wire together cleanly."""
    app = create_application()
    assert app is not None
    # Check that handlers were added to the dispatcher
    handler_count = sum(len(h_list) for h_list in app.handlers.values())
    assert handler_count >= 10

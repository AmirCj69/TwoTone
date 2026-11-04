"""Authentication decorator, user identification, persistent menu, and welcome handlers."""
import logging
from functools import wraps
from typing import Callable, Coroutine, Any
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import config

logger = logging.getLogger("TwoTone.Auth")


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Return the persistent bottom keyboard always available to both partners."""
    keyboard = [
        ["🌱 Share a Feeling"],
        ["📖 Journal", "📊 Insights"],
        ["✨ Custom Feelings", "❓ Guide"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def authorized_only(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """Decorator to restrict handler execution to configured partner IDs."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user:
            logger.info("Incoming interaction from User ID: %s (%s)", user.id, user.full_name)
        if not user or not config.is_authorized(user.id):
            user_id = user.id if user else "Unknown"
            user_name = user.full_name if user else "Anonymous"
            logger.warning("Unauthorized user attempted access: %s (%s)", user_id, user_name)
            msg = (
                "🔒 *TwoTone is an exclusive couple space.*\n\n"
                f"Your Telegram ID is: `{user_id}`\n"
                f"Name: {user_name}\n\n"
                "If you are the bot owner, please add this ID to your `.env` configuration file "
                "under `USER_A_ID` or `USER_B_ID`, then restart the bot."
            )
            if update.effective_message:
                await update.effective_message.reply_text(msg, parse_mode="Markdown")
            elif update.callback_query:
                await update.callback_query.answer("Unauthorized access.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


async def myid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's Telegram ID for setup and configuration."""
    user = update.effective_user
    if not user:
        return
    logger.info("myid requested by User ID: %s (%s)", user.id, user.full_name)
    status = "✅ Authorized Partner" if config.is_authorized(user.id) else "🔒 Not in .env yet"
    text = (
        "🆔 *Your Telegram Identity*\n\n"
        f"• **User ID**: `{user.id}`\n"
        f"• **Name**: {user.full_name}\n"
        f"• **Username**: @{user.username or 'none'}\n"
        f"• **Status**: {status}\n\n"
        "Copy your User ID and paste it into `.env` as `USER_A_ID` or `USER_B_ID`."
    )
    if update.effective_message:
        await update.effective_message.reply_text(text, parse_mode="Markdown")


@authorized_only
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the authorized couple and show persistent action bar."""
    user = update.effective_user
    sender_name = config.get_sender_name(user.id)
    _, _, partner_name = config.get_partner_info(user.id)

    reply_markup = get_main_reply_keyboard()

    text = (
        f"🤍 *Welcome to TwoTone, {sender_name}*\n\n"
        f"This is your shared, private space with *{partner_name}*.\n\n"
        "Whenever something is hard to voice directly—or whenever you feel "
        "love, fatigue, or sensitivity—tap **🌱 Share a Feeling** below.\n\n"
        "Use the buttons at the bottom of your screen anytime to navigate."
    )
    if update.effective_message:
        await update.effective_message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


@authorized_only
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain bot commands and philosophy."""
    if update.callback_query:
        await update.callback_query.answer()

    text = (
        "🕊️ *TwoTone Guide*\n\n"
        "TwoTone helps you communicate feelings without confrontation, defensiveness, "
        "or vulnerability fatigue.\n\n"
        "✨ *How to Use:*\n"
        "1. Tap **🌱 Share a Feeling** below (or type `/feel`).\n"
        "2. Tap your emotion from the grid.\n"
        "3. Tap what you need right now ➔ *Delivered instantly with care!*\n\n"
        "✨ *Navigation:*\n"
        "• **🌱 Share a Feeling** — Send an emotion card.\n"
        "• **📖 Journal** — Review past feelings and mutual acknowledgments.\n"
        "• **📊 Insights** — View emotional balance and statistics.\n"
        "• **✨ Custom Feelings** — Add your private inside tags.\n"
        "• `/cancel` — Cancel any active prompt.\n\n"
        "_Everything you send is private, gentle, and delivered only to your partner._"
    )
    if update.effective_message:
        await update.effective_message.reply_text(
            text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown"
        )

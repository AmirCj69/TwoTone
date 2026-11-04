"""Handlers for adding and managing couple custom feelings."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from bot.config import config
from bot.database import db
from bot.handlers.auth import authorized_only, get_main_reply_keyboard

CUSTOM_NAME, CUSTOM_EMOJI = range(2)


@authorized_only
async def add_feeling_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start adding a custom couple feeling."""
    if update.callback_query:
        await update.callback_query.answer()

    text = (
        "✨ *Add a Couple Feeling*\n\n"
        "Create a personalized feeling tag or inside joke that either of you can select.\n\n"
        "First, **type the name of the feeling**:\n"
        "(e.g., _'Missing our morning tea'_, _'Overstimulated'_, _'Need silly banter'_)\n\n"
        "Type `/cancel` to abort."
    )
    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")
    return CUSTOM_NAME


async def custom_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the name and prompt for emoji."""
    feeling_name = update.message.text.strip()
    if not feeling_name:
        await update.message.reply_text("Please provide a valid name.")
        return CUSTOM_NAME

    context.user_data["custom_feeling_name"] = feeling_name
    await update.message.reply_text(
        f"Great! Name: *{feeling_name}*\n\n"
        "Now, send **one or two emojis** to represent this feeling (e.g. 🍵 or 🧸):",
        parse_mode="Markdown",
    )
    return CUSTOM_EMOJI


async def custom_emoji_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save custom feeling to the database and notify partner."""
    emoji = update.message.text.strip()
    name = context.user_data.pop("custom_feeling_name", "Custom Feeling")
    user = update.effective_user

    feeling_id = await db.add_custom_feeling(user.id, name, emoji)
    partner_id, sender_name, partner_name = config.get_partner_info(user.id)

    # Confirmation to user
    await update.message.reply_text(
        f"✨ *Saved to your couple catalog!*\n\n"
        f"{emoji} *{name}*\n\n"
        "You or your partner can now pick this in `/feel` under 'Couple Custom Feelings'.",
        parse_mode="Markdown",
    )

    # Notify partner
    try:
        await context.bot.send_message(
            chat_id=partner_id,
            text=(
                f"✨ *{sender_name} added a new feeling to your couple catalog:*\n\n"
                f"{emoji} *{name}*\n\n"
                "You can now use it when sharing feelings!"
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    return ConversationHandler.END


async def cancel_custom_feeling(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel adding custom feeling."""
    context.user_data.pop("custom_feeling_name", None)
    await update.message.reply_text("Cancelled adding custom feeling.")
    return ConversationHandler.END


@authorized_only
async def list_feelings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display all custom feelings with delete buttons."""
    feelings = await db.get_custom_feelings()
    if not feelings:
        text = (
            "✨ *No custom feelings added yet.*\n\n"
            "Use `/add_feeling` to create your first personal feeling tag!"
        )
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
        return

    keyboard = [
        [
            InlineKeyboardButton(f"{cf['emoji']} {cf['feeling_name']}", callback_data="noop"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"del_cf:{cf['id']}"),
        ]
        for cf in feelings
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "✨ *Your Couple Custom Feelings:*\nTap 🗑️ to delete any tag:"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def delete_feeling_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle deleting a custom feeling."""
    query = update.callback_query
    if not query or not query.data:
        return

    cf_id = int(query.data.split(":", 1)[1])
    success = await db.delete_custom_feeling(cf_id)
    if success:
        await query.answer("Custom feeling deleted.", show_alert=True)
        # Refresh the list
        await list_feelings_handler(update, context)
    else:
        await query.answer("Could not find this feeling.", show_alert=True)


def get_custom_feeling_conversation_handler() -> ConversationHandler:
    """Return ConversationHandler for /add_feeling."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("add_feeling", add_feeling_entry),
            CallbackQueryHandler(add_feeling_entry, pattern="^menu:custom$"),
        ],
        states={
            CUSTOM_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_name_received),
            ],
            CUSTOM_EMOJI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_emoji_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_custom_feeling)],
        allow_reentry=True,
        per_chat=True,
        per_user=True,
        per_message=False,
    )

"""Streamlined 2-Tap Emotion Sharing ConversationHandler."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.config import config
from bot.constants.emotions import (
    EMOTION_GRID,
    NEEDS_CATALOG,
    QUICK_REACTIONS,
    find_emotion_label,
    find_need_label,
)
from bot.database import db
from bot.handlers.auth import get_main_reply_keyboard

logger = logging.getLogger("TwoTone.Feel")

# Two primary conversation states (plus optional note state)
SELECT_EMOTION, SELECT_NEED, ATTACH_NOTE = range(3)


def _build_emotion_grid(custom_feelings: list) -> InlineKeyboardMarkup:
    """Build a compact 2-column inline grid for fast emotion selection."""
    buttons = []
    # Build 2-column rows for core emotions
    for i in range(0, len(EMOTION_GRID), 2):
        row = [
            InlineKeyboardButton(
                EMOTION_GRID[i][1], callback_data=f"emo:{EMOTION_GRID[i][0]}"
            )
        ]
        if i + 1 < len(EMOTION_GRID):
            row.append(
                InlineKeyboardButton(
                    EMOTION_GRID[i + 1][1],
                    callback_data=f"emo:{EMOTION_GRID[i + 1][0]}",
                )
            )
        buttons.append(row)

    # Couple custom feelings (if any)
    if custom_feelings:
        cf_row = []
        for cf in custom_feelings:
            label = f"{cf['emoji']} {cf['feeling_name']}"
            cf_row.append(
                InlineKeyboardButton(label, callback_data=f"emo:custom_{cf['id']}")
            )
            if len(cf_row) == 2:
                buttons.append(cf_row)
                cf_row = []
        if cf_row:
            buttons.append(cf_row)

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="feel_cancel")])
    return InlineKeyboardMarkup(buttons)


def _build_needs_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for 1-tap need selection and instant dispatch."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"need_send:{key}")]
        for key, label in NEEDS_CATALOG
    ]
    # Options for adding a custom note or going back
    buttons.append(
        [InlineKeyboardButton("✍️ Add a note first", callback_data="need_add_note")]
    )
    buttons.append(
        [
            InlineKeyboardButton("🔙 Back", callback_data="back:to_emotions"),
            InlineKeyboardButton("❌ Cancel", callback_data="feel_cancel"),
        ]
    )
    return InlineKeyboardMarkup(buttons)


async def feel_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: Present clean 2-column emotion grid."""
    user = update.effective_user
    if not user or not config.is_authorized(user.id):
        if update.effective_message:
            await update.effective_message.reply_text("🔒 Unauthorized.")
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    # Reset in-memory feeling draft
    context.user_data["feel"] = {}

    custom_feelings = await db.get_custom_feelings()
    reply_markup = _build_emotion_grid(custom_feelings)

    text = (
        "🌱 *Step 1 of 2: How are you feeling right now?*\n\n"
        "Tap the emotion that speaks to your current state:"
    )

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="Markdown"
            )
        except Exception:
            await update.effective_message.reply_text(
                text, reply_markup=reply_markup, parse_mode="Markdown"
            )
    else:
        await update.effective_message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    return SELECT_EMOTION


async def emotion_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: User picked emotion, present 1-tap needs for immediate send."""
    query = update.callback_query
    await query.answer()

    emo_key = query.data.split(":", 1)[1]
    context.user_data["feel"]["emotion_key"] = emo_key

    # Lookup label
    if emo_key.startswith("custom_"):
        cf_id = int(emo_key.replace("custom_", ""))
        custom_feelings = await db.get_custom_feelings()
        matched = next((cf for cf in custom_feelings if cf["id"] == cf_id), None)
        emo_label = (
            f"{matched['emoji']} {matched['feeling_name']}"
            if matched
            else "Custom Feeling"
        )
    else:
        emo_label = find_emotion_label(emo_key)

    context.user_data["feel"]["emotion_label"] = emo_label

    text = (
        "💌 *Step 2 of 2: What would help right now?*\n\n"
        f"Selected: *{emo_label}*\n\n"
        "Tap a need below to **send immediately** 🚀\n"
        "_(or tap 'Add a note first' if you wish to type context)_:"
    )
    await query.edit_message_text(
        text, reply_markup=_build_needs_keyboard(), parse_mode="Markdown"
    )
    return SELECT_NEED


async def need_send_direct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 1-tap need selection: Dispatches immediately with no typing!"""
    query = update.callback_query
    await query.answer("Delivering feeling... 🤍")

    need_key = query.data.split(":", 1)[1]
    context.user_data["feel"]["need_key"] = need_key
    context.user_data["feel"]["need_label"] = find_need_label(need_key)

    return await dispatch_emotion(update, context, note=None)


async def prompt_add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User wants to type an optional note before sending."""
    query = update.callback_query
    await query.answer()

    feel_data = context.user_data.get("feel", {})
    emo_label = feel_data.get("emotion_label", "Feeling")
    partner_id, sender_name, partner_name = config.get_partner_info(
        update.effective_user.id
    )

    buttons = [
        [InlineKeyboardButton("🚀 Send As Is (No Note)", callback_data="send_now")],
        [
            InlineKeyboardButton("🔙 Back to Needs", callback_data="back:to_needs"),
            InlineKeyboardButton("❌ Cancel", callback_data="feel_cancel"),
        ],
    ]

    text = (
        f"✍️ *Add a note for {partner_name}:*\n\n"
        f"• **Feeling**: {emo_label}\n\n"
        "Type your message below and press send in Telegram.\n"
        "Or tap **Send As Is** if you change your mind."
    )
    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown"
    )
    return ATTACH_NOTE


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle backwards navigation inside the 2-step composer."""
    query = update.callback_query
    await query.answer()
    back_target = query.data.split(":", 1)[1]

    if back_target == "to_emotions":
        custom_feelings = await db.get_custom_feelings()
        text = (
            "🌱 *Step 1 of 2: How are you feeling right now?*\n\n"
            "Tap the emotion that speaks to your current state:"
        )
        await query.edit_message_text(
            text,
            reply_markup=_build_emotion_grid(custom_feelings),
            parse_mode="Markdown",
        )
        return SELECT_EMOTION

    elif back_target == "to_needs":
        emo_label = context.user_data.get("feel", {}).get("emotion_label", "Feeling")
        text = (
            "💌 *Step 2 of 2: What would help right now?*\n\n"
            f"Selected: *{emo_label}*\n\n"
            "Tap a need below to **send immediately** 🚀:"
        )
        await query.edit_message_text(
            text, reply_markup=_build_needs_keyboard(), parse_mode="Markdown"
        )
        return SELECT_NEED

    return SELECT_EMOTION


async def dispatch_emotion(
    update: Update, context: ContextTypes.DEFAULT_TYPE, note: str = None
) -> int:
    """Deliver the formatted emotion card to the partner and save to SQLite."""
    user = update.effective_user
    feel_data = context.user_data.get("feel", {})
    if not feel_data:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Draft expired. Please tap '🌱 Share a Feeling' again.",
                reply_markup=get_main_reply_keyboard(),
            )
        return ConversationHandler.END

    partner_id, sender_name, partner_name = config.get_partner_info(user.id)

    # 1. Save to Database
    log_id = await db.log_emotion(
        sender_id=user.id,
        recipient_id=partner_id,
        category_key=feel_data.get("category_key", "general"),
        emotion_key=feel_data.get("emotion_key", "unknown"),
        emotion_label=feel_data.get("emotion_label", "Feeling"),
        need_key=feel_data.get("need_key", "no_reply"),
        need_label=feel_data.get("need_label", "No words needed"),
        note=note,
    )

    # 2. Build Card for Partner
    note_line = f"\n📝 *Note*: _{note}_\n" if note else ""
    card_text = (
        "💌 *TwoTone Message*\n"
        f"From: *{sender_name}*\n\n"
        f"💭 *Feeling*: {feel_data.get('emotion_label')}\n"
        f"🎯 *Need*: {feel_data.get('need_label')}"
        f"{note_line}\n"
        "_Take a gentle breath. No pressure to fix anything—just holding space for each other._"
    )

    # 3. Build Reaction Buttons for Partner
    partner_keyboard = [
        [
            InlineKeyboardButton("🤍 I hear you", callback_data=f"react:{log_id}:ack_hear"),
            InlineKeyboardButton("🫂 Sending a hug", callback_data=f"react:{log_id}:ack_hug"),
        ],
        [
            InlineKeyboardButton("🕊️ Giving space", callback_data=f"react:{log_id}:ack_space"),
            InlineKeyboardButton("⏳ Talk soon", callback_data=f"react:{log_id}:ack_soon"),
        ],
        [
            InlineKeyboardButton("✨ Love you", callback_data=f"react:{log_id}:ack_love"),
            InlineKeyboardButton("💬 Gentle Reply", callback_data=f"reply:{log_id}"),
        ],
    ]
    partner_markup = InlineKeyboardMarkup(partner_keyboard)

    try:
        sent_msg = await context.bot.send_message(
            chat_id=partner_id,
            text=card_text,
            reply_markup=partner_markup,
            parse_mode="Markdown",
        )
        await db.set_recipient_message_id(log_id, sent_msg.message_id)
        delivery_success = True
    except Exception as e:
        logger.error(f"Failed to deliver emotion card to partner {partner_id}: {e}")
        delivery_success = False

    # 4. Confirmation to Sender
    if delivery_success:
        confirmation = (
            f"🕊️ *Your feeling was delivered to {partner_name} with care.*\n\n"
            f"• **Feeling**: {feel_data.get('emotion_label')}\n"
            f"• **Need**: {feel_data.get('need_label')}"
            f"{note_line}\n"
            "You will be gently notified when they acknowledge it 🤍."
        )
    else:
        confirmation = (
            f"⚠️ Could not reach {partner_name}. Please make sure they have opened the bot "
            "and sent at least one message."
        )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            confirmation, parse_mode="Markdown"
        )
        # Re-attach persistent menu
        await update.effective_message.reply_text(
            "What would you like to do next?",
            reply_markup=get_main_reply_keyboard(),
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            confirmation,
            reply_markup=get_main_reply_keyboard(),
            parse_mode="Markdown",
        )

    context.user_data.pop("feel", None)
    return ConversationHandler.END


async def note_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom text note input."""
    note_text = update.message.text.strip() if update.message and update.message.text else ""
    return await dispatch_emotion(update, context, note=note_text)


async def send_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Send As Is without note."""
    query = update.callback_query
    await query.answer()
    return await dispatch_emotion(update, context, note=None)


async def feel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel emotion flow."""
    context.user_data.pop("feel", None)
    text = "🤍 Cancelled. Take gentle care of yourself."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text)
        await update.effective_message.reply_text(
            "Main Menu:", reply_markup=get_main_reply_keyboard()
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            text, reply_markup=get_main_reply_keyboard()
        )
    return ConversationHandler.END


def get_feel_conversation_handler() -> ConversationHandler:
    """Construct and return the ConversationHandler for /feel."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("feel", feel_entry),
            CallbackQueryHandler(feel_entry, pattern="^menu:feel$"),
            MessageHandler(filters.Regex("^🌱 Share a Feeling$"), feel_entry),
        ],
        states={
            SELECT_EMOTION: [
                CallbackQueryHandler(emotion_selected, pattern="^emo:"),
                CallbackQueryHandler(feel_cancel, pattern="^feel_cancel$"),
            ],
            SELECT_NEED: [
                CallbackQueryHandler(need_send_direct, pattern="^need_send:"),
                CallbackQueryHandler(prompt_add_note, pattern="^need_add_note$"),
                CallbackQueryHandler(back_navigation, pattern="^back:to_emotions$"),
                CallbackQueryHandler(feel_cancel, pattern="^feel_cancel$"),
            ],
            ATTACH_NOTE: [
                CallbackQueryHandler(send_now_callback, pattern="^send_now$"),
                CallbackQueryHandler(back_navigation, pattern="^back:to_needs$"),
                CallbackQueryHandler(feel_cancel, pattern="^feel_cancel$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, note_received),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", feel_cancel),
            CallbackQueryHandler(feel_cancel, pattern="^feel_cancel$"),
        ],
        allow_reentry=True,
        per_chat=True,
        per_user=True,
        per_message=False,
    )

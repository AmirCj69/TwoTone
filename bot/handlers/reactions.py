"""Handlers for partner reactions and gentle follow-up replies."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import config
from bot.constants.emotions import find_reaction_label
from bot.database import db

logger = logging.getLogger(__name__)


async def reaction_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 1-click reaction button clicks by the receiving partner."""
    query = update.callback_query
    if not query or not query.data:
        return

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "react":
        return

    log_id = int(parts[1])
    reaction_key = parts[2]
    reaction_label = find_reaction_label(reaction_key)
    user = update.effective_user

    entry = await db.get_emotion_by_id(log_id)
    if not entry:
        await query.answer("Could not find this feeling entry.", show_alert=True)
        return

    # Verify the clicker is the intended recipient
    if user.id != entry["recipient_id"]:
        await query.answer("Only the receiving partner can acknowledge this card.", show_alert=True)
        return

    # Update database
    await db.record_reaction(log_id, reaction_key, reaction_label)

    # 1. Update the recipient's card view
    partner_id, sender_name, partner_name = config.get_partner_info(entry["sender_id"])
    note_line = f"\n📝 *Note*: _{entry['note']}_\n" if entry["note"] else ""

    updated_card = (
        "💌 *TwoTone Message*\n"
        f"From: *{sender_name}*\n\n"
        f"💭 *Feeling*: {entry['emotion_label']}\n"
        f"🎯 *Need*: {entry['need_label']}"
        f"{note_line}\n"
        f"✅ *You acknowledged this with*: {reaction_label}"
    )

    # Keep a gentle reply button available
    follow_up_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Send Gentle Follow-up Note", callback_data=f"reply:{log_id}")]
    ])

    try:
        await query.edit_message_text(
            updated_card, reply_markup=follow_up_markup, parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Could not edit card message: {e}")

    await query.answer(f"Sent: {reaction_label}")

    # 2. Notify the original sender
    sender_notification = (
        f"🤍 *{partner_name} acknowledged your feeling*\n\n"
        f"• **Your feeling**: {entry['emotion_label']}\n"
        f"• **Their response**: {reaction_label}\n\n"
        "_You are held, heard, and cared for._"
    )

    try:
        await context.bot.send_message(
            chat_id=entry["sender_id"],
            text=sender_notification,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to notify original sender {entry['sender_id']}: {e}")


async def reply_prompt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt the partner to write a gentle custom reply."""
    query = update.callback_query
    if not query or not query.data:
        return

    parts = query.data.split(":")
    if len(parts) != 2 or parts[0] != "reply":
        return

    log_id = int(parts[1])
    user = update.effective_user

    entry = await db.get_emotion_by_id(log_id)
    if not entry or user.id != entry["recipient_id"]:
        await query.answer("Unauthorized.", show_alert=True)
        return

    await query.answer()
    context.user_data["pending_reply_log_id"] = log_id

    sender_name = config.get_sender_name(entry["sender_id"])
    prompt = (
        f"💬 *Reply to {sender_name}:*\n\n"
        "Type your gentle thoughts, comfort, or reassurance below and send it.\n"
        "Or type `/cancel` to dismiss."
    )
    await query.message.reply_text(prompt, parse_mode="Markdown")


async def reply_text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text message when pending_reply_log_id is active."""
    log_id = context.user_data.get("pending_reply_log_id")
    if not log_id:
        return

    reply_text = update.message.text.strip() if update.message and update.message.text else ""
    if not reply_text:
        return

    entry = await db.get_emotion_by_id(log_id)
    if not entry:
        context.user_data.pop("pending_reply_log_id", None)
        return

    user = update.effective_user
    partner_name = config.get_sender_name(user.id)
    sender_name = config.get_sender_name(entry["sender_id"])

    # Save reply note in database
    await db.record_reply_note(log_id, reply_text)
    context.user_data.pop("pending_reply_log_id", None)

    # Deliver to original sender
    msg_to_sender = (
        f"💌 *Gentle reply from {partner_name}:*\n\n"
        f"_{reply_text}_\n\n"
        f"_(In response to: {entry['emotion_label']})_"
    )
    try:
        await context.bot.send_message(
            chat_id=entry["sender_id"],
            text=msg_to_sender,
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            f"🕊️ Delivered to {sender_name}.", parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to deliver gentle reply: {e}")
        await update.message.reply_text(
            "⚠️ Could not deliver your reply. Please try again."
        )

"""Handlers for viewing emotional history timeline and shared couple stats."""
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import config
from bot.database import db
from bot.handlers.auth import authorized_only, get_main_reply_keyboard


def _format_time(iso_str: str) -> str:
    """Format ISO timestamp into friendly readable string."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %H:%M")
    except Exception:
        return iso_str[:16] if iso_str else ""


@authorized_only
async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the recent shared emotional history."""
    if update.callback_query:
        await update.callback_query.answer()

    entries = await db.get_history(limit=7)
    if not entries:
        msg = (
            "📖 *Emotional Journal*\n\n"
            "No feelings recorded yet. Whenever either of you shares a feeling "
            "using **🌱 Share a Feeling**, your shared history will be preserved here."
        )
        if update.effective_message:
            await update.effective_message.reply_text(
                msg, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown"
            )
        return

    lines = ["📖 *Shared Emotional Timeline (Recent)*\n"]
    for e in entries:
        sender_name = config.get_sender_name(e["sender_id"])
        time_str = _format_time(e["created_at"])
        status = (
            f"✅ *{e['reaction_label']}*"
            if e.get("reaction_label")
            else "⏳ _Pending acknowledgment_"
        )
        note_str = f"  📝 _{e['note']}_\n" if e.get("note") else ""
        reply_str = f"  💬 _Reply: {e['reply_note']}_\n" if e.get("reply_note") else ""

        entry_text = (
            f"• *{time_str}* — From *{sender_name}*\n"
            f"  💭 {e['emotion_label']}\n"
            f"  🎯 {e['need_label']}\n"
            f"{note_str}"
            f"  Status: {status}\n"
            f"{reply_str}"
        )
        lines.append(entry_text)

    full_text = "\n".join(lines)
    if update.effective_message:
        await update.effective_message.reply_text(
            full_text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown"
        )


@authorized_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display couple's emotional stats and trends."""
    if update.callback_query:
        await update.callback_query.answer()

    stats = await db.get_stats()
    total = stats["total_sent"]
    acked = stats["acknowledged"]
    pct = round((acked / total) * 100) if total > 0 else 0

    category_labels = {
        "vulnerable": "🌱 Vulnerable & Tender",
        "affection": "🤍 Warmth & Affection",
        "heavy": "🌧️ Heavy & Friction",
        "comfort": "🛋️ Comfort & Closeness",
        "custom": "✨ Couple Custom",
    }

    cat_breakdown = []
    for cat_key, count in stats.get("categories", {}).items():
        label = category_labels.get(cat_key, cat_key.capitalize())
        cat_breakdown.append(f"• {label}: **{count}**")

    cat_text = "\n".join(cat_breakdown) if cat_breakdown else "• _No categories recorded yet_"

    text = (
        "📊 *TwoTone Shared Insights*\n\n"
        f"• Total feelings shared: **{total}**\n"
        f"• Acknowledged with care: **{acked}** ({pct}%)\n\n"
        "✨ *Frequencies Shared:*\n"
        f"{cat_text}\n\n"
        "_Every feeling shared is an act of vulnerability and trust._ 🤍"
    )

    if update.effective_message:
        await update.effective_message.reply_text(
            text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown"
        )

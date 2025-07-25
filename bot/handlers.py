# bot/handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import USER_MAP, MOOD_OPTIONS
from bot.utils import load_mood_data, save_mood_data, get_timestamp, count_moods
import asyncio

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[m] for m in MOOD_OPTIONS]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("TwoTone is live. How are you feeling?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = USER_MAP.get(user_id, {}).get("name")
    partner_id = USER_MAP.get(user_id, {}).get("partner_id")

    if not partner_id:
        await update.message.reply_text("You're not in the love circuit 💔")
        return

    mood = update.message.text.strip()
    mood_data = load_mood_data()
    timestamp = get_timestamp()

    if str(user_id) not in mood_data:
        mood_data[str(user_id)] = []
    mood_data[str(user_id)].append({"mood": mood, "time": timestamp})
    save_mood_data(mood_data)

    if mood in MOOD_OPTIONS:
        await update.message.reply_text(f"✅ Mood \"{mood}\" sent.")
        try:
            text = MOOD_OPTIONS[mood].format(sender=user_name)
            await context.bot.send_message(chat_id=partner_id, text=text)
        except:
            await update.message.reply_text("Couldn’t reach your partner 😭")

        if mood == "I'm Mad 😠":
            await asyncio.sleep(1800)
            await context.bot.send_message(chat_id=user_id, text="Still mad? Or cooled down? 🙈")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mood_data = load_mood_data()
    entries = mood_data.get(str(user_id), [])
    if not entries:
        await update.message.reply_text("No mood entries yet 😶")
        return

    counter = count_moods(entries)
    lines = ["📊 Your Mood Stats:"]
    for mood, count in counter.items():
        lines.append(f"{mood} — {count}x")
    await update.message.reply_text("\n".join(lines))

async def send_mood_check(app):
    for user_id in USER_MAP:
        keyboard = [["All Good 😊", "Meh 😐", "Not Great 😶"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        try:
            await app.bot.send_message(chat_id=user_id, text="💭 Mood check. How you feelin’?", reply_markup=reply_markup)
        except:
            continue

# ✅ Custom Message Sender
async def custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = USER_MAP.get(user_id, {}).get("partner_id")

    if not partner_id:
        await update.message.reply_text("You’re not in the partner list.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /sendmsg your message here")
        return

    secret = " ".join(context.args)
    button = InlineKeyboardButton("🔐 Tap to Reveal", callback_data=f"REVEAL|{secret}")
    reply_markup = InlineKeyboardMarkup([[button]])

    await context.bot.send_message(chat_id=partner_id, text="💌 You received a message:", reply_markup=reply_markup)
    await update.message.reply_text("✅ Secret message sent.")

# ✅ Reveal Handler
async def handle_reveal_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("REVEAL|"):
        secret = data.split("|", 1)[1]
        await query.edit_message_text(f"💌 Revealed Message:\n\n{secret}")

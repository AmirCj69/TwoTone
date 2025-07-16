# bot/handlers.py

import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import USER_MAP, MOOD_OPTIONS
from bot.utils import (
    load_mood_data,
    save_mood_data,
    get_timestamp,
    secret_commands,
    count_moods
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[m] for m in MOOD_OPTIONS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("TwoTone is live. How are you feeling?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = USER_MAP.get(user_id, {}).get("name")
    partner_id = USER_MAP.get(user_id, {}).get("partner_id")

    if not partner_id:
        await update.message.reply_text("You're not recognized in this love circuit 💔")
        return

    mood = update.message.text.strip()
    mood_data = load_mood_data()
    timestamp = get_timestamp()

    if str(user_id) not in mood_data:
        mood_data[str(user_id)] = []
    mood_data[str(user_id)].append({"mood": mood, "time": timestamp})
    save_mood_data(mood_data)

    if mood.startswith("/"):
        await update.message.reply_text(secret_commands(mood))
        return

    if mood in MOOD_OPTIONS:
        await update.message.reply_text(f"✅ Your mood \"{mood}\" has been sent.")
        try:
            await context.bot.send_message(chat_id=partner_id, text=f"{user_name} {MOOD_OPTIONS[mood]}")
        except Exception:
            await update.message.reply_text("Couldn't reach your partner. Maybe they need to restart me 😭")

        if mood == "I’m Mad 😡":
            await asyncio.sleep(1800)
            await context.bot.send_message(chat_id=user_id, text="Still feeling mad? Or ready to let it go? 🙗")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mood_data = load_mood_data()
    entries = mood_data.get(str(user_id), [])
    if not entries:
        await update.message.reply_text("You haven’t sent any moods yet 😶")
        return

    counter = count_moods(entries)
    lines = ["📊 Your Mood Stats:"]
    for mood, count in counter.items():
        lines.append(f"{mood} — {count}x")
    await update.message.reply_text("\n".join(lines))

async def send_mood_check(application):
    keyboard = [["All Good 😊", "Meh 😐", "Not Great 😶"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    for user_id in USER_MAP:
        try:
            await application.bot.send_message(
                chat_id=user_id,
                text="💭 Just checking in… how's your mood right now?",
                reply_markup=reply_markup
            )
        except:
            continue

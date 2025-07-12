from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime

# 🧠 REAL user IDs here
BOT_TOKEN = "7889785504:AAGVb24kVk66p_f0HU2YpGaxQO92uVHelpQ"
HE_ID = 499080623   # Your Telegram ID
SHE_ID = 634034210  # Ghazal's Telegram ID

# 🎭 User configuration
USER_MAP = {
    int(HE_ID): {"partner_id": int(SHE_ID), "label": "He"},
    int(SHE_ID): {"partner_id": int(HE_ID), "label": "She"}
}

# 💬 Mood text map
MESSAGE_MAP = {
    "I'm Mad 😠": "💢 {sender} is mad right now.",
    "I'm Not Mad Anymore ✅": "✅ {sender} is not mad anymore. Vibes are back.",
    "I Miss You 💗": "💗 {sender} misses you.",
    "I Need Space 🗳️": "🗳️ {sender} needs a little space right now.",
    "I Need Attention 🧸": "🧸 {sender} needs some love and attention ASAP.",
    "I'm A Moody Bitch Right Now 🌪️": "🌪️ {sender} is in Moody Bitch Mode. Approach with snacks or memes.",
    "I Love You ❤️": "❤️ {sender} loves you deeply.",
    "I'm Sad 😔": "😔 {sender} is feeling down. Be gentle.",
    "There's Something Wrong With Me But I Can't Say It 🫥": "🫥 {sender} is struggling silently. Just be there.",
    "Let’s Reset 🔄": "🔄 {sender} wants to reset the mood. Let’s start fresh.",
    "Please Reassure Me 🥺": "🥺 {sender} needs reassurance. Let them know they’re loved."
}

# 🕒 Mood history
last_moods = {}

# 🕒 Formatter
def format_time(t: datetime):
    return t.strftime("%Y-%m-%d – %I:%M %p")

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["I'm Mad 😠", "I'm Not Mad Anymore ✅"],
        ["I Miss You 💗", "I Need Space 🗳️"],
        ["I Need Attention 🧸", "I'm A Moody Bitch Right Now 🌪️"],
        ["I Love You ❤️", "I'm Sad 😔"],
        ["Let’s Reset 🔄", "Please Reassure Me 🥺"],
        ["There's Something Wrong With Me But I Can't Say It 🫥"]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🎛️ TwoTone is live.\nTap a mood to notify your partner.",
        reply_markup=markup
    )

# ✅ Mood handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in USER_MAP:
        await update.message.reply_text("❌ You're not registered.")
        return

    if text not in MESSAGE_MAP:
        await update.message.reply_text("Please use a button.")
        return

    sender_label = USER_MAP[user_id]["label"]
    partner_id = USER_MAP[user_id]["partner_id"]
    message = MESSAGE_MAP[text].format(sender=sender_label)

    # Store last mood
    last_moods[user_id] = (text, datetime.now())

    await context.bot.send_message(chat_id=partner_id, text=message)
    await update.message.reply_text("✅ Your mood has been sent via TwoTone.")

# ✅ Status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = []
    for user_id, info in USER_MAP.items():
        label = info["label"]
        if user_id in last_moods:
            mood_text, mood_time = last_moods[user_id]
            formatted = format_time(mood_time)
            lines.append(f'Last Mood from {label}: "{mood_text}" — {formatted}')
        else:
            lines.append(f"No mood yet from {label}.")
    await update.message.reply_text("\n".join(lines))

# 🧠 Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("TwoTone is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

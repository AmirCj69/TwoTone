# main.py
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, handle_message, stats, send_mood_check

TOKEN = "your-token-here"

async def post_init(application):
    application.create_task(run_mood_check(application))  # 👈 Run it after app is live

async def main():
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Remove webhook and drop pending updates
    await application.bot.delete_webhook(drop_pending_updates=True)

    # ✅ Run bot
    await application.run_polling()

async def run_mood_check(application):
    while True:
        await asyncio.sleep(3600)  # or whatever your interval is
        await send_mood_check(application)

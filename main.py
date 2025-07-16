# main.py

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.handlers import start, handle_message, stats, send_mood_check

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def run_mood_check(application):
    while True:
        await asyncio.sleep(43200)  # 12 hours
        await send_mood_check(application)

async def post_init(application):
    # This ensures the task runs AFTER bot has started
    application.create_task(run_mood_check(application))

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()

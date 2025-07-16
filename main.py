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

async def run_mood_check(app):
    while True:
        await asyncio.sleep(43200)  # 12 hours
        await send_mood_check(app)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot first
    await app.initialize()
    await app.start()
    app.create_task(run_mood_check(app))  # This is now safe to start
    await app.updater.start_polling()
    await app.updater.wait_for_stop()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

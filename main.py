# main.py

import asyncio
import nest_asyncio
nest_asyncio.apply()

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, handle_message, stats, send_mood_check
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def post_init(application):
    application.create_task(run_mood_check(application))

async def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.run_polling()

async def run_mood_check(application):
    while True:
        await asyncio.sleep(3600)
        await send_mood_check(application)

if __name__ == "__main__":
    asyncio.run(main())

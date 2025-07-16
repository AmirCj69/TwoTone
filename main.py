# main.py
import asyncio
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, handle_message, stats, send_mood_check
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def post_init(application):
    application.create_task(run_mood_check(application))  # Run mood check after start

async def run_mood_check(application):
    while True:
        await asyncio.sleep(3600)  # 1 hour
        await send_mood_check(application)

async def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.run_polling()

# ---- Run main safely even if loop is already running ----
try:
    asyncio.run(main())
except RuntimeError as e:
    if "event loop is already running" in str(e):
        # For environments like Jupyter, Replit etc.
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(main())
    else:
        raise

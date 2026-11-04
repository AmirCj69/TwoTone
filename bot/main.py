"""Main entry point for TwoTone Telegram Bot."""
import asyncio
import logging
import sys
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.config import config
from bot.database import db
from bot.handlers.auth import start_handler, help_handler, myid_handler
from bot.handlers.feel import get_feel_conversation_handler
from bot.handlers.reactions import (
    reaction_callback_handler,
    reply_prompt_handler,
    reply_text_message_handler,
)
from bot.handlers.custom_feelings import (
    get_custom_feeling_conversation_handler,
    list_feelings_handler,
    delete_feeling_callback,
)
from bot.handlers.history import history_handler, stats_handler

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("TwoTone")


async def post_init(application: Application) -> None:
    """Operations performed after application is initialized."""
    # Initialize SQLite database
    await db.init_db()
    logger.info("Database initialized successfully at: %s", config.database_path)

    # Set up Telegram menu commands
    commands = [
        BotCommand("feel", "Share a feeling gently"),
        BotCommand("history", "View shared emotional timeline"),
        BotCommand("stats", "View shared emotional insights"),
        BotCommand("add_feeling", "Add a custom feeling tag"),
        BotCommand("list_feelings", "Manage custom feelings"),
        BotCommand("help", "How TwoTone works"),
        BotCommand("myid", "View your Telegram ID"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands registered successfully.")
    except Exception as e:
        logger.warning("Could not set bot commands: %s", e)


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and inform the user gently."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "🤍 Something went wrong processing that request. Please try /feel again."
            )
        except Exception:
            pass


def create_application() -> Application:
    """Build and configure the Telegram application."""
    if not config.bot_token:
        logger.error("BOT_TOKEN is not configured! Please set it in your .env file.")

    application = (
        Application.builder()
        .token(config.bot_token or "DUMMY_TOKEN_FOR_TESTING")
        .post_init(post_init)
        .build()
    )

    # 0. Global Error Handler
    application.add_error_handler(global_error_handler)

    # 1. Conversation handlers (Must be registered before general message handlers)
    application.add_handler(get_feel_conversation_handler())
    application.add_handler(get_custom_feeling_conversation_handler())

    # 2. Command & Persistent Button handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(MessageHandler(filters.Regex("^❓ Guide$"), help_handler))
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(MessageHandler(filters.Regex("^📖 Journal$"), history_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(MessageHandler(filters.Regex("^📊 Insights$"), stats_handler))
    application.add_handler(CommandHandler("list_feelings", list_feelings_handler))
    application.add_handler(MessageHandler(filters.Regex("^✨ Custom Feelings$"), list_feelings_handler))

    # 3. Callback handlers
    application.add_handler(CallbackQueryHandler(reaction_callback_handler, pattern="^react:"))
    application.add_handler(CallbackQueryHandler(reply_prompt_handler, pattern="^reply:"))
    application.add_handler(CallbackQueryHandler(delete_feeling_callback, pattern="^del_cf:"))
    application.add_handler(CallbackQueryHandler(history_handler, pattern="^menu:history$"))
    application.add_handler(CallbackQueryHandler(stats_handler, pattern="^menu:stats$"))
    application.add_handler(CallbackQueryHandler(help_handler, pattern="^menu:help$"))
    application.add_handler(CallbackQueryHandler(list_feelings_handler, pattern="^menu:custom$"))

    # 4. Fallback text handler for gentle replies
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply_text_message_handler)
    )

    return application


def main() -> None:
    """Run the bot in polling mode."""
    if not config.bot_token:
        print("\n" + "=" * 60)
        print("ERROR: BOT_TOKEN is missing!")
        print("Please copy .env.example to .env and fill in your Bot Token.")
        print("=" * 60 + "\n")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("TwoTone Couples Bot Starting Up...")
    print(f"Partner A: {config.user_a_name} (ID: {config.user_a_id})")
    print(f"Partner B: {config.user_b_name} (ID: {config.user_b_id})")
    print(f"Database: {config.database_path}")
    print("=" * 60 + "\n")

    app = create_application()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

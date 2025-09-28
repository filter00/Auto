import os
from dotenv import load_dotenv
from telegram import __version__ as ptb_version
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import asyncio

from handlers.message_handler import on_message
from utils.logger import get_logger

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

DELETE_DELAY = int(os.getenv("DELETE_DELAY", "10"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_DELETES", "4"))

logger = get_logger("bot")
logger.info(f"python-telegram-bot version: {ptb_version}")

def main():
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Put shared objects in bot_data
    app.bot_data["DELETE_DELAY"] = DELETE_DELAY
    app.bot_data["DELETE_SEMAPHORE"] = asyncio.Semaphore(MAX_CONCURRENT)

    # Handle all messages except service updates (like new_chat_member, etc.)
    app.add_handler(MessageHandler(filters.ALL & (~filters.StatusUpdate), on_message))

    logger.info("Starting bot (run_polling)...")
    app.run_polling(allowed_updates=None)  # blocking

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")

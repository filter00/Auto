import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import get_logger

logger = get_logger("message_handler")

async def bot_can_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    try:
        bot_id = context.bot.id
        member = await context.bot.get_chat_member(chat_id, bot_id)
        # If bot is creator or admin with can_delete_messages -> OK
        if member.status == "creator":
            return True
        if member.status == "administrator":
            return bool(getattr(member, "can_delete_messages", False))
        return False
    except Exception as e:
        logger.exception("Failed to check bot chat member: %s", e)
        return False

async def schedule_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, author_info: str, delay: int):
    await asyncio.sleep(delay)
    sem = context.bot_data.get("DELETE_SEMAPHORE")
    if sem is None:
        sem = asyncio.Semaphore(4)
    async with sem:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info("Deleted message %s from %s in chat %s", message_id, author_info, chat_id)
        except Exception as e:
            # Common reasons: already deleted, insufficient permissions, message too old in channels, network issues
            logger.warning("Could not delete message %s in chat %s: %s", message_id, chat_id, e)

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called for every message (excluding StatusUpdate). Schedules deletion after DELETE_DELAY seconds.
    This WILL attempt to delete admins' messages as well.
    """
    message = update.effective_message
    if not message:
        return

    # Optionally ignore bot messages (comment out if you want to delete bot messages too)
    if message.from_user and message.from_user.is_bot:
        return

    chat_id = message.chat_id
    message_id = message.message_id
    author = message.from_user
    author_info = f"{author.id}:{author.username or author.full_name}"

    # Check if bot has permission to delete in this chat
    can_delete = await bot_can_delete(context, chat_id)
    if not can_delete:
        logger.warning("Bot lacks delete permission in chat %s. Skipping deletion of message %s (%s).", chat_id, message_id, author_info)
        return

    # Log if message is from admin/creator (we still delete)
    try:
        member = await context.bot.get_chat_member(chat_id, author.id)
        if member.status in ("administrator", "creator"):
            logger.info("Scheduling deletion of ADMIN message %s by %s in chat %s", message_id, author_info, chat_id)
        else:
            logger.debug("Scheduling deletion of message %s by %s in chat %s", message_id, author_info, chat_id)
    except Exception:
        pass

    delay = int(context.bot_data.get("DELETE_DELAY", os.getenv("DELETE_DELAY", 10)))
    # Schedule deletion task
    context.application.create_task(schedule_delete(context, chat_id, message_id, author_info, delay))

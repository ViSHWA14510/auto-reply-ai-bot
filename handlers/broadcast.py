import asyncio
import time

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest, RetryAfter, TelegramError

import database
from config import ADMIN_IDS

# How often the live status message is allowed to refresh (seconds).
# Keeps us comfortably under Telegram's edit-rate limits.
STATUS_REFRESH_INTERVAL = 2.5

# Tiny delay between sends so we don't trip Telegram's global flood limits.
SEND_DELAY = 0.05


def _progress_text(total: int, done: int, sent: int, blocked: int, failed: int, finished: bool = False) -> str:
    header = "✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ" if finished else "📡 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ..."
    return (
        f"{header}\n\n"
        f"👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total}\n"
        f"📨 sᴇɴᴛ: {sent}\n"
        f"🚫 ʙʟᴏᴄᴋᴇᴅ (ʀᴇᴍᴏᴠᴇᴅ): {blocked}\n"
        f"⚠️ ꜰᴀɪʟᴇᴅ: {failed}\n"
        f"📊 ᴘʀᴏɢʀᴇss: {done}/{total}"
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: reply to the message you want to send to everyone with /broadcast"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return  # silently ignore non-admins

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Reply to the message you want to broadcast with the /broadcast command."
        )
        return

    source = update.message.reply_to_message
    user_ids = database.get_all_user_ids()
    total = len(user_ids)

    if total == 0:
        await update.message.reply_text("No users in the database yet.")
        return

    sent = blocked = failed = 0
    status = await update.message.reply_text(_progress_text(total, 0, sent, blocked, failed))
    last_refresh = time.monotonic()

    for i, uid in enumerate(user_ids, start=1):
        while True:
            try:
                await context.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=source.chat_id,
                    message_id=source.message_id,
                )
                sent += 1
                break
            except Forbidden:
                # User blocked the bot — remove them so future broadcasts skip them
                database.remove_user(uid)
                blocked += 1
                break
            except RetryAfter as e:
                # Telegram flood control — wait it out, then retry this same user
                await asyncio.sleep(e.retry_after + 0.5)
                continue
            except (BadRequest, TelegramError):
                failed += 1
                break

        # Refresh the live status message — throttled by time, and always on the last user
        now = time.monotonic()
        if i == total or (now - last_refresh) >= STATUS_REFRESH_INTERVAL:
            try:
                await status.edit_text(_progress_text(total, i, sent, blocked, failed))
            except TelegramError:
                pass
            last_refresh = now

        await asyncio.sleep(SEND_DELAY)

    await status.edit_text(_progress_text(total, total, sent, blocked, failed, finished=True))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    count = database.get_user_count()
    await update.message.reply_text(f"📊 Total users in database: {count}")

"""
Generic handler for free-text messages / user queries.

Behaviour:
- If the admin is marked OFFLINE (/offline) and the AI assistant is enabled,
  the bot replies instantly using the configured AI provider, and still
  notifies the admin (tagged as an auto-reply) so they can see what was asked
  and step in if needed.
- Otherwise — admin ONLINE, AI disabled, or the AI call fails for any reason —
  the message is simply forwarded to the admin and the user gets a polite
  acknowledgement, exactly like before. The bot never leaves a user with no
  response at all.
- An admin can REPLY (in Telegram, swipe/long-press -> Reply) to any of these
  notification messages, and whatever they type is relayed straight back to
  that user — see _try_relay_admin_reply() below.

Every admin notification includes the user's Telegram ID as a tappable
monospace code block, so you can copy it with one tap on mobile.
"""

from html import escape

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, TelegramError

import database
from config import ADMIN_IDS, AI_ENABLED
from utils import to_small_caps, bold

try:
    from ai_assistant import get_ai_reply
except Exception as e:  # missing package, bad import-time config, etc.
    print(f"[messages] AI assistant unavailable: {e}")
    get_ai_reply = None


async def _notify_admins(context: ContextTypes.DEFAULT_TYPE, text: str, user_id: int):
    """Sends `text` to every admin and remembers which user each copy is about,
    so a reply to that specific message can be relayed back to the right person."""
    for admin_id in ADMIN_IDS:
        try:
            sent = await context.bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
            database.save_notification(admin_id, sent.message_id, user_id)
        except Exception:
            pass


def _user_header(user) -> str:
    name = escape(user.first_name or "")
    username = escape(user.username or "no_username")
    return f"<b>{name}</b> (@{username}, id: <code>{user.id}</code>)"


async def _try_relay_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """If this message is an admin replying to a tracked notification, relays
    the reply to the original user and returns True. Returns False (does
    nothing) if it's not a tracked reply, so the caller can fall through to
    the normal message-handling flow."""
    message = update.message
    if not message.reply_to_message:
        return False

    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        return False

    target_user_id = database.get_notification_user(admin_id, message.reply_to_message.message_id)
    if target_user_id is None:
        return False  # not a reply to a tracked notification — let it fall through

    try:
        # copy_message (rather than send_message) so photos/files/etc. work too, not just text
        await context.bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )
        await message.reply_text("✅ Sent to user.")
    except Forbidden:
        await message.reply_text("⚠️ Couldn't deliver — this user has blocked the bot.")
    except TelegramError as e:
        await message.reply_text(f"⚠️ Failed to send: {e}")

    return True


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for any message that is a reply, sent by an admin. Handles
    photos/documents/etc. too (via copy_message), not just plain text.
    Falls back to the normal handle_message flow if this turns out not to be
    a reply to a tracked notification (e.g. it expired/was pruned) and the
    admin's message has text."""
    if await _try_relay_admin_reply(update, context):
        return
    if update.message.text:
        await handle_message(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _try_relay_admin_reply(update, context):
        return

    user = update.effective_user
    text = update.message.text

    should_use_ai = AI_ENABLED and get_ai_reply is not None and not database.is_admin_online()

    if should_use_ai:
        ai_reply = get_ai_reply(user.id, text, user.first_name)
        if ai_reply:
            await update.message.reply_text(ai_reply)
            await _notify_admins(
                context,
                f"🤖 Auto-replied (you're offline) to {_user_header(user)}:\n\n"
                f"❓ {escape(text)}\n\n💬 {escape(ai_reply)}\n\n"
                f"<i>Reply to this message to send a follow-up yourself.</i>",
                user.id,
            )
            return
        # AI call failed — fall through to the manual flow below

    await _notify_admins(
        context,
        f"📩 New message from {_user_header(user)}:\n\n{escape(text)}\n\n"
        f"<i>Reply to this message to answer them directly.</i>",
        user.id,
    )
    reply = bold(to_small_caps(
        "thanks for reaching out! 🙏\n"
        "your message has been received and our team will get back to you shortly."
    ))
    await update.message.reply_text(reply, parse_mode="HTML")

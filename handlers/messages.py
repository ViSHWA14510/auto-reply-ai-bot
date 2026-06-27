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

Every admin notification includes the user's Telegram ID as a tappable
monospace code block, so you can copy it with one tap on mobile.
"""

from html import escape

from telegram import Update
from telegram.ext import ContextTypes

import database
from config import ADMIN_IDS, AI_ENABLED
from utils import to_small_caps

try:
    from ai_assistant import get_ai_reply
except Exception as e:  # missing package, bad import-time config, etc.
    print(f"[messages] AI assistant unavailable: {e}")
    get_ai_reply = None


async def _notify_admins(context: ContextTypes.DEFAULT_TYPE, text: str):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception:
            pass


def _user_header(user) -> str:
    name = escape(user.first_name or "")
    username = escape(user.username or "no_username")
    return f"<b>{name}</b> (@{username}, id: <code>{user.id}</code>)"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                f"❓ {escape(text)}\n\n💬 {escape(ai_reply)}",
            )
            return
        # AI call failed — fall through to the manual flow below

    await _notify_admins(
        context,
        f"📩 New message from {_user_header(user)}:\n\n{escape(text)}",
    )
    reply = to_small_caps(
        "thanks for reaching out! 🙏\n"
        "your message has been received and our team will get back to you shortly."
    )
    await update.message.reply_text(reply)

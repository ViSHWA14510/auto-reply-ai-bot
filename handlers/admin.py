from telegram import Update
from telegram.ext import ContextTypes

import database
from config import ADMIN_IDS


async def online_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    database.set_admin_status("online")
    await update.message.reply_text(
        "🟢 You're marked as online.\n"
        "The AI assistant will stay quiet — user messages will be forwarded to you as usual."
    )


async def offline_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    database.set_admin_status("offline")
    await update.message.reply_text(
        "🔴 You're marked as offline.\n"
        "The AI assistant will now auto-reply to users instantly, and will still "
        "notify you of every conversation so you can step in anytime."
    )


async def admin_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    status = "🟢 online" if database.is_admin_online() else "🔴 offline (AI assisting users)"
    await update.message.reply_text(f"Current status: {status}")

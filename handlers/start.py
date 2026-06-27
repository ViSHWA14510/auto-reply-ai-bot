from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database
from utils import to_small_caps, bold
from config import WELCOME_PHOTO


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.add_user(user.id, user.username, user.first_name)

    caption = bold(to_small_caps(
        "welcome aboard! 🎉\n\n"
        "we're delighted to have you here 💫\n"
        "this bot keeps you updated and connected with our community.\n\n"
        "📌 send /link anytime to get our official channel links\n"
        "💬 just type your question below, we're happy to help"
    ))

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(to_small_caps("get channel links 🔗"), callback_data="show_links")]
    ])

    try:
        await update.message.reply_photo(
            photo=WELCOME_PHOTO,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception:
        # Falls back to text-only if the photo URL/path is invalid or unreachable
        await update.message.reply_text(caption, parse_mode="HTML", reply_markup=keyboard)

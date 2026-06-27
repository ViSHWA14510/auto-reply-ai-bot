import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import CHANNELS, LINK_EXPIRY_SECONDS
from utils import to_small_caps, bold


async def _generate_links(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Create one fresh, single-use invite link per channel for this user.
    Each link auto-expires after LINK_EXPIRY_SECONDS (default: 1 hour).
    """
    buttons = []
    expire_unix = int(time.time()) + LINK_EXPIRY_SECONDS

    for label, chat_id in CHANNELS.items():
        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"user_{user_id}_{int(time.time())}",
                expire_date=expire_unix,
                member_limit=1,  # one-time use — just for this user
            )
            # Buttons can't render bold/HTML formatting, so this stays small-caps only.
            buttons.append([InlineKeyboardButton(to_small_caps(label), url=invite.invite_link)])

            # Telegram already auto-expires the link via expire_date. This job is a
            # belt-and-suspenders explicit revoke, which also removes it immediately
            # from the channel's "manage invite links" list.
            if context.job_queue:
                context.job_queue.run_once(
                    _revoke_link_job,
                    when=LINK_EXPIRY_SECONDS,
                    data={"chat_id": chat_id, "invite_link": invite.invite_link},
                    name=f"revoke_{user_id}_{chat_id}",
                )
        except TelegramError as e:
            # Most likely cause: bot is not an admin in that channel/group
            print(f"[link] Failed to create invite for {chat_id}: {e}")

    return buttons


async def _revoke_link_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    try:
        await context.bot.revoke_chat_invite_link(
            chat_id=data["chat_id"], invite_link=data["invite_link"]
        )
    except TelegramError as e:
        print(f"[link] Revoke skipped (likely already expired/used): {e}")


def _links_text():
    return bold(to_small_caps(
        "here are our official channel links 👇\n\n"
        "for your security, each link is personal and works only once.\n"
        "it will expire automatically in 1 hour, so please join now!"
    ))


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    buttons = await _generate_links(context, user_id)

    if not buttons:
        await update.effective_message.reply_text(
            bold(to_small_caps("sorry, links are unavailable right now. please try again later.")),
            parse_mode="HTML",
        )
        return

    await update.effective_message.reply_text(
        _links_text(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def link_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline 'Get Channel Links' button shown on /start."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    buttons = await _generate_links(context, user_id)

    if not buttons:
        await query.message.reply_text(
            bold(to_small_caps("sorry, links are unavailable right now.")), parse_mode="HTML"
        )
        return

    await query.message.reply_text(
        _links_text(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)
    )

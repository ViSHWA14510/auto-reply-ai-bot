import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import database
from config import BOT_TOKEN, ADMIN_IDS
from handlers.start import start
from handlers.link import link_command, link_button_callback
from handlers.broadcast import broadcast_command, stats_command
from handlers.admin import online_command, offline_command, admin_status_command
from handlers.messages import handle_message, handle_admin_reply

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main():
    database.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    if app.job_queue:
        app.job_queue.run_repeating(
            lambda context: database.prune_old_notifications(),
            interval=24 * 60 * 60,  # once a day
            first=60,  # small delay after startup
            name="prune_old_notifications",
        )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("online", online_command))
    app.add_handler(CommandHandler("offline", offline_command))
    app.add_handler(CommandHandler("status", admin_status_command))
    app.add_handler(CallbackQueryHandler(link_button_callback, pattern="^show_links$"))
    # Must be registered BEFORE the generic text handler below: this catches
    # any reply (text, photo, document, etc.) from an admin first, and relays
    # it to the original user if it's a reply to a tracked notification.
    app.add_handler(
        MessageHandler(filters.REPLY & filters.User(user_id=ADMIN_IDS) & ~filters.COMMAND, handle_admin_reply)
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()

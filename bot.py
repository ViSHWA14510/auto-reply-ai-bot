import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import database
from config import BOT_TOKEN
from handlers.start import start
from handlers.link import link_command, link_button_callback
from handlers.broadcast import broadcast_command, stats_command
from handlers.admin import online_command, offline_command, admin_status_command
from handlers.messages import handle_message

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main():
    database.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("online", online_command))
    app.add_handler(CommandHandler("offline", offline_command))
    app.add_handler(CommandHandler("status", admin_status_command))
    app.add_handler(CallbackQueryHandler(link_button_callback, pattern="^show_links$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()

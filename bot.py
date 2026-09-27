"""
PAWNS Investment Bot - Main Entry Point
"""
import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from database import init_db
from handlers import (
    start_handler, my_investment_handler, withdrawal_handler,
    transaction_history_handler, support_handler,
    admin_handler, button_handler, message_handler
)
from scheduler import start_scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    # Initialize database
    init_db()
    logger.info("Database initialized.")

    # Build application
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_handler))

    # Callback query handler (button presses)
    app.add_handler(CallbackQueryHandler(button_handler))

    # Message handler (for text input during conversations)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Start background scheduler (notifications, maturity checks)
    start_scheduler(app)

    logger.info("PAWNS Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

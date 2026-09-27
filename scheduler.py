"""
PAWNS Bot — Background Scheduler
Handles: maturity checks, investor notifications
"""
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.constants import ParseMode

import database as db
import messages as msg
import keyboards as kb
from utils import is_matured, investment_remaining_seconds

logger = logging.getLogger(__name__)


async def check_maturities(bot):
    """Check all active investments and send notifications / unlock withdrawals."""
    investments = db.get_all_active_investments()
    now = datetime.now(timezone.utc)

    for inv in investments:
        inv_id = inv['investment_id']
        telegram_id = inv['telegram_id']
        maturity_ts = inv['maturity_ts']

        remaining = investment_remaining_seconds(maturity_ts)

        # ── Maturity reached ──────────────────────────────────
        if is_matured(maturity_ts) and not inv['notified_maturity']:
            db.update_investment_status(inv_id, status='ACTIVE', withdrawal_eligible=1)
            db.mark_notified(inv_id, 'notified_maturity')
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=msg.notif_matured(),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=kb.withdrawal_available_keyboard()
                )
                logger.info(f"Maturity notification sent: {inv_id}")
            except Exception as e:
                logger.warning(f"Could not notify {telegram_id}: {e}")
            continue

        # ── 7 days before ────────────────────────────────────
        if remaining <= 7 * 86400 and remaining > 6 * 86400 and not inv['notified_7d']:
            db.mark_notified(inv_id, 'notified_7d')
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=msg.notif_7days(),
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"7-day notification sent: {inv_id}")
            except Exception as e:
                logger.warning(f"Could not notify {telegram_id}: {e}")

        # ── 24 hours before ──────────────────────────────────
        if remaining <= 86400 and remaining > 82800 and not inv['notified_24h']:
            db.mark_notified(inv_id, 'notified_24h')
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=msg.notif_24hours(),
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"24-hour notification sent: {inv_id}")
            except Exception as e:
                logger.warning(f"Could not notify {telegram_id}: {e}")


def start_scheduler(app):
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_maturities,
        trigger='interval',
        minutes=5,  # Check every 5 minutes
        args=[app.bot],
        id='maturity_check',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started (maturity check every 5 minutes).")
    return scheduler

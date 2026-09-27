"""
PAWNS Bot — All update handlers
"""
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import database as db
import messages as msg
import keyboards as kb
from config import (
    ADMIN_IDS, SUPER_ADMIN_ID, INVESTMENT_PLANS,
    MIN_WITHDRAWAL, MAX_WITHDRAWAL, SUPPORTED_NETWORKS,
    STATE_IDLE, STATE_AWAIT_WITHDRAWAL_AMOUNT,
    STATE_AWAIT_WALLET_ADDRESS, STATE_AWAIT_NETWORK,
    STATE_CONFIRM_WITHDRAWAL, STATE_ADMIN_AWAIT_VERIFY_ID,
    STATE_ADMIN_AWAIT_AMOUNT, STATE_ADMIN_AWAIT_PLAN,
    STATE_ADMIN_AWAIT_REJECT_REASON,
)
from utils import investment_remaining_seconds, is_matured, format_currency

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────

def is_admin(user_id):
    return user_id in ADMIN_IDS or user_id == SUPER_ADMIN_ID


async def send_or_edit(update, text, keyboard=None, parse_mode=ParseMode.MARKDOWN):
    """Send a new message or edit the existing one if from a callback."""
    kw = dict(text=text, parse_mode=parse_mode, reply_markup=keyboard)
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(**kw)
        except Exception:
            await update.callback_query.message.reply_text(**kw)
    else:
        await update.message.reply_text(**kw)


# ── /start ────────────────────────────────────────────────────

async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.upsert_investor(user.id, user.username, user.full_name)
    db.set_investor_state(user.id, STATE_IDLE)
    text = (
        f"*Welcome to PAWNS Investment ♟️*\n\n"
        f"Hello {user.first_name},\n\n"
        f"Use the menu below to manage your investment."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=kb.main_menu_keyboard())


# ── /admin ────────────────────────────────────────────────────

async def admin_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return
    await update.message.reply_text(
        "*PAWNS Admin Panel*", parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb.admin_main_keyboard()
    )


# ── my_investment ─────────────────────────────────────────────

async def my_investment_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    inv = db.get_active_investment(user_id)
    if not inv:
        await send_or_edit(update, msg.no_investment_msg(), kb.back_to_main_keyboard())
        return
    remaining = investment_remaining_seconds(inv['maturity_ts'])
    text = msg.investment_dashboard_msg(inv, remaining)
    await send_or_edit(update, text, kb.investment_dashboard_keyboard())


# ── withdrawal ────────────────────────────────────────────────

async def withdrawal_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    inv = db.get_active_investment(user_id)
    if not inv:
        await send_or_edit(update, msg.no_investment_msg(), kb.back_to_main_keyboard())
        return

    remaining = investment_remaining_seconds(inv['maturity_ts'])

    if not is_matured(inv['maturity_ts']):
        # LOCKED
        text = msg.withdrawal_locked_msg(remaining)
        await send_or_edit(update, text, kb.withdrawal_locked_keyboard())
        return

    # Check for pending withdrawal
    pending = db.get_pending_withdrawal(user_id)
    if pending:
        await send_or_edit(
            update,
            f"⏳ You already have a pending withdrawal request.\n\n"
            f"Request ID: `{pending['request_id']}`\n"
            f"Status: *{pending['status']}*",
            kb.back_to_main_keyboard()
        )
        return

    # AVAILABLE
    text = msg.withdrawal_available_msg(inv)
    await send_or_edit(update, text, kb.withdrawal_available_keyboard())


async def request_withdrawal_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    inv = db.get_active_investment(user_id)
    if not inv or not is_matured(inv['maturity_ts']):
        await send_or_edit(update, "⛔ Withdrawal is not available yet.")
        return

    db.set_investor_state(user_id, STATE_AWAIT_WITHDRAWAL_AMOUNT,
                          {"investment_id": inv['investment_id'],
                           "available": inv['recorded_balance']})
    text = msg.withdrawal_request_msg(inv['recorded_balance'])
    await send_or_edit(update, text, kb.back_to_main_keyboard())


# ── transaction history ───────────────────────────────────────

async def transaction_history_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = db.get_withdrawal_history(user_id)
    text = msg.transaction_history_msg(history)
    await send_or_edit(update, text, kb.back_to_main_keyboard())


# ── support ───────────────────────────────────────────────────

async def support_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *PAWNS Support*\n\n"
        "For assistance, please contact our support team.\n\n"
        "_A support agent will respond shortly._"
    )
    await send_or_edit(update, text, kb.back_to_main_keyboard())


# ── agreement ─────────────────────────────────────────────────

async def agreement_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    inv = db.get_active_investment(user_id)
    if not inv:
        await send_or_edit(update, "No active investment found.", kb.back_to_main_keyboard())
        return
    text = (
        f"📄 *INVESTMENT AGREEMENT*\n\n"
        f"Investment ID: `{inv['investment_id']}`\n"
        f"Contract Version: {inv['contract_version']}\n\n"
        f"Your investment agreement is on file with PAWNS.\n"
        f"Please contact support if you require a copy."
    )
    await send_or_edit(update, text, kb.back_to_main_keyboard())


# ── Admin: verify payment ─────────────────────────────────────

async def admin_verify_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.set_investor_state(user_id, STATE_ADMIN_AWAIT_VERIFY_ID)
    await send_or_edit(update, "Enter the investor's *Telegram User ID* to verify payment:",
                       kb.back_to_main_keyboard())


async def admin_pending_withdrawals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pending = db.get_all_pending_withdrawals()
    if not pending:
        await send_or_edit(update, "✅ No pending withdrawals.", kb.admin_main_keyboard())
        return
    for wd in pending:
        investor = db.get_investor(wd['telegram_id'])
        inv = db.get_investment_by_id(wd['investment_id'])
        text = msg.admin_new_withdrawal_msg(investor, wd, inv)
        await update.callback_query.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb.admin_withdrawal_keyboard(wd['request_id'])
        )


async def admin_approve_withdrawal(update: Update, ctx: ContextTypes.DEFAULT_TYPE, request_id: str):
    admin_id = update.effective_user.id
    wd = db.get_withdrawal_by_id(request_id)
    if not wd:
        await send_or_edit(update, "Withdrawal not found.")
        return
    db.update_withdrawal_status(request_id, "APPROVED", admin_id=admin_id, note="Approved by admin")
    db.write_audit(admin_id, "APPROVE_WITHDRAWAL", target_id=request_id)

    # Notify investor
    try:
        await ctx.bot.send_message(
            chat_id=wd['telegram_id'],
            text=(f"✅ *PAWNS:* Your withdrawal request `{request_id}` has been *approved* "
                  f"and is being processed."),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.warning(f"Could not notify investor: {e}")

    await send_or_edit(update, f"✅ Withdrawal `{request_id}` approved.", kb.admin_main_keyboard())


async def admin_reject_withdrawal(update: Update, ctx: ContextTypes.DEFAULT_TYPE, request_id: str):
    admin_id = update.effective_user.id
    db.set_investor_state(admin_id, STATE_ADMIN_AWAIT_REJECT_REASON,
                          {"request_id": request_id})
    await send_or_edit(update, f"Enter rejection reason for `{request_id}`:")


# ── Main button router ────────────────────────────────────────

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data == "main_menu":
        await send_or_edit(update, "♟️ *PAWNS Investment Menu*",
                           kb.main_menu_keyboard())
    elif data == "my_investment":
        await my_investment_handler(update, ctx)
    elif data == "withdraw":
        await withdrawal_handler(update, ctx)
    elif data == "request_withdrawal":
        await request_withdrawal_handler(update, ctx)
    elif data == "tx_history":
        await transaction_history_handler(update, ctx)
    elif data == "support":
        await support_handler(update, ctx)
    elif data == "agreement":
        await agreement_handler(update, ctx)

    # Network selection
    elif data.startswith("net_"):
        network = data[4:]
        state, state_data = db.get_investor_state(user_id)
        if state != STATE_AWAIT_NETWORK:
            return
        state_data['network'] = network
        db.set_investor_state(user_id, STATE_CONFIRM_WITHDRAWAL, state_data)
        text = msg.withdrawal_confirm_msg(
            state_data['amount'], network, state_data['wallet']
        )
        await send_or_edit(update, text, kb.confirm_withdrawal_keyboard())

    elif data == "confirm_withdrawal":
        await handle_confirm_withdrawal(update, ctx)

    # Admin actions
    elif data == "admin_verify" and is_admin(user_id):
        await admin_verify_start(update, ctx)
    elif data == "admin_pending_wd" and is_admin(user_id):
        await admin_pending_withdrawals(update, ctx)
    elif data == "admin_all_inv" and is_admin(user_id):
        await admin_all_investments(update, ctx)
    elif data == "admin_audit" and is_admin(user_id):
        await admin_audit_log(update, ctx)
    elif data.startswith("wd_approve_") and is_admin(user_id):
        request_id = data[len("wd_approve_"):]
        await admin_approve_withdrawal(update, ctx, request_id)
    elif data.startswith("wd_reject_") and is_admin(user_id):
        request_id = data[len("wd_reject_"):]
        await admin_reject_withdrawal(update, ctx, request_id)
    elif data.startswith("wd_view_") and is_admin(user_id):
        request_id = data[len("wd_view_"):]
        wd = db.get_withdrawal_by_id(request_id)
        inv = db.get_investment_by_id(wd['investment_id']) if wd else None
        if inv:
            remaining = investment_remaining_seconds(inv['maturity_ts'])
            text = msg.investment_dashboard_msg(inv, remaining)
            await send_or_edit(update, text, kb.admin_main_keyboard())
    elif data.startswith("wd_contact_") and is_admin(user_id):
        request_id = data[len("wd_contact_"):]
        wd = db.get_withdrawal_by_id(request_id)
        if wd:
            investor = db.get_investor(wd['telegram_id'])
            username = investor['username'] if investor else None
            if username:
                await send_or_edit(update, f"Contact investor: @{username}", kb.admin_main_keyboard())
            else:
                await send_or_edit(update,
                                   f"Investor Telegram ID: `{wd['telegram_id']}`\nNo username set.",
                                   kb.admin_main_keyboard())


async def handle_confirm_withdrawal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state, state_data = db.get_investor_state(user_id)
    if state != STATE_CONFIRM_WITHDRAWAL:
        return

    req_id = db.create_withdrawal(
        investment_id=state_data['investment_id'],
        telegram_id=user_id,
        amount=state_data['amount'],
        wallet=state_data['wallet'],
        network=state_data['network']
    )
    db.set_investor_state(user_id, STATE_IDLE)

    text = msg.withdrawal_submitted_msg(req_id, state_data['amount'])
    await send_or_edit(update, text, kb.withdrawal_submitted_keyboard())

    # Notify admins
    investor = db.get_investor(user_id)
    wd = db.get_withdrawal_by_id(req_id)
    inv = db.get_investment_by_id(state_data['investment_id'])
    admin_text = msg.admin_new_withdrawal_msg(investor, wd, inv)
    for admin_id in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb.admin_withdrawal_keyboard(req_id)
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")


# ── Text message router (conversation states) ─────────────────

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state, state_data = db.get_investor_state(user_id)

    if state == STATE_AWAIT_WITHDRAWAL_AMOUNT:
        await handle_withdrawal_amount(update, ctx, text, state_data)

    elif state == STATE_AWAIT_WALLET_ADDRESS:
        state_data['wallet'] = text
        db.set_investor_state(user_id, STATE_AWAIT_NETWORK, state_data)
        await update.message.reply_text(
            "Select your withdrawal network:",
            reply_markup=kb.network_keyboard()
        )

    elif state == STATE_ADMIN_AWAIT_VERIFY_ID:
        await handle_admin_verify_id(update, ctx, text)

    elif state == STATE_ADMIN_AWAIT_AMOUNT:
        await handle_admin_verify_amount(update, ctx, text, state_data)

    elif state == STATE_ADMIN_AWAIT_PLAN:
        await handle_admin_verify_plan(update, ctx, text, state_data)

    elif state == STATE_ADMIN_AWAIT_REJECT_REASON:
        await handle_admin_reject_reason(update, ctx, text, state_data)

    else:
        # Default — show main menu
        await update.message.reply_text(
            "Use the menu below ⬇️",
            reply_markup=kb.main_menu_keyboard()
        )


async def handle_withdrawal_amount(update, ctx, text, state_data):
    user_id = update.effective_user.id
    try:
        amount = float(text.replace(",", "").replace("$", ""))
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number.")
        return

    available = state_data.get('available', 0)
    if amount < MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"⚠️ Minimum withdrawal is {format_currency(MIN_WITHDRAWAL)}."
        )
        return
    if amount > MAX_WITHDRAWAL:
        await update.message.reply_text(
            f"⚠️ Maximum withdrawal is {format_currency(MAX_WITHDRAWAL)}."
        )
        return
    if amount > available:
        await update.message.reply_text(
            f"⚠️ Amount exceeds available balance of {format_currency(available)}."
        )
        return

    state_data['amount'] = amount
    db.set_investor_state(user_id, STATE_AWAIT_WALLET_ADDRESS, state_data)
    await update.message.reply_text(
        "Enter your *USDT withdrawal wallet address*:",
        parse_mode="Markdown"
    )


# ── Admin flow: verify payment ────────────────────────────────

async def handle_admin_verify_id(update, ctx, text):
    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        return
    try:
        investor_id = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ Invalid Telegram ID. Enter a number.")
        return

    investor = db.get_investor(investor_id)
    if not investor:
        # Auto-create a placeholder
        db.upsert_investor(investor_id, None, "Unknown")

    db.set_investor_state(admin_id, STATE_ADMIN_AWAIT_AMOUNT, {"investor_id": investor_id})
    await update.message.reply_text(
        f"Investor ID: `{investor_id}`\n\nEnter investment *amount* (USD):",
        parse_mode="Markdown"
    )


async def handle_admin_verify_amount(update, ctx, text, state_data):
    admin_id = update.effective_user.id
    try:
        amount = float(text.replace(",", "").replace("$", ""))
    except ValueError:
        await update.message.reply_text("⚠️ Invalid amount.")
        return

    state_data['amount'] = amount
    db.set_investor_state(admin_id, STATE_ADMIN_AWAIT_PLAN, state_data)

    plan_lines = "\n".join(
        [f"• `{k}` — {v['label']}" for k, v in INVESTMENT_PLANS.items()]
    )
    await update.message.reply_text(
        f"Amount: {format_currency(amount)}\n\nEnter plan key:\n{plan_lines}",
        parse_mode="Markdown"
    )


async def handle_admin_verify_plan(update, ctx, text, state_data):
    admin_id = update.effective_user.id
    plan_key = text.strip().lower()
    if plan_key not in INVESTMENT_PLANS:
        await update.message.reply_text("⚠️ Invalid plan key. Try again.")
        return

    plan = INVESTMENT_PLANS[plan_key]
    investor_id = state_data['investor_id']
    amount = state_data['amount']
    duration_days = plan['duration_days']

    now = datetime.now(timezone.utc)
    maturity = now + timedelta(days=duration_days)

    inv_id = db.create_investment(
        telegram_id=investor_id,
        amount=amount,
        plan_key=plan_key,
        plan_label=plan['label'],
        duration_days=duration_days,
        start_ts=now.isoformat(),
        maturity_ts=maturity.isoformat(),
        recorded_balance=amount,  # Admin updates balance separately
    )

    db.write_audit(admin_id, "CREATE_INVESTMENT", target_id=inv_id,
                   details=f"amount={amount}, plan={plan_key}, investor={investor_id}")
    db.set_investor_state(admin_id, STATE_IDLE)

    # Notify investor
    inv = db.get_investment_by_id(inv_id)
    try:
        await ctx.bot.send_message(
            chat_id=investor_id,
            text=msg.investment_activated_msg(inv),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb.activation_keyboard()
        )
    except Exception as e:
        logger.warning(f"Could not notify investor {investor_id}: {e}")

    await update.message.reply_text(
        f"✅ Investment `{inv_id}` created and investor notified.",
        parse_mode="Markdown",
        reply_markup=kb.admin_main_keyboard()
    )


async def handle_admin_reject_reason(update, ctx, text, state_data):
    admin_id = update.effective_user.id
    request_id = state_data.get('request_id')
    if not request_id:
        return
    wd = db.get_withdrawal_by_id(request_id)
    if not wd:
        return
    db.update_withdrawal_status(request_id, "REJECTED", admin_id=admin_id, note=text)
    db.write_audit(admin_id, "REJECT_WITHDRAWAL", target_id=request_id, details=text)
    db.set_investor_state(admin_id, STATE_IDLE)

    try:
        await ctx.bot.send_message(
            chat_id=wd['telegram_id'],
            text=(f"❌ *PAWNS:* Your withdrawal request `{request_id}` has been rejected.\n\n"
                  f"Reason: {text}\n\nContact support if you have questions."),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.warning(f"Could not notify investor: {e}")

    await update.message.reply_text(
        f"✅ Withdrawal `{request_id}` rejected.",
        parse_mode="Markdown",
        reply_markup=kb.admin_main_keyboard()
    )


# ── Admin: all investments & audit ───────────────────────────

async def admin_all_investments(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    invs = db.get_all_active_investments()
    if not invs:
        await send_or_edit(update, "No active investments.", kb.admin_main_keyboard())
        return
    lines = ["📊 *ACTIVE INVESTMENTS*\n"]
    for inv in invs[:10]:  # Show max 10
        lines.append(
            f"• `{inv['investment_id']}`\n"
            f"  User: `{inv['telegram_id']}` | Amount: {format_currency(inv['amount'])}\n"
            f"  Plan: {inv['plan_label']} | Matures: {inv['maturity_ts'][:10]}\n"
        )
    await send_or_edit(update, "\n".join(lines), kb.admin_main_keyboard())


async def admin_audit_log(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from database import get_conn
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY logged_at DESC LIMIT 10"
        ).fetchall()
    if not rows:
        await send_or_edit(update, "No audit entries yet.", kb.admin_main_keyboard())
        return
    lines = ["📜 *RECENT AUDIT LOG*\n"]
    for r in rows:
        lines.append(f"• [{r['logged_at'][:16]}] Admin `{r['admin_id']}` — {r['action']} on `{r['target_id']}`")
    await send_or_edit(update, "\n".join(lines), kb.admin_main_keyboard())

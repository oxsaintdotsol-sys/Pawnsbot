"""
PAWNS Bot — Inline keyboard builders
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("♟️ MY INVESTMENT", callback_data="my_investment")],
        [InlineKeyboardButton("💰 WITHDRAW", callback_data="withdraw")],
        [InlineKeyboardButton("📜 TRANSACTION HISTORY", callback_data="tx_history")],
        [InlineKeyboardButton("📄 INVESTMENT AGREEMENT", callback_data="agreement")],
        [InlineKeyboardButton("🆘 SUPPORT", callback_data="support")],
    ])


def investment_dashboard_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ WITHDRAWAL", callback_data="withdraw")],
        [InlineKeyboardButton("📄 INVESTMENT AGREEMENT", callback_data="agreement")],
        [InlineKeyboardButton("📜 TRANSACTION HISTORY", callback_data="tx_history")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="main_menu")],
    ])


def withdrawal_locked_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 REFRESH COUNTDOWN", callback_data="withdraw")],
        [InlineKeyboardButton("📄 VIEW TERMS", callback_data="agreement")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="my_investment")],
    ])


def withdrawal_available_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 REQUEST WITHDRAWAL", callback_data="request_withdrawal")],
        [InlineKeyboardButton("📊 VIEW INVESTMENT", callback_data="my_investment")],
    ])


def network_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("TRC20", callback_data="net_TRC20")],
        [InlineKeyboardButton("BSC / BEP20", callback_data="net_BSC / BEP20")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")],
    ])


def confirm_withdrawal_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ CONFIRM WITHDRAWAL", callback_data="confirm_withdrawal")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")],
    ])


def withdrawal_submitted_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 VIEW INVESTMENT", callback_data="my_investment")],
        [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="main_menu")],
    ])


def admin_withdrawal_keyboard(request_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ APPROVE", callback_data=f"wd_approve_{request_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"wd_reject_{request_id}")],
        [InlineKeyboardButton("🔍 VIEW INVESTMENT", callback_data=f"wd_view_{request_id}")],
        [InlineKeyboardButton("💬 CONTACT INVESTOR", callback_data=f"wd_contact_{request_id}")],
    ])


def admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ VERIFY PAYMENT", callback_data="admin_verify")],
        [InlineKeyboardButton("📋 PENDING WITHDRAWALS", callback_data="admin_pending_wd")],
        [InlineKeyboardButton("📊 ALL INVESTMENTS", callback_data="admin_all_inv")],
        [InlineKeyboardButton("📜 AUDIT LOG", callback_data="admin_audit")],
    ])


def back_to_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="main_menu")],
    ])


def activation_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 MY INVESTMENT", callback_data="my_investment")],
    ])

"""
PAWNS Bot Configuration
- Set your values in the .env file, not here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot & Admin ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Comma-separated list of Telegram user IDs who are admins
# Example: "123456789,987654321"
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()]

# Super admin — only this ID can modify investment records
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))

# ── Database ─────────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "pawns.db")

# ── Investment Plans ─────────────────────────────────────────
INVESTMENT_PLANS = {
    "high_risk_3m": {
        "label": "High Risk — 3 Months",
        "duration_days": 90,
    },
    "medium_risk_6m": {
        "label": "Medium Risk — 6 Months",
        "duration_days": 180,
    },
    "low_risk_12m": {
        "label": "Low Risk — 12 Months",
        "duration_days": 365,
    },
}

# ── Withdrawal ────────────────────────────────────────────────
MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", "100"))
MAX_WITHDRAWAL = float(os.getenv("MAX_WITHDRAWAL", "100000"))
SUPPORTED_NETWORKS = ["TRC20", "BSC / BEP20"]

# ── Conversation states ───────────────────────────────────────
(
    STATE_IDLE,
    STATE_AWAIT_WITHDRAWAL_AMOUNT,
    STATE_AWAIT_WALLET_ADDRESS,
    STATE_AWAIT_NETWORK,
    STATE_CONFIRM_WITHDRAWAL,
    STATE_ADMIN_AWAIT_VERIFY_ID,
    STATE_ADMIN_AWAIT_AMOUNT,
    STATE_ADMIN_AWAIT_PLAN,
    STATE_ADMIN_AWAIT_REJECT_REASON,
) = range(9)

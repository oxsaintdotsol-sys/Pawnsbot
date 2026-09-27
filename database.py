"""
PAWNS Bot — Database Layer (SQLite)
"""
import sqlite3
import logging
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS investors (
            telegram_id     INTEGER PRIMARY KEY,
            username        TEXT,
            full_name       TEXT,
            joined_at       TEXT DEFAULT (datetime('now')),
            state           INTEGER DEFAULT 0,
            state_data      TEXT
        );

        CREATE TABLE IF NOT EXISTS investments (
            investment_id       TEXT PRIMARY KEY,
            telegram_id         INTEGER NOT NULL,
            amount              REAL NOT NULL,
            plan_key            TEXT NOT NULL,
            plan_label          TEXT NOT NULL,
            duration_days       INTEGER NOT NULL,
            start_ts            TEXT NOT NULL,
            maturity_ts         TEXT NOT NULL,
            contract_version    TEXT DEFAULT 'v1.0',
            recorded_balance    REAL NOT NULL,
            status              TEXT DEFAULT 'ACTIVE',
            withdrawal_eligible INTEGER DEFAULT 0,
            payment_txid        TEXT,
            payment_wallet      TEXT,
            payment_network     TEXT,
            created_at          TEXT DEFAULT (datetime('now')),
            updated_at          TEXT DEFAULT (datetime('now')),
            notified_7d         INTEGER DEFAULT 0,
            notified_24h        INTEGER DEFAULT 0,
            notified_maturity   INTEGER DEFAULT 0,
            FOREIGN KEY (telegram_id) REFERENCES investors(telegram_id)
        );

        CREATE TABLE IF NOT EXISTS withdrawals (
            request_id          TEXT PRIMARY KEY,
            investment_id       TEXT NOT NULL,
            telegram_id         INTEGER NOT NULL,
            amount              REAL NOT NULL,
            wallet_address      TEXT NOT NULL,
            network             TEXT NOT NULL,
            status              TEXT DEFAULT 'PENDING',
            created_at          TEXT DEFAULT (datetime('now')),
            updated_at          TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (investment_id) REFERENCES investments(investment_id)
        );

        CREATE TABLE IF NOT EXISTS withdrawal_status_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id      TEXT NOT NULL,
            old_status      TEXT,
            new_status      TEXT NOT NULL,
            admin_id        INTEGER,
            note            TEXT,
            logged_at       TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (request_id) REFERENCES withdrawals(request_id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id    INTEGER NOT NULL,
            action      TEXT NOT NULL,
            target_id   TEXT,
            details     TEXT,
            logged_at   TEXT DEFAULT (datetime('now'))
        );
        """)
    logger.info("Database tables ready.")


# ── Investor helpers ──────────────────────────────────────────

def upsert_investor(telegram_id, username, full_name):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO investors (telegram_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
        """, (telegram_id, username, full_name))


def get_investor(telegram_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM investors WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()


def set_investor_state(telegram_id, state, state_data=None):
    import json
    with get_conn() as conn:
        conn.execute(
            "UPDATE investors SET state=?, state_data=? WHERE telegram_id=?",
            (state, json.dumps(state_data) if state_data else None, telegram_id)
        )


def get_investor_state(telegram_id):
    import json
    with get_conn() as conn:
        row = conn.execute(
            "SELECT state, state_data FROM investors WHERE telegram_id=?",
            (telegram_id,)
        ).fetchone()
        if row:
            data = json.loads(row["state_data"]) if row["state_data"] else {}
            return row["state"], data
        return 0, {}


# ── Investment helpers ────────────────────────────────────────

def create_investment(telegram_id, amount, plan_key, plan_label,
                      duration_days, start_ts, maturity_ts,
                      recorded_balance, payment_txid=None,
                      payment_wallet=None, payment_network=None):
    import uuid
    from datetime import datetime
    date_str = datetime.utcnow().strftime("%Y%m%d")
    short = str(uuid.uuid4()).split("-")[0].upper()
    inv_id = f"PAWNS-INV-{date_str}-{short}"

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO investments
            (investment_id, telegram_id, amount, plan_key, plan_label,
             duration_days, start_ts, maturity_ts, recorded_balance,
             payment_txid, payment_wallet, payment_network)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (inv_id, telegram_id, amount, plan_key, plan_label,
              duration_days, start_ts, maturity_ts, recorded_balance,
              payment_txid, payment_wallet, payment_network))
    return inv_id


def get_active_investment(telegram_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT * FROM investments
            WHERE telegram_id=? AND status='ACTIVE'
            ORDER BY created_at DESC LIMIT 1
        """, (telegram_id,)).fetchone()


def get_investment_by_id(investment_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM investments WHERE investment_id=?", (investment_id,)
        ).fetchone()


def update_investment_status(investment_id, status, withdrawal_eligible=None):
    with get_conn() as conn:
        if withdrawal_eligible is not None:
            conn.execute("""
                UPDATE investments SET status=?, withdrawal_eligible=?,
                updated_at=datetime('now') WHERE investment_id=?
            """, (status, withdrawal_eligible, investment_id))
        else:
            conn.execute("""
                UPDATE investments SET status=?,
                updated_at=datetime('now') WHERE investment_id=?
            """, (status, investment_id))


def get_all_active_investments():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM investments WHERE status='ACTIVE'"
        ).fetchall()


def mark_notified(investment_id, field):
    with get_conn() as conn:
        conn.execute(
            f"UPDATE investments SET {field}=1 WHERE investment_id=?",
            (investment_id,)
        )


# ── Withdrawal helpers ────────────────────────────────────────

def create_withdrawal(investment_id, telegram_id, amount, wallet, network):
    import uuid
    req_id = f"PAWNS-WD-{str(uuid.uuid4()).split('-')[0].upper()}"
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO withdrawals
            (request_id, investment_id, telegram_id, amount, wallet_address, network)
            VALUES (?,?,?,?,?,?)
        """, (req_id, investment_id, telegram_id, amount, wallet, network))
        conn.execute("""
            INSERT INTO withdrawal_status_log
            (request_id, old_status, new_status, note)
            VALUES (?, NULL, 'PENDING', 'Withdrawal request submitted by investor')
        """, (req_id,))
    return req_id


def get_pending_withdrawal(telegram_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT * FROM withdrawals
            WHERE telegram_id=? AND status IN ('PENDING','UNDER REVIEW','APPROVED','PROCESSING')
            LIMIT 1
        """, (telegram_id,)).fetchone()


def get_withdrawal_by_id(request_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM withdrawals WHERE request_id=?", (request_id,)
        ).fetchone()


def update_withdrawal_status(request_id, new_status, admin_id=None, note=None):
    with get_conn() as conn:
        old = conn.execute(
            "SELECT status FROM withdrawals WHERE request_id=?", (request_id,)
        ).fetchone()
        old_status = old["status"] if old else None
        conn.execute("""
            UPDATE withdrawals SET status=?, updated_at=datetime('now')
            WHERE request_id=?
        """, (new_status, request_id))
        conn.execute("""
            INSERT INTO withdrawal_status_log
            (request_id, old_status, new_status, admin_id, note)
            VALUES (?,?,?,?,?)
        """, (request_id, old_status, new_status, admin_id, note))


def get_withdrawal_history(telegram_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT * FROM withdrawals WHERE telegram_id=?
            ORDER BY created_at DESC
        """, (telegram_id,)).fetchall()


def get_all_pending_withdrawals():
    with get_conn() as conn:
        return conn.execute("""
            SELECT w.*, i.telegram_id as inv_user_id
            FROM withdrawals w
            JOIN investments i ON w.investment_id = i.investment_id
            WHERE w.status IN ('PENDING','UNDER REVIEW')
            ORDER BY w.created_at ASC
        """).fetchall()


# ── Audit log ─────────────────────────────────────────────────

def write_audit(admin_id, action, target_id=None, details=None):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO audit_log (admin_id, action, target_id, details)
            VALUES (?,?,?,?)
        """, (admin_id, action, target_id, details))

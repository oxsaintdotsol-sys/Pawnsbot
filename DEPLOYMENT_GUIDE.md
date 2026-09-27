# PAWNS Bot — Deployment Guide
## From Zero to Live in ~20 Minutes

---

## WHAT YOU HAVE

```
pawns_bot/
├── bot.py              ← Main entry point
├── config.py           ← Settings & constants
├── database.py         ← All database logic (SQLite)
├── handlers.py         ← All user & admin flows
├── keyboards.py        ← All buttons/menus
├── messages.py         ← All message templates
├── scheduler.py        ← Background maturity checker
├── utils.py            ← Shared helpers
├── requirements.txt    ← Python packages needed
├── Procfile            ← Tells Railway how to run the bot
├── runtime.txt         ← Python version
├── .env.example        ← Template for your secrets
└── .gitignore          ← Prevents secrets from being uploaded
```

---

## STEP 1 — Create Your Telegram Bot (5 minutes)

1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. BotFather will ask for a name — enter: `PAWNS Investment`
4. Then it will ask for a username — enter something like: `pawns_invest_bot`
   (must end in `bot`, must be unique)
5. BotFather will give you a **token** that looks like:
   `1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ`
6. **Copy and save this token** — you'll need it in Step 3.

---

## STEP 2 — Find Your Telegram Admin ID (2 minutes)

1. Open Telegram and search for **@userinfobot**
2. Send any message to it
3. It will reply with your **User ID** (a number like `123456789`)
4. **Copy and save this number** — you're the admin.

If you have other admins, have them do the same and collect their IDs.

---

## STEP 3 — Upload to GitHub (5 minutes)

1. Go to **https://github.com** and create a free account if you don't have one
2. Click **"New repository"**
3. Name it: `pawns-bot`
4. Set it to **Private** (important — keeps your code safe)
5. Click **"Create repository"**
6. On your computer, go into the `pawns_bot` folder
7. Open a terminal/command prompt in that folder and run:

```bash
git init
git add .
git commit -m "Initial PAWNS bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pawns-bot.git
git push -u origin main
```

> ⚠️ Do NOT upload your `.env` file — the `.gitignore` already blocks it.

---

## STEP 4 — Deploy on Railway (5 minutes)

1. Go to **https://railway.app** and sign up (free) with your GitHub account
2. Click **"New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your `pawns-bot` repository
5. Railway will detect it automatically. Click **Deploy**.

**Now add your environment variables:**

6. In Railway, click your project → click **"Variables"** tab
7. Add these one by one (click "+ New Variable" for each):

| Variable Name     | Value                              |
|-------------------|------------------------------------|
| `BOT_TOKEN`       | Your token from BotFather          |
| `ADMIN_IDS`       | Your Telegram ID (e.g. `123456789`)|
| `SUPER_ADMIN_ID`  | Your Telegram ID (same or different)|
| `MIN_WITHDRAWAL`  | `100`                              |
| `MAX_WITHDRAWAL`  | `100000`                           |

8. After adding all variables, click **"Deploy"** again (or it may auto-redeploy)

---

## STEP 5 — Test Your Bot

1. Open Telegram
2. Search for your bot's username (e.g. `@pawns_invest_bot`)
3. Send `/start` — you should see the PAWNS welcome menu
4. Send `/admin` — you should see the admin panel

**Test the full flow:**
1. As admin, send `/admin`
2. Click **VERIFY PAYMENT**
3. Enter your own Telegram ID (to test)
4. Enter an amount (e.g. `1000`)
5. Enter a plan key: `high_risk_3m`
6. The bot will send you an investment activation message
7. Click **MY INVESTMENT** to see the dashboard

---

## HOW THE ADMIN FLOW WORKS

### To activate an investor's investment:
1. Admin sends `/admin`
2. Clicks **✅ VERIFY PAYMENT**
3. Enters the investor's Telegram ID
4. Enters the investment amount
5. Enters the plan key (`high_risk_3m`, `medium_risk_6m`, or `low_risk_12m`)
6. Bot automatically creates the investment and notifies the investor

### To process a withdrawal:
1. Admin receives a notification when investor submits withdrawal
2. Admin clicks **✅ APPROVE** or **❌ REJECT**
3. If rejecting, admin enters a reason
4. Investor is automatically notified of the decision

---

## INVESTMENT PLANS

| Plan Key         | Label                | Duration |
|------------------|----------------------|----------|
| `high_risk_3m`   | High Risk — 3 Months | 90 days  |
| `medium_risk_6m` | Medium Risk — 6 Months | 180 days |
| `low_risk_12m`   | Low Risk — 12 Months | 365 days |

To add/change plans, edit the `INVESTMENT_PLANS` section in `config.py`.

---

## IMPORTANT NOTES

- The database file (`pawns.db`) is stored on Railway's server.
  Railway's free tier may reset it if the service goes to sleep.
  **For production use, upgrade to Railway's $5/month plan** or use an
  external database like Supabase (free PostgreSQL).

- The countdown is **server-side** — users cannot manipulate it by
  changing their phone's clock.

- The withdrawal lock is enforced in the backend — it cannot be bypassed
  from the Telegram interface.

- All admin actions are logged in the `audit_log` table.

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check Railway logs → make sure BOT_TOKEN is set correctly |
| `/admin` says Unauthorized | Make sure your Telegram ID is in ADMIN_IDS variable |
| Investment not activating | Check that you entered a valid plan key exactly as shown |
| Can't find investor ID | Have them message @userinfobot on Telegram |

---

## SUPPORT

For any issues with the bot code, review the Railway deployment logs:
Railway Dashboard → Your Project → **Logs** tab.

# Vemail V42 UX Rebuild

Flask/Render SaaS temporary email app using mail.tm style API integration, Telegram verification, Free/Pro plan limits, unified inbox, notification center, and a separated admin console.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="change-me"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="strong-password"
python app.py
```

Open `http://127.0.0.1:5000`.

## Render

Set at least:

- SECRET_KEY
- PUBLIC_BASE_URL
- ADMIN_USERNAME
- ADMIN_PASSWORD
- ADMIN_BOT_TOKEN + ADMIN_CHAT_ID for admin alerts
- USER_BOT_TOKEN for user verification/alerts

SQLite is stored in `instance/vemail.sqlite3`. For production, use a persistent disk or external DB.

## V42 focus

- User pages are separated into Dashboard, Inbox, Mailboxes, Notifications, Account, Upgrade.
- Admin is separated into Overview, Users, Payments, Plans, Limits, Notifications, Telegram, Settings, Backup.
- Video downloader code and plan fields were intentionally removed.

## V42.1 environment compatibility
V42 reads config from Render environment variables first, then falls back to DB settings. Supported aliases include:

- `PUBLIC_BASE_URL` or `RENDER_EXTERNAL_URL`
- `ADMIN_BOT_TOKEN`, `ADMIN_TELEGRAM_BOT_TOKEN`, or `REPORT_BOT_TOKEN`
- `ADMIN_CHAT_ID`, `ADMIN_TELEGRAM_CHAT_ID`, or `REPORT_CHAT_ID`
- `USER_BOT_TOKEN`, `USER_TELEGRAM_BOT_TOKEN`, or `TELEGRAM_BOT_TOKEN`
- `USER_BOT_USERNAME`, `USER_TELEGRAM_BOT_USERNAME`, or `TELEGRAM_BOT_USERNAME`
- `USDT_TRC20_ADDRESS` or `CRYPTO_USDT_TRC20`
- `DATABASE_PATH`

DB settings fallback keys from V39/V40/V41 are also supported, including `admin_telegram_bot_token`, `telegram_bot_token`, `telegram_admin_chat_id`, `user_telegram_bot_token`, `user_telegram_bot_username`, and `crypto_usdt_trc20`.

## Import an old JSON backup
To import a V39/V40/V41 JSON backup into the V42 database:

```bash
python -S restore_v41_backup.py /path/to/vemail-backup.json
```

The importer ignores removed video fields/tables on purpose.


## V42.6 fixes
- Login now accepts the user's primary Vemail mailbox address instead of username for normal users.
- Inbox navigation shows a new-message badge based on unread message notifications.
- Mobile wrapping/overflow fixes for mailbox addresses, dates, extracted links, message details, and cards.

## V42.23 Business API

Business-plan users can create API keys from Account → Business API. API keys are shown once and stored hashed.

Authentication:

```bash
Authorization: Bearer vemail_live_xxx
```

Endpoints:

```bash
GET  /api/v1/docs
GET  /api/v1/usage
GET  /api/v1/mailboxes
POST /api/v1/mailboxes              # JSON: {"local":"optional-name"}
GET  /api/v1/messages?limit=10&offset=0&mailbox=<id_or_address>&unread=1
GET  /api/v1/messages/<id>?mark_read=1
POST /api/v1/messages/<id>/read
POST /api/v1/messages/read-all
```

The API never bypasses plan limits. Mailbox creation is blocked at `mailbox_limit`; new domains are restricted by `domain_limit`; message sync/storage stops at `message_history`, while quota notifications continue through the existing notification engine.

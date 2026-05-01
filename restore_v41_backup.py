"""
Restore/import a Vemail V39/V40/V41 JSON backup into the V42 UX Rebuild database.
Usage:
  python -S restore_v41_backup.py /path/to/vemail-backup.json

Notes:
- This importer maps old tables to the V42 schema.
- It intentionally ignores removed video_usage data and video plan fields.
- Environment variables still win at runtime; imported settings are fallback only.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "instance", "vemail.sqlite3"))


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def iso_from_ts(value):
    try:
        value = int(value or 0)
        if value <= 0:
            return None
        return datetime.fromtimestamp(value, tz=timezone.utc).replace(microsecond=0).isoformat()
    except Exception:
        return None


def main(path):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    tables = payload.get("tables", {})
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Reuse the app initializer so the target schema exists.
    import app as vemail_app
    vemail_app.init_db()

    old_user_to_new = {}
    for u in tables.get("users", []):
        username = u.get("display_name") or (u.get("email") or "user").split("@")[0]
        email = u.get("email") or username
        existing = cur.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if existing:
            uid = existing["id"]
        else:
            cur.execute(
                """INSERT INTO users(username,password_hash,plan,verified,telegram_chat_id,telegram_username,telegram_linked,telegram_mail_alerts,is_admin,disabled,last_activity,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    username,
                    u.get("password_hash") or "",
                    u.get("plan_code") or "free",
                    int(u.get("email_verified") or 0),
                    u.get("telegram_chat_id") or None,
                    u.get("telegram") or None,
                    1 if u.get("telegram_chat_id") else 0,
                    int(u.get("telegram_forward_enabled") or 0),
                    int(u.get("is_admin") or 0),
                    0 if int(u.get("is_active", 1) or 0) else 1,
                    iso_from_ts(u.get("last_login_at")),
                    iso_from_ts(u.get("created_at")) or now_iso(),
                ),
            )
            uid = cur.lastrowid
        old_user_to_new[u.get("id")] = uid

    mailbox_by_address = {}
    for m in tables.get("user_mailboxes", []):
        uid = old_user_to_new.get(m.get("user_id"))
        if not uid:
            continue
        address = m.get("address")
        if not address:
            continue
        cur.execute(
            """INSERT OR IGNORE INTO mailboxes(user_id,address,password,mailtm_id,token,is_primary,is_active,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                uid,
                address,
                m.get("password") or "",
                m.get("mailtm_id"),
                m.get("token"),
                1,
                int(m.get("is_active", 1) or 0),
                iso_from_ts(m.get("created_at")) or now_iso(),
            ),
        )
        row = cur.execute("SELECT id FROM mailboxes WHERE address=?", (address,)).fetchone()
        if row:
            mailbox_by_address[address] = row["id"]

    for msg in tables.get("saved_messages", []):
        uid = old_user_to_new.get(msg.get("user_id"))
        mid = mailbox_by_address.get(msg.get("mailbox_address"))
        if not uid or not mid:
            continue
        cur.execute(
            """INSERT OR IGNORE INTO messages(user_id,mailbox_id,mailtm_message_id,subject,sender,recipient,body,raw_json,received_at,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                uid,
                mid,
                msg.get("message_id"),
                msg.get("subject"),
                msg.get("sender"),
                msg.get("mailbox_address"),
                msg.get("body") or msg.get("intro") or "",
                json.dumps(msg, ensure_ascii=False),
                msg.get("created_at_remote"),
                iso_from_ts(msg.get("saved_at")) or now_iso(),
            ),
        )

    for p in tables.get("plans", []):
        key = p.get("code") or p.get("key")
        if not key:
            continue
        cur.execute(
            """INSERT INTO plans(key,label,price,mailbox_limit,domain_limit,message_history,can_save_messages,can_change_primary_email,telegram_mail_alerts_allowed)
               VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET
               label=excluded.label, price=excluded.price, mailbox_limit=excluded.mailbox_limit,
               domain_limit=excluded.domain_limit, message_history=excluded.message_history,
               can_save_messages=excluded.can_save_messages,
               can_change_primary_email=excluded.can_change_primary_email,
               telegram_mail_alerts_allowed=excluded.telegram_mail_alerts_allowed""",
            (
                key,
                p.get("name") or p.get("label") or key,
                float(p.get("price_usdt") or p.get("price") or 0),
                int(p.get("mailbox_limit") or 1),
                int(p.get("domain_limit") or 1),
                int(p.get("message_history") or 25),
                int(p.get("can_save_messages") or 0),
                int(p.get("can_change_primary_email") or 0),
                0 if key == "free" else 1,
            ),
        )

    for s in tables.get("settings", []):
        key = s.get("key")
        if key:
            cur.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, s.get("value") or ""))

    # Old video tables/fields are intentionally not restored.
    conn.commit()
    conn.close()
    print(f"Imported backup into {DB_PATH}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -S restore_v41_backup.py /path/to/vemail-backup.json")
        raise SystemExit(2)
    main(sys.argv[1])

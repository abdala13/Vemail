import os
import re
import json
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import quote_plus

import requests
from flask import (
    Flask, Response, abort, flash, g, jsonify, redirect, render_template,
    request, session, url_for, send_file, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash

APP_VERSION = "Vemail V42.23 Business API"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(INSTANCE_DIR, "vemail.sqlite3"))
MAILTM_BASE = os.environ.get("MAILTM_BASE", "https://api.mail.tm")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL") or ""
PUBLIC_BASE_URL = PUBLIC_BASE_URL.rstrip("/")

app = Flask(__name__, instance_path=INSTANCE_DIR)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)


I18N = {
 "ar": {
  "Secure temporary inbox":"صندوق بريد مؤقت آمن","Home":"الرئيسية","Inbox":"البريد","Upgrade":"الترقية","Account":"الحساب","Admin":"الإدارة","Sign out":"تسجيل الخروج","Sign in":"تسجيل الدخول","Notifications":"الإشعارات","Dashboard":"لوحة التحكم","Mailboxes":"الصناديق","Developed by":"تم تطوير الموقع بواسطة","for year":"لعام","Language":"اللغة",
  "User dashboard":"لوحة المستخدم","Welcome":"مرحبًا","A simple control center instead of one crowded page.":"مركز تحكم بسيط بدل صفحة واحدة مزدحمة.","Open Inbox":"فتح البريد","Current plan":"الخطة الحالية","Primary mailbox":"البريد الأساسي","Telegram":"تيليجرام","New unread":"غير مقروءة","Messages":"الرسائل","Next actions":"إجراءات سريعة","Manage mailboxes":"إدارة الصناديق","Upgrade account":"ترقية الحساب","Linked":"مربوط","Not linked":"غير مربوط","System alerts only":"تنبيهات النظام فقط","Verified":"مفعّل","used":"مستخدم","saved":"محفوظة",
  "Unified inbox":"البريد الموحد","All mailbox messages":"كل رسائل الصناديق","Messages are loaded only from mailboxes owned by your account.":"يتم تحميل الرسائل فقط من الصناديق المملوكة لحسابك.","Refresh":"تحديث","Mark inbox read":"تحديد رسائل البريد كمقروءة","All mailboxes":"كل الصناديق","Primary only":"الأساسي فقط","Sub only":"الفرعية فقط","Search":"بحث","Open":"فتح","Copy code":"نسخ الكود","Copy link":"نسخ الرابط","No messages yet. Refresh after using your mailbox.":"لا توجد رسائل بعد. حدّث بعد استخدام البريد.","Show more":"عرض المزيد","From":"من","To":"إلى","Mailbox":"الصندوق","Date":"التاريخ","Message":"رسالة","Back":"رجوع","Extracted codes":"الأكواد المستخرجة","No codes detected.":"لم يتم العثور على أكواد.","Extracted links":"الروابط المستخرجة","No links detected.":"لم يتم العثور على روابط.","Body":"المحتوى","Copy":"نسخ",
  "Notification center":"مركز الإشعارات","Opening the bell does not delete notifications. Mark them read when you choose.":"فتح الجرس لا يحذف الإشعارات. اجعلها مقروءة عندما تريد.","Mark all read":"تعيين الكل كمقروء","No notifications yet.":"لا توجد إشعارات بعد.",
  "Temporary email SaaS":"منصة بريد مؤقت","Clean temporary inboxes with Telegram activation.":"صناديق بريد مؤقتة منظمة مع تفعيل تيليجرام.","Create a mailbox first. Then save it with a username and password. No external Gmail required.":"أنشئ بريدًا أولًا، ثم احفظه باسم مستخدم وكلمة مرور. لا نطلب بريد Gmail خارجي.","Create temporary mailbox":"إنشاء بريد مؤقت","View plans":"عرض الخطط","Ready to save":"جاهز للحفظ","Your temporary mailbox":"بريدك المؤقت","Create account to save this mailbox":"إنشاء حساب لحفظ هذا البريد","How it works":"كيف يعمل؟","Create mailbox":"إنشاء بريد","Generate a temporary mail.tm mailbox directly from the home page.":"إنشاء بريد mail.tm مؤقت مباشرة من الصفحة الرئيسية.","Save account":"حفظ الحساب","Register using the generated mailbox, username, and password only.":"سجّل باستخدام البريد الذي تم إنشاؤه واسم المستخدم وكلمة المرور فقط.","Verify Telegram":"تفعيل تيليجرام","Open the verification link or enter the code, then use the unified inbox.":"افتح رابط التحقق أو أدخل الرمز، ثم استخدم البريد الموحد.","Plans":"الخطط",
  "Use your primary Vemail mailbox, not an external Gmail address.":"استخدم بريد Vemail الأساسي وليس Gmail خارجي.","Primary Vemail address":"بريد Vemail الأساسي","Password":"كلمة المرور","Forgot password?":"نسيت كلمة المرور؟","Register with generated mailbox":"التسجيل بالبريد المنشأ","Save your Vemail mailbox":"احفظ بريد Vemail الخاص بك","Username":"اسم المستخدم","Confirm password":"تأكيد كلمة المرور","Create account and verify Telegram":"إنشاء الحساب وتفعيل تيليجرام","Telegram activation":"تفعيل تيليجرام","Activate your account":"فعّل حسابك","Open Telegram":"فتح تيليجرام","Using a computer?":"تستخدم الكمبيوتر؟","Activation code":"رمز التفعيل","Verify code":"تحقق من الرمز",
  "Your inboxes":"صناديقك","Free accounts keep one mailbox. Paid plans can add more.":"الحساب المجاني يحتفظ بصندوق واحد. الخطط المدفوعة تضيف المزيد.","Make primary":"جعله أساسيًا","Create new mailbox":"إنشاء صندوق جديد","Create":"إنشاء","Mailbox limit reached":"وصلت إلى حد الصناديق","Plans and payment":"الخطط والدفع","Network":"الشبكة","TXID":"رقم العملية","Submit payment request":"إرسال طلب الدفع","Payment history":"سجل المدفوعات","Your payment history":"سجل مدفوعاتك","Track every upgrade request and admin decision.":"تابع كل طلب ترقية وقرار الإدارة.","No payment requests yet.":"لا توجد طلبات دفع حتى الآن.","Submitted":"تم الإرسال","Decided":"تم القرار","Pending":"معلّق","Accepted":"مقبول","Rejected":"مرفوض","Open payment history":"فتح سجل المدفوعات","Payment timeline":"سجل الدفع","Confirmed revenue":"الإيراد المؤكد","Review upgrade requests, TXIDs, and user payment status.":"راجع طلبات الترقية وأرقام TXID وحالة دفع المستخدم.",
  "Settings":"الإعدادات","Account data":"بيانات الحساب","Plan":"الخطة","Status":"الحالة","Send test message":"إرسال رسالة اختبار","Enable":"تفعيل","Disable":"تعطيل","email-to-Telegram alerts":"تنبيهات البريد إلى تيليجرام","Change password":"تغيير كلمة المرور","Current password":"كلمة المرور الحالية","New password":"كلمة المرور الجديدة","Save password":"حفظ كلمة المرور","Password recovery":"استرداد كلمة المرور","Open recovery page":"فتح صفحة الاسترداد","Recover your account":"استرداد حسابك","Send Telegram reset code":"إرسال رمز الاسترداد إلى تيليجرام","Back to login":"العودة لتسجيل الدخول","Telegram verification":"تحقق تيليجرام","Set a new password":"تعيين كلمة مرور جديدة","Update password":"تحديث كلمة المرور",
  "Admin Console":"لوحة الإدارة","Overview":"نظرة عامة","Users":"المستخدمون","Payments":"المدفوعات","Limits":"الحدود","Mail.tm":"Mail.tm","Backup":"النسخ الاحتياطي","Admin overview":"نظرة عامة للإدارة","Business health":"صحة النظام","Last 14 days":"آخر 14 يوم","User management":"إدارة المستخدمين","User":"المستخدم","Boxes":"الصناديق","Last activity":"آخر نشاط","Details":"التفاصيل","Payment requests":"طلبات الدفع","Amount":"المبلغ","Actions":"الإجراءات","Accept":"قبول","Reject":"رفض","Delete":"حذف","Edit SaaS plans":"تعديل خطط SaaS","Price":"السعر","Mailbox limit":"حد الصناديق","Domain limit":"حد النطاقات","Message history":"سجل الرسائل","Save plan":"حفظ الخطة","Limit intelligence":"مراقبة الحدود","View user":"عرض المستخدم","Admin notifications":"إشعارات الإدارة","System events":"أحداث النظام","No admin notifications.":"لا توجد إشعارات إدارية.","Download JSON backup":"تحميل نسخة JSON","Mailbox creation diagnostics":"تشخيص إنشاء الصناديق","Base URL":"الرابط الأساسي","Response type":"نوع الاستجابة","Domains count":"عدد النطاقات","Sample domains":"عينة النطاقات","Failed":"فشل","Error":"خطأ","Note":"ملاحظة",
  "Browser notifications":"إشعارات المتصفح","Enable browser notifications to receive native alerts while the site is open or running in the background.":"فعّل إشعارات المتصفح لتظهر تنبيهات أصلية عندما يكون الموقع مفتوحًا أو يعمل في الخلفية.","For alerts while the site is fully closed, keep Telegram linked or add a server-side push worker later.":"للتنبيهات عندما يكون الموقع مغلقًا بالكامل، أبقِ تيليجرام مربوطًا أو أضف عامل دفع خادمي لاحقًا.","Copied":"تم النسخ","Mailbox created":"تم إنشاء البريد","Create failed":"فشل الإنشاء","Creating...":"جارٍ الإنشاء...","Inbox updated. New messages:":"تم تحديث البريد. رسائل جديدة:","New email received":"وصلت رسالة جديدة","No messages yet. Waiting for new mail...":"لا توجد رسائل بعد. بانتظار بريد جديد...","Refresh failed":"فشل التحديث","Not verified":"غير مفعّل","Mail alerts on":"تنبيهات البريد مفعلة","Primary":"أساسي","Sub":"فرعي","Unread":"غير مقروء","unknown":"غير معروف","Yes":"نعم","No":"لا", "Payment requests are only available after login. Admin approval sends site and Telegram notifications.":"طلبات الدفع متاحة بعد تسجيل الدخول فقط. موافقة الأدمن ترسل إشعارًا داخل الموقع وعلى تيليجرام.", "mailboxes":"صناديق", "saved messages":"رسائل محفوظة", "domain limit":"حد النطاقات", "Telegram mail alerts":"تنبيهات البريد على تيليجرام", "Allowed":"مسموح", "Paste transaction ID":"الصق رقم العملية", "Payment address":"عنوان الدفع", "Send USDT to this address, then paste your TXID below.":"أرسل USDT إلى هذا العنوان، ثم الصق رقم العملية TXID بالأسفل.", "Copy address":"نسخ العنوان", "Wallet address is not configured yet. Contact support.":"عنوان المحفظة غير مضبوط بعد. تواصل مع الدعم.", "Amount":"المبلغ", "Network":"الشبكة", "TXID":"رقم العملية", "Submit payment request":"إرسال طلب الدفع"
 }
}
def get_lang():
    lang = session.get("lang")
    if lang not in ("ar", "en"):
        lang = "ar"
        session["lang"] = lang
    return lang
def tr(text):
    return text if get_lang()=="en" else I18N.get("ar",{}).get(text,text)
PLAN_DEFAULTS = {
    "free": {
        "label": "Free",
        "price": 0,
        "mailbox_limit": 1,
        "domain_limit": 1,
        "message_history": 25,
        "can_save_messages": 1,
        "can_change_primary_email": 0,
        "telegram_mail_alerts_allowed": 0,
    },
    "pro": {
        "label": "Pro",
        "price": 5,
        "mailbox_limit": 5,
        "domain_limit": 3,
        "message_history": 1000,
        "can_save_messages": 1,
        "can_change_primary_email": 1,
        "telegram_mail_alerts_allowed": 1,
    },
    "business": {
        "label": "Business",
        "price": 15,
        "mailbox_limit": 25,
        "domain_limit": 10,
        "message_history": 5000,
        "can_save_messages": 1,
        "can_change_primary_email": 1,
        "telegram_mail_alerts_allowed": 1,
    },
}


# -------------------- Configuration bridge --------------------
def _direct_setting(key, default=""):
    """Read a setting directly without depending on Flask g/request lifecycle."""
    try:
        if not os.path.exists(DB_PATH):
            return default
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return row[0] if row and row[0] not in (None, "") else default
    except Exception:
        return default


def cfg(names, setting_keys=None, default=""):
    """Environment-first config reader with backward-compatible DB setting fallback."""
    if isinstance(names, str):
        names = [names]
    for name in names:
        val = os.environ.get(name)
        if val not in (None, ""):
            return val
    setting_keys = setting_keys or []
    if isinstance(setting_keys, str):
        setting_keys = [setting_keys]
    for key in setting_keys:
        val = _direct_setting(key)
        if val not in (None, ""):
            return val
    return default


def public_base_url():
    return cfg(["PUBLIC_BASE_URL", "RENDER_EXTERNAL_URL"], "public_base_url", PUBLIC_BASE_URL).rstrip("/")

# -------------------- Database --------------------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn:
        conn.close()

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free',
            verified INTEGER NOT NULL DEFAULT 0,
            telegram_chat_id TEXT,
            telegram_username TEXT,
            telegram_linked INTEGER NOT NULL DEFAULT 0,
            telegram_mail_alerts INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            disabled INTEGER NOT NULL DEFAULT 0,
            last_activity TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS mailboxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            address TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            mailtm_id TEXT,
            token TEXT,
            is_primary INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mailbox_id INTEGER NOT NULL,
            mailtm_message_id TEXT,
            subject TEXT,
            sender TEXT,
            recipient TEXT,
            body TEXT,
            raw_json TEXT,
            received_at TEXT,
            read_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(mailbox_id, mailtm_message_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(mailbox_id) REFERENCES mailboxes(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            admin_only INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL DEFAULT 'account',
            title TEXT NOT NULL,
            body TEXT,
            action_url TEXT,
            read_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS verification_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            code TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code_hash TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            amount REAL NOT NULL,
            network TEXT NOT NULL DEFAULT 'TRC20',
            txid TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            decided_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS plans (
            key TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            mailbox_limit INTEGER NOT NULL DEFAULT 1,
            domain_limit INTEGER NOT NULL DEFAULT 1,
            message_history INTEGER NOT NULL DEFAULT 25,
            can_save_messages INTEGER NOT NULL DEFAULT 1,
            can_change_primary_email INTEGER NOT NULL DEFAULT 0,
            telegram_mail_alerts_allowed INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS telegram_duplicate_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            attempted_user_id INTEGER,
            token TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(chat_id, attempted_user_id, token)
        );
        CREATE TABLE IF NOT EXISTS web_notification_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, event_key)
        );
        CREATE TABLE IF NOT EXISTS limit_alert_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alert_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, alert_key)
        );
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_hash TEXT NOT NULL UNIQUE,
            key_prefix TEXT NOT NULL,
            label TEXT NOT NULL DEFAULT 'Business API',
            last_used_at TEXT,
            revoked_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS api_request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            api_key_id INTEGER,
            path TEXT,
            status_code INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY(api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
        );
        """
    )
    # Lightweight migrations for databases created by older V42/V41 builds.
    existing_message_cols = {row[1] for row in cur.execute("PRAGMA table_info(messages)").fetchall()}
    if "read_at" not in existing_message_cols:
        cur.execute("ALTER TABLE messages ADD COLUMN read_at TEXT")

    existing_payment_cols = {row[1] for row in cur.execute("PRAGMA table_info(payments)").fetchall()}
    if "decided_at" not in existing_payment_cols:
        cur.execute("ALTER TABLE payments ADD COLUMN decided_at TEXT")
    for key, p in PLAN_DEFAULTS.items():
        cur.execute(
            """INSERT OR IGNORE INTO plans
               (key,label,price,mailbox_limit,domain_limit,message_history,can_save_messages,can_change_primary_email,telegram_mail_alerts_allowed)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (key, p["label"], p["price"], p["mailbox_limit"], p["domain_limit"], p["message_history"],
             p["can_save_messages"], p["can_change_primary_email"], p["telegram_mail_alerts_allowed"]),
        )
    admin_username = cfg(["ADMIN_USERNAME", "ADMIN_EMAIL", "ADMIN_USER"], "admin_email", "admin")
    admin_password = cfg(["ADMIN_PASSWORD", "ADMIN_PASS"], default="admin12345")
    cur.execute("SELECT id FROM users WHERE username=?", (admin_username,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users(username,password_hash,plan,verified,is_admin,created_at) VALUES(?,?,?,?,?,?)",
            (admin_username, generate_password_hash(admin_password), "business", 1, 1, now_iso()),
        )
    for k, v in {
        "site_name": "Vemail",
        "usdt_trc20_address": cfg(["USDT_TRC20_ADDRESS", "CRYPTO_USDT_TRC20"], "crypto_usdt_trc20", "SET_USDT_ADDRESS"),
        "crypto_usdt_trc20": cfg(["USDT_TRC20_ADDRESS", "CRYPTO_USDT_TRC20"], "crypto_usdt_trc20", ""),
        "verification_mode": "Telegram Link",
        "public_base_url": public_base_url(),
        "mailtm_base": cfg(["MAILTM_BASE", "MAIL_TM_BASE"], "mailtm_base", "https://api.mail.tm"),
        "admin_telegram_bot_token": cfg(["ADMIN_BOT_TOKEN", "ADMIN_TELEGRAM_BOT_TOKEN", "REPORT_BOT_TOKEN"], "admin_telegram_bot_token", ""),
        "admin_telegram_chat_id": cfg(["ADMIN_CHAT_ID", "ADMIN_TELEGRAM_CHAT_ID", "REPORT_CHAT_ID"], ["admin_telegram_chat_id", "telegram_admin_chat_id"], ""),
        "user_telegram_bot_token": cfg(["USER_BOT_TOKEN", "USER_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"], "user_telegram_bot_token", ""),
        "user_telegram_bot_username": cfg(["USER_BOT_USERNAME", "USER_TELEGRAM_BOT_USERNAME", "TELEGRAM_BOT_USERNAME"], "user_telegram_bot_username", ""),
        "recaptcha_site_key": cfg(["RECAPTCHA_SITE_KEY", "GOOGLE_RECAPTCHA_SITE_KEY", "RECAPTCHA_PUBLIC_KEY", "GOOGLE_CAPTCHA_SITE_KEY"], ["recaptcha_site_key", "google_recaptcha_site_key"], ""),
        "recaptcha_secret_key": cfg(["RECAPTCHA_SECRET_KEY", "GOOGLE_RECAPTCHA_SECRET_KEY", "RECAPTCHA_PRIVATE_KEY", "GOOGLE_CAPTCHA_SECRET_KEY"], ["recaptcha_secret_key", "google_recaptcha_secret_key"], ""),
    }.items():
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    conn.commit()
    conn.close()

@app.before_request
def ensure_db_and_csrf():
    init_db()
    g.user = current_user()
    if request.method == "POST" and not request.path.startswith("/api/v1/") and request.endpoint not in {"api_temp_mailbox", "api_refresh_inbox", "telegram_verify_webhook"}:
        token = session.get("csrf_token")
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        if not token or not supplied or not hmac.compare_digest(token, supplied):
            abort(400, "CSRF token missing or invalid")

def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token

app.jinja_env.globals["csrf_token"] = csrf_token
app.jinja_env.globals["app_version"] = APP_VERSION
app.jinja_env.globals["_"] = tr

@app.get("/language/<lang>")
def set_language(lang):
    session["lang"] = "en" if lang == "en" else "ar"
    return redirect(request.referrer or url_for("home"))

@app.get("/sw.js")
def service_worker():
    response = send_from_directory(os.path.join(BASE_DIR, "static", "js"), "sw.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


# -------------------- Helpers --------------------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    row = db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not row or row["disabled"]:
        session.clear()
        return None
    return row

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not g.user:
            flash("Please sign in first.", "warning")
            return redirect(url_for("login"))
        db().execute("UPDATE users SET last_activity=? WHERE id=?", (now_iso(), g.user["id"]))
        db().commit()
        return fn(*args, **kwargs)
    return wrapper

def verified_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not g.user:
            return redirect(url_for("login"))
        if not g.user["verified"]:
            return redirect(url_for("verify"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not g.user or not g.user["is_admin"]:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

def get_plan(plan_key=None):
    key = plan_key or (g.user["plan"] if g.user else "free")
    return db().execute("SELECT * FROM plans WHERE key=?", (key,)).fetchone()

def create_notification(user_id, title, body="", category="account", admin_only=0, action_url=None, telegram=False):
    db().execute(
        "INSERT INTO notifications(user_id,admin_only,category,title,body,action_url,created_at) VALUES(?,?,?,?,?,?,?)",
        (user_id, int(admin_only), category, title, body, action_url, now_iso()),
    )
    db().commit()
    if admin_only:
        send_admin_telegram(f"🔔 {title}\n{body}")
    elif telegram and user_id:
        user = db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        send_user_telegram(user, f"🔔 {title}\n{body}")

def unread_count(user_id=None, admin_only=0):
    if admin_only:
        return db().execute("SELECT COUNT(*) c FROM notifications WHERE admin_only=1 AND read_at IS NULL").fetchone()["c"]
    if not user_id:
        return 0
    return db().execute("SELECT COUNT(*) c FROM notifications WHERE user_id=? AND admin_only=0 AND read_at IS NULL", (user_id,)).fetchone()["c"]

def unread_message_count(user_id=None):
    """Count real unread emails, not notification rows.

    This keeps the Inbox badge accurate: one unread email = one badge count,
    and opening the message marks it as read.
    """
    if not user_id:
        return 0
    try:
        return db().execute(
            "SELECT COUNT(*) c FROM messages WHERE user_id=? AND read_at IS NULL",
            (user_id,),
        ).fetchone()["c"]
    except sqlite3.OperationalError:
        return 0


def limit_alert_once(user_id, alert_key):
    """Return True once per user/plan/quota state so limit warnings do not spam."""
    if not user_id or not alert_key:
        return False
    try:
        db().execute(
            "INSERT INTO limit_alert_events(user_id,alert_key,created_at) VALUES(?,?,?)",
            (user_id, str(alert_key), now_iso()),
        )
        db().commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError:
        return True

def quota_warning_threshold(limit_value):
    """Small warning window before the package is consumed.
    Free 25 messages -> warn at last 3. Larger plans -> warn at last 10.
    """
    try:
        limit_value = int(limit_value or 0)
    except Exception:
        limit_value = 0
    if limit_value <= 0:
        return 0
    return max(1, min(10, (limit_value + 9) // 10))

def user_message_count(user_id):
    return db().execute("SELECT COUNT(*) c FROM messages WHERE user_id=?", (user_id,)).fetchone()["c"]

def user_mailbox_count(user_id):
    return db().execute("SELECT COUNT(*) c FROM mailboxes WHERE user_id=?", (user_id,)).fetchone()["c"]

def user_domain_count(user_id):
    return db().execute("""SELECT COUNT(DISTINCT lower(substr(address, instr(address,'@')+1))) c
                         FROM mailboxes WHERE user_id=? AND instr(address,'@')>0""", (user_id,)).fetchone()["c"]

def user_domains(user_id):
    rows = db().execute("""SELECT DISTINCT lower(substr(address, instr(address,'@')+1)) domain
                           FROM mailboxes WHERE user_id=? AND instr(address,'@')>0""", (user_id,)).fetchall()
    return [r["domain"] for r in rows if r["domain"]]

def notify_quota_state(user, plan, quota_type, used, limit_value, force_reached=False):
    """Create site + Telegram alerts before and at package limits.
    This is intentionally independent from normal email-message notifications.
    """
    if not user or not plan:
        return
    try:
        used = int(used or 0); limit_value = int(limit_value or 0)
    except Exception:
        return
    if limit_value <= 0:
        return
    remaining = max(0, limit_value - used)
    plan_key = plan["key"] if "key" in plan.keys() else str(user["plan"])
    send_tg = bool(user["telegram_linked"])
    if used >= limit_value or force_reached:
        key = f"{quota_type}:reached:{plan_key}:{limit_value}"
        if limit_alert_once(user["id"], key):
            if quota_type == "messages":
                title = "Message limit reached"
                body = f"Your {plan['label']} package has used {used}/{limit_value} saved messages. New incoming emails are now blocked from display until you upgrade."
            elif quota_type == "mailboxes":
                title = "Mailbox limit reached"
                body = f"Your {plan['label']} package has used {used}/{limit_value} mailboxes. Upgrade to create more mailboxes."
            else:
                title = "Domain limit reached"
                body = f"Your {plan['label']} package has used {used}/{limit_value} mailbox domains. New mailboxes must stay within your allowed domains or you need to upgrade."
            create_notification(user["id"], title, body, "limits", telegram=send_tg, action_url=url_for("upgrade"))
            create_notification(None, title, f"User {user['username']} reached {quota_type} quota: {used}/{limit_value}", "limits", admin_only=1)
        return
    threshold = quota_warning_threshold(limit_value)
    if remaining <= threshold:
        key = f"{quota_type}:near:{plan_key}:{limit_value}"
        if limit_alert_once(user["id"], key):
            if quota_type == "messages":
                title = "Message limit almost reached"
                body = f"You have {remaining} saved message slots left in your {plan['label']} package ({used}/{limit_value}). Upgrade before new messages are blocked."
            elif quota_type == "mailboxes":
                title = "Mailbox limit almost reached"
                body = f"You have {remaining} mailbox slot left in your {plan['label']} package ({used}/{limit_value})."
            else:
                title = "Domain limit almost reached"
                body = f"You have {remaining} domain slot left in your {plan['label']} package ({used}/{limit_value})."
            create_notification(user["id"], title, body, "limits", telegram=send_tg, action_url=url_for("upgrade"))

def enforce_all_quota_warnings(user_id):
    user = db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        return
    plan = db().execute("SELECT * FROM plans WHERE key=?", (user["plan"],)).fetchone()
    if not plan:
        return
    notify_quota_state(user, plan, "messages", user_message_count(user_id), plan["message_history"])
    notify_quota_state(user, plan, "mailboxes", user_mailbox_count(user_id), plan["mailbox_limit"])
    notify_quota_state(user, plan, "domains", user_domain_count(user_id), plan["domain_limit"])

def mark_browser_event_once(user_id, event_key):
    """Return True only once per user/event so browser notifications are not repeated forever."""
    if not user_id or not event_key:
        return False
    try:
        db().execute(
            "INSERT INTO web_notification_events(user_id,event_key,created_at) VALUES(?,?,?)",
            (user_id, str(event_key), now_iso()),
        )
        db().commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError:
        return True


def should_send_duplicate_telegram_warning(chat_id, attempted_user_id, token):
    """Avoid repeated Telegram warnings when Telegram retries webhook delivery."""
    try:
        db().execute(
            "INSERT INTO telegram_duplicate_warnings(chat_id, attempted_user_id, token, created_at) VALUES(?,?,?,?)",
            (str(chat_id), attempted_user_id, token, now_iso()),
        )
        db().commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError:
        return True

def db_first_cfg(setting_keys, env_names, default=""):
    """For admin-editable settings, DB value wins so the admin panel can fix Render config mistakes."""
    if isinstance(setting_keys, str):
        setting_keys = [setting_keys]
    for key in setting_keys:
        val = _direct_setting(key)
        if val not in (None, ""):
            return val
    return cfg(env_names, [], default)

def admin_bot_token():
    return db_first_cfg(["admin_telegram_bot_token"], ["ADMIN_BOT_TOKEN", "ADMIN_TELEGRAM_BOT_TOKEN", "REPORT_BOT_TOKEN", "TELEGRAM_ADMIN_BOT_TOKEN"])

def admin_chat_id():
    return db_first_cfg(["admin_telegram_chat_id", "telegram_admin_chat_id"], ["ADMIN_CHAT_ID", "ADMIN_TELEGRAM_CHAT_ID", "REPORT_CHAT_ID", "TELEGRAM_ADMIN_CHAT_ID"])

def user_bot_token():
    return db_first_cfg(["user_telegram_bot_token", "telegram_bot_token"], ["USER_BOT_TOKEN", "USER_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"])

def user_bot_username():
    return db_first_cfg(["user_telegram_bot_username", "telegram_bot_username"], ["USER_BOT_USERNAME", "USER_TELEGRAM_BOT_USERNAME", "TELEGRAM_BOT_USERNAME"], "YourVemailUserBot")

def send_admin_telegram(text):
    token = admin_bot_token()
    chat_id = admin_chat_id()
    if not token or not chat_id:
        print("ADMIN_TELEGRAM_MISSING_CONFIG", {"has_token": bool(token), "has_chat_id": bool(chat_id)})
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
        if not r.ok:
            print("ADMIN_TELEGRAM_SEND_ERROR", r.status_code, r.text[:500])
        return r.ok
    except Exception as exc:
        print("ADMIN_TELEGRAM_SEND_EXCEPTION", exc)
        return False

def send_user_telegram(user, text):
    token = user_bot_token()
    if isinstance(user, dict):
        chat_id = user.get("telegram_chat_id")
    elif user:
        chat_id = user["telegram_chat_id"]
    else:
        chat_id = None
    if not token or not chat_id:
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
        if not r.ok:
            print("USER_TELEGRAM_SEND_ERROR", r.status_code, r.text[:500])
        return r.ok
    except Exception as exc:
        print("USER_TELEGRAM_SEND_EXCEPTION", exc)
        return False

def telegram_api(token, method, payload=None):
    if not token:
        return {"ok": False, "description": "Missing token"}
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=payload or {}, timeout=12)
        try:
            data = r.json()
        except Exception:
            data = {"ok": r.ok, "description": r.text[:500]}
        if not r.ok and data.get("ok") is not False:
            data["ok"] = False
        return data
    except Exception as exc:
        return {"ok": False, "description": str(exc)}


# -------------------- Mail.tm bridge --------------------
def _json_error_detail(data):
    """Return a readable API error even when the server returns a list/string instead of a dict."""
    if isinstance(data, dict):
        return (data.get("hydra:description") or data.get("message") or
                data.get("detail") or data.get("title") or str(data)[:700])
    if isinstance(data, list):
        return "; ".join(str(x)[:180] for x in data[:4]) or "empty list response"
    return str(data)[:700]

def _collection_items(data, *keys):
    """mail.tm/proxies may return either Hydra dicts or raw lists. Normalize both."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            val = data.get(key)
            if isinstance(val, list):
                return val
        for key in ("data", "results", "records"):
            val = data.get(key)
            if isinstance(val, list):
                return val
    return []

def mailtm_request(method, path, token=None, json_payload=None, timeout=18):
    """Small, strict mail.tm client. Raises a useful RuntimeError on failure."""
    base = cfg(["MAILTM_BASE", "MAIL_TM_BASE"], "mailtm_base", MAILTM_BASE).rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = base + path
    headers = {"Accept": "application/json", "User-Agent": "Vemail/42.5 (+https://mail.tm attribution)"}
    if json_payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.request(method.upper(), url, headers=headers, json=json_payload, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"mail.tm network error: {exc}") from exc
    try:
        data = r.json() if r.text else {}
    except Exception:
        data = {"raw": r.text[:700]}
    if not r.ok:
        raise RuntimeError(f"mail.tm {method.upper()} {path} failed [{r.status_code}]: {_json_error_detail(data)}")
    return data

def _mailtm_domains():
    """Return active public domains from mail.tm. Supports Hydra dict and raw list response shapes."""
    data = mailtm_request("GET", "/domains")
    domains = _collection_items(data, "hydra:member", "member", "items")
    clean = []
    for d in domains:
        if isinstance(d, str):
            domain = d.strip().lower()
            active = True
            private = False
        elif isinstance(d, dict):
            domain = (d.get("domain") or d.get("name") or "").strip().lower()
            active = d.get("isActive") is not False
            private = d.get("isPrivate") is True
        else:
            continue
        if domain and active and not private:
            clean.append(domain)
    if not clean:
        raise RuntimeError(f"mail.tm returned no active public domains. Raw response: {str(data)[:500]}")
    return clean

def _safe_local_part(local=None):
    local = (local or "").strip().lower()
    local = re.sub(r"[^a-z0-9._-]", "", local)
    local = local.strip("._-")
    if len(local) < 4:
        local = "vm" + secrets.token_hex(5)
    if len(local) > 28:
        local = local[:28].strip("._-")
    # mail.tm is picky; keep final generated local simple.
    local = re.sub(r"[._-]{2,}", "-", local)
    return local or ("vm" + secrets.token_hex(5))


def create_mailtm_account(local=None, allowed_domains=None):
    """Create a real mailbox in mail.tm and return address/password/token/id.

    The previous V42.3 ZIP called this function but did not actually define it,
    which caused creation to fail on Home and Mailboxes. This version restores
    the real account -> token flow documented by mail.tm.
    """
    domains = _mailtm_domains()
    if allowed_domains:
        allowed_set = {str(d).lower().strip() for d in allowed_domains if str(d).strip()}
        filtered = [d for d in domains if d.lower() in allowed_set]
        if filtered:
            domains = filtered
        else:
            raise RuntimeError("No available mail.tm domain matches your plan domain limit")
    base_local = _safe_local_part(local)
    last_error = None
    # Try several local/domain combinations to survive duplicate addresses/rate noise.
    attempts = []
    for i in range(12):
        suffix = "" if i == 0 and local else secrets.token_hex(3)
        lp = base_local if not suffix else f"{base_local}-{suffix}"
        domain = domains[i % len(domains)]
        attempts.append(f"{lp}@{domain}")
    for address in attempts:
        password = "Vm!" + secrets.token_urlsafe(18)
        try:
            account = mailtm_request("POST", "/accounts", json_payload={"address": address, "password": password})
            tok = mailtm_request("POST", "/token", json_payload={"address": address, "password": password})
            token = tok.get("token")
            if not token:
                raise RuntimeError("mail.tm token response did not contain token")
            return {
                "address": account.get("address") or address,
                "password": password,
                "token": token,
                "mailtm_id": account.get("id") or tok.get("id") or "",
            }
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()
            # Conflict/duplicate is expected; try another address. For rate limit/network, also try briefly.
            if any(x in msg for x in ["already", "exist", "409", "rate", "429", "network"]):
                continue
            continue
    raise RuntimeError(f"Could not create mail.tm mailbox after retries: {last_error}")

def extract_codes_links(text):
    text = text or ""
    codes = sorted(set(re.findall(r"(?<!\w)(\d{4,8}|[A-Z0-9]{6,10})(?!\w)", text)))[:8]
    links = sorted(set(re.findall(r"https?://[^\s<>'\"]+", text)))[:10]
    return codes, links

def sync_mailbox(mailbox):
    if not mailbox["token"]:
        return 0
    user = db().execute("SELECT * FROM users WHERE id=?", (mailbox["user_id"],)).fetchone()
    if not user:
        return 0
    plan = db().execute("SELECT * FROM plans WHERE key=?", (user["plan"],)).fetchone()
    if not plan:
        plan = db().execute("SELECT * FROM plans WHERE key='free'").fetchone()

    try:
        data = mailtm_request("GET", "/messages", token=mailbox["token"])
        items = _collection_items(data, "hydra:member", "items", "member")
    except Exception as exc:
        create_notification(mailbox["user_id"], "Inbox sync issue", str(exc), "messages")
        return 0

    inserted = 0
    for item in items:
        mid = item.get("id")
        if not mid:
            continue
        exists = db().execute(
            "SELECT id FROM messages WHERE mailbox_id=? AND mailtm_message_id=?",
            (mailbox["id"], mid),
        ).fetchone()
        if exists:
            continue

        current_count = user_message_count(mailbox["user_id"])
        limit_value = int(plan["message_history"] or 0)
        if limit_value <= 0 or current_count >= limit_value:
            # Strict package rule: do not save or display messages beyond the plan limit.
            notify_quota_state(user, plan, "messages", current_count, limit_value, force_reached=True)
            continue

        full = item
        try:
            full = mailtm_request("GET", f"/messages/{mid}", token=mailbox["token"])
        except Exception:
            pass
        body = full.get("text") or full.get("html") or item.get("intro") or ""
        sender_obj = full.get("from") or item.get("from")
        sender = sender_obj.get("address") if isinstance(sender_obj, dict) else str(sender_obj or "")
        recipient = mailbox["address"]
        db().execute(
            """INSERT OR IGNORE INTO messages(user_id,mailbox_id,mailtm_message_id,subject,sender,recipient,body,raw_json,received_at,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (mailbox["user_id"], mailbox["id"], mid, full.get("subject") or item.get("subject"), sender, recipient, body, json.dumps(full), full.get("createdAt") or item.get("createdAt"), now_iso()),
        )
        inserted += 1
        create_notification(user["id"], "New email received", f"{mailbox['address']} received: {full.get('subject') or '(no subject)'}", "messages")
        if user["telegram_mail_alerts"] and plan["telegram_mail_alerts_allowed"]:
            send_user_telegram(user, f"📩 {mailbox['address']}\n{full.get('subject') or '(no subject)'}\nFrom: {sender}")

        new_count = current_count + 1
        notify_quota_state(user, plan, "messages", new_count, limit_value)

    db().commit()
    return inserted

def user_mailboxes(user_id):
    return db().execute("SELECT * FROM mailboxes WHERE user_id=? ORDER BY is_primary DESC, created_at DESC", (user_id,)).fetchall()

# -------------------- Google reCAPTCHA --------------------
def recaptcha_site_key():
    return cfg(
        ["RECAPTCHA_SITE_KEY", "GOOGLE_RECAPTCHA_SITE_KEY", "RECAPTCHA_PUBLIC_KEY", "GOOGLE_CAPTCHA_SITE_KEY"],
        ["recaptcha_site_key", "google_recaptcha_site_key"],
        "",
    )


def recaptcha_secret_key():
    return cfg(
        ["RECAPTCHA_SECRET_KEY", "GOOGLE_RECAPTCHA_SECRET_KEY", "RECAPTCHA_PRIVATE_KEY", "GOOGLE_CAPTCHA_SECRET_KEY"],
        ["recaptcha_secret_key", "google_recaptcha_secret_key"],
        "",
    )


def recaptcha_enabled():
    return bool(recaptcha_site_key() and recaptcha_secret_key())


def verify_recaptcha(action_label="form"):
    """Validate Google reCAPTCHA v2 checkbox token when configured."""
    site_key = recaptcha_site_key()
    secret_key = recaptcha_secret_key()
    if not site_key and not secret_key:
        return True
    if not site_key or not secret_key:
        flash("Google reCAPTCHA keys are incomplete. Add both site key and secret key.", "danger")
        return False
    token = request.form.get("g-recaptcha-response", "").strip()
    if not token:
        flash("Please complete the Google reCAPTCHA verification.", "danger")
        return False
    try:
        resp = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": secret_key,
                "response": token,
                "remoteip": request.headers.get("CF-Connecting-IP") or request.remote_addr,
            },
            timeout=8,
        )
        data = resp.json() if resp.content else {}
    except Exception as exc:
        print("RECAPTCHA_VERIFY_ERROR", action_label, exc)
        flash("Could not verify Google reCAPTCHA right now. Please try again.", "danger")
        return False
    if not data.get("success"):
        print("RECAPTCHA_FAILED", action_label, data.get("error-codes"))
        flash("Google reCAPTCHA verification failed. Please try again.", "danger")
        return False
    return True

# -------------------- Business API helpers --------------------
def api_key_hash(raw_key):
    return generate_password_hash(raw_key)

def check_api_key_hash(stored_hash, raw_key):
    try:
        return check_password_hash(stored_hash, raw_key)
    except Exception:
        return False

def business_api_enabled_for(user, plan=None):
    plan = plan or db().execute("SELECT * FROM plans WHERE key=?", (user["plan"],)).fetchone()
    return bool(user["is_admin"] or (plan and plan["key"] == "business"))

def api_error(message, status=400, code="error"):
    resp = jsonify({"ok": False, "error": {"code": code, "message": message}})
    resp.status_code = status
    return resp

def api_key_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        raw_key = ""
        if auth.lower().startswith("bearer "):
            raw_key = auth.split(" ", 1)[1].strip()
        if not raw_key:
            return api_error("Missing Bearer API key.", 401, "missing_api_key")
        prefix = raw_key[:14]
        rows = db().execute("""SELECT k.*, u.username, u.plan, u.verified, u.disabled, u.is_admin
                               FROM api_keys k JOIN users u ON u.id=k.user_id
                               WHERE k.revoked_at IS NULL AND k.key_prefix=?""", (prefix,)).fetchall()
        selected = None
        for row in rows:
            if check_api_key_hash(row["key_hash"], raw_key):
                selected = row
                break
        if not selected:
            return api_error("Invalid API key.", 401, "invalid_api_key")
        if selected["disabled"]:
            return api_error("Account disabled.", 403, "account_disabled")
        if not selected["verified"]:
            return api_error("Account must be verified before using the API.", 403, "account_not_verified")
        user = db().execute("SELECT * FROM users WHERE id=?", (selected["user_id"],)).fetchone()
        plan = db().execute("SELECT * FROM plans WHERE key=?", (user["plan"],)).fetchone()
        if not business_api_enabled_for(user, plan):
            return api_error("Business API is available only on the Business plan.", 403, "business_plan_required")
        g.api_user = user
        g.api_plan = plan
        g.api_key = selected
        db().execute("UPDATE api_keys SET last_used_at=? WHERE id=?", (now_iso(), selected["id"]))
        db().commit()
        return fn(*args, **kwargs)
    return wrapper

def api_sync_owned_mailboxes():
    new_total = 0
    for box in user_mailboxes(g.api_user["id"]):
        new_total += sync_mailbox(box)
    enforce_all_quota_warnings(g.api_user["id"])
    return new_total

def api_quota_payload(user_id=None, plan=None):
    user_id = user_id or g.api_user["id"]
    plan = plan or g.api_plan
    return {
        "plan": plan["key"],
        "mailboxes": {"used": user_mailbox_count(user_id), "limit": int(plan["mailbox_limit"] or 0)},
        "domains": {"used": user_domain_count(user_id), "limit": int(plan["domain_limit"] or 0)},
        "messages": {"used": user_message_count(user_id), "limit": int(plan["message_history"] or 0)},
        "telegram_mail_alerts_allowed": bool(plan["telegram_mail_alerts_allowed"]),
    }

def serialize_mailbox(box):
    return {
        "id": box["id"],
        "address": box["address"],
        "primary": bool(box["is_primary"]),
        "active": bool(box["is_active"]),
        "created_at": box["created_at"],
    }

def serialize_message(row, include_body=False):
    codes, links = extract_codes_links(row["body"] or "")
    data = {
        "id": row["id"],
        "subject": row["subject"] or "(No subject)",
        "from": row["sender"] or "unknown",
        "to": row["recipient"] or row["mailbox_address"],
        "mailbox": {"id": row["mailbox_id"], "address": row["mailbox_address"], "primary": bool(row["is_primary"])},
        "received_at": row["received_at"] or row["created_at"],
        "read": bool(row["read_at"]),
        "codes": codes,
        "links": links,
    }
    if include_body:
        data["body"] = row["body"] or ""
    return data

@app.context_processor
def inject_common():
    return {
        "current_user": g.get("user"),
        "unread_notifications": unread_count(g.user["id"]) if g.get("user") else 0,
        "unread_message_notifications": unread_message_count(g.user["id"]) if g.get("user") else 0,
        "admin_unread_notifications": unread_count(admin_only=1) if g.get("user") and g.user["is_admin"] else 0,
        "current_lang": get_lang(),
        "is_rtl": get_lang() == "ar",
        "recaptcha_site_key": recaptcha_site_key(),
        "recaptcha_enabled": recaptcha_enabled(),
    }

# -------------------- Public/Auth --------------------
@app.get("/")
def home():
    plans = db().execute("SELECT * FROM plans ORDER BY price ASC").fetchall()
    temp = session.get("visitor_mailbox")
    return render_template("home.html", plans=plans, temp=temp)

@app.post("/api/temp-mailbox")
def api_temp_mailbox():
    try:
        local = request.form.get("local") or (request.get_json(silent=True) or {}).get("local") if request.content_type and "json" in request.content_type else request.form.get("local")
        mb = create_mailtm_account(local)
        session["visitor_mailbox"] = mb
        return jsonify({"ok": True, "mailbox": mb["address"]})
    except Exception as exc:
        print("MAILBOX_CREATE_ERROR", exc)
        return jsonify({"ok": False, "error": str(exc)}), 502

@app.get("/register")
def register():
    temp = session.get("visitor_mailbox")
    if not temp:
        flash("Create a temporary mailbox first, then save it with an account.", "warning")
        return redirect(url_for("home"))
    return render_template("register.html", temp=temp)

@app.post("/register")
def register_post():
    temp = session.get("visitor_mailbox")
    if not temp:
        return redirect(url_for("home"))
    if not verify_recaptcha("register"):
        return redirect(url_for("register"))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    if len(username) < 3 or len(password) < 8 or password != confirm:
        flash("Use a username, matching passwords, and at least 8 password characters.", "danger")
        return redirect(url_for("register"))
    try:
        cur = db().execute(
            "INSERT INTO users(username,password_hash,plan,created_at) VALUES(?,?,?,?)",
            (username, generate_password_hash(password), "free", now_iso()),
        )
        user_id = cur.lastrowid
        db().execute(
            "INSERT INTO mailboxes(user_id,address,password,mailtm_id,token,is_primary,created_at) VALUES(?,?,?,?,?,?,?)",
            (user_id, temp["address"], temp["password"], temp.get("mailtm_id"), temp.get("token"), 1, now_iso()),
        )
        db().commit()
        session.pop("visitor_mailbox", None)
        session["user_id"] = user_id
        create_verification(user_id)
        create_notification(user_id, "Welcome to Vemail", "Connect Telegram to activate your account.", "account")
        create_notification(None, "New user registered", f"{username} registered with {temp['address']}", "account", admin_only=1)
        return redirect(url_for("verify"))
    except sqlite3.IntegrityError:
        flash("Username or mailbox already exists.", "danger")
        return redirect(url_for("register"))

@app.get("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")

@app.post("/forgot-password")
def forgot_password_post():
    if not verify_recaptcha("forgot_password"):
        return redirect(url_for("forgot_password"))
    email = request.form.get("email", "").strip().lower()
    user = find_user_by_mailbox(email)
    # Privacy-safe response: do not reveal whether an account exists.
    if user and user["telegram_linked"] and user["telegram_chat_id"]:
        code = f"{secrets.randbelow(900000)+100000}"
        expires = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
        db().execute("UPDATE password_resets SET used=1 WHERE user_id=? AND used=0", (user["id"],))
        db().execute("INSERT INTO password_resets(user_id,code_hash,expires_at,created_at) VALUES(?,?,?,?)",
                     (user["id"], generate_password_hash(code), expires, now_iso()))
        db().commit()
        send_user_telegram(user, f"🔐 Vemail password reset code: {code}\nThis code expires in 20 minutes.")
        session["reset_user_id"] = user["id"]
        session["reset_email"] = email
    flash("If this mailbox is linked to Telegram, a reset code was sent to your Telegram account.", "success")
    return redirect(url_for("reset_password"))

@app.get("/reset-password")
def reset_password():
    if not session.get("reset_user_id"):
        flash("Start password recovery with your Vemail mailbox first.", "warning")
        return redirect(url_for("forgot_password"))
    return render_template("reset_password.html", email=session.get("reset_email", ""))

@app.post("/reset-password")
def reset_password_post():
    uid = session.get("reset_user_id")
    if not uid:
        return redirect(url_for("forgot_password"))
    if not verify_recaptcha("reset_password"):
        return redirect(url_for("reset_password"))
    code = request.form.get("code", "").strip()
    new_password = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    if len(new_password) < 8 or new_password != confirm:
        flash("Password must be at least 8 characters and match confirmation.", "danger")
        return redirect(url_for("reset_password"))
    rows = db().execute("SELECT * FROM password_resets WHERE user_id=? AND used=0 ORDER BY id DESC LIMIT 5", (uid,)).fetchall()
    now = datetime.now(timezone.utc).isoformat()
    valid = None
    for row in rows:
        if row["expires_at"] >= now and check_password_hash(row["code_hash"], code):
            valid = row
            break
    if not valid:
        flash("Wrong or expired Telegram reset code.", "danger")
        return redirect(url_for("reset_password"))
    db().execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_password), uid))
    db().execute("UPDATE password_resets SET used=1 WHERE user_id=?", (uid,))
    db().commit()
    user = db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    create_notification(uid, "Password reset completed", "Your password was changed using Telegram verification.", "account", telegram=bool(user and user["telegram_linked"]))
    session.pop("reset_user_id", None)
    session.pop("reset_email", None)
    flash("Password updated. You can sign in now.", "success")
    return redirect(url_for("login"))

@app.get("/login")
def login():
    return render_template("login.html")

@app.post("/login")
def login_post():
    identifier = (request.form.get("email") or request.form.get("username") or "").strip().lower()
    password = request.form.get("password", "")
    user = None
    # Normal users sign in with their primary Vemail mailbox. Admin accounts may still
    # sign in with their configured admin username/email if they do not own a mailbox.
    if identifier:
        user = db().execute("SELECT * FROM users WHERE LOWER(username)=?", (identifier,)).fetchone()
        if not user:
            user = db().execute(
                """SELECT u.* FROM users u
                   JOIN mailboxes b ON b.user_id=u.id
                   WHERE LOWER(b.address)=? AND b.is_primary=1 AND u.disabled=0
                   LIMIT 1""",
                (identifier,),
            ).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid login. Use your primary Vemail address and password.", "danger")
        return redirect(url_for("login"))
    if user["disabled"]:
        flash("Account disabled.", "danger")
        return redirect(url_for("login"))
    session.clear(); session["user_id"] = user["id"]; session.permanent = True
    if user["verified"]:
        create_notification(user["id"], "Login notice", "Your Vemail account was opened.", "account", telegram=bool(user["telegram_linked"]))
        return redirect(url_for("dashboard"))
    return redirect(url_for("verify"))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

def create_verification(user_id):
    token = secrets.token_urlsafe(32)
    code = f"{secrets.randbelow(900000)+100000}"
    expires = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    db().execute("INSERT INTO verification_tokens(user_id,token,code,expires_at,created_at) VALUES(?,?,?,?,?)", (user_id, token, code, expires, now_iso()))
    db().commit()
    return token, code

def find_user_by_mailbox(address):
    address = (address or "").strip().lower()
    if not address:
        return None
    return db().execute("""SELECT u.* FROM users u
                         JOIN mailboxes b ON b.user_id=u.id
                         WHERE LOWER(b.address)=? AND u.disabled=0
                         ORDER BY b.is_primary DESC LIMIT 1""", (address,)).fetchone()


@app.get("/verify")
@login_required
def verify():
    row = db().execute("SELECT * FROM verification_tokens WHERE user_id=? AND used=0 ORDER BY id DESC", (g.user["id"],)).fetchone()
    if not row:
        token, code = create_verification(g.user["id"])
        row = db().execute("SELECT * FROM verification_tokens WHERE token=?", (token,)).fetchone()
    bot_name = user_bot_username()
    base = public_base_url() or request.url_root.rstrip("/")
    # Safe website link: redirects to Telegram. It must not verify the user without a Telegram chat_id.
    verify_url = f"{base}{url_for('telegram_verify_link', token=row['token'])}"
    telegram_url = f"https://t.me/{bot_name}?start=verify_{row['token']}"
    return render_template("verify.html", verify_url=verify_url, telegram_url=telegram_url, bot_name=bot_name, telegram_linked=bool(g.user["telegram_chat_id"]))

@app.post("/verify")
@login_required
def verify_post():
    code = request.form.get("code", "").strip()
    user = db().execute("SELECT * FROM users WHERE id=?", (g.user["id"],)).fetchone()
    row = db().execute("SELECT * FROM verification_tokens WHERE user_id=? AND used=0 AND code=? ORDER BY id DESC", (g.user["id"], code)).fetchone()
    if not row:
        flash("Wrong or expired code. Open Telegram first, press Start, then enter the code sent by the bot.", "danger")
        return redirect(url_for("verify"))
    if not user["telegram_chat_id"]:
        flash("Telegram is not linked yet. Press Open Telegram and Start first so the bot can capture your Telegram chat.", "warning")
        return redirect(url_for("verify"))
    db().execute("UPDATE verification_tokens SET used=1 WHERE id=?", (row["id"],))
    db().execute("UPDATE users SET verified=1, telegram_linked=1 WHERE id=?", (g.user["id"],))
    db().commit()
    create_notification(g.user["id"], "Account activated", "Telegram verification completed successfully.", "account", telegram=True)
    return redirect(url_for("dashboard"))

@app.get("/tg/verify/<token>")
def telegram_verify_link(token):
    row = db().execute("SELECT * FROM verification_tokens WHERE token=? AND used=0", (token,)).fetchone()
    bot_name = user_bot_username()
    if not row:
        return "Invalid, expired, or already used verification link. Return to Vemail and request a new activation link."
    telegram_url = f"https://t.me/{bot_name}?start=verify_{row['token']}"
    return redirect(telegram_url)

@app.post("/telegram/user-webhook")
def telegram_verify_webhook():
    data = request.get_json(silent=True) or {}
    msg = data.get("message") or data.get("edited_message") or {}
    chat = msg.get("chat") or {}
    text = msg.get("text", "") or ""
    chat_id = str(chat.get("id")) if chat.get("id") else ""
    username = chat.get("username") or chat.get("first_name") or ""

    m = re.search(r"verify_([A-Za-z0-9_\-]+)", text)
    if m:
        token = m.group(1)
        row = db().execute("SELECT * FROM verification_tokens WHERE token=? AND used=0", (token,)).fetchone()
        if row and chat_id:
            existing = db().execute(
                "SELECT id, username FROM users WHERE telegram_chat_id=? AND telegram_linked=1 AND id<>? LIMIT 1",
                (chat_id, row["user_id"]),
            ).fetchone()
            if existing:
                # Always return HTTP 200 to Telegram. Returning 409/4xx makes Telegram retry
                # the same webhook and the user receives the same warning many times.
                if should_send_duplicate_telegram_warning(chat_id, row["user_id"], token):
                    send_user_telegram(
                        {"telegram_chat_id": chat_id},
                        "⚠️ This Telegram account is already linked to another Vemail account. One Telegram account can verify only one Vemail account.",
                    )
                    create_notification(
                        None,
                        "Duplicate Telegram link blocked",
                        f"Telegram chat_id {chat_id} tried to link another Vemail account.",
                        "telegram",
                        admin_only=1,
                    )
                return jsonify({"ok": True, "blocked": True, "reason": "telegram_already_linked"})
            db().execute("UPDATE users SET telegram_chat_id=?, telegram_username=?, telegram_linked=1 WHERE id=?", (chat_id, username, row["user_id"]))
            db().commit()
            user = db().execute("SELECT * FROM users WHERE id=?", (row["user_id"],)).fetchone()
            send_user_telegram(user, f"✅ Telegram linked to Vemail.\nYour activation code is: {row['code']}\nEnter this code on the Vemail activation page.")
        elif chat_id:
            send_user_telegram({"telegram_chat_id": chat_id}, "⚠️ This Vemail activation link is invalid or already used. Please open Vemail and request a new verification link.")
    elif text.startswith("/start") and chat_id:
        send_user_telegram({"telegram_chat_id": chat_id}, "Welcome to Vemail. Please open the activation link from the website so I can send your verification code.")
    return jsonify({"ok": True})


# -------------------- User UI --------------------
@app.get("/dashboard")
@login_required
@verified_required
def dashboard():
    boxes = user_mailboxes(g.user["id"])
    plan = get_plan()
    enforce_all_quota_warnings(g.user["id"])
    message_count = db().execute("SELECT COUNT(*) c FROM messages WHERE user_id=?", (g.user["id"],)).fetchone()["c"]
    primary = next((b for b in boxes if b["is_primary"]), boxes[0] if boxes else None)
    return render_template("dashboard.html", plan=plan, boxes=boxes, primary=primary, message_count=message_count)

@app.get("/inbox")
@login_required
@verified_required
def inbox():
    boxes = user_mailboxes(g.user["id"])
    for box in boxes:
        sync_mailbox(box)
    enforce_all_quota_warnings(g.user["id"])
    mailbox_filter = request.args.get("mailbox", "all")
    q = request.args.get("q", "").strip()
    params = [g.user["id"]]
    where = "m.user_id=?"
    if mailbox_filter == "primary":
        where += " AND b.is_primary=1"
    elif mailbox_filter == "sub":
        where += " AND b.is_primary=0"
    elif mailbox_filter.isdigit():
        where += " AND m.mailbox_id=?"; params.append(int(mailbox_filter))
    if q:
        where += " AND (m.subject LIKE ? OR m.sender LIKE ? OR m.body LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    display_limit = max(0, min(50, int(get_plan()["message_history"] or 0)))
    if display_limit <= 0:
        rows = []
    else:
        rows = db().execute(f"""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                                  JOIN mailboxes b ON b.id=m.mailbox_id
                                  WHERE {where} ORDER BY COALESCE(m.received_at,m.created_at) DESC LIMIT ?""", params + [display_limit]).fetchall()
    enriched = []
    for r in rows:
        codes, links = extract_codes_links(r["body"] or "")
        enriched.append({"row": r, "codes": codes, "links": links})
    return render_template("inbox.html", boxes=boxes, messages=enriched, mailbox_filter=mailbox_filter, q=q)

@app.get("/message/<int:message_id>")
@login_required
@verified_required
def message_detail(message_id):
    r = db().execute("""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                        JOIN mailboxes b ON b.id=m.mailbox_id
                        WHERE m.id=? AND m.user_id=?""", (message_id, g.user["id"])).fetchone()
    if not r:
        abort(404)
    if not r["read_at"]:
        db().execute("UPDATE messages SET read_at=? WHERE id=? AND user_id=?", (now_iso(), message_id, g.user["id"]))
        db().commit()
        r = db().execute("""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                        JOIN mailboxes b ON b.id=m.mailbox_id
                        WHERE m.id=? AND m.user_id=?""", (message_id, g.user["id"])).fetchone()
    codes, links = extract_codes_links(r["body"] or "")
    return render_template("message_detail.html", msg=r, codes=codes, links=links)

@app.post("/inbox/read-all")
@login_required
@verified_required
def inbox_read_all():
    """Mark all messages owned by the current user as read.
    This only touches rows with the current user's user_id, so it does not affect
    other users, admin notifications, payment notifications, or plan counters.
    """
    db().execute(
        "UPDATE messages SET read_at=? WHERE user_id=? AND read_at IS NULL",
        (now_iso(), g.user["id"]),
    )
    db().commit()
    wants_json = "application/json" in request.headers.get("Accept", "").lower() or request.is_json
    if wants_json:
        return jsonify({"ok": True, "unread": unread_message_count(g.user["id"]), "unread_notifications": unread_count(g.user["id"])})
    flash("Inbox messages marked as read.", "success")
    return redirect(url_for("inbox"))

@app.post("/api/inbox/refresh")
@login_required
def api_refresh_inbox():
    total = 0
    for box in user_mailboxes(g.user["id"]):
        total += sync_mailbox(box)
    enforce_all_quota_warnings(g.user["id"])
    return jsonify({"ok": True, "new": total, "unread": unread_message_count(g.user["id"])})

@app.get("/api/inbox/live")
@login_required
@verified_required
def api_inbox_live():
    """Background inbox refresh for the UI without reloading the page."""
    new_total = 0
    boxes = user_mailboxes(g.user["id"])
    for box in boxes:
        new_total += sync_mailbox(box)

    mailbox_filter = request.args.get("mailbox", "all")
    q = request.args.get("q", "").strip()
    params = [g.user["id"]]
    where = "m.user_id=?"
    if mailbox_filter == "primary":
        where += " AND b.is_primary=1"
    elif mailbox_filter == "sub":
        where += " AND b.is_primary=0"
    elif mailbox_filter.isdigit():
        where += " AND m.mailbox_id=?"
        params.append(int(mailbox_filter))
    if q:
        where += " AND (m.subject LIKE ? OR m.sender LIKE ? OR m.body LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]

    display_limit = max(0, min(50, int(get_plan()["message_history"] or 0)))
    if display_limit <= 0:
        rows = []
    else:
        rows = db().execute(f"""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                                  JOIN mailboxes b ON b.id=m.mailbox_id
                                  WHERE {where} ORDER BY COALESCE(m.received_at,m.created_at) DESC LIMIT ?""", params + [display_limit]).fetchall()
    messages = []
    for r in rows:
        codes, links = extract_codes_links(r["body"] or "")
        messages.append({
            "id": r["id"],
            "subject": r["subject"] or "(No subject)",
            "sender": r["sender"] or "unknown",
            "mailbox_address": r["mailbox_address"],
            "is_primary": bool(r["is_primary"]),
            "received_at": r["received_at"] or r["created_at"],
            "read": bool(r["read_at"]),
            "first_code": codes[0] if codes else "",
            "first_link": links[0] if links else "",
            "url": url_for("message_detail", message_id=r["id"]),
        })
    return jsonify({
        "ok": True,
        "new": new_total,
        "unread": unread_message_count(g.user["id"]),
        "messages": messages,
    })

@app.get("/api/ui/state")
@login_required
@verified_required
def api_ui_state():
    """Background state refresh used by every logged-in page.
    Browser permission alone does not create notifications; this endpoint syncs
    the user's own mailboxes, then returns one-shot native notification events
    for the frontend service worker to display outside the page.
    """
    new_total = 0
    for box in user_mailboxes(g.user["id"]):
        new_total += sync_mailbox(box)
    enforce_all_quota_warnings(g.user["id"])

    browser_events = []
    if new_total > 0:
        key = f"mail-batch:{g.user['id']}:{unread_message_count(g.user['id'])}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        if mark_browser_event_once(g.user["id"], key):
            browser_events.append({
                "title": "New email received" if get_lang() == "en" else "وصلت رسالة جديدة",
                "body": (f"{new_total} new message(s) in your Vemail inbox" if get_lang() == "en" else f"وصلت {new_total} رسالة جديدة في بريد Vemail"),
                "url": url_for("inbox"),
                "tag": "vemail-new-mail"
            })

    return jsonify({
        "ok": True,
        "new": new_total,
        "unread_messages": unread_message_count(g.user["id"]),
        "unread_notifications": unread_count(g.user["id"]),
        "admin_unread_notifications": unread_count(admin_only=1) if g.user["is_admin"] else 0,
        "browser_notifications": browser_events,
        "browser_notifications_supported": True,
        "message_limit": int(get_plan()["message_history"] or 0),
        "message_count": user_message_count(g.user["id"]),
        "mailbox_limit": int(get_plan()["mailbox_limit"] or 0),
        "mailbox_count": user_mailbox_count(g.user["id"]),
    })

@app.get("/mailboxes")
@login_required
@verified_required
def mailboxes():
    boxes = user_mailboxes(g.user["id"])
    plan = get_plan()
    return render_template("mailboxes.html", boxes=boxes, plan=plan)

@app.post("/mailboxes/create")
@login_required
@verified_required
def create_mailbox():
    plan = get_plan()
    count = user_mailbox_count(g.user["id"])
    user = db().execute("SELECT * FROM users WHERE id=?", (g.user["id"],)).fetchone()
    if count >= int(plan["mailbox_limit"] or 0):
        notify_quota_state(user, plan, "mailboxes", count, plan["mailbox_limit"], force_reached=True)
        flash("Mailbox limit reached. Upgrade to add more.", "warning")
        return redirect(url_for("mailboxes"))
    notify_quota_state(user, plan, "mailboxes", count, plan["mailbox_limit"])
    domain_count = user_domain_count(g.user["id"])
    current_domains = user_domains(g.user["id"])
    allowed_domains = current_domains if domain_count >= int(plan["domain_limit"] or 0) and current_domains else None
    if domain_count >= int(plan["domain_limit"] or 0) and not current_domains:
        notify_quota_state(user, plan, "domains", domain_count, plan["domain_limit"], force_reached=True)
        flash("Domain limit reached. Upgrade to add more domains.", "warning")
        return redirect(url_for("mailboxes"))
    local = request.form.get("local", "").strip()
    try:
        mb = create_mailtm_account(local, allowed_domains=allowed_domains)
    except Exception as exc:
        print("MAILBOX_CREATE_ERROR", exc)
        create_notification(g.user["id"], "Mailbox creation failed", str(exc), "account", telegram=bool(g.user["telegram_linked"]))
        flash("Mailbox creation failed: " + str(exc), "warning")
        return redirect(url_for("mailboxes"))
    db().execute("INSERT INTO mailboxes(user_id,address,password,mailtm_id,token,is_primary,created_at) VALUES(?,?,?,?,?,?,?)", (g.user["id"], mb["address"], mb["password"], mb.get("mailtm_id"), mb.get("token"), 0, now_iso()))
    db().commit()
    create_notification(g.user["id"], "Mailbox created", mb["address"], "account")
    enforce_all_quota_warnings(g.user["id"])
    return redirect(url_for("mailboxes"))

@app.post("/mailboxes/<int:box_id>/primary")
@login_required
@verified_required
def make_primary(box_id):
    plan = get_plan()
    if not plan["can_change_primary_email"]:
        flash("Changing primary mailbox is available on paid plans.", "warning")
        return redirect(url_for("mailboxes"))
    box = db().execute("SELECT * FROM mailboxes WHERE id=? AND user_id=?", (box_id, g.user["id"])).fetchone()
    if not box:
        abort(404)
    db().execute("UPDATE mailboxes SET is_primary=0 WHERE user_id=?", (g.user["id"],))
    db().execute("UPDATE mailboxes SET is_primary=1 WHERE id=?", (box_id,))
    db().commit()
    return redirect(url_for("mailboxes"))

@app.get("/notifications")
@login_required
@verified_required
def notifications():
    cat = request.args.get("cat", "all")
    params = [g.user["id"]]
    where = "user_id=? AND admin_only=0"
    if cat != "all":
        where += " AND category=?"; params.append(cat)
    rows = db().execute(f"SELECT * FROM notifications WHERE {where} ORDER BY created_at DESC LIMIT 100", params).fetchall()
    return render_template("notifications.html", notifications=rows, cat=cat)

@app.post("/notifications/read-all")
@login_required
def notifications_read_all():
    db().execute("UPDATE notifications SET read_at=? WHERE user_id=? AND admin_only=0 AND read_at IS NULL", (now_iso(), g.user["id"]))
    db().commit()
    return redirect(url_for("notifications"))

@app.get("/account")
@login_required
@verified_required
def account():
    plan = get_plan()
    api_keys = db().execute("SELECT id, key_prefix, label, last_used_at, revoked_at, created_at FROM api_keys WHERE user_id=? ORDER BY created_at DESC", (g.user["id"],)).fetchall()
    new_api_key = session.pop("new_api_key", None)
    return render_template("account.html", plan=plan, api_keys=api_keys, new_api_key=new_api_key, business_api_enabled=business_api_enabled_for(g.user, plan))

@app.post("/account/api-key/create")
@login_required
@verified_required
def create_business_api_key():
    plan = get_plan()
    if not business_api_enabled_for(g.user, plan):
        create_notification(g.user["id"], "Business API unavailable", "Upgrade to Business to create API keys.", "plan", telegram=bool(g.user["telegram_linked"]))
        flash("Business API is available only on the Business plan.", "warning")
        return redirect(url_for("account"))
    raw_key = "vemail_live_" + secrets.token_urlsafe(32)
    prefix = raw_key[:14]
    db().execute("INSERT INTO api_keys(user_id,key_hash,key_prefix,label,created_at) VALUES(?,?,?,?,?)", (g.user["id"], api_key_hash(raw_key), prefix, request.form.get("label") or "Business API", now_iso()))
    db().commit()
    session["new_api_key"] = raw_key
    create_notification(g.user["id"], "Business API key created", "A new API key was created. Copy it now; it will not be shown again.", "account", telegram=bool(g.user["telegram_linked"]))
    return redirect(url_for("account"))

@app.post("/account/api-key/<int:key_id>/revoke")
@login_required
@verified_required
def revoke_business_api_key(key_id):
    db().execute("UPDATE api_keys SET revoked_at=? WHERE id=? AND user_id=? AND revoked_at IS NULL", (now_iso(), key_id, g.user["id"]))
    db().commit()
    create_notification(g.user["id"], "Business API key revoked", "An API key was revoked.", "account", telegram=bool(g.user["telegram_linked"]))
    return redirect(url_for("account"))

@app.post("/account/password")
@login_required
@verified_required
def change_password():
    current = request.form.get("current_password", "")
    new = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    if not check_password_hash(g.user["password_hash"], current) or len(new) < 8 or new != confirm:
        flash("Password change failed. Check current password and confirmation.", "danger")
        return redirect(url_for("account"))
    db().execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new), g.user["id"]))
    db().commit()
    create_notification(g.user["id"], "Password changed", "Your account password was changed.", "account", telegram=bool(g.user["telegram_linked"]))
    flash("Password updated.", "success")
    return redirect(url_for("account"))

@app.post("/account/telegram-mail-alerts")
@login_required
@verified_required
def toggle_telegram_mail_alerts():
    plan = get_plan()
    enable = 1 if request.form.get("enabled") == "1" else 0
    if enable and not plan["telegram_mail_alerts_allowed"]:
        flash("Email-to-Telegram alerts are a paid feature.", "warning")
        return redirect(url_for("upgrade"))
    db().execute("UPDATE users SET telegram_mail_alerts=? WHERE id=?", (enable, g.user["id"]))
    db().commit()
    return redirect(url_for("account"))

@app.post("/account/test-telegram")
@login_required
@verified_required
def test_telegram_user():
    ok = send_user_telegram(g.user, "✅ Vemail test message.")
    flash("Test sent." if ok else "Telegram test failed or chat id is missing.", "success" if ok else "warning")
    return redirect(url_for("account"))

@app.post("/api/browser-notification-test")
@login_required
@verified_required
def api_browser_notification_test():
    return jsonify({
        "ok": True,
        "notification": {
            "title": "Vemail",
            "body": "Browser notifications are enabled." if get_lang() == "en" else "تم تفعيل إشعارات المتصفح.",
            "url": url_for("dashboard"),
            "tag": "vemail-test"
        }
    })

@app.get("/upgrade")
@login_required
@verified_required
def upgrade():
    plans = db().execute("SELECT * FROM plans ORDER BY price ASC").fetchall()
    wallet_address = db_first_cfg(["usdt_trc20_address", "crypto_usdt_trc20"], ["USDT_TRC20_ADDRESS", "CRYPTO_USDT_TRC20"], "")
    return render_template("upgrade.html", plans=plans, wallet_address=wallet_address)

@app.post("/upgrade/request")
@login_required
@verified_required
def upgrade_request():
    plan_key = request.form.get("plan")
    plan = get_plan(plan_key)
    if not plan or plan["key"] == "free":
        abort(400)
    txid = request.form.get("txid", "").strip()
    network = request.form.get("network", "TRC20").strip()
    db().execute("INSERT INTO payments(user_id,plan,amount,network,txid,status,created_at) VALUES(?,?,?,?,?,?,?)", (g.user["id"], plan["key"], plan["price"], network, txid, "pending", now_iso()))
    db().commit()
    create_notification(g.user["id"], "Payment request submitted", f"Your {plan['label']} request is pending admin review.", "plan", telegram=bool(g.user["telegram_linked"]))
    create_notification(None, "New payment request", f"{g.user['username']} requested {plan['label']} / TXID: {txid}", "plan", admin_only=1)
    return redirect(url_for("payment_history"))

@app.get("/payments-history")
@login_required
@verified_required
def payment_history():
    rows = db().execute(
        """SELECT p.*, COALESCE(pl.label, p.plan) AS plan_label
           FROM payments p
           LEFT JOIN plans pl ON pl.key = p.plan
           WHERE p.user_id=?
           ORDER BY p.created_at DESC""",
        (g.user["id"],),
    ).fetchall()
    totals = {
        "all": db().execute("SELECT COUNT(*) c FROM payments WHERE user_id=?", (g.user["id"],)).fetchone()["c"],
        "pending": db().execute("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='pending'", (g.user["id"],)).fetchone()["c"],
        "accepted": db().execute("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='accepted'", (g.user["id"],)).fetchone()["c"],
        "rejected": db().execute("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='rejected'", (g.user["id"],)).fetchone()["c"],
        "paid": db().execute("SELECT COALESCE(SUM(amount),0) c FROM payments WHERE user_id=? AND status='accepted'", (g.user["id"],)).fetchone()["c"],
    }
    return render_template("payment_history.html", payments=rows, totals=totals)

# -------------------- Admin --------------------
# -------------------- Business API v1 --------------------
@app.get("/api/v1/usage")
@api_key_required
def api_v1_usage():
    api_sync_owned_mailboxes()
    return jsonify({"ok": True, "usage": api_quota_payload()})

@app.get("/api/v1/mailboxes")
@api_key_required
def api_v1_mailboxes():
    boxes = [serialize_mailbox(b) for b in user_mailboxes(g.api_user["id"])]
    return jsonify({"ok": True, "usage": api_quota_payload(), "mailboxes": boxes})

@app.post("/api/v1/mailboxes")
@api_key_required
def api_v1_create_mailbox():
    plan = g.api_plan
    count = user_mailbox_count(g.api_user["id"])
    if count >= int(plan["mailbox_limit"] or 0):
        notify_quota_state(g.api_user, plan, "mailboxes", count, plan["mailbox_limit"], force_reached=True)
        return api_error("Mailbox limit reached for this plan.", 403, "mailbox_limit_reached")
    domain_count = user_domain_count(g.api_user["id"])
    current_domains = user_domains(g.api_user["id"])
    allowed_domains = current_domains if domain_count >= int(plan["domain_limit"] or 0) and current_domains else None
    payload = request.get_json(silent=True) or {}
    local = str(payload.get("local") or "").strip()
    try:
        mb = create_mailtm_account(local, allowed_domains=allowed_domains)
    except Exception as exc:
        create_notification(g.api_user["id"], "API mailbox creation failed", str(exc), "account", telegram=bool(g.api_user["telegram_linked"]))
        return api_error("Mailbox creation failed: " + str(exc), 502, "mailbox_create_failed")
    db().execute("INSERT INTO mailboxes(user_id,address,password,mailtm_id,token,is_primary,created_at) VALUES(?,?,?,?,?,?,?)", (g.api_user["id"], mb["address"], mb["password"], mb.get("mailtm_id"), mb.get("token"), 0 if count else 1, now_iso()))
    db().commit()
    box = db().execute("SELECT * FROM mailboxes WHERE user_id=? AND address=?", (g.api_user["id"], mb["address"])).fetchone()
    create_notification(g.api_user["id"], "API mailbox created", mb["address"], "account", telegram=bool(g.api_user["telegram_linked"]))
    enforce_all_quota_warnings(g.api_user["id"])
    return jsonify({"ok": True, "mailbox": serialize_mailbox(box), "usage": api_quota_payload()}), 201

@app.get("/api/v1/messages")
@api_key_required
def api_v1_messages():
    api_sync_owned_mailboxes()
    limit = max(1, min(50, int(request.args.get("limit", 10))))
    offset = max(0, int(request.args.get("offset", 0)))
    params = [g.api_user["id"]]
    where = "m.user_id=?"
    mailbox = request.args.get("mailbox")
    unread = request.args.get("unread")
    if mailbox:
        if mailbox.isdigit():
            where += " AND m.mailbox_id=?"; params.append(int(mailbox))
        else:
            where += " AND b.address=?"; params.append(mailbox)
    if unread in ("1", "true", "yes"):
        where += " AND m.read_at IS NULL"
    rows = db().execute(f"""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                          JOIN mailboxes b ON b.id=m.mailbox_id
                          WHERE {where} ORDER BY COALESCE(m.received_at,m.created_at) DESC LIMIT ? OFFSET ?""", params + [limit, offset]).fetchall()
    return jsonify({"ok": True, "usage": api_quota_payload(), "messages": [serialize_message(r) for r in rows]})

@app.get("/api/v1/messages/<int:message_id>")
@api_key_required
def api_v1_message_detail(message_id):
    r = db().execute("""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                        JOIN mailboxes b ON b.id=m.mailbox_id
                        WHERE m.id=? AND m.user_id=?""", (message_id, g.api_user["id"])).fetchone()
    if not r:
        return api_error("Message not found.", 404, "message_not_found")
    if request.args.get("mark_read") in ("1", "true", "yes") and not r["read_at"]:
        db().execute("UPDATE messages SET read_at=? WHERE id=? AND user_id=?", (now_iso(), message_id, g.api_user["id"]))
        db().commit()
        r = db().execute("""SELECT m.*, b.address mailbox_address, b.is_primary FROM messages m
                        JOIN mailboxes b ON b.id=m.mailbox_id
                        WHERE m.id=? AND m.user_id=?""", (message_id, g.api_user["id"])).fetchone()
    return jsonify({"ok": True, "message": serialize_message(r, include_body=True)})

@app.post("/api/v1/messages/<int:message_id>/read")
@api_key_required
def api_v1_message_read(message_id):
    db().execute("UPDATE messages SET read_at=? WHERE id=? AND user_id=?", (now_iso(), message_id, g.api_user["id"]))
    db().commit()
    return jsonify({"ok": True, "unread": unread_message_count(g.api_user["id"])})

@app.post("/api/v1/messages/read-all")
@api_key_required
def api_v1_messages_read_all():
    db().execute("UPDATE messages SET read_at=? WHERE user_id=? AND read_at IS NULL", (now_iso(), g.api_user["id"]))
    db().commit()
    return jsonify({"ok": True, "unread": unread_message_count(g.api_user["id"])})

@app.get("/api/v1/docs")
def api_v1_docs():
    return jsonify({
        "ok": True,
        "name": "Vemail Business API v1",
        "auth": "Authorization: Bearer <api_key>",
        "business_plan_required": True,
        "endpoints": [
            "GET /api/v1/usage",
            "GET /api/v1/mailboxes",
            "POST /api/v1/mailboxes {local?}",
            "GET /api/v1/messages?limit=10&offset=0&mailbox=<id_or_address>&unread=1",
            "GET /api/v1/messages/<id>?mark_read=1",
            "POST /api/v1/messages/<id>/read",
            "POST /api/v1/messages/read-all"
        ]
    })

@app.get("/admin")
@login_required
@admin_required
def admin_overview():
    kpi = {
        "users": db().execute("SELECT COUNT(*) c FROM users WHERE is_admin=0").fetchone()["c"],
        "verified": db().execute("SELECT COUNT(*) c FROM users WHERE verified=1 AND is_admin=0").fetchone()["c"],
        "mailboxes": db().execute("SELECT COUNT(*) c FROM mailboxes").fetchone()["c"],
        "messages": db().execute("SELECT COUNT(*) c FROM messages").fetchone()["c"],
        "pending_payments": db().execute("SELECT COUNT(*) c FROM payments WHERE status='pending'").fetchone()["c"],
        "confirmed_revenue": db().execute("SELECT COALESCE(SUM(amount),0) c FROM payments WHERE status='accepted'").fetchone()["c"],
        "expected_revenue": db().execute("SELECT COALESCE(SUM(amount),0) c FROM payments WHERE status='pending'").fetchone()["c"],
    }
    chart = []
    today = datetime.now(timezone.utc).date()
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        prefix = d.isoformat()
        chart.append({
            "date": prefix[5:],
            "new_users": db().execute("SELECT COUNT(*) c FROM users WHERE created_at LIKE ?", (prefix + "%",)).fetchone()["c"],
            "messages": db().execute("SELECT COUNT(*) c FROM messages WHERE created_at LIKE ?", (prefix + "%",)).fetchone()["c"],
            "payments": db().execute("SELECT COUNT(*) c FROM payments WHERE created_at LIKE ?", (prefix + "%",)).fetchone()["c"],
        })
    return render_template("admin_overview.html", kpi=kpi, chart=json.dumps(chart))

@app.get("/admin/users")
@login_required
@admin_required
def admin_users():
    rows = db().execute("""SELECT u.*,
        (SELECT COUNT(*) FROM mailboxes b WHERE b.user_id=u.id) mailboxes_count,
        (SELECT COUNT(*) FROM messages m WHERE m.user_id=u.id) messages_count
        FROM users u WHERE u.is_admin=0 ORDER BY u.created_at DESC""").fetchall()
    return render_template("admin_users.html", users=rows)

@app.get("/admin/users/<int:user_id>")
@login_required
@admin_required
def admin_user_detail(user_id):
    user = db().execute("SELECT * FROM users WHERE id=? AND is_admin=0", (user_id,)).fetchone()
    if not user: abort(404)
    boxes = user_mailboxes(user_id)
    messages = db().execute("SELECT * FROM messages WHERE user_id=? ORDER BY created_at DESC LIMIT 25", (user_id,)).fetchall()
    notes = db().execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 25", (user_id,)).fetchall()
    payments = db().execute("SELECT p.*, COALESCE(pl.label, p.plan) AS plan_label FROM payments p LEFT JOIN plans pl ON pl.key=p.plan WHERE p.user_id=? ORDER BY p.created_at DESC", (user_id,)).fetchall()
    plans = db().execute("SELECT * FROM plans ORDER BY price").fetchall()
    api_keys = db().execute("SELECT id, key_prefix, label, last_used_at, revoked_at, created_at FROM api_keys WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
    return render_template("admin_user_detail.html", user=user, boxes=boxes, messages=messages, notes=notes, payments=payments, plans=plans, api_keys=api_keys)

@app.post("/admin/users/<int:user_id>/plan")
@login_required
@admin_required
def admin_change_plan(user_id):
    plan = request.form.get("plan")
    if not get_plan(plan): abort(400)
    db().execute("UPDATE users SET plan=? WHERE id=? AND is_admin=0", (plan, user_id))
    db().commit()
    create_notification(user_id, "Plan changed", f"Your account is now on {plan}.", "plan", telegram=True)
    return redirect(url_for("admin_user_detail", user_id=user_id))

@app.post("/admin/users/<int:user_id>/verify")
@login_required
@admin_required
def admin_verify_user(user_id):
    db().execute("UPDATE users SET verified=1 WHERE id=? AND is_admin=0", (user_id,))
    db().commit()
    create_notification(user_id, "Account manually verified", "Admin activated your account.", "account", telegram=True)
    return redirect(url_for("admin_user_detail", user_id=user_id))

@app.post("/admin/users/<int:user_id>/notify")
@login_required
@admin_required
def admin_notify_user(user_id):
    title = request.form.get("title", "Admin message")
    body = request.form.get("body", "")
    create_notification(user_id, title, body, "account", telegram=True)
    return redirect(url_for("admin_user_detail", user_id=user_id))

@app.post("/admin/users/<int:user_id>/delete")
@login_required
@admin_required
def admin_delete_user(user_id):
    db().execute("DELETE FROM users WHERE id=? AND is_admin=0", (user_id,))
    db().commit()
    return redirect(url_for("admin_users"))

@app.get("/admin/payments")
@login_required
@admin_required
def admin_payments():
    status = request.args.get("status", "all")
    params = []
    where = "1=1"
    if status != "all":
        where = "p.status=?"; params.append(status)
    rows = db().execute(f"""
        SELECT p.*,
               u.username,
               u.plan AS current_plan,
               (SELECT mb.address FROM mailboxes mb WHERE mb.user_id=u.id ORDER BY mb.is_primary DESC, mb.id ASC LIMIT 1) AS primary_email,
               COALESCE(pl.label, p.plan) AS plan_label
        FROM payments p
        JOIN users u ON u.id=p.user_id
        LEFT JOIN plans pl ON pl.key=p.plan
        WHERE {where}
        ORDER BY p.created_at DESC
    """, params).fetchall()
    return render_template("admin_payments.html", payments=rows, status=status)

@app.post("/admin/payments/<int:payment_id>/<action>")
@login_required
@admin_required
def admin_payment_action(payment_id, action):
    p = db().execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    if not p: abort(404)
    if action == "accept":
        db().execute("UPDATE payments SET status='accepted', decided_at=? WHERE id=?", (now_iso(), payment_id))
        db().execute("UPDATE users SET plan=? WHERE id=?", (p["plan"], p["user_id"]))
        create_notification(p["user_id"], "Payment accepted", f"Your {p['plan']} plan is active.", "plan", telegram=True)
    elif action == "reject":
        db().execute("UPDATE payments SET status='rejected', decided_at=? WHERE id=?", (now_iso(), payment_id))
        create_notification(p["user_id"], "Payment rejected", "Please contact support or submit a corrected TXID.", "plan", telegram=True)
    elif action == "delete":
        db().execute("DELETE FROM payments WHERE id=?", (payment_id,))
    else:
        abort(400)
    db().commit()
    return redirect(url_for("admin_payments"))

@app.get("/admin/plans")
@login_required
@admin_required
def admin_plans():
    plans = db().execute("SELECT * FROM plans ORDER BY price").fetchall()
    return render_template("admin_plans.html", plans=plans)

@app.post("/admin/plans/<key>")
@login_required
@admin_required
def admin_update_plan(key):
    fields = ["price","mailbox_limit","domain_limit","message_history","can_save_messages","can_change_primary_email","telegram_mail_alerts_allowed"]
    vals = []
    for f in fields:
        vals.append(float(request.form.get(f, 0)) if f == "price" else int(request.form.get(f, 0)))
    db().execute("""UPDATE plans SET price=?, mailbox_limit=?, domain_limit=?, message_history=?, can_save_messages=?, can_change_primary_email=?, telegram_mail_alerts_allowed=? WHERE key=?""", (*vals, key))
    db().commit()
    return redirect(url_for("admin_plans"))

@app.get("/admin/limits")
@login_required
@admin_required
def admin_limits():
    users = db().execute("""SELECT u.*, p.mailbox_limit, p.message_history,
        (SELECT COUNT(*) FROM mailboxes b WHERE b.user_id=u.id) mailbox_count,
        (SELECT COUNT(*) FROM messages m WHERE m.user_id=u.id) message_count
        FROM users u JOIN plans p ON p.key=u.plan WHERE u.is_admin=0 ORDER BY message_count DESC""").fetchall()
    return render_template("admin_limits.html", users=users)

@app.get("/admin/notifications")
@login_required
@admin_required
def admin_notifications():
    rows = db().execute("SELECT * FROM notifications WHERE admin_only=1 ORDER BY created_at DESC LIMIT 100").fetchall()
    return render_template("admin_notifications.html", notifications=rows)

@app.post("/admin/notifications/read-all")
@login_required
@admin_required
def admin_notifications_read_all():
    db().execute("UPDATE notifications SET read_at=? WHERE admin_only=1 AND read_at IS NULL", (now_iso(),))
    db().commit()
    return redirect(url_for("admin_notifications"))

@app.post("/admin/telegram/save")
@login_required
@admin_required
def admin_telegram_save():
    keys = [
        "admin_telegram_bot_token", "admin_telegram_chat_id",
        "user_telegram_bot_token", "user_telegram_bot_username",
        "public_base_url"
    ]
    for key in keys:
        value = request.form.get(key, "").strip()
        db().execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    db().commit()
    flash("Telegram settings saved. Now test Admin Bot and set User Bot webhook.", "success")
    return redirect(url_for("admin_telegram"))

@app.post("/admin/telegram/test")
@login_required
@admin_required
def admin_telegram_test():
    ok = send_admin_telegram("✅ Vemail admin bot test.")
    flash("Admin Telegram test sent." if ok else "Admin Telegram test failed. Check Admin Bot token/chat id and make sure you pressed Start in the admin bot.", "success" if ok else "warning")
    return redirect(url_for("admin_telegram"))

@app.post("/admin/telegram/set-user-webhook")
@login_required
@admin_required
def admin_set_user_webhook():
    base = public_base_url() or request.url_root.rstrip("/")
    webhook_url = f"{base}/telegram/user-webhook"
    result = telegram_api(user_bot_token(), "setWebhook", {"url": webhook_url, "drop_pending_updates": False})
    flash(("User Bot webhook set: " if result.get("ok") else "User Bot webhook failed: ") + str(result.get("description") or result.get("result")), "success" if result.get("ok") else "warning")
    return redirect(url_for("admin_telegram"))

@app.get("/admin/telegram")
@login_required
@admin_required
def admin_telegram():
    base = public_base_url() or request.url_root.rstrip("/")
    u_token = user_bot_token()
    a_token = admin_bot_token()
    status = {
        "admin_bot": bool(a_token and admin_chat_id()),
        "user_bot": bool(u_token),
        "admin_has_chat": bool(admin_chat_id()),
        "public_base_url": base,
        "user_webhook_url": f"{base}/telegram/user-webhook",
        "user_getme": telegram_api(u_token, "getMe") if u_token else {"ok": False, "description": "Missing user token"},
        "user_webhook_info": telegram_api(u_token, "getWebhookInfo") if u_token else {"ok": False, "description": "Missing user token"},
        "admin_getme": telegram_api(a_token, "getMe") if a_token else {"ok": False, "description": "Missing admin token"},
    }
    telegram_settings = {
        "admin_telegram_bot_token": _direct_setting("admin_telegram_bot_token"),
        "admin_telegram_chat_id": _direct_setting("admin_telegram_chat_id") or _direct_setting("telegram_admin_chat_id"),
        "user_telegram_bot_token": _direct_setting("user_telegram_bot_token"),
        "user_telegram_bot_username": _direct_setting("user_telegram_bot_username"),
        "public_base_url": _direct_setting("public_base_url") or public_base_url(),
    }
    return render_template("admin_telegram.html", status=status, telegram_settings=telegram_settings)


@app.get("/admin/mailtm")
@login_required
@admin_required
def admin_mailtm():
    diag = {"base": cfg(["MAILTM_BASE", "MAIL_TM_BASE"], "mailtm_base", MAILTM_BASE)}
    try:
        raw = mailtm_request("GET", "/domains")
        domains = _mailtm_domains()
        diag.update({"ok": True, "domains_count": len(domains), "sample_domains": domains[:6], "raw_type": type(raw).__name__})
    except Exception as exc:
        diag.update({"ok": False, "error": str(exc)})
    return render_template("admin_mailtm.html", diag=diag)


@app.get("/admin/settings")
@login_required
@admin_required
def admin_settings():
    rows = db().execute("SELECT * FROM settings ORDER BY key").fetchall()
    db_warning = "SQLite file is inside the app instance folder. Use persistent disk/external DB on Render."
    return render_template("admin_settings.html", settings=rows, db_path=DB_PATH, db_warning=db_warning)

@app.post("/admin/settings")
@login_required
@admin_required
def admin_settings_post():
    for key, value in request.form.items():
        if key == "csrf_token": continue
        db().execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    db().commit()
    return redirect(url_for("admin_settings"))

@app.get("/admin/backup")
@login_required
@admin_required
def admin_backup():
    return render_template("admin_backup.html")

@app.get("/admin/backup.json")
@login_required
@admin_required
def admin_backup_json():
    data = {}
    for table in ["users", "mailboxes", "messages", "notifications", "payments", "plans", "settings"]:
        data[table] = [dict(r) for r in db().execute(f"SELECT * FROM {table}").fetchall()]
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(payload, mimetype="application/json", headers={"Content-Disposition": "attachment; filename=vemail_v42_backup.json"})

@app.errorhandler(403)
def forbidden(_e):
    return render_template("error.html", title="403", message="You do not have permission to open this page."), 403

@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", title="404", message="Page not found."), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

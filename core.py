"""Ortak yardımcılar: yapılandırma, veritabanı, para, güvenlik, doğrulama, dekoratörler."""
import hashlib
import hmac
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import abort, flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db as dbm

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "")
_admin_plain = os.getenv("ADMIN_PASSWORD", "")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "").strip()

if not (ADMIN_USERNAME and (ADMIN_PASSWORD_HASH or _admin_plain) and SECRET_KEY):
    raise RuntimeError(
        ".env dosyasında ADMIN_USERNAME, ADMIN_PASSWORD_HASH (veya ADMIN_PASSWORD) ve SECRET_KEY tanımlı olmalı. "
        "Örnek için .env.example dosyasına bak."
    )

# Yönetici şifresi bellekte de düz metin tutulmaz: .env'de düz metin varsa açılışta hash'lenir (kalıcı çözüm:
# `python manage.py hash-admin`, .env'ye ADMIN_PASSWORD_HASH yazar ve düz metni siler).
ADMIN_PASSWORD_IS_PLAINTEXT = not ADMIN_PASSWORD_HASH
ADMIN_PASSWORD_LENGTH = len(_admin_plain)
# Yönetici oturumları bu parmak izine bağlanır: .env'de yönetici şifresi/adı değişirse eski oturumlar düşer
# (düz metin şifrede hash her açılışta farklı tuzlandığı için parmak izi düz metinden/.env'deki değerden türetilir).
ADMIN_PW_FP = hashlib.sha256(("apw|" + ADMIN_USERNAME + "|" + (ADMIN_PASSWORD_HASH or _admin_plain)).encode()).hexdigest()[:16]
if ADMIN_PASSWORD_IS_PLAINTEXT:
    ADMIN_PASSWORD_HASH = generate_password_hash(_admin_plain)
_admin_plain = ""
os.environ.pop("ADMIN_PASSWORD", None)


def verify_admin_password(password):
    return check_password_hash(ADMIN_PASSWORD_HASH, password or "")

DB_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/epin.db")
# Vercel (VERCEL=1 otomatik tanımlı) ya da SERVERLESS=1: kalıcı disk, arka plan iş parçacığı ve yazılabilir dosya sistemi yok
ON_VERCEL = bool(os.getenv("VERCEL"))
SERVERLESS = ON_VERCEL or os.getenv("SERVERLESS", "0") == "1"
if ON_VERCEL and not dbm.remote():
    raise RuntimeError(
        "Vercel'de TURSO_DATABASE_URL ve TURSO_AUTH_TOKEN ortam degiskenleri tanimli olmali "
        "(yerel SQLite dosyasi Vercel'de kalici degildir). README: 'Vercel'e yayinlama'."
    )

TR_OFFSET = timedelta(hours=3)  # Türkiye sabit UTC+3
ADMIN_SESSION_SECONDS = 8 * 3600  # admin oturumu 8 saat sonra düşer


class BizError(Exception):
    """Kullanıcıya gösterilecek iş kuralı hatası."""


# --------------------------------------------------------------------------- veritabanı
def get_db():
    if "db" not in g:
        g.db = dbm.connect(DB_PATH)
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def q(sql, args=()):
    return get_db().execute(sql, args).fetchall()


def q1(sql, args=()):
    return get_db().execute(sql, args).fetchone()


def ex(sql, args=()):
    return get_db().execute(sql, args)


def tx():
    return dbm.tx(get_db())


# --------------------------------------------------------------------------- ayarlar
def settings():
    if "settings" not in g:
        g.settings = {r["key"]: r["value"] for r in q("SELECT key, value FROM settings")}
    return g.settings


SECRET_SETTINGS = set()          # gizli tutulacak ayar anahtarları (şu an yok)
# Dış sistemlerin çerezsiz POST edebildiği yollar (CSRF dışı, kendi imzasıyla doğrulanır); şu an yok
EXTERNAL_POST_PATHS = set()


def public_settings():
    """Şablonlara verilen ayarlar: gizli anahtarlar hariç."""
    return {k: v for k, v in settings().items() if k not in SECRET_SETTINGS and not k.startswith(("admin_2fa_", "admin_sec_"))}


def setting(key, default=""):
    return settings().get(key, default)


def setting_kurus(key, default=0):
    v = to_kurus(setting(key, ""))
    return default if v is None else v


def setting_pct(key, default="0"):
    try:
        v = Decimal(setting(key, default).replace(",", "."))
    except InvalidOperation:
        v = Decimal(default)
    return min(max(v, Decimal(0)), Decimal(100))


def setting_int(key, default):
    try:
        return int(setting(key, str(default)))
    except ValueError:
        return default


# --------------------------------------------------------------------------- para
MAX_MONEY_TL = Decimal(10_000_000)     # tek bir tutar alanı için üst sınır


def to_kurus(text):
    """'1.234,56' / '100' / '12.5' -> kuruş (int). Geçersizse None."""
    s = str(text or "").strip().replace(" ", "").replace("₺", "").replace("TL", "")
    if not s or len(s) > 20 or not re.fullmatch(r"[0-9.,]+", s):      # bilimsel gösterim (1e9), işaret, harf yok
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    if not d.is_finite() or d > MAX_MONEY_TL:
        return None
    return int((d * 100).to_integral_value(rounding=ROUND_HALF_UP))


def fmt_money(kurus):
    kurus = int(kurus or 0)
    sign = "-" if kurus < 0 else ""
    tl, kr = divmod(abs(kurus), 100)
    return f"{sign}{tl:,}".replace(",", ".") + f",{kr:02d} ₺"


def fmt_signed(kurus):
    """Bakiye hareketi için işaretli tutar: +250,00 ₺ / -40,00 ₺."""
    kurus = int(kurus or 0)
    return ("+" if kurus > 0 else "") + fmt_money(kurus)


def fmt_plain(kurus):
    """Form alanlarına yazılacak düz değer: 1050 -> '10,50'."""
    tl, kr = divmod(int(kurus or 0), 100)
    return f"{tl},{kr:02d}"


def pct_of(amount, pct):
    return int((Decimal(int(amount)) * Decimal(pct) / 100).to_integral_value(rounding=ROUND_HALF_UP))


def change_balance(user_id, delta, kind, description, ref_type=None, ref_id=None):
    """Bakiyeyi değiştirir ve defter kaydı atar. Mutlaka tx() içinde çağır."""
    ex("UPDATE users SET balance = balance + ? WHERE id = ?", (delta, user_id))
    bal = q1("SELECT balance FROM users WHERE id = ?", (user_id,))["balance"]
    ex(
        "INSERT INTO transactions(user_id, kind, amount, balance_after, description, ref_type, ref_id)"
        " VALUES (?,?,?,?,?,?,?)",
        (user_id, kind, delta, bal, description, ref_type, ref_id),
    )
    return bal


def withdrawable(user_id):
    """Çekilebilir tutar: yalnızca satış kazançları (ve yöneticinin 'kazanç' olarak eklediği tutarlar).

    Bakiye yükleme alışveriş içindir; kart/havale ile yüklenen para çekilemez (dolandırıcılık ve
    kara para aklama riskini azaltır). Admin panelinden 'withdraw_only_earnings' = 0 yapılabilir.
    """
    earned = q1(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM transactions WHERE user_id = ? AND kind IN ('sale', 'bonus')",
        (user_id,),
    )["s"]
    used = q1(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM transactions WHERE user_id = ? AND kind IN ('withdraw', 'withdraw_refund')",
        (user_id,),
    )["s"]
    bal = q1("SELECT balance FROM users WHERE id = ?", (user_id,))["balance"]
    return max(min(bal, earned + used), 0)


# --------------------------------------------------------------------------- zaman
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fmt_dt(value, with_time=True):
    if not value:
        return "-"
    try:
        d = datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S") + TR_OFFSET
    except ValueError:
        return str(value)
    return d.strftime("%d.%m.%Y %H:%M" if with_time else "%d.%m.%Y")


def time_ago(value):
    """'3 dk önce', '2 sa önce', '5 gün önce' ..."""
    if not value:
        return "-"
    try:
        d = datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return str(value)
    sec = int((utcnow() - d).total_seconds())
    if sec < 45:
        return "az önce"
    if sec < 3600:
        return f"{sec // 60 or 1} dk önce"
    if sec < 86400:
        return f"{sec // 3600} sa önce"
    if sec < 86400 * 30:
        return f"{sec // 86400} gün önce"
    return fmt_dt(value, False)


def seconds_to_midnight():
    """Türkiye saatiyle gece yarısına kalan saniye (günün fırsatları geri sayımı)."""
    now = utcnow() + TR_OFFSET
    nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((nxt - now).total_seconds())


def client_ip():
    return (request.remote_addr or "")[:45]


def utc_str(dt=None):
    return (dt or utcnow()).strftime("%Y-%m-%d %H:%M:%S")


def local_to_utc(text):
    """<input type=datetime-local> (Türkiye saati) -> veritabanı için UTC metni; boşsa None."""
    text = (text or "").strip().replace("T", " ")
    if not text:
        return None
    for f in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return utc_str(datetime.strptime(text, f) - TR_OFFSET)
        except ValueError:
            continue
    return None


def utc_to_local_input(value):
    if not value:
        return ""
    try:
        return (datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S") + TR_OFFSET).strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return ""


def daily_series(sql, args=(), days=14):
    """sql, (d = 'YYYY-MM-DD' Türkiye günü, v = sayı) döndürmeli. Boş günler 0 ile doldurulur."""
    data = {r["d"]: r["v"] or 0 for r in q(sql, args)}
    today = (utcnow() + TR_OFFSET).date()
    out = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        out.append({"label": day.strftime("%d.%m"), "value": data.get(day.isoformat(), 0)})
    peak = max((x["value"] for x in out), default=0) or 1
    for x in out:
        x["pct"] = max(int(x["value"] * 100 / peak), 3) if x["value"] else 0
    return out


# --------------------------------------------------------------------------- güvenlik
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def check_csrf():
    sent = request.form.get("csrf_token", "")
    real = session.get("_csrf", "")
    if not sent or not real or not hmac.compare_digest(sent, real):
        abort(400, "Güvenlik doğrulaması başarısız. Sayfayı yenileyip tekrar dene.")


_NEXT_OK = re.compile(r"^/(?!/)[A-Za-z0-9_\-./?=&%~+:,@!$*;()#]*$")


def safe_next(target):
    """Yalnızca site içi yollar: '//', '\\', boşluk/sekme/satır sonu gibi tarayıcının yok saydığı karakterler reddedilir."""
    if target and len(target) <= 300 and _NEXT_OK.match(target):
        return target
    return None


def _rl_key(key):
    return (key if key is not None else (request.remote_addr or "?"))[:80]


def is_limited(scope, limit=8, window=600, key=None):
    """Son `window` saniyede `limit` veya daha fazla kayıtlı deneme var mı? (SQLite: yeniden başlatmada ve
    çoklu işlemde de geçerli)"""
    n = q1("SELECT COUNT(*) AS c FROM rate_hits WHERE scope = ? AND key = ? AND ts > ?", (scope, _rl_key(key), time.time() - window))["c"]
    return n >= limit


def record_attempt(scope, key=None):
    now = time.time()
    ex("INSERT INTO rate_hits(scope, key, ts) VALUES (?,?,?)", (scope, _rl_key(key), now))
    if secrets.randbelow(100) == 0:                                   # ara sıra eski kayıtları süpür
        ex("DELETE FROM rate_hits WHERE ts < ?", (now - 86400,))


def clear_attempts(scope, key=None):
    ex("DELETE FROM rate_hits WHERE scope = ? AND key = ?", (scope, _rl_key(key)))


def rate_hit(scope, limit, window, key=None):
    """Sayar ve sınır aşıldıysa True döner (genel amaçlı hız sınırı)."""
    if is_limited(scope, limit, window, key):
        return True
    record_attempt(scope, key)
    return False


def ident_key(text):
    """Kullanıcı adı/e-posta için (hesap başına) sınır anahtarı; ham değer saklanmaz."""
    return "i:" + hashlib.sha256((text or "").strip().lower().encode()).hexdigest()[:20]


def log_admin(action, detail=""):
    ex("INSERT INTO admin_log(action, detail, ip) VALUES (?,?,?)", (action, detail, request.remote_addr or ""))


# --------------------------------------------------------------------------- doğrulama
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")


COMMON_PASSWORDS = {
    "12345678", "123456789", "1234567890", "password", "password1", "qwerty123", "11111111", "00000000", "iloveyou",
    "abc12345", "sifre123", "sifre1234", "parola123", "12341234", "qwertyui", "asdfghjk", "istanbul", "galatasaray",
    "fenerbahce", "besiktas", "trabzonspor", "admin123", "admin1234", "letmein1", "welcome1", "itemal123",
}


def weak_password(password, username="", email=""):
    """Zayıf/uygunsuz şifre için Türkçe uyarı, uygunsa None. Üst sınır: hash işlemiyle hizmet dışı bırakmayı önler."""
    if not 8 <= len(password) <= 128:
        return "Şifre 8 ile 128 karakter arasında olmalı."
    low = password.lower()
    if low in COMMON_PASSWORDS or len(set(password)) < 4:
        return "Bu şifre çok kolay tahmin edilir. Daha özgün bir şifre seç."
    if username and low == username.lower():
        return "Şifre kullanıcı adınla aynı olamaz."
    if email and low == email.lower().split("@")[0]:
        return "Şifre e-posta adresinle aynı olamaz."
    # kullanıcı adını ya da e-postanın yerel kısmını içeren şifreler kolay tahmin edilir
    if username and len(username) >= 3 and username.lower() in low:
        return "Şifre kullanıcı adını içeremez."
    local = email.lower().split("@")[0] if email else ""
    if len(local) >= 4 and local in low:
        return "Şifre e-posta adresinin ilk kısmını içeremez."
    return None


def needs_rehash(password_hash):
    """Eski/zayıf parametreli hash'leri girişte yükseltmek için (varsayılan: scrypt n=32768,r=8,p=1)."""
    return not (password_hash or "").startswith("scrypt:32768:8:1$")


def field(name, maxlen=200):
    return (request.form.get(name) or "").strip()[:maxlen]


def valid_tc(no):
    """T.C. kimlik numarası algoritma doğrulaması."""
    if not re.fullmatch(r"[1-9]\d{10}", no or ""):
        return False
    d = [int(c) for c in no]
    if ((sum(d[0:9:2]) * 7) - sum(d[1:8:2])) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def parse_codes(text, max_lines=2000, max_len=300):
    seen, out = set(), []
    for line in (text or "").splitlines():
        code = line.strip()
        if not code or code in seen:
            continue
        if len(code) > max_len:
            raise BizError(f"Bir kod {max_len} karakterden uzun olamaz.")
        seen.add(code)
        out.append(code)
    if len(out) > max_lines:
        raise BizError(f"Tek seferde en fazla {max_lines} kod eklenebilir.")
    return out


def delete_upload(name):
    import storage

    storage.delete("kyc", Path(name).name)


# --------------------------------------------------------------------------- sorgular / sayfalama
LISTING_SELECT = """
SELECT l.*, c.name AS cat_name, c.slug AS cat_slug, c.color AS cat_color,
       u.username AS seller_name, u.avatar AS seller_avatar, u.kyc_status AS seller_kyc,
       COALESCE(NULLIF(u.store_name, ''), u.username) AS seller_display,
       (SELECT COALESCE(MAX(sp.tick), 0) FROM user_packages up JOIN store_packages sp ON sp.id = up.package_id
         WHERE up.user_id = l.seller_id AND up.starts_at <= datetime('now') AND (up.ends_at IS NULL OR up.ends_at > datetime('now'))) AS seller_tick,
       (SELECT CASE COALESCE(MAX(CASE sp.tier WHEN 'diamond' THEN 2 WHEN 'gold' THEN 1 ELSE 0 END), 0) WHEN 2 THEN 'diamond' WHEN 1 THEN 'gold' ELSE '' END
          FROM user_packages up JOIN store_packages sp ON sp.id = up.package_id
         WHERE up.user_id = l.seller_id AND up.starts_at <= datetime('now') AND (up.ends_at IS NULL OR up.ends_at > datetime('now'))) AS seller_tier,
       (SELECT COUNT(*) FROM listing_codes k WHERE k.listing_id = l.id AND k.is_sold = 0) AS stock
FROM listings l
JOIN categories c ON c.id = l.category_id
JOIN users u ON u.id = l.seller_id
"""


def paginate(sql, args=(), per_page=15):
    page = request.args.get("page", 1, type=int) or 1
    page = max(page, 1)
    total = q1(f"SELECT COUNT(*) AS c FROM ({sql})", args)["c"]
    pages = max((total + per_page - 1) // per_page, 1)
    page = min(page, pages)
    rows = q(f"{sql} LIMIT ? OFFSET ?", (*args, per_page, (page - 1) * per_page))
    return {"rows": rows, "page": page, "pages": pages, "total": total}


def page_url(n):
    args = request.args.to_dict(flat=True)
    args["page"] = n
    return url_for(request.endpoint, **(request.view_args or {}), **args)


def can_sell(user):
    if not user or user["is_banned"]:
        return False
    if setting("require_seller_approval", "1") == "1":
        return bool(user["is_seller"])
    return True


# --------------------------------------------------------------------------- dekoratörler
def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not g.user:
            flash("Devam etmek için giriş yapmalısın.", "warn")
            return redirect(url_for("login", next=request.full_path.rstrip("?")))
        return view(*a, **kw)

    return wrapped


def seller_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not g.user:
            flash("Devam etmek için giriş yapmalısın.", "warn")
            return redirect(url_for("login", next=request.path))
        if not can_sell(g.user):
            flash("Satıcı paneli için önce satıcı başvurunun onaylanması gerekiyor.", "warn")
            return redirect(url_for("seller_apply"))
        return view(*a, **kw)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("admin") or time.time() - session.get("admin_at", 0) > ADMIN_SESSION_SECONDS:
            session.pop("admin", None)
            return redirect(url_for("admin.login", next=request.path))
        return view(*a, **kw)

    return wrapped

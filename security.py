"""Güvenlik katmanı: çerez, CORS, istek sınırları, girdi temizliği, log maskeleme, sır şifreleme.

app.py içinde `security.install(app)` ile tek yerden bağlanır.
"""
import base64
import hashlib
import logging
import os
import re
import time
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken
from flask import Request, abort, g, jsonify, request, session
from flask.sessions import SecureCookieSessionInterface
from werkzeug.datastructures import ImmutableMultiDict

import core

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

# --------------------------------------------------------------------------- girdi temizliği
# NUL ve kontrol karakterleri, çift yönlü metin (bidi) gizleme karakterleri, sıfır genişlikli karakterler
_BAD_CHARS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f‪-‮⁦-⁩​-‍⁠﻿]")
MAX_FIELD_LEN = 20_000       # tek bir form alanı için üst sınır
FIELD_LIMITS = {"codes": 700_000}   # toplu e-pin kodu alanı: 2000 kod x 300 karakter
MAX_FIELDS = 400


def clean_text(value):
    return _BAD_CHARS.sub("", value)


class SafeRequest(Request):
    """Form alanlarını okurken kontrol karakterlerini atar; aşırı uzun/çok alanlı istekleri reddeder."""

    max_form_parts = MAX_FIELDS

    def _load_form_data(self):
        super()._load_form_data()
        form = self.__dict__.get("form")
        if form is None:
            return
        items = []
        for key, value in form.items(multi=True):
            if len(value) > FIELD_LIMITS.get(key, MAX_FIELD_LEN) or len(key) > 100:
                abort(413)
            items.append((clean_text(key), clean_text(value)))
        if len(items) > MAX_FIELDS:
            abort(413)
        self.__dict__["form"] = ImmutableMultiDict(items)


# --------------------------------------------------------------------------- çerez
class HardenedSession(SecureCookieSessionInterface):
    """HttpOnly + SameSite=Lax; HTTPS altında Secure ve `__Host-` önekli çerez (alt alan adına sızmaz)."""

    def _secure(self, app):
        mode = app.config.get("COOKIE_SECURE_MODE", "auto")
        if mode == "1":
            return True
        if mode == "0":
            return False
        return request.is_secure

    def get_cookie_secure(self, app):
        return self._secure(app)

    def get_cookie_name(self, app):
        return "__Host-itm" if self._secure(app) else "itm"

    def get_cookie_domain(self, app):
        return None            # __Host- öneki Domain özniteliğini yasaklar

    def get_cookie_path(self, app):
        return "/"


def session_fingerprint(password_hash):
    return hashlib.sha256(("pw|" + (password_hash or "")).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- log maskeleme
_REDACT = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1[gizli]"),
    (re.compile(r"itm_[A-Za-z0-9_-]{16,}"), "itm_[gizli]"),
    (re.compile(r"(?i)\b(token|api_key|apikey|key|secret|signature|sig|password|passwd|pwd|csrf_token|session|cookie|code|hash|res)=([^&\s\"']+)"), r"\1=[gizli]"),
    (re.compile(r"(?i)(set-cookie|cookie|authorization|x-api-key)\s*:\s*[^\r\n]+"), r"\1: [gizli]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_.-]{10,}"), "[gizli]"),      # JWT / imzalı oturum değerleri
    (re.compile(r"[A-Za-z0-9_+/=-]{40,}"), "[gizli]"),                            # uzun rastgele değerler
]


def redact(text):
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


def install_log_redaction():
    """Tüm log kayıtları (werkzeug erişim günlüğü dahil) yazılmadan önce token/anahtar/imza içerenleri maskeler."""
    if getattr(logging, "_itm_redaction", False):
        return
    previous = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        try:
            msg = record.getMessage()
            masked = redact(msg)
            if masked != msg:
                record.msg, record.args = masked, ()
        except Exception:   # log maskeleme uygulamayı asla düşürmemeli
            pass
        return record

    logging.setLogRecordFactory(factory)
    logging._itm_redaction = True


def mask_ident(text):
    """Başarısız girişte yazılan kullanıcı adı alanı yanlışlıkla şifre olabilir: yalnızca baş harfler ve uzunluk loglanır."""
    text = text or ""
    return f"{text[:2]}*** ({len(text)} karakter)"


# --------------------------------------------------------------------------- veritabanındaki sırların şifrelenmesi
_PREFIX = "enc1:"


def _fernet():
    digest = hashlib.sha256(b"itemal-secretbox-v1|" + core.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plain):
    plain = plain or ""
    if not plain or plain.startswith(_PREFIX):
        return plain
    return _PREFIX + _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(stored):
    """Şifreli değeri çözer. Eski (düz) kayıtlar olduğu gibi döner; SECRET_KEY değiştiyse boş döner."""
    stored = stored or ""
    if not stored.startswith(_PREFIX):
        return stored
    try:
        return _fernet().decrypt(stored[len(_PREFIX):].encode()).decode()
    except (InvalidToken, ValueError):
        return ""


def migrate_secrets(conn):
    """Düz metin kayıtlı gizli ayarları (SECRET_SETTINGS) şifreli hale getirir; tekrar çalıştırılabilir."""
    for key in sorted(core.SECRET_SETTINGS):
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row and row[0] and not row[0].startswith(_PREFIX):
            conn.execute("UPDATE settings SET value = ? WHERE key = ?", (encrypt_secret(row[0]), key))


def lock_down_files(base_dir, db_path):
    """Sırların ve kimlik görsellerinin bulunduğu dosya/klasörleri yalnızca sahibine açar (POSIX)."""
    try:
        for path, mode in ((base_dir / ".env", 0o600), (db_path.parent, 0o700), (db_path, 0o600), (base_dir / "uploads", 0o700)):
            if path.exists():
                os.chmod(path, mode)
    except OSError:
        pass                              # Windows / izin yok: sessizce geç


# --------------------------------------------------------------------------- istek sınırları
UPLOAD_LIMITS = {                      # multipart kabul eden uç noktalar -> en fazla gövde boyutu
    "kyc": 28 * 1024 * 1024,
    "profile": 6 * 1024 * 1024,
    "seller.listing_new": 8 * 1024 * 1024,
    "seller.listing_edit": 8 * 1024 * 1024,
    "seller.store": 14 * 1024 * 1024,
    "admin.listing_new": 8 * 1024 * 1024,
    "admin.listing_edit": 8 * 1024 * 1024,
    "admin.categories": 8 * 1024 * 1024,
    "admin.category_posters": 30 * 1024 * 1024,
    "admin.banners": 8 * 1024 * 1024,
    "admin.banner_edit": 8 * 1024 * 1024,
}
SERVERLESS_BODY_LIMIT = 4_300_000      # Vercel işlevleri 4,5 MB'tan büyük gövdeyi kabul etmez; tarayıcı görselleri önceden küçültür
if core.SERVERLESS:
    UPLOAD_LIMITS = {k: min(v, SERVERLESS_BODY_LIMIT) for k, v in UPLOAD_LIMITS.items()}
TEXT_BODY_LIMIT = 1024 * 1024          # yükleme olmayan formlar / JSON
MAX_FILES_PER_REQUEST = 30


def _global_write_limit():
    return int(os.getenv("RATE_GLOBAL_WRITES", "240"))          # IP başına dakikada yazma isteği


def _guard_request():
    """Her istekten önce: Origin denetimi, gövde boyutu, dosya sayısı, genel yazma sınırı."""
    method = request.method
    if method in SAFE_METHODS:
        return None
    path = request.path
    ep = request.endpoint or ""

    # 1) Tarayıcıdan gelen çapraz site yazma istekleri (CSRF'in ikinci hattı). API hariç.
    if not (path.startswith("/api/") or path in core.EXTERNAL_POST_PATHS):
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            abort(403)
        origin = request.headers.get("Origin")
        if origin and origin != "null":
            if urlsplit(origin).netloc.lower() != request.host.lower() and origin.rstrip("/") not in trusted_origins():
                abort(403)
        elif origin == "null":
            abort(403)

    # 2) Gövde boyutu
    length = request.content_length
    if request.mimetype == "multipart/form-data":
        limit = UPLOAD_LIMITS.get(ep)
        if limit is None:
            abort(413)                                              # yükleme beklemeyen uçta multipart kabul edilmez
    else:
        limit = TEXT_BODY_LIMIT
    if length is not None and length > limit:
        abort(413)
    request.max_content_length = limit

    # 3) Genel yazma hızı (IP başına)
    if not path.startswith("/static/") and core.rate_hit("write", _global_write_limit(), 60):
        return _too_many()
    return None


def post_auth_checks():
    """Kullanıcı yüklendikten sonra: dosya sayısı ve yükleme hızı."""
    if request.method in SAFE_METHODS or request.mimetype != "multipart/form-data":
        return None
    files = request.files.getlist("posters") if request.endpoint == "admin.category_posters" else []
    if len(files) > MAX_FILES_PER_REQUEST or len(request.files) > MAX_FILES_PER_REQUEST:
        abort(413)
    if any(f and f.filename for f in request.files.values()):
        key = f"u{g.user['id']}" if g.get("user") else None
        if core.rate_hit("upload", 40, 3600, key=key):
            return _too_many()
    return None


def _too_many():
    if request.path.startswith("/api/") or request.headers.get("X-Requested-With") == "fetch":
        resp = jsonify({"ok": False, "error": "Çok fazla istek. Biraz bekleyip tekrar dene."})
    else:
        from flask import render_template
        return render_template("error.html", code=429, title="Çok fazla istek", message="Kısa sürede çok fazla işlem yaptın. Biraz bekleyip tekrar dene."), 429
    resp.status_code = 429
    resp.headers["Retry-After"] = "60"
    return resp


# --------------------------------------------------------------------------- CORS + güvenlik başlıkları
def allowed_origins():
    """CORS izin listesi (.env: CORS_ORIGINS=https://a.example,https://b.example). Varsayılan: boş = hiçbir dış site."""
    raw = os.getenv("CORS_ORIGINS", "")
    return {o.strip().rstrip("/") for o in raw.split(",") if o.strip()}


def trusted_origins():
    """Kendi sitenin genel adresi proxy arkasında farklı görünüyorsa .env: TRUSTED_ORIGINS=https://site.example"""
    raw = os.getenv("TRUSTED_ORIGINS", "")
    return {o.strip().rstrip("/") for o in raw.split(",") if o.strip()}


CSP = (
    "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
    "connect-src 'self'; font-src 'self'; media-src 'self'; object-src 'none'; frame-src 'none'; worker-src 'none'; "
    "manifest-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
)
PERMISSIONS = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"


def apply_headers(resp):
    h = resp.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("X-Frame-Options", "DENY")
    h.setdefault("Referrer-Policy", "same-origin")
    h.setdefault("Content-Security-Policy", CSP)
    h.setdefault("Permissions-Policy", PERMISSIONS)
    h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    h.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    h.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    if request.is_secure or os.getenv("COOKIE_SECURE") == "1":
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    # JSON yanıtlarında < > & karakterlerini \u escape'ine çevir (HTML olarak yorumlanma ihtimaline karşı ikinci savunma; geçerli JSON kalır)
    if resp.mimetype == "application/json" and not resp.direct_passthrough:
        body = resp.get_data()
        if b"<" in body or b">" in body or b"&" in body:
            resp.set_data(body.replace(b"<", b"\\u003c").replace(b">", b"\\u003e").replace(b"&", b"\\u0026"))
    # CORS: varsayılan kapalı. Yalnızca /api/ ve yalnızca .env'de listelenen kaynaklara açılır; çerez/kimlik bilgisi asla.
    for name in ("Access-Control-Allow-Origin", "Access-Control-Allow-Credentials"):
        h.pop(name, None)
    h.add("Vary", "Origin")
    origin = request.headers.get("Origin", "")
    if origin and request.path.startswith("/api/v1/") and origin.rstrip("/") in allowed_origins():
        h["Access-Control-Allow-Origin"] = origin
        h["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        h["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        h["Access-Control-Max-Age"] = "600"
    return resp


# --------------------------------------------------------------------------- kurulum
def install(app):
    app.request_class = SafeRequest
    app.session_interface = HardenedSession()
    app.config["COOKIE_SECURE_MODE"] = os.getenv("COOKIE_SECURE", "auto").strip().lower()
    app.config["MAX_FORM_MEMORY_SIZE"] = TEXT_BODY_LIMIT
    app.config["MAX_FORM_PARTS"] = MAX_FIELDS
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    install_log_redaction()
    app.before_request(_guard_request)          # app.py'deki _before'dan ÖNCE çalışmalı (gövde okunmadan boyut sınırı)
    app.after_request(apply_headers)

    @app.errorhandler(OverflowError)
    def _overflow(_e):
        from flask import render_template
        return render_template("error.html", code=400, title="İstek reddedildi", message="Geçersiz sayı değeri."), 400

    @app.errorhandler(429)
    def _e429(_e):
        return _too_many()

    return app

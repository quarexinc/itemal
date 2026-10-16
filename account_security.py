"""Üye (alıcı/satıcı) girişi ve hesap güvenliği.

- Form koruması: honeypot + imzalı form zaman damgası (1,5 sn'den hızlı / 30 dk'dan eski gönderim reddedilir)
- Giriş: CAPTCHA eşiği, IP bazlı kademeli kilit (15 dk -> 1 sa -> 24 sa), başarısız giriş özeti (login_failures)
- Yeni cihaz/IP uyarısı, güvenlik bildirimleri, "tüm cihazlardan çıkış" (users.sess_ver)
- İsteğe bağlı iki adımlı doğrulama (TOTP + yedek kodlar; totp.py)

app.py'de tek satır: account_security.install(app)   (captcha.install(app) de buradan çağrılır)
"""
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import time

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from markupsafe import Markup
from werkzeug.security import check_password_hash

import captcha
import core
import security
import services
import totp
from core import ex, field, q, q1

bp = Blueprint("accsec", __name__)

GENERIC_LOGIN_ERROR = "Kullanıcı adı/e-posta, şifre veya güvenlik doğrulaması hatalı. Kontrol edip tekrar dene."
CAPTCHA_AFTER = 3                      # IP'de ya da hesapta bu kadar hatalı denemeden sonra CAPTCHA zorunlu
LOCK_TIERS = (900, 3600, 86400)        # tekrarlayan IP kilidi: 15 dk, 1 sa, 24 sa
MIN_FORM_AGE = 1.5                     # sn: daha hızlı gönderilen form bot sayılır
MAX_FORM_AGE = 1800                    # sn: 30 dk'dan eski form geçersiz
PRE2FA_TTL = 300                       # parola doğru, ikinci adım bekleniyor (sn)
HONEYPOT = "hp_site"


# --------------------------------------------------------------------------- tarayıcı / IP özeti
def ua():
    return request.headers.get("User-Agent", "")[:160]


def ua_summary(agent):
    a = agent or ""
    if not a:
        return "Bilinmeyen tarayıcı"
    if "Edg/" in a or "EdgA/" in a or "EdgiOS" in a:
        b = "Edge"
    elif "OPR/" in a or "Opera" in a:
        b = "Opera"
    elif "Firefox/" in a or "FxiOS" in a:
        b = "Firefox"
    elif "Chrome/" in a or "CriOS" in a:
        b = "Chrome"
    elif "Safari/" in a:
        b = "Safari"
    else:
        b = "Diğer tarayıcı"
    if "Windows" in a:
        os_ = "Windows"
    elif "Android" in a:
        os_ = "Android"
    elif "iPhone" in a or "iPad" in a or "iPod" in a:
        os_ = "iOS"
    elif "Mac OS X" in a or "Macintosh" in a:
        os_ = "macOS"
    elif "CrOS" in a:
        os_ = "ChromeOS"
    elif "Linux" in a or "X11" in a:
        os_ = "Linux"
    else:
        os_ = "bilinmeyen sistem"
    return f"{b} ({os_})"


def ua_hash(agent):
    s = ua_summary(agent)
    if s.startswith("Diğer tarayıcı") or s.startswith("Bilinmeyen"):
        s += "|" + (agent or "")[:40]                      # tanınmayan istemcileri birbirinden ayır
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def ip_prefix(ip):
    """IPv4 için /24, IPv6 için /48 öneki (aynı ağdan farklı adres 'yeni' sayılmaz)."""
    try:
        addr = ipaddress.ip_address((ip or "").strip())
    except ValueError:
        return ip or ""
    if addr.version == 4:
        return ".".join(str(addr).split(".")[:3])
    return str(ipaddress.ip_network(f"{addr}/48", strict=False).network_address)


def mask_ip(ip):
    """***.***.12.4 (IPv4) / ****:****:...:abcd:1234 (IPv6)."""
    ip = (ip or "").strip()
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "***"
    if addr.version == 4:
        p = str(addr).split(".")
        return f"***.***.{p[2]}.{p[3]}"
    g_ = addr.exploded.split(":")
    return "****:****:****:****:****:****:" + ":".join(g_[-2:])


# --------------------------------------------------------------------------- form koruması: honeypot + imzalı zaman damgası
def _form_mac(scope, ts, nonce):
    msg = f"form|{scope}|{ts}|{nonce}|{core.csrf_token()}".encode()
    return hmac.new(core.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()[:24]


def form_token(scope, ts=None):
    ts = int(ts if ts is not None else time.time())
    nonce = secrets.token_hex(4)
    return f"{ts}.{nonce}.{_form_mac(scope, ts, nonce)}"


def form_guard(scope):
    """Şablon: gizli honeypot alanı + imzalı zaman damgası. Betik gerekmez."""
    return Markup(
        '<div class="hp" aria-hidden="true"><label for="{hp}-{s}">Bu alanı boş bırak</label>'
        '<input type="text" id="{hp}-{s}" name="{hp}" value="" tabindex="-1" autocomplete="off"></div>'
        '<input type="hidden" name="ft" value="{ft}">'
    ).format(hp=HONEYPOT, s=scope, ft=form_token(scope))


def check_form(scope):
    """Sorun yoksa None; aksi halde kısa neden kodu (honeypot / hizli / bayat / imza)."""
    if (request.form.get(HONEYPOT) or "").strip():
        return "honeypot"
    parts = (request.form.get("ft") or "").split(".")
    if len(parts) != 3 or not parts[0].isdigit() or len(parts[0]) > 12:
        return "imza"
    ts, nonce, mac = int(parts[0]), parts[1][:16], parts[2]
    if not hmac.compare_digest(mac, _form_mac(scope, ts, nonce)):
        return "imza"
    age = time.time() - ts
    if age < MIN_FORM_AGE:
        return "hizli"
    if age > MAX_FORM_AGE:
        return "bayat"
    return None


# --------------------------------------------------------------------------- sayaçlar, CAPTCHA eşiği, kademeli kilit
def _count(scope, key, window):
    return q1("SELECT COUNT(*) AS c FROM rate_hits WHERE scope = ? AND key = ? AND ts > ?", (scope, core._rl_key(key), time.time() - window))["c"]


def login_captcha_needed(ikey=None):
    if _count("login", None, 600) >= CAPTCHA_AFTER:
        return True
    return bool(ikey) and _count("login_acct", ikey, 900) >= CAPTCHA_AFTER


_STRIKES = tuple(f"login_strike{i}" for i in (1, 2, 3))


def ip_lock_left():
    """Bu IP için kademeli kilitten kalan saniye (0: kilit yok)."""
    now = time.time()
    left = 0
    rows = q(
        "SELECT scope, MAX(ts) AS ts FROM rate_hits WHERE scope IN (?,?,?) AND key = ? AND ts > ? GROUP BY scope",
        (*_STRIKES, core._rl_key(None), now - 86400),
    )
    for r in rows:
        level = int(r["scope"][-1])
        left = max(left, int(r["ts"] + LOCK_TIERS[level - 1] - now))
    return max(left, 0)


def lock_text(seconds):
    if seconds >= 3600:
        return f"{(seconds + 3599) // 3600} saat"
    return f"{max((seconds + 59) // 60, 1)} dakika"


def maybe_strike():
    """IP başına 10 dk'da 8 hatalı denemeye ulaşıldıysa kilit başlatır; her tekrarda süre uzar (15 dk, 1 sa, 24 sa)."""
    if core.is_limited("login") and not ip_lock_left():
        n = q1(
            "SELECT COUNT(*) AS c FROM rate_hits WHERE scope IN (?,?,?) AND key = ? AND ts > ?",
            (*_STRIKES, core._rl_key(None), time.time() - 86400),
        )["c"]
        core.record_attempt(_STRIKES[min(n, 2)])


def log_failure(reason, ident="", user=None):
    """Kalıcı özet: ham kullanıcı adı yazılmaz (yanlışlıkla şifre yazılmış olabilir)."""
    ex(
        "INSERT INTO login_failures(user_id, ident, ip, agent, reason) VALUES (?,?,?,?,?)",
        (user["id"] if user else None, security.mask_ident(ident), core.client_ip(), ua(), reason[:40]),
    )
    if secrets.randbelow(100) == 0:
        ex("DELETE FROM login_failures WHERE created_at < datetime('now', '-90 days')")


def bot_failure(reason, ident=""):
    """Honeypot / çok hızlı / bayat form / yanlış CAPTCHA: IP sayacına yazılır; hesabı ve tüm site sayacını etkilemez."""
    core.record_attempt("login")
    log_failure(reason, ident)
    maybe_strike()


def credential_failure(ident, ikey, user, reason):
    core.record_attempt("login")
    core.record_attempt("login_acct", key=ikey)
    core.record_attempt("login_all", key="*")
    log_failure(reason, ident, user)
    maybe_strike()


# --------------------------------------------------------------------------- bildirimler
def security_notice(uid, title, body):
    services.notify(uid, title, body, url_for("profile") + "#guvenlik")


def now_text():
    return core.fmt_dt(core.utc_str())


def is_new_device(uid, ip, agent):
    """Daha önce hiç giriş kaydı yoksa (ilk giriş) yeni sayılmaz; aksi halde (IP /24, tarayıcı) ikilisi görülmemişse yeni."""
    rows = q("SELECT ip, agent FROM login_events WHERE user_id = ? ORDER BY id DESC LIMIT 300", (uid,))
    if not rows:
        return False
    sig = (ip_prefix(ip), ua_hash(agent))
    return not any((ip_prefix(r["ip"]), ua_hash(r["agent"])) == sig for r in rows)


def notify_new_device(uid, ip, agent):
    security_notice(
        uid, "Yeni cihazdan giriş",
        f"Hesabına yeni bir cihazdan giriş yapıldı: {ua_summary(agent)}, IP {mask_ip(ip)}, {now_text()}. "
        "Sen değilsen şifreni değiştir ve diğer oturumları kapat.",
    )


def bump_sessions(uid, keep_current=True):
    """sess_ver'i artırır: tüm eski oturumlar düşer. Geçerli oturum yeni sürümle yenilenir."""
    ex("UPDATE users SET sess_ver = sess_ver + 1 WHERE id = ?", (uid,))
    ver = q1("SELECT sess_ver FROM users WHERE id = ?", (uid,))["sess_ver"]
    if keep_current:
        session["sv"] = ver
    return ver


# --------------------------------------------------------------------------- giriş tamamlama + ikinci adım
def finish_login(user, nxt, remember, ikey=None):
    ip, agent = core.client_ip(), ua()
    new_device = is_new_device(user["id"], ip, agent)
    session.clear()
    session["uid"] = user["id"]
    session["pv"] = security.session_fingerprint(user["password_hash"])
    session["sv"] = user["sess_ver"]
    session.permanent = bool(remember)
    core.clear_attempts("login")
    if ikey:
        core.clear_attempts("login_acct", key=ikey)
    ex("UPDATE users SET last_login = datetime('now'), last_ip = ? WHERE id = ?", (ip, user["id"]))
    ex("INSERT INTO login_events(user_id, ip, agent) VALUES (?,?,?)", (user["id"], ip, agent))
    if new_device:
        notify_new_device(user["id"], ip, agent)
    return redirect(core.safe_next(nxt) or url_for("account"))


def has_2fa(user):
    return bool(user and user["totp_secret"])


def start_2fa(user, nxt, remember, ikey):
    session.clear()
    session["pre2fa"] = {
        "u": user["id"], "pv": security.session_fingerprint(user["password_hash"]),
        "exp": int(time.time()) + PRE2FA_TTL, "nxt": nxt or "", "rm": 1 if remember else 0, "ik": ikey or "",
    }
    return redirect(url_for("accsec.login_2fa"))


def _pre2fa_user():
    pre = session.get("pre2fa")
    if not isinstance(pre, dict) or pre.get("exp", 0) < time.time():
        return None, None
    user = q1("SELECT * FROM users WHERE id = ?", (pre.get("u"),))
    if not user or user["is_banned"] or not has_2fa(user) or pre.get("pv") != security.session_fingerprint(user["password_hash"]):
        return None, None
    return pre, user


def _digits(code):
    return "".join(ch for ch in str(code or "") if ch.isalnum())


def consume_code(user, code):
    """TOTP ya da yedek kodu tüketir. Doğruysa 'totp' / 'yedek', değilse None. Aynı kod ikinci kez kabul edilmez."""
    raw = _digits(code)
    if len(raw) == totp.DIGITS and raw.isdigit():
        secret = security.decrypt_secret(user["totp_secret"])
        step = totp.verify(secret, raw, window=1, last_step=user["totp_last_step"]) if secret else None
        if step is not None:
            cur = ex("UPDATE users SET totp_last_step = ? WHERE id = ? AND totp_last_step < ?", (step, user["id"], step))
            return "totp" if cur.rowcount == 1 else None
        return None
    try:
        hashes = json.loads(user["totp_backup"] or "[]")
    except ValueError:
        hashes = []
    idx = totp.check_backup(code, hashes)
    if idx is None:
        return None
    rest = hashes[:idx] + hashes[idx + 1:]
    cur = ex("UPDATE users SET totp_backup = ? WHERE id = ? AND totp_backup = ?", (json.dumps(rest), user["id"], user["totp_backup"]))
    return "yedek" if cur.rowcount == 1 else None


@bp.route("/giris/dogrula", methods=["GET", "POST"])
def login_2fa():
    if g.user:
        return redirect(url_for("account"))
    pre, user = _pre2fa_user()
    if not pre:
        session.pop("pre2fa", None)
        flash("Doğrulama süresi doldu. Lütfen yeniden giriş yap.", "warn")
        return redirect(url_for("login"))
    ukey = f"u{user['id']}"
    if request.method == "POST":
        if ip_lock_left() or core.is_limited("login2fa", 5, 600) or core.is_limited("login2fa_acct", 5, 900, key=ukey):
            flash("Çok fazla hatalı deneme. Biraz bekleyip yeniden giriş yap.", "bad")
            return render_template("login_2fa.html"), 429
        how = consume_code(user, request.form.get("code"))
        if how:
            core.clear_attempts("login2fa")
            core.clear_attempts("login2fa_acct", key=ukey)
            if how == "yedek":
                left = len(json.loads(q1("SELECT totp_backup FROM users WHERE id = ?", (user["id"],))["totp_backup"] or "[]"))
                security_notice(user["id"], "Yedek kod kullanıldı", f"Girişte bir yedek kod kullanıldı. Kalan yedek kod: {left}. Bu sen değilsen şifreni değiştir.")
            return finish_login(user, pre.get("nxt"), pre.get("rm"), pre.get("ik"))
        core.record_attempt("login2fa")
        core.record_attempt("login2fa_acct", key=ukey)
        log_failure("2fa", user["username"], user)
        flash("Doğrulama kodu hatalı ya da kullanılmış. Yeni kodu girip tekrar dene.", "bad")
    return render_template("login_2fa.html")


# --------------------------------------------------------------------------- kayıt ön kontrolü
def register_precheck():
    """Honeypot + zaman damgası + CAPTCHA (her zaman) + deneme hızı. Hata varsa Türkçe mesaj, yoksa None."""
    if core.rate_hit("register_try", 20, 600):
        return "Çok fazla deneme yaptın. Birkaç dakika sonra tekrar dene."
    if check_form("register"):
        return "Kayıt tamamlanamadı. Formu kontrol edip tekrar dene."
    if not captcha.verify("register", request.form.get("captcha")):
        return "Güvenlik doğrulaması hatalı ya da süresi dolmuş. Resimdeki karakterleri yeniden yaz."
    return None


# --------------------------------------------------------------------------- açık formlarda kötüye kullanım -> CAPTCHA
def abuse_needs_captcha(scope, limit=3, window=900):
    """Giriş yapmış kullanıcı kısa sürede `limit` işlem yaptıysa sonraki için CAPTCHA istenir."""
    if not g.get("user"):
        return False
    return _count(f"abuse_{scope}", f"u{g.user['id']}", window) >= limit


def abuse_record(scope):
    if g.get("user"):
        core.record_attempt(f"abuse_{scope}", key=f"u{g.user['id']}")


# --------------------------------------------------------------------------- satıcı için zorunlu 2FA
def seller_2fa_gate():
    """seller._guard içinden: ayar açıksa 2FA'sız satıcı panele giremez, güvenlik sayfasına yönlenir."""
    u = g.get("user")
    if u and core.setting("require_seller_2fa", "0") == "1" and not has_2fa(u):
        flash("Satıcı paneli için iki adımlı doğrulamayı etkinleştirmen gerekiyor.", "warn")
        return redirect(url_for("accsec.twofa"))
    return None


# --------------------------------------------------------------------------- profil > güvenlik
def sec_summary():
    """profile.html güvenlik bölümü verileri."""
    u = g.get("user")
    if not u:
        return {}
    events = q("SELECT * FROM login_events WHERE user_id = ? ORDER BY id DESC LIMIT 10", (u["id"],))
    failed = q1("SELECT COUNT(*) AS c FROM login_failures WHERE user_id = ? AND created_at > datetime('now', '-1 day')", (u["id"],))["c"]
    try:
        backups = len(json.loads(u["totp_backup"] or "[]"))
    except ValueError:
        backups = 0
    return {"events": events, "failed_24h": failed, "twofa": has_2fa(u), "backups": backups, "now_ip": core.client_ip()}


@bp.post("/profil/tum-cikis")
@core.login_required
def logout_all():
    bump_sessions(g.user["id"])
    security_notice(g.user["id"], "Tüm cihazlardan çıkış yapıldı", f"{now_text()} tarihinde tüm cihazlardaki oturumların kapatıldı. Bu işlemi sen yapmadıysan şifreni hemen değiştir.")
    flash("Diğer tüm cihazlardaki oturumlar kapatıldı. Bu cihazdaki oturumun açık kaldı.", "ok")
    return redirect(url_for("profile") + "#guvenlik")


def _pending_secret():
    pend = session.get("totp_pending")
    if isinstance(pend, dict) and pend.get("exp", 0) > time.time():
        secret = security.decrypt_secret(pend.get("s", ""))
        if secret:
            return secret
    secret = totp.gen_secret()
    session["totp_pending"] = {"s": security.encrypt_secret(secret), "exp": int(time.time()) + 900}
    return secret


def _group(secret):
    return " ".join(secret[i:i + 4] for i in range(0, len(secret), 4))


def _twofa_view(**extra):
    u = g.user
    ctx = {"enabled": has_2fa(u), "backups": 0, "codes": None}
    if ctx["enabled"]:
        try:
            ctx["backups"] = len(json.loads(u["totp_backup"] or "[]"))
        except ValueError:
            pass
    else:
        secret = _pending_secret()
        uri = totp.otpauth_uri(secret, u["username"], issuer=core.setting("site_name", "itemal") or "itemal")
        svg = totp.qr_svg(uri)
        ctx.update(secret_text=_group(secret), qr=Markup(svg) if svg else "")
    ctx.update(extra)
    return render_template("profile_2fa.html", **ctx)


@bp.route("/profil/2fa", methods=["GET", "POST"])
@core.login_required
def twofa():
    u = g.user
    if request.method != "POST":
        return _twofa_view()
    action = request.form.get("action")
    ukey = f"u{u['id']}"
    if core.is_limited("sec2fa", 5, 900, key=ukey):
        flash("Çok fazla hatalı deneme. 15 dakika sonra tekrar dene.", "bad")
        return _twofa_view(), 429
    code = request.form.get("code", "")[:40]
    if action == "enable" and not has_2fa(u):
        pend = session.get("totp_pending")
        secret = security.decrypt_secret(pend.get("s", "")) if isinstance(pend, dict) and pend.get("exp", 0) > time.time() else ""
        step = totp.verify(secret, code, window=1) if secret else None
        if step is None:
            core.record_attempt("sec2fa", key=ukey)
            flash("Kod hatalı. Uygulamadaki güncel 6 haneli kodu gir.", "bad")
            return _twofa_view()
        plain, hashes = totp.new_backup_codes(10)
        ex(
            "UPDATE users SET totp_secret = ?, totp_last_step = ?, totp_backup = ? WHERE id = ?",
            (security.encrypt_secret(secret), step, json.dumps(hashes), u["id"]),
        )
        session.pop("totp_pending", None)
        security_notice(u["id"], "İki adımlı doğrulama açıldı", f"{now_text()} tarihinde hesabına iki adımlı doğrulama eklendi. Bu işlemi sen yapmadıysan şifreni değiştirip destekle iletişime geç.")
        g.user = q1("SELECT * FROM users WHERE id = ?", (u["id"],))
        flash("İki adımlı doğrulama etkinleştirildi.", "ok")
        return _twofa_view(codes=plain)
    if action in ("disable", "regen") and has_2fa(u):
        password = request.form.get("password", "")[:256]
        if not check_password_hash(u["password_hash"], password):
            core.record_attempt("sec2fa", key=ukey)
            flash("Şifre hatalı.", "bad")
            return _twofa_view()
        how = consume_code(u, code) if action == "disable" else ("totp" if _digits(code).isdigit() and consume_code(u, code) == "totp" else None)
        if not how:
            core.record_attempt("sec2fa", key=ukey)
            flash("Doğrulama kodu hatalı." if action == "disable" else "Yedek kodları yenilemek için uygulamadaki 6 haneli kodu gir.", "bad")
            return _twofa_view()
        if action == "disable":
            ex("UPDATE users SET totp_secret = '', totp_last_step = 0, totp_backup = '' WHERE id = ?", (u["id"],))
            security_notice(u["id"], "İki adımlı doğrulama kapatıldı", f"{now_text()} tarihinde iki adımlı doğrulama kapatıldı. Bu işlemi sen yapmadıysan şifreni hemen değiştir.")
            g.user = q1("SELECT * FROM users WHERE id = ?", (u["id"],))
            flash("İki adımlı doğrulama kapatıldı.", "info")
            return redirect(url_for("profile") + "#guvenlik")
        plain, hashes = totp.new_backup_codes(10)
        ex("UPDATE users SET totp_backup = ? WHERE id = ?", (json.dumps(hashes), u["id"]))
        security_notice(u["id"], "Yedek kodlar yenilendi", f"{now_text()} tarihinde yedek kodların yenilendi; eskileri geçersiz.")
        g.user = q1("SELECT * FROM users WHERE id = ?", (u["id"],))
        flash("Yeni yedek kodlar oluşturuldu. Eskileri artık geçersiz.", "ok")
        return _twofa_view(codes=plain)
    return redirect(url_for("accsec.twofa"))


def after_password_change(uid):
    """Şifre değişince: diğer oturumlar düşer (sess_ver) ve güvenlik bildirimi gider."""
    bump_sessions(uid)
    security_notice(uid, "Şifren değiştirildi", f"{now_text()} tarihinde hesap şifren değiştirildi ve diğer cihazlardaki oturumlar kapatıldı. Bu işlemi sen yapmadıysan hemen destek talebi aç.")


# --------------------------------------------------------------------------- kurulum
def install(app):
    captcha.install(app)
    if "accsec" not in app.blueprints:
        app.register_blueprint(bp)
    app.jinja_env.globals.update(form_guard=form_guard, sec_summary=sec_summary)
    app.jinja_env.filters.update(uasum=ua_summary, maskip=mask_ip)
    return app

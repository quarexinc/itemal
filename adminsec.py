"""Yönetici paneli güvenliği: oturum sertleştirme, IP izin listesi, kademeli kilit, iki adımlı doğrulama (TOTP),
giriş olayları, yeni cihaz uyarısı, form zaman damgası ve (ayrık) CAPTCHA.

Bağlantı: app.py içinde `adminsec.install(app)` (security.install'dan ÖNCE). Rotalar admin_auth.py içindedir.
Ortam değişkenleri:
  ADMIN_2FA           required (varsayılan) | optional | off (acil durum bayrağı)
  ADMIN_ALLOWED_IPS   virgülle IP/CIDR; tanımlıysa dışındakiler /admin/* için 404 alır
  ADMIN_URL_PREFIX    yönetim yolu (varsayılan /admin); açılışta okunur
  ADMIN_BIND_IP       1: oturum istemcinin /24 (IPv6: /48) ağına bağlanır
  ADMIN_FAIL_DELAY    başarısız girişte en az bekleme (sn, varsayılan 0.6; 0 = kapalı)
"""
import hashlib
import hmac
import ipaddress
import json
import math
import os
import random
import re
import secrets
import time

from flask import abort, flash, g, redirect, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

import core
import security
import totp

# --------------------------------------------------------------------------- yapılandırma
IDLE_SECONDS = 30 * 60            # bosta kalma (kayan)
PRE_SECONDS = 5 * 60              # parola doğru, 2. adım bekliyor
FORM_MIN_SECONDS = 1.5            # bundan hızlı gönderilen giriş formu reddedilir
FORM_MAX_SECONDS = 2 * 3600
LOCK_STEPS = (15 * 60, 60 * 60, 24 * 60 * 60)     # 1., 2., 3. ve sonraki kilitler
LOCK_AFTER = 5                    # kilit için hatalı giriş sayısı (15 dk içinde)
CAPTCHA_AFTER = 2                 # bu kadar hatadan sonra CAPTCHA zorunlu
TFA_IP_LIMIT = (5, 600)           # kod denemesi: IP başına 5 / 10 dk
TFA_ALL_LIMIT = (30, 3600)        # tüm site için 30 / saat
BACKUP_COUNT = 10
_RESERVED = {"static", "api", "satici", "hesabim", "giris", "kayit", "cikis", "media", "magaza", "ilan", "ilanlar", "captcha"}


def _clean_prefix():
    raw = (os.getenv("ADMIN_URL_PREFIX", "") or "/admin").strip().rstrip("/")
    if not raw.startswith("/"):
        raw = "/" + raw
    seg = r"[A-Za-z0-9][A-Za-z0-9_\-]{0,40}"
    if not re.fullmatch(f"/{seg}(/{seg}){{0,3}}", raw) or raw.split("/")[1].lower() in _RESERVED:
        raise RuntimeError("ADMIN_URL_PREFIX geçersiz: /ad biçiminde (harf, rakam, - ve _), en çok 4 bölüm olmalı ve site yollarıyla çakışmamalı.")
    return raw


URL_PREFIX = _clean_prefix()


def mode():
    v = (os.getenv("ADMIN_2FA", "required") or "required").strip().lower()
    return v if v in ("required", "optional", "off") else "required"


def bind_ip():
    return os.getenv("ADMIN_BIND_IP", "0").strip() == "1"


def _parse_nets(raw, strict_fail):
    nets = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            nets.append(ipaddress.ip_network(part, strict=False))
        except ValueError:
            if strict_fail:
                raise RuntimeError(f"ADMIN_ALLOWED_IPS içinde geçersiz IP/CIDR: {part!r}")
    return nets


_nets_cache = ("", [], False)


def allowed_nets():
    """(ağ listesi, tanımlı_mı). Tanımlı ama hiç geçerli giriş yoksa kimseye izin verilmez (güvenli kapanış)."""
    global _nets_cache
    raw = os.getenv("ADMIN_ALLOWED_IPS", "").strip()
    if _nets_cache[0] != raw:
        _nets_cache = (raw, _parse_nets(raw, False), bool(raw))
    return _nets_cache[1], _nets_cache[2]


def ip_allowed(ip=None):
    nets, defined = allowed_nets()
    if not defined:
        return True
    try:
        addr = ipaddress.ip_address(ip or core.client_ip())
    except ValueError:
        return False
    if addr.version == 6 and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return any(addr in n for n in nets)


# --------------------------------------------------------------------------- yardımcılar
def ua_string():
    return (request.headers.get("User-Agent") or "")[:300]


def ua_hash():
    return hashlib.sha256(ua_string().encode()).hexdigest()[:16]


def net_id(ip):
    try:
        addr = ipaddress.ip_address(ip)
        return str(ipaddress.ip_network(f"{ip}/{24 if addr.version == 4 else 48}", strict=False))
    except ValueError:
        return ip or ""


def mask_ip(ip):
    ip = ip or ""
    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:2]) + ":*"
    parts = ip.split(".")
    return ".".join(parts[:2]) + ".*.*" if len(parts) == 4 else ip[:6] + "*"


def browser_label(ua):
    ua = ua or ""
    low = ua.lower()
    if "edg/" in low:
        b = "Edge"
    elif "opr/" in low or "opera" in low:
        b = "Opera"
    elif "firefox/" in low:
        b = "Firefox"
    elif "chrome/" in low or "crios" in low:
        b = "Chrome"
    elif "safari/" in low:
        b = "Safari"
    elif low.startswith(("curl", "python", "go-http", "wget")):
        b = "Komut satırı aracı"
    else:
        b = "Bilinmeyen tarayıcı" if ua else "Tarayıcı bilgisi yok"
    for key, name in (("Windows", "Windows"), ("Android", "Android"), ("iPhone", "iOS"), ("iPad", "iOS"), ("Mac OS X", "macOS"), ("Linux", "Linux")):
        if key in ua:
            return f"{b} / {name}"
    return b


def is_admin_request():
    ep = request.endpoint or ""
    if ep.startswith("admin."):
        return True
    p = request.path
    return p == URL_PREFIX or p.startswith(URL_PREFIX + "/")


# --------------------------------------------------------------------------- ayar deposu (settings tablosu)
def _get(key):
    return core.settings().get(key, "")


def _put(key, value):
    core.ex("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    core.settings()[key] = value


def _del(*keys):
    for k in keys:
        core.ex("DELETE FROM settings WHERE key = ?", (k,))
        core.settings().pop(k, None)


# --------------------------------------------------------------------------- iki adımlı doğrulama (TOTP)
def tfa_enabled():
    """Kayıt var mı? (SECRET_KEY değişip çözülemese bile 'kurulu' sayılır: sessizce parola-only'e düşmez; çözüm: admin-2fa-reset)"""
    return bool(_get("admin_2fa_secret"))


def tfa_secret():
    return security.decrypt_secret(_get("admin_2fa_secret"))


def tfa_since():
    return _get("admin_2fa_since")


def backup_hashes():
    try:
        data = json.loads(security.decrypt_secret(_get("admin_2fa_backup")) or "[]")
        return [str(x) for x in data] if isinstance(data, list) else []
    except ValueError:
        return []


def backup_left():
    return len(backup_hashes())


def pending_secret():
    """Kurulum sırasındaki (henüz onaylanmamış) gizli anahtar; 15 dk geçerli, şifreli saklanır."""
    raw = security.decrypt_secret(_get("admin_2fa_pending"))
    if raw and "|" in raw:
        sec, ts = raw.split("|", 1)
        try:
            if time.time() - float(ts) < 900 and sec:
                return sec
        except ValueError:
            pass
    sec = totp.gen_secret()
    _put("admin_2fa_pending", security.encrypt_secret(f"{sec}|{time.time()}"))
    return sec


def enable_tfa(secret, step):
    """Gizli anahtarı kaydeder; 10 yedek kod üretir ve açık listeyi döner (bir daha gösterilmez)."""
    plain, hashes = totp.new_backup_codes(BACKUP_COUNT)
    with core.tx():
        _put("admin_2fa_secret", security.encrypt_secret(secret))
        _put("admin_2fa_step", str(int(step)))
        _put("admin_2fa_backup", security.encrypt_secret(json.dumps(hashes)))
        _put("admin_2fa_since", core.utc_str())
        _del("admin_2fa_pending")
    return plain


def regenerate_backup():
    plain, hashes = totp.new_backup_codes(BACKUP_COUNT)
    _put("admin_2fa_backup", security.encrypt_secret(json.dumps(hashes)))
    return plain


def disable_tfa():
    _del("admin_2fa_secret", "admin_2fa_step", "admin_2fa_backup", "admin_2fa_since", "admin_2fa_pending")


def commit_step(step):
    """Zaman adımını yalnızca ilerletir (aynı kodun eşzamanlı/yeniden kullanımı reddedilir). True = bu istek kazandı."""
    core.ex("INSERT OR IGNORE INTO settings(key, value) VALUES ('admin_2fa_step', '0')")
    cur = core.ex("UPDATE settings SET value = ? WHERE key = 'admin_2fa_step' AND CAST(value AS INTEGER) < ?", (str(int(step)), int(step)))
    core.settings()["admin_2fa_step"] = str(int(step))
    return cur.rowcount == 1


def check_totp(code):
    """Yalnızca TOTP kodu: kabul edilirse True (adım tüketilir)."""
    secret = tfa_secret()
    if not secret:
        return False
    try:
        last = int(_get("admin_2fa_step") or 0)
    except ValueError:
        last = 0
    step = totp.verify(secret, code, window=1, last_step=last)
    return step is not None and commit_step(step)


def check_second_factor(code):
    """6 haneli TOTP ya da yedek kod. 'totp' | 'backup' | None döner. Yedek kod tek kullanımlıktır."""
    code = (code or "").strip()
    if not tfa_enabled() or not code:
        return None
    digits = "".join(code.split())
    if digits.isdigit() and len(digits) == totp.DIGITS:
        return "totp" if check_totp(digits) else None
    stored = _get("admin_2fa_backup")
    hashes = backup_hashes()
    idx = totp.check_backup(code, hashes)
    if idx is None:
        return None
    rest = hashes[:idx] + hashes[idx + 1:]
    cur = core.ex("UPDATE settings SET value = ? WHERE key = 'admin_2fa_backup' AND value = ?", (security.encrypt_secret(json.dumps(rest)), stored))
    if cur.rowcount != 1:
        return None
    core.settings().pop("admin_2fa_backup", None)
    return "backup"


def tfa_limited():
    return core.is_limited("admin_2fa", *TFA_IP_LIMIT) or core.is_limited("admin_2fa_all", *TFA_ALL_LIMIT, key="*")


def tfa_hit():
    core.record_attempt("admin_2fa")
    core.record_attempt("admin_2fa_all", key="*")


def tfa_clear():
    core.clear_attempts("admin_2fa")


# --------------------------------------------------------------------------- kademeli kilit
def lock_remaining():
    row = core.q1("SELECT MAX(ts) AS t FROM rate_hits WHERE scope = 'admin_lock' AND key = ?", (core._rl_key(None),))
    until = (row["t"] or 0) if row else 0
    return max(0, int(math.ceil(until - time.time())))


def lock_message(seconds):
    if seconds >= 3600:
        span = f"{int(math.ceil(seconds / 3600))} saat"
    else:
        span = f"{max(1, int(math.ceil(seconds / 60)))} dakika"
    return f"Çok fazla başarısız deneme. {span} sonra tekrar dene."


def failures_now():
    return core.q1("SELECT COUNT(*) AS c FROM rate_hits WHERE scope = 'admin_login' AND key = ? AND ts > ?", (core._rl_key(None), time.time() - 900))["c"]


def site_limited():
    return core.is_limited("admin_login_all", 30, 3600, key="*")


def register_failure():
    """Başarısız girişi sayar. Eşik aşılırsa IP'yi kilitler ve kilit süresini (saniye) döner, değilse 0."""
    core.record_attempt("admin_login")
    core.record_attempt("admin_login_all", key="*")
    if failures_now() < LOCK_AFTER:
        return 0
    key = core._rl_key(None)
    level = core.q1("SELECT COUNT(*) AS c FROM rate_hits WHERE scope = 'admin_lockn' AND key = ? AND ts > ?", (key, time.time() - 86400))["c"]
    dur = LOCK_STEPS[min(level, len(LOCK_STEPS) - 1)]
    now = time.time()
    core.ex("INSERT INTO rate_hits(scope, key, ts) VALUES ('admin_lock', ?, ?)", (key, now + dur))
    core.ex("INSERT INTO rate_hits(scope, key, ts) VALUES ('admin_lockn', ?, ?)", (key, now))
    core.clear_attempts("admin_login")
    return dur


def clear_login_state():
    core.clear_attempts("admin_login")
    core.clear_attempts("admin_lockn")
    core.clear_attempts("admin_lock")


def fail_delay(start):
    """Başarısız girişlerde sabit taban + kısa rastgele gecikme (kullanıcı adı doğru/yanlış süre farkı sızdırmaz)."""
    try:
        base = float(os.getenv("ADMIN_FAIL_DELAY", "0.6"))
    except ValueError:
        base = 0.6
    if base <= 0:
        return
    rest = base + random.uniform(0, 0.25) - (time.monotonic() - start)
    if rest > 0:
        time.sleep(rest)


# --------------------------------------------------------------------------- giriş olayları ve yeni cihaz uyarısı
EVENT_LABELS = {
    "ok": ("Başarılı giriş", "ok"),
    "pw_ok": ("Parola doğru, 2. adım bekliyor", "warn"),
    "bad_login": ("Hatalı kullanıcı adı veya şifre", "bad"),
    "bad_captcha": ("Hatalı güvenlik kodu (CAPTCHA)", "bad"),
    "blocked_form": ("Form reddedildi (bot şüphesi)", "bad"),
    "locked": ("IP kilitlendi", "bad"),
    "bad_2fa": ("Hatalı iki adımlı kod", "bad"),
    "2fa_limit": ("Kod deneme sınırı aşıldı", "bad"),
}


def record_event(result, ident="", detail=""):
    core.ex(
        "INSERT INTO admin_login_events(ip, ua, ua_hash, ident, result, detail) VALUES (?,?,?,?,?,?)",
        (core.client_ip(), ua_string()[:200], ua_hash(), (ident or "")[:60], result, (detail or "")[:200]),
    )
    if secrets.randbelow(40) == 0:      # tablo şişmesin; başarılı girişler (yeni cihaz algısı için) ayrı korunur
        core.ex("DELETE FROM admin_login_events WHERE result != 'ok' AND id <= (SELECT MAX(id) FROM admin_login_events) - 2000")
        core.ex("DELETE FROM admin_login_events WHERE result = 'ok' AND id NOT IN (SELECT id FROM admin_login_events WHERE result = 'ok' ORDER BY id DESC LIMIT 500)")


def recent_events(limit=30):
    out = []
    for r in core.q("SELECT * FROM admin_login_events ORDER BY id DESC LIMIT ?", (limit,)):
        label, cls = EVENT_LABELS.get(r["result"], (r["result"], "muted"))
        out.append({
            "at": r["created_at"], "ip": mask_ip(r["ip"]), "browser": browser_label(r["ua"]),
            "label": label, "cls": cls, "detail": r["detail"], "ident": r["ident"],
        })
    return out


def detect_new_device():
    """Daha önce başarılı giriş varsa ve bu IP / tarayıcı hiç görülmediyse neden listesini döner."""
    ok_any = core.q1("SELECT 1 FROM admin_login_events WHERE result = 'ok' LIMIT 1")
    if not ok_any:
        return []
    why = []
    if not core.q1("SELECT 1 FROM admin_login_events WHERE result = 'ok' AND ip = ? LIMIT 1", (core.client_ip(),)):
        why.append("yeni IP")
    if not core.q1("SELECT 1 FROM admin_login_events WHERE result = 'ok' AND ua_hash = ? LIMIT 1", (ua_hash(),)):
        why.append("yeni tarayıcı")
    return why


def current_alert():
    raw = _get("admin_sec_alert")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except ValueError:
        return None


def raise_alert(why):
    data = {"at": core.utc_str(), "ip": mask_ip(core.client_ip()), "browser": browser_label(ua_string()), "why": " ve ".join(why)}
    _put("admin_sec_alert", json.dumps(data, ensure_ascii=False))
    core.log_admin("Yeni cihazdan yönetici girişi", f"{data['why']}: {data['ip']} / {data['browser']}")


def dismiss_alert():
    _del("admin_sec_alert")


# --------------------------------------------------------------------------- giriş formu: imzalı zaman damgası
def _ser():
    return URLSafeTimedSerializer(core.SECRET_KEY, salt="admin-login-form-v1")


def form_token():
    return _ser().dumps({"t": time.time()})


def check_form_token(token):
    """'ok' | 'fast' | 'expired' | 'bad'"""
    try:
        data = _ser().loads(token or "", max_age=FORM_MAX_SECONDS)
        age = time.time() - float(data["t"])
    except SignatureExpired:
        return "expired"
    except (BadSignature, KeyError, TypeError, ValueError):
        return "bad"
    return "fast" if age < FORM_MIN_SECONDS else "ok"


# --------------------------------------------------------------------------- CAPTCHA
# Ortak self-hosted captcha modülüne (captcha.py, kapsam "admin") ince sarmalayıcı. Modül yoksa CAPTCHA istenmez;
# diğer korumalar (kademeli kilit, honeypot, form zaman damgası, 2FA) CAPTCHA'dan bağımsız çalışır.
def _captcha_mod():
    try:
        import captcha

        return captcha
    except ImportError:
        return None


def captcha_required():
    """2 hatalı girişten sonra CAPTCHA zorunlu."""
    return failures_now() >= CAPTCHA_AFTER and _captcha_mod() is not None


def admin_captcha_ok(answer):
    mod = _captcha_mod()
    return True if mod is None else bool(mod.verify("admin", answer))


# --------------------------------------------------------------------------- oturum
ADMIN_KEYS = ("admin", "admin_at", "admin_seen", "admin_ua", "admin_net", "admin_pw", "admin_2fa")


def drop_admin():
    for k in ADMIN_KEYS:
        session.pop(k, None)


def start_session(via_2fa):
    """Tam yönetici oturumu: eski oturum tamamen silinir, yenisi açılır (oturum sabitleme yok)."""
    session.clear()
    now = int(time.time())
    session.update(admin=True, admin_at=now, admin_seen=now, admin_ua=ua_hash(), admin_pw=core.ADMIN_PW_FP, admin_2fa=bool(via_2fa))
    if bind_ip():
        session["admin_net"] = net_id(core.client_ip())
    session.permanent = False


def start_pre(kind, nxt=""):
    """Parola doğru; 2. adım (kod ya da zorunlu kurulum) için 5 dakikalık dar kapsamlı durum. Panele erişim vermez."""
    session.clear()
    pre = {"k": kind, "at": int(time.time()), "ua": ua_hash(), "nx": nxt or ""}
    if bind_ip():
        pre["net"] = net_id(core.client_ip())
    session["admin_pre"] = pre
    session.permanent = False


def pre_state():
    pre = session.get("admin_pre")
    if not isinstance(pre, dict):
        return None
    if time.time() - pre.get("at", 0) > PRE_SECONDS or pre.get("ua") != ua_hash() or (bind_ip() and pre.get("net") != net_id(core.client_ip())):
        session.pop("admin_pre", None)
        return None
    return pre


def _invalid_reason():
    now = time.time()
    if now - session.get("admin_at", 0) > core.ADMIN_SESSION_SECONDS:
        return "Yönetici oturumunun süresi doldu. Tekrar giriş yap."
    if now - session.get("admin_seen", 0) > IDLE_SECONDS:
        return "Uzun süre işlem yapılmadığı için oturum kapatıldı. Tekrar giriş yap."
    if session.get("admin_ua") != ua_hash() or session.get("admin_pw") != core.ADMIN_PW_FP:
        return "Güvenlik nedeniyle oturum kapatıldı. Tekrar giriş yap."
    if bind_ip() and session.get("admin_net") != net_id(core.client_ip()):
        return "Ağ adresin değiştiği için oturum kapatıldı. Tekrar giriş yap."
    if mode() != "off" and not session.get("admin_2fa"):
        # oturum 2FA olmadan açılmış: zorunluysa ya da bu arada 2FA kurulduysa geçersiz
        if mode() == "required" or tfa_enabled():
            return "Güvenlik ayarları değiştiği için tekrar giriş yapmalısın."
    return None


def _is_poll():
    return request.headers.get("X-Requested-With") == "fetch" or request.headers.get("Accept", "").startswith("application/json")


def check_session():
    """Her istekte: geçersiz yönetici oturumunu düşürür (genel sayfalardaki 'yönetici' görünümü dahil)."""
    if not session.get("admin"):
        return None
    reason = _invalid_reason()
    if reason:
        drop_admin()
        g.admin_dropped = reason
        return None
    if is_admin_request() and not _is_poll():
        session["admin_seen"] = int(time.time())       # kayan zaman aşımı: yalnızca yönetim paneli etkinliği sayılır
    return None


def is_full():
    return bool(session.get("admin"))


PRE_ENDPOINTS = {"admin.verify", "admin.setup", "admin.logout"}
PUBLIC_ENDPOINTS = {"admin.login"}


def guard():
    """admin blueprint'i before_request: yalnızca tam oturum panele girer; 2. adım bekleyen oturum yalnızca doğrulama/kurulum/çıkışa."""
    ep = request.endpoint
    if ep in PUBLIC_ENDPOINTS or session.get("admin"):
        return None
    pre = pre_state()
    if pre:
        want = "admin.verify" if pre["k"] == "verify" else "admin.setup"
        if ep in PRE_ENDPOINTS and (ep == "admin.logout" or ep == want):
            return None
        return redirect(url_for(want))
    msg = g.get("admin_dropped")
    if msg:
        flash(msg, "warn")
    return redirect(url_for("admin.login", next=request.path))


# --------------------------------------------------------------------------- Flask bağlantısı
def _before():
    if is_admin_request() and not ip_allowed():
        abort(404)                            # izin dışı IP için yönetim yolu hiç yokmuş gibi davranır (giriş sayfası dahil)
    return check_session()


def _after(resp):
    if is_admin_request():
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


def _ctx():
    if not (session.get("admin") and (request.endpoint or "").startswith("admin.")):
        return {}
    return {"admsec": {"alert": current_alert(), "tfa_warn": mode() == "optional" and not tfa_enabled(), "mode": mode()}}


def install(app):
    allowed_nets()
    if os.getenv("ADMIN_ALLOWED_IPS", "").strip():
        _parse_nets(os.getenv("ADMIN_ALLOWED_IPS", ""), True)      # geçersiz giriş varsa açılışta hata ver
    app.before_request(_before)
    app.after_request(_after)
    app.context_processor(_ctx)
    return app

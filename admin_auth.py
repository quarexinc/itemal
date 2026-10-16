"""Yönetici girişi rotaları: giriş (+CAPTCHA/honeypot), iki adımlı doğrulama, zorunlu kurulum, güvenlik sayfası, çıkış.

Mantık adminsec.py içindedir; burada yalnızca HTTP akışı vardır. Rotalar admin blueprint'ine eklenir (admin.py sonunda içe aktarılır).
"""
import hmac
import time

from flask import flash, redirect, render_template, request, session, url_for
from markupsafe import Markup

import adminsec
import core
import security
import totp
from admin import bp

GENERIC_FAIL = "Kullanıcı adı veya şifre hatalı."


# --------------------------------------------------------------------------- giriş
def _login_page(status=200):
    nxt = core.safe_next(request.values.get("next")) or ""
    return render_template("admin_login.html", ft=adminsec.form_token(), captcha=adminsec.captcha_required(), nxt=nxt), status


def _complete(via_2fa, how=""):
    """Tüm adımlar geçti: olayı yaz, sayaçları sıfırla, yeni oturum aç, yeni cihaz uyarısı üret."""
    why = adminsec.detect_new_device()
    adminsec.record_event("ok", security.mask_ident(core.ADMIN_USERNAME), how)
    adminsec.clear_login_state()
    adminsec.tfa_clear()
    adminsec.start_session(via_2fa)
    core.log_admin("Yönetici girişi", how)
    if why:
        adminsec.raise_alert(why)


def _fail(start, result, message, ident, count=True, detail="", log=True):
    dur = adminsec.register_failure() if count else 0
    adminsec.record_event(result, ident, detail)
    if log:
        core.log_admin("Başarısız giriş denemesi", f"kullanıcı adı: {ident}")
    if dur:
        adminsec.record_event("locked", ident, f"{dur // 60} dk")
        core.log_admin("Yönetici girişi kilitlendi", f"{adminsec.mask_ip(core.client_ip())}: {dur // 60} dk")
        message = adminsec.lock_message(dur)
    adminsec.fail_delay(start)
    flash(message, "bad")
    return _login_page(429 if dur else 200)


@bp.route("/giris", methods=["GET", "POST"])
def login():
    if session.get("admin"):
        return redirect(url_for("admin.dashboard"))
    if request.method == "GET":
        return _login_page()
    start = time.monotonic()
    wait = adminsec.lock_remaining()
    if wait or adminsec.site_limited():
        flash(adminsec.lock_message(wait or 900), "bad")
        return _login_page(429)
    ident = security.mask_ident(request.form.get("username", ""))
    state = adminsec.check_form_token(request.form.get("ft"))
    if request.form.get("website", "").strip():                       # honeypot: insan görmez, bot doldurur
        return _fail(start, "blocked_form", GENERIC_FAIL, ident, detail="honeypot", log=False)
    if state == "fast":
        return _fail(start, "blocked_form", "Form çok hızlı gönderildi. Birkaç saniye bekleyip tekrar dene.", ident, count=False, detail="hızlı gönderim", log=False)
    if state == "expired":
        return _fail(start, "blocked_form", "Sayfanın süresi doldu. Aşağıdaki formu doldurup tekrar dene.", ident, count=False, detail="form süresi doldu", log=False)
    if state == "bad":
        return _fail(start, "blocked_form", GENERIC_FAIL, ident, detail="form imzası yok/geçersiz", log=False)
    if adminsec.captcha_required() and not adminsec.admin_captcha_ok(request.form.get("captcha")):
        return _fail(start, "bad_captcha", "Güvenlik kodu hatalı.", ident)
    # kullanıcı adı ve parola her zaman ikisi de değerlendirilir (süre farkı sızdırmaz)
    user_ok = hmac.compare_digest(request.form.get("username", "")[:120].encode(), core.ADMIN_USERNAME.encode())
    pass_ok = core.verify_admin_password(request.form.get("password", "")[:256])
    if not (user_ok and pass_ok):
        return _fail(start, "bad_login", GENERIC_FAIL, ident)
    core.clear_attempts("admin_login")
    nxt = core.safe_next(request.form.get("next")) or ""
    m = adminsec.mode()
    if m == "off" or (m == "optional" and not adminsec.tfa_enabled()):
        _complete(False, "iki adımlı doğrulama yok" if m == "off" else "iki adımlı doğrulama kurulu değil")
        return redirect(nxt or url_for("admin.dashboard"))
    adminsec.record_event("pw_ok", ident)
    if adminsec.tfa_enabled():
        adminsec.start_pre("verify", nxt)
        return redirect(url_for("admin.verify"))
    adminsec.start_pre("setup", nxt)
    return redirect(url_for("admin.setup"))


@bp.post("/cikis")
def logout():
    if session.get("admin"):
        core.log_admin("Yönetici çıkışı")
    session.clear()                                              # tam temizlik: yönetici, ön-oturum, CAPTCHA, CSRF
    flash("Yönetici oturumu kapatıldı.", "info")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- 2. adım: kod
def _tfa_abort():
    adminsec.record_event("2fa_limit", security.mask_ident(core.ADMIN_USERNAME))
    core.log_admin("İki adımlı kod deneme sınırı aşıldı", adminsec.mask_ip(core.client_ip()))
    session.clear()
    flash("Çok fazla hatalı kod denemesi. 10 dakika sonra yeniden giriş yapmayı dene.", "bad")
    return redirect(url_for("admin.login"))


@bp.route("/dogrula", methods=["GET", "POST"])
def verify():
    if session.get("admin"):
        return redirect(url_for("admin.dashboard"))
    pre = adminsec.pre_state()
    if not pre or pre["k"] != "verify":
        return redirect(url_for("admin.login"))
    if request.method == "POST":
        if adminsec.tfa_limited():
            return _tfa_abort()
        adminsec.tfa_hit()
        kind = adminsec.check_second_factor(request.form.get("code", ""))
        if kind:
            _complete(True, "TOTP kodu" if kind == "totp" else "yedek kod")
            if kind == "backup":
                left = adminsec.backup_left()
                core.log_admin("Yedek kod kullanıldı", f"kalan: {left}")
                flash(f"Yedek kod kullanıldı. Kalan yedek kod: {left}. Güvenlik sayfasından yenilerini üretebilirsin.", "warn")
            return redirect(pre.get("nx") or url_for("admin.dashboard"))
        adminsec.record_event("bad_2fa", security.mask_ident(core.ADMIN_USERNAME))
        flash("Kod geçersiz ya da daha önce kullanılmış.", "bad")
    return render_template("admin_2fa.html", minutes_left=max(1, int((adminsec.PRE_SECONDS - (time.time() - pre["at"])) // 60) + 1))


# --------------------------------------------------------------------------- kurulum
def _setup_page(secret, **kw):
    account = core.ADMIN_USERNAME or "admin"
    issuer = (core.setting("site_name", "itemal") or "itemal")[:30]
    uri = totp.otpauth_uri(secret, account, issuer)
    svg = totp.qr_svg(uri)
    return render_template(
        "admin_2fa_setup.html",
        layout="admin_base.html" if session.get("admin") else "admin_authbase.html",
        full=bool(session.get("admin")), secret=secret,
        secret_fmt=" ".join(secret[i:i + 4] for i in range(0, len(secret), 4)),
        qr=Markup(svg) if svg else None, uri=uri, **kw,
    )


@bp.route("/guvenlik/kurulum", methods=["GET", "POST"])
def setup():
    full = bool(session.get("admin"))
    pre = None if full else adminsec.pre_state()
    if not full and (not pre or pre["k"] != "setup"):
        return redirect(url_for("admin.login"))
    if adminsec.tfa_enabled():
        if full:
            flash("İki adımlı doğrulama zaten etkin.", "info")
            return redirect(url_for("admin.security_page"))
        return redirect(url_for("admin.login"))
    if full and adminsec.mode() == "off":
        flash("ADMIN_2FA=off iken iki adımlı doğrulama kurulamaz. Önce .env içinde optional ya da required yap.", "warn")
        return redirect(url_for("admin.security_page"))
    secret = adminsec.pending_secret()
    if request.method == "POST":
        if adminsec.tfa_limited():
            if pre:
                return _tfa_abort()
            flash("Çok fazla hatalı deneme. 10 dakika sonra tekrar dene.", "bad")
            return _setup_page(secret, done=False)
        adminsec.tfa_hit()
        if full and not core.verify_admin_password(request.form.get("password", "")[:256]):
            adminsec.record_event("bad_2fa", security.mask_ident(core.ADMIN_USERNAME), "kurulumda parola hatalı")
            flash("Parola hatalı.", "bad")
            return _setup_page(secret, done=False)
        step = totp.verify(secret, request.form.get("code", ""), window=1)
        if step is None:
            adminsec.record_event("bad_2fa", security.mask_ident(core.ADMIN_USERNAME), "kurulum kodu hatalı")
            flash("Kod hatalı. Uygulamadaki güncel 6 haneli kodu gir (saatin doğru olduğundan emin ol).", "bad")
            return _setup_page(secret, done=False)
        codes = adminsec.enable_tfa(secret, step)
        core.log_admin("İki adımlı doğrulama etkinleştirildi")
        if pre:
            _complete(True, "zorunlu kurulum")
            nxt = pre.get("nx") or ""
        else:
            adminsec.tfa_clear()
            session["admin_2fa"] = True
            nxt = ""
        return _setup_page(secret, done=True, codes=codes, nxt=nxt)
    return _setup_page(secret, done=False)


# --------------------------------------------------------------------------- güvenlik sayfası
def _security_page(new_codes=None):
    now = time.time()
    idle_left = max(0, int(adminsec.IDLE_SECONDS - (now - session.get("admin_seen", now))))
    abs_left = max(0, int(core.ADMIN_SESSION_SECONDS - (now - session.get("admin_at", now))))
    nets, defined = adminsec.allowed_nets()
    info = {
        "idle_min": adminsec.IDLE_SECONDS // 60, "abs_hours": core.ADMIN_SESSION_SECONDS // 3600,
        "idle_left": idle_left // 60 + (1 if idle_left % 60 else 0), "abs_left": abs_left // 60,
        "bind_ip": adminsec.bind_ip(), "allow_count": len(nets) if defined else 0,
        "prefix": adminsec.URL_PREFIX, "custom_prefix": adminsec.URL_PREFIX != "/admin",
        "mode": adminsec.mode(), "your_ip": adminsec.mask_ip(core.client_ip()),
    }
    return render_template(
        "admin_security.html", enabled=adminsec.tfa_enabled(), since=adminsec.tfa_since(), left=adminsec.backup_left(),
        mode=adminsec.mode(), events=adminsec.recent_events(30), info=info, new_codes=new_codes,
    )


@bp.route("/guvenlik")
def security_page():
    return _security_page()


def _reauth(redirect_to="admin.security_page"):
    """Parola + güncel TOTP kodu ister. Başarılıysa None, değilse yönlendirme yanıtı döner."""
    if not adminsec.tfa_enabled():
        flash("İki adımlı doğrulama kurulu değil.", "warn")
        return redirect(url_for(redirect_to))
    if adminsec.tfa_limited():
        flash("Çok fazla hatalı deneme. 10 dakika sonra tekrar dene.", "bad")
        return redirect(url_for(redirect_to))
    adminsec.tfa_hit()
    if not core.verify_admin_password(request.form.get("password", "")[:256]) or not adminsec.check_totp(request.form.get("code", "")):
        adminsec.record_event("bad_2fa", security.mask_ident(core.ADMIN_USERNAME), "güvenlik sayfası: parola/kod hatalı")
        flash("Parola ya da kod hatalı (kod daha önce kullanılmış olabilir; yenisini bekle).", "bad")
        return redirect(url_for(redirect_to))
    adminsec.tfa_clear()
    return None


@bp.post("/guvenlik/yedek-kodlar")
def backup_regenerate():
    bad = _reauth()
    if bad:
        return bad
    codes = adminsec.regenerate_backup()
    core.log_admin("Yedek kodlar yeniden üretildi")
    return _security_page(new_codes=codes)


@bp.post("/guvenlik/kapat")
def tfa_disable():
    if adminsec.mode() == "required":
        flash("ADMIN_2FA=required iken iki adımlı doğrulama kapatılamaz.", "bad")
        return redirect(url_for("admin.security_page"))
    bad = _reauth()
    if bad:
        return bad
    adminsec.disable_tfa()
    core.log_admin("İki adımlı doğrulama kapatıldı")
    flash("İki adımlı doğrulama kapatıldı.", "warn")
    return redirect(url_for("admin.security_page"))


@bp.post("/guvenlik/uyari-kapat")
def security_dismiss():
    adminsec.dismiss_alert()
    core.log_admin("Yeni cihaz uyarısı onaylandı")
    flash("Uyarı kapatıldı.", "info")
    return redirect(url_for("admin.dashboard"))

"""itemal - Flask ile kullanıcıdan kullanıcıya e-pin pazaryeri.

Çalıştır:  python app.py
HTML şablonları ve CSS/JS ilk çalıştırmada otomatik üretilir (templates_gen.py).
"""
import os
import re
import sqlite3
from datetime import date, datetime, timedelta

from flask import (
    Flask, Response, abort, flash, g, jsonify, redirect, render_template, request, session, url_for,
)
from markupsafe import Markup, escape
from werkzeug.security import check_password_hash, generate_password_hash

import account_security as accsec
import payments as pay_mod
import captcha
import adminsec
import core
import db as dbm
import catbanner
import extras
import security
import services
import storage
import templates_gen
from core import BizError, ex, field, q, q1

if dbm.ensure_ready(core.DB_PATH):             # şema/tohum güncel değilse kurar; güncelse tek sorgu yapar (Vercel soğuk başlangıç)
    _boot = dbm.connect(core.DB_PATH)
    try:
        security.migrate_secrets(_boot)      # düz metin kayıtlı gizli ayarları şifrele (varsa)
    finally:
        _boot.close()
if not core.SERVERLESS:
    security.lock_down_files(core.BASE_DIR, core.DB_PATH)
    # Vercel'de dosya sistemi salt okunurdur: şablonlar ve public/static önceden üretilip pakete konur (manage.py build)
    templates_gen.generate(core.BASE_DIR, force=os.getenv("REGENERATE_TEMPLATES", "1") == "1")

app = Flask(
    __name__,
    template_folder=str(core.BASE_DIR / "templates"),
    static_folder=str(core.BASE_DIR / "public" / "static"),
    static_url_path="/static",
)
app.config.update(
    SECRET_KEY=core.SECRET_KEY,
    MAX_CONTENT_LENGTH=32 * 1024 * 1024,        # mutlak üst sınır; uç noktaya özel sınırlar security.py'de
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    TEMPLATES_AUTO_RELOAD=os.getenv("DEBUG") == "1",
    JSON_AS_ASCII=False,
)
if os.getenv("TRUST_PROXY", "1" if core.ON_VERCEL else "0") == "1":
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
adminsec.install(app)           # yönetici güvenliği: IP izin listesi (404), oturum sertleştirme, /admin başlıkları (en başta)
security.install(app)          # çerez, CORS, istek sınırları, girdi temizliği, log maskeleme (before_request'lerin en başında)
DUMMY_HASH = generate_password_hash("dummy-password-for-timing")

# --------------------------------------------------------------------------- Jinja
STATUS = {
    "pending": ("Beklemede", "warn"),
    "approved": ("Onaylandı", "ok"),
    "rejected": ("Reddedildi", "bad"),
    "active": ("Yayında", "ok"),
    "paused": ("Duraklatıldı", "warn"),
    "removed": ("Kaldırıldı", "bad"),
    "blocked": ("Yönetici engeli", "bad"),
    "none": ("Doğrulanmadı", "muted"),
    "held": ("Emanette", "warn"),
    "released": ("Tamamlandı", "ok"),
    "disputed": ("İtiraz var", "bad"),
    "refunded": ("İade edildi", "muted"),
    "open": ("Açık", "warn"),
    "resolved": ("Çözüldü", "ok"),
    "dismissed": ("Reddedildi", "muted"),
    "awaiting": ("Ödeme bekleniyor", "muted"),
}
TX_KINDS = {
    "deposit": "Bakiye yükleme",
    "purchase": "Satın alma",
    "sale": "Satış geliri",
    "withdraw": "Çekim talebi",
    "withdraw_refund": "Çekim iadesi",
    "refund": "Sipariş iadesi",
    "bonus": "Kazanç ekleme (yönetici)",
    "admin": "Yönetici düzenlemesi",
    "doping": "Doping satın alma",
    "package": "Mağaza paketi",
    "store_fee": "Mağaza adı / adres ücreti",
}


def mask_name(name):
    name = name or ""
    return name[:2] + "***" if len(name) > 2 else name[:1] + "***"


def cover_url(name, small=False):
    if not name:
        return ""
    return url_for("media_cover_small" if small else "media_cover", name=name)


def avatar_url(name):
    return url_for("media_avatar", name=name) if name else ""


def csrf_field():
    return Markup('<input type="hidden" name="csrf_token" value="%s">') % core.csrf_token()


app.jinja_env.filters.update(
    money=core.fmt_money,
    smoney=core.fmt_signed,
    plain=core.fmt_plain,
    dt=core.fmt_dt,
    slabel=lambda s: STATUS.get(s, (s, "muted"))[0],
    sclass=lambda s: STATUS.get(s, (s, "muted"))[1],
    kindlabel=lambda k: TX_KINDS.get(k, k),
    tlabel=lambda s: services.TICKET_STATUS.get(s, (s, "muted"))[0],
    tclass=lambda s: services.TICKET_STATUS.get(s, (s, "muted"))[1],
    plabel=lambda s: services.PRIORITIES.get(s, (s, "muted"))[0],
    pclass=lambda s: services.PRIORITIES.get(s, (s, "muted"))[1],
    tcat=lambda s: services.TICKET_CATEGORIES.get(s, s),
    mask=mask_name,
    ago=core.time_ago,
    mono=services.mono,
    local_input=core.utc_to_local_input,
)
app.jinja_env.globals.update(
    pay_methods=pay_mod.public_methods,
    pay_icon=pay_mod.clean_icon,
    csrf_token=core.csrf_token,
    csrf_field=csrf_field,
    page_url=core.page_url,
    cover_url=cover_url,
    category_banner_url=catbanner.category_banner_url,
    avatar_url=avatar_url,
    rating_of=services.rating_of,
    badges_for=services.user_badges,
    BADGES=services.BADGES,
    TICKET_CATEGORIES=services.TICKET_CATEGORIES,
    PRIORITIES=services.PRIORITIES,
)
app.teardown_appcontext(core.close_db)


@app.before_request
def _before():
    # /api/* çerez kullanmaz (anahtarla doğrulanır)
    if request.method == "POST" and not request.path.startswith("/api/") and request.path not in core.EXTERNAL_POST_PATHS:
        core.check_csrf()
    g.user = None
    ep = request.endpoint or ""
    if (
        core.setting("maintenance_mode", "0") == "1" and not session.get("admin")
        and not (ep == "static" or ep == "cron_daily" or ep.startswith(("admin.", "api.", "media_", "captcha.")))
    ):
        return render_template("maintenance.html"), 503
    if not request.path.startswith("/static/"):
        services.release_due()
    uid = session.get("uid")
    if uid:
        user = q1("SELECT * FROM users WHERE id = ?", (uid,))
        # yasaklı hesap ya da şifresi değişmiş (eski oturum) -> oturum düşer
        # ya da "tüm cihazlardan çıkış" yapılmış (sess_ver arttı) -> oturum düşer
        if (
            user and not user["is_banned"] and session.get("pv") == security.session_fingerprint(user["password_hash"])
            and session.get("sv", 0) == user["sess_ver"]
        ):
            g.user = user
        else:
            session.pop("uid", None)
            session.pop("pv", None)
            session.pop("sv", None)
    return security.post_auth_checks()


@app.after_request
def _cache_headers(resp):
    ep = request.endpoint or ""
    if ep != "static" and not ep.startswith("media_"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.context_processor
def _ctx():
    user = g.get("user")
    ctx = {
        "site_name": core.setting("site_name", "itemal"),
        "upload_max": security.SERVERLESS_BODY_LIMIT if core.SERVERLESS else 0,
        "cfg": core.public_settings(),
        "me": user,
        "is_admin": bool(session.get("admin")),
        "can_sell": core.can_sell(user),
        "year": datetime.now().year,
        "unread_chat": 0,
        "answered_tickets": 0,
    }
    ctx["nav_categories"] = []          # /static/... 404 sayfası da şablonu kullanır
    ctx["notif_unread"] = 0
    ctx["notif_recent"] = []
    ctx["fav_ids"] = set()
    ctx["fav_total"] = 0
    if user:
        ctx["unread_chat"] = services.unread_messages(user["id"])
        ctx["answered_tickets"] = services.answered_tickets(user["id"])
        ctx["notif_unread"] = q1("SELECT COUNT(*) AS n FROM notifications WHERE user_id = ? AND is_read = 0", (user["id"],))["n"]
        ctx["notif_recent"] = q("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 6", (user["id"],))
        favs = q("SELECT listing_id FROM favorites WHERE user_id = ?", (user["id"],))
        ctx["fav_ids"] = {f["listing_id"] for f in favs}
        ctx["fav_total"] = len(favs)
    if request.endpoint != "static":
        ctx["nav_categories"] = q("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id")
        if ctx["is_admin"]:
            ctx["pending"] = q1(
                "SELECT (SELECT COUNT(*) FROM deposits WHERE status='pending') AS deposits,"
                " (SELECT COUNT(*) FROM withdrawals WHERE status='pending') AS withdrawals,"
                " (SELECT COUNT(*) FROM kyc_requests WHERE status='pending') AS kyc,"
                " (SELECT COUNT(*) FROM seller_applications WHERE status='pending') AS sellers,"
                " (SELECT COUNT(*) FROM tickets WHERE status IN ('open')) AS tickets,"
                " (SELECT COUNT(*) FROM reports WHERE status='open') AS reports"
            )
    return ctx


def like_escape(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def render_error(code, title, message):
    return render_template("error.html", code=code, title=title, message=message), code


@app.errorhandler(400)
def _e400(e):
    return render_error(400, "İstek reddedildi", getattr(e, "description", "Geçersiz istek."))


@app.errorhandler(403)
def _e403(e):
    return render_error(403, "Erişim yok", "Bu sayfaya erişim iznin yok.")


@app.errorhandler(404)
def _e404(e):
    return render_error(404, "Sayfa bulunamadı", "Aradığın sayfa taşınmış ya da hiç var olmamış olabilir.")


@app.errorhandler(413)
def _e413(e):
    return render_error(413, "Dosya çok büyük", "Yüklediğin dosyaların toplam boyutu sınırı aşıyor. Daha küçük veya daha az görsel seçip tekrar dene.")


@app.errorhandler(500)
def _e500(e):
    return render_error(500, "Bir şeyler ters gitti", "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar dene.")


# --------------------------------------------------------------------------- zamanlanmış iş (Vercel Cron)
@app.get("/cron/gunluk")
def cron_daily():
    """Vercel Cron günde bir çağırır (Authorization: Bearer CRON_SECRET). Her iki yöntem de tekrar çalıştırılabilir (idempotent)."""
    import hmac

    secret = os.getenv("CRON_SECRET", "")
    got = request.headers.get("Authorization", "")
    if not secret or not hmac.compare_digest(got, "Bearer " + secret):
        abort(404)
    released = services.release_due(force=True)             # süresi dolan emanetler (istek başı tarama zaten yapar; bu yedek)
    ex("DELETE FROM rate_hits WHERE ts < ?", (int(__import__("time").time()) - 86400,))
    ad_banners = doping.cleanup_banners()                    # süresi dolalı birkaç gün olmuş reklam bannerları
    return jsonify(ok=True, released=released, ad_banners=ad_banners)


# --------------------------------------------------------------------------- medya (kapak / avatar)
def _media(kind, filename):
    found = storage.get(kind, filename)
    if not found:
        abort(404)
    resp = Response(found[1], mimetype=found[0])
    # Adlar rastgele ve değişmez: tarayıcı ve Vercel CDN uzun süre önbelleğe alabilir
    resp.headers["Cache-Control"] = "public, max-age=2592000, s-maxage=2592000, immutable"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


def _valid_media(name):
    if not services.MEDIA_NAME_RE.match(name or ""):
        abort(404)
    return name


@app.route("/medya/kapak/<name>")
def media_cover(name):
    return _media("cover", _valid_media(name))


@app.route("/medya/kapak-kucuk/<name>")
def media_cover_small(name):
    return _media("cover", "t_" + _valid_media(name))


@app.route("/medya/avatar/<name>")
def media_avatar(name):
    return _media("avatar", _valid_media(name))


# --------------------------------------------------------------------------- vitrin
PUBLIC_WHERE = " WHERE l.status = 'active' AND c.is_active = 1 AND u.is_banned = 0 "


@app.route("/")
def index():
    return render_template("index.html", **extras.home_context())


@app.route("/ilanlar")
def listings():
    where = ["l.status = 'active'", "c.is_active = 1", "u.is_banned = 0"]
    args = []
    text = request.args.get("q", "").strip()[:60]
    if text:
        where.append("(l.title LIKE ? ESCAPE '\\' OR l.description LIKE ? ESCAPE '\\')")
        args += [f"%{like_escape(text)}%"] * 2
    cat = request.args.get("kategori", "").strip()
    if cat:
        where.append("c.slug = ?")
        args.append(cat)
    if request.args.get("stok") == "1":
        where.append("EXISTS (SELECT 1 FROM listing_codes k WHERE k.listing_id = l.id AND k.is_sold = 0)")
    pmin, pmax = core.to_kurus(request.args.get("min")), core.to_kurus(request.args.get("max"))
    if pmin is not None:
        where.append("l.price >= ?")
        args.append(pmin)
    if pmax is not None:
        where.append("l.price <= ?")
        args.append(pmax)
    min_rating = request.args.get("puan", type=int)
    if min_rating in (3, 4, 5):
        where.append("l.rating_count > 0 AND CAST(l.rating_sum AS REAL) / l.rating_count >= ?")
        args.append(min_rating)
    sorts = {
        "yeni": "l.id DESC",
        "onerilen": "l.is_featured DESC, l.id DESC",
        "ucuz": "l.price ASC, l.id DESC",
        "pahali": "l.price DESC, l.id DESC",
        "populer": "l.sales_count DESC, l.id DESC",
        "puan": "CASE WHEN l.rating_count = 0 THEN 0 ELSE CAST(l.rating_sum AS REAL) / l.rating_count END DESC, l.rating_count DESC",
    }
    sort = request.args.get("sirala", "yeni")
    if sort not in sorts:
        sort = "yeni"
    page = core.paginate(core.LISTING_SELECT + " WHERE " + " AND ".join(where) + " ORDER BY " + sorts[sort], args, 12)
    # doping vitrinleri: yalnızca 1. sayfa, arama/sıralama filtrelerinden bağımsız (kategori seçiliyse önce kategori vitrini)
    vitrin_cat, vitrin_market = [], []
    if page["page"] == 1:
        if cat:
            vitrin_cat = doping.showcase("category", cat)
        vitrin_market = doping.showcase("market", "", [r["id"] for r in vitrin_cat])
    page["rows"] = doping.flag_rows(page["rows"])
    return render_template(
        "listings.html", page=page, text=text, cat=cat, sort=sort, only_stock=request.args.get("stok") == "1",
        pmin=request.args.get("min", ""), pmax=request.args.get("max", ""), min_rating=min_rating or 0,
        vitrin_cat=vitrin_cat, vitrin_market=vitrin_market,
    )


@app.route("/ilan/<int:lid>")
def listing_detail(lid):
    item = q1(core.LISTING_SELECT + " WHERE l.id = ?", (lid,))
    if not item:
        abort(404)
    owner = bool(g.user and g.user["id"] == item["seller_id"])
    seller = q1("SELECT * FROM users WHERE id = ?", (item["seller_id"],))
    visible = item["status"] == "active" and not seller["is_banned"]
    if not (visible or owner or session.get("admin")):
        abort(404)
    if visible and not owner:
        ex("UPDATE listings SET views = views + 1 WHERE id = ?", (lid,))
    stats = services.seller_stats(item["seller_id"])
    related = q(
        core.LISTING_SELECT
        + " WHERE l.status = 'active' AND l.category_id = ? AND l.id != ? AND u.is_banned = 0 ORDER BY l.id DESC LIMIT 4",
        (item["category_id"], lid),
    )
    reviews = q(
        "SELECT r.*, b.username AS buyer_name FROM reviews r JOIN users b ON b.id = r.buyer_id"
        " WHERE r.listing_id = ? AND r.is_hidden = 0 ORDER BY r.id DESC LIMIT 10",
        (lid,),
    )
    max_qty = max(1, min(core.setting_int("max_qty_per_order", 10), item["stock"] or 1))
    others = q(
        core.LISTING_SELECT + " WHERE l.status = 'active' AND l.seller_id = ? AND l.id != ? AND c.is_active = 1 ORDER BY l.id DESC LIMIT 4",
        (item["seller_id"], lid),
    )
    fav_count = q1("SELECT COUNT(*) AS n FROM favorites WHERE listing_id = ?", (lid,))["n"]
    return render_template(
        "listing.html", l=item, seller=seller, seller_stats=stats, seller_badges=services.user_badges(seller, stats),
        related=related, reviews=reviews, is_owner=owner, visible=visible, max_qty=max_qty, others=others, fav_count=fav_count,
        seller_vacation=storeplus.vacation_active(seller),
    )


@app.route("/<username>", endpoint="storefront")
def storefront(username):
    """Mağaza sayfası: alanadi/<özel adres ya da kullanıcı adı> (storeplus.resolve)."""
    return storeplus.resolve(username, render_storefront)


@app.route("/magaza/<username>", endpoint="storefront_legacy")
def storefront_legacy(username):
    return storeplus.resolve_legacy(username, render_storefront)


def render_storefront(seller):
    page = core.paginate(
        core.LISTING_SELECT + " WHERE l.status = 'active' AND l.seller_id = ? AND c.is_active = 1 ORDER BY (stock > 0) DESC, l.id DESC",
        (seller["id"],),
        12,
    )
    stats = services.seller_stats(seller["id"])
    reviews = q(
        "SELECT r.*, b.username AS buyer_name, l.title AS listing_title FROM reviews r"
        " JOIN users b ON b.id = r.buyer_id JOIN listings l ON l.id = r.listing_id"
        " WHERE r.seller_id = ? AND r.is_hidden = 0 ORDER BY r.id DESC LIMIT 10",
        (seller["id"],),
    )
    scomments = q(
        "SELECT c.*, a.username AS author_name FROM seller_comments c JOIN users a ON a.id = c.author_id"
        " WHERE c.seller_id = ? AND c.is_hidden = 0 ORDER BY c.id DESC LIMIT 30",
        (seller["id"],),
    )
    my_comment = q1("SELECT * FROM seller_comments WHERE seller_id = ? AND author_id = ?", (seller["id"], g.user["id"])) if g.user else None
    return render_template(
        "storefront.html", seller=seller, page=page, stats=stats, reviews=reviews, badges=services.user_badges(seller, stats),
        scomments=scomments, my_comment=my_comment, **storeplus.store_ctx(seller),
    )


@app.route("/sss")
def faq():
    return render_template("faq.html")


# --------------------------------------------------------------------------- satın alma
@app.post("/ilan/<int:lid>/satin-al")
@core.login_required
def buy(lid):
    if core.rate_hit("buy", 30, 600, key=f"u{g.user['id']}"):
        flash("Kısa sürede çok fazla satın alma denemesi yaptın. Biraz bekle.", "bad")
        return redirect(url_for("listing_detail", lid=lid))
    qty = request.form.get("qty", 1, type=int) or 1
    max_qty = core.setting_int("max_qty_per_order", 10)
    coupon_code = field("coupon", 40)
    if not 1 <= qty <= max_qty:
        flash(f"Adet 1 ile {max_qty} arasında olmalı.", "bad")
        return redirect(url_for("listing_detail", lid=lid))
    try:
        with core.tx():
            item = q1("SELECT * FROM listings WHERE id = ?", (lid,))
            if not item or item["status"] != "active":
                raise BizError("Bu ilan artık satışta değil.")
            if item["is_demo"] and core.setting("demo_sales", "1") != "1":
                raise BizError("Bu ilan şu anda satışa kapalı.")
            if item["seller_id"] == g.user["id"]:
                raise BizError("Kendi ilanını satın alamazsın.")
            seller = q1("SELECT * FROM users WHERE id = ?", (item["seller_id"],))
            if seller["is_banned"]:
                raise BizError("Bu satıcının ilanları şu an satışta değil.")
            if storeplus.vacation_active(seller):
                raise BizError("Bu mağaza şu an tatilde; yeni sipariş almıyor. Daha sonra tekrar dene.")
            buyer = q1("SELECT balance FROM users WHERE id = ?", (g.user["id"],))
            total = item["price"] * qty
            coupon, discount = (None, 0)
            if coupon_code:
                coupon, discount = services.coupon_check(coupon_code, g.user["id"], total, item["category_id"])
            pay = total - discount
            if buyer["balance"] < pay:
                raise BizError(f"Yetersiz bakiye. Gerekli tutar {core.fmt_money(pay)}, bakiyen {core.fmt_money(buyer['balance'])}.")
            codes = q(
                "SELECT id FROM listing_codes WHERE listing_id = ? AND is_sold = 0 ORDER BY id LIMIT ?", (lid, qty)
            )
            if len(codes) < qty:
                raise BizError("Yeterli stok kalmadı. Adedi azaltıp tekrar dene.")
            rate, _source = services.commission_info(seller, item["category_id"])
            commission = core.pct_of(total, rate)
            earning = total - commission
            cur = ex(
                "INSERT INTO orders(buyer_id, seller_id, listing_id, listing_title, unit_price, quantity, total,"
                " commission_rate, commission, seller_earning, discount, coupon_code, escrow_status, release_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'held', datetime('now', ?))",
                (g.user["id"], item["seller_id"], lid, item["title"], item["price"], qty, total, float(rate), commission, earning,
                 discount, coupon["code"] if coupon else "", f"+{core.setting_int('escrow_days', 3)} days"),
            )
            oid = cur.lastrowid
            ex(
                f"UPDATE listing_codes SET is_sold = 1, order_id = ? WHERE id IN ({','.join('?' * len(codes))})",
                (oid, *[c["id"] for c in codes]),
            )
            ex("UPDATE listings SET sales_count = sales_count + ?, updated_at = datetime('now') WHERE id = ?", (qty, lid))
            note = f" (kupon {coupon['code']})" if coupon else ""
            core.change_balance(g.user["id"], -pay, "purchase", f"#{oid} {item['title']} x{qty}{note}", "order", oid)
            if coupon:
                ex("UPDATE coupons SET used_count = used_count + 1 WHERE id = ?", (coupon["id"],))
                ex("INSERT INTO coupon_uses(coupon_id, user_id, order_id, amount) VALUES (?,?,?,?)", (coupon["id"], g.user["id"], oid, discount))
            if item["is_demo"]:
                storeplus.restock_listing(lid)
            services.notify(item["seller_id"], "Yeni satış", f"{item['title']} x{qty} satıldı. {core.fmt_money(earning)} alıcı onayı bekliyor.", url_for("seller.sales"))
    except BizError as err:
        flash(str(err), "bad")
        return redirect(url_for("listing_detail", lid=lid))
    except sqlite3.IntegrityError:
        flash("Yetersiz bakiye.", "bad")
        return redirect(url_for("listing_detail", lid=lid))
    flash("Satın alma tamamlandı. Kodların aşağıda; kontrol edip siparişi onaylayabilirsin.", "ok")
    return redirect(url_for("order_detail", oid=oid))


# --------------------------------------------------------------------------- üyelik
@app.route("/kayit", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("account"))
    form = {}
    if core.setting("allow_registration", "1") != "1":
        flash("Yeni üyelik alımı şu an kapalı.", "warn")
        return redirect(url_for("login"))
    if request.method == "POST":
        form = {"username": field("username", 30), "email": field("email", 120).lower()}
        password = request.form.get("password", "")
        errors = []
        pre = accsec.register_precheck()        # honeypot + form zaman damgası + CAPTCHA (her zaman) + deneme hızı
        if pre:
            errors.append(pre)
        if core.is_limited("register", 10, 3600):
            errors.append("Çok fazla deneme yaptın. Bir süre sonra tekrar dene.")
        if not core.USERNAME_RE.match(form["username"]):
            errors.append("Kullanıcı adı 3-20 karakter olmalı; yalnızca harf, rakam ve alt çizgi içerebilir.")
        elif storeplus.username_blocked(form["username"]):
            errors.append(storeplus.username_blocked(form["username"]))
        if not core.EMAIL_RE.match(form["email"]):
            errors.append("Geçerli bir e-posta adresi gir.")
        weak = core.weak_password(password, form["username"], form["email"])
        if weak:
            errors.append(weak)
        if password != request.form.get("password2", ""):
            errors.append("Şifreler eşleşmiyor.")
        if not request.form.get("agree"):
            errors.append("Kullanım koşullarını kabul etmelisin.")
        if not errors:
            core.record_attempt("register")
            try:
                cur = ex(
                    "INSERT INTO users(username, email, password_hash, reg_ip, last_ip) VALUES (?,?,?,?,?)",
                    (form["username"], form["email"], generate_password_hash(password), core.client_ip(), core.client_ip()),
                )
                ex("INSERT INTO login_events(user_id, ip, agent) VALUES (?,?,?)", (cur.lastrowid, core.client_ip(), request.headers.get("User-Agent", "")[:160]))
            except sqlite3.IntegrityError:
                errors.append("Bu kullanıcı adı veya e-posta zaten kayıtlı.")
            else:
                session.clear()
                session["uid"] = cur.lastrowid
                session["pv"] = security.session_fingerprint(q1("SELECT password_hash FROM users WHERE id = ?", (cur.lastrowid,))["password_hash"])
                session["sv"] = 0
                session.permanent = True
                flash("Hoş geldin. Hesabın oluşturuldu.", "ok")
                return redirect(url_for("account"))
        for e in errors:
            flash(e, "bad")
    return render_template("register.html", form=form)


@app.route("/giris", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("account"))
    nxt = core.safe_next(request.values.get("next"))
    if request.method == "POST":
        ident = field("ident", 120)
        ikey = core.ident_key(ident)
        # hem IP başına hem hesap başına sınır: dağıtık deneme de tek hesabı kilitlemeden yavaşlatılır;
        # tekrarlayan IP kilitleri kademelidir (15 dk -> 1 saat -> 24 saat)
        lock = accsec.ip_lock_left()
        if lock or core.is_limited("login") or core.is_limited("login_acct", 6, 900, key=ikey) or core.is_limited("login_all", 60, 600, key="*"):
            flash(f"Çok fazla başarısız deneme. Güvenlik nedeniyle giriş geçici olarak kısıtlandı; {accsec.lock_text(lock or 600)} sonra tekrar dene.", "bad")
            return render_template("login.html", next=nxt, show_captcha=accsec.login_captcha_needed(ikey)), 429
        # honeypot + imzalı zaman damgası, eşik aşıldıysa CAPTCHA; hepsi tek tip genel hata verir
        bad = accsec.check_form("login")
        if bad:
            accsec.bot_failure(bad, ident)
        elif accsec.login_captcha_needed(ikey) and not captcha.verify("login", request.form.get("captcha")):
            bad = "captcha"
            accsec.bot_failure(bad, ident)
        if bad:
            flash(accsec.GENERIC_LOGIN_ERROR, "bad")
            return render_template("login.html", next=nxt, show_captcha=accsec.login_captcha_needed(ikey))
        password = request.form.get("password", "")[:256]
        user = q1("SELECT * FROM users WHERE username = ? OR email = ?", (ident, ident.lower()))
        ok = check_password_hash(user["password_hash"] if user else DUMMY_HASH, password)
        if user and ok:
            if user["is_banned"]:
                flash("Hesabın askıya alınmış. Destek ile iletişime geç.", "bad")
                return render_template("login.html", next=nxt)
            if core.needs_rehash(user["password_hash"]):
                ex("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(password), user["id"]))
                user = q1("SELECT * FROM users WHERE id = ?", (user["id"],))
            if accsec.has_2fa(user):                       # parola doğru: ikinci adım (TOTP / yedek kod)
                return accsec.start_2fa(user, nxt, request.form.get("remember"), ikey)
            return accsec.finish_login(user, nxt, request.form.get("remember"), ikey)
        accsec.credential_failure(ident, ikey, user, "parola" if user else "kullanici")
        flash(accsec.GENERIC_LOGIN_ERROR, "bad")
        return render_template("login.html", next=nxt, show_captcha=accsec.login_captcha_needed(ikey))
    return render_template("login.html", next=nxt, show_captcha=accsec.login_captcha_needed())


@app.post("/cikis")
def logout():
    session.clear()
    flash("Çıkış yaptın.", "info")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- hesabım
@app.route("/hesabim")
@core.login_required
def account():
    uid = g.user["id"]
    stats = q1(
        "SELECT (SELECT COUNT(*) FROM orders WHERE buyer_id = ?1) AS orders,"
        " (SELECT COALESCE(SUM(total), 0) FROM orders WHERE buyer_id = ?1) AS spent,"
        " (SELECT COUNT(*) FROM deposits WHERE user_id = ?1 AND status = 'pending') AS pending_deposits,"
        " (SELECT COUNT(*) FROM withdrawals WHERE user_id = ?1 AND status = 'pending') AS pending_withdrawals",
        (uid,),
    )
    recent_orders = q("SELECT * FROM orders WHERE buyer_id = ? ORDER BY id DESC LIMIT 5", (uid,))
    recent_tx = q("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 6", (uid,))
    return render_template("account.html", stats=stats, recent_orders=recent_orders, recent_tx=recent_tx)


@app.route("/bakiye", methods=["GET", "POST"])
@core.login_required
def balance():
    methods = q("SELECT * FROM payment_methods WHERE is_active = 1 ORDER BY sort_order, id")
    min_deposit = core.setting_kurus("min_deposit", 2000)
    if request.method == "POST":
        if core.rate_hit("deposit", 10, 3600, key=f"u{g.user['id']}"):
            flash("Kısa sürede çok fazla ödeme bildirimi gönderdin. Biraz bekle.", "bad")
            return redirect(url_for("balance"))
        method = q1("SELECT * FROM payment_methods WHERE id = ? AND is_active = 1", (request.form.get("method_id", type=int),))
        amount = core.to_kurus(request.form.get("amount"))
        reference = field("reference", 120)
        note = field("note", 300)
        try:
            if not method:
                raise BizError("Geçerli bir yükleme yöntemi seç.")
            need = max(min_deposit, method["min_amount"])
            if amount is None or amount < need:
                raise BizError(f"Bu yöntem için minimum yükleme tutarı {core.fmt_money(need)}.")
            top = min(50_000_000, method["max_amount"]) if method["max_amount"] else 50_000_000
            if amount > top:
                raise BizError(f"Bu yöntemle tek seferde en fazla {core.fmt_money(top)} yükleme bildirilebilir.")
            if len(reference) < 3:
                raise BizError("Dekont/işlem numarası veya gönderen adı alanını doldur.")
            open_count = q1("SELECT COUNT(*) AS c FROM deposits WHERE user_id = ? AND status = 'pending'", (g.user["id"],))["c"]
            if open_count >= 5:
                raise BizError("Bekleyen 5 talebin var. Onaylanmasını bekle.")
        except BizError as err:
            flash(str(err), "bad")
        else:
            import payments as pay
            bonus = pay.bonus_for(amount, method["bonus_percent"])
            cur = ex(
                "INSERT INTO deposits(user_id, method_id, method_name, amount, bonus, reference, note) VALUES (?,?,?,?,?,?,?)",
                (g.user["id"], method["id"], method["name"], amount, bonus, reference, note),
            )
            flash(
                f"Yükleme bildirimin alındı (talep no #{cur.lastrowid}). Ödemen kontrol edildikten sonra bakiyene eklenecek"
                + (f"; {core.fmt_money(bonus)} yükleme bonusu da eklenecek." if bonus else "."),
                "ok",
            )
            return redirect(url_for("balance"))
    history = q("SELECT * FROM deposits WHERE user_id = ? ORDER BY id DESC LIMIT 15", (g.user["id"],))
    pay_links = q("SELECT * FROM pay_links WHERE is_active = 1 ORDER BY sort_order, id")
    want = request.args.get("tutar", "")
    pre_amount = core.to_kurus(want) if want else None
    pre_method = request.args.get("yontem", type=int)
    return render_template(
        "balance.html", methods=methods, history=history, min_deposit=min_deposit, pay_links=pay_links,
        pre_amount=pre_amount if pre_amount and 100 <= pre_amount <= 50_000_000 else None,
        pre_method=pre_method if pre_method in [m["id"] for m in methods] else (methods[0]["id"] if methods else None),
        pm_kind_icon=pay_mod.KIND_ICON, pm_clean_icon=pay_mod.clean_icon,
    )


@app.route("/cekim", methods=["GET", "POST"])
@core.login_required
def withdraw():
    uid = g.user["id"]
    if g.user["kyc_status"] != "approved":
        return redirect(url_for("kyc", devam="cekim"))
    min_w = core.setting_kurus("min_withdraw", 10000)
    fee_rate = core.setting_pct("withdraw_fee_percent", "2")
    earnings_only = core.setting("withdraw_only_earnings", "1") == "1"
    methods = ["IBAN (Banka Havalesi)", "Papara", "Kripto (USDT - TRC20)"]
    if request.method == "POST":
        amount = core.to_kurus(request.form.get("amount"))
        method = request.form.get("method", "")
        info = re.sub(r"\s+", " ", field("account_info", 300))
        try:
            if core.rate_hit("withdraw", 10, 3600, key=f"u{uid}"):
                raise BizError("Kısa sürede çok fazla çekim denemesi yaptın. Biraz bekle.")
            with core.tx():
                available = core.withdrawable(uid) if earnings_only else q1("SELECT balance FROM users WHERE id = ?", (uid,))["balance"]
                if method not in methods:
                    raise BizError("Geçerli bir çekim yöntemi seç.")
                if amount is None or amount < min_w:
                    raise BizError(f"Minimum çekim tutarı {core.fmt_money(min_w)}.")
                if amount > available:
                    raise BizError(f"Çekilebilir bakiyen {core.fmt_money(available)}.")
                info = services.validate_payout(method, info)
                if q1("SELECT COUNT(*) AS c FROM withdrawals WHERE user_id = ? AND status = 'pending'", (uid,))["c"] >= 3:
                    raise BizError("Bekleyen 3 çekim talebin var. Sonuçlanmasını bekle.")
                fee = core.pct_of(amount, fee_rate)
                cur = ex(
                    "INSERT INTO withdrawals(user_id, amount, fee, net, method, account_info) VALUES (?,?,?,?,?,?)",
                    (uid, amount, fee, amount - fee, method, info),
                )
                core.change_balance(uid, -amount, "withdraw", f"Çekim talebi #{cur.lastrowid}", "withdrawal", cur.lastrowid)
        except BizError as err:
            flash(str(err), "bad")
        else:
            flash("Çekim talebin alındı. Onaylandığında ödemen yapılacak.", "ok")
            return redirect(url_for("withdraw"))
    available = core.withdrawable(uid) if earnings_only else g.user["balance"]
    history = q("SELECT * FROM withdrawals WHERE user_id = ? ORDER BY id DESC LIMIT 15", (uid,))
    last = {}
    for r in q("SELECT method, account_info FROM withdrawals WHERE user_id = ? ORDER BY id DESC LIMIT 20", (uid,)):
        last.setdefault(r["method"], r["account_info"])
    return render_template(
        "withdraw.html", methods=methods, history=history, available=available, min_w=min_w, fee_rate=fee_rate, earnings_only=earnings_only,
        last_accounts=last,
    )


@app.route("/siparislerim")
@core.login_required
def orders():
    page = core.paginate(
        "SELECT o.*, u.username AS seller_name, (SELECT COUNT(*) FROM reviews r WHERE r.order_id = o.id) AS reviewed"
        " FROM orders o JOIN users u ON u.id = o.seller_id WHERE o.buyer_id = ? ORDER BY o.id DESC",
        (g.user["id"],),
        10,
    )
    return render_template("orders.html", page=page)


@app.route("/siparis/<int:oid>")
@core.login_required
def order_detail(oid):
    order = q1(
        "SELECT o.*, b.username AS buyer_name, s.username AS seller_name FROM orders o"
        " JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id WHERE o.id = ?",
        (oid,),
    )
    if not order or g.user["id"] not in (order["buyer_id"], order["seller_id"]):
        abort(404)
    is_buyer = g.user["id"] == order["buyer_id"]
    codes = q("SELECT code FROM listing_codes WHERE order_id = ? ORDER BY id", (oid,)) if is_buyer else []
    review = q1("SELECT * FROM reviews WHERE order_id = ?", (oid,))
    return render_template("order.html", o=order, codes=codes, is_buyer=is_buyer, review=review)


@app.post("/siparis/<int:oid>/degerlendir")
@core.login_required
def review_create(oid):
    order = q1("SELECT * FROM orders WHERE id = ? AND buyer_id = ?", (oid, g.user["id"]))
    if not order:
        abort(404)
    rating = request.form.get("rating", type=int)
    comment = field("comment", 500)
    if rating not in (1, 2, 3, 4, 5):
        flash("Lütfen 1 ile 5 arasında bir puan seç.", "bad")
        return redirect(url_for("order_detail", oid=oid))
    try:
        with core.tx():
            ex(
                "INSERT INTO reviews(order_id, listing_id, seller_id, buyer_id, rating, comment) VALUES (?,?,?,?,?,?)",
                (oid, order["listing_id"], order["seller_id"], g.user["id"], rating, comment),
            )
            services.recalc_rating(order["listing_id"])
            services.notify(order["seller_id"], "Yeni yorum", f"{order['listing_title']} için {rating}/5 puan aldın.", url_for("seller.reviews"))
    except sqlite3.IntegrityError:
        flash("Bu sipariş için zaten değerlendirme yaptın.", "info")
    else:
        flash("Değerlendirmen için teşekkürler. Satıcı ve diğer alıcılar görebilecek.", "ok")
    return redirect(url_for("order_detail", oid=oid))


@app.route("/hareketler")
@core.login_required
def transactions():
    page = core.paginate("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC", (g.user["id"],), 20)
    return render_template("transactions.html", page=page)


# --------------------------------------------------------------------------- mesajlaşma (alıcı <-> satıcı)
CONV_SELECT = (
    "SELECT v.*, l.title AS listing_title, l.cover AS listing_cover, l.status AS listing_status,"
    " b.username AS buyer_name, b.avatar AS buyer_avatar,"
    " s.username AS seller_name, s.avatar AS seller_avatar,"
    " COALESCE(NULLIF(s.store_name, ''), s.username) AS seller_display"
    " FROM conversations v JOIN listings l ON l.id = v.listing_id"
    " JOIN users b ON b.id = v.buyer_id JOIN users s ON s.id = v.seller_id"
)


def my_conversation(cid):
    conv = q1(CONV_SELECT + " WHERE v.id = ?", (cid,))
    if not conv or g.user["id"] not in (conv["buyer_id"], conv["seller_id"]):
        abort(404)
    return conv


@app.post("/ilan/<int:lid>/mesaj")
@core.login_required
def chat_start(lid):
    item = q1("SELECT * FROM listings WHERE id = ? AND status = 'active'", (lid,))
    if not item:
        abort(404)
    if item["seller_id"] == g.user["id"]:
        flash("Kendi ilanına mesaj gönderemezsin.", "info")
        return redirect(url_for("listing_detail", lid=lid))
    seller = q1("SELECT is_banned FROM users WHERE id = ?", (item["seller_id"],))
    if seller["is_banned"]:
        abort(404)
    conv = q1("SELECT id FROM conversations WHERE listing_id = ? AND buyer_id = ?", (lid, g.user["id"]))
    if not conv:
        if core.is_limited("chatstart", 10, 3600):
            flash("Kısa sürede çok fazla yeni konuşma başlattın. Biraz bekle.", "bad")
            return redirect(url_for("listing_detail", lid=lid))
        core.record_attempt("chatstart")
        cur = ex("INSERT INTO conversations(listing_id, buyer_id, seller_id) VALUES (?,?,?)", (lid, g.user["id"], item["seller_id"]))
        cid = cur.lastrowid
        storeplus.auto_reply_on_start(cid, item["seller_id"])
    else:
        cid = conv["id"]
    return redirect(url_for("chat", cid=cid))


@app.route("/mesajlar")
@core.login_required
def inbox():
    uid = g.user["id"]
    rows = q(
        CONV_SELECT + " WHERE v.buyer_id = ?1 OR v.seller_id = ?1 ORDER BY v.last_message_at DESC LIMIT 100",
        (uid,),
    )
    convs = []
    for c in rows:
        last = q1("SELECT body, sender_id, created_at FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 1", (c["id"],))
        unread = q1(
            "SELECT COUNT(*) AS n FROM messages WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL", (c["id"], uid)
        )["n"]
        convs.append({"c": c, "last": last, "unread": unread, "other": c["seller_display"] if c["buyer_id"] == uid else c["buyer_name"],
                      "other_avatar": c["seller_avatar"] if c["buyer_id"] == uid else c["buyer_avatar"]})
    return render_template("inbox.html", convs=convs)


@app.route("/mesajlar/<int:cid>", methods=["GET", "POST"])
@core.login_required
def chat(cid):
    conv = my_conversation(cid)
    uid = g.user["id"]
    if request.method == "POST":
        body = services.clean_message(request.form.get("body"))
        wants_json = request.headers.get("X-Requested-With") == "fetch"
        error = ""
        if conv["is_locked"]:
            error = "Bu konuşma yönetim tarafından kilitlendi."
        elif not body:
            error = "Boş mesaj gönderilemez."
        elif core.is_limited("chatmsg", 30, 60):
            error = "Çok hızlı mesaj gönderiyorsun. Biraz bekle."
        msg_id = 0
        if not error:
            core.record_attempt("chatmsg")
            cur = ex("INSERT INTO messages(conversation_id, sender_id, body) VALUES (?,?,?)", (cid, uid, body))
            msg_id = cur.lastrowid
            ex("UPDATE conversations SET last_message_at = datetime('now') WHERE id = ?", (cid,))
        if wants_json:
            return jsonify({"ok": not error, "error": error, "id": msg_id}), (200 if not error else 400)
        if error:
            flash(error, "bad")
        return redirect(url_for("chat", cid=cid) + "#son")
    ex("UPDATE messages SET read_at = datetime('now') WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL", (cid, uid))
    msgs = q("SELECT * FROM (SELECT * FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 200) ORDER BY id", (cid,))
    other_id = conv["seller_id"] if conv["buyer_id"] == uid else conv["buyer_id"]
    other = q1("SELECT * FROM users WHERE id = ?", (other_id,))
    return render_template(
        "chat.html", conv=conv, msgs=msgs, other=other, other_badges=services.user_badges(other) if other["is_seller"] else [],
        last_id=msgs[-1]["id"] if msgs else 0,
    )


@app.route("/mesajlar/<int:cid>/yeni")
@core.login_required
def chat_poll(cid):
    my_conversation(cid)
    uid = g.user["id"]
    after = request.args.get("after", 0, type=int)
    rows = q("SELECT * FROM messages WHERE conversation_id = ? AND id > ? ORDER BY id LIMIT 100", (cid, after))
    ex("UPDATE messages SET read_at = datetime('now') WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL", (cid, uid))
    return jsonify([
        {"id": m["id"], "mine": m["sender_id"] == uid, "body": m["body"], "time": core.fmt_dt(m["created_at"])} for m in rows
    ])


# --------------------------------------------------------------------------- destek talepleri
@app.route("/destek")
@core.login_required
def tickets():
    page = core.paginate("SELECT * FROM tickets WHERE user_id = ? ORDER BY updated_at DESC, id DESC", (g.user["id"],), 15)
    return render_template("tickets.html", page=page)


@app.route("/destek/yeni", methods=["GET", "POST"])
@core.login_required
def ticket_new():
    uid = g.user["id"]
    my_orders = q("SELECT id, listing_title FROM orders WHERE buyer_id = ? OR seller_id = ? ORDER BY id DESC LIMIT 30", (uid, uid))
    form = {}
    need_captcha = accsec.abuse_needs_captcha("ticket")         # kısa sürede 3 talepten sonra CAPTCHA
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ("subject", "category", "order_id", "message")}
        try:
            if need_captcha and not captcha.verify("ticket", request.form.get("captcha")):
                raise BizError("Güvenlik doğrulaması hatalı ya da süresi dolmuş. Resimdeki karakterleri yeniden yaz.")
            subject = field("subject", 100)
            message = services.clean_message(request.form.get("message"), 3000)
            category = request.form.get("category")
            order_id = request.form.get("order_id", type=int)
            if len(subject) < 5:
                raise BizError("Konu en az 5 karakter olmalı.")
            if category not in services.TICKET_CATEGORIES:
                raise BizError("Bir kategori seç.")
            if len(message) < 10:
                raise BizError("Mesajın en az 10 karakter olmalı; sorunu ayrıntılı anlat.")
            if order_id and not q1("SELECT 1 FROM orders WHERE id = ? AND (buyer_id = ? OR seller_id = ?)", (order_id, uid, uid)):
                raise BizError("Seçtiğin sipariş sana ait değil.")
            if q1("SELECT COUNT(*) AS c FROM tickets WHERE user_id = ? AND status != 'closed'", (uid,))["c"] >= 5:
                raise BizError("Açık 5 destek talebin var. Önce mevcutların sonuçlanmasını bekle.")
            with core.tx():
                cur = ex(
                    "INSERT INTO tickets(user_id, subject, category, order_id, priority) VALUES (?,?,?,?,?)",
                    (uid, subject, category, order_id or None,
                     "high" if category in ("odeme", "sikayet") or packages.priority_support(uid) else "normal"),
                )
                ex("INSERT INTO ticket_messages(ticket_id, author, user_id, body) VALUES (?,?,?,?)", (cur.lastrowid, "user", uid, message))
        except BizError as err:
            flash(str(err), "bad")
        else:
            accsec.abuse_record("ticket")
            flash(f"Destek talebin oluşturuldu (#{cur.lastrowid}). En kısa sürede yanıtlayacağız.", "ok")
            return redirect(url_for("ticket_view", tid=cur.lastrowid))
    return render_template("ticket_new.html", my_orders=my_orders, form=form, preset_order=request.args.get("siparis", type=int), need_captcha=accsec.abuse_needs_captcha("ticket"))


@app.route("/destek/<int:tid>", methods=["GET", "POST"])
@core.login_required
def ticket_view(tid):
    ticket = q1("SELECT * FROM tickets WHERE id = ? AND user_id = ?", (tid, g.user["id"]))
    if not ticket:
        abort(404)
    if request.method == "POST":
        if request.form.get("action") == "close":
            ex("UPDATE tickets SET status = 'closed', updated_at = datetime('now') WHERE id = ?", (tid,))
            flash("Talep kapatıldı.", "info")
        else:
            body = services.clean_message(request.form.get("message"), 3000)
            if len(body) < 2:
                flash("Mesaj boş olamaz.", "bad")
            elif core.is_limited("ticketmsg", 15, 600):
                flash("Çok fazla mesaj gönderdin. Biraz bekle.", "bad")
            else:
                core.record_attempt("ticketmsg")
                with core.tx():
                    ex("INSERT INTO ticket_messages(ticket_id, author, user_id, body) VALUES (?,?,?,?)", (tid, "user", g.user["id"], body))
                    ex("UPDATE tickets SET status = 'open', last_reply_by = 'user', updated_at = datetime('now') WHERE id = ?", (tid,))
                flash("Mesajın gönderildi.", "ok")
        return redirect(url_for("ticket_view", tid=tid))
    msgs = q("SELECT * FROM ticket_messages WHERE ticket_id = ? AND is_internal = 0 ORDER BY id", (tid,))
    return render_template("ticket.html", t=ticket, msgs=msgs)


# --------------------------------------------------------------------------- kimlik onayı
@app.route("/kimlik", methods=["GET", "POST"])
@core.login_required
def kyc():
    uid = g.user["id"]
    last = q1("SELECT * FROM kyc_requests WHERE user_id = ? ORDER BY id DESC LIMIT 1", (uid,))
    if request.method == "POST":
        if g.user["kyc_status"] in ("pending", "approved"):
            flash("Kimlik başvurun zaten inceleniyor veya onaylı.", "info")
            return redirect(url_for("kyc"))
        full_name = field("full_name", 80)
        id_number = field("id_number", 11)
        birth = field("birth_date", 10)
        doc_type = request.form.get("doc_type") if request.form.get("doc_type") in ("kimlik", "ehliyet") else "kimlik"
        saved, infos = [], {}
        try:
            if core.is_limited("kyc", 5, 3600):
                raise BizError("Çok fazla deneme yaptın. Bir süre sonra tekrar dene.")
            core.record_attempt("kyc")
            if len(full_name.split()) < 2 or len(full_name) < 5:
                raise BizError("Ad soyadını kimlikte yazdığı gibi eksiksiz gir.")
            if not core.valid_tc(id_number):
                raise BizError("T.C. kimlik numarası geçersiz.")
            try:
                born = datetime.strptime(birth, "%Y-%m-%d").date()
            except ValueError:
                raise BizError("Doğum tarihi geçersiz.")
            today = date.today()
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            if not 18 <= age <= 100:
                raise BizError("Hizmetlerimizi kullanmak için 18 yaşından büyük olmalısın.")
            if q1("SELECT 1 FROM kyc_requests WHERE id_number = ? AND user_id != ? AND status IN ('pending','approved')", (id_number, uid)):
                raise BizError("Bu kimlik numarası başka bir hesapta kullanılıyor.")
            for key, label in (("id_front", "Kimlik ön yüz"), ("id_back", "Kimlik arka yüz"), ("selfie", "Kimlikle selfie")):
                info = services.inspect_kyc_image(request.files.get(key), label)
                saved.append(info["name"])
                infos[key] = info
            hashes = {"front": infos["id_front"]["hash"], "back": infos["id_back"]["hash"], "selfie": infos["selfie"]["hash"]}
            flags = [f for i in infos.values() for f in i["flags"]] + services.kyc_duplicate_flags(uid, id_number, hashes)
        except BizError as err:
            for name in saved:
                core.delete_upload(name)
            flash(str(err), "bad")
        else:
            with core.tx():
                ex(
                    "INSERT INTO kyc_requests(user_id, doc_type, full_name, id_number, birth_date, id_front, id_back, selfie,"
                    " front_hash, back_hash, selfie_hash, flags) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (uid, doc_type, full_name, id_number, birth, *saved, hashes["front"], hashes["back"], hashes["selfie"], "\n".join(flags)),
                )
                ex("UPDATE users SET kyc_status = 'pending' WHERE id = ?", (uid,))
            flash("Kimlik başvurun alındı. En kısa sürede incelenecek.", "ok")
            return redirect(url_for("kyc"))
    return render_template("kyc.html", last=last)


# --------------------------------------------------------------------------- satıcı başvurusu
@app.route("/satici-basvuru", methods=["GET", "POST"])
@core.login_required
def seller_apply():
    if core.can_sell(g.user):
        return redirect(url_for("seller.dashboard"))
    uid = g.user["id"]
    last = q1("SELECT * FROM seller_applications WHERE user_id = ? ORDER BY id DESC LIMIT 1", (uid,))
    pending = bool(last and last["status"] == "pending")
    form = {}
    if request.method == "POST" and not pending:
        form = {"store_name": field("store_name", 40), "description": field("description", 500), "experience": field("experience", 500)}
        try:
            if not 3 <= len(form["store_name"]) <= 40:
                raise BizError("Mağaza adı 3-40 karakter olmalı.")
            if len(form["description"]) < 20:
                raise BizError("Mağaza açıklaması en az 20 karakter olmalı.")
            if not request.form.get("agree"):
                raise BizError("Satıcı kurallarını kabul etmelisin.")
            taken = q1(
                "SELECT 1 FROM users WHERE store_name = ? COLLATE NOCASE AND id != ?"
                " UNION SELECT 1 FROM seller_applications WHERE store_name = ? COLLATE NOCASE AND status = 'pending'",
                (form["store_name"], uid, form["store_name"]),
            )
            if taken:
                raise BizError("Bu mağaza adı kullanılıyor, başka bir ad seç.")
        except BizError as err:
            flash(str(err), "bad")
        else:
            ex(
                "INSERT INTO seller_applications(user_id, store_name, description, experience) VALUES (?,?,?,?)",
                (uid, form["store_name"], form["description"], form["experience"]),
            )
            flash("Satıcı başvurun alındı. Sonuç hesabına yansıyacak.", "ok")
            return redirect(url_for("seller_apply"))
    return render_template("seller_apply.html", last=last, pending=pending, form=form)


# --------------------------------------------------------------------------- profil
@app.route("/profil", methods=["GET", "POST"])
@core.login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "phone":
            phone = field("phone", 20)
            if phone and not re.fullmatch(r"[0-9+\s()-]{7,20}", phone):
                flash("Telefon numarası geçersiz.", "bad")
            else:
                ex("UPDATE users SET phone = ? WHERE id = ?", (phone, g.user["id"]))
                flash("Telefon bilgin güncellendi.", "ok")
        elif action == "avatar":
            try:
                name = services.save_avatar(request.files.get("avatar"))
                if not name:
                    raise BizError("Bir görsel seç.")
            except BizError as err:
                flash(str(err), "bad")
            else:
                services.delete_avatar(g.user["avatar"])
                ex("UPDATE users SET avatar = ? WHERE id = ?", (name, g.user["id"]))
                flash("Profil fotoğrafın güncellendi.", "ok")
        elif action == "avatar_remove":
            services.delete_avatar(g.user["avatar"])
            ex("UPDATE users SET avatar = '' WHERE id = ?", (g.user["id"],))
            flash("Profil fotoğrafın kaldırıldı.", "info")
        elif action == "password":
            current = request.form.get("current", "")[:256]
            new = request.form.get("new", "")
            if core.is_limited("chpw", 6, 900):
                flash("Çok fazla deneme yaptın. Biraz bekle.", "bad")
            elif not check_password_hash(g.user["password_hash"], current):
                core.record_attempt("chpw")
                flash("Mevcut şifren hatalı.", "bad")
            elif core.weak_password(new, g.user["username"], g.user["email"]):
                flash(core.weak_password(new, g.user["username"], g.user["email"]), "bad")
            elif new != request.form.get("new2", ""):
                flash("Yeni şifreler eşleşmiyor.", "bad")
            else:
                new_hash = generate_password_hash(new)
                ex("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, g.user["id"]))
                session["pv"] = security.session_fingerprint(new_hash)      # diğer cihazlardaki oturumlar düşer
                accsec.after_password_change(g.user["id"])                    # sess_ver artar + güvenlik bildirimi
                flash("Şifren değiştirildi. Diğer cihazlardaki oturumların kapatıldı.", "ok")
        return redirect(url_for("profile"))
    return render_template("profile.html", my_badges=services.user_badges(g.user))


# --------------------------------------------------------------------------- bloklar
from admin import bp as admin_bp  # noqa: E402
from api import bp as api_bp  # noqa: E402
from seller import bp as seller_bp  # noqa: E402
import doping  # noqa: E402,F401  (satıcı ve yönetici blueprint'lerine doping rotalarını ekler; kayıttan önce içe aktarılmalı)
import packages  # noqa: E402  (mağaza paketleri: seller/admin rotaları; blueprint kaydından önce yüklenmeli)

import community  # noqa: E402  (takip ve çekilişler: seller/admin blueprint'lerine rota ekler)
import storeplus  # noqa: E402  (mağaza adresi, vitrin, finans vb.: seller/admin blueprint'lerine rota ekler; kayıttan önce yüklenmeli)

packages.install(app)
storeplus.install(app)
community.install(app)
app.register_blueprint(seller_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(extras.bp)
accsec.install(app)       # CAPTCHA (/captcha/<kapsam>.png), form koruması, 2FA ve güvenlik rotaları
import trust  # noqa: E402

app.register_blueprint(trust.bp)
import paylink  # noqa: E402

app.register_blueprint(paylink.bp)
app.jinja_env.globals["REASONS"] = trust.REASONS
with app.app_context():                      # rota adıyla çakışan eski kullanıcı adlarına güvenli mağaza adresi ver
    try:
        storeplus.fix_reserved()
    except Exception as err:  # pragma: no cover
        print("itemal: mağaza adresi düzeltmesi atlandı:", err, flush=True)

import demo  # noqa: E402

if core.SERVERLESS:
    # arka plan iş parçacığı serverless'ta yok: demo veri, her sıcak işlevin ilk isteğinde (bir kez, kilitli) yüklenir
    app.demo_thread = None
    _demo_checked = {"done": False}

    @app.before_request
    def _lazy_demo_seed():
        if _demo_checked["done"] or os.getenv("AUTO_DEMO", "1") != "1":
            return
        _demo_checked["done"] = True
        try:
            demo.autoseed()
        except Exception as err:  # pragma: no cover
            print("itemal: demo veri yüklenemedi:", err, flush=True)
else:
    app.demo_thread = demo.start_autoseed(app)

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("DEBUG") == "1",
    )

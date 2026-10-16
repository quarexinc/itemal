"""Mağaza+: özel mağaza adresi, vitrin özelleştirme, tatil modu, otomatik karşılama, satış hedefi, müşteri listesi,
toplu ilan işlemleri (satıcı) ile mağaza yönetimi, finans/kasa raporu, canlı akış ve toplu ilan işlemleri (yönetim).

Mağaza adresi: alanadi/<adres>. Satıcı adres seçmezse kullanıcı adı geçerlidir. /magaza/<kullanıcı_adı> eski biçimi
kalıcı yönlendirmeyle yeni adrese gider. Eski adres 30 gün boyunca yönlendirilir ve başkasına verilmez.
Satıcı paneli:  seller.showcase, seller.customers, seller.customers_csv, seller.bulk, seller.listing_copy
Yönetim paneli: admin.stores, admin.store_action, admin.finance, admin.feed, admin.bulk_listings
"""
import csv
import io
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import Response, abort, current_app, flash, g, redirect, render_template, request, session, url_for

import core
import services
import storage as media_store
from admin import bp as admin_bp
from core import BizError, ex, field, q, q1
from seller import bp as seller_bp

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,29}$")
COOLDOWN_DAYS = 7
HISTORY_DAYS = 30
BLOCKED_WORDS = ("admin", "itemal", "destek", "yetkili", "moderator", "resmi", "support", "official")
RESERVED_EXTRA = {
    "admin", "yonetim", "yonetici", "satici", "api", "static", "media", "captcha", "magaza", "magazalar", "ilan", "ilanlar",
    "giris", "kayit", "cikis", "hesabim", "profil", "bakiye", "cekim", "siparis", "siparislerim", "hareketler", "mesajlar",
    "destek", "sss", "kimlik", "bildirimler", "favoriler", "sepet", "odeme", "kategori", "kategoriler", "arama", "ara",
    "hakkimizda", "iletisim", "gizlilik", "kullanim-sartlari", "robots.txt", "sitemap.xml", "favicon.ico", "cron", "health",
    "www", "mail", "ftp", "itemal", "login", "logout", "register", "support", "help", "about", "contact", "null", "undefined",
}

THEMES = {
    "": ("Mor (varsayılan)", "#7c5cff"),
    "mavi": ("Mavi", "#2f7bff"),
    "turkuaz": ("Turkuaz", "#0ea5b7"),
    "yesil": ("Yeşil", "#16a34a"),
    "altin": ("Altın", "#d9a406"),
    "turuncu": ("Turuncu", "#f97316"),
    "kirmizi": ("Kırmızı", "#ef4444"),
    "pembe": ("Pembe", "#ec4899"),
    "grafit": ("Grafit", "#64748b"),
}

# Ücretsiz temalar; diğerleri Premium Vitrin / Elmas paketi ya da altın-elmas kademesi ister.
FREE_THEMES = ("", "mavi", "yesil")
_reserved_cache = None


# --------------------------------------------------------------------------- adres kuralları
def reserved():
    """Kök dizinde zaten kullanılan ilk yol parçaları + sabit yasak liste (rota tablosundan bir kez hesaplanır)."""
    global _reserved_cache
    if _reserved_cache is None:
        names = set(RESERVED_EXTRA)
        for rule in current_app.url_map.iter_rules():
            seg = rule.rule.lstrip("/").split("/")[0].lower()
            if seg and not seg.startswith("<"):
                names.add(seg)
        _reserved_cache = names
    return _reserved_cache


def is_reserved(name):
    return (name or "").lower() in reserved()


def slug_error(raw, uid):
    """Adres uygunsa (küçük harfli adres, None), değilse (None, Türkçe hata) döner."""
    slug = (raw or "").strip().lower().lstrip("/")
    if not SLUG_RE.match(slug):
        return None, "Adres 3-30 karakter olmalı; yalnızca harf, rakam, tire ve alt çizgi kullan ve harf ya da rakamla başla."
    own = q1("SELECT username FROM users WHERE id = ?", (uid,))
    own_name = (own["username"] if own else "").lower()
    if slug != own_name:
        if slug in reserved():
            return None, "Bu adres sistem için ayrılmış. Başka bir ad dene."
        if any(w in slug for w in BLOCKED_WORDS):
            return None, "Yönetimi ya da sitenin kendisini çağrıştıran adresler kullanılamaz."
    if q1("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE AND id != ?", (slug, uid)):
        return None, "Bu adres başka bir kullanıcıya ait."
    if q1("SELECT 1 FROM users WHERE store_slug = ? COLLATE NOCASE AND id != ?", (slug, uid)):
        return None, "Bu adres başka bir mağaza tarafından kullanılıyor."
    if q1(
        "SELECT 1 FROM store_slug_history WHERE slug = ? COLLATE NOCASE AND user_id != ? AND changed_at >= datetime('now', ?)",
        (slug, uid, f"-{HISTORY_DAYS} days"),
    ):
        return None, f"Bu adres yakın zamanda başka bir mağazadaydı; {HISTORY_DAYS} gün sonra yeniden alınabilir."
    return slug, None


def cooldown_left(user):
    """Adres değiştirmek için kalan gün (0: değiştirilebilir)."""
    raw = user["slug_changed_at"]
    if not raw:
        return 0
    try:
        when = datetime.strptime(str(raw)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return 0
    left = when + timedelta(days=COOLDOWN_DAYS) - core.utcnow()
    return max(0, -(-left.total_seconds() // 86400)) if left.total_seconds() > 0 else 0


def fee_name():
    return core.setting_kurus("fee_store_name", 20000)


def fee_slug():
    return core.setting_kurus("fee_store_slug", 30000)


def slug_fee_due(user):
    """Adres değişikliği ücretli mi? İlk belirleme ücretsiz; daha önce adresi olan (ya da değiştirmiş) satıcı öder."""
    if (user["store_slug"] or "") or q1("SELECT 1 FROM store_slug_history WHERE user_id = ?", (user["id"],)):
        return fee_slug()
    return 0


def name_fee_due(user):
    return fee_name() if (user["store_name"] or "").strip() else 0


def charge_fee(uid, amount, description):
    """Bakiyeden ücret keser (core.tx() içinde çağır). Yetersizse BizError."""
    if amount <= 0:
        return
    row = q1("SELECT balance FROM users WHERE id = ?", (uid,))
    if not row or row["balance"] < amount:
        raise BizError(f"Bakiyen yetersiz. Bu işlem {core.fmt_money(amount)} tutarındadır; önce bakiye yükle.")
    core.change_balance(uid, -amount, "store_fee", description)


def set_slug(user, raw, by_admin=False):
    """Mağaza adresini ayarlar. Boş değer ya da kullanıcı adının kendisi: varsayılana (kullanıcı adı) dönüş."""
    uid = user["id"]
    raw = (raw or "").strip().lower().lstrip("/")
    cur = (user["store_slug"] or "").lower()
    if not raw or raw == (user["username"] or "").lower():
        new = ""
    else:
        new, err = slug_error(raw, uid)
        if err:
            raise BizError(err)
    if new == cur:
        return False
    if not by_admin:
        left = cooldown_left(user)
        if left:
            raise BizError(f"Mağaza adresini en sık {COOLDOWN_DAYS} günde bir değiştirebilirsin. {int(left)} gün sonra tekrar dene.")
    fee = 0 if by_admin else slug_fee_due(user)
    with core.tx():
        charge_fee(uid, fee, "Mağaza adresi değişikliği")
        if cur:
            ex("INSERT INTO store_slug_history(user_id, slug) VALUES (?,?)", (uid, cur))
        if new:
            ex("DELETE FROM store_slug_history WHERE user_id = ? AND slug = ? COLLATE NOCASE", (uid, new))
        ex("UPDATE users SET store_slug = ?, slug_changed_at = datetime('now') WHERE id = ?", (new, uid))
    return True


def username_blocked(name):
    """Kayıtta kullanıcı adı: ayrılmış kelime ya da başkasının mağaza adresi olamaz. Hata metni ya da None."""
    n = (name or "").lower()
    if n in reserved():
        return "Bu kullanıcı adı kullanılamaz. Başka bir ad seç."
    if q1("SELECT 1 FROM users WHERE store_slug = ? COLLATE NOCASE", (n,)):
        return "Bu kullanıcı adı kullanılamaz. Başka bir ad seç."
    if q1("SELECT 1 FROM store_slug_history WHERE slug = ? COLLATE NOCASE AND changed_at >= datetime('now', ?)", (n, f"-{HISTORY_DAYS} days")):
        return "Bu kullanıcı adı kullanılamaz. Başka bir ad seç."
    return None


def store_path(user):
    return url_for("storefront", username=user["username"])


def store_url(user):
    return url_for("storefront", username=user["username"], _external=True)


def fix_reserved():
    """Kullanıcı adı rota adıyla çakışan hesaplara (eski kayıtlar) güvenli bir mağaza adresi verir. Yalnızca bir kez, sessizce."""
    rows = q("SELECT id, username FROM users WHERE store_slug = ''")
    names = reserved()
    for r in rows:
        if r["username"].lower() in names:
            base = (r["username"].lower() + "-magaza")[:30]
            cand, n = base, 1
            while q1("SELECT 1 FROM users WHERE (store_slug = ? COLLATE NOCASE OR username = ? COLLATE NOCASE) AND id != ?", (cand, cand, r["id"])):
                n += 1
                cand = f"{base[:27]}-{n}"
            ex("UPDATE users SET store_slug = ? WHERE id = ?", (cand, r["id"]))


# --------------------------------------------------------------------------- herkese açık mağaza sayfası
def _slug_map():
    try:
        m = g.get("slug_map")
        if m is None:
            m = {r["username"].lower(): r["store_slug"] for r in q("SELECT username, store_slug FROM users WHERE store_slug <> ''")}
            g.slug_map = m
        return m
    except RuntimeError:                      # uygulama bağlamı yok (betik, test)
        return {}


def resolve(name, render):
    """/<ad>: önce özel adres, sonra kullanıcı adı, sonra eski adres (yönlendirme). Yoksa 404."""
    seller = q1("SELECT * FROM users WHERE store_slug = ? COLLATE NOCASE AND store_slug <> ''", (name,))
    if seller:
        if not core.can_sell(seller):
            abort(404)
        if seller["store_slug"] != name:
            return redirect(store_path(seller), 301)
        return render(seller)
    user = q1("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (name,))
    if user and core.can_sell(user):
        if user["store_slug"] or user["username"] != name:
            return redirect(store_path(user), 301)
        return render(user)
    old = q1(
        "SELECT user_id FROM store_slug_history WHERE slug = ? COLLATE NOCASE AND changed_at >= datetime('now', ?) ORDER BY id DESC LIMIT 1",
        (name, f"-{HISTORY_DAYS} days"),
    )
    if old:
        target = q1("SELECT * FROM users WHERE id = ?", (old["user_id"],))
        if target and core.can_sell(target):
            return redirect(store_path(target), 301)
    abort(404)


def resolve_legacy(username, render):
    """/magaza/<kullanıcı_adı> ya da adres: yeni adrese kalıcı yönlendirme."""
    seller = q1("SELECT * FROM users WHERE username = ? COLLATE NOCASE OR store_slug = ? COLLATE NOCASE", (username, username))
    if not seller or not core.can_sell(seller):
        abort(404)
    return redirect(store_path(seller), 301)


def count_view(seller):
    """Mağaza sayfası görüntülemesi: sahibi, yönetici ve botlar sayılmaz; oturum başına mağaza başına bir kez."""
    if (g.user and g.user["id"] == seller["id"]) or session.get("admin"):
        return
    ua = (request.headers.get("User-Agent") or "").lower()
    if not ua or any(w in ua for w in ("bot", "spider", "crawl", "slurp", "preview", "curl", "python-requests")):
        return
    seen = session.get("svw") if isinstance(session.get("svw"), list) else []
    if seller["id"] in seen:
        return
    ex("UPDATE users SET store_views = store_views + 1 WHERE id = ?", (seller["id"],))
    session["svw"] = (seen + [seller["id"]])[-30:]


def _mix(hexc, other, t):
    a = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def theme_allowed(uid, key):
    if key in FREE_THEMES:
        return True
    try:
        import packages
        return packages.theme_unlocked(uid)
    except Exception:
        return False


def theme_style(key):
    """Mağaza sayfasının vurgu rengi için satır içi CSS değişkenleri ('' = varsayılan tema)."""
    if not key or key not in THEMES:
        return ""
    h = THEMES[key][1]
    r, gr, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    p2 = _mix(h, "#ffffff", .30)
    return (f"--p:{h};--p-h:{_mix(h, '#ffffff', .14)};--p-d:{_mix(h, '#000000', .25)};--p-2:{p2};--p-3:{_mix(h, '#ffffff', .6)};"
            f"--p-soft:rgba({r},{gr},{b},.16);--grad:linear-gradient(135deg,{h},{p2})")


def vacation_active(user):
    """Tatil modu açık ve süresi dolmamışsa True."""
    if not user["store_vacation"]:
        return False
    until = user["vacation_until"]
    return not until or str(until)[:19] > core.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def socials(user):
    out = []
    for key, label, icon in (("store_discord", "Discord", "message"), ("store_telegram", "Telegram", "send"),
                             ("store_instagram", "Instagram", "image"), ("store_web", "Web sitesi", "external")):
        if user[key]:
            out.append({"label": label, "url": user[key], "icon": icon})
    return out


def store_ctx(seller):
    """storefront.html için ek bağlam (tema, duyuru, tatil, sosyal bağlantılar, adres)."""
    import community
    count_view(seller)
    vac = vacation_active(seller)
    return {
        **community.store_extra(seller),
        "theme_css": theme_style(seller["store_theme"] if theme_allowed(seller["id"], seller["store_theme"] or "") else ""),
        "vacation": vac,
        "vacation_until": seller["vacation_until"] if vac else None,
        "socials": socials(seller),
        "store_link": store_url(seller),
    }


def auto_reply_on_start(cid, seller_id):
    """Yeni konuşmada satıcının otomatik karşılama mesajını (varsa) ekler."""
    row = q1("SELECT auto_reply FROM users WHERE id = ?", (seller_id,))
    if row and row["auto_reply"]:
        ex("INSERT INTO messages(conversation_id, sender_id, body) VALUES (?,?,?)", (cid, seller_id, row["auto_reply"]))
        ex("UPDATE conversations SET last_message_at = datetime('now') WHERE id = ?", (cid,))


def restock_listing(lid):
    """Demo ilanın stoğu azalınca kendiliğinden doldurur (demo ilanlar satın alınabilir; vitrin boş görünmez)."""
    import demo
    left = q1("SELECT COUNT(*) AS n FROM listing_codes WHERE listing_id = ? AND is_sold = 0", (lid,))["n"]
    if left < 4:
        for _ in range(14):
            ex("INSERT OR IGNORE INTO listing_codes(listing_id, code) VALUES (?,?)", (lid, demo._code()))


# --------------------------------------------------------------------------- bağlantı doğrulama
def _clean_social(kind, raw):
    v = (raw or "").strip()
    if not v:
        return ""
    if kind == "discord":
        m = re.match(r"^(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([A-Za-z0-9-]{2,32})/?$", v, re.I) or re.fullmatch(r"([A-Za-z0-9-]{2,32})", v)
        if not m:
            raise BizError("Discord için davet bağlantısını gir (örnek: discord.gg/davetkodu).")
        return "https://discord.gg/" + m.group(1)
    if kind == "telegram":
        m = re.match(r"^(?:https?://)?(?:www\.)?(?:t|telegram)\.me/([A-Za-z0-9_]{4,32})/?$", v, re.I) or re.fullmatch(r"@?([A-Za-z0-9_]{4,32})", v)
        if not m:
            raise BizError("Telegram için kullanıcı adını gir (örnek: @magazam).")
        return "https://t.me/" + m.group(1)
    if kind == "instagram":
        m = re.match(r"^(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9._]{1,30})/?$", v, re.I) or re.fullmatch(r"@?([A-Za-z0-9._]{1,30})", v)
        if not m:
            raise BizError("Instagram için kullanıcı adını gir (örnek: @magazam).")
        return "https://instagram.com/" + m.group(1)
    u = urlparse(v if "://" in v else "https://" + v)
    if u.scheme not in ("http", "https") or "." not in (u.hostname or "") or u.username or u.password or len(v) > 120 or re.search(r"\s", v):
        raise BizError("Web sitesi adresi geçerli değil (örnek: https://siteadi.com).")
    return u.geturl()


def _end_of_day_utc(day):
    """'YYYY-MM-DD' (Türkiye günü) -> o günün bitişi, UTC metni. Geçersizse BizError."""
    try:
        d = datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        raise BizError("Tatil bitiş tarihi geçerli değil.")
    end = d + timedelta(days=1) - core.TR_OFFSET
    if end <= core.utcnow():
        raise BizError("Tatil bitiş tarihi bugünden sonra olmalı.")
    if end > core.utcnow() + timedelta(days=60):
        raise BizError("Tatil en fazla 60 gün sürebilir.")
    return end.strftime("%Y-%m-%d %H:%M:%S")


def goal_progress(user):
    """Bu ayki net kazanç ve hedef ilerlemesi (hedef yoksa None)."""
    goal = int(user["sales_goal"] or 0)
    if goal <= 0:
        return None
    month_start = (core.utcnow() + core.TR_OFFSET).strftime("%Y-%m-01")
    got = q1(
        "SELECT COALESCE(SUM(seller_earning), 0) AS s, COALESCE(SUM(quantity), 0) AS n FROM orders"
        " WHERE seller_id = ? AND escrow_status != 'refunded' AND date(created_at, '+3 hours') >= ?",
        (user["id"], month_start),
    )
    now = core.utcnow() + core.TR_OFFSET
    nxt = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_left = max(0, (nxt - now).days)
    pct = min(100, int(got["s"] * 100 / goal))
    return {"goal": goal, "got": got["s"], "qty": got["n"], "pct": pct, "left": max(0, goal - got["s"]), "days_left": days_left,
            "done": got["s"] >= goal}


# --------------------------------------------------------------------------- satıcı: vitrin ayarları
@seller_bp.route("/vitrin", methods=["GET", "POST"])
def showcase():
    u = g.user
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "slug":
                paid = slug_fee_due(u)
                changed = set_slug(u, request.form.get("slug", ""))
                flash(("Mağaza adresin güncellendi." + (f" {core.fmt_money(paid)} bakiyenden düşüldü." if paid else "")) if changed else "Adres zaten bu şekilde.", "ok" if changed else "info")
            elif action == "look":
                theme = request.form.get("theme", u["store_theme"] or "")
                if theme not in THEMES:
                    raise BizError("Geçerli bir tema seç.")
                if theme != (u["store_theme"] or "") and not theme_allowed(u["id"], theme):
                    raise BizError("Bu tema Premium Vitrin ya da Elmas paketi gerektirir. Paketler sayfasından açabilirsin.")
                notice = field("notice", 140)
                ex(
                    "UPDATE users SET store_theme = ?, store_notice = ?, store_discord = ?, store_telegram = ?, store_instagram = ?, store_web = ? WHERE id = ?",
                    (theme, notice, _clean_social("discord", request.form.get("discord")), _clean_social("telegram", request.form.get("telegram")),
                     _clean_social("instagram", request.form.get("instagram")), _clean_social("web", request.form.get("web")), u["id"]),
                )
                flash("Vitrin görünümün kaydedildi.", "ok")
            elif action == "vacation_on":
                until = ""
                day = (request.form.get("until") or "").strip()
                if day:
                    until = _end_of_day_utc(day)
                ex("UPDATE users SET store_vacation = 1, vacation_until = ? WHERE id = ?", (until or None, u["id"]))
                flash("Tatil modu açıldı. Mağazan yeni sipariş almaz, ilanların görünmeye devam eder.", "ok")
            elif action == "vacation_off":
                ex("UPDATE users SET store_vacation = 0, vacation_until = NULL WHERE id = ?", (u["id"],))
                flash("Tatil modu kapatıldı. Mağazan yeniden sipariş alıyor.", "ok")
            elif action == "reply":
                ex("UPDATE users SET auto_reply = ? WHERE id = ?", (field("auto_reply", 400), u["id"]))
                flash("Otomatik karşılama mesajı kaydedildi.", "ok")
            elif action == "goal":
                raw = (request.form.get("goal") or "").strip()
                kurus = 0
                if raw:
                    kurus = core.to_kurus(raw)
                    if kurus is None or not 10000 <= kurus <= 100_000_000:
                        raise BizError("Hedef 100 ₺ ile 1.000.000 ₺ arasında olmalı. Boş bırakırsan hedef kaldırılır.")
                ex("UPDATE users SET sales_goal = ? WHERE id = ?", (kurus, u["id"]))
                flash("Aylık hedefin kaydedildi." if kurus else "Aylık hedef kaldırıldı.", "ok")
            else:
                abort(400)
        except BizError as err:
            flash(str(err), "bad")
        return redirect(url_for("seller.showcase"))
    me = q1("SELECT * FROM users WHERE id = ?", (u["id"],))
    return render_template(
        "seller_showcase.html", slug_fee=slug_fee_due(me), fee_slug_amount=fee_slug(), balance=me["balance"], u=me, themes=THEMES, free_themes=FREE_THEMES, themes_open=theme_allowed(u["id"], "x"), link=store_url(me), path=store_path(me), cool=cooldown_left(me),
        vac=vacation_active(me), goal=goal_progress(me), history=q("SELECT slug, changed_at FROM store_slug_history WHERE user_id = ? ORDER BY id DESC LIMIT 5", (u["id"],)),
        host=request.host,
    )


@seller_bp.route("/vitrin/qr.svg")
def showcase_qr():
    """Mağaza adresinin QR kodu (afiş, kartvizit ve sosyal medya için)."""
    import segno
    buf = io.BytesIO()
    segno.make(store_url(g.user), error="m").save(buf, kind="svg", scale=8, border=2, dark="#1a1140", light="#ffffff", xmldecl=False, svgns=True)
    return Response(buf.getvalue(), mimetype="image/svg+xml", headers={"Cache-Control": "private, max-age=300"})


# --------------------------------------------------------------------------- satıcı: müşteriler
CUSTOMER_SORTS = {"son": ("Son alışveriş", "last_at DESC"), "harcama": ("En çok harcayan", "spent DESC"), "adet": ("En sık alan", "orders DESC, spent DESC")}


def _customers(uid, sort, text):
    where, args = "o.seller_id = ? AND o.escrow_status != 'refunded'", [uid]
    if text:
        where += " AND u.username LIKE ? ESCAPE '\\'"
        args.append("%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    return (
        "SELECT u.id, u.username, u.avatar, COUNT(o.id) AS orders, COALESCE(SUM(o.quantity), 0) AS qty,"
        " COALESCE(SUM(o.total - o.discount), 0) AS spent, MAX(o.created_at) AS last_at, MIN(o.created_at) AS first_at"
        " FROM orders o JOIN users u ON u.id = o.buyer_id WHERE " + where + " GROUP BY u.id ORDER BY " + CUSTOMER_SORTS[sort][1],
        args,
    )


@seller_bp.route("/musteriler")
def customers():
    sort = request.args.get("sirala", "son")
    if sort not in CUSTOMER_SORTS:
        sort = "son"
    text = request.args.get("q", "").strip()[:30]
    sql, args = _customers(g.user["id"], sort, text)
    page = core.paginate(sql, args, 20)
    sums = q1(
        "SELECT COUNT(*) AS n, COALESCE(SUM(CASE WHEN c >= 2 THEN 1 ELSE 0 END), 0) AS repeat, COALESCE(SUM(s), 0) AS spent, COALESCE(SUM(c), 0) AS orders"
        " FROM (SELECT COUNT(*) AS c, SUM(total - discount) AS s FROM orders WHERE seller_id = ? AND escrow_status != 'refunded' GROUP BY buyer_id)",
        (g.user["id"],),
    )
    return render_template("seller_customers.html", page=page, sort=sort, sorts=CUSTOMER_SORTS, text=text, sums=sums)


@seller_bp.route("/musteriler.csv")
def customers_csv():
    sql, args = _customers(g.user["id"], "son", "")
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(["Kullanici", "Siparis", "Adet", "Toplam harcama (TL)", "Ilk alisveris", "Son alisveris"])
    for r in q(sql + " LIMIT 5000", args):
        w.writerow([r["username"], r["orders"], r["qty"], f"{r['spent'] / 100:.2f}".replace(".", ","), core.fmt_dt(r["first_at"]), core.fmt_dt(r["last_at"])])
    return Response("﻿" + out.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=musteriler.csv"})


# --------------------------------------------------------------------------- satıcı: toplu işlemler ve kopyalama
@seller_bp.post("/ilanlar/toplu")
def bulk():
    ids = [i for i in request.form.getlist("ids", type=int) if i > 0][:200]
    action = request.form.get("action", "")
    if not ids:
        flash("Önce işlem yapılacak ilanları işaretle.", "bad")
        return redirect(request.referrer or url_for("seller.listings"))
    marks = ",".join("?" * len(ids))
    rows = q(f"SELECT * FROM listings WHERE seller_id = ? AND status != 'removed' AND id IN ({marks})", (g.user["id"], *ids))
    if not rows:
        abort(404)
    done = 0
    try:
        with core.tx():
            if action in ("pause", "activate"):
                src, dst = ("active", "paused") if action == "pause" else ("paused", "active")
                for r in rows:
                    if r["status"] == src:
                        ex("UPDATE listings SET status = ?, updated_at = datetime('now') WHERE id = ?", (dst, r["id"]))
                        done += 1
                msg = f"{done} ilan {'duraklatıldı' if action == 'pause' else 'yayına alındı'}."
            elif action == "delete":
                for r in rows:
                    ex("UPDATE listings SET status = 'removed', updated_at = datetime('now') WHERE id = ?", (r["id"],))
                    done += 1
                msg = f"{done} ilan silindi. Geçmiş siparişler korunur."
            elif action == "price":
                try:
                    pct = float((request.form.get("pct") or "").replace(",", "."))
                except ValueError:
                    raise BizError("Yüzde değerini sayı olarak gir (örnek: 10 ya da -5).")
                if not -50 <= pct <= 100 or abs(pct) < 0.1:
                    raise BizError("Yüzde -50 ile +100 arasında olmalı.")
                for r in rows:
                    if r["status"] == "blocked":
                        continue
                    new = int(round(r["price"] * (1 + pct / 100) / 10.0)) * 10          # 10 kuruşa yuvarla
                    new = min(max(new, 100), 10_000_000)
                    old = r["old_price"] if r["old_price"] and r["old_price"] > new and r["old_price"] <= new * 5 else 0
                    ex("UPDATE listings SET price = ?, old_price = ?, is_deal = CASE WHEN ? > 0 THEN is_deal ELSE 0 END, updated_at = datetime('now') WHERE id = ?",
                       (new, old, old, r["id"]))
                    done += 1
                msg = f"{done} ilanın fiyatı %{str(pct).replace('.', ',').rstrip('0').rstrip(',')} değiştirildi."
            else:
                abort(400)
    except BizError as err:
        flash(str(err), "bad")
        return redirect(request.referrer or url_for("seller.listings"))
    flash(msg if done else "İşaretlediğin ilanlarda bu işlem uygulanamadı.", "ok" if done else "info")
    return redirect(request.referrer or url_for("seller.listings"))


@seller_bp.post("/ilan/<int:lid>/kopyala")
def listing_copy(lid):
    item = q1("SELECT * FROM listings WHERE id = ? AND seller_id = ? AND status != 'removed'", (lid, g.user["id"]))
    if not item:
        abort(404)
    if core.rate_hit("copy", 30, 3600, key=f"u{g.user['id']}"):
        flash("Kısa sürede çok fazla ilan kopyaladın. Biraz bekle.", "bad")
        return redirect(url_for("seller.listings"))
    cover = ""
    if item["cover"]:
        import uuid
        main = media_store.get("cover", item["cover"])
        thumb = media_store.get("cover", "t_" + item["cover"])
        if main:
            cover = uuid.uuid4().hex + ".webp"
            media_store.put("cover", cover, main[1], main[0])
            if thumb:
                media_store.put("cover", "t_" + cover, thumb[1], thumb[0])
    title = item["title"]
    title = (title if title.endswith(" (kopya)") else title[:82] + " (kopya)")[:90]
    cur = ex(
        "INSERT INTO listings(seller_id, category_id, title, description, cover, price, old_price, status) VALUES (?,?,?,?,?,?,?, 'paused')",
        (g.user["id"], item["category_id"], title, item["description"], cover, item["price"], item["old_price"]),
    )
    flash("İlan kopyalandı. Kopya duraklatılmış durumda; kod ekleyip yayına alabilirsin.", "ok")
    return redirect(url_for("seller.stock", lid=cur.lastrowid))


# --------------------------------------------------------------------------- yönetim: mağazalar
STORE_SORTS = {"satis": ("Satışa göre", "sold DESC"), "ziyaret": ("Ziyarete göre", "u.store_views DESC"), "yeni": ("En yeni", "u.id DESC"),
               "ilan": ("İlan sayısına göre", "listings DESC")}


@admin_bp.route("/magazalar")
def stores():
    sort = request.args.get("sirala", "satis")
    if sort not in STORE_SORTS:
        sort = "satis"
    text = request.args.get("q", "").strip()[:40]
    where, args = ["u.is_seller = 1"], []
    if text:
        where.append("(u.username LIKE ? ESCAPE '\\' OR u.store_name LIKE ? ESCAPE '\\' OR u.store_slug LIKE ? ESCAPE '\\')")
        like = "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        args += [like] * 3
    flt = request.args.get("durum", "")
    if flt == "tatil":
        where.append("u.store_vacation = 1")
    elif flt == "adresli":
        where.append("u.store_slug <> ''")
    elif flt == "demo":
        where.append("u.is_demo = 1")
    elif flt == "gercek":
        where.append("u.is_demo = 0")
    sql = (
        "SELECT u.id, u.username, u.store_name, u.store_slug, u.store_views, u.store_vacation, u.vacation_until, u.is_banned, u.is_demo,"
        " (SELECT COUNT(*) FROM listings l WHERE l.seller_id = u.id AND l.status = 'active') AS listings,"
        " (SELECT COALESCE(SUM(quantity), 0) FROM orders o WHERE o.seller_id = u.id AND o.escrow_status != 'refunded') + u.demo_sold AS sold,"
        " (SELECT COALESCE(SUM(total), 0) FROM orders o WHERE o.seller_id = u.id AND o.escrow_status != 'refunded' AND o.created_at >= datetime('now','-30 days')) AS gmv30"
        " FROM users u WHERE " + " AND ".join(where) + " ORDER BY " + STORE_SORTS[sort][1] + ", u.id DESC"
    )
    page = core.paginate(sql, args, 25)
    kpi = q1(
        "SELECT COUNT(*) AS n, COALESCE(SUM(store_slug <> ''), 0) AS custom, COALESCE(SUM(store_vacation = 1), 0) AS vac,"
        " COALESCE(SUM(store_views), 0) AS views FROM users WHERE is_seller = 1"
    )
    return render_template("admin_stores.html", page=page, sort=sort, sorts=STORE_SORTS, text=text, flt=flt, kpi=kpi, vacation_active=vacation_active)


@admin_bp.post("/magaza/<int:uid>/islem")
def store_action(uid):
    u = q1("SELECT * FROM users WHERE id = ? AND is_seller = 1", (uid,))
    if not u:
        abort(404)
    action = request.form.get("action", "")
    try:
        if action == "slug":
            changed = set_slug(u, request.form.get("slug", ""), by_admin=True)
            core.log_admin("Mağaza adresi", f"{u['username']} -> {(request.form.get('slug') or '').strip().lower() or 'varsayılan'}")
            flash("Mağaza adresi güncellendi." if changed else "Adres zaten bu şekilde.", "ok" if changed else "info")
        elif action == "vacation_off":
            ex("UPDATE users SET store_vacation = 0, vacation_until = NULL WHERE id = ?", (uid,))
            core.log_admin("Tatil modu kapatıldı", u["username"])
            flash("Tatil modu kapatıldı.", "ok")
        elif action == "reset_notice":
            ex("UPDATE users SET store_notice = '', store_discord = '', store_telegram = '', store_instagram = '', store_web = '' WHERE id = ?", (uid,))
            core.log_admin("Vitrin içeriği sıfırlandı", u["username"])
            flash("Mağaza duyurusu ve bağlantıları temizlendi.", "ok")
        else:
            abort(400)
    except BizError as err:
        flash(str(err), "bad")
    return redirect(request.referrer or url_for("admin.stores"))


# --------------------------------------------------------------------------- yönetim: finans / kasa
FIN_RANGES = {7: "7 gün", 30: "30 gün", 90: "90 gün", 365: "1 yıl"}


@admin_bp.route("/finans")
def finance():
    days = request.args.get("gun", 30, type=int)
    if days not in FIN_RANGES:
        days = 30
    since = f"-{days} days"
    rev = q1(
        "SELECT"
        " (SELECT COALESCE(SUM(commission), 0) FROM orders WHERE escrow_status != 'refunded' AND created_at >= datetime('now', ?)) AS commission,"
        " (SELECT COALESCE(SUM(fee), 0) FROM withdrawals WHERE status = 'approved' AND created_at >= datetime('now', ?)) AS wd_fee,"
        " (SELECT COALESCE(SUM(price), 0) FROM listing_dopings WHERE created_at >= datetime('now', ?)) AS doping,"
        " (SELECT COALESCE(SUM(price), 0) FROM user_packages WHERE source = 'buy' AND created_at >= datetime('now', ?)) AS packages,"
        " (SELECT COALESCE(SUM(discount), 0) FROM orders WHERE escrow_status != 'refunded' AND created_at >= datetime('now', ?)) AS coupons,"
        " (SELECT COALESCE(SUM(total), 0) FROM orders WHERE escrow_status != 'refunded' AND created_at >= datetime('now', ?)) AS gmv,"
        " (SELECT COUNT(*) FROM orders WHERE escrow_status != 'refunded' AND created_at >= datetime('now', ?)) AS orders",
        (since,) * 7,
    )
    revenue = rev["commission"] + rev["wd_fee"] + rev["doping"] + rev["packages"]
    net_revenue = revenue - rev["coupons"]
    # kasa: nakit girişi/çıkışı ve yükümlülükler (tüm zamanlar)
    cash = q1(
        "SELECT (SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE status = 'approved') AS cash_in,"
        " (SELECT COALESCE(SUM(net), 0) FROM withdrawals WHERE status = 'approved') AS cash_out,"
        " (SELECT COALESCE(SUM(balance), 0) FROM users WHERE is_demo = 0) AS balances,"
        " (SELECT COALESCE(SUM(balance), 0) FROM users WHERE is_demo = 1) AS demo_balances,"
        " (SELECT COALESCE(SUM(seller_earning), 0) FROM orders WHERE escrow_status IN ('held', 'disputed')) AS held,"
        " (SELECT COALESCE(SUM(amount), 0) FROM withdrawals WHERE status = 'pending') AS pending_wd,"
        " (SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE status = 'pending') AS pending_dep,"
        " (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE kind IN ('admin', 'bonus')) AS adjustments"
    )
    liabilities = cash["balances"] + cash["held"] + cash["pending_wd"]
    net_cash = cash["cash_in"] - cash["cash_out"]
    est_profit = net_cash - liabilities + cash["adjustments"]
    series = core.daily_series(
        "SELECT d, SUM(v) AS v FROM ("
        " SELECT date(created_at,'+3 hours') AS d, commission AS v FROM orders WHERE escrow_status != 'refunded' AND created_at >= datetime('now', ?)"
        " UNION ALL SELECT date(created_at,'+3 hours'), price FROM listing_dopings WHERE created_at >= datetime('now', ?)"
        " UNION ALL SELECT date(created_at,'+3 hours'), price FROM user_packages WHERE source = 'buy' AND created_at >= datetime('now', ?)"
        " UNION ALL SELECT date(created_at,'+3 hours'), fee FROM withdrawals WHERE status = 'approved' AND created_at >= datetime('now', ?)"
        ") GROUP BY d", (since,) * 4, min(days, 60),
    )
    flow = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, SUM(amount) AS v FROM deposits WHERE status = 'approved' AND created_at >= datetime('now', ?) GROUP BY d",
        (since,), min(days, 60),
    )
    top_stores = q(
        "SELECT u.id, u.username, u.store_name, COUNT(o.id) AS orders, SUM(o.total) AS gmv, SUM(o.commission) AS fee FROM orders o"
        " JOIN users u ON u.id = o.seller_id WHERE o.escrow_status != 'refunded' AND o.created_at >= datetime('now', ?) GROUP BY u.id ORDER BY fee DESC LIMIT 8",
        (since,),
    )
    big = q(
        "SELECT t.id, t.created_at, t.kind, t.amount, t.description, u.username, u.id AS uid FROM transactions t JOIN users u ON u.id = t.user_id"
        " WHERE ABS(t.amount) >= 500000 AND t.created_at >= datetime('now', ?) ORDER BY t.id DESC LIMIT 10",
        (since,),
    )
    return render_template(
        "admin_finance.html", days=days, ranges=FIN_RANGES, rev=rev, revenue=revenue, net_revenue=net_revenue, cash=cash,
        liabilities=liabilities, net_cash=net_cash, est_profit=est_profit, series=series, flow=flow, top_stores=top_stores, big=big,
    )


# --------------------------------------------------------------------------- yönetim: canlı akış
FEED_KINDS = {"": "Hepsi", "siparis": "Siparişler", "kayit": "Yeni üyeler", "para": "Para hareketleri", "destek": "Destek ve şikayet", "ilan": "İlanlar"}


@admin_bp.route("/akis")
def feed():
    kind = request.args.get("tur", "")
    if kind not in FEED_KINDS:
        kind = ""
    parts = []
    if kind in ("", "siparis"):
        parts.append(
            "SELECT o.created_at AS ts, 'siparis' AS kind, 'Sipariş #' || o.id || ': ' || o.listing_title AS title,"
            " b.username || ' -> ' || s.username || ' (' || o.quantity || ' adet)' AS sub, o.total AS amount, '/siparis/' || o.id AS link"
            " FROM orders o JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id ORDER BY o.id DESC LIMIT 40"
        )
    if kind in ("", "kayit"):
        parts.append(
            "SELECT created_at AS ts, 'kayit' AS kind, 'Yeni üye: ' || username AS title, CASE WHEN is_seller = 1 THEN 'Satıcı' ELSE 'Alıcı' END AS sub, NULL AS amount, NULL AS link FROM users WHERE is_demo = 0 ORDER BY id DESC LIMIT 30"
        )
    if kind in ("", "para"):
        parts.append(
            "SELECT d.created_at AS ts, 'para' AS kind, 'Bakiye yükleme (' || d.status || ')' AS title, u.username || ' - ' || d.method_name AS sub, d.amount AS amount, NULL AS link FROM deposits d JOIN users u ON u.id = d.user_id ORDER BY d.id DESC LIMIT 30"
        )
        parts.append(
            "SELECT w.created_at AS ts, 'para' AS kind, 'Çekim talebi (' || w.status || ')' AS title, u.username || ' - ' || w.method AS sub, w.amount AS amount, NULL AS link FROM withdrawals w JOIN users u ON u.id = w.user_id ORDER BY w.id DESC LIMIT 30"
        )
    if kind in ("", "destek"):
        parts.append("SELECT t.created_at AS ts, 'destek' AS kind, 'Destek talebi: ' || t.subject AS title, u.username AS sub, NULL AS amount, NULL AS link FROM tickets t JOIN users u ON u.id = t.user_id ORDER BY t.id DESC LIMIT 30")
        parts.append("SELECT r.created_at AS ts, 'destek' AS kind, 'Şikayet: ' || r.kind AS title, r.reason AS sub, NULL AS amount, NULL AS link FROM reports r ORDER BY r.id DESC LIMIT 30")
    if kind in ("", "ilan"):
        parts.append(
            "SELECT l.created_at AS ts, 'ilan' AS kind, 'Yeni ilan: ' || l.title AS title, u.username AS sub, l.price AS amount, '/ilan/' || l.id AS link FROM listings l JOIN users u ON u.id = l.seller_id WHERE l.is_demo = 0 ORDER BY l.id DESC LIMIT 30"
        )
    sql = "SELECT * FROM (" + " UNION ALL ".join(f"SELECT * FROM ({p})" for p in parts) + ") ORDER BY ts DESC"
    rows = q(sql + " LIMIT 120")
    return render_template("admin_feed.html", rows=rows, kind=kind, kinds=FEED_KINDS)


# --------------------------------------------------------------------------- yönetim: toplu ilan işlemleri
@admin_bp.post("/ilanlar/toplu")
def bulk_listings():
    ids = [i for i in request.form.getlist("ids", type=int) if i > 0][:300]
    action = request.form.get("action", "")
    if action not in ("active", "paused", "blocked", "removed", "feature", "unfeature"):
        abort(400)
    if not ids:
        flash("Önce işlem yapılacak ilanları işaretle.", "bad")
        return redirect(request.referrer or url_for("admin.listings"))
    marks = ",".join("?" * len(ids))
    rows = q(f"SELECT id, title, seller_id FROM listings WHERE id IN ({marks})", ids)
    with core.tx():
        if action in ("feature", "unfeature"):
            ex(f"UPDATE listings SET is_featured = ? WHERE id IN ({marks})", (1 if action == "feature" else 0, *ids))
        else:
            ex(f"UPDATE listings SET status = ?, updated_at = datetime('now') WHERE id IN ({marks})", (action, *ids))
            if action in ("blocked", "removed"):
                for r in rows:
                    services.notify(r["seller_id"], "İlanın yayından kaldırıldı", f"{r['title'][:80]} yönetim tarafından {'engellendi' if action == 'blocked' else 'kaldırıldı'}.", url_for("seller.listings"))
    core.log_admin("Toplu ilan işlemi", f"{len(rows)} ilan -> {action}")
    flash(f"{len(rows)} ilan güncellendi.", "ok")
    return redirect(request.referrer or url_for("admin.listings"))


def install(app):
    """Şablon globalleri, url_defaults ve kapanışta çalışacak ilk kurulum."""
    app.jinja_env.globals.update(store_theme_css=theme_style, store_path=store_path, store_url=store_url, vacation_on=vacation_active, THEMES=THEMES)

    @app.url_defaults
    def _slug_defaults(endpoint, values):
        # url_for('storefront', username=X): X'in özel adresi varsa adres o olur
        if endpoint == "storefront" and values.get("username") is not None:
            slug = _slug_map().get(str(values["username"]).lower())
            if slug:
                values["username"] = slug

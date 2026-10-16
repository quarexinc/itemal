"""Vitrin ek özellikleri: arama önerisi, favoriler, bildirimler, kupon kontrolü, banner takibi, robots/sitemap
ve ana sayfa verileri."""
import re

from flask import Blueprint, Response, abort, g, jsonify, redirect, render_template, request, url_for

import core
import services
from core import BizError, ex, q, q1

bp = Blueprint("site", __name__)

PUBLIC_WHERE = " WHERE l.status = 'active' AND c.is_active = 1 AND u.is_banned = 0 "
GROUP_ORDER = ["PC & Konsol", "Mobil", "Uygulama & Abonelik", "Hediye Kartları"]


def _like(text):
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _pk_cols():
    import packages                    # geç içe aktarım: packages seller/admin blueprint'lerini yükler

    return packages.sql_cols("u.id")


def _cover(name, small=True):
    return url_for("media_cover_small" if small else "media_cover", name=name) if name else ""


# --------------------------------------------------------------------------- ana sayfa
def active_banners(slot):
    import doping  # noqa: E402  (doping.py seller/admin blueprint'lerini içe aktarır; döngüsel içe aktarmayı önlemek için yerel)

    now = core.utc_str()
    # satın alınan reklam bannerları (is_ad=1) yalnızca ilan hâlâ satışa açıksa (yayında, stoklu, satıcı yetkili) gösterilir
    rows = q(
        "SELECT b.*, l.title AS ad_title, l.price AS ad_price, COALESCE(NULLIF(u.store_name, ''), u.username) AS ad_store"
        " FROM banners b LEFT JOIN listings l ON l.id = b.listing_id"
        " LEFT JOIN categories c ON c.id = l.category_id LEFT JOIN users u ON u.id = l.seller_id"
        " WHERE b.slot = ? AND b.is_active = 1 AND (b.starts_at IS NULL OR b.starts_at <= ?)"
        " AND (b.ends_at IS NULL OR b.ends_at >= ?)"
        " AND (b.is_ad = 0 OR (l.id IS NOT NULL AND " + doping.public_cond() +
        " AND EXISTS (SELECT 1 FROM listing_dopings d WHERE d.banner_id = b.id AND " + doping.LIVE + ")"
        " AND EXISTS (SELECT 1 FROM listing_codes k WHERE k.listing_id = l.id AND k.is_sold = 0)))"
        " ORDER BY b.sort_order, b.id",
        (slot, now, now),
    )
    rows = [dict(r) for r in rows]
    for r in rows:
        if r["is_ad"]:       # reklam afişinde ilanın güncel başlığı ve fiyatı görünür
            r["title"] = r["ad_title"]
            r["subtitle"] = f"{r['ad_store']} | {core.fmt_money(r['ad_price'])}"
    if rows:
        ids = ",".join(str(r["id"]) for r in rows)
        ex(f"UPDATE banners SET views = views + 1 WHERE id IN ({ids})")
    return rows


def home_context():
    base = core.LISTING_SELECT + PUBLIC_WHERE
    categories = q(
        "SELECT c.*, (SELECT COUNT(*) FROM listings l WHERE l.category_id = c.id AND l.status = 'active') AS n,"
        " (SELECT MIN(l.price) FROM listings l WHERE l.category_id = c.id AND l.status = 'active') AS min_price"
        " FROM categories c WHERE c.is_active = 1 ORDER BY c.sort_order, c.id"
    )
    daily = [c for c in categories if c["is_daily"]]
    if not daily:
        daily = sorted(categories, key=lambda c: -c["n"])[:8]
    groups = [g_ for g_ in GROUP_ORDER if any(c["grp"] == g_ for c in categories)]
    groups += sorted({c["grp"] for c in categories if c["grp"] and c["grp"] not in GROUP_ORDER})
    deals = q(base + "AND l.is_deal = 1 ORDER BY (stock > 0) DESC, l.id DESC LIMIT 8")
    featured = q(base + "AND l.is_featured = 1 ORDER BY (stock > 0) DESC, l.id DESC LIMIT 4")
    latest = q(base + "ORDER BY (stock > 0) DESC, l.id DESC LIMIT 8")
    popular = q(base + "AND l.sales_count > 0 ORDER BY l.sales_count DESC, l.id DESC LIMIT 4")
    sellers = q(
        "SELECT u.*, COALESCE(SUM(l.sales_count), 0) AS sold, COUNT(l.id) AS n_listings,"
        " (SELECT COUNT(*) FROM reviews r WHERE r.seller_id = u.id AND r.is_hidden = 0) AS rc,"
        " (SELECT COALESCE(AVG(rating), 0) FROM reviews r WHERE r.seller_id = u.id AND r.is_hidden = 0) AS avg,"
        " " + _pk_cols() +
        " FROM users u JOIN listings l ON l.seller_id = u.id AND l.status = 'active'"
        " WHERE u.is_banned = 0 AND u.is_seller = 1 GROUP BY u.id ORDER BY sold DESC, avg DESC LIMIT 6"
    )
    seller_cards = [{"u": s, "badges": services.user_badges(s)[:2]} for s in sellers]
    reviews = q(
        "SELECT r.*, b.username AS buyer_name, l.title AS listing_title, l.id AS lid, s.username AS seller_name,"
        " COALESCE(NULLIF(s.store_name, ''), s.username) AS seller_display FROM reviews r"
        " JOIN users b ON b.id = r.buyer_id JOIN listings l ON l.id = r.listing_id JOIN users s ON s.id = r.seller_id"
        " WHERE r.is_hidden = 0 AND r.rating >= 4 AND length(r.comment) >= 12 ORDER BY r.id DESC LIMIT 6"
    )
    ticker = []
    if core.setting("home_ticker", "1") == "1":
        rows = q(
            "SELECT o.created_at, o.listing_title, o.quantity, b.username AS buyer FROM orders o"
            " JOIN users b ON b.id = o.buyer_id ORDER BY o.id DESC LIMIT 14"
        )
        ticker = [{"kind": "sale", "who": r["buyer"], "text": r["listing_title"], "at": r["created_at"], "qty": r["quantity"]} for r in rows]
        if len(ticker) < 5:
            for r in latest[:8]:
                ticker.append({"kind": "new", "who": r["seller_display"], "text": r["title"], "at": r["created_at"], "qty": 0, "uid": r["seller_id"]})
        if len(ticker) < 3:
            ticker = []
    stats = q1(
        "SELECT (SELECT COUNT(*) FROM users) AS users,"
        " (SELECT COUNT(*) FROM users WHERE is_seller = 1) AS sellers,"
        " ((SELECT COALESCE(SUM(quantity), 0) FROM orders) + (SELECT COALESCE(SUM(demo_sold), 0) FROM users)) AS sold,"
        " (SELECT COUNT(*) FROM listings WHERE status = 'active') AS listings"
    )
    return dict(
        hero=active_banners("hero"), strips=active_banners("strip"), categories=categories, daily=daily, groups=groups,
        deals=deals, featured=featured, latest=latest, popular=popular, seller_cards=seller_cards, reviews=reviews,
        ticker=ticker, stats=stats, left=core.seconds_to_midnight(),
    )


# --------------------------------------------------------------------------- arama önerisi
@bp.route("/ara/oner")
def search_suggest():
    text = request.args.get("q", "").strip()[:60]
    items = []
    if len(text) >= 2:
        for c in q(
            "SELECT c.*, (SELECT COUNT(*) FROM listings l WHERE l.category_id = c.id AND l.status = 'active') AS n"
            " FROM categories c WHERE c.is_active = 1 AND c.name LIKE ? ESCAPE '\\' ORDER BY n DESC LIMIT 3",
            (_like(text),),
        ):
            items.append({
                "title": c["name"], "meta": f"Kategori - {c['n']} ilan", "url": url_for("listings", kategori=c["slug"]),
                "color": c["color"] or "#7c5cff", "mono": services.mono(c["name"]), "cover": "",
            })
        for l in q(
            core.LISTING_SELECT + PUBLIC_WHERE + "AND l.title LIKE ? ESCAPE '\\' ORDER BY (stock > 0) DESC, l.sales_count DESC LIMIT 5",
            (_like(text),),
        ):
            items.append({
                "title": l["title"], "meta": f"{l['cat_name']} - {core.fmt_money(l['price'])}",
                "url": url_for("listing_detail", lid=l["id"]), "cover": _cover(l["cover"]),
                "color": l["cat_color"] or "#7c5cff", "mono": services.mono(l["cat_name"]),
            })
    return jsonify({"items": items})


# --------------------------------------------------------------------------- favoriler
@bp.post("/favori/<int:lid>")
def favorite_toggle(lid):
    if not g.user:
        return jsonify({"error": "login"}), 401
    item = q1("SELECT id FROM listings WHERE id = ? AND status = 'active'", (lid,))
    if not item:
        return jsonify({"error": "yok"}), 404
    uid = g.user["id"]
    if q1("SELECT 1 FROM favorites WHERE user_id = ? AND listing_id = ?", (uid, lid)):
        ex("DELETE FROM favorites WHERE user_id = ? AND listing_id = ?", (uid, lid))
        on = False
    else:
        ex("INSERT OR IGNORE INTO favorites(user_id, listing_id) VALUES (?,?)", (uid, lid))
        on = True
    count = q1("SELECT COUNT(*) AS n FROM favorites WHERE user_id = ?", (uid,))["n"]
    return jsonify({"on": on, "count": count})


@bp.route("/favorilerim")
@core.login_required
def favorites():
    page = core.paginate(
        core.LISTING_SELECT + " JOIN favorites f ON f.listing_id = l.id WHERE f.user_id = ? AND l.status = 'active'"
        " AND c.is_active = 1 AND u.is_banned = 0 ORDER BY f.created_at DESC",
        (g.user["id"],), 12,
    )
    return render_template("favorites.html", page=page)


# --------------------------------------------------------------------------- bildirimler
KIND_LABELS = {"ok": "Başarılı işlem", "bad": "Olumsuz sonuç", "warn": "Dikkat", "info": "Bilgi"}


def _kind_of(n):
    return n["kind"] or services.notif_kind(n["title"], n["body"])


@bp.route("/bildirimler")
@core.login_required
def notifications():
    flt = request.args.get("durum", "")
    where, args = "user_id = ?", [g.user["id"]]
    if flt == "okunmamis":
        where += " AND is_read = 0"
    elif flt in KIND_LABELS:
        where += " AND (kind = ? OR (kind = '' AND ? = 'info'))"
        args += [flt, flt]
    page = core.paginate("SELECT * FROM notifications WHERE " + where + " ORDER BY id DESC", args, 20)
    view = []
    for n in page["rows"]:
        d = dict(n)
        d["kind"] = _kind_of(n)
        view.append(d)
    unread = q1("SELECT COUNT(*) AS n FROM notifications WHERE user_id = ? AND is_read = 0", (g.user["id"],))["n"]
    return render_template("notifications.html", page=page, items=view, flt=flt, unread=unread, kinds=KIND_LABELS)


@bp.route("/bildirim/<int:nid>")
@core.login_required
def notif_view(nid):
    """Bildirim detayı: tam metin, durum rozeti, ilgili sipariş özeti ve ilgili sayfaya bağlantı."""
    n = q1("SELECT * FROM notifications WHERE id = ? AND user_id = ?", (nid, g.user["id"]))
    if not n:
        abort(404)
    if not n["is_read"]:
        ex("UPDATE notifications SET is_read = 1 WHERE id = ?", (nid,))
    kind = _kind_of(n)
    order = None
    m = re.match(r"^/siparis/(\d+)", n["link"] or "")
    if m:
        order = q1(
            "SELECT o.*, b.username AS buyer_name, s.username AS seller_name FROM orders o JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id"
            " WHERE o.id = ? AND (o.buyer_id = ? OR o.seller_id = ?)", (int(m.group(1)), g.user["id"], g.user["id"]),
        )
    prev_n = q1("SELECT id FROM notifications WHERE user_id = ? AND id > ? ORDER BY id LIMIT 1", (g.user["id"], nid))
    next_n = q1("SELECT id FROM notifications WHERE user_id = ? AND id < ? ORDER BY id DESC LIMIT 1", (g.user["id"], nid))
    return render_template("notification_view.html", n=n, kind=kind, label=KIND_LABELS[kind], order=order, prev_n=prev_n, next_n=next_n)


@bp.post("/bildirimler/hepsi-okundu")
@core.login_required
def notif_read_all():
    ex("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (g.user["id"],))
    return redirect(request.referrer or url_for("site.notifications"))


@bp.post("/bildirim/<int:nid>/sil")
@core.login_required
def notif_delete(nid):
    ex("DELETE FROM notifications WHERE id = ? AND user_id = ?", (nid, g.user["id"]))
    return redirect(url_for("site.notifications"))


@bp.post("/bildirim/okundu")
@core.login_required
def notif_read():
    ex("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (g.user["id"],))
    return jsonify({"ok": True})


# --------------------------------------------------------------------------- kupon kontrolü
@bp.route("/kupon/kontrol/<int:lid>")
def coupon_check(lid):
    if not g.user:
        return jsonify({"ok": False, "msg": "Kupon kullanmak için giriş yapmalısın.", "discount": 0})
    if core.rate_hit("coupon", 40, 600, key=f"u{g.user['id']}"):          # kupon kodu tahminini yavaşlatır
        return jsonify({"ok": False, "msg": "Çok fazla kupon denemesi. Biraz bekle.", "discount": 0}), 429
    item = q1("SELECT * FROM listings WHERE id = ? AND status = 'active'", (lid,))
    if not item:
        return jsonify({"ok": False, "msg": "İlan bulunamadı.", "discount": 0})
    qty = max(1, min(request.args.get("qty", 1, type=int) or 1, core.setting_int("max_qty_per_order", 10)))
    try:
        coupon, discount = services.coupon_check(request.args.get("kod", ""), g.user["id"], item["price"] * qty, item["category_id"])
    except BizError as err:
        return jsonify({"ok": False, "msg": str(err), "discount": 0})
    return jsonify({"ok": True, "msg": f"Kupon uygulandı: {core.fmt_money(discount)} indirim.", "discount": discount})


# --------------------------------------------------------------------------- banner tıklama takibi
@bp.route("/git/banner/<int:bid>")
def banner_go(bid):
    b = q1("SELECT * FROM banners WHERE id = ?", (bid,))
    if not b:
        abort(404)
    ex("UPDATE banners SET clicks = clicks + 1 WHERE id = ?", (bid,))
    link = (b["link"] or "").strip()
    if link.startswith("/") and not link.startswith("//"):
        return redirect(link)
    if link.startswith(("http://", "https://")):
        return redirect(link)
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- kategoriler sayfası
@bp.route("/kategoriler")
def categories():
    rows = q(
        "SELECT c.*, (SELECT COUNT(*) FROM listings l WHERE l.category_id = c.id AND l.status = 'active') AS n,"
        " (SELECT MIN(l.price) FROM listings l WHERE l.category_id = c.id AND l.status = 'active') AS min_price"
        " FROM categories c WHERE c.is_active = 1 ORDER BY c.sort_order, c.id"
    )
    groups = [g_ for g_ in GROUP_ORDER if any(c["grp"] == g_ for c in rows)]
    groups += sorted({c["grp"] for c in rows if c["grp"] and c["grp"] not in GROUP_ORDER})
    return render_template("categories.html", cats=rows, groups=groups)


# --------------------------------------------------------------------------- mağazalar
SELLER_SORTS = {
    "satis": ("En çok satan", "sold DESC, avg DESC"),
    "puan": ("En yüksek puan", "avg DESC, rc DESC, sold DESC"),
    "ilan": ("En çok ilan", "n_listings DESC, sold DESC"),
    "yeni": ("Yeni mağazalar", "u.id DESC"),
}


@bp.route("/saticilar")
def sellers():
    text = request.args.get("q", "").strip()[:40]
    sort = request.args.get("sirala", "satis")
    if sort not in SELLER_SORTS:
        sort = "satis"
    where, args = "", []
    if text:
        where = " AND (u.store_name LIKE ? ESCAPE '\\' OR u.username LIKE ? ESCAPE '\\')"
        args = [_like(text), _like(text)]
    rows = q(
        "SELECT u.*, COALESCE(SUM(l.sales_count), 0) AS sold, COUNT(l.id) AS n_listings,"
        " (SELECT COUNT(*) FROM reviews r WHERE r.seller_id = u.id AND r.is_hidden = 0) AS rc,"
        " (SELECT COALESCE(AVG(rating), 0) FROM reviews r WHERE r.seller_id = u.id AND r.is_hidden = 0) AS avg,"
        " " + _pk_cols() +
        " FROM users u JOIN listings l ON l.seller_id = u.id AND l.status = 'active'"
        # mağaza paketleri: öne çıkan > elmas > altın > seçilen sıralama
        " WHERE u.is_banned = 0 AND u.is_seller = 1" + where
        + " GROUP BY u.id ORDER BY pk_featured DESC, pk_rank DESC, " + SELLER_SORTS[sort][1] + " LIMIT 60",
        args,
    )
    cards = [{"u": s, "badges": services.user_badges(s)[:2]} for s in rows]
    return render_template("sellers.html", cards=cards, text=text, sort=sort, sorts=SELLER_SORTS)


# --------------------------------------------------------------------------- robots / sitemap
@bp.route("/robots.txt")
def robots():
    body = "User-agent: *\nDisallow: /admin\nDisallow: /satici/\nDisallow: /hesabim\nDisallow: /api/\n"
    body += f"Sitemap: {request.host_url.rstrip('/')}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip("/")
    urls = [base + "/", base + url_for("listings"), base + url_for("site.categories"), base + url_for("site.sellers"), base + url_for("faq")]
    urls += [base + url_for("listings", kategori=c["slug"]) for c in q("SELECT slug FROM categories WHERE is_active = 1")]
    urls += [base + url_for("listing_detail", lid=r["id"]) for r in q("SELECT id FROM listings WHERE status = 'active' ORDER BY id DESC LIMIT 1000")]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join(f"<url><loc>{u.replace('&', '&amp;')}</loc></url>\n" for u in urls)
    xml += "</urlset>\n"
    return Response(xml, mimetype="application/xml")

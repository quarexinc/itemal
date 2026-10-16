"""Satıcı paneli: /satici/..."""
import csv
import io
import re
from datetime import datetime

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, url_for

import account_security as accsec
import core
import services
from core import BizError, ex, field, q, q1

bp = Blueprint("seller", __name__, url_prefix="/satici")
MAX_LISTINGS = 200
ESCROW_LABELS = {"held": "Emanette", "released": "Tamamlandı", "disputed": "İtiraz var", "refunded": "İade edildi"}
MAX_API_KEYS = 5


@bp.before_request
def _guard():
    # Tüm satıcı rotaları giriş + satıcı yetkisi ister
    if not g.user:
        return redirect(url_for("login", next=request.path))
    if not core.can_sell(g.user):
        return redirect(url_for("seller_apply"))
    gate = accsec.seller_2fa_gate()          # require_seller_2fa=1 ise iki adımlı doğrulamasız satıcı paneli yok
    if gate:
        return gate


@bp.context_processor
def _nav_counts():
    """Yan menüdeki rozetler: emanetteki sipariş, yanıtsız yorum, stoğu azalan ilan."""
    uid = g.user["id"] if g.get("user") else 0
    row = q1(
        "SELECT (SELECT COUNT(*) FROM orders WHERE seller_id = ?1 AND escrow_status IN ('held', 'disputed')) AS held,"
        " (SELECT COUNT(*) FROM reviews WHERE seller_id = ?1 AND seller_reply = '' AND is_hidden = 0) AS unreplied,"
        " (SELECT COUNT(*) FROM listings l WHERE l.seller_id = ?1 AND l.status IN ('active', 'paused')"
        "   AND (SELECT COUNT(*) FROM listing_codes k WHERE k.listing_id = l.id AND k.is_sold = 0) < 5) AS lowstock",
        (uid,),
    )
    return {"s_nav": row}


def own_listing(lid):
    item = q1("SELECT * FROM listings WHERE id = ? AND seller_id = ? AND status != 'removed'", (lid, g.user["id"]))
    if not item:
        abort(404)
    return item


def categories():
    return q("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id")


def rates_map():
    """{kategori_id: (oran, kaynak)} - satıcının her kategoride ödeyeceği komisyon."""
    return {c["id"]: services.commission_info(g.user, c["id"]) for c in categories()}


def handle_cover(existing="", required=False):
    """Yüklenen kapak varsa işler. (dosya_adı, yeni_mi) döndürür."""
    file = request.files.get("cover")
    if file and file.filename:
        return services.save_cover(file), True
    if required and not existing:
        raise BizError("Kapak görseli yüklemelisin. Görselli ilanlar çok daha fazla ilgi görür.")
    return existing, False


# --------------------------------------------------------------------------- dashboard
def _trend(cur, prev):
    """Önceki döneme göre değişim yüzdesi (önceki dönem 0 ise None)."""
    if not prev:
        return None
    return round((cur - prev) * 100 / prev)


def _greeting():
    hour = (core.utcnow() + core.TR_OFFSET).hour
    return "Günaydın" if 5 <= hour < 12 else ("İyi günler" if hour < 18 else "İyi akşamlar")


@bp.route("/")
def dashboard():
    import storeplus  # noqa: E402  (storeplus bu blueprint'e rota ekler; döngüsel içe aktarmayı önlemek için yerel)

    uid = g.user["id"]
    days = request.args.get("gun", 14, type=int)
    if days not in (7, 14, 30):
        days = 14
    totals = q1(
        "SELECT COALESCE(SUM(quantity), 0) AS sold, COALESCE(SUM(total), 0) AS gross,"
        " COALESCE(SUM(commission), 0) AS fee, COALESCE(SUM(seller_earning), 0) AS net, COUNT(*) AS orders"
        " FROM orders WHERE seller_id = ? AND escrow_status != 'refunded'",
        (uid,),
    )
    periods = q1(
        "SELECT"
        " COALESCE(SUM(CASE WHEN d = date('now','+3 hours') THEN seller_earning END), 0) AS today_net,"
        " COALESCE(SUM(CASE WHEN d = date('now','+3 hours') THEN quantity END), 0) AS today_qty,"
        " COALESCE(SUM(CASE WHEN d = date('now','+3 hours','-1 day') THEN seller_earning END), 0) AS yday_net,"
        " COALESCE(SUM(CASE WHEN d >= date('now','+3 hours','-6 days') THEN seller_earning END), 0) AS week_net,"
        " COALESCE(SUM(CASE WHEN d >= date('now','+3 hours','-6 days') THEN quantity END), 0) AS week_qty,"
        " COALESCE(SUM(CASE WHEN d BETWEEN date('now','+3 hours','-13 days') AND date('now','+3 hours','-7 days') THEN seller_earning END), 0) AS prev_week_net,"
        " COALESCE(SUM(CASE WHEN d >= date('now','+3 hours','-29 days') THEN seller_earning END), 0) AS month_net,"
        " COALESCE(SUM(CASE WHEN d >= date('now','+3 hours','-29 days') THEN quantity END), 0) AS month_qty,"
        " COALESCE(SUM(CASE WHEN d BETWEEN date('now','+3 hours','-59 days') AND date('now','+3 hours','-30 days') THEN seller_earning END), 0) AS prev_month_net"
        " FROM (SELECT seller_earning, quantity, date(created_at, '+3 hours') AS d FROM orders WHERE seller_id = ? AND escrow_status != 'refunded')",
        (uid,),
    )
    trends = {
        "today": _trend(periods["today_net"], periods["yday_net"]),
        "week": _trend(periods["week_net"], periods["prev_week_net"]),
        "month": _trend(periods["month_net"], periods["prev_month_net"]),
    }
    counts = q1(
        "SELECT COALESCE(SUM(status = 'active'), 0) AS active, COALESCE(SUM(status = 'paused'), 0) AS paused,"
        " COALESCE(SUM(status = 'blocked'), 0) AS blocked, COALESCE(SUM(views), 0) AS views"
        " FROM listings WHERE seller_id = ? AND status != 'removed'",
        (uid,),
    )
    stock_total = q1(
        "SELECT COUNT(*) AS c FROM listing_codes k JOIN listings l ON l.id = k.listing_id"
        " WHERE l.seller_id = ? AND l.status IN ('active', 'paused') AND k.is_sold = 0",
        (uid,),
    )["c"]
    low_stock = q(
        "SELECT * FROM (" + core.LISTING_SELECT + " WHERE l.seller_id = ? AND l.status IN ('active','paused'))"
        " WHERE stock < 5 ORDER BY stock, id LIMIT 6",
        (uid,),
    )
    top = q(
        "SELECT listing_id, listing_title, SUM(quantity) AS qty, SUM(seller_earning) AS net"
        " FROM orders WHERE seller_id = ? AND escrow_status != 'refunded' GROUP BY listing_id ORDER BY net DESC LIMIT 5",
        (uid,),
    )
    top_max = max((t["net"] for t in top), default=0) or 1
    chart_net = core.daily_series(
        "SELECT date(created_at, '+3 hours') AS d, SUM(seller_earning) AS v FROM orders"
        f" WHERE seller_id = ? AND escrow_status != 'refunded' AND created_at >= datetime('now', '-{days + 2} days') GROUP BY d",
        (uid,), days=days,
    )
    recent = q(
        "SELECT o.*, u.username AS buyer_name FROM orders o JOIN users u ON u.id = o.buyer_id"
        " WHERE o.seller_id = ? ORDER BY o.id DESC LIMIT 8",
        (uid,),
    )
    pending_wd = q1(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM withdrawals WHERE user_id = ? AND status = 'pending'", (uid,)
    )["s"]
    stats = services.seller_stats(uid)
    unreplied = q1("SELECT COUNT(*) AS c FROM reviews WHERE seller_id = ? AND seller_reply = '' AND is_hidden = 0", (uid,))["c"]
    held = services.held_total(uid)
    disputed = q1("SELECT COUNT(*) AS c, COALESCE(SUM(seller_earning), 0) AS s FROM orders WHERE seller_id = ? AND escrow_status = 'disputed'", (uid,))
    soldout = sum(1 for l in low_stock if l["stock"] == 0)
    # dikkat gerektirenler: önem sırasıyla
    attention = []
    if counts["blocked"]:
        attention.append(("bad", f"{counts['blocked']} ilanın yönetim tarafından engellendi.", url_for("ticket_new"), "Destek talebi aç"))
    if disputed["c"]:
        attention.append(("bad", f"{disputed['c']} siparişe alıcı itiraz etti ({core.fmt_money(disputed['s'])}). Yönetim inceliyor.", url_for("seller.sales", durum="disputed"), "Siparişlere bak"))
    if soldout:
        attention.append(("warn", f"{soldout} ilanının stoğu tükendi; alıcılar satın alamıyor.", url_for("seller.listings", durum="soldout"), "Kod ekle"))
    elif low_stock:
        attention.append(("warn", f"{len(low_stock)} ilanının stoğu azaldı (5 koddan az).", url_for("seller.listings", sirala="stok"), "Stokları gör"))
    if unreplied:
        attention.append(("info", f"{unreplied} yorum yanıtını bekliyor.", url_for("seller.reviews", durum="yanitsiz"), "Yanıtla"))
    pending_held = held["n"] - disputed["c"]
    if pending_held > 0:
        attention.append(("info", f"{pending_held} siparişin alıcı onayı bekliyor; onaylanınca ya da süre dolunca bakiyene geçer.", url_for("seller.earnings"), "Ayrıntı"))
    return render_template(
        "seller_dashboard.html",
        totals=totals, periods=periods, trends=trends, counts=counts, stock_total=stock_total, low_stock=low_stock, top=top, top_max=top_max,
        chart=chart_net, days=days, recent=recent, withdrawable=core.withdrawable(uid), pending_wd=pending_wd,
        stats=stats, badges=services.user_badges(g.user, stats), unreplied=unreplied, held=held, attention=attention, greeting=_greeting(),
        global_rate=core.setting_pct("commission_percent", "5"), personal_rate=g.user["commission_rate"],
        goal=storeplus.goal_progress(g.user), vacation=storeplus.vacation_active(g.user),
    )


# --------------------------------------------------------------------------- ilanlar
LISTING_SORTS = {
    "yeni": ("En yeni", "id DESC"),
    "satis": ("En çok satan", "sales_count DESC, id DESC"),
    "goruntulenme": ("En çok görüntülenen", "views DESC, id DESC"),
    "stok": ("Stok (az olan önce)", "stock ASC, id DESC"),
    "fiyat_azalan": ("Fiyat (yüksek)", "price DESC"),
    "fiyat_artan": ("Fiyat (düşük)", "price ASC"),
}


@bp.route("/ilanlar")
def listings():
    uid = g.user["id"]
    status = request.args.get("durum", "")
    sort = request.args.get("sirala", "yeni")
    if sort not in LISTING_SORTS:
        sort = "yeni"
    text = request.args.get("q", "").strip()[:60]
    inner_where, args = "l.seller_id = ? AND l.status != 'removed'", [uid]
    if text:
        inner_where += " AND l.title LIKE ? ESCAPE '\\'"
        args.append("%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    base = "SELECT * FROM (" + core.LISTING_SELECT + " WHERE " + inner_where + ")"
    outer = ""
    if status in ("active", "paused", "blocked"):
        outer = " WHERE status = ?"
        args = args + [status]
    elif status == "soldout":
        outer = " WHERE stock = 0 AND status != 'blocked'"
    else:
        status = ""
    page = core.paginate(base + outer + " ORDER BY " + LISTING_SORTS[sort][1], args, 15)
    counts = q1(
        "SELECT COUNT(*) AS n, COALESCE(SUM(status = 'active'), 0) AS active, COALESCE(SUM(status = 'paused'), 0) AS paused,"
        " COALESCE(SUM(status = 'blocked'), 0) AS blocked, COALESCE(SUM(stock = 0 AND status != 'blocked'), 0) AS soldout,"
        " COALESCE(SUM(stock), 0) AS stock_sum, COALESCE(SUM(views), 0) AS views, COALESCE(SUM(sales_count), 0) AS sales"
        " FROM (" + core.LISTING_SELECT + " WHERE l.seller_id = ? AND l.status != 'removed')",
        (uid,),
    )
    import doping  # noqa: E402  (doping.py bu blueprint'e rota ekler; döngüsel içe aktarmayı önlemek için yerel)

    page["rows"] = doping.attach(page["rows"])
    return render_template("seller_listings.html", page=page, status=status, text=text, sort=sort, sorts=LISTING_SORTS, counts=counts)


@bp.route("/ilan/yeni", methods=["GET", "POST"])
def listing_new():
    import doping  # noqa: E402  (doping.py bu blueprint'e rota ekler; döngüsel içe aktarmayı önlemek için yerel)

    form = {}
    dsel = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ("title", "description", "price", "old_price", "category_id", "codes", "phone")}
        cover = ""
        dp_items, dp_done = [], []
        dp_key = doping.read_key()
        try:
            phone = services.read_phone()
            data = services.read_listing_form()
            codes = core.parse_codes(request.form.get("codes"))
            if not codes:
                raise BizError("En az bir e-pin kodu ekle (her satıra bir kod).")
            dp_items = doping.read_items()
            if dp_items and dp_key is None:
                raise BizError("Form süresi doldu; sayfayı yenileyip tekrar dene.")
            if q1("SELECT COUNT(*) AS c FROM listings WHERE seller_id = ? AND status != 'removed'", (g.user["id"],))["c"] >= MAX_LISTINGS:
                raise BizError(f"En fazla {MAX_LISTINGS} ilanın olabilir.")
            cover, _ = handle_cover(required=core.setting("require_cover", "1") == "1")
            with core.tx():       # ilan + seçilen dopingler tek işlemde: bakiye yetmezse ilan oluşmaz
                ex("UPDATE users SET phone = ? WHERE id = ?", (phone, g.user["id"]))
                cur = ex(
                    "INSERT INTO listings(seller_id, category_id, title, description, price, old_price, cover) VALUES (?,?,?,?,?,?,?)",
                    (g.user["id"], data["category_id"], data["title"], data["description"], data["price"], data["old_price"], cover or ""),
                )
                for c in codes:
                    ex("INSERT INTO listing_codes(listing_id, code) VALUES (?,?)", (cur.lastrowid, c))
                if dp_items:
                    dp_done = doping.purchase_in_tx(g.user["id"], cur.lastrowid, dp_items, dp_key)
        except BizError as err:
            services.delete_cover(cover)
            msg = str(err)
            if dp_items:
                msg += " İlan oluşturulmadı" + ("; kapak görselini yeniden seçmen gerekiyor." if cover else ".")
            flash(msg, "bad")
            dsel = doping.selected_from_form()
        else:
            msg = f"İlan yayınlandı ({len(codes)} kod stoğa eklendi)."
            if dp_done:
                msg += f" Doping etkinleştirildi, {core.fmt_money(sum(d['price'] for d in dp_done))} bakiyenden düşüldü."
            flash(msg, "ok")
            return redirect(url_for("seller.listings"))
    return render_template("seller_listing_form.html", form=form, cats=categories(), item=None, rates=rates_map(), **doping.form_ctx(dsel))


@bp.route("/ilan/<int:lid>/duzenle", methods=["GET", "POST"])
def listing_edit(lid):
    item = own_listing(lid)
    if request.method == "POST":
        new_cover = ""
        try:
            phone = services.read_phone()
            data = services.read_listing_form()
            cover, replaced = handle_cover(existing=item["cover"], required=core.setting("require_cover", "1") == "1")
            new_cover = cover if replaced else ""
        except BizError as err:
            flash(str(err), "bad")
        else:
            ex("UPDATE users SET phone = ? WHERE id = ?", (phone, g.user["id"]))
            ex(
                "UPDATE listings SET title = ?, description = ?, price = ?, old_price = ?, category_id = ?, cover = ?,"
                " is_deal = CASE WHEN ? > price THEN is_deal ELSE 0 END, updated_at = datetime('now') WHERE id = ?",
                (data["title"], data["description"], data["price"], data["old_price"], data["category_id"], cover, data["old_price"], lid),
            )
            if new_cover and item["cover"]:
                services.delete_cover(item["cover"])
            flash("İlan güncellendi.", "ok")
            return redirect(url_for("seller.listings"))
    form = {
        "title": item["title"], "description": item["description"],
        "price": core.fmt_plain(item["price"]), "category_id": item["category_id"],
        "old_price": core.fmt_plain(item["old_price"]) if item["old_price"] else "",
    }
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ("title", "description", "price", "old_price", "category_id", "phone")}
    return render_template("seller_listing_form.html", form=form, cats=categories(), item=item, rates=rates_map())


@bp.post("/ilan/<int:lid>/durum")
def listing_status(lid):
    item = own_listing(lid)
    if item["status"] == "blocked":
        flash("Bu ilan yönetici tarafından engellendi; yeniden yayına alamazsın.", "bad")
    else:
        new = "paused" if item["status"] == "active" else "active"
        ex("UPDATE listings SET status = ?, updated_at = datetime('now') WHERE id = ?", (new, lid))
        flash("İlan yayına alındı." if new == "active" else "İlan duraklatıldı.", "ok")
    return redirect(request.referrer or url_for("seller.listings"))


@bp.post("/ilan/<int:lid>/sil")
def listing_delete(lid):
    own_listing(lid)
    ex("UPDATE listings SET status = 'removed', updated_at = datetime('now') WHERE id = ?", (lid,))
    flash("İlan silindi. Geçmiş siparişler korunur.", "info")
    return redirect(url_for("seller.listings"))


# --------------------------------------------------------------------------- stok
@bp.route("/ilan/<int:lid>/stok", methods=["GET", "POST"])
def stock(lid):
    item = own_listing(lid)
    if request.method == "POST":
        try:
            codes = core.parse_codes(request.form.get("codes"))
            if not codes:
                raise BizError("Eklenecek kod bulunamadı (her satıra bir kod yaz).")
            with core.tx():
                existing = {r["code"] for r in q("SELECT code FROM listing_codes WHERE listing_id = ?", (lid,))}
                fresh = [c for c in codes if c not in existing]
                for c in fresh:
                    ex("INSERT INTO listing_codes(listing_id, code) VALUES (?,?)", (lid, c))
                ex("UPDATE listings SET updated_at = datetime('now') WHERE id = ?", (lid,))
        except BizError as err:
            flash(str(err), "bad")
        else:
            skipped = len(codes) - len(fresh)
            msg = f"{len(fresh)} kod stoğa eklendi."
            if skipped:
                msg += f" {skipped} kod zaten kayıtlı olduğu için atlandı."
            flash(msg, "ok")
        return redirect(url_for("seller.stock", lid=lid))
    counts = q1(
        "SELECT COALESCE(SUM(is_sold = 0), 0) AS available, COALESCE(SUM(is_sold = 1), 0) AS sold"
        " FROM listing_codes WHERE listing_id = ?",
        (lid,),
    )
    page = core.paginate("SELECT * FROM listing_codes WHERE listing_id = ? AND is_sold = 0 ORDER BY id DESC", (lid,), 30)
    return render_template("seller_stock.html", l=item, counts=counts, page=page)


@bp.post("/ilan/<int:lid>/stok/<int:cid>/sil")
def stock_delete(lid, cid):
    own_listing(lid)
    cur = ex("DELETE FROM listing_codes WHERE id = ? AND listing_id = ? AND is_sold = 0", (cid, lid))
    flash("Kod silindi." if cur.rowcount else "Kod bulunamadı veya satılmış.", "ok" if cur.rowcount else "bad")
    return redirect(request.referrer or url_for("seller.stock", lid=lid))


# --------------------------------------------------------------------------- satışlar
def sales_filter():
    where, args = ["o.seller_id = ?"], [g.user["id"]]
    lid = request.args.get("ilan", type=int)
    if lid:
        where.append("o.listing_id = ?")
        args.append(lid)
    status = request.args.get("durum", "")
    if status in ("held", "released", "disputed", "refunded"):
        where.append("o.escrow_status = ?")
        args.append(status)
    text = request.args.get("q", "").strip()[:40]
    if text:
        if text.lstrip("#").isdigit():
            where.append("o.id = ?")
            args.append(int(text.lstrip("#")))
        else:
            where.append("b.username LIKE ? ESCAPE '\\'")
            args.append("%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    for key, op in (("baslangic", ">="), ("bitis", "<=")):
        val = request.args.get(key, "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", val):
            where.append(f"date(o.created_at, '+3 hours') {op} ?")
            args.append(val)
    sql = (
        "SELECT o.*, b.username AS buyer_name FROM orders o JOIN users b ON b.id = o.buyer_id"
        " WHERE " + " AND ".join(where) + " ORDER BY o.id DESC"
    )
    return sql, args


@bp.route("/satislar")
def sales():
    sql, args = sales_filter()
    page = core.paginate(sql, args, 20)
    sums = q1(
        f"SELECT COALESCE(SUM(quantity), 0) AS qty, COALESCE(SUM(total), 0) AS gross,"
        f" COALESCE(SUM(commission), 0) AS fee, COALESCE(SUM(seller_earning), 0) AS net FROM ({sql})",
        args,
    )
    my_listings = q("SELECT id, title FROM listings WHERE seller_id = ? AND status != 'removed' ORDER BY title", (g.user["id"],))
    status_counts = {r["escrow_status"]: r["c"] for r in q("SELECT escrow_status, COUNT(*) AS c FROM orders WHERE seller_id = ? GROUP BY escrow_status", (g.user["id"],))}
    return render_template("seller_sales.html", page=page, sums=sums, my_listings=my_listings, f=request.args, status_counts=status_counts)


def csv_safe(value):
    value = str(value)
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


@bp.route("/satislar.csv")
def sales_csv():
    sql, args = sales_filter()
    rows = q(sql + " LIMIT 5000", args)
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Sipariş No", "Tarih", "İlan", "Alıcı", "Adet", "Birim Fiyat", "Toplam", "Komisyon Oranı %", "Komisyon", "Net Kazanç", "Durum"])
    for r in rows:
        w.writerow([
            r["id"], core.fmt_dt(r["created_at"]), csv_safe(r["listing_title"]), csv_safe(r["buyer_name"]), r["quantity"],
            core.fmt_plain(r["unit_price"]), core.fmt_plain(r["total"]), str(r["commission_rate"]).replace(".", ","),
            core.fmt_plain(r["commission"]), core.fmt_plain(r["seller_earning"]), ESCROW_LABELS.get(r["escrow_status"], r["escrow_status"]),
        ])
    name = "satislar-" + datetime.now().strftime("%Y%m%d") + ".csv"
    return Response(buf.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={name}"})


# --------------------------------------------------------------------------- kazançlar
@bp.route("/kazanc")
def earnings():
    uid = g.user["id"]
    held_rows = q(
        "SELECT o.*, u.username AS buyer_name FROM orders o JOIN users u ON u.id = o.buyer_id"
        " WHERE o.seller_id = ? AND o.escrow_status IN ('held', 'disputed') ORDER BY o.release_at, o.id LIMIT 30", (uid,),
    )
    held = services.held_total(uid)
    wd = q1(
        "SELECT COALESCE(SUM(CASE WHEN status = 'pending' THEN amount END), 0) AS pending,"
        " COALESCE(SUM(CASE WHEN status = 'approved' THEN net END), 0) AS paid, COUNT(*) AS n FROM withdrawals WHERE user_id = ?", (uid,),
    )
    lifetime = q1("SELECT COALESCE(SUM(seller_earning), 0) AS net FROM orders WHERE seller_id = ? AND escrow_status != 'refunded'", (uid,))["net"]
    history = q("SELECT * FROM withdrawals WHERE user_id = ? ORDER BY id DESC LIMIT 15", (uid,))
    return render_template(
        "seller_earnings.html", held_rows=held_rows, held=held, wd=wd, lifetime=lifetime, history=history,
        withdrawable=core.withdrawable(uid), min_w=core.setting_kurus("min_withdraw", 10000),
        fee_rate=core.setting_pct("withdraw_fee_percent", "2"), kyc_ok=g.user["kyc_status"] == "approved",
    )


# --------------------------------------------------------------------------- komisyon
@bp.route("/komisyon")
def commission():
    rows = []
    for c in categories():
        rate, source = services.commission_info(g.user, c["id"])
        rows.append({"cat": c, "rate": rate, "source": source})
    totals = q1(
        "SELECT COALESCE(SUM(commission), 0) AS fee, COALESCE(SUM(total), 0) AS gross FROM orders WHERE seller_id = ?",
        (g.user["id"],),
    )
    fee_rate = core.setting_pct("withdraw_fee_percent", "2")
    return render_template("seller_commission.html", rows=rows, totals=totals, fee_rate=fee_rate)


# --------------------------------------------------------------------------- yorumlar
@bp.route("/yorumlar")
def reviews():
    only_open = request.args.get("durum") == "yanitsiz"
    where = "r.seller_id = ? AND r.is_hidden = 0" + (" AND r.seller_reply = ''" if only_open else "")
    page = core.paginate(
        "SELECT r.*, b.username AS buyer_name, l.title AS listing_title FROM reviews r"
        " JOIN users b ON b.id = r.buyer_id JOIN listings l ON l.id = r.listing_id"
        " WHERE " + where + " ORDER BY r.id DESC",
        (g.user["id"],), 10,
    )
    return render_template("seller_reviews.html", page=page, only_open=only_open, stats=services.seller_stats(g.user["id"]))


@bp.post("/yorum/<int:rid>/yanit")
def review_reply(rid):
    r = q1("SELECT * FROM reviews WHERE id = ? AND seller_id = ?", (rid, g.user["id"]))
    if not r:
        abort(404)
    reply = field("reply", 300)
    if len(reply) < 2:
        flash("Yanıt boş olamaz.", "bad")
    else:
        ex("UPDATE reviews SET seller_reply = ?, replied_at = datetime('now') WHERE id = ?", (reply, rid))
        flash("Yanıtın yayınlandı.", "ok")
    return redirect(request.referrer or url_for("seller.reviews"))


# --------------------------------------------------------------------------- API anahtarları
@bp.route("/api", methods=["GET", "POST"])
def api_keys():
    uid = g.user["id"]
    new_key = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            name = field("name", 40)
            active = q1("SELECT COUNT(*) AS c FROM api_keys WHERE user_id = ? AND is_active = 1", (uid,))["c"]
            if len(name) < 2:
                flash("Anahtara bir ad ver (ör. Stok botu).", "bad")
            elif active >= MAX_API_KEYS:
                flash(f"En fazla {MAX_API_KEYS} aktif anahtarın olabilir.", "bad")
            else:
                plain, prefix, digest = services.new_api_key()
                ex("INSERT INTO api_keys(user_id, name, key_prefix, key_hash) VALUES (?,?,?,?)", (uid, name, prefix, digest))
                new_key = plain
        elif action == "revoke":
            ex("UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?", (request.form.get("id", type=int), uid))
            flash("Anahtar iptal edildi.", "info")
            return redirect(url_for("seller.api_keys"))
    keys = q("SELECT * FROM api_keys WHERE user_id = ? ORDER BY id DESC", (uid,))
    return render_template("seller_api.html", keys=keys, new_key=new_key)


# --------------------------------------------------------------------------- mağaza
@bp.route("/magaza", methods=["GET", "POST"])
def store():
    if request.method == "POST":
        action = request.form.get("action", "store")
        if action == "avatar":
            try:
                name = services.save_avatar(request.files.get("avatar"))
                if not name:
                    raise BizError("Bir görsel seç.")
            except BizError as err:
                flash(str(err), "bad")
            else:
                services.delete_avatar(g.user["avatar"])
                ex("UPDATE users SET avatar = ? WHERE id = ?", (name, g.user["id"]))
                flash("Mağaza profil fotoğrafı güncellendi.", "ok")
            return redirect(url_for("seller.store"))
        if action == "banner":
            try:
                name = services.save_store_banner(request.files.get("banner"))
                if not name:
                    raise BizError("Bir görsel seç.")
            except BizError as err:
                flash(str(err), "bad")
            else:
                services.delete_cover(g.user["store_banner"])
                ex("UPDATE users SET store_banner = ? WHERE id = ?", (name, g.user["id"]))
                flash("Mağaza kapak görseli güncellendi.", "ok")
            return redirect(url_for("seller.store"))
        if action == "banner_remove":
            services.delete_cover(g.user["store_banner"])
            ex("UPDATE users SET store_banner = '' WHERE id = ?", (g.user["id"],))
            flash("Kapak görseli kaldırıldı.", "info")
            return redirect(url_for("seller.store"))
        if action == "avatar_remove":
            services.delete_avatar(g.user["avatar"])
            ex("UPDATE users SET avatar = '' WHERE id = ?", (g.user["id"],))
            flash("Profil fotoğrafı kaldırıldı.", "info")
            return redirect(url_for("seller.store"))
        name = field("store_name", 40)
        desc = field("store_desc", 500)
        if not 3 <= len(name) <= 40:
            flash("Mağaza adı 3-40 karakter olmalı.", "bad")
        elif q1("SELECT 1 FROM users WHERE store_name = ? COLLATE NOCASE AND id != ?", (name, g.user["id"])):
            flash("Bu mağaza adı kullanılıyor.", "bad")
        else:
            import storeplus
            me = q1("SELECT * FROM users WHERE id = ?", (g.user["id"],))
            fee = storeplus.name_fee_due(me) if name != (me["store_name"] or "") else 0
            try:
                with core.tx():
                    storeplus.charge_fee(me["id"], fee, "Mağaza adı değişikliği")
                    ex("UPDATE users SET store_name = ?, store_desc = ? WHERE id = ?", (name, desc, me["id"]))
            except BizError as err:
                flash(str(err), "bad")
                return redirect(url_for("seller.store"))
            flash("Mağaza bilgilerin güncellendi." + (f" {core.fmt_money(fee)} bakiyenden düşüldü." if fee else ""), "ok")
            return redirect(url_for("seller.store"))
    import storeplus
    return render_template("seller_store.html", badges=services.user_badges(g.user), name_fee=storeplus.name_fee_due(g.user), name_fee_amount=storeplus.fee_name())

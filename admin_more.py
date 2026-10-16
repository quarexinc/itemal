"""Yönetim paneli - ek modüller: global arama, banner, kupon, rapor/dışa aktarma, duyuru, sistem ve yedek, demo veri."""
import csv
import io
import os
import platform
import re
import sqlite3
import sys
from datetime import datetime

from flask import Response, abort, flash, redirect, render_template, request, url_for

import core
import db as dbm
import security
import storage
import demo
import services
from admin import _csv_safe, bp, like
from core import BizError, ex, field, q, q1

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,30}$")


def _color(name, default):
    val = (request.form.get(name) or default).strip()
    if not HEX_RE.match(val):
        raise BizError("Renkler #rrggbb biçiminde olmalı.")
    return val.lower()


def _link(value):
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("/") and not value.startswith("//"):
        return value[:300]
    if value.startswith(("http://", "https://")):
        return value[:300]
    raise BizError("Bağlantı '/' ile (site içi) ya da http(s):// ile başlamalı.")


# --------------------------------------------------------------------------- global arama
@bp.route("/ara")
def search():
    text = request.args.get("q", "").strip()[:60]
    res = {"users": [], "listings": [], "orders": [], "tickets": [], "deposits": []}
    if text:
        num = int(text) if text.isdigit() else None
        res["users"] = q(
            "SELECT id, username, email, balance, is_banned, is_seller FROM users WHERE username LIKE ? ESCAPE '\\'"
            " OR email LIKE ? ESCAPE '\\' OR id = ? OR store_name LIKE ? ESCAPE '\\' OR reg_ip = ? OR last_ip = ? ORDER BY id DESC LIMIT 8",
            (like(text), like(text), num or -1, like(text), text, text),
        )
        res["listings"] = q(
            core.LISTING_SELECT + " WHERE l.title LIKE ? ESCAPE '\\' OR l.id = ? ORDER BY l.id DESC LIMIT 8", (like(text), num or -1)
        )
        res["orders"] = q(
            "SELECT o.*, b.username AS buyer_name, s.username AS seller_name FROM orders o JOIN users b ON b.id = o.buyer_id"
            " JOIN users s ON s.id = o.seller_id WHERE o.id = ? OR o.listing_title LIKE ? ESCAPE '\\' OR b.username LIKE ? ESCAPE '\\'"
            " ORDER BY o.id DESC LIMIT 8",
            (num or -1, like(text), like(text)),
        )
        res["tickets"] = q(
            "SELECT t.*, u.username FROM tickets t JOIN users u ON u.id = t.user_id WHERE t.id = ? OR t.subject LIKE ? ESCAPE '\\'"
            " ORDER BY t.id DESC LIMIT 8",
            (num or -1, like(text)),
        )
        res["deposits"] = q(
            "SELECT d.*, u.username FROM deposits d JOIN users u ON u.id = d.user_id WHERE d.id = ? OR d.reference LIKE ? ESCAPE '\\'"
            " ORDER BY d.id DESC LIMIT 8",
            (num or -1, like(text)),
        )
    total = sum(len(v) for v in res.values())
    return render_template("admin_search.html", text=text, res=res, total=total)


# --------------------------------------------------------------------------- bannerlar
def _banner_from_form(existing=None):
    slot = request.form.get("slot")
    if slot not in ("hero", "strip"):
        raise BizError("Konum seçilmeli.")
    title = field("title", 70)
    if len(title) < 3:
        raise BizError("Başlık en az 3 karakter olmalı.")
    data = {
        "slot": slot, "title": title, "subtitle": field("subtitle", 140), "cta_text": field("cta_text", 30),
        "link": _link(request.form.get("link")), "color1": _color("color1", "#7c5cff"), "color2": _color("color2", "#1b1140"),
        "sort_order": request.form.get("sort_order", 0, type=int) or 0,
        "is_active": 1 if request.form.get("is_active") else 0,
        "starts_at": core.local_to_utc(request.form.get("starts_at")), "ends_at": core.local_to_utc(request.form.get("ends_at")),
    }
    if data["starts_at"] and data["ends_at"] and data["ends_at"] <= data["starts_at"]:
        raise BizError("Bitiş zamanı başlangıçtan sonra olmalı.")
    image = existing["image"] if existing else ""
    file = request.files.get("image")
    new_image = ""
    if file and file.filename:
        new_image = services.save_banner(file) or ""
        image = new_image
    elif request.form.get("remove_image"):
        image = ""
    data["image"] = image
    return data, new_image


@bp.route("/bannerlar", methods=["GET", "POST"])
def banners():
    form = {}
    if request.method == "POST":
        new_image = ""
        try:
            data, new_image = _banner_from_form()
            ex(
                "INSERT INTO banners(slot, title, subtitle, cta_text, link, image, color1, color2, is_active, sort_order, starts_at, ends_at)"
                " VALUES (:slot,:title,:subtitle,:cta_text,:link,:image,:color1,:color2,:is_active,:sort_order,:starts_at,:ends_at)",
                data,
            )
            core.log_admin("Banner eklendi", f"{data['slot']} - {data['title']}")
            flash("Banner eklendi.", "ok")
            return redirect(url_for("admin.banners"))
        except BizError as err:
            services.delete_cover(new_image)
            flash(str(err), "bad")
            form = request.form
    rows = q("SELECT * FROM banners ORDER BY slot, sort_order, id")
    return render_template("admin_banners.html", rows=rows, form=form, edit=None)


@bp.route("/banner/<int:bid>", methods=["GET", "POST"])
def banner_edit(bid):
    b = q1("SELECT * FROM banners WHERE id = ?", (bid,))
    if not b:
        abort(404)
    if request.method == "POST":
        new_image = ""
        try:
            data, new_image = _banner_from_form(b)
            data["id"] = bid
            ex(
                "UPDATE banners SET slot=:slot, title=:title, subtitle=:subtitle, cta_text=:cta_text, link=:link, image=:image,"
                " color1=:color1, color2=:color2, is_active=:is_active, sort_order=:sort_order, starts_at=:starts_at, ends_at=:ends_at"
                " WHERE id=:id",
                data,
            )
            if b["image"] and b["image"] != data["image"]:
                services.delete_cover(b["image"])
            core.log_admin("Banner güncellendi", f"#{bid} {data['title']}")
            flash("Banner güncellendi.", "ok")
            return redirect(url_for("admin.banners"))
        except BizError as err:
            services.delete_cover(new_image)
            flash(str(err), "bad")
    return render_template("admin_banners.html", rows=q("SELECT * FROM banners ORDER BY slot, sort_order, id"), form={}, edit=b)


@bp.post("/banner/<int:bid>/islem")
def banner_action(bid):
    b = q1("SELECT * FROM banners WHERE id = ?", (bid,))
    if not b:
        abort(404)
    action = request.form.get("action")
    if action == "toggle":
        ex("UPDATE banners SET is_active = 1 - is_active WHERE id = ?", (bid,))
        core.log_admin("Banner durumu", f"#{bid} {b['title']}")
        flash("Banner durumu değişti.", "ok")
    elif action == "delete":
        ex("DELETE FROM banners WHERE id = ?", (bid,))
        services.delete_cover(b["image"])
        core.log_admin("Banner silindi", f"#{bid} {b['title']}")
        flash("Banner silindi.", "ok")
    elif action == "reset":
        ex("UPDATE banners SET views = 0, clicks = 0 WHERE id = ?", (bid,))
        flash("Sayaçlar sıfırlandı.", "ok")
    else:
        abort(400)
    return redirect(url_for("admin.banners"))


# --------------------------------------------------------------------------- kuponlar
def _coupon_from_form():
    code = field("code", 30).upper()
    if not CODE_RE.match(code):
        raise BizError("Kupon kodu 3-30 karakter olmalı; harf, rakam, tire ve alt çizgi içerebilir.")
    kind = request.form.get("kind")
    if kind not in ("percent", "fixed"):
        raise BizError("İndirim türü seçilmeli.")
    if kind == "percent":
        try:
            value = float((request.form.get("value") or "").replace(",", "."))
        except ValueError:
            raise BizError("İndirim yüzdesi sayı olmalı.")
        if not 1 <= value <= 90:
            raise BizError("Yüzde 1 ile 90 arasında olmalı.")
    else:
        kurus = core.to_kurus(request.form.get("value"))
        if kurus is None or kurus < 100:
            raise BizError("Sabit indirim en az 1 TL olmalı.")
        value = kurus
    min_total = core.to_kurus(request.form.get("min_total")) if request.form.get("min_total", "").strip() else 0
    max_disc = core.to_kurus(request.form.get("max_discount")) if request.form.get("max_discount", "").strip() else 0
    if min_total is None or max_disc is None or min_total < 0 or max_disc < 0:
        raise BizError("Tutar alanları geçersiz.")
    cat = request.form.get("category_id", type=int)
    if cat and not q1("SELECT 1 FROM categories WHERE id = ?", (cat,)):
        raise BizError("Kategori bulunamadı.")
    starts, expires = core.local_to_utc(request.form.get("starts_at")), core.local_to_utc(request.form.get("expires_at"))
    if starts and expires and expires <= starts:
        raise BizError("Bitiş zamanı başlangıçtan sonra olmalı.")
    return {
        "code": code, "kind": kind, "value": value, "min_total": min_total, "max_discount": max_disc,
        "max_uses": max(0, request.form.get("max_uses", 0, type=int) or 0), "per_user": max(0, request.form.get("per_user", 1, type=int) or 0),
        "category_id": cat or None, "starts_at": starts, "expires_at": expires, "is_active": 1 if request.form.get("is_active") else 0,
    }


@bp.route("/kuponlar", methods=["GET", "POST"])
def coupons():
    form = {}
    if request.method == "POST":
        try:
            data = _coupon_from_form()
            ex(
                "INSERT INTO coupons(code, kind, value, min_total, max_discount, max_uses, per_user, category_id, starts_at, expires_at, is_active)"
                " VALUES (:code,:kind,:value,:min_total,:max_discount,:max_uses,:per_user,:category_id,:starts_at,:expires_at,:is_active)",
                data,
            )
            core.log_admin("Kupon oluşturuldu", data["code"])
            flash(f"{data['code']} kuponu oluşturuldu.", "ok")
            return redirect(url_for("admin.coupons"))
        except sqlite3.IntegrityError:
            flash("Bu kupon kodu zaten var.", "bad")
            form = request.form
        except BizError as err:
            flash(str(err), "bad")
            form = request.form
    rows = q(
        "SELECT c.*, cat.name AS cat_name, (SELECT COALESCE(SUM(amount), 0) FROM coupon_uses u WHERE u.coupon_id = c.id) AS given"
        " FROM coupons c LEFT JOIN categories cat ON cat.id = c.category_id ORDER BY c.id DESC"
    )
    cats = q("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY sort_order, id")
    totals = q1("SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS given FROM coupon_uses")
    return render_template("admin_coupons.html", rows=rows, cats=cats, form=form, totals=totals, now=core.utc_str())


@bp.post("/kupon/<int:cid>/islem")
def coupon_action(cid):
    c = q1("SELECT * FROM coupons WHERE id = ?", (cid,))
    if not c:
        abort(404)
    action = request.form.get("action")
    if action == "toggle":
        ex("UPDATE coupons SET is_active = 1 - is_active WHERE id = ?", (cid,))
        core.log_admin("Kupon durumu", f"{c['code']}")
        flash("Kupon durumu değişti.", "ok")
    elif action == "delete":
        used = q1("SELECT COUNT(*) AS n FROM coupon_uses WHERE coupon_id = ?", (cid,))["n"]
        if used:
            ex("UPDATE coupons SET is_active = 0 WHERE id = ?", (cid,))
            flash("Kupon kullanılmış olduğu için silinmedi, pasife alındı.", "info")
        else:
            ex("DELETE FROM coupons WHERE id = ?", (cid,))
            flash("Kupon silindi.", "ok")
        core.log_admin("Kupon silindi/pasife alındı", c["code"])
    else:
        abort(400)
    return redirect(url_for("admin.coupons"))


# --------------------------------------------------------------------------- fırsat işareti
@bp.post("/ilan/<int:lid>/firsat")
def listing_deal(lid):
    item = q1("SELECT * FROM listings WHERE id = ?", (lid,))
    if not item:
        abort(404)
    if item["is_deal"]:
        ex("UPDATE listings SET is_deal = 0 WHERE id = ?", (lid,))
        flash("İlan fırsat listesinden çıkarıldı.", "ok")
    else:
        old = item["old_price"]
        raw = request.form.get("old_price", "").strip()
        if raw:
            old = core.to_kurus(raw) or 0
        if old <= item["price"] or old > item["price"] * 5:
            flash("Fırsat için güncel fiyattan yüksek bir eski fiyat gerekir (ilanı düzenleyip gir ya da buraya yaz).", "bad")
            return redirect(request.referrer or url_for("admin.listings"))
        ex("UPDATE listings SET is_deal = 1, old_price = ? WHERE id = ?", (old, lid))
        flash("İlan fırsat listesine eklendi.", "ok")
    core.log_admin("İlan fırsat işareti", f"#{lid} {item['title'][:50]}")
    return redirect(request.referrer or url_for("admin.listings"))


# --------------------------------------------------------------------------- raporlar
RANGES = {7: "Son 7 gün", 30: "Son 30 gün", 90: "Son 90 gün", 365: "Son 1 yıl"}


@bp.route("/raporlar")
def reports():
    days = request.args.get("gun", 30, type=int)
    if days not in RANGES:
        days = 30
    since = f"-{days} days"
    kpi = q1(
        "SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS gmv, COALESCE(SUM(commission), 0) AS fee,"
        " COALESCE(SUM(discount), 0) AS discount, COALESCE(SUM(quantity), 0) AS qty, COUNT(DISTINCT buyer_id) AS buyers"
        " FROM orders WHERE created_at >= datetime('now', ?)", (since,),
    )
    money_in = q1(
        "SELECT (SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE status = 'approved' AND created_at >= datetime('now', ?)) AS deposits,"
        " (SELECT COALESCE(SUM(net), 0) FROM withdrawals WHERE status = 'approved' AND created_at >= datetime('now', ?)) AS payouts,"
        " (SELECT COALESCE(SUM(price), 0) FROM listing_dopings WHERE created_at >= datetime('now', ?)) AS doping,"
        " (SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', ?)) AS new_users,"
        " (SELECT COUNT(*) FROM users WHERE is_seller = 1 AND created_at >= datetime('now', ?)) AS new_sellers",
        (since, since, since, since, since),
    )
    span = min(days, 30)
    chart = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, SUM(total) AS v FROM orders WHERE created_at >= datetime('now', ?) GROUP BY d", (since,), span
    )
    chart_orders = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, COUNT(*) AS v FROM orders WHERE created_at >= datetime('now', ?) GROUP BY d", (since,), span
    )
    by_cat = q(
        "SELECT c.name, c.color, COUNT(o.id) AS orders, COALESCE(SUM(o.total), 0) AS gmv FROM orders o"
        " JOIN listings l ON l.id = o.listing_id JOIN categories c ON c.id = l.category_id"
        " WHERE o.created_at >= datetime('now', ?) GROUP BY c.id ORDER BY gmv DESC LIMIT 10", (since,),
    )
    top_sellers = q(
        "SELECT u.id, u.username, COUNT(o.id) AS orders, SUM(o.total) AS gmv, SUM(o.commission) AS fee FROM orders o"
        " JOIN users u ON u.id = o.seller_id WHERE o.created_at >= datetime('now', ?) GROUP BY u.id ORDER BY gmv DESC LIMIT 8", (since,),
    )
    top_buyers = q(
        "SELECT u.id, u.username, COUNT(o.id) AS orders, SUM(o.total - o.discount) AS spent FROM orders o"
        " JOIN users u ON u.id = o.buyer_id WHERE o.created_at >= datetime('now', ?) GROUP BY u.id ORDER BY spent DESC LIMIT 8", (since,),
    )
    top_listings = q(
        "SELECT o.listing_id, o.listing_title, SUM(o.quantity) AS qty, SUM(o.total) AS gmv FROM orders o"
        " WHERE o.created_at >= datetime('now', ?) GROUP BY o.listing_id ORDER BY gmv DESC LIMIT 8", (since,),
    )
    by_method = q(
        "SELECT d.method_name AS name, COUNT(d.id) AS n, COALESCE(SUM(d.amount), 0) AS total FROM deposits d"
        " WHERE d.status = 'approved' AND d.created_at >= datetime('now', ?) GROUP BY d.method_name ORDER BY total DESC", (since,),
    )
    coupon_rows = q(
        "SELECT c.code, COUNT(u.id) AS n, COALESCE(SUM(u.amount), 0) AS given FROM coupon_uses u JOIN coupons c ON c.id = u.coupon_id"
        " WHERE u.created_at >= datetime('now', ?) GROUP BY c.id ORDER BY given DESC LIMIT 8", (since,),
    )
    banner_rows = q("SELECT title, slot, views, clicks FROM banners ORDER BY clicks DESC, views DESC LIMIT 6")
    return render_template(
        "admin_reports.html", days=days, ranges=RANGES, kpi=kpi, mi=money_in, chart=chart, chart_orders=chart_orders, by_cat=by_cat,
        top_sellers=top_sellers, top_buyers=top_buyers, top_listings=top_listings, by_method=by_method, coupon_rows=coupon_rows,
        banner_rows=banner_rows, span=span,
    )


EXPORTS = {
    "siparisler": (
        "SELECT o.id, o.created_at, o.listing_title, b.username AS buyer, s.username AS seller, o.quantity, o.total, o.discount, o.coupon_code,"
        " o.commission_rate, o.commission, o.seller_earning FROM orders o JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id"
        " ORDER BY o.id DESC LIMIT 50000",
        ["No", "Tarih", "İlan", "Alıcı", "Satıcı", "Adet", "Toplam", "İndirim", "Kupon", "Oran %", "Komisyon", "Satıcı kazancı"],
        {"created_at": "dt", "total": "money", "discount": "money", "commission": "money", "seller_earning": "money"},
    ),
    "kullanicilar": (
        "SELECT id, username, email, created_at, last_login, is_seller, is_banned, kyc_status, balance, store_name, reg_ip FROM users ORDER BY id LIMIT 50000",
        ["No", "Kullanıcı", "E-posta", "Kayıt", "Son giriş", "Satıcı", "Engelli", "Kimlik", "Bakiye", "Mağaza", "Kayıt IP"],
        {"created_at": "dt", "last_login": "dt", "balance": "money"},
    ),
    "yuklemeler": (
        "SELECT d.id, d.created_at, u.username, d.method_name AS method, d.amount, d.status, d.reference FROM deposits d"
        " JOIN users u ON u.id = d.user_id ORDER BY d.id DESC LIMIT 50000",
        ["No", "Tarih", "Kullanıcı", "Yöntem", "Tutar", "Durum", "Referans"],
        {"created_at": "dt", "amount": "money"},
    ),
    "cekimler": (
        "SELECT w.id, w.created_at, u.username, w.method, w.amount, w.fee, w.net, w.status FROM withdrawals w"
        " JOIN users u ON u.id = w.user_id ORDER BY w.id DESC LIMIT 50000",
        ["No", "Tarih", "Kullanıcı", "Yöntem", "Tutar", "Kesinti", "Net", "Durum"],
        {"created_at": "dt", "amount": "money", "fee": "money", "net": "money"},
    ),
    "ilanlar": (
        "SELECT l.id, l.created_at, l.title, u.username AS seller, c.name AS category, l.price, l.old_price, l.status, l.sales_count, l.views FROM listings l"
        " JOIN users u ON u.id = l.seller_id JOIN categories c ON c.id = l.category_id ORDER BY l.id DESC LIMIT 50000",
        ["No", "Tarih", "Başlık", "Satıcı", "Kategori", "Fiyat", "Eski fiyat", "Durum", "Satış", "Görüntülenme"],
        {"created_at": "dt", "price": "money", "old_price": "money"},
    ),
}


@bp.route("/disa-aktar/<what>")
def export(what):
    if what not in EXPORTS:
        abort(404)
    sql, header, fmt = EXPORTS[what]
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(header)
    for r in q(sql):
        row = []
        for key in r.keys():
            v = r[key]
            kind = fmt.get(key)
            if kind == "dt":
                v = core.fmt_dt(v) if v else ""
            elif kind == "money":
                v = core.fmt_plain(v) if v else "0,00"
            row.append(_csv_safe("" if v is None else v))
        w.writerow(row)
    core.log_admin("Dışa aktarma", what)
    name = f"{what}-{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(buf.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={name}"})


# --------------------------------------------------------------------------- duyuru / toplu bildirim
@bp.route("/duyuru", methods=["GET", "POST"])
def broadcast():
    form = {}
    if request.method == "POST":
        form = request.form
        try:
            title, body = field("title", 100), field("body", 280)
            link = (request.form.get("link") or "").strip()[:200]
            if link and not (link.startswith("/") and not link.startswith("//")):
                raise BizError("Bağlantı site içi bir yol olmalı (örn. /ilanlar).")
            if len(title) < 3:
                raise BizError("Başlık en az 3 karakter olmalı.")
            aud = request.form.get("audience")
            base = "SELECT id FROM users WHERE is_banned = 0"
            args = []
            if aud == "sellers":
                base += " AND is_seller = 1"
            elif aud == "buyers":
                base += " AND id IN (SELECT DISTINCT buyer_id FROM orders)"
            elif aud == "user":
                target = q1("SELECT id FROM users WHERE username = ?", (field("username", 30),))
                if not target:
                    raise BizError("Kullanıcı bulunamadı.")
                base += " AND id = ?"
                args.append(target["id"])
            elif aud != "all":
                raise BizError("Hedef kitle seçilmeli.")
            with core.tx():
                cur = ex(f"INSERT INTO notifications(user_id, title, body, link) SELECT id, ?, ?, ? FROM ({base})", (title, body, link, *args))
            n = cur.rowcount
            core.log_admin("Bildirim gönderildi", f"{aud} ({n} kişi): {title[:60]}")
            flash(f"Bildirim {n} kullanıcıya gönderildi.", "ok")
            return redirect(url_for("admin.broadcast"))
        except BizError as err:
            flash(str(err), "bad")
    history = q("SELECT * FROM admin_log WHERE action = 'Bildirim gönderildi' ORDER BY id DESC LIMIT 12")
    counts = q1(
        "SELECT (SELECT COUNT(*) FROM users WHERE is_banned = 0) AS everyone,"
        " (SELECT COUNT(*) FROM users WHERE is_banned = 0 AND is_seller = 1) AS sellers,"
        " (SELECT COUNT(DISTINCT buyer_id) FROM orders) AS buyers"
    )
    return render_template("admin_broadcast.html", form=form, history=history, counts=counts)


# --------------------------------------------------------------------------- sistem, yedek, demo veri
def _dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


@bp.route("/sistem")
def system():
    if dbm.remote():
        db_size = q1("SELECT (SELECT page_count FROM pragma_page_count) * (SELECT page_size FROM pragma_page_size) AS s")["s"] or 0
    else:
        db_path = str(core.DB_PATH)
        db_size = sum(os.path.getsize(p) for p in (db_path, db_path + "-wal") if os.path.exists(p))
    media_bytes, media_count = storage.total_size()
    try:
        import flask
        flask_v = flask.__version__
    except Exception:  # pragma: no cover
        flask_v = "?"
    try:
        import PIL
        pil_v = PIL.__version__
    except Exception:  # pragma: no cover
        pil_v = "?"
    tables = {}
    for t in ("users", "listings", "listing_codes", "orders", "transactions", "notifications", "favorites", "login_events", "admin_log", "tickets"):
        tables[t] = q1(f"SELECT COUNT(*) AS n FROM {t}")["n"]
    checks = []

    def add(ok, title, hint):
        checks.append({"ok": ok, "title": title, "hint": hint})

    add(not core.ADMIN_PASSWORD_IS_PLAINTEXT, "Yönetici şifresi .env'de hash'li", "Düz metin ADMIN_PASSWORD yerine hash için sunucuda `python manage.py hash-admin` çalıştır.")
    add(core.ADMIN_PASSWORD_LENGTH == 0 or core.ADMIN_PASSWORD_LENGTH >= 12, "Yönetici şifresi yeterince uzun", "Yönetici şifresi en az 12 karakter olmalı.")
    add(len(core.SECRET_KEY) >= 32, "SECRET_KEY güçlü", ".env içindeki SECRET_KEY en az 32 rastgele karakter olmalı.")
    add(os.getenv("COOKIE_SECURE", "auto").lower() in ("1", "auto"), "Güvenli çerez açık", "HTTPS altında çerez otomatik Secure olur (COOKIE_SECURE=auto/1). Proxy arkasındaysan TRUST_PROXY=1 ekle.")
    add(not security.allowed_origins(), "CORS kapalı", "CORS_ORIGINS boş bırakılırsa hiçbir dış site API'ye tarayıcıdan erişemez.")
    add(os.getenv("DEBUG") != "1", "Hata ayıklama kapalı", "Canlıda DEBUG=1 kullanma.")
    add(bool(os.getenv("PAYMENT_WEBHOOK_SECRET")), "Ödeme webhook anahtarı tanımlı", "Otomatik ödeme entegrasyonu için PAYMENT_WEBHOOK_SECRET tanımla (kullanmıyorsan boş kalabilir).")
    add(bool(q1("SELECT 1 FROM payment_methods WHERE is_active = 1")), "En az bir ödeme yöntemi aktif", "Ödeme Yöntemleri sayfasından IBAN veya cüzdan bilgisi ekle.")
    add(core.setting("maintenance_mode", "0") == "0", "Site bakım modunda değil", "Bakım modu açık: yönetici dışında kimse siteye giremez.")
    add(core.setting("demo_loaded", "0") == "0", "Demo veri yüklü değil", "Demo veri yüklü; canlıya çıkmadan önce Araçlar bölümünden sil.")
    add(bool(core.setting("last_backup_at", "")), "Yedek alınmış", "Henüz yedek almadın; aşağıdaki düğmeyle indirebilirsin.")
    info = {
        "Python": platform.python_version(), "Flask": flask_v, "Veritabanı": "Turso (uzak libSQL)" if dbm.remote() else "SQLite " + sqlite3.sqlite_version, "Pillow": pil_v,
        "İşletim sistemi": f"{platform.system()} {platform.release()}", "Çalışma dizini": str(core.BASE_DIR),
    }
    demo_counts = q1("SELECT (SELECT COUNT(*) FROM listings WHERE is_demo = 1) AS listings, (SELECT COUNT(*) FROM users WHERE is_demo = 1 AND is_seller = 1) AS sellers, (SELECT COUNT(*) FROM reviews WHERE is_demo = 1) AS reviews")
    return render_template(
        "admin_system.html", db_size=_size(db_size), up_size=_size(media_bytes), tables=tables,
        checks=checks, info=info, last_backup=core.setting("last_backup_at", ""), demo_loaded=core.setting("demo_loaded", "0") == "1",
        demo_counts=demo_counts, demo_sales=core.setting("demo_sales", "1") == "1",
    )


def _sql_lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (bytes, bytearray)):
        return "X'" + bytes(v).hex() + "'"
    return "'" + str(v).replace("'", "''") + "'"


def _sql_dump():
    """Uzak veritabanı için metin yedeği (INSERT satırları). Görseller (media) dahil değildir; Turso panelinden de tam yedek alınabilir."""
    out = ["-- itemal yedeği (görseller hariç)", "PRAGMA foreign_keys = OFF;", "BEGIN;"]
    tables = [r["name"] for r in q("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name != 'media' ORDER BY name")]
    for t in tables:
        rows = q(f"SELECT * FROM {t}")
        for r in rows:
            cols = r.keys()
            out.append(f"INSERT INTO {t}({', '.join(cols)}) VALUES ({', '.join(_sql_lit(r[c]) for c in cols)});")
    out.append("COMMIT;")
    return "\n".join(out) + "\n"


@bp.post("/sistem/yedek")
def backup():
    if dbm.remote():
        data = _sql_dump().encode("utf-8")
        ext = "sql"
    else:
        src = sqlite3.connect(str(core.DB_PATH))
        mem = sqlite3.connect(":memory:")
        try:
            src.backup(mem)
            data = mem.serialize()
        finally:
            mem.close()
            src.close()
        ext = "db"
    ex("INSERT INTO settings(key, value) VALUES ('last_backup_at', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (core.utc_str(),))
    core.log_admin("Veritabanı yedeği indirildi", _size(len(data)))
    name = f"yedek-{datetime.now().strftime('%Y%m%d-%H%M')}.{ext}"
    return Response(bytes(data), mimetype="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={name}"})


@bp.post("/sistem/demo")
def demo_action():
    action = request.form.get("action")
    if action == "load":
        made = demo.load()
        if made:
            core.log_admin("Demo veri yüklendi", f"{made} ilan")
            flash(f"Demo veri yüklendi: {made} ilan, mağazalar ve yorumlar. Canlıya çıkmadan önce silmeyi unutma.", "info")
        else:
            flash("Demo veri zaten yüklü.", "info")
    elif action in ("sales_on", "sales_off"):
        ex("INSERT INTO settings(key, value) VALUES ('demo_sales', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", ("1" if action == "sales_on" else "0",))
        core.log_admin("Demo satışı", "açık" if action == "sales_on" else "kapalı")
        flash("Demo ilanlar satın alınabilir." if action == "sales_on" else "Demo ilanlar satışa kapatıldı.", "ok")
    elif action == "clear":
        n_l, n_u = demo.clear()
        core.log_admin("Demo veri silindi", f"{n_l} ilan, {n_u} satıcı")
        flash(f"Demo veri silindi ({n_l} ilan, {n_u} hesap).", "ok")
    else:
        abort(400)
    return redirect(url_for("admin.system"))

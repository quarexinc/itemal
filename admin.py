"""Yönetici paneli: /admin/...  (admin bilgileri .env dosyasından okunur)"""
import csv
import hmac
import io
import os
import re
import secrets
import sqlite3
import string
import time
from datetime import datetime

from flask import (
    Blueprint, Response, abort, flash, g, redirect, render_template, request, session, url_for,
)
from werkzeug.security import generate_password_hash

import adminsec
import security

import core
import services
import storage
from core import BizError, ex, field, q, q1

bp = Blueprint("admin", __name__, url_prefix=adminsec.URL_PREFIX)      # ADMIN_URL_PREFIX (varsayılan /admin)
TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

KYC_REJECT_REASONS = [
    "Fotoğraf bulanık veya okunmuyor",
    "Girilen bilgiler kimlikle uyuşmuyor",
    "Selfie, kimlik sahibiyle eşleşmiyor",
    "Kimlik geçersiz veya süresi dolmuş",
    "Görselde düzenleme/sahtecilik şüphesi",
    "Kimliğin bir yüzü eksik veya kesik",
    "Selfie'de kimlik net görünmüyor",
]


@bp.before_request
def _guard():
    # tam oturum yoksa yalnızca giriş / 2. adım sayfalarına izin verilir (adminsec.guard)
    return adminsec.guard()


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.translate(TR_MAP).lower()).strip("-")
    return s or "kategori"


def status_counts(table):
    rows = q(f"SELECT status, COUNT(*) AS c FROM {table} GROUP BY status")
    out = {"pending": 0, "approved": 0, "rejected": 0}
    out.update({r["status"]: r["c"] for r in rows})
    return out


def like(text):
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def random_password(n=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


# giriş, iki adımlı doğrulama, güvenlik sayfası ve çıkış rotaları: admin_auth.py (aynı blueprint'e eklenir)


# --------------------------------------------------------------------------- pano
@bp.route("/")
def dashboard():
    stats = q1(
        "SELECT (SELECT COUNT(*) FROM users) AS users,"
        " (SELECT COUNT(*) FROM users WHERE is_banned = 1) AS banned,"
        " (SELECT COUNT(*) FROM users WHERE is_seller = 1) AS sellers,"
        " (SELECT COUNT(*) FROM users WHERE date(created_at,'+3 hours') = date('now','+3 hours')) AS new_today,"
        " (SELECT COUNT(*) FROM listings WHERE status = 'active') AS listings,"
        " (SELECT COUNT(*) FROM orders) AS orders,"
        " (SELECT COALESCE(SUM(total), 0) FROM orders) AS gmv,"
        " (SELECT COALESCE(SUM(commission), 0) FROM orders) AS commission,"
        " (SELECT COALESCE(SUM(fee), 0) FROM withdrawals WHERE status = 'approved') AS wd_fees,"
        " (SELECT COALESCE(SUM(price), 0) FROM listing_dopings) AS doping,"
        " (SELECT COALESCE(SUM(balance), 0) FROM users) AS liabilities,"
        " (SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE status = 'approved') AS deposited,"
        " (SELECT COALESCE(SUM(net), 0) FROM withdrawals WHERE status = 'approved') AS paid_out,"
        " (SELECT COUNT(*) FROM listing_codes WHERE is_sold = 0) AS stock_codes,"
        " (SELECT COUNT(*) FROM tickets WHERE status != 'closed') AS open_tickets,"
        " (SELECT COUNT(*) FROM reviews WHERE is_hidden = 0 AND is_demo = 0) AS reviews"
    )
    chart_gmv = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, SUM(total) AS v FROM orders"
        " WHERE created_at >= datetime('now','-16 days') GROUP BY d"
    )
    chart_users = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, COUNT(*) AS v FROM users"
        " WHERE created_at >= datetime('now','-16 days') GROUP BY d"
    )
    recent_orders = q(
        "SELECT o.*, b.username AS buyer_name, s.username AS seller_name FROM orders o"
        " JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id ORDER BY o.id DESC LIMIT 8"
    )
    recent_users = q("SELECT id, username, email, created_at, kyc_status FROM users ORDER BY id DESC LIMIT 6")
    recent_log = q("SELECT * FROM admin_log ORDER BY id DESC LIMIT 6")
    recent_tickets = q(
        "SELECT t.*, u.username FROM tickets t JOIN users u ON u.id = t.user_id WHERE t.status != 'closed'"
        " ORDER BY (t.last_reply_by = 'user') DESC, t.updated_at DESC LIMIT 5"
    )
    chart_dep = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, SUM(amount) AS v FROM deposits WHERE status = 'approved'"
        " AND created_at >= datetime('now','-16 days') GROUP BY d"
    )
    week = q1(
        "SELECT (SELECT COALESCE(SUM(total), 0) FROM orders WHERE created_at >= datetime('now','-7 days')) AS gmv,"
        " (SELECT COALESCE(SUM(total), 0) FROM orders WHERE created_at >= datetime('now','-14 days') AND created_at < datetime('now','-7 days')) AS prev_gmv,"
        " (SELECT COUNT(*) FROM users WHERE created_at >= datetime('now','-7 days')) AS users,"
        " (SELECT COUNT(*) FROM users WHERE created_at >= datetime('now','-14 days') AND created_at < datetime('now','-7 days')) AS prev_users,"
        " (SELECT COALESCE(SUM(discount), 0) FROM orders) AS discounts,"
        " (SELECT COUNT(*) FROM coupons WHERE is_active = 1) AS coupons,"
        " (SELECT COUNT(*) FROM banners WHERE is_active = 1) AS banners"
    )
    top_cats = q(
        "SELECT c.name, c.color, COUNT(o.id) AS orders, COALESCE(SUM(o.total), 0) AS gmv FROM orders o"
        " JOIN listings l ON l.id = o.listing_id JOIN categories c ON c.id = l.category_id"
        " WHERE o.created_at >= datetime('now','-30 days') GROUP BY c.id ORDER BY gmv DESC LIMIT 6"
    )
    low_stock = q1(
        "SELECT COUNT(*) AS n FROM (SELECT l.id, (SELECT COUNT(*) FROM listing_codes k WHERE k.listing_id = l.id AND k.is_sold = 0) AS s"
        " FROM listings l WHERE l.status = 'active') WHERE s = 0"
    )["n"]
    return render_template(
        "admin_dashboard.html",
        stats=stats, chart_gmv=chart_gmv, chart_users=chart_users, recent_orders=recent_orders,
        recent_users=recent_users, recent_log=recent_log, recent_tickets=recent_tickets,
        chart_dep=chart_dep, week=week, top_cats=top_cats, out_of_stock=low_stock, demo_loaded=core.setting("demo_loaded", "0") == "1",
    )


# --------------------------------------------------------------------------- kullanıcılar
@bp.route("/kullanicilar")
def users():
    text = request.args.get("q", "").strip()[:60]
    flt = request.args.get("filtre", "")
    where, args = ["1=1"], []
    if text:
        if text.isdigit():
            where.append("(u.id = ? OR u.username LIKE ? ESCAPE '\\')")
            args += [int(text), like(text)]
        else:
            where.append("(u.username LIKE ? ESCAPE '\\' OR u.email LIKE ? ESCAPE '\\')")
            args += [like(text)] * 2
    if flt == "seller":
        where.append("u.is_seller = 1")
    elif flt == "banned":
        where.append("u.is_banned = 1")
    elif flt in ("pending", "approved", "rejected", "none"):
        where.append("u.kyc_status = ?")
        args.append(flt)
    page = core.paginate(
        "SELECT u.*, (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.id) AS buys,"
        " (SELECT COALESCE(SUM(quantity), 0) FROM orders o WHERE o.seller_id = u.id) AS sold"
        " FROM users u WHERE " + " AND ".join(where) + " ORDER BY u.id DESC",
        args, 20,
    )
    return render_template("admin_users.html", page=page, text=text, flt=flt)


@bp.route("/kullanici/yeni", methods=["GET", "POST"])
def user_new():
    form = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ("username", "email", "store_name", "balance")}
        form["is_seller"] = bool(request.form.get("is_seller"))
        form["kyc_ok"] = bool(request.form.get("kyc_ok"))
        try:
            username, email = field("username", 30), field("email", 120).lower()
            password = request.form.get("password", "") or random_password()
            generated = not request.form.get("password")
            store = field("store_name", 40)
            balance = core.to_kurus(request.form.get("balance")) if request.form.get("balance", "").strip() else 0
            if not core.USERNAME_RE.match(username):
                raise BizError("Kullanıcı adı 3-20 karakter olmalı; yalnızca harf, rakam ve alt çizgi içerebilir.")
            if not core.EMAIL_RE.match(email):
                raise BizError("Geçerli bir e-posta adresi gir.")
            if not 8 <= len(password) <= 128:
                raise BizError("Şifre en az 8 karakter olmalı.")
            if balance is None or balance < 0:
                raise BizError("Açılış bakiyesi geçersiz.")
            if form["is_seller"]:
                if not 3 <= len(store) <= 40:
                    raise BizError("Satıcı için mağaza adı (3-40 karakter) gir.")
                if q1("SELECT 1 FROM users WHERE store_name = ? COLLATE NOCASE", (store,)):
                    raise BizError("Bu mağaza adı kullanılıyor.")
            with core.tx():
                cur = ex(
                    "INSERT INTO users(username, email, password_hash, is_seller, kyc_status, store_name) VALUES (?,?,?,?,?,?)",
                    (username, email, generate_password_hash(password), 1 if form["is_seller"] else 0,
                     "approved" if form["kyc_ok"] else "none", store if form["is_seller"] else ""),
                )
                if balance:
                    core.change_balance(cur.lastrowid, balance, "admin", "Yönetici: açılış bakiyesi", "admin", None)
            core.log_admin("Üye oluşturuldu", f"{username} (#{cur.lastrowid}) satıcı={form['is_seller']} kimlik={form['kyc_ok']}")
        except sqlite3.IntegrityError:
            flash("Bu kullanıcı adı veya e-posta zaten kayıtlı.", "bad")
        except BizError as err:
            flash(str(err), "bad")
        else:
            flash(f"Üye oluşturuldu.{' Geçici şifre: ' + password + ' (bir daha gösterilmeyecek)' if generated else ''}", "info")
            return redirect(url_for("admin.user", uid=cur.lastrowid))
    return render_template("admin_user_new.html", form=form)


def _same_ip(uid, u):
    ips = sorted({ip for ip in (u["reg_ip"], u["last_ip"]) if ip})
    if not ips:
        return []
    marks = ",".join("?" * len(ips))
    return q(
        f"SELECT id, username, is_banned FROM users WHERE id != ? AND (reg_ip IN ({marks}) OR last_ip IN ({marks})) LIMIT 12",
        (uid, *ips, *ips),
    )


@bp.route("/kullanici/<int:uid>")
def user(uid):
    u = q1("SELECT * FROM users WHERE id = ?", (uid,))
    if not u:
        abort(404)
    stats = q1(
        "SELECT (SELECT COUNT(*) FROM orders WHERE buyer_id = ?1) AS buys,"
        " (SELECT COALESCE(SUM(total), 0) FROM orders WHERE buyer_id = ?1) AS spent,"
        " (SELECT COALESCE(SUM(quantity), 0) FROM orders WHERE seller_id = ?1) AS sold,"
        " (SELECT COALESCE(SUM(seller_earning), 0) FROM orders WHERE seller_id = ?1) AS earned,"
        " (SELECT COALESCE(SUM(commission), 0) FROM orders WHERE seller_id = ?1) AS fees,"
        " (SELECT COUNT(*) FROM listings WHERE seller_id = ?1 AND status != 'removed') AS listings,"
        " (SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE user_id = ?1 AND status = 'approved') AS deposited,"
        " (SELECT COALESCE(SUM(net), 0) FROM withdrawals WHERE user_id = ?1 AND status = 'approved') AS withdrawn,"
        " (SELECT COUNT(*) FROM tickets WHERE user_id = ?1) AS tickets,"
        " (SELECT COUNT(*) FROM api_keys WHERE user_id = ?1 AND is_active = 1) AS api_keys",
        (uid,),
    )
    manual = {r["badge"] for r in q("SELECT badge FROM user_badges WHERE user_id = ?", (uid,))}
    return render_template(
        "admin_user.html",
        u=u, stats=stats, withdrawable=core.withdrawable(uid), manual=manual,
        badges=services.user_badges(u), seller_stats=services.seller_stats(uid), manual_badges=services.MANUAL_BADGES,
        eff_rate=core.setting_pct("commission_percent", "5"),
        kyc=q1("SELECT * FROM kyc_requests WHERE user_id = ? ORDER BY id DESC LIMIT 1", (uid,)),
        application=q1("SELECT * FROM seller_applications WHERE user_id = ? ORDER BY id DESC LIMIT 1", (uid,)),
        txs=q("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 15", (uid,)),
        orders=q("SELECT * FROM orders WHERE buyer_id = ? OR seller_id = ? ORDER BY id DESC LIMIT 10", (uid, uid)),
        lst=q(core.LISTING_SELECT + " WHERE l.seller_id = ? AND l.status != 'removed' ORDER BY l.id DESC LIMIT 10", (uid,)),
        events=q("SELECT * FROM login_events WHERE user_id = ? ORDER BY id DESC LIMIT 8", (uid,)),
        same_ip=_same_ip(uid, u),
    )


@bp.post("/kullanici/<int:uid>/islem")
def user_action(uid):
    u = q1("SELECT * FROM users WHERE id = ?", (uid,))
    if not u:
        abort(404)
    action = request.form.get("action")
    try:
        if action == "ban":
            ex("UPDATE users SET is_banned = 1 WHERE id = ?", (uid,))
            core.log_admin("Kullanıcı engellendi", f"{u['username']} (#{uid}) - {field('reason', 200)}")
            flash(f"{u['username']} engellendi; ilanları yayından kalktı.", "ok")
        elif action == "unban":
            ex("UPDATE users SET is_banned = 0 WHERE id = ?", (uid,))
            core.log_admin("Engel kaldırıldı", f"{u['username']} (#{uid})")
            flash("Engel kaldırıldı.", "ok")
        elif action == "seller_on":
            ex("UPDATE users SET is_seller = 1 WHERE id = ?", (uid,))
            core.log_admin("Satıcı yetkisi verildi", f"{u['username']} (#{uid})")
            flash("Satıcı yetkisi verildi.", "ok")
        elif action == "seller_off":
            with core.tx():
                ex("UPDATE users SET is_seller = 0 WHERE id = ?", (uid,))
                ex("UPDATE listings SET status = 'paused' WHERE seller_id = ? AND status = 'active'", (uid,))
            core.log_admin("Satıcı yetkisi alındı", f"{u['username']} (#{uid})")
            flash("Satıcı yetkisi alındı; aktif ilanları duraklatıldı.", "ok")
        elif action == "balance":
            kind = request.form.get("type")
            amount = core.to_kurus(request.form.get("amount"))
            reason = field("reason", 200)
            if amount is None or amount <= 0:
                raise BizError("Geçerli bir tutar gir.")
            if len(reason) < 3:
                raise BizError("İşlem için bir gerekçe yaz.")
            with core.tx():
                if kind == "add":
                    core.change_balance(uid, amount, "admin", f"Yönetici: {reason}", "admin", None)
                elif kind == "bonus":
                    core.change_balance(uid, amount, "bonus", f"Yönetici: {reason}", "admin", None)
                elif kind == "sub":
                    cur = q1("SELECT balance FROM users WHERE id = ?", (uid,))["balance"]
                    if amount > cur:
                        raise BizError("Düşülecek tutar kullanıcının bakiyesinden büyük.")
                    core.change_balance(uid, -amount, "admin", f"Yönetici: {reason}", "admin", None)
                else:
                    raise BizError("Geçersiz işlem türü.")
                if kind in ("add", "bonus"):
                    services.notify(uid, "Bakiyeniz onaylandı", f"{core.fmt_signed(amount)} hesabınıza eklendi. {reason}", url_for("balance"))
                else:
                    services.notify(uid, "Bakiyenizden düşüldü", f"{core.fmt_signed(-amount)} - {reason}", url_for("transactions"))
            core.log_admin("Bakiye düzenlendi", f"{u['username']} (#{uid}) {kind} {core.fmt_money(amount)} - {reason}")
            flash("Bakiye güncellendi.", "ok")
        elif action == "reset_pw":
            temp = random_password()
            ex("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(temp), uid))
            core.log_admin("Şifre sıfırlandı", f"{u['username']} (#{uid})")
            flash(f"Geçici şifre: {temp}  (bir daha gösterilmeyecek; kullanıcıya ilet ve değiştirmesini söyle)", "info")
        elif action == "kyc_reset":
            ex("UPDATE users SET kyc_status = 'none' WHERE id = ?", (uid,))
            core.log_admin("Kimlik durumu sıfırlandı", f"{u['username']} (#{uid})")
            flash("Kimlik durumu sıfırlandı; kullanıcı yeniden başvurabilir.", "ok")
        elif action == "commission":
            rate = services.parse_rate(request.form.get("rate"))
            ex("UPDATE users SET commission_rate = ? WHERE id = ?", (rate, uid))
            core.log_admin("Satıcı komisyon oranı", f"{u['username']} (#{uid}) -> {'genel oran' if rate is None else '%' + str(rate)}")
            flash("Genel oran uygulanacak." if rate is None else f"Bu satıcı için komisyon %{rate} olarak ayarlandı.", "ok")
        elif action in ("badge_add", "badge_remove"):
            badge = request.form.get("badge")
            if badge not in services.MANUAL_BADGES:
                raise BizError("Geçersiz rozet.")
            if action == "badge_add":
                ex("INSERT OR IGNORE INTO user_badges(user_id, badge) VALUES (?,?)", (uid, badge))
            else:
                ex("DELETE FROM user_badges WHERE user_id = ? AND badge = ?", (uid, badge))
            core.log_admin("Rozet " + ("verildi" if action == "badge_add" else "alındı"), f"{u['username']} (#{uid}) {badge}")
            flash("Rozet güncellendi.", "ok")
        elif action == "note":
            ex("UPDATE users SET admin_note = ? WHERE id = ?", (field("admin_note", 1000), uid))
            core.log_admin("Kullanıcı notu", f"{u['username']} (#{uid})")
            flash("Not kaydedildi.", "ok")
        elif action == "notify":
            title, body = field("title", 100), field("body", 280)
            if len(title) < 3:
                raise BizError("Bildirim başlığı en az 3 karakter olmalı.")
            services.notify(uid, title, body, "")
            core.log_admin("Kullanıcıya bildirim", f"{u['username']} (#{uid}): {title[:60]}")
            flash("Bildirim gönderildi.", "ok")
        elif action == "avatar_remove":
            services.delete_avatar(u["avatar"])
            ex("UPDATE users SET avatar = '' WHERE id = ?", (uid,))
            core.log_admin("Profil fotoğrafı kaldırıldı", f"{u['username']} (#{uid})")
            flash("Profil fotoğrafı kaldırıldı.", "ok")
        else:
            abort(400)
    except BizError as err:
        flash(str(err), "bad")
    return redirect(url_for("admin.user", uid=uid))


# --------------------------------------------------------------------------- ilanlar
@bp.route("/ilanlar")
def listings():
    text = request.args.get("q", "").strip()[:60]
    status = request.args.get("durum", "")
    where, args = ["1=1"], []
    if text:
        where.append("(l.title LIKE ? ESCAPE '\\' OR u.username LIKE ? ESCAPE '\\')")
        args += [like(text)] * 2
    if status in ("active", "paused", "blocked", "removed"):
        where.append("l.status = ?")
        args.append(status)
    elif status == "featured":
        where.append("l.is_featured = 1")
    page = core.paginate(core.LISTING_SELECT + " WHERE " + " AND ".join(where) + " ORDER BY l.id DESC", args, 20)
    return render_template("admin_listings.html", page=page, text=text, status=status)


def _admin_listing_cats():
    return q("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id")


@bp.route("/ilan/yeni", methods=["GET", "POST"])
def listing_new():
    form = {}
    cover = ""
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ("seller", "title", "description", "price", "old_price", "category_id", "codes")}
        form["make_seller"] = bool(request.form.get("make_seller"))
        try:
            seller = q1("SELECT * FROM users WHERE username = ?", (field("seller", 30),))
            if not seller or seller["is_banned"]:
                raise BizError("Satıcı kullanıcı bulunamadı veya engelli.")
            data = services.read_listing_form()
            codes = core.parse_codes(request.form.get("codes"))
            if not codes:
                raise BizError("En az bir e-pin kodu ekle (her satıra bir kod).")
            if not core.can_sell(seller):
                if not form["make_seller"]:
                    raise BizError("Bu kullanıcı satıcı değil. 'Bu kullanıcıyı satıcı yap' kutusunu işaretle.")
            file = request.files.get("cover")
            if file and file.filename:
                cover = services.save_cover(file)
            elif core.setting("require_cover", "1") == "1":
                raise BizError("Kapak görseli yükle.")
            with core.tx():
                if not core.can_sell(seller):
                    ex("UPDATE users SET is_seller = 1, store_name = CASE WHEN store_name = '' THEN username ELSE store_name END WHERE id = ?", (seller["id"],))
                cur = ex(
                    "INSERT INTO listings(seller_id, category_id, title, description, price, old_price, cover) VALUES (?,?,?,?,?,?,?)",
                    (seller["id"], data["category_id"], data["title"], data["description"], data["price"], data["old_price"], cover),
                )
                for c in codes:
                    ex("INSERT INTO listing_codes(listing_id, code) VALUES (?,?)", (cur.lastrowid, c))
            core.log_admin("İlan oluşturuldu", f"#{cur.lastrowid} {data['title'][:50]} satıcı {seller['username']}")
        except BizError as err:
            services.delete_cover(cover)
            flash(str(err), "bad")
        else:
            flash(f"İlan oluşturuldu ({len(codes)} kod stoğa eklendi).", "ok")
            return redirect(url_for("admin.listings"))
    sellers = q("SELECT username FROM users WHERE is_banned = 0 ORDER BY is_seller DESC, username LIMIT 500")
    return render_template("admin_listing_form.html", form=form, cats=_admin_listing_cats(), item=None, sellers=sellers)


@bp.route("/ilan/<int:lid>/duzenle", methods=["GET", "POST"])
def listing_edit(lid):
    item = q1(core.LISTING_SELECT + " WHERE l.id = ?", (lid,))
    if not item:
        abort(404)
    if request.method == "POST":
        new_cover = ""
        try:
            data = services.read_listing_form()
            file = request.files.get("cover")
            cover = item["cover"]
            if file and file.filename:
                new_cover = cover = services.save_cover(file)
            with core.tx():
                ex(
                    "UPDATE listings SET title = ?, description = ?, price = ?, old_price = ?, category_id = ?, cover = ?,"
                    " is_deal = CASE WHEN ? > price THEN is_deal ELSE 0 END, updated_at = datetime('now') WHERE id = ?",
                    (data["title"], data["description"], data["price"], data["old_price"], data["category_id"], cover, data["old_price"], lid),
                )
                codes = core.parse_codes(request.form.get("codes"))
                existing = {r["code"] for r in q("SELECT code FROM listing_codes WHERE listing_id = ?", (lid,))}
                fresh = [c for c in codes if c not in existing]
                for c in fresh:
                    ex("INSERT INTO listing_codes(listing_id, code) VALUES (?,?)", (lid, c))
            if new_cover and item["cover"]:
                services.delete_cover(item["cover"])
            core.log_admin("İlan düzenlendi", f"#{lid} {data['title'][:50]} (+{len(fresh)} kod)")
        except BizError as err:
            services.delete_cover(new_cover)
            flash(str(err), "bad")
        else:
            flash("İlan güncellendi." + (f" {len(fresh)} yeni kod stoğa eklendi." if fresh else ""), "ok")
            return redirect(url_for("admin.listings"))
    form = {
        "title": item["title"], "description": item["description"], "price": core.fmt_plain(item["price"]),
        "category_id": item["category_id"], "seller": item["seller_name"], "codes": "",
        "old_price": core.fmt_plain(item["old_price"]) if item["old_price"] else "",
    }
    if request.method == "POST":
        form.update({k: request.form.get(k, "") for k in ("title", "description", "price", "old_price", "category_id", "codes")})
    return render_template("admin_listing_form.html", form=form, cats=_admin_listing_cats(), item=item, sellers=[])


@bp.post("/ilan/<int:lid>/durum")
def listing_status(lid):
    new = request.form.get("status")
    if new not in ("active", "paused", "blocked", "removed"):
        abort(400)
    item = q1("SELECT title, seller_id FROM listings WHERE id = ?", (lid,))
    if not item:
        abort(404)
    ex("UPDATE listings SET status = ?, updated_at = datetime('now') WHERE id = ?", (new, lid))
    if new in ("blocked", "removed"):
        services.notify(item["seller_id"], "İlanın yayından kaldırıldı", f"{item['title'][:80]} yönetim tarafından {'engellendi' if new == 'blocked' else 'kaldırıldı'}.", url_for("seller.listings"))
    core.log_admin("İlan durumu değişti", f"#{lid} {item['title'][:50]} -> {new}")
    flash("İlan durumu güncellendi.", "ok")
    return redirect(request.referrer or url_for("admin.listings"))


@bp.post("/ilan/<int:lid>/one-cikar")
def listing_feature(lid):
    item = q1("SELECT title, is_featured FROM listings WHERE id = ?", (lid,))
    if not item:
        abort(404)
    new = 0 if item["is_featured"] else 1
    ex("UPDATE listings SET is_featured = ? WHERE id = ?", (new, lid))
    core.log_admin("İlan öne çıkarma", f"#{lid} {item['title'][:50]} -> {'açık' if new else 'kapalı'}")
    flash("İlan öne çıkarıldı." if new else "İlan öne çıkanlardan kaldırıldı.", "ok")
    return redirect(request.referrer or url_for("admin.listings"))


@bp.route("/siparisler")
def orders():
    text = request.args.get("q", "").strip()[:60]
    where, args = ["1=1"], []
    if text:
        if text.lstrip("#").isdigit():
            where.append("o.id = ?")
            args.append(int(text.lstrip("#")))
        else:
            where.append("(b.username LIKE ? ESCAPE '\\' OR s.username LIKE ? ESCAPE '\\' OR o.listing_title LIKE ? ESCAPE '\\')")
            args += [like(text)] * 3
    sql = (
        "SELECT o.*, b.username AS buyer_name, s.username AS seller_name FROM orders o"
        " JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id"
        " WHERE " + " AND ".join(where) + " ORDER BY o.id DESC"
    )
    page = core.paginate(sql, args, 20)
    sums = q1(
        f"SELECT COALESCE(SUM(quantity),0) AS qty, COALESCE(SUM(total),0) AS gross, COALESCE(SUM(commission),0) AS fee FROM ({sql})",
        args,
    )
    return render_template("admin_orders.html", page=page, text=text, sums=sums)


# --------------------------------------------------------------------------- depozito / çekim
def status_filter(default="pending"):
    status = request.args.get("durum", default)
    return status if status in ("pending", "approved", "rejected", "all") else default


@bp.route("/depozitolar")
def deposits():
    status = status_filter()
    where = "" if status == "all" else "WHERE d.status = ?"
    page = core.paginate(
        "SELECT d.*, u.username FROM deposits d JOIN users u ON u.id = d.user_id " + where + " ORDER BY d.id DESC",
        () if status == "all" else (status,), 20,
    )
    return render_template("admin_deposits.html", page=page, status=status, counts=status_counts("deposits"))


@bp.post("/depozito/<int:did>")
def deposit_action(did):
    action = request.form.get("action")
    note = field("note", 300)
    try:
        with core.tx():
            d = q1("SELECT * FROM deposits WHERE id = ?", (did,))
            if not d:
                abort(404)
            if d["status"] != "pending":
                raise BizError("Bu talep zaten sonuçlandırılmış.")
            if action == "approve":
                ex("UPDATE deposits SET status = 'approved', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (note, did))
                core.change_balance(d["user_id"], d["amount"], "deposit", f"Yükleme #{did} - {d['method_name']}", "deposit", did)
                bonus = int(d["bonus"] or 0)
                if bonus > 0:
                    core.change_balance(d["user_id"], bonus, "deposit", f"Yükleme bonusu #{did} - {d['method_name']}", "deposit", did)
                total = d["amount"] + bonus
                core.log_admin("Yükleme onaylandı", f"#{did} {core.fmt_money(d['amount'])}" + (f" + bonus {core.fmt_money(bonus)}" if bonus else "") + f" kullanıcı #{d['user_id']}")
                services.notify(
                    d["user_id"], "Bakiyeniz onaylandı",
                    f"{core.fmt_signed(total)} hesabınıza eklendi. Ödemeniz onaylandı." + (f" ({core.fmt_money(bonus)} yükleme bonusu dahil)" if bonus else ""),
                    url_for("balance"), kind="ok",
                )
                flash(f"Yükleme onaylandı, {core.fmt_money(total)} bakiyeye eklendi.", "ok")
            elif action == "reject":
                ex("UPDATE deposits SET status = 'rejected', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (note, did))
                core.log_admin("Yükleme reddedildi", f"#{did} kullanıcı #{d['user_id']} - {note}")
                services.notify(d["user_id"], "Yükleme talebin reddedildi", note or "Ayrıntı için destek talebi açabilirsin.", url_for("balance"))
                flash("Yükleme talebi reddedildi.", "ok")
            else:
                abort(400)
    except BizError as err:
        flash(str(err), "bad")
    return redirect(request.referrer or url_for("admin.deposits"))


@bp.route("/cekimler")
def withdrawals():
    status = status_filter()
    where = "" if status == "all" else "WHERE w.status = ?"
    page = core.paginate(
        "SELECT w.*, u.username,"
        " (SELECT full_name FROM kyc_requests k WHERE k.user_id = w.user_id AND k.status = 'approved' ORDER BY k.id DESC LIMIT 1) AS kyc_name"
        " FROM withdrawals w JOIN users u ON u.id = w.user_id " + where + " ORDER BY w.id DESC",
        () if status == "all" else (status,), 20,
    )
    return render_template("admin_withdrawals.html", page=page, status=status, counts=status_counts("withdrawals"))


@bp.post("/cekim/<int:wid>")
def withdrawal_action(wid):
    action = request.form.get("action")
    note = field("note", 300)
    try:
        with core.tx():
            w = q1("SELECT * FROM withdrawals WHERE id = ?", (wid,))
            if not w:
                abort(404)
            if w["status"] != "pending":
                raise BizError("Bu talep zaten sonuçlandırılmış.")
            if action == "approve":
                ex("UPDATE withdrawals SET status = 'approved', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (note, wid))
                core.log_admin("Çekim onaylandı", f"#{wid} net {core.fmt_money(w['net'])} kullanıcı #{w['user_id']}")
                services.notify(w["user_id"], "Çekim talebin onaylandı", f"{core.fmt_money(w['net'])} ödeme yapılacak.", url_for("withdraw"))
                flash(f"Çekim onaylandı. Kullanıcıya {core.fmt_money(w['net'])} ödemeyi unutma.", "ok")
            elif action == "reject":
                ex("UPDATE withdrawals SET status = 'rejected', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (note, wid))
                core.change_balance(w["user_id"], w["amount"], "withdraw_refund", f"Çekim #{wid} reddedildi, iade", "withdrawal", wid)
                core.log_admin("Çekim reddedildi", f"#{wid} {core.fmt_money(w['amount'])} iade edildi - {note}")
                services.notify(w["user_id"], "Çekim talebin reddedildi", (note or "Tutar bakiyene iade edildi."), url_for("withdraw"))
                flash("Çekim reddedildi, tutar kullanıcının bakiyesine iade edildi.", "ok")
            else:
                abort(400)
    except BizError as err:
        flash(str(err), "bad")
    return redirect(request.referrer or url_for("admin.withdrawals"))


# --------------------------------------------------------------------------- satıcı başvuruları
@bp.route("/saticilar")
def sellers():
    status = status_filter()
    where = "" if status == "all" else "WHERE a.status = ?"
    page = core.paginate(
        "SELECT a.*, u.username, u.email, u.kyc_status FROM seller_applications a JOIN users u ON u.id = a.user_id "
        + where + " ORDER BY a.id DESC",
        () if status == "all" else (status,), 20,
    )
    return render_template("admin_sellers.html", page=page, status=status, counts=status_counts("seller_applications"))


@bp.post("/satici/<int:aid>")
def seller_action(aid):
    action = request.form.get("action")
    note = field("note", 300)
    try:
        with core.tx():
            a = q1("SELECT * FROM seller_applications WHERE id = ?", (aid,))
            if not a:
                abort(404)
            if a["status"] != "pending":
                raise BizError("Bu başvuru zaten sonuçlandırılmış.")
            if action == "approve":
                ex("UPDATE seller_applications SET status = 'approved', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (note, aid))
                ex("UPDATE users SET is_seller = 1, store_name = ?, store_desc = ? WHERE id = ?", (a["store_name"], a["description"], a["user_id"]))
                core.log_admin("Satıcı başvurusu onaylandı", f"#{aid} kullanıcı #{a['user_id']} ({a['store_name']})")
                services.notify(a["user_id"], "Satıcı başvurun onaylandı", "Artık ilan oluşturabilirsin.", url_for("seller.dashboard"))
                flash("Başvuru onaylandı; kullanıcı artık satıcı.", "ok")
            elif action == "reject":
                ex("UPDATE seller_applications SET status = 'rejected', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (note, aid))
                core.log_admin("Satıcı başvurusu reddedildi", f"#{aid} kullanıcı #{a['user_id']} - {note}")
                services.notify(a["user_id"], "Satıcı başvurun reddedildi", note or "Ayrıntı için destek ile iletişime geç.", url_for("seller_apply"))
                flash("Başvuru reddedildi.", "ok")
            else:
                abort(400)
    except sqlite3.IntegrityError:
        flash("İşlem yapılamadı.", "bad")
    except BizError as err:
        flash(str(err), "bad")
    return redirect(request.referrer or url_for("admin.sellers"))


# --------------------------------------------------------------------------- kimlik incelemesi
@bp.route("/kimlik")
def kyc():
    status = status_filter()
    where = "" if status == "all" else "WHERE k.status = ?"
    page = core.paginate(
        "SELECT k.*, u.username, u.email, u.created_at AS user_created, u.phone FROM kyc_requests k JOIN users u ON u.id = k.user_id "
        + where + " ORDER BY k.id DESC",
        () if status == "all" else (status,), 6,
    )
    items = []
    for r in page["rows"]:
        same_name = q(
            "SELECT DISTINCT u.username FROM kyc_requests k2 JOIN users u ON u.id = k2.user_id"
            " WHERE k2.user_id != ? AND k2.full_name = ? COLLATE NOCASE",
            (r["user_id"], r["full_name"]),
        )
        previous = q1(
            "SELECT COUNT(*) AS c FROM kyc_requests WHERE user_id = ? AND id < ? AND status = 'rejected'", (r["user_id"], r["id"])
        )["c"]
        items.append({
            "r": r, "flags": [f for f in (r["flags"] or "").split("\n") if f],
            "same_name": [s["username"] for s in same_name], "prev_rejects": previous,
        })
    return render_template(
        "admin_kyc.html", page=page, items=items, status=status, counts=status_counts("kyc_requests"), reasons=KYC_REJECT_REASONS
    )


@bp.post("/kimlik/<int:kid>")
def kyc_action(kid):
    action = request.form.get("action")
    note = field("note", 300)
    try:
        with core.tx():
            k = q1("SELECT * FROM kyc_requests WHERE id = ?", (kid,))
            if not k:
                abort(404)
            if k["status"] != "pending":
                raise BizError("Bu başvuru zaten sonuçlandırılmış.")
            if action == "approve":
                checks = [c for c in ("doc", "data", "face") if request.form.get("chk_" + c)]
                if len(checks) < 3:
                    raise BizError("Onaylamak için üç kontrol kutusunu da işaretlemelisin (belge, bilgiler, yüz eşleşmesi).")
                ex(
                    "UPDATE kyc_requests SET status = 'approved', admin_note = ?, checklist = ?, reviewed_at = datetime('now') WHERE id = ?",
                    (note, ",".join(checks), kid),
                )
                ex("UPDATE users SET kyc_status = 'approved' WHERE id = ?", (k["user_id"],))
                core.log_admin("Kimlik onaylandı", f"#{kid} kullanıcı #{k['user_id']}")
                services.notify(k["user_id"], "Kimliğin doğrulandı", "Artık çekim talebi oluşturabilirsin.", url_for("kyc"))
                flash("Kimlik onaylandı.", "ok")
            elif action == "reject":
                reason = request.form.get("reason", "")
                if reason not in KYC_REJECT_REASONS and len(note) < 3:
                    raise BizError("Bir ret nedeni seç veya açıklama yaz; kullanıcıya gösterilecek.")
                full_note = (reason + (" - " + note if note else "")) if reason in KYC_REJECT_REASONS else note
                ex(
                    "UPDATE kyc_requests SET status = 'rejected', admin_note = ?, reviewed_at = datetime('now') WHERE id = ?",
                    (full_note, kid),
                )
                ex("UPDATE users SET kyc_status = 'rejected' WHERE id = ?", (k["user_id"],))
                core.log_admin("Kimlik reddedildi", f"#{kid} kullanıcı #{k['user_id']} - {full_note}")
                services.notify(k["user_id"], "Kimlik başvurun reddedildi", full_note, url_for("kyc"))
                flash("Kimlik reddedildi; kullanıcı yeniden başvurabilir.", "ok")
            else:
                abort(400)
    except BizError as err:
        flash(str(err), "bad")
    return redirect(request.referrer or url_for("admin.kyc"))


@bp.route("/kimlik/<int:kid>/dosya/<which>")
def kyc_file(kid, which):
    column = {"on": "id_front", "arka": "id_back", "selfie": "selfie"}.get(which)
    row = q1("SELECT * FROM kyc_requests WHERE id = ?", (kid,))
    if not column or not row:
        abort(404)
    found = storage.get("kyc", row[column]) if row[column] else None
    if not found:
        abort(404)
    resp = Response(found[1], mimetype=found[0])
    resp.headers["Cache-Control"] = "private, no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


# --------------------------------------------------------------------------- destek talepleri
@bp.route("/destek")
def tickets():
    status = request.args.get("durum", "open")
    if status not in ("open", "answered", "closed", "all"):
        status = "open"
    text = request.args.get("q", "").strip()[:60]
    prio = request.args.get("oncelik", "")
    where, args = ["1=1"], []
    if status != "all":
        where.append("t.status = ?")
        args.append(status)
    if prio in ("normal", "high", "urgent"):
        where.append("t.priority = ?")
        args.append(prio)
    if text:
        if text.lstrip("#").isdigit():
            where.append("t.id = ?")
            args.append(int(text.lstrip("#")))
        else:
            where.append("(t.subject LIKE ? ESCAPE '\\' OR u.username LIKE ? ESCAPE '\\')")
            args += [like(text)] * 2
    page = core.paginate(
        "SELECT t.*, u.username FROM tickets t JOIN users u ON u.id = t.user_id WHERE " + " AND ".join(where)
        + " ORDER BY (t.priority = 'urgent') DESC, (t.priority = 'high') DESC, t.updated_at DESC",
        args, 20,
    )
    rows = q("SELECT status, COUNT(*) AS c FROM tickets GROUP BY status")
    counts = {"open": 0, "answered": 0, "closed": 0}
    counts.update({r["status"]: r["c"] for r in rows})
    return render_template("admin_tickets.html", page=page, status=status, text=text, prio=prio, counts=counts)


@bp.route("/destek/<int:tid>", methods=["GET", "POST"])
def ticket(tid):
    t = q1("SELECT t.*, u.username, u.email, u.kyc_status FROM tickets t JOIN users u ON u.id = t.user_id WHERE t.id = ?", (tid,))
    if not t:
        abort(404)
    if request.method == "POST":
        action = request.form.get("action")
        body = services.clean_message(request.form.get("message"), 3000)
        if action == "reply":
            if len(body) < 2:
                flash("Yanıt boş olamaz.", "bad")
            else:
                with core.tx():
                    ex("INSERT INTO ticket_messages(ticket_id, author, body) VALUES (?,?,?)", (tid, "staff", body))
                    ex(
                        "UPDATE tickets SET status = ?, last_reply_by = 'staff', updated_at = datetime('now') WHERE id = ?",
                        ("closed" if request.form.get("close") else "answered", tid),
                    )
                services.notify(t["user_id"], "Destek talebin yanıtlandı", t["subject"][:100], url_for("ticket_view", tid=tid))
                core.log_admin("Destek talebi yanıtlandı", f"#{tid}")
                flash("Yanıt gönderildi.", "ok")
        elif action == "note":
            if len(body) < 2:
                flash("Not boş olamaz.", "bad")
            else:
                ex("INSERT INTO ticket_messages(ticket_id, author, body, is_internal) VALUES (?,?,?,1)", (tid, "staff", body))
                flash("İç not eklendi (kullanıcı göremez).", "ok")
        elif action == "status" and request.form.get("status") in ("open", "answered", "closed"):
            ex("UPDATE tickets SET status = ?, updated_at = datetime('now') WHERE id = ?", (request.form.get("status"), tid))
            flash("Durum güncellendi.", "ok")
        elif action == "priority" and request.form.get("priority") in ("normal", "high", "urgent"):
            ex("UPDATE tickets SET priority = ? WHERE id = ?", (request.form.get("priority"), tid))
            flash("Öncelik güncellendi.", "ok")
        else:
            abort(400)
        return redirect(url_for("admin.ticket", tid=tid))
    msgs = q("SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY id", (tid,))
    order = q1("SELECT id, listing_title, total FROM orders WHERE id = ?", (t["order_id"],)) if t["order_id"] else None
    return render_template("admin_ticket.html", t=t, msgs=msgs, order=order)


# --------------------------------------------------------------------------- sohbet denetimi
@bp.route("/mesajlar")
def chats():
    text = request.args.get("q", "").strip()[:60]
    where, args = ["1=1"], []
    if text:
        where.append("(b.username LIKE ? ESCAPE '\\' OR s.username LIKE ? ESCAPE '\\' OR l.title LIKE ? ESCAPE '\\')")
        args += [like(text)] * 3
    page = core.paginate(
        "SELECT v.*, l.title AS listing_title, b.username AS buyer_name, s.username AS seller_name,"
        " (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = v.id) AS n"
        " FROM conversations v JOIN listings l ON l.id = v.listing_id JOIN users b ON b.id = v.buyer_id"
        " JOIN users s ON s.id = v.seller_id WHERE " + " AND ".join(where) + " ORDER BY v.last_message_at DESC",
        args, 20,
    )
    return render_template("admin_chats.html", page=page, text=text)


@bp.route("/mesajlar/<int:cid>", methods=["GET", "POST"])
def chat(cid):
    conv = q1(
        "SELECT v.*, l.title AS listing_title, b.username AS buyer_name, s.username AS seller_name FROM conversations v"
        " JOIN listings l ON l.id = v.listing_id JOIN users b ON b.id = v.buyer_id JOIN users s ON s.id = v.seller_id WHERE v.id = ?",
        (cid,),
    )
    if not conv:
        abort(404)
    if request.method == "POST":
        locked = 0 if conv["is_locked"] else 1
        ex("UPDATE conversations SET is_locked = ? WHERE id = ?", (locked, cid))
        core.log_admin("Sohbet " + ("kilitlendi" if locked else "kilidi açıldı"), f"#{cid}")
        flash("Sohbet kilitlendi." if locked else "Sohbetin kilidi açıldı.", "ok")
        return redirect(url_for("admin.chat", cid=cid))
    core.log_admin("Sohbet görüntülendi", f"#{cid} {conv['buyer_name']} / {conv['seller_name']}")
    msgs = q("SELECT m.*, u.username FROM messages m JOIN users u ON u.id = m.sender_id WHERE m.conversation_id = ? ORDER BY m.id", (cid,))
    return render_template("admin_chat.html", conv=conv, msgs=msgs)


# --------------------------------------------------------------------------- yorumlar
@bp.route("/yorumlar")
def reviews():
    flt = request.args.get("durum", "")
    where, args = ["1=1"], []
    if flt == "hidden":
        where.append("r.is_hidden = 1")
    elif flt == "low":
        where.append("r.rating <= 2")
    page = core.paginate(
        "SELECT r.*, b.username AS buyer_name, s.username AS seller_name, l.title AS listing_title FROM reviews r"
        " JOIN users b ON b.id = r.buyer_id JOIN users s ON s.id = r.seller_id JOIN listings l ON l.id = r.listing_id"
        " WHERE " + " AND ".join(where) + " ORDER BY r.id DESC",
        args, 20,
    )
    return render_template("admin_reviews.html", page=page, flt=flt)


@bp.post("/yorum/<int:rid>")
def review_action(rid):
    r = q1("SELECT * FROM reviews WHERE id = ?", (rid,))
    if not r:
        abort(404)
    hide = 1 if request.form.get("action") == "hide" else 0
    with core.tx():
        ex("UPDATE reviews SET is_hidden = ? WHERE id = ?", (hide, rid))
        services.recalc_rating(r["listing_id"])
    core.log_admin("Yorum " + ("gizlendi" if hide else "yeniden gösterildi"), f"#{rid}")
    flash("Yorum gizlendi." if hide else "Yorum yeniden yayında.", "ok")
    return redirect(request.referrer or url_for("admin.reviews"))


# --------------------------------------------------------------------------- kategoriler
@bp.route("/kategoriler", methods=["GET", "POST"])
def categories():
    if request.method == "POST":
        action = request.form.get("action")
        name = field("name", 40)
        order = request.form.get("sort_order", 0, type=int) or 0
        new_image = ""
        try:
            if action in ("add", "edit") and not 2 <= len(name) <= 40:
                raise BizError("Kategori adı 2-40 karakter olmalı.")
            color = (request.form.get("color") or "#7c5cff").strip()
            if action in ("add", "edit") and not re.match(r"^#[0-9a-fA-F]{6}$", color):
                raise BizError("Renk #rrggbb biçiminde olmalı.")
            grp, tagline = field("grp", 40), field("tagline", 90)
            daily = 1 if request.form.get("is_daily") else 0
            if action == "add":
                slug, n = slugify(name), 2
                while q1("SELECT 1 FROM categories WHERE slug = ?", (slug,)):
                    slug = f"{slugify(name)}-{n}"
                    n += 1
                rate = services.parse_rate(request.form.get("rate"))
                ex(
                    "INSERT INTO categories(name, slug, sort_order, commission_rate, grp, color, tagline, is_daily) VALUES (?,?,?,?,?,?,?,?)",
                    (name, slug, order, rate, grp, color.lower(), tagline, daily),
                )
                core.log_admin("Kategori eklendi", name)
                flash("Kategori eklendi.", "ok")
            elif action == "edit":
                cid = request.form.get("id", type=int)
                cur = q1("SELECT * FROM categories WHERE id = ?", (cid,))
                if not cur:
                    abort(404)
                active = 1 if request.form.get("is_active") else 0
                rate = services.parse_rate(request.form.get("rate"))
                image = cur["image"]
                file = request.files.get("poster")
                if file and file.filename:
                    new_image = image = services.save_poster(file) or image
                elif request.form.get("remove_poster"):
                    image = ""
                ex(
                    "UPDATE categories SET name = ?, sort_order = ?, is_active = ?, commission_rate = ?, grp = ?, color = ?, tagline = ?,"
                    " is_daily = ?, image = ? WHERE id = ?",
                    (name, order, active, rate, grp, color.lower(), tagline, daily, image, cid),
                )
                if cur["image"] and cur["image"] != image:
                    services.delete_cover(cur["image"])
                core.log_admin("Kategori güncellendi", f"#{cid} {name} komisyon={'genel' if rate is None else rate}")
                flash("Kategori güncellendi.", "ok")
            elif action == "delete":
                cid = request.form.get("id", type=int)
                if q1("SELECT 1 FROM listings WHERE category_id = ?", (cid,)):
                    raise BizError("Bu kategoride ilanlar var; silmek yerine pasife alabilirsin.")
                cur = q1("SELECT image FROM categories WHERE id = ?", (cid,))
                ex("DELETE FROM categories WHERE id = ?", (cid,))
                if cur:
                    services.delete_cover(cur["image"])
                core.log_admin("Kategori silindi", f"#{cid}")
                flash("Kategori silindi.", "ok")
            else:
                abort(400)
        except BizError as err:
            services.delete_cover(new_image)
            flash(str(err), "bad")
        return redirect(url_for("admin.categories"))
    cats = q(
        "SELECT c.*, (SELECT COUNT(*) FROM listings l WHERE l.category_id = c.id AND l.status != 'removed') AS n"
        " FROM categories c ORDER BY c.sort_order, c.id"
    )
    return render_template("admin_categories.html", cats=cats, global_rate=core.setting_pct("commission_percent", "5"))


@bp.post("/kategoriler/toplu-afis")
def category_posters():
    """Dosya adı kategori kısa adıyla eşleşen görselleri toplu yükler (discord.jpg, steam.png, valorant.webp ...)."""
    cats = q("SELECT id, slug, name, image FROM categories")
    done, missed = [], []
    for f in request.files.getlist("posters"):
        if not f or not f.filename:
            continue
        stem = slugify(os.path.splitext(f.filename)[0])
        hit = next((c for c in cats if stem in (c["slug"], slugify(c["name"]))), None)
        if not hit:
            near = [c for c in cats if c["slug"].startswith(stem + "-") or slugify(c["name"]).startswith(stem + "-")]
            hit = near[0] if len(near) == 1 else None
        new_image = ""
        try:
            new_image = services.save_poster(f) if hit else ""
        except BizError:
            new_image = ""
        if not hit or not new_image:
            missed.append(f.filename[:40])
            continue
        ex("UPDATE categories SET image = ? WHERE id = ?", (new_image, hit["id"]))
        services.delete_cover(hit["image"])
        done.append(hit["name"])
    if done:
        core.log_admin("Toplu afiş yüklendi", ", ".join(done)[:200])
        flash(f"{len(done)} kategoriye afiş yüklendi.", "ok")
    if missed:
        flash("Eşleşmeyen veya okunamayan dosyalar: " + ", ".join(missed[:8]), "bad")
    if not done and not missed:
        flash("Dosya seçilmedi.", "bad")
    return redirect(url_for("admin.categories"))


# --------------------------------------------------------------------------- komisyon raporu
@bp.route("/komisyon")
def commission():
    totals = q1(
        "SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS gmv, COALESCE(SUM(commission), 0) AS fee,"
        " COALESCE(SUM(seller_earning), 0) AS payout, COALESCE(SUM(discount), 0) AS discount,"
        " (SELECT COALESCE(SUM(fee), 0) FROM withdrawals WHERE status = 'approved') AS wd_fee,"
        " (SELECT COALESCE(SUM(price), 0) FROM listing_dopings) AS doping FROM orders"
    )
    by_cat = q(
        "SELECT c.id, c.name, c.commission_rate, COUNT(o.id) AS orders, COALESCE(SUM(o.total), 0) AS gmv,"
        " COALESCE(SUM(o.commission), 0) AS fee FROM categories c"
        " LEFT JOIN listings l ON l.category_id = c.id LEFT JOIN orders o ON o.listing_id = l.id"
        " GROUP BY c.id ORDER BY fee DESC, c.sort_order"
    )
    by_seller = q(
        "SELECT u.id, u.username, u.commission_rate, COUNT(o.id) AS orders, SUM(o.total) AS gmv, SUM(o.commission) AS fee"
        " FROM orders o JOIN users u ON u.id = o.seller_id GROUP BY u.id ORDER BY fee DESC LIMIT 10"
    )
    custom = q("SELECT id, username, commission_rate FROM users WHERE commission_rate IS NOT NULL ORDER BY username")
    chart = core.daily_series(
        "SELECT date(created_at,'+3 hours') AS d, SUM(commission) AS v FROM orders"
        " WHERE created_at >= datetime('now','-16 days') GROUP BY d"
    )
    return render_template(
        "admin_commission.html", totals=totals, by_cat=by_cat, by_seller=by_seller, custom=custom, chart=chart,
        global_rate=core.setting_pct("commission_percent", "5"), fee_rate=core.setting_pct("withdraw_fee_percent", "2"),
    )


def _csv_safe(value):
    value = str(value)
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


@bp.route("/komisyon.csv")
def commission_csv():
    rows = q(
        "SELECT o.*, b.username AS buyer_name, s.username AS seller_name, c.name AS cat_name FROM orders o"
        " JOIN users b ON b.id = o.buyer_id JOIN users s ON s.id = o.seller_id"
        " JOIN listings l ON l.id = o.listing_id JOIN categories c ON c.id = l.category_id ORDER BY o.id DESC LIMIT 20000"
    )
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Sipariş No", "Tarih", "Kategori", "İlan", "Satıcı", "Alıcı", "Adet", "Toplam", "Oran %", "Komisyon", "Satıcı Kazancı"])
    for r in rows:
        w.writerow([
            r["id"], core.fmt_dt(r["created_at"]), _csv_safe(r["cat_name"]), _csv_safe(r["listing_title"]), r["seller_name"], r["buyer_name"],
            r["quantity"], core.fmt_plain(r["total"]), str(r["commission_rate"]).replace(".", ","), core.fmt_plain(r["commission"]),
            core.fmt_plain(r["seller_earning"]),
        ])
    name = "komisyon-" + datetime.now().strftime("%Y%m%d") + ".csv"
    return Response(buf.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={name}"})


# --------------------------------------------------------------------------- ödeme yöntemleri
@bp.route("/odeme-yontemleri", methods=["GET", "POST"])
def payments():
    import payments as pay
    if request.method == "POST":
        action = request.form.get("action")
        name = field("name", 60)
        kind = request.form.get("kind") if request.form.get("kind") in pay.KINDS else "other"
        details = field("details", 600)
        instructions = field("instructions", 600)
        min_amount = core.to_kurus(request.form.get("min_amount")) or 0
        max_raw = (request.form.get("max_amount") or "").strip()
        max_amount = core.to_kurus(max_raw) if max_raw else 0
        order = request.form.get("sort_order", 0, type=int) or 0
        active = 1 if request.form.get("is_active") else 0
        eta = field("eta", 40)
        badge = field("badge", 24)
        color = pay.clean_color(request.form.get("color"))
        icon = pay.clean_icon(request.form.get("icon"), kind)
        try:
            bonus_raw = (request.form.get("bonus_percent") or "0").strip().replace(",", ".") or "0"
            try:
                bonus = round(float(bonus_raw), 2)
            except ValueError:
                raise BizError("Bonus oranı sayı olmalı.")
            if action in ("add", "edit"):
                if not 2 <= len(name) <= 60 or not details:
                    raise BizError("Yöntem adı ve ödeme bilgileri (IBAN, adres vb.) zorunlu.")
                if not 0 <= bonus <= pay.MAX_BONUS:
                    raise BizError(f"Bonus oranı 0 ile {pay.MAX_BONUS} arasında olmalı.")
                if max_amount is None or max_amount < 0 or (max_amount and max_amount < min_amount):
                    raise BizError("Maksimum tutar, minimum tutardan küçük olamaz (sınırsız için boş bırak).")
            if action == "add":
                ex(
                    "INSERT INTO payment_methods(name, kind, details, instructions, min_amount, max_amount, bonus_percent, eta, icon, color, badge, is_active, sort_order)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (name, kind, details, instructions, min_amount, max_amount, bonus, eta, icon, color, badge, active, order),
                )
                core.log_admin("Ödeme yöntemi eklendi", name)
                flash("Ödeme yöntemi eklendi.", "ok")
            elif action == "add_template":
                tpl = pay.BY_KEY.get(request.form.get("template", ""))
                if not tpl:
                    raise BizError("Geçerli bir şablon seç.")
                key, tname, tkind, tdetails, tinst, tmin, teta, ticon, tcolor, tbadge = tpl
                if q1("SELECT 1 FROM payment_methods WHERE name = ?", (tname,)):
                    raise BizError("Bu yöntem zaten listede var.")
                nxt = (q1("SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM payment_methods")["n"])
                ex(
                    "INSERT INTO payment_methods(name, kind, details, instructions, min_amount, eta, icon, color, badge, is_active, sort_order)"
                    " VALUES (?,?,?,?,?,?,?,?,?,0,?)",
                    (tname, tkind, tdetails, tinst, tmin * 100, teta, ticon, tcolor, tbadge, nxt),
                )
                core.log_admin("Ödeme yöntemi şablondan eklendi", tname)
                flash(f"{tname} eklendi. Bilgilerini kendi hesabına göre düzenleyip aktifleştir.", "ok")
            elif action == "edit":
                mid = request.form.get("id", type=int)
                ex(
                    "UPDATE payment_methods SET name=?, kind=?, details=?, instructions=?, min_amount=?, max_amount=?, bonus_percent=?, eta=?, icon=?, color=?, badge=?,"
                    " is_active=?, sort_order=? WHERE id=?",
                    (name, kind, details, instructions, min_amount, max_amount, bonus, eta, icon, color, badge, active, order, mid),
                )
                core.log_admin("Ödeme yöntemi güncellendi", f"#{mid} {name} aktif={active}")
                flash("Ödeme yöntemi güncellendi.", "ok")
            elif action == "toggle":
                mid = request.form.get("id", type=int)
                row = q1("SELECT is_active, name FROM payment_methods WHERE id = ?", (mid,))
                if not row:
                    abort(404)
                ex("UPDATE payment_methods SET is_active = ? WHERE id = ?", (0 if row["is_active"] else 1, mid))
                core.log_admin("Ödeme yöntemi " + ("pasife alındı" if row["is_active"] else "aktifleştirildi"), f"#{mid} {row['name']}")
                flash("Yöntem pasife alındı." if row["is_active"] else "Yöntem aktifleştirildi.", "ok")
            elif action == "delete":
                mid = request.form.get("id", type=int)
                try:
                    ex("DELETE FROM payment_methods WHERE id = ?", (mid,))
                    flash("Ödeme yöntemi silindi.", "ok")
                except sqlite3.IntegrityError:
                    ex("UPDATE payment_methods SET is_active = 0 WHERE id = ?", (mid,))
                    flash("Bu yöntemle yapılmış yüklemeler olduğu için silinmedi, pasife alındı.", "info")
                core.log_admin("Ödeme yöntemi silindi/pasife alındı", f"#{mid}")
            else:
                abort(400)
        except BizError as err:
            flash(str(err), "bad")
        pay.reset_cache()
        return redirect(url_for("admin.payments"))
    stats = pay.method_stats()
    totals = q1(
        "SELECT COALESCE(SUM(CASE WHEN status = 'approved' THEN amount END), 0) AS ok_sum, SUM(status = 'approved') AS ok_n,"
        " SUM(status = 'pending') AS pend_n, COALESCE(SUM(CASE WHEN status = 'pending' THEN amount END), 0) AS pend_sum FROM deposits"
    )
    return render_template(
        "admin_payments.html", methods=q("SELECT * FROM payment_methods ORDER BY sort_order, id"), stats=stats, totals=totals,
        templates=pay.TEMPLATES, kinds=pay.KINDS, icons=pay.ICONS,
    )


# --------------------------------------------------------------------------- entegrasyon (API / webhook)
@bp.route("/entegrasyon")
def integration():
    stats = q1(
        "SELECT (SELECT COUNT(*) FROM api_keys WHERE is_active = 1) AS keys,"
        " (SELECT COUNT(*) FROM deposits WHERE auto = 1) AS auto_deposits,"
        " (SELECT MAX(last_used_at) FROM api_keys) AS last_api_use"
    )
    keys = q(
        "SELECT k.*, u.username FROM api_keys k JOIN users u ON u.id = k.user_id ORDER BY k.id DESC LIMIT 50"
    )
    secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
    return render_template(
        "admin_integration.html", stats=stats, keys=keys, secret_set=bool(secret), secret_hint=(secret[:4] + "..." + secret[-4:]) if len(secret) > 12 else "",
        base=request.host_url.rstrip("/"),
    )


@bp.post("/entegrasyon/anahtar/<int:kid>")
def api_key_revoke(kid):
    ex("UPDATE api_keys SET is_active = 0 WHERE id = ?", (kid,))
    core.log_admin("API anahtarı iptal edildi", f"#{kid}")
    flash("API anahtarı iptal edildi.", "ok")
    return redirect(url_for("admin.integration"))


# --------------------------------------------------------------------------- ayarlar
@bp.route("/ayarlar", methods=["GET", "POST"])
def site_settings():
    if request.method == "POST":
        try:
            values = {
                "site_name": field("site_name", 30),
                "site_tagline": field("site_tagline", 120),
                "support_email": field("support_email", 120),
                "announcement": field("announcement", 300),
            }
            if not values["site_name"]:
                raise BizError("Site adı boş olamaz.")
            for key, label in (("commission_percent", "Genel komisyon"), ("withdraw_fee_percent", "Çekim kesintisi")):
                raw = field(key, 8).replace(",", ".")
                try:
                    val = float(raw)
                except ValueError:
                    raise BizError(f"{label} oranı sayı olmalı.")
                if not 0 <= val <= 50:
                    raise BizError(f"{label} oranı 0 ile 50 arasında olmalı.")
                values[key] = raw
            for key, label in (("min_withdraw", "Minimum çekim"), ("min_deposit", "Minimum yükleme")):
                k = core.to_kurus(request.form.get(key))
                if k is None or k < 100:
                    raise BizError(f"{label} tutarı en az 1 ₺ olmalı.")
                values[key] = core.fmt_plain(k).replace(",00", "")
            qty = request.form.get("max_qty_per_order", type=int)
            if not qty or not 1 <= qty <= 100:
                raise BizError("Sipariş başına maksimum adet 1-100 arasında olmalı.")
            values["max_qty_per_order"] = str(qty)
            for key, label in (("fee_store_name", "Mağaza adı değişikliği ücreti"), ("fee_store_slug", "Mağaza adresi değişikliği ücreti")):
                k = core.to_kurus(request.form.get(key, "0") or "0")
                if k is None or k < 0 or k > 10_000_000:
                    raise BizError(f"{label} 0 ile 100.000 ₺ arasında olmalı.")
                values[key] = core.fmt_plain(k).replace(",00", "")
            tms = request.form.get("trusted_min_sales", type=int)
            if tms is None or not 1 <= tms <= 100000:
                raise BizError("Güvenilir satıcı için asgari satış adedi 1 veya daha fazla olmalı.")
            values["trusted_min_sales"] = str(tms)
            try:
                tmr = float(field("trusted_min_rating", 5).replace(",", "."))
            except ValueError:
                raise BizError("Güvenilir satıcı asgari puanı sayı olmalı.")
            if not 1 <= tmr <= 5:
                raise BizError("Güvenilir satıcı asgari puanı 1 ile 5 arasında olmalı.")
            values["trusted_min_rating"] = str(tmr)
            for flag in ("require_seller_approval", "withdraw_only_earnings", "require_cover", "maintenance_mode", "allow_registration", "home_ticker", "require_seller_2fa"):
                values[flag] = "1" if request.form.get(flag) else "0"
            values["meta_description"] = field("meta_description", 200)
            values["support_hours"] = field("support_hours", 60)
            for key in ("social_discord", "social_telegram", "social_instagram"):
                url = field(key, 200)
                if url and not url.startswith(("http://", "https://")):
                    raise BizError("Sosyal medya bağlantıları http:// veya https:// ile başlamalı.")
                values[key] = url
            days = request.form.get("escrow_days", core.setting_int("escrow_days", 3), type=int)
            if days is None or not 0 <= days <= 30:
                raise BizError("Emanet süresi 0-30 gün arasında olmalı.")
            values["escrow_days"] = str(days)
            secs = request.form.get("hero_seconds", type=int)
            if not secs or not 3 <= secs <= 20:
                raise BizError("Slider geçiş süresi 3-20 saniye olmalı.")
            values["hero_seconds"] = str(secs)
        except BizError as err:
            flash(str(err), "bad")
        else:
            with core.tx():
                for key, val in values.items():
                    ex("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, val))
            core.log_admin("Ayarlar güncellendi")
            flash("Ayarlar kaydedildi.", "ok")
            return redirect(url_for("admin.site_settings"))
    return render_template("admin_settings.html")


# --------------------------------------------------------------------------- defter / günlük
@bp.route("/islemler")
def transactions():
    text = request.args.get("q", "").strip()[:40]
    kind = request.args.get("tur", "")
    where, args = ["1=1"], []
    if text:
        where.append("u.username LIKE ? ESCAPE '\\'")
        args.append(like(text))
    if kind:
        where.append("t.kind = ?")
        args.append(kind)
    page = core.paginate(
        "SELECT t.*, u.username FROM transactions t JOIN users u ON u.id = t.user_id WHERE "
        + " AND ".join(where) + " ORDER BY t.id DESC",
        args, 25,
    )
    return render_template("admin_transactions.html", page=page, text=text, kind=kind)


@bp.route("/gunluk")
def log():
    page = core.paginate("SELECT * FROM admin_log ORDER BY id DESC", (), 30)
    return render_template("admin_log.html", page=page)


import admin_trust  # noqa: E402,F401
import paylink  # noqa: E402,F401  (ödeme linki yönetim rotaları)
import admin_more  # noqa: E402,F401  (ek yönetim modülleri aynı blueprint'e rota ekler)
import admin_auth  # noqa: E402,F401  (giriş / 2FA / güvenlik rotaları)

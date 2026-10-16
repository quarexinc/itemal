"""Mağaza paketleri: mavi tik, altın/elmas mağaza, öne çıkan mağaza, düşük komisyon, hızlı teslimat rozeti.

Satıcı:  /satici/paketler (seller.packages), POST /satici/paketler/<pid>/al (seller.package_buy).
Yönetim: /admin/paketler (admin.packages, admin.package_edit, admin.package_grant, admin.package_revoke).
Şablon globalleri: pkg_marks(kullanıcı_id | satır), pkg_tier(kullanıcı_id), my_packages().

Süre mantığı: her satın alma user_packages'e bir satır ekler. Aynı paket tekrar alınırsa yeni satır, mevcut bitişten
başlar (süre uzar). Etkin olma koşulu starts_at <= şimdi < ends_at (ends_at NULL = kalıcı); zamanlanmış iş gerekmez.
Tüm zamanlar UTC metni ('YYYY-MM-DD HH:MM:SS'); karşılaştırmalar SQLite datetime('now') ile yapılır.
"""
import re
import sqlite3

from flask import abort, flash, g, redirect, render_template, request, url_for
from markupsafe import Markup, escape

import core
import services
from admin import bp as admin_bp
from core import BizError, ex, field, q, q1
from seller import bp as seller_bp

ACTIVE_COND = "up.starts_at <= datetime('now') AND (up.ends_at IS NULL OR up.ends_at > datetime('now'))"
MAX_PRICE_TL = 100000
TIER_RANK = {"": 0, "gold": 1, "diamond": 2}
TIER_LABEL = {"gold": "Altın mağaza", "diamond": "Elmas mağaza"}
_NO_MARKS = {"tick": 0, "tier": "", "rank": 0, "fast": 0, "featured": 0, "disc": 0.0, "gslots": 0, "theme": 0, "support": 0}
_ICON_FILES = {"vtick": "mavitik.svg", "vgold": "tier-gold.svg", "vdiamond": "tier-diamond.svg"}


# --------------------------------------------------------------------------- etkin paket önbelleği (istek başına)
def marks_map(reload=False):
    """Etkin paketlerden türetilen kullanıcı özellikleri: {kullanıcı_id: {tick, tier, rank, fast, featured, disc, gslots, theme, support}}.
    Tek sorgu; süre bitimi sorguda hesaplanır. Aynı istek içinde önbelleğe alınır (reset() ile sıfırlanır)."""
    cached = g.get("pkg_map")
    if cached is not None and not reload:
        return cached
    out = {}
    rows = q(
        "SELECT d.user_id, sp.tick, sp.tier, sp.featured, sp.fast_badge, sp.commission_discount,"
        " sp.giveaway_slots, sp.theme_unlock, sp.priority_support"
        " FROM (SELECT DISTINCT up.user_id, up.package_id FROM user_packages up WHERE " + ACTIVE_COND + ") AS d"
        " JOIN store_packages sp ON sp.id = d.package_id"
    )
    for r in rows:
        m = out.setdefault(int(r["user_id"]), dict(_NO_MARKS))
        if r["tick"]:
            m["tick"] = 1
        rank = TIER_RANK.get(r["tier"] or "", 0)
        if rank > m["rank"]:
            m["rank"] = rank
            m["tier"] = r["tier"]
        if r["fast_badge"]:
            m["fast"] = 1
        if r["featured"]:
            m["featured"] = 1
        m["disc"] += float(r["commission_discount"] or 0)
        m["gslots"] += int(r["giveaway_slots"] or 0)
        if r["theme_unlock"]:
            m["theme"] = 1
        if r["priority_support"]:
            m["support"] = 1
    g.pkg_map = out
    return out


def marks(uid):
    try:
        uid = int(uid)
    except (TypeError, ValueError):
        return dict(_NO_MARKS)
    return marks_map().get(uid, _NO_MARKS)


def reset():
    g.pop("pkg_map", None)


def commission_discount(uid):
    """Etkin paketlerin toplam komisyon indirimi (puan)."""
    return round(float(marks(uid)["disc"]), 4)


def badge_keys(uid):
    """services.user_badges() için: etkin paketlerden gelen rozet anahtarları."""
    m = marks(uid)
    keys = []
    if m["tier"] == "diamond":
        keys.append("tier_diamond")
    elif m["tier"] == "gold":
        keys.append("tier_gold")
    if m["fast"]:
        keys.append("fast_delivery")
    return keys


def sql_cols(uid_expr):
    """Mağaza listesi gibi sorgulara eklenecek hesaplı sütunlar (pk_featured, pk_rank). uid_expr: örn. 'u.id'."""
    frm = (
        " FROM user_packages up JOIN store_packages sp ON sp.id = up.package_id WHERE up.user_id = "
        + uid_expr + " AND " + ACTIVE_COND
    )
    return (
        "(SELECT COALESCE(MAX(sp.featured), 0)" + frm + ") AS pk_featured,"
        " (SELECT COALESCE(MAX(CASE sp.tier WHEN 'diamond' THEN 2 WHEN 'gold' THEN 1 ELSE 0 END), 0)" + frm + ") AS pk_rank"
    )


def _keys(x):
    try:
        return list(x.keys())
    except Exception:
        return None


def marks_html(x):
    """Şablon: {{ pkg_marks(kullanıcı_id) }} ya da {{ pkg_marks(satır) }}. İsmin yanına mavi tik ve (varsa)
    altın/elmas rozetini basar; paket yoksa boş döner."""
    keys = _keys(x)
    if keys is not None and "seller_tick" in keys:
        tick = int(x["seller_tick"] or 0)
        tier = (x["seller_tier"] if "seller_tier" in keys else "") or ""
    else:
        if keys is not None:
            uid = (x["seller_id"] if "seller_id" in keys else None) or (x["id"] if "id" in keys else None) or 0
        else:
            uid = x
        try:
            uid = int(uid)
        except Exception:
            return Markup("")
        if uid <= 0:
            return Markup("")
        m = marks(uid)
        tick, tier = int(m["tick"]), m["tier"]
    html = ""
    if tick:
        html += (
            '<img class="vtick" src="%s" width="16" height="16" alt="Mavi tik" title="Mavi tik: doğrulanmış mağaza">'
            % escape(url_for("static", filename="mavitik.svg"))
        )
    if tier in ("gold", "diamond"):
        html += '<img class="vtier vtier-%s" src="%s" width="16" height="16" alt="%s" title="%s">' % (
            tier, escape(url_for("static", filename="tier-%s.svg" % tier)), escape(TIER_LABEL[tier]), escape(TIER_LABEL[tier]),
        )
    return Markup(html)


def tier_of(uid):
    return marks(uid)["tier"]


def theme_unlocked(uid):
    """Tüm vitrin temaları: Premium Vitrin / Elmas paketi ya da altın-elmas kademesi etkinse True."""
    m = marks(uid)
    return bool(m["theme"] or m["rank"] >= 1)


def priority_support(uid):
    return bool(marks(uid)["support"])


def my_packages():
    return user_active(int(g.user["id"])) if g.get("user") else []


def install(app):
    """Şablon globallerini kaydeder (app.py, blueprint kaydından önce çağırır)."""
    app.jinja_env.globals.update(pkg_marks=marks_html, pkg_tier=tier_of, my_packages=my_packages)


# --------------------------------------------------------------------------- biçim yardımcıları
def num(v):
    """1.5 -> '1,5'; 2.0 -> '2'."""
    s = ("%.2f" % float(v)).rstrip("0").rstrip(".")
    return (s or "0").replace(".", ",")


def duration_label(p):
    return f"{int(p['duration_days'])} gün" if int(p["duration_days"]) > 0 else "Kalıcı"


def features(p):
    """Paket kartı için özellik listesi (bayraklardan üretilir)."""
    f = []
    if p["tick"]:
        f.append("Mağaza adının yanında mavi tik (her yerde görünür)")
    if p["tier"] == "gold":
        f += ["Altın mağaza rozeti", "Mağaza sayfanda altın çerçeve ve vurgu", "Mağazalar listesinde öncelikli sıralama"]
    elif p["tier"] == "diamond":
        f += ["Elmas mağaza rozeti", "Mağaza sayfanda elmas çerçeve ve vurgu", "Mağazalar listesinde öncelikli sıralama"]
    if p["featured"]:
        f.append('Mağazalar sayfasında "Öne çıkan" etiketiyle en üstte')
    if float(p["commission_discount"] or 0) > 0:
        f.append("Komisyon oranında " + num(p["commission_discount"]) + " puan indirim")
    if p["fast_badge"]:
        f.append('"Hızlı teslimat" rozeti')
    if int(p["giveaway_slots"] or 0) > 0:
        f.append(f"Aynı anda {int(p['giveaway_slots'])} ek çekiliş hakkı (standart 3)")
    if p["theme_unlock"]:
        f.append("Tüm vitrin temaları ve renk seçenekleri")
    if p["priority_support"]:
        f.append("Destek talepleri yüksek öncelikle açılır")
    f.append(
        f"{int(p['duration_days'])} gün geçerli; tekrar alırsan süre uzar" if int(p["duration_days"]) > 0
        else "Tek seferlik ödeme, süresiz geçerli"
    )
    return f


def icon_html(p):
    """Paket kartı simgesi (HTML). icon: v* özel rozet SVG'leri ya da sprite simgesi."""
    icon = str(p["icon"] or "")
    if icon in _ICON_FILES:
        return Markup('<img src="%s" alt="" width="40" height="40">' % escape(url_for("static", filename=_ICON_FILES[icon])))
    name = icon if re.fullmatch(r"[a-z0-9-]{1,30}", icon) else "zap"
    return Markup('<svg class="i" aria-hidden="true"><use href="#i-%s"/></svg>' % escape(name))


def color_of(p):
    return p["color"] if re.fullmatch(r"#[0-9a-fA-F]{3,8}", str(p["color"] or "")) else "#7c5cff"


def _state(row, now):
    if row["ends_at"] is not None and row["ends_at"] <= row["starts_at"]:
        return "cancelled"
    if row["ends_at"] is not None and row["ends_at"] <= now:
        return "ended"
    if row["starts_at"] > now:
        return "queued"
    return "active"


def _form_int(name, default=0):
    s = (request.form.get(name) or "").strip()
    return int(s) if re.fullmatch(r"[0-9]{1,12}", s) else default


# --------------------------------------------------------------------------- sorgular
def all_packages(only_active=False):
    return q("SELECT * FROM store_packages" + (" WHERE is_active = 1" if only_active else "") + " ORDER BY sort_order, id")


def user_active(uid):
    """Kullanıcının etkin paketleri (pakete göre toplanmış): [{package_id, name, icon, color, permanent, until}]."""
    rows = q(
        "SELECT up.package_id, up.starts_at, up.ends_at, sp.name, sp.icon, sp.color"
        " FROM user_packages up JOIN store_packages sp ON sp.id = up.package_id"
        " WHERE up.user_id = ? AND (up.ends_at IS NULL OR (up.ends_at > datetime('now') AND up.ends_at > up.starts_at)) ORDER BY up.id",
        (uid,),
    )
    now = core.utc_str()
    out = {}
    for r in rows:
        o = out.setdefault(int(r["package_id"]), {
            "package_id": int(r["package_id"]), "name": r["name"], "icon": r["icon"], "color": r["color"],
            "permanent": False, "until": None, "active": False,
        })
        if r["ends_at"] is None:
            o["permanent"] = True
        elif o["until"] is None or r["ends_at"] > o["until"]:
            o["until"] = r["ends_at"]
        if r["starts_at"] <= now:
            o["active"] = True
    return [o for o in out.values() if o["active"]]


def apply(uid, p, days, price, source):
    """Paketi kullanıcıya uygular (core.tx() içinde çağır). Kalıcı paket zaten varsa BizError.
    (starts_at, ends_at|None, user_package_id, extended) döndürür."""
    pid = int(p["id"])
    now = q1("SELECT datetime('now') AS n")["n"]
    if q1("SELECT 1 AS x FROM user_packages WHERE user_id = ? AND package_id = ? AND ends_at IS NULL", (uid, pid)):
        raise BizError("Bu pakete zaten kalıcı olarak sahipsin.")
    starts, ends, extended = now, None, False
    if days > 0:
        last = q1(
            "SELECT MAX(ends_at) AS m FROM user_packages WHERE user_id = ? AND package_id = ? AND ends_at > datetime('now')"
            " AND ends_at > starts_at",                  # iptal edilmiş (başlangıç = bitiş) satırlar süreyi uzatmaz
            (uid, pid),
        )
        if last and last["m"]:
            starts = last["m"]
            extended = True
        ends = q1("SELECT datetime(?, ?) AS e", (starts, f"+{int(days)} days"))["e"]
    cur = ex(
        "INSERT INTO user_packages(user_id, package_id, price, source, starts_at, ends_at) VALUES (?,?,?,?,?,?)",
        (uid, pid, price, source, starts, ends),
    )
    return starts, ends, cur.lastrowid, extended


# --------------------------------------------------------------------------- satıcı: paketler
@seller_bp.route("/paketler", endpoint="packages")
def seller_packages():
    me = g.user
    uid = int(me["id"])
    owned = {o["package_id"]: o for o in user_active(uid)}
    # sırada bekleyen (henüz başlamamış) satırlar da bitişi uzatır: bitiş en geç satırdan alınır
    future = q(
        "SELECT package_id, MAX(ends_at) AS m, SUM(ends_at IS NULL) AS perm FROM user_packages"
        " WHERE user_id = ? AND (ends_at IS NULL OR (ends_at > datetime('now') AND ends_at > starts_at)) GROUP BY package_id",
        (uid,),
    )
    for f in future:
        o = owned.get(int(f["package_id"]))
        if o:
            if f["perm"]:
                o["permanent"] = True
            elif f["m"]:
                o["until"] = f["m"]
    bal = int(me["balance"])
    cards = []
    for p in all_packages(True):
        o = owned.get(int(p["id"]))
        price = int(p["price"])
        cards.append({
            "p": p, "icon": icon_html(p), "color": color_of(p), "features": features(p), "duration": duration_label(p),
            "owned": o, "locked": bool(o and o["permanent"]), "can_afford": bal >= price, "missing": max(price - bal, 0),
        })
    now = core.utc_str()
    history = []
    for h in q(
        "SELECT up.*, sp.name, sp.icon, sp.color FROM user_packages up JOIN store_packages sp ON sp.id = up.package_id"
        " WHERE up.user_id = ? ORDER BY up.id DESC LIMIT 10",
        (uid,),
    ):
        d = dict(h)
        d["state"] = _state(d, now)
        history.append(d)
    return render_template("seller_packages.html", cards=cards, active_list=list(owned.values()), history=history, balance=bal)


@seller_bp.post("/paketler/<int:pid>/al", endpoint="package_buy")
def seller_package_buy(pid):
    me = g.user
    uid = int(me["id"])
    back = url_for("seller.packages")
    if not core.can_sell(me):
        abort(403)
    if core.rate_hit("pkgbuy", 20, 600, f"u{uid}"):
        flash("Kısa sürede çok fazla deneme yaptın. Biraz bekle.", "bad")
        return redirect(back)
    res = {}
    try:
        with core.tx():                                  # BEGIN IMMEDIATE: aynı kullanıcının eşzamanlı istekleri sıralanır
            u = q1("SELECT id, balance, is_banned FROM users WHERE id = ?", (uid,))
            if not u or u["is_banned"]:
                raise BizError("Bu işlem yapılamıyor.")
            p = q1("SELECT * FROM store_packages WHERE id = ?", (pid,))
            if not p or not p["is_active"]:
                raise BizError("Bu paket şu anda satışta değil.")
            if q1("SELECT 1 AS x FROM user_packages WHERE user_id = ? AND package_id = ? AND ends_at IS NULL", (uid, pid)):
                raise BizError("Bu pakete zaten kalıcı olarak sahipsin.")
            if q1(
                "SELECT 1 AS x FROM user_packages WHERE user_id = ? AND package_id = ? AND source = 'buy'"
                " AND created_at > datetime('now', '-8 seconds')",
                (uid, pid),
            ):
                raise BizError("Bu paketi az önce satın aldın; çift ücret alınmaması için işlem tekrarlanmadı.")
            price = int(p["price"])
            if int(u["balance"]) < price:
                raise BizError(f"Yetersiz bakiye. Gerekli tutar {core.fmt_money(price)}, bakiyen {core.fmt_money(u['balance'])}.")
            _starts, ends, upid, extended = apply(uid, p, int(p["duration_days"]), price, "buy")
            core.change_balance(uid, -price, "package", "Mağaza paketi: " + p["name"], "package", upid)
            until = "süresiz" if ends is None else core.fmt_dt(ends, False) + " tarihine kadar"
            services.notify(
                uid, "Paket etkinleştirildi",
                f"{p['name']} paketi {'uzatıldı' if extended else 'etkinleştirildi'} ({until}). {core.fmt_money(price)} bakiyenden düşüldü.",
                url_for("seller.packages"),
            )
            res = {"p": p, "ends": ends, "extended": extended}
    except BizError as err:
        flash(str(err), "bad")
        return redirect(back)
    except sqlite3.IntegrityError:
        flash("Yetersiz bakiye.", "bad")
        return redirect(back)
    reset()
    p = res["p"]
    msg = p["name"] + (" paketinin süresi uzatıldı" if res["extended"] else " paketi etkinleştirildi")
    if res["ends"] is not None:
        msg += "; yeni bitiş: " + core.fmt_dt(res["ends"], False)
    msg += "."
    if p["tick"]:
        msg += " Mavi tik artık mağaza adının yanında görünüyor."
    flash(msg, "ok")
    return redirect(back)


# --------------------------------------------------------------------------- yönetim: paketler
@admin_bp.route("/paketler", endpoint="packages")
def admin_packages():
    try:
        filt = int(request.args.get("paket", "0") or 0)
    except ValueError:
        filt = 0
    where, args = "", []
    if filt > 0:
        where = " WHERE up.package_id = ?"
        args.append(filt)
    page = core.paginate(
        "SELECT up.*, u.username, COALESCE(NULLIF(u.store_name, ''), u.username) AS store, sp.name AS package_name,"
        " sp.color AS package_color FROM user_packages up JOIN users u ON u.id = up.user_id"
        " JOIN store_packages sp ON sp.id = up.package_id" + where + " ORDER BY up.id DESC",
        args, 15,
    )
    now = core.utc_str()
    rows = []
    for r in page["rows"]:
        d = dict(r)
        d["state"] = _state(d, now)
        rows.append(d)
    page["rows"] = rows
    stats = {
        int(s["id"]): s for s in q(
            "SELECT sp.id, COUNT(up.id) AS sales, COALESCE(SUM(up.price), 0) AS revenue,"
            " COUNT(DISTINCT CASE WHEN " + ACTIVE_COND + " THEN up.user_id END) AS active_users"
            " FROM store_packages sp LEFT JOIN user_packages up ON up.package_id = sp.id GROUP BY sp.id"
        )
    }
    pkgs = []
    total_sales = total_active = 0
    for p in all_packages():
        s = stats.get(int(p["id"]))
        sales, revenue, active_users = (int(s["sales"]), int(s["revenue"]), int(s["active_users"])) if s else (0, 0, 0)
        pkgs.append({
            "p": p, "sales": sales, "revenue": revenue, "active_users": active_users,
            "price_plain": core.fmt_plain(p["price"]), "disc_plain": num(p["commission_discount"]),
            "icon": icon_html(p), "color": color_of(p), "features": features(p),
        })
        total_sales += sales
        total_active += active_users
    paid = q1("SELECT COUNT(*) AS n, COALESCE(SUM(price), 0) AS s FROM user_packages WHERE source = 'buy'")
    holders = q1("SELECT COUNT(DISTINCT up.user_id) AS n FROM user_packages up WHERE " + ACTIVE_COND)["n"]
    totals = {"sales": paid["n"], "revenue": paid["s"], "active": total_active, "holders": holders, "granted": total_sales - paid["n"]}
    return render_template("admin_packages.html", pkgs=pkgs, page=page, filter=filt, now=now, totals=totals)


@admin_bp.post("/paketler/<int:pid>", endpoint="package_edit")
def admin_package_edit(pid):
    p = q1("SELECT * FROM store_packages WHERE id = ?", (pid,))
    if not p:
        abort(404)
    errors = []
    name = field("name", 80)
    if len(name) < 2:
        errors.append("Paket adı en az 2 karakter olmalı.")
    price = core.to_kurus(request.form.get("price", ""))
    if price is None or price > MAX_PRICE_TL * 100:
        errors.append(f"Fiyat geçerli bir tutar olmalı (en fazla {MAX_PRICE_TL:,} TL).".replace(",", "."))
    days_raw = (request.form.get("duration_days") or "").strip()
    days = int(days_raw) if re.fullmatch(r"[0-9]{1,4}", days_raw) else -1
    if days < 0 or days > 3650:
        errors.append("Süre 0 (kalıcı) ile 3650 gün arasında olmalı.")
    disc_raw = (request.form.get("commission_discount") or "").strip().replace(",", ".")
    if disc_raw == "":
        disc = float(p["commission_discount"] or 0)
    else:
        disc = float(disc_raw) if re.fullmatch(r"[0-9]*\.?[0-9]+", disc_raw) else -1.0
    if float(p["commission_discount"] or 0) > 0 or disc_raw != "":
        if disc < 0 or disc > 50:
            errors.append("Komisyon indirimi 0 ile 50 puan arasında olmalı.")
    sort_raw = (request.form.get("sort_order") or "").strip()
    sort = int(sort_raw) if re.fullmatch(r"-?[0-9]{1,6}", sort_raw) else int(p["sort_order"])
    gs_raw = (request.form.get("giveaway_slots") or "").strip()
    gslots = int(p["giveaway_slots"] or 0)
    if int(p["giveaway_slots"] or 0) > 0 or gs_raw != "":
        gslots = int(gs_raw) if re.fullmatch(r"[0-9]{1,2}", gs_raw) else -1
        if not 0 <= gslots <= 50:
            errors.append("Ek çekiliş hakkı 0 ile 50 arasında olmalı.")
            gslots = int(p["giveaway_slots"] or 0)
    if errors:
        flash(" ".join(errors), "bad")
        return redirect(url_for("admin.packages") + f"#paket-{pid}")
    active = 1 if "is_active" in request.form else 0
    ex(
        "UPDATE store_packages SET name = ?, tagline = ?, description = ?, price = ?, duration_days = ?, is_active = ?,"
        " sort_order = ?, commission_discount = ?, giveaway_slots = ? WHERE id = ?",
        (name, field("tagline", 160), field("description", 1000), price, days, active, sort, round(disc, 2), gslots, pid),
    )
    core.log_admin("Paket düzenlendi", f"#{pid} {p['code']} fiyat {core.fmt_money(price)}, süre {days} gün, {'aktif' if active else 'pasif'}")
    flash(f"{name} paketi güncellendi.", "ok")
    return redirect(url_for("admin.packages") + f"#paket-{pid}")


@admin_bp.post("/paketler/ver", endpoint="package_grant")
def admin_package_grant():
    username = field("username", 40)
    pid = _form_int("package_id")
    days_raw = (request.form.get("days") or "").strip()
    back = url_for("admin.packages") + "#ver"
    u = q1("SELECT * FROM users WHERE username = ?", (username,)) if username else None
    p = q1("SELECT * FROM store_packages WHERE id = ?", (pid,)) if pid else None
    if not u:
        flash("Kullanıcı bulunamadı.", "bad")
        return redirect(back)
    if not p:
        flash("Geçerli bir paket seç.", "bad")
        return redirect(back)
    if not core.can_sell(u):
        flash("Paketler yalnızca satıcı hesaplarına verilebilir.", "bad")
        return redirect(back)
    days = int(p["duration_days"])
    if days_raw != "":
        if not re.fullmatch(r"[0-9]{1,4}", days_raw) or not 1 <= int(days_raw) <= 3650:
            flash("Gün sayısı 1 ile 3650 arasında olmalı (boş bırakırsan paketin süresi uygulanır).", "bad")
            return redirect(back)
        if days > 0:
            days = int(days_raw)
    try:
        with core.tx():
            _starts, ends, _upid, _ext = apply(int(u["id"]), p, days, 0, "admin")
            services.notify(
                u["id"], "Paket hediye edildi",
                f"{p['name']} paketi hesabına tanımlandı ({'süresiz' if ends is None else core.fmt_dt(ends, False) + ' tarihine kadar'}).",
                url_for("seller.packages"),
            )
    except BizError as err:
        flash(str(err), "bad")
        return redirect(back)
    reset()
    core.log_admin("Paket verildi", f"{u['username']} <- {p['name']} ({'kalıcı' if ends is None else str(days) + ' gün'})")
    flash(f"{p['name']} paketi {u['username']} kullanıcısına verildi.", "ok")
    return redirect(url_for("admin.packages"))


@admin_bp.post("/paketler/kaldir", endpoint="package_revoke")
def admin_package_revoke():
    uid = _form_int("user_id")
    pid = _form_int("package_id")
    u = q1("SELECT id, username FROM users WHERE id = ?", (uid,)) if uid else None
    p = q1("SELECT id, name FROM store_packages WHERE id = ?", (pid,)) if pid else None
    if not u or not p:
        abort(404)
    with core.tx():
        # etkin satırlar şimdi biter; sıradaki (henüz başlamamış) satırlar iptal edilir (başlangıç = bitiş)
        ex("UPDATE user_packages SET ends_at = starts_at WHERE user_id = ? AND package_id = ? AND starts_at > datetime('now')", (uid, pid))
        ex(
            "UPDATE user_packages SET ends_at = datetime('now') WHERE user_id = ? AND package_id = ?"
            " AND starts_at <= datetime('now') AND (ends_at IS NULL OR ends_at > datetime('now'))",
            (uid, pid),
        )
    reset()
    core.log_admin("Paket kaldırıldı", f"{u['username']} - {p['name']}")
    flash(f"{p['name']} paketi {u['username']} kullanıcısından kaldırıldı.", "ok")
    return redirect(url_for("admin.packages"))

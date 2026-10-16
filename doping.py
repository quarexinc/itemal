"""Doping (ilan öne çıkarma) sistemi.

  - market   : Pazar vitrini  (/ilanlar sayfasının üstündeki "Vitrin" satırı)
  - category : Vitrin ürün    (kategori seçiliyken "Kategori vitrini" satırı)
  - banner   : Reklam banneri (ana sayfa hero slider'ında otomatik oluşan "Reklam" afişi)

Fiyatlar doping_prices tablosundadır (kuruş) ve yönetici panelinden (/admin/doping) düzenlenir. Satın alma bakiyeden,
tek işlemde yapılır. Aynı ilan+tür için süresi dolmamış doping varsa yeni satın alma süreyi UZATIR: yeni satır
öncekinin bitişinden başlar (zincir). Süre kontrolü sorgu anında (datetime('now')) yapılır; zamanlanmış iş gerekmez
(yalnızca süresi dolmuş reklam bannerlarının temizliği /cron/gunluk ve yönetici doping sayfasında yapılır).

Satıcı ve yönetici rotaları seller / admin blueprint'lerine bu modülden eklenir (endpoint adları: seller.doping,
seller.doping_buy, admin.doping). Modül, blueprint'ler uygulamaya kaydedilmeden önce içe aktarılmalıdır (app.py).
"""
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta

from flask import abort, flash, g, redirect, render_template, request, url_for

import core
import services
import storage
from core import BizError, ex, q, q1

DOPING_KINDS = {
    "market": ("Pazar vitrini", "İlanlar sayfasının en üstündeki Vitrin satırında gösterilir."),
    "category": ("Vitrin ürün", "İlanın kategorisi açıldığında sayfanın üstündeki Kategori vitrini satırında gösterilir."),
    "banner": ("Reklam banneri", "Ana sayfanın üstündeki reklam panosunda ilanının görseli ve bağlantısıyla otomatik yayınlanır."),
}
DOPING_HOURS = (12, 24, 48, 168)
SHOWCASE_LIMIT = 8
BANNER_KEEP_DAYS = 3
MIN_PRICE = 100                   # 1 TL
MAX_PRICE = 10_000_000            # 100.000 TL
# Süresi içinde (başlamış ve bitmemiş) doping koşulu; tablo takma adı d.
LIVE = "d.starts_at <= datetime('now') AND d.ends_at > datetime('now')"


# --------------------------------------------------------------------------- yardımcılar
def hours_label(h):
    h = int(h)
    if h == 168:
        return "1 hafta"
    if h >= 24 and h % 24 == 0:
        return f"{h // 24} gün"
    return f"{h} saat"


def kind_label(kind):
    return DOPING_KINDS[kind][0] if kind in DOPING_KINDS else kind


def placeholders(n):
    return ",".join("?" * n)


def price_map(only_active=True):
    """Etkin fiyatlar: {tür: {saat: kuruş}}."""
    out = {}
    for r in q("SELECT kind, hours, price, is_active FROM doping_prices ORDER BY kind, hours"):
        if only_active and not r["is_active"]:
            continue
        if r["kind"] not in DOPING_KINDS or int(r["hours"]) not in DOPING_HOURS:
            continue
        out.setdefault(r["kind"], {})[int(r["hours"])] = int(r["price"])
    return out


def kinds_view():
    """Şablonlar için seçenek listesi: [{key,label,desc,options:[{hours,label,price}]}].
    Fiyat yalnızca görüntü içindir; sunucu satın alırken veritabanından okur."""
    prices = price_map(True)
    out = []
    for key, (label, desc) in DOPING_KINDS.items():
        opts = [{"hours": h, "label": hours_label(h), "price": p} for h, p in sorted(prices.get(key, {}).items())]
        out.append({"key": key, "label": label, "desc": desc, "options": opts})
    return out


def read_items():
    """Formdaki doping_<tür> alanlarını okur: [(tür, saat), ...]. Geçersiz tür/süre BizError."""
    items = []
    for kind in DOPING_KINDS:
        raw = (request.form.get("doping_" + kind) or "").strip()
        if raw in ("", "0"):
            continue
        if not re.fullmatch(r"\d{1,4}", raw) or int(raw) not in DOPING_HOURS:
            raise BizError("Geçersiz doping süresi seçildi.")
        items.append((kind, int(raw)))
    return items


def selected_from_form():
    """Formda seçili süreler (yeniden gösterim için): {tür: saat | 0}."""
    sel = {}
    for kind in DOPING_KINDS:
        raw = (request.form.get("doping_" + kind) or "").strip()
        sel[kind] = int(raw) if re.fullmatch(r"\d{1,4}", raw) else 0
    return sel


def new_key():
    return secrets.token_hex(12)


def read_key():
    k = (request.form.get("req_key") or "").strip()
    return k if re.fullmatch(r"[0-9a-f]{24}", k) else None


def form_ctx(sel=None):
    """Şablon bağlamı: doping bölümü için."""
    sel = sel or {}
    return {"doping": kinds_view(), "dsel": {k: int(sel.get(k, 0) or 0) for k in DOPING_KINDS}, "dkey": new_key()}


def public_cond():
    """Herkese açık "satışa açık ilan" koşulu (l, c, u takma adlarıyla)."""
    seller_ok = "u.is_seller = 1" if core.setting("require_seller_approval", "1") == "1" else "1 = 1"
    return f"l.status = 'active' AND c.is_active = 1 AND u.is_banned = 0 AND {seller_ok}"


def block_reason(listing, user, stock):
    """İlan doping alamıyorsa nedenini döndürür; alabiliyorsa None."""
    if listing["status"] != "active":
        if listing["status"] == "blocked":
            return "Bu ilan yönetici tarafından engellendi; doping alınamaz."
        return "Doping yalnızca yayındaki ilanlar için alınabilir. Önce ilanı yayına al."
    if not core.can_sell(user):
        return "Satış yetkin kapalı olduğu için doping alınamaz."
    if stock <= 0:
        return "Stoğu biten ilana doping alınamaz. Önce kod ekle."
    cat = q1("SELECT is_active FROM categories WHERE id = ?", (listing["category_id"],))
    if not cat or not cat["is_active"]:
        return "İlanın kategorisi şu an kapalı; doping alınamaz."
    return None


def utc_plus(utc, hours):
    try:
        base = datetime.strptime(str(utc)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        base = core.utcnow()
    return core.utc_str(base + timedelta(hours=int(hours)))


def dark_hex(color):
    m = re.fullmatch(r"#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", color or "")
    if not m:
        return "#1b1140"
    return "#" + "".join(f"{int(int(c, 16) * 0.28):02x}" for c in m.groups())


def copy_cover(name):
    """Kapağı yeni dosya adıyla kopyalar (banner silinince ilanın kapağı etkilenmesin). Başarısızsa ''."""
    if not name or not services.MEDIA_NAME_RE.match(name):
        return ""
    found = storage.get("cover", name)
    if not found:
        return ""
    new = uuid.uuid4().hex + "." + name.rsplit(".", 1)[-1]
    storage.put("cover", new, found[1], found[0])
    return new


def cleanup_banners():
    """Süresi bitmiş reklam bannerlarını (ve görsellerini) birkaç gün sonra siler; doping kaydının banner_id'sini boşaltır."""
    n = 0
    rows = q(
        "SELECT id, image FROM banners WHERE is_ad = 1 AND ends_at IS NOT NULL AND ends_at < datetime('now', ?)",
        (f"-{BANNER_KEEP_DAYS} days",),
    )
    for b in rows:
        if ex("DELETE FROM banners WHERE id = ? AND is_ad = 1", (b["id"],)).rowcount == 1:
            ex("UPDATE listing_dopings SET banner_id = NULL WHERE banner_id = ?", (b["id"],))
            services.delete_cover(b["image"])
            n += 1
    return n


def banner_usage():
    """Aktif reklam banner doluluğu: (adet, en erken biten zaman | None)."""
    r = q1(
        "SELECT COUNT(*) AS n, MIN(e) AS first_end FROM ("
        " SELECT b.id, MAX(d.ends_at) AS e FROM banners b JOIN listing_dopings d ON d.banner_id = b.id"
        " WHERE b.is_ad = 1 AND b.slot = 'hero' AND b.is_active = 1 AND (b.ends_at IS NULL OR b.ends_at > datetime('now'))"
        " AND d.ends_at > datetime('now') GROUP BY b.id HAVING SUM(d.starts_at <= datetime('now')) > 0) AS t"
    )
    return int(r["n"]), r["first_end"]


def max_banners():
    return max(0, min(core.setting_int("doping_max_banners", 8), 50))


# --------------------------------------------------------------------------- satın alma çekirdeği
def purchase(uid, lid, items, req_key=None):
    """Seçili dopingleri satın alır (kendi işlemini açar). Hata durumunda hiçbir şey kaydedilmez."""
    _check_items(items)
    with core.tx():
        return purchase_in_tx(uid, lid, items, req_key)


def _check_items(items):
    if not items:
        raise BizError("En az bir doping seç.")
    seen = set()
    for kind, hours in items:
        if kind not in DOPING_KINDS or hours not in DOPING_HOURS:
            raise BizError("Geçersiz doping seçimi.")
        if kind in seen:
            raise BizError("Aynı doping türü bir kez seçilebilir.")
        seen.add(kind)


def purchase_in_tx(uid, lid, items, req_key=None):
    """purchase() çekirdeği: çağıran core.tx() içinde olmalıdır (ilan formu, ilanı ve dopingi tek işlemde oluşturur).
    Yazma kilidi (BEGIN IMMEDIATE) bakiye, ilan ve reklam panosu doluluğu denetimlerini yarışsız kılar."""
    _check_items(items)
    user = q1("SELECT * FROM users WHERE id = ?", (uid,))
    if not user:
        raise BizError("Kullanıcı bulunamadı.")
    l = q1(core.LISTING_SELECT + " WHERE l.id = ?", (lid,))
    if not l or l["seller_id"] != uid or l["status"] == "removed":
        raise BizError("Bu ilan için doping alamazsın.")
    if req_key and q1("SELECT 1 AS x FROM listing_dopings WHERE req_key LIKE ?", (req_key + "%",)):
        raise BizError("Bu istek zaten işlendi; tekrar ücret alınmadı.")
    stock = q1("SELECT COUNT(*) AS c FROM listing_codes WHERE listing_id = ? AND is_sold = 0", (lid,))["c"]
    reason = block_reason(l, user, stock)
    if reason:
        raise BizError(reason)

    # fiyatlar yalnızca veritabanından okunur
    plan, total = [], 0
    for kind, hours in items:
        p = q1("SELECT price FROM doping_prices WHERE kind = ? AND hours = ? AND is_active = 1", (kind, hours))
        if not p or int(p["price"]) <= 0:
            raise BizError(f"{kind_label(kind)} için {hours_label(hours)} seçeneği şu an satışta değil.")
        total += int(p["price"])
        plan.append((kind, hours, int(p["price"])))
    if user["balance"] < total:
        raise BizError(f"Yetersiz bakiye. Doping tutarı {core.fmt_money(total)}, bakiyen {core.fmt_money(user['balance'])}.")

    now = q1("SELECT datetime('now') AS n")["n"]
    done = []
    for idx, (kind, hours, price) in enumerate(plan, start=1):
        # art arda alınan dopingler zincirlenir
        chain = q1(
            "SELECT MAX(ends_at) AS e FROM listing_dopings WHERE listing_id = ? AND kind = ? AND ends_at > datetime('now')",
            (lid, kind),
        )
        extending = bool(chain["e"])
        starts = chain["e"] if extending else now
        ends = utc_plus(starts, hours)
        key = f"{req_key}{idx}" if req_key else None
        if key is None:
            dup = q1(
                "SELECT id FROM listing_dopings WHERE seller_id = ? AND listing_id = ? AND kind = ? AND hours = ?"
                " AND created_at >= datetime('now', '-3 seconds') LIMIT 1",
                (uid, lid, kind, hours),
            )
            if dup:
                raise BizError("Aynı doping isteği az önce işlendi. Sayfayı yenileyip dopinglerini kontrol et.")

        banner_id = None
        if kind == "banner":
            if extending:
                prev = q1(
                    "SELECT banner_id FROM listing_dopings WHERE listing_id = ? AND kind = ? AND ends_at > datetime('now')"
                    " ORDER BY ends_at DESC LIMIT 1",
                    (lid, kind),
                )
                b = q1("SELECT * FROM banners WHERE id = ? AND is_ad = 1", (prev["banner_id"],)) if prev and prev["banner_id"] else None
                if not b or not b["is_active"]:
                    raise BizError("Bu ilanın reklam bannerı yönetim tarafından kaldırıldı ya da kapatıldı; süre uzatılamıyor.")
                banner_id = int(b["id"])
                ex("UPDATE banners SET ends_at = ? WHERE id = ?", (ends, banner_id))
            else:
                used, first_end = banner_usage()
                if used >= max_banners():
                    when = core.fmt_dt(first_end) if first_end else "daha sonra"
                    raise BizError(f"Reklam panosu şu an dolu, en erken {when} tarihinde tekrar dene.")
                banner_id = create_banner(l, now, ends)

        try:
            cur = ex(
                "INSERT INTO listing_dopings(listing_id, seller_id, kind, hours, price, starts_at, ends_at, banner_id, req_key)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (lid, uid, kind, hours, price, starts, ends, banner_id, key),
            )
        except sqlite3.IntegrityError:
            raise BizError("Bu istek zaten işlendi; tekrar ücret alınmadı.")
        did = int(cur.lastrowid)
        desc = f"Doping: {kind_label(kind)} ({hours_label(hours)}) - ilan #{lid}"
        core.change_balance(uid, -price, "doping", desc, "doping", did)
        done.append({"id": did, "kind": kind, "hours": hours, "price": price, "starts_at": starts, "ends_at": ends,
                     "banner_id": banner_id, "extended": extending})
    names = ", ".join(f"{kind_label(d['kind'])} ({hours_label(d['hours'])})" for d in done)
    services.notify(uid, "Doping etkinleştirildi", f"{l['title'][:60]}: {names}", url_for("seller.doping"))
    return done


def create_banner(l, starts, ends):
    """Reklam banner satırını oluşturur; kapağı banner görseli olarak kopyalar."""
    image = copy_cover(l["cover"])
    c1 = l["cat_color"] if re.fullmatch(r"#[0-9a-fA-F]{6}", l["cat_color"] or "") else "#7c5cff"
    cur = ex(
        "INSERT INTO banners(slot, title, subtitle, cta_text, link, image, color1, color2, is_active, sort_order, starts_at, ends_at, is_ad, listing_id)"
        " VALUES ('hero', ?, ?, 'İlana git', ?, ?, ?, ?, 1, 0, ?, ?, 1, ?)",
        (
            l["title"][:160], f"{l['seller_display']} | {core.fmt_money(l['price'])}"[:400],
            url_for("listing_detail", lid=l["id"]), image, c1, dark_hex(c1), starts, ends, l["id"],
        ),
    )
    return int(cur.lastrowid)


# --------------------------------------------------------------------------- vitrin sorguları (herkese açık)
def showcase(kind, cat_slug="", exclude=(), limit=SHOWCASE_LIMIT):
    """Vitrin satırı: aktif dopingli, satışa açık, stoklu ilanlar (rastgele sırada)."""
    where = public_cond()
    args = []
    if cat_slug:
        where += " AND c.slug = ?"
        args.append(cat_slug)
    where += f" AND EXISTS (SELECT 1 FROM listing_dopings d WHERE d.listing_id = l.id AND d.kind = ? AND {LIVE})"
    args.append(kind)
    exclude = [int(x) for x in exclude]
    if exclude:
        where += f" AND l.id NOT IN ({placeholders(len(exclude))})"
        args += exclude
    rows = q(f"SELECT * FROM ({core.LISTING_SELECT} WHERE {where}) WHERE stock > 0 ORDER BY RANDOM() LIMIT {int(limit)}", args)
    out = []
    for r in rows:
        d = dict(r)
        d["vitrin"] = 1
        out.append(d)
    return out


def flag_rows(rows):
    """Normal liste satırlarına, aktif vitrin dopingi olanlar için vitrin=1 işareti koyar (satırlar sözlüğe çevrilir)."""
    rows = [dict(r) for r in rows]
    if not rows:
        return rows
    ids = [int(r["id"]) for r in rows]
    hit = {
        r["listing_id"]
        for r in q(
            f"SELECT DISTINCT d.listing_id FROM listing_dopings d WHERE d.kind IN ('market', 'category') AND {LIVE}"
            f" AND d.listing_id IN ({placeholders(len(ids))})",
            ids,
        )
    }
    for r in rows:
        r["vitrin"] = 1 if r["id"] in hit else 0
    return rows


def attach(rows):
    """Her ilan satırına 'dp' (aktif doping listesi) ekler: [{kind,label,ends_at}] (satırlar sözlüğe çevrilir)."""
    rows = [dict(r) for r in rows]
    if not rows:
        return rows
    ids = [int(r["id"]) for r in rows]
    by = {}
    for r in q(
        "SELECT listing_id, kind, MAX(ends_at) AS ends_at FROM listing_dopings WHERE ends_at > datetime('now')"
        f" AND listing_id IN ({placeholders(len(ids))}) GROUP BY listing_id, kind ORDER BY kind",
        ids,
    ):
        by.setdefault(r["listing_id"], []).append({"kind": r["kind"], "label": kind_label(r["kind"]), "ends_at": r["ends_at"]})
    for r in rows:
        r["dp"] = by.get(r["id"], [])
    return rows


# --------------------------------------------------------------------------- satıcı rotaları
from seller import bp as seller_bp  # noqa: E402


def _own_listing(lid):
    item = q1(core.LISTING_SELECT + " WHERE l.id = ? AND l.seller_id = ? AND l.status != 'removed'", (lid, g.user["id"]))
    if not item:
        abort(404)
    return item


@seller_bp.route("/doping", endpoint="doping")
def seller_doping():
    uid = g.user["id"]
    listings = attach(q(
        "SELECT * FROM (" + core.LISTING_SELECT + " WHERE l.seller_id = ? AND l.status IN ('active', 'paused', 'blocked'))"
        " ORDER BY id DESC LIMIT 100",
        (uid,),
    ))
    active = [dict(a) for a in q(
        "SELECT d.listing_id, d.kind, MAX(d.ends_at) AS ends_at, MIN(d.starts_at) AS starts_at, COUNT(*) AS n, SUM(d.price) AS spent,"
        " l.title, l.cover, l.status FROM listing_dopings d JOIN listings l ON l.id = d.listing_id"
        " WHERE d.seller_id = ? AND d.ends_at > datetime('now') GROUP BY d.listing_id, d.kind ORDER BY ends_at",
        (uid,),
    )]
    now = core.utc_str()
    for a in active:
        a["label"] = kind_label(a["kind"])
        a["live"] = a["starts_at"] <= now
    history = [dict(h) for h in q(
        "SELECT d.*, l.title FROM listing_dopings d JOIN listings l ON l.id = d.listing_id WHERE d.seller_id = ? ORDER BY d.id DESC LIMIT 15",
        (uid,),
    )]
    for h in history:
        h["label"] = kind_label(h["kind"])
        h["hours_label"] = hours_label(h["hours"])
    total_spent = q1("SELECT COALESCE(SUM(price), 0) AS s FROM listing_dopings WHERE seller_id = ?", (uid,))["s"]
    used, first_end = banner_usage()
    return render_template(
        "seller_doping.html", listings=listings, active=active, history=history, kinds=kinds_view(), total_spent=total_spent,
        banner_used=used, banner_max=max_banners(), banner_first_end=first_end,
    )


@seller_bp.route("/doping/<int:lid>", methods=["GET", "POST"], endpoint="doping_buy")
def seller_doping_buy(lid):
    item = _own_listing(lid)
    uid = g.user["id"]
    sel = {}
    if request.method == "POST":
        try:
            items = read_items()
            key = read_key()
            if key is None:
                raise BizError("Form süresi doldu; sayfayı yenileyip tekrar dene.")
            done = purchase(uid, lid, items, key)
        except BizError as err:
            flash(str(err), "bad")
            sel = selected_from_form()
        else:
            total = sum(d["price"] for d in done)
            parts = [
                f"{kind_label(d['kind'])} ({hours_label(d['hours'])})" + (" süresi uzatıldı" if d["extended"] else " başladı")
                for d in done
            ]
            flash(f"Doping satın alındı: {', '.join(parts)}. Tutar {core.fmt_money(total)} bakiyenden düşüldü.", "ok")
            return redirect(url_for("seller.doping"))
        item = _own_listing(lid)
    cur = q1("SELECT * FROM users WHERE id = ?", (uid,))
    stock = q1("SELECT COUNT(*) AS c FROM listing_codes WHERE listing_id = ? AND is_sold = 0", (lid,))["c"]
    block = block_reason(item, cur, stock)
    return render_template(
        "seller_doping_buy.html", item=item, blocked=block, balance=cur["balance"], active_dp=attach([item])[0]["dp"], **form_ctx(sel),
    )


# --------------------------------------------------------------------------- yönetici
from admin import bp as admin_bp  # noqa: E402


@admin_bp.route("/doping", methods=["GET", "POST"], endpoint="doping")
def admin_doping():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "prices":
                rows = q("SELECT * FROM doping_prices ORDER BY id")
                upd = []
                for r in rows:
                    price = core.to_kurus(request.form.get(f"price_{r['id']}"))
                    if price is None or price < MIN_PRICE or price > MAX_PRICE:
                        raise BizError(f"{kind_label(r['kind'])} / {hours_label(r['hours'])}: fiyat 1 ₺ ile 100.000 ₺ arasında olmalı.")
                    upd.append((r, price, 1 if request.form.get(f"active_{r['id']}") else 0))
                changes = []
                with core.tx():
                    for r, price, active in upd:
                        if r["price"] != price or r["is_active"] != active:
                            ex("UPDATE doping_prices SET price = ?, is_active = ? WHERE id = ?", (price, active, r["id"]))
                            changes.append(f"{r['kind']}/{r['hours']}s {core.fmt_plain(r['price'])}->{core.fmt_plain(price)}" + ("" if active else " (kapalı)"))
                if changes:
                    core.log_admin("Doping fiyatları", "; ".join(changes)[:480])
                    flash("Doping fiyatları kaydedildi.", "ok")
                else:
                    flash("Değişiklik yok.", "info")
            elif action == "settings":
                mx = request.form.get("doping_max_banners", type=int)
                if mx is None or not 0 <= mx <= 50:
                    raise BizError("Reklam panosu kapasitesi 0 ile 50 arasında olmalı.")
                ex(
                    "INSERT INTO settings(key, value) VALUES ('doping_max_banners', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (str(mx),),
                )
                core.log_admin("Doping ayarı", f"reklam panosu kapasitesi: {mx}")
                flash("Reklam panosu kapasitesi kaydedildi.", "ok")
            else:
                abort(400)
        except BizError as err:
            flash(str(err), "bad")
        return redirect(url_for("admin.doping"))
    cleanup_banners()
    prices = [dict(p) for p in q("SELECT * FROM doping_prices ORDER BY id")]
    for p in prices:
        p["kind_label"] = kind_label(p["kind"])
        p["hours_label"] = hours_label(p["hours"])
    totals = q1(
        "SELECT COUNT(*) AS n, COALESCE(SUM(price), 0) AS revenue,"
        " COALESCE(SUM(CASE WHEN created_at >= datetime('now', '-7 days') THEN price END), 0) AS week,"
        " COALESCE(SUM(CASE WHEN created_at >= datetime('now', '-30 days') THEN price END), 0) AS month"
        " FROM listing_dopings"
    )
    by_kind = {k: {"kind": k, "label": kind_label(k), "n": 0, "revenue": 0, "active": 0} for k in DOPING_KINDS}
    for r in q("SELECT kind, COUNT(*) AS n, COALESCE(SUM(price), 0) AS revenue FROM listing_dopings GROUP BY kind"):
        if r["kind"] in by_kind:
            by_kind[r["kind"]].update(n=r["n"], revenue=r["revenue"])
    for r in q(f"SELECT d.kind, COUNT(DISTINCT d.listing_id) AS n FROM listing_dopings d WHERE {LIVE} GROUP BY d.kind"):
        if r["kind"] in by_kind:
            by_kind[r["kind"]]["active"] = r["n"]
    recent = [dict(r) for r in q(
        "SELECT d.*, l.title, u.username FROM listing_dopings d JOIN listings l ON l.id = d.listing_id JOIN users u ON u.id = d.seller_id"
        " ORDER BY d.id DESC LIMIT 25"
    )]
    now = core.utc_str()
    for r in recent:
        r["label"] = kind_label(r["kind"])
        r["hours_label"] = hours_label(r["hours"])
        r["live"] = r["starts_at"] <= now < r["ends_at"]
    used, first_end = banner_usage()
    return render_template(
        "admin_doping.html", prices=prices, totals=totals, by_kind=list(by_kind.values()), recent=recent,
        banner_used=used, banner_max=max_banners(), banner_first_end=first_end,
    )

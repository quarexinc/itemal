"""Topluluk: satıcı takibi ve çekilişler.

Herkese açık: community.follow_toggle, community.following, community.giveaways, community.giveaway_view,
              community.giveaway_join, community.giveaway_leave
Satıcı:       seller.followers, seller.giveaways, seller.giveaway_new, seller.giveaway_draw, seller.giveaway_cancel
Yönetim:      admin.giveaways, admin.giveaway_cancel, admin.giveaway_setting

Çekiliş kuralları: satıcı başına en fazla 3 açık çekiliş (pakette ek hak olabilir); katılım için giriş, en az 1 saatlik
hesap, isteğe bağlı olarak "satıcıyı takip et" / "bu mağazadan alışveriş yapmış ol" koşulları; kura sunucuda
secrets.SystemRandom ile çekilir; süre dolunca kendiliğinden (services.release_due içinden) ya da satıcı isteyince.
"""
import secrets
from datetime import timedelta

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for

import core
import services
from admin import bp as admin_bp
from core import BizError, ex, field, q, q1
from seller import bp as seller_bp

bp = Blueprint("community", __name__)

BASE_SLOTS = 3
DURATIONS = {24: "1 gün", 72: "3 gün", 168: "7 gün", 336: "14 gün"}
GW_STATUS = {"open": ("Devam ediyor", "ok"), "drawn": ("Sonuçlandı", "info"), "cancelled": ("İptal edildi", "bad")}


# --------------------------------------------------------------------------- takip
def follower_count(sid):
    return q1("SELECT COUNT(*) AS n FROM seller_follows WHERE seller_id = ?", (sid,))["n"]


def is_following(uid, sid):
    return bool(uid and q1("SELECT 1 FROM seller_follows WHERE user_id = ? AND seller_id = ?", (uid, sid)))


def notify_followers(seller_id, title, body, link, key):
    """Takipçilere bildirim düşer; aynı satıcı için saatte en fazla 3 toplu bildirim (spam koruması)."""
    if core.rate_hit("fnotify:" + key, 3, 3600, key=f"s{seller_id}"):
        return 0
    rows = q("SELECT user_id FROM seller_follows WHERE seller_id = ? ORDER BY created_at DESC LIMIT 500", (seller_id,))
    for r in rows:
        services.notify(r["user_id"], title, body, link, kind="info")
    return len(rows)


@bp.post("/takip/<int:sid>")
@core.login_required
def follow_toggle(sid):
    seller = q1("SELECT * FROM users WHERE id = ? AND is_banned = 0", (sid,))
    if not seller or not core.can_sell(seller):
        abort(404)
    wants_json = request.headers.get("X-Requested-With") == "fetch"
    msg, following = "", False
    if sid == g.user["id"]:
        msg = "Kendi mağazanı takip edemezsin."
    elif core.rate_hit("follow", 60, 3600, key=f"u{g.user['id']}"):
        msg = "Kısa sürede çok fazla takip işlemi yaptın. Biraz bekle."
    elif is_following(g.user["id"], sid):
        ex("DELETE FROM seller_follows WHERE user_id = ? AND seller_id = ?", (g.user["id"], sid))
        msg = "Takipten çıkıldı."
    else:
        ex("INSERT OR IGNORE INTO seller_follows(user_id, seller_id) VALUES (?,?)", (g.user["id"], sid))
        following = True
        msg = "Mağazayı takip ediyorsun. Yeni ilan ve çekilişlerden haberdar olacaksın."
        services.notify(sid, "Yeni takipçi", f"{g.user['username']} mağazanı takip etmeye başladı.", url_for("seller.followers"), kind="ok")
    if wants_json:
        return jsonify({"ok": True, "following": following, "count": follower_count(sid), "msg": msg})
    flash(msg, "ok" if following else "info")
    return redirect(request.referrer or url_for("storefront", username=seller["username"]))


@bp.route("/takip-ettiklerim")
@core.login_required
def following():
    rows = q(
        "SELECT u.id, u.username, u.store_name, u.avatar, f.created_at AS since,"
        " (SELECT COUNT(*) FROM listings l WHERE l.seller_id = u.id AND l.status = 'active') AS listings,"
        " (SELECT COUNT(*) FROM giveaways gw WHERE gw.seller_id = u.id AND gw.status = 'open' AND gw.ends_at > datetime('now')) AS gws"
        " FROM seller_follows f JOIN users u ON u.id = f.seller_id WHERE f.user_id = ? AND u.is_banned = 0 ORDER BY f.created_at DESC",
        (g.user["id"],),
    )
    fresh = q(
        core.LISTING_SELECT
        + " WHERE l.status = 'active' AND c.is_active = 1 AND u.is_banned = 0 AND l.seller_id IN (SELECT seller_id FROM seller_follows WHERE user_id = ?)"
        " ORDER BY l.id DESC LIMIT 8",
        (g.user["id"],),
    )
    return render_template("following.html", rows=rows, fresh=fresh)


# --------------------------------------------------------------------------- çekilişler (herkese açık)
def slots_for(uid):
    try:
        import packages
        extra = int(packages.marks(uid).get("gslots", 0))
    except Exception:
        extra = 0
    return BASE_SLOTS + extra


def remaining(ends_at):
    """'2 gün 4 saat' gibi kalan süre; bitmişse 'Süre doldu'."""
    try:
        from datetime import datetime
        end = datetime.strptime(str(ends_at)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "-"
    left = end - core.utcnow()
    secs = int(left.total_seconds())
    if secs <= 0:
        return "Süre doldu"
    d, rest = divmod(secs, 86400)
    h, rest = divmod(rest, 3600)
    m = rest // 60
    if d:
        return f"{d} gün {h} saat"
    if h:
        return f"{h} saat {m} dk"
    return f"{max(m, 1)} dk"


GW_SELECT = (
    "SELECT gw.*, u.username AS seller_name, u.store_name, u.avatar AS seller_avatar FROM giveaways gw JOIN users u ON u.id = gw.seller_id"
)


@bp.route("/cekilisler")
def giveaways():
    sweep()
    open_rows = q(GW_SELECT + " WHERE gw.status = 'open' AND gw.ends_at > datetime('now') AND u.is_banned = 0 ORDER BY gw.ends_at LIMIT 60")
    done = q(GW_SELECT + " WHERE gw.status = 'drawn' AND u.is_banned = 0 ORDER BY gw.drawn_at DESC LIMIT 9")
    mine = set()
    if g.user:
        mine = {r["giveaway_id"] for r in q("SELECT giveaway_id FROM giveaway_entries WHERE user_id = ?", (g.user["id"],))}
    return render_template("giveaways.html", open_rows=open_rows, done=done, mine=mine, remaining=remaining)


def _winners(gid):
    return q(
        "SELECT u.id, u.username FROM giveaway_entries e JOIN users u ON u.id = e.user_id WHERE e.giveaway_id = ? AND e.is_winner = 1 ORDER BY u.username",
        (gid,),
    )


def eligibility(gw, user):
    """(katılabilir_mi, açıklama). Koşullar: giriş, açık çekiliş, kendi çekilişi değil, hesap yaşı, takip/alışveriş şartı."""
    if gw["status"] != "open" or gw["ends_at"] <= core.utc_str():
        return False, "Bu çekiliş sona erdi."
    if not user:
        return False, "Katılmak için giriş yapmalısın."
    if user["id"] == gw["seller_id"]:
        return False, "Kendi çekilişine katılamazsın."
    created = str(user["created_at"])[:19]
    if created > (core.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"):
        return False, "Çekilişlere katılmak için hesabının en az 1 saatlik olması gerekir."
    if gw["need_purchase"] and not q1(
        "SELECT 1 FROM orders WHERE buyer_id = ? AND seller_id = ? AND escrow_status != 'refunded' LIMIT 1", (user["id"], gw["seller_id"])
    ):
        return False, "Bu çekilişe yalnızca mağazadan alışveriş yapmış üyeler katılabilir."
    return True, ""


@bp.route("/cekilis/<int:gid>")
def giveaway_view(gid):
    sweep()
    gw = q1(GW_SELECT + " WHERE gw.id = ?", (gid,))
    if not gw:
        abort(404)
    uid = g.user["id"] if g.user else None
    entered = bool(uid and q1("SELECT 1 FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?", (gid, uid)))
    ok, why = eligibility(gw, g.user)
    follows = is_following(uid, gw["seller_id"])
    won = bool(uid and q1("SELECT 1 FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ? AND is_winner = 1", (gid, uid)))
    return render_template(
        "giveaway_view.html", gw=gw, entered=entered, ok=ok, why=why, follows=follows, won=won,
        winners=_winners(gid) if gw["status"] == "drawn" else [], left=remaining(gw["ends_at"]), status=GW_STATUS[gw["status"]],
        is_owner=bool(uid and uid == gw["seller_id"]),
    )


@bp.post("/cekilis/<int:gid>/katil")
@core.login_required
def giveaway_join(gid):
    gw = q1(GW_SELECT + " WHERE gw.id = ?", (gid,))
    if not gw:
        abort(404)
    try:
        if core.rate_hit("gwjoin", 40, 3600, key=f"u{g.user['id']}"):
            raise BizError("Kısa sürede çok fazla katılım denemesi yaptın. Biraz bekle.")
        ok, why = eligibility(gw, g.user)
        if not ok:
            raise BizError(why)
        if gw["need_follow"] and not is_following(g.user["id"], gw["seller_id"]):
            if request.form.get("follow") == "1":
                ex("INSERT OR IGNORE INTO seller_follows(user_id, seller_id) VALUES (?,?)", (g.user["id"], gw["seller_id"]))
            else:
                raise BizError("Bu çekilişe katılmak için önce mağazayı takip etmelisin.")
        with core.tx():
            cur = ex("INSERT OR IGNORE INTO giveaway_entries(giveaway_id, user_id) VALUES (?,?)", (gid, g.user["id"]))
            if cur.rowcount:
                ex("UPDATE giveaways SET entry_count = entry_count + 1 WHERE id = ?", (gid,))
        flash("Çekilişe katıldın. Bol şans!" if cur.rowcount else "Zaten bu çekilişe katıldın.", "ok" if cur.rowcount else "info")
    except BizError as err:
        flash(str(err), "bad")
    return redirect(url_for("community.giveaway_view", gid=gid))


@bp.post("/cekilis/<int:gid>/ayril")
@core.login_required
def giveaway_leave(gid):
    gw = q1("SELECT * FROM giveaways WHERE id = ?", (gid,))
    if not gw or gw["status"] != "open":
        abort(404)
    with core.tx():
        cur = ex("DELETE FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?", (gid, g.user["id"]))
        if cur.rowcount:
            ex("UPDATE giveaways SET entry_count = MAX(entry_count - 1, 0) WHERE id = ?", (gid,))
    flash("Çekilişten ayrıldın.", "info")
    return redirect(url_for("community.giveaway_view", gid=gid))


# --------------------------------------------------------------------------- kura
_last_sweep = [0.0]


def sweep(force=False):
    """Süresi dolan açık çekilişleri çeker (en fazla 60 sn'de bir)."""
    import time
    now = time.time()
    if not force and now - _last_sweep[0] < 60:
        return 0
    _last_sweep[0] = now
    due = q("SELECT id FROM giveaways WHERE status = 'open' AND ends_at <= datetime('now') LIMIT 20")
    n = 0
    for r in due:
        if draw(r["id"], by="otomatik"):
            n += 1
    return n


def draw(gid, by="otomatik"):
    """Kurayı çeker ve kazananlara bildirim düşer. Zaten çekilmişse/iptal edilmişse False."""
    with core.tx():
        cur = ex("UPDATE giveaways SET status = 'drawn', drawn_at = datetime('now') WHERE id = ? AND status = 'open'", (gid,))
        if cur.rowcount != 1:
            return False
        gw = q1("SELECT * FROM giveaways WHERE id = ?", (gid,))
        pool = [r["user_id"] for r in q("SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?", (gid,))]
        if gw["need_follow"]:            # takip şartı çekiliş anında da geçerli: takipten çıkanlar elenir
            keep = {r["user_id"] for r in q("SELECT user_id FROM seller_follows WHERE seller_id = ?", (gw["seller_id"],))}
            pool = [u for u in pool if u in keep]
        picked = secrets.SystemRandom().sample(pool, min(len(pool), gw["winners"])) if pool else []
        for u in picked:
            ex("UPDATE giveaway_entries SET is_winner = 1 WHERE giveaway_id = ? AND user_id = ?", (gid, u))
        link = f"/cekilis/{gid}"
        for u in picked:
            services.notify(u, "Çekilişi kazandın", f"{gw['title']} çekilişini kazandın. Ödül: {gw['prize']}. Ödülün için satıcıyla mesajlaşabilirsin.", link, kind="ok")
        names = ", ".join(r["username"] for r in q(f"SELECT username FROM users WHERE id IN ({','.join('?' * len(picked))})", picked)) if picked else "katılım olmadı"
        services.notify(gw["seller_id"], "Çekilişin sonuçlandı", f"{gw['title']}: kazananlar {names}. Ödülü teslim etmeyi unutma.", link, kind="ok")
        losers = [u for u in pool if u not in picked][:300]
        for u in losers:
            services.notify(u, "Çekiliş sonuçlandı", f"{gw['title']} çekilişi sonuçlandı. Kazananları çekiliş sayfasında görebilirsin.", link, kind="info")
    return True


# --------------------------------------------------------------------------- satıcı paneli
@seller_bp.route("/takipciler")
def followers():
    page = core.paginate(
        "SELECT u.id, u.username, u.avatar, f.created_at AS since,"
        " (SELECT COUNT(*) FROM orders o WHERE o.buyer_id = u.id AND o.seller_id = f.seller_id AND o.escrow_status != 'refunded') AS orders"
        " FROM seller_follows f JOIN users u ON u.id = f.user_id WHERE f.seller_id = ? ORDER BY f.created_at DESC",
        (g.user["id"],), 25,
    )
    week = q1("SELECT COUNT(*) AS n FROM seller_follows WHERE seller_id = ? AND created_at >= datetime('now', '-7 days')", (g.user["id"],))["n"]
    total = follower_count(g.user["id"])
    buyers = q1(
        "SELECT COUNT(*) AS n FROM seller_follows f WHERE f.seller_id = ? AND EXISTS (SELECT 1 FROM orders o WHERE o.buyer_id = f.user_id"
        " AND o.seller_id = f.seller_id AND o.escrow_status != 'refunded')", (g.user["id"],),
    )["n"]
    return render_template("seller_followers.html", page=page, total=total, week=week, buyers=buyers)


@seller_bp.route("/cekilisler")
def giveaways():
    mine = q("SELECT * FROM giveaways WHERE seller_id = ? ORDER BY id DESC LIMIT 50", (g.user["id"],))
    open_n = sum(1 for r in mine if r["status"] == "open")
    slots = slots_for(g.user["id"])
    enabled = core.setting("giveaway_enabled", "1") == "1"
    return render_template(
        "seller_giveaways.html", rows=mine, open_n=open_n, slots=slots, enabled=enabled, durations=DURATIONS, status=GW_STATUS, remaining=remaining,
        followers=follower_count(g.user["id"]),
    )


@seller_bp.post("/cekilis/yeni")
def giveaway_new():
    try:
        if core.setting("giveaway_enabled", "1") != "1":
            raise BizError("Çekiliş özelliği şu an kapalı.")
        title, prize, desc = field("title", 80), field("prize", 120), field("description", 600)
        winners = request.form.get("winners", type=int) or 1
        hours = request.form.get("hours", type=int) or 0
        if not 5 <= len(title) <= 80:
            raise BizError("Çekiliş başlığı 5-80 karakter olmalı.")
        if not 3 <= len(prize) <= 120:
            raise BizError("Ödülü kısaca yaz (3-120 karakter).")
        if not 1 <= winners <= 10:
            raise BizError("Kazanan sayısı 1 ile 10 arasında olmalı.")
        if hours not in DURATIONS:
            raise BizError("Geçerli bir süre seç.")
        open_n = q1("SELECT COUNT(*) AS n FROM giveaways WHERE seller_id = ? AND status = 'open'", (g.user["id"],))["n"]
        slots = slots_for(g.user["id"])
        if open_n >= slots:
            raise BizError(f"Aynı anda en fazla {slots} açık çekilişin olabilir. Birini bitir ya da Çekiliş paketi al.")
        daily = max(10, slots * 3)
        if core.rate_hit("gwnew", daily, 86400, key=f"u{g.user['id']}"):
            raise BizError(f"Bir günde en fazla {daily} çekiliş açabilirsin.")
        ends = (core.utcnow() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cur = ex(
            "INSERT INTO giveaways(seller_id, title, prize, description, winners, ends_at, need_follow, need_purchase) VALUES (?,?,?,?,?,?,?,?)",
            (g.user["id"], title, prize, desc, winners, ends, 1 if request.form.get("need_follow") else 0, 1 if request.form.get("need_purchase") else 0),
        )
        notify_followers(g.user["id"], "Yeni çekiliş: " + title[:60], f"{g.user['store_name'] or g.user['username']} çekiliş başlattı. Ödül: {prize}", url_for("community.giveaway_view", gid=cur.lastrowid), "gw")
        flash("Çekiliş yayınlandı. Takipçilerin bilgilendirildi.", "ok")
        return redirect(url_for("community.giveaway_view", gid=cur.lastrowid))
    except BizError as err:
        flash(str(err), "bad")
        return redirect(url_for("seller.giveaways"))


def _own_gw(gid):
    gw = q1("SELECT * FROM giveaways WHERE id = ? AND seller_id = ?", (gid, g.user["id"]))
    if not gw:
        abort(404)
    return gw


@seller_bp.post("/cekilis/<int:gid>/cek")
def giveaway_draw(gid):
    gw = _own_gw(gid)
    if gw["status"] != "open":
        flash("Bu çekiliş zaten sonuçlandı ya da iptal edildi.", "info")
    elif not gw["entry_count"]:
        flash("Henüz katılımcı yok; süre dolana kadar bekleyebilir ya da çekilişi iptal edebilirsin.", "bad")
    elif draw(gid, by="satıcı"):
        flash("Kura çekildi. Kazananlara bildirim gönderildi.", "ok")
    return redirect(request.referrer or url_for("seller.giveaways"))


@seller_bp.post("/cekilis/<int:gid>/iptal")
def giveaway_cancel(gid):
    gw = _own_gw(gid)
    if gw["status"] == "open":
        ex("UPDATE giveaways SET status = 'cancelled', drawn_at = datetime('now') WHERE id = ?", (gid,))
        flash("Çekiliş iptal edildi.", "info")
    return redirect(url_for("seller.giveaways"))


# --------------------------------------------------------------------------- yönetim
@admin_bp.route("/cekilisler")
def giveaways_admin():
    flt = request.args.get("durum", "")
    where, args = "1=1", []
    if flt in GW_STATUS:
        where, args = "gw.status = ?", [flt]
    page = core.paginate(GW_SELECT + " WHERE " + where + " ORDER BY gw.id DESC", args, 25)
    kpi = q1(
        "SELECT COUNT(*) AS n, COALESCE(SUM(status = 'open'), 0) AS open_n, COALESCE(SUM(entry_count), 0) AS entries FROM giveaways"
    )
    return render_template("admin_giveaways.html", page=page, flt=flt, kpi=kpi, status=GW_STATUS, enabled=core.setting("giveaway_enabled", "1") == "1")


@admin_bp.post("/cekilis/<int:gid>/iptal")
def giveaway_cancel_admin(gid):
    gw = q1("SELECT * FROM giveaways WHERE id = ?", (gid,))
    if not gw:
        abort(404)
    if gw["status"] == "open":
        ex("UPDATE giveaways SET status = 'cancelled', drawn_at = datetime('now') WHERE id = ?", (gid,))
        services.notify(gw["seller_id"], "Çekilişin iptal edildi", f"{gw['title'][:80]} çekilişi yönetim tarafından iptal edildi.", url_for("seller.giveaways"), kind="bad")
        core.log_admin("Çekiliş iptal", f"#{gid} {gw['title'][:50]}")
        flash("Çekiliş iptal edildi.", "ok")
    return redirect(request.referrer or url_for("admin.giveaways_admin"))


@admin_bp.post("/cekilisler/ayar")
def giveaway_setting():
    on = "1" if request.form.get("enabled") == "1" else "0"
    ex("INSERT INTO settings(key, value) VALUES ('giveaway_enabled', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (on,))
    core.log_admin("Çekiliş özelliği", "açık" if on == "1" else "kapalı")
    flash("Çekiliş özelliği açıldı." if on == "1" else "Çekiliş özelliği kapatıldı.", "ok")
    return redirect(url_for("admin.giveaways_admin"))


# --------------------------------------------------------------------------- mağaza sayfası verileri
def store_extra(seller):
    """storefront.html için: takipçi, çekilişler, başarılı işlem sayısı/oranı, yorum yazma yetkisi."""
    uid = g.user["id"] if g.user else None
    row = q1(
        "SELECT COALESCE(SUM(escrow_status = 'released'), 0) AS ok, COALESCE(SUM(escrow_status = 'refunded'), 0) AS refunded,"
        " COALESCE(SUM(escrow_status = 'disputed'), 0) AS disputed FROM orders WHERE seller_id = ?",
        (seller["id"],),
    )
    ok = int(row["ok"]) + int(seller["demo_sold"] or 0)
    total = ok + int(row["refunded"]) + int(row["disputed"])
    can_comment = bool(
        uid and uid != seller["id"]
        and q1("SELECT 1 FROM orders WHERE buyer_id = ? AND seller_id = ? AND escrow_status != 'refunded' LIMIT 1", (uid, seller["id"]))
    )
    gws = q(GW_SELECT + " WHERE gw.seller_id = ? AND gw.status = 'open' AND gw.ends_at > datetime('now') ORDER BY gw.ends_at LIMIT 3", (seller["id"],))
    return {
        "followers": follower_count(seller["id"]),
        "i_follow": is_following(uid, seller["id"]),
        "ok_orders": ok,
        "ok_rate": int(round(ok * 100 / total)) if total >= 5 else None,
        "can_comment": can_comment,
        "store_gws": gws,
        "gw_left": remaining,
    }


def install(app):
    app.register_blueprint(bp)
    app.jinja_env.globals.update(follower_count=follower_count, gw_remaining=remaining)

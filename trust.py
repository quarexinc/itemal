"""Güven katmanı: rapor (ilan/kullanıcı), mağaza yorumları, sipariş onayı (emanet) ve canlı bildirim akışı."""
from datetime import datetime

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for

import core
import services
from core import BizError, ex, field, q, q1

bp = Blueprint("trust", __name__)

LISTING_REASONS = [
    "Sahte veya kullanılmış kod şüphesi",
    "Yanıltıcı başlık veya açıklama",
    "Yasaklı ya da uygunsuz ürün",
    "Fiyat veya stok manipülasyonu",
    "Platform dışına yönlendirme",
    "Diğer",
]
USER_REASONS = [
    "Dolandırıcılık şüphesi",
    "Küfür, hakaret veya taciz",
    "Platform dışı ödeme talebi",
    "Sahte hesap veya kimlik taklidi",
    "Spam veya istenmeyen mesaj",
    "Diğer",
]
ORDER_REASONS = [
    "Kod çalışmıyor",
    "Kod daha önce kullanılmış",
    "Yanlış ürün teslim edildi",
    "Satıcı yanıt vermiyor",
    "Diğer",
]
REASONS = {"listing": LISTING_REASONS, "user": USER_REASONS, "order": ORDER_REASONS}


def _make_report(kind, target_id, reasons):
    reason = field("reason", 80)
    detail = field("detail", 600)
    if reason not in reasons:
        raise BizError("Lütfen bir şikayet nedeni seç.")
    if reason == "Diğer" and len(detail) < 10:
        raise BizError("Diğer seçeneğinde birkaç cümleyle açıklama yazmalısın.")
    if core.is_limited("report", 12, 3600):
        raise BizError("Kısa sürede çok fazla bildirim gönderdin. Biraz sonra tekrar dene.")
    if q1("SELECT 1 FROM reports WHERE kind = ? AND target_id = ? AND reporter_id = ? AND status = 'open'", (kind, target_id, g.user["id"])):
        raise BizError("Bu bildirimin zaten inceleniyor. Yeni bir gelişme olursa destek talebi açabilirsin.")
    core.record_attempt("report")
    cur = ex(
        "INSERT INTO reports(kind, target_id, reporter_id, reason, detail) VALUES (?,?,?,?,?)",
        (kind, target_id, g.user["id"], reason, detail),
    )
    return cur.lastrowid


# --------------------------------------------------------------------------- rapor
@bp.post("/ilan/<int:lid>/raporla")
@core.login_required
def report_listing(lid):
    item = q1("SELECT id, seller_id FROM listings WHERE id = ? AND status != 'removed'", (lid,))
    if not item:
        abort(404)
    try:
        if item["seller_id"] == g.user["id"]:
            raise BizError("Kendi ilanını bildiremezsin.")
        _make_report("listing", lid, LISTING_REASONS)
    except BizError as err:
        flash(str(err), "bad")
    else:
        flash("Bildirimin alındı. İlan ekibimiz tarafından incelenecek.", "ok")
    return redirect(url_for("listing_detail", lid=lid))


@bp.post("/kullanici/<username>/raporla")
@core.login_required
def report_user(username):
    target = q1("SELECT id, username FROM users WHERE username = ?", (username,))
    if not target:
        abort(404)
    try:
        if target["id"] == g.user["id"]:
            raise BizError("Kendini bildiremezsin.")
        _make_report("user", target["id"], USER_REASONS)
    except BizError as err:
        flash(str(err), "bad")
    else:
        flash("Bildirimin alındı. Yönetim ekibi inceleyecek.", "ok")
    return redirect(request.referrer or url_for("storefront", username=username))


# --------------------------------------------------------------------------- mağaza yorumları
@bp.post("/magaza/<username>/yorum")
@core.login_required
def seller_comment(username):
    seller = q1("SELECT * FROM users WHERE username = ? AND is_banned = 0", (username,))
    if not seller or not core.can_sell(seller):
        abort(404)
    body = services.clean_message(request.form.get("body"), 500)
    try:
        if seller["id"] == g.user["id"]:
            raise BizError("Kendi mağazana yorum yazamazsın.")
        if not q1("SELECT 1 FROM orders WHERE buyer_id = ? AND seller_id = ? AND escrow_status != 'refunded' LIMIT 1", (g.user["id"], seller["id"])):
            raise BizError("Mağaza yorumunu yalnızca bu satıcıdan alışveriş yapmış alıcılar yazabilir.")
        if not 5 <= len(body) <= 500:
            raise BizError("Yorum 5 ile 500 karakter arasında olmalı.")
        if core.is_limited("scomment", 8, 3600):
            raise BizError("Kısa sürede çok fazla yorum yazdın. Biraz sonra tekrar dene.")
        core.record_attempt("scomment")
        ex(
            "INSERT INTO seller_comments(seller_id, author_id, body) VALUES (?,?,?)"
            " ON CONFLICT(seller_id, author_id) DO UPDATE SET body = excluded.body, created_at = datetime('now')",
            (seller["id"], g.user["id"], body),
        )
        services.notify(seller["id"], "Mağazana yeni yorum", body[:80], url_for("storefront", username=username))
    except BizError as err:
        flash(str(err), "bad")
    else:
        flash("Yorumun eklendi.", "ok")
    return redirect(url_for("storefront", username=username) + "#yorumlar")


@bp.post("/magaza/yorum/<int:cid>/sil")
@core.login_required
def seller_comment_delete(cid):
    row = q1("SELECT c.*, u.username FROM seller_comments c JOIN users u ON u.id = c.seller_id WHERE c.id = ?", (cid,))
    if not row or row["author_id"] != g.user["id"]:
        abort(404)
    ex("DELETE FROM seller_comments WHERE id = ?", (cid,))
    flash("Yorumun silindi.", "info")
    return redirect(url_for("storefront", username=row["username"]) + "#yorumlar")


# --------------------------------------------------------------------------- sipariş onayı (emanet)
@bp.post("/siparis/<int:oid>/onayla")
@core.login_required
def order_confirm(oid):
    order = q1("SELECT * FROM orders WHERE id = ? AND buyer_id = ?", (oid, g.user["id"]))
    if not order:
        abort(404)
    with core.tx():
        done = services.release_order(oid, by="alıcı")
    if done:
        flash("Siparişi onayladın. Tutar satıcıya aktarıldı, teşekkürler.", "ok")
    else:
        flash("Bu sipariş zaten sonuçlanmış.", "info")
    return redirect(url_for("order_detail", oid=oid))


@bp.post("/siparis/<int:oid>/itiraz")
@core.login_required
def order_dispute(oid):
    order = q1("SELECT * FROM orders WHERE id = ? AND buyer_id = ?", (oid, g.user["id"]))
    if not order:
        abort(404)
    try:
        if order["escrow_status"] != "held":
            raise BizError("Bu sipariş için artık itiraz edilemez.")
        with core.tx():
            _make_report("order", oid, ORDER_REASONS)
            ex("UPDATE orders SET escrow_status = 'disputed' WHERE id = ? AND escrow_status = 'held'", (oid,))
            services.notify(order["seller_id"], "Siparişe itiraz edildi", f"#{oid} numaralı sipariş yönetim tarafından inceleniyor.", url_for("order_detail", oid=oid))
    except BizError as err:
        flash(str(err), "bad")
    else:
        flash("İtirazın alındı. Tutar incelemenin sonucuna kadar satıcıya aktarılmayacak.", "ok")
    return redirect(url_for("order_detail", oid=oid))


# --------------------------------------------------------------------------- canlı bildirim akışı (kısa aralıklı sorgu)
@bp.get("/canli")
def live():
    """Yeni mesaj / bildirim / bakiye bilgisini döndürür. İstemci ~2 sn'de bir sorar; m ve n son görülen kimliklerdir."""
    if not g.user:
        return jsonify({"ok": False}), 401
    uid = g.user["id"]
    top = q1(
        "SELECT (SELECT COALESCE(MAX(m.id), 0) FROM messages m JOIN conversations v ON v.id = m.conversation_id"
        "  WHERE m.sender_id != ?1 AND (v.buyer_id = ?1 OR v.seller_id = ?1)) AS m,"
        " (SELECT COALESCE(MAX(id), 0) FROM notifications WHERE user_id = ?1) AS n,"
        " (SELECT COUNT(*) FROM notifications WHERE user_id = ?1 AND is_read = 0) AS nu,"
        " (SELECT balance FROM users WHERE id = ?1) AS bal",
        (uid,),
    )
    out = {
        "ok": True, "m": top["m"], "n": top["n"], "unread_notif": top["nu"],
        "unread_chat": services.unread_messages(uid), "balance": core.fmt_money(top["bal"]), "events": [],
    }
    m_after = request.args.get("m", type=int)
    n_after = request.args.get("n", type=int)
    if m_after is not None and top["m"] > m_after:
        rows = q(
            "SELECT m.id, m.body, m.conversation_id, u.username, COALESCE(NULLIF(u.store_name, ''), u.username) AS shown"
            " FROM messages m JOIN conversations v ON v.id = m.conversation_id JOIN users u ON u.id = m.sender_id"
            " WHERE m.id > ?2 AND m.sender_id != ?1 AND (v.buyer_id = ?1 OR v.seller_id = ?1) ORDER BY m.id LIMIT 5",
            (uid, m_after),
        )
        for r in rows:
            out["events"].append({
                "kind": "message", "id": r["id"], "title": "Yeni mesaj: " + r["shown"], "body": r["body"][:120],
                "url": url_for("chat", cid=r["conversation_id"]), "conv": r["conversation_id"],
            })
    if n_after is not None and top["n"] > n_after:
        for r in q("SELECT * FROM notifications WHERE user_id = ? AND id > ? ORDER BY id LIMIT 5", (uid, n_after)):
            out["events"].append({
                "kind": "notif", "id": r["id"], "title": r["title"], "body": r["body"],
                "url": url_for("site.notif_view", nid=r["id"]),
            })
    return jsonify(out)

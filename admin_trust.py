"""Yönetim paneli - güven modülleri: şikayet kuyruğu, mağaza yorumları, emanet işlemleri."""
from flask import abort, flash, redirect, render_template, request, url_for

import core
import services
from admin import bp, like
from core import BizError, ex, field, q, q1


# --------------------------------------------------------------------------- şikayetler
@bp.route("/bildirimler")
def complaints():
    status = request.args.get("durum", "open")
    if status not in ("open", "resolved", "dismissed", "all"):
        status = "open"
    kind = request.args.get("tur", "")
    where, args = [], []
    if status != "all":
        where.append("r.status = ?")
        args.append(status)
    if kind in ("listing", "user", "order"):
        where.append("r.kind = ?")
        args.append(kind)
    sql = (
        "SELECT r.*, rp.username AS reporter_name,"
        " l.title AS listing_title, l.status AS listing_status, l.seller_id AS listing_seller,"
        " tu.username AS target_name, tu.is_banned AS target_banned,"
        " o.listing_title AS order_title, o.escrow_status AS order_escrow, o.total AS order_total, o.seller_id AS order_seller"
        " FROM reports r JOIN users rp ON rp.id = r.reporter_id"
        " LEFT JOIN listings l ON r.kind = 'listing' AND l.id = r.target_id"
        " LEFT JOIN users tu ON r.kind = 'user' AND tu.id = r.target_id"
        " LEFT JOIN orders o ON r.kind = 'order' AND o.id = r.target_id"
        + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY r.id DESC"
    )
    page = core.paginate(sql, args, 20)
    counts = {r["status"]: r["c"] for r in q("SELECT status, COUNT(*) AS c FROM reports GROUP BY status")}
    return render_template("admin_complaints.html", page=page, status=status, kind=kind, counts=counts)


@bp.post("/bildirim/<int:rid>")
def complaint_action(rid):
    action = request.form.get("action")
    note = field("note", 300)
    try:
        with core.tx():
            r = q1("SELECT * FROM reports WHERE id = ?", (rid,))
            if not r:
                abort(404)
            if r["status"] != "open":
                raise BizError("Bu bildirim zaten sonuçlandırılmış.")
            result = "resolved"
            if action == "dismiss":
                result = "dismissed"
            elif action == "block_listing" and r["kind"] == "listing":
                ex("UPDATE listings SET status = 'blocked', updated_at = datetime('now') WHERE id = ?", (r["target_id"],))
                core.log_admin("Bildirim üzerine ilan engellendi", f"ilan #{r['target_id']} bildirim #{rid}")
            elif action == "ban_user" and r["kind"] == "user":
                ex("UPDATE users SET is_banned = 1 WHERE id = ?", (r["target_id"],))
                core.log_admin("Bildirim üzerine hesap askıya alındı", f"kullanıcı #{r['target_id']} bildirim #{rid}")
            elif action == "release_order" and r["kind"] == "order":
                if not services.release_order(r["target_id"], by="yönetim"):
                    raise BizError("Sipariş zaten sonuçlanmış.")
                core.log_admin("Bildirim üzerine emanet serbest bırakıldı", f"sipariş #{r['target_id']} bildirim #{rid}")
            elif action == "refund_order" and r["kind"] == "order":
                if not services.refund_order(r["target_id"], note):
                    raise BizError("Sipariş zaten sonuçlanmış.")
                core.log_admin("Bildirim üzerine sipariş iade edildi", f"sipariş #{r['target_id']} bildirim #{rid}")
            elif action != "resolve":
                abort(400)
            ex("UPDATE reports SET status = ?, admin_note = ?, reviewed_at = datetime('now') WHERE id = ?", (result, note, rid))
            services.notify(r["reporter_id"], "Bildirimin incelendi", note or "Bildirimin için teşekkürler, gerekli işlem yapıldı." if result == "resolved" else (note or "Bildirimin incelendi; işlem gerektiren bir durum bulunamadı."), "")
    except BizError as err:
        flash(str(err), "bad")
    else:
        flash("Bildirim sonuçlandırıldı.", "ok")
    return redirect(request.referrer or url_for("admin.complaints"))


# --------------------------------------------------------------------------- mağaza yorumları
@bp.route("/magaza-yorumlari")
def seller_comments():
    page = core.paginate(
        "SELECT c.*, a.username AS author_name, s.username AS seller_name FROM seller_comments c"
        " JOIN users a ON a.id = c.author_id JOIN users s ON s.id = c.seller_id ORDER BY c.id DESC",
        (), 20,
    )
    return render_template("admin_scomments.html", page=page)


@bp.post("/magaza-yorumu/<int:cid>")
def seller_comment_action(cid):
    action = request.form.get("action")
    if not q1("SELECT 1 FROM seller_comments WHERE id = ?", (cid,)):
        abort(404)
    if action == "hide":
        ex("UPDATE seller_comments SET is_hidden = 1 WHERE id = ?", (cid,))
    elif action == "show":
        ex("UPDATE seller_comments SET is_hidden = 0 WHERE id = ?", (cid,))
    elif action == "delete":
        ex("DELETE FROM seller_comments WHERE id = ?", (cid,))
    else:
        abort(400)
    core.log_admin("Mağaza yorumu düzenlendi", f"#{cid} {action}")
    flash("İşlem yapıldı.", "ok")
    return redirect(request.referrer or url_for("admin.seller_comments"))


# --------------------------------------------------------------------------- emanet
@bp.post("/siparis/<int:oid>/emanet")
def escrow_action(oid):
    action = request.form.get("action")
    try:
        with core.tx():
            if not q1("SELECT 1 FROM orders WHERE id = ?", (oid,)):
                abort(404)
            if action == "release":
                ok = services.release_order(oid, by="yönetim")
            elif action == "refund":
                ok = services.refund_order(oid, field("note", 200))
            else:
                abort(400)
            if not ok:
                raise BizError("Bu sipariş emanette değil.")
            core.log_admin("Emanet işlemi", f"sipariş #{oid}: {action}")
    except BizError as err:
        flash(str(err), "bad")
    else:
        flash("Emanet işlemi tamamlandı.", "ok")
    return redirect(request.referrer or url_for("admin.orders"))

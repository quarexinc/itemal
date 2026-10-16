"""API: /api/v1/... (satıcı REST API'si, Bearer anahtar) ve /api/webhook/odeme (HMAC imzalı ödeme bildirimi).

Bu uçlar çerez/oturum kullanmaz, bu yüzden CSRF korumasının dışındadır.
"""
import hashlib
import hmac
import os
import time

from flask import Blueprint, g, jsonify, request

import core
import services
from core import BizError, ex, q, q1

bp = Blueprint("api", __name__, url_prefix="/api")
WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
_hits = {}


def err(message, status=400):
    return jsonify({"error": message}), status


def rate_ok(bucket, limit=120, window=60):
    """SQLite tabanlı sayaç: yeniden başlatmada ve çok işlemli çalışmada da geçerli."""
    return not core.rate_hit("api", limit, window, key=":".join(str(b) for b in bucket))


def authenticate():
    """Authorization: Bearer itm_... -> (api_key satırı, kullanıcı) ya da (None, hata yanıtı)."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, err("Authorization: Bearer <api_anahtari> başlığı gerekli.", 401)
    if core.is_limited("api_bad", 20, 600):
        return None, err("Çok fazla geçersiz anahtar denemesi. Biraz bekle.", 429)
    key = q1("SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1", (services.hash_api_key(header[7:].strip()[:200]),))
    if not key:
        core.record_attempt("api_bad")
        return None, err("Geçersiz veya iptal edilmiş API anahtarı.", 401)
    user = q1("SELECT * FROM users WHERE id = ?", (key["user_id"],))
    if not user or user["is_banned"] or not core.can_sell(user):
        return None, err("Bu anahtarın sahibi satıcı işlemleri yapamıyor.", 403)
    if not rate_ok(("key", key["id"])):
        return None, err("Çok fazla istek. Dakikada en fazla 120 istek gönderebilirsin.", 429)
    ex("UPDATE api_keys SET last_used_at = datetime('now') WHERE id = ?", (key["id"],))
    return user, None


def listing_json(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["cat_name"],
        "price": round(row["price"] / 100, 2),
        "status": row["status"],
        "stock": row["stock"],
        "sales_count": row["sales_count"],
        "views": row["views"],
        "rating": services.rating_of(row),
        "review_count": row["rating_count"],
    }


@bp.route("/v1/me")
def me():
    user, bad = authenticate()
    if bad:
        return bad
    stats = services.seller_stats(user["id"])
    return jsonify({
        "username": user["username"],
        "store_name": user["store_name"] or user["username"],
        "balance": round(user["balance"] / 100, 2),
        "withdrawable": round(core.withdrawable(user["id"]) / 100, 2),
        "total_sold": stats["sold"],
        "rating": stats["rating"],
        "review_count": stats["reviews"],
        "badges": [b["label"] for b in services.user_badges(user, stats)],
    })


@bp.route("/v1/listings")
def listings():
    user, bad = authenticate()
    if bad:
        return bad
    rows = q(core.LISTING_SELECT + " WHERE l.seller_id = ? AND l.status != 'removed' ORDER BY l.id DESC LIMIT 500", (user["id"],))
    return jsonify({"listings": [listing_json(r) for r in rows]})


def own_listing(user, lid):
    return q1(core.LISTING_SELECT + " WHERE l.id = ? AND l.seller_id = ? AND l.status != 'removed'", (lid, user["id"]))


@bp.post("/v1/listings/<int:lid>/stock")
def add_stock(lid):
    user, bad = authenticate()
    if bad:
        return bad
    item = own_listing(user, lid)
    if not item:
        return err("İlan bulunamadı.", 404)
    body = request.get_json(silent=True) or {}
    raw = body.get("codes")
    if not isinstance(raw, list) or not raw or not all(isinstance(c, str) for c in raw):
        return err('Gövde {"codes": ["KOD1", "KOD2"]} biçiminde olmalı.')
    try:
        codes = core.parse_codes("\n".join(raw))
        if not codes:
            raise BizError("Eklenecek kod bulunamadı.")
        with core.tx():
            existing = {r["code"] for r in q("SELECT code FROM listing_codes WHERE listing_id = ?", (lid,))}
            fresh = [c for c in codes if c not in existing]
            for c in fresh:
                ex("INSERT INTO listing_codes(listing_id, code) VALUES (?,?)", (lid, c))
            ex("UPDATE listings SET updated_at = datetime('now') WHERE id = ?", (lid,))
    except BizError as e:
        return err(str(e))
    stock = q1("SELECT COUNT(*) AS c FROM listing_codes WHERE listing_id = ? AND is_sold = 0", (lid,))["c"]
    return jsonify({"added": len(fresh), "skipped": len(codes) - len(fresh), "stock": stock})


@bp.post("/v1/listings/<int:lid>/status")
def set_status(lid):
    user, bad = authenticate()
    if bad:
        return bad
    item = own_listing(user, lid)
    if not item:
        return err("İlan bulunamadı.", 404)
    if item["status"] == "blocked":
        return err("İlan yönetici tarafından engellendi.", 403)
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ("active", "paused"):
        return err('status "active" veya "paused" olmalı.')
    ex("UPDATE listings SET status = ?, updated_at = datetime('now') WHERE id = ?", (status, lid))
    return jsonify({"id": lid, "status": status})


@bp.route("/v1/orders")
def orders():
    user, bad = authenticate()
    if bad:
        return bad
    after = request.args.get("after_id", 0, type=int)
    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    rows = q(
        "SELECT o.*, b.username AS buyer_name FROM orders o JOIN users b ON b.id = o.buyer_id"
        " WHERE o.seller_id = ? AND o.id > ? ORDER BY o.id LIMIT ?",
        (user["id"], after, limit),
    )
    return jsonify({"orders": [
        {
            "id": r["id"], "listing_id": r["listing_id"], "listing_title": r["listing_title"], "buyer": r["buyer_name"],
            "quantity": r["quantity"], "total": round(r["total"] / 100, 2), "commission_rate": r["commission_rate"],
            "commission": round(r["commission"] / 100, 2), "net_earning": round(r["seller_earning"] / 100, 2),
            "created_at": r["created_at"],
        } for r in rows
    ]})


# --------------------------------------------------------------------------- ödeme webhook'u
@bp.post("/webhook/odeme")
def payment_webhook():
    """Ödeme sağlayıcısı başarılı ödemeyi buraya bildirir; bekleyen yükleme talebi otomatik onaylanır.

    Başlık: X-Signature = HMAC-SHA256(PAYMENT_WEBHOOK_SECRET, ham istek gövdesi) (hex)
    Gövde : {"deposit_id": 12, "amount": "250.00", "status": "success", "transaction_id": "ABC123"}
    """
    if not WEBHOOK_SECRET:
        return err("Webhook yapılandırılmamış (PAYMENT_WEBHOOK_SECRET).", 503)
    if not rate_ok(("hook", request.remote_addr), 120, 60):
        return err("Çok fazla istek.", 429)
    raw = request.get_data()
    sent = request.headers.get("X-Signature", "").strip().lower()
    expected = hmac.new(WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not sent or not hmac.compare_digest(sent, expected):
        return err("İmza doğrulanamadı.", 401)
    body = request.get_json(silent=True) or {}
    deposit_id = body.get("deposit_id")
    txid = str(body.get("transaction_id") or "").strip()[:80]
    status = body.get("status")
    amount = core.to_kurus(body.get("amount"))
    if not isinstance(deposit_id, int) or not txid or status not in ("success", "failed") or amount is None:
        return err("deposit_id (sayı), transaction_id, status (success/failed) ve amount zorunlu.")
    try:
        with core.tx():
            d = q1("SELECT * FROM deposits WHERE id = ?", (deposit_id,))
            if not d:
                raise BizError("Yükleme talebi bulunamadı.")
            if d["provider_ref"] == txid and d["status"] != "pending":
                return jsonify({"ok": True, "already_processed": True})
            if d["status"] != "pending":
                raise BizError("Talep zaten sonuçlanmış.")
            if q1("SELECT 1 FROM deposits WHERE provider_ref = ? AND id != ?", (txid, deposit_id)):
                raise BizError("Bu işlem numarası başka bir talepte kullanıldı.")
            if status == "failed":
                ex("UPDATE deposits SET status = 'rejected', provider_ref = ?, auto = 1, admin_note = 'Ödeme sağlayıcısı başarısız bildirdi',"
                   " reviewed_at = datetime('now') WHERE id = ?", (txid, deposit_id))
                core.log_admin("Webhook: yükleme reddedildi", f"#{deposit_id} işlem {txid}")
                return jsonify({"ok": True, "status": "rejected"})
            if amount != d["amount"]:
                raise BizError("Tutar talep edilen tutarla eşleşmiyor.")
            ex("UPDATE deposits SET status = 'approved', provider_ref = ?, auto = 1, admin_note = 'Otomatik onay (webhook)',"
               " reviewed_at = datetime('now') WHERE id = ?", (txid, deposit_id))
            core.change_balance(d["user_id"], d["amount"], "deposit", f"Yükleme #{deposit_id} (otomatik) - {d['method_name']}", "deposit", deposit_id)
            services.notify(d["user_id"], "Bakiye yüklendi", f"{core.fmt_money(d['amount'])} hesabına eklendi.", "/bakiye")
            core.log_admin("Webhook: yükleme onaylandı", f"#{deposit_id} {core.fmt_money(d['amount'])} işlem {txid}")
    except BizError as e:
        return err(str(e), 409)
    return jsonify({"ok": True, "status": "approved"})

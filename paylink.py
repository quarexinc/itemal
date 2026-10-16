"""Ödeme linki ile bakiye yükleme.

Akış:
  1. Yönetici, Yönetim > Ödeme linkleri sayfasında başlık + dış ödeme linki + sabit fiyat tanımlar.
  2. Kullanıcı Bakiye Yükle sayfasında linkin kartındaki "Öde" düğmesine basar: link yeni sekmede açılır,
     bu sekmede "ödemen işleniyor" ekranı gelir (bekleyen bir `deposits` kaydı açılır).
  3. Yönetici Bakiye Yüklemeleri sayfasında kaydı onaylayınca tutar bakiyeye eklenir (mevcut onay akışı).
Kart/ödeme bilgisi bu sitede hiç alınmaz; ödeme dış sayfada yapılır, bakiye yalnızca yönetici onayıyla yüklenir.
"""
import re
from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for

import core
from core import BizError, ex, field, q, q1

bp = Blueprint("paylink", __name__)

MAX_PENDING = 5
MAX_AMOUNT = 50_000_000                     # 500.000 TL
_CTRL = re.compile(r"[\s\x00-\x1f\x7f]")


def clean_url(raw):
    """Yalnızca https:// adresleri; kullanıcı adı/şifre içeren, boşluklu ya da çok uzun adresler reddedilir."""
    url = (raw or "").strip()
    if not url or len(url) > 500 or _CTRL.search(url):
        raise BizError("Ödeme linki geçersiz (boşluk içermemeli, en fazla 500 karakter).")
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme != "https" or not host or "." not in host or "@" in parts.netloc:
        raise BizError("Ödeme linki https:// ile başlayan geçerli bir adres olmalı.")
    return url


# --------------------------------------------------------------------------- kullanıcı
@bp.post("/bakiye/link/<int:lid>/baslat")
@core.login_required
def start(lid):
    """Bekleyen yükleme kaydı açar. Tarayıcı (JS) bu sırada linki yeni sekmede açar; JSON döner."""
    wants_json = request.headers.get("X-Requested-With") == "fetch"
    uid = g.user["id"]
    try:
        link = q1("SELECT * FROM pay_links WHERE id = ? AND is_active = 1", (lid,))
        if not link:
            raise BizError("Bu ödeme linki artık kullanılmıyor.")
        if core.rate_hit("paylink", 12, 3600, key=f"u{uid}"):
            raise BizError("Kısa sürede çok fazla ödeme başlattın. Biraz bekle.")
        # çift tıklama: aynı link için son dakikada açılmış kayıt varsa onu kullan
        recent = q1(
            "SELECT id FROM deposits WHERE user_id = ? AND link_id = ? AND status = 'pending'"
            " AND created_at > datetime('now', '-1 minute') ORDER BY id DESC LIMIT 1", (uid, lid),
        )
        if recent:
            did = recent["id"]
        else:
            open_count = q1("SELECT COUNT(*) AS c FROM deposits WHERE user_id = ? AND status = 'pending'", (uid,))["c"]
            if open_count >= MAX_PENDING:
                raise BizError(f"Bekleyen {MAX_PENDING} talebin var. Onaylanmasını bekle ya da bir tanesini iptal et.")
            did = ex(
                "INSERT INTO deposits(user_id, method_id, method_name, amount, reference, link_id, link_url) VALUES (?,NULL,?,?,?,?,?)",
                (uid, link["title"], link["amount"], "", link["id"], link["url"]),
            ).lastrowid
    except BizError as err:
        if wants_json:
            return jsonify({"ok": False, "error": str(err)}), 400
        flash(str(err), "bad")
        return redirect(url_for("balance"))
    target = url_for("paylink.wait", did=did)
    if wants_json:
        return jsonify({"ok": True, "next": target})
    return redirect(target)


def _own(did):
    d = q1("SELECT * FROM deposits WHERE id = ? AND user_id = ?", (did, g.user["id"]))
    if not d:
        abort(404)
    return d


@bp.get("/bakiye/odeme/<int:did>")
@core.login_required
def wait(did):
    d = _own(did)
    return render_template("pay_wait.html", d=d, balance_now=q1("SELECT balance FROM users WHERE id = ?", (g.user["id"],))["balance"])


@bp.post("/bakiye/odeme/<int:did>/bilgi")
@core.login_required
def info(did):
    d = _own(did)
    try:
        if d["status"] != "pending":
            raise BizError("Bu talep zaten sonuçlanmış.")
        reference = field("reference", 120)
        note = field("note", 300)
        if len(reference) < 3:
            raise BizError("Ödeme numarası, dekont no veya ödemede kullandığın ad soyadı yaz (en az 3 karakter).")
        ex("UPDATE deposits SET reference = ?, note = ? WHERE id = ? AND status = 'pending'", (reference, note, did))
        flash("Bilgin yönetime iletildi. Ödemen kontrol edilince bakiyene eklenecek.", "ok")
    except BizError as err:
        flash(str(err), "bad")
    return redirect(url_for("paylink.wait", did=did))


@bp.post("/bakiye/odeme/<int:did>/iptal")
@core.login_required
def cancel(did):
    d = _own(did)
    if d["status"] == "pending":
        ex("UPDATE deposits SET status = 'rejected', admin_note = 'Kullanıcı vazgeçti', reviewed_at = datetime('now') WHERE id = ? AND status = 'pending'", (did,))
        flash("Ödeme talebi iptal edildi. Ödemeyi yaptıysan iptal etme; destek talebi aç.", "info")
    return redirect(url_for("balance"))


# --------------------------------------------------------------------------- yönetim
from admin import bp as admin_bp  # noqa: E402


def _form():
    title = field("title", 80)
    if len(title) < 3:
        raise BizError("Başlık en az 3 karakter olmalı.")
    amount = core.to_kurus(request.form.get("amount"))
    if amount is None or amount <= 0:
        raise BizError("Geçerli bir fiyat gir.")
    if amount > MAX_AMOUNT:
        raise BizError("Fiyat en fazla 500.000 TL olabilir.")
    return {
        "title": title, "description": field("description", 200), "url": clean_url(request.form.get("url")),
        "amount": amount, "sort_order": request.form.get("sort_order", 0, type=int) or 0,
        "is_active": 1 if request.form.get("is_active") else 0,
    }


@admin_bp.route("/odeme-linkleri", methods=["GET", "POST"])
def admin_paylinks():
    edit = None
    form = {}
    if request.method == "POST":
        lid = request.form.get("id", type=int)
        try:
            data = _form()
            if lid:
                if not q1("SELECT 1 FROM pay_links WHERE id = ?", (lid,)):
                    abort(404)
                ex("UPDATE pay_links SET title=:title, description=:description, url=:url, amount=:amount, sort_order=:sort_order, is_active=:is_active WHERE id=:id",
                   {**data, "id": lid})
                core.log_admin("Ödeme linki güncellendi", f"#{lid} {data['title']} {core.fmt_money(data['amount'])}")
                flash("Ödeme linki güncellendi.", "ok")
            else:
                new_id = ex(
                    "INSERT INTO pay_links(title, description, url, amount, sort_order, is_active) VALUES (:title,:description,:url,:amount,:sort_order,:is_active)", data,
                ).lastrowid
                core.log_admin("Ödeme linki eklendi", f"#{new_id} {data['title']} {core.fmt_money(data['amount'])}")
                flash("Ödeme linki eklendi.", "ok")
            return redirect(url_for("admin.admin_paylinks"))
        except BizError as err:
            flash(str(err), "bad")
            form = dict(request.form)
            edit = q1("SELECT * FROM pay_links WHERE id = ?", (lid,)) if lid else None
    else:
        lid = request.args.get("duzenle", type=int)
        edit = q1("SELECT * FROM pay_links WHERE id = ?", (lid,)) if lid else None
    if edit and not form:
        form = {"id": edit["id"], "title": edit["title"], "description": edit["description"], "url": edit["url"],
                "amount": core.fmt_plain(edit["amount"]), "sort_order": edit["sort_order"], "is_active": "1" if edit["is_active"] else ""}
    elif not form:
        form = {"is_active": "1", "sort_order": 0}
    rows = q(
        "SELECT p.*,"
        " (SELECT COUNT(*) FROM deposits d WHERE d.link_id = p.id AND d.status = 'pending') AS pending_n,"
        " (SELECT COUNT(*) FROM deposits d WHERE d.link_id = p.id AND d.status = 'approved') AS approved_n"
        " FROM pay_links p ORDER BY p.sort_order, p.id"
    )
    return render_template("admin_paylinks.html", rows=rows, edit=edit, form=form)


@admin_bp.post("/odeme-linkleri/<int:lid>/durum")
def admin_paylink_toggle(lid):
    row = q1("SELECT * FROM pay_links WHERE id = ?", (lid,))
    if not row:
        abort(404)
    ex("UPDATE pay_links SET is_active = ? WHERE id = ?", (0 if row["is_active"] else 1, lid))
    core.log_admin("Ödeme linki " + ("kapatıldı" if row["is_active"] else "açıldı"), f"#{lid} {row['title']}")
    return redirect(url_for("admin.admin_paylinks"))


@admin_bp.post("/odeme-linkleri/<int:lid>/sil")
def admin_paylink_delete(lid):
    row = q1("SELECT * FROM pay_links WHERE id = ?", (lid,))
    if not row:
        abort(404)
    ex("DELETE FROM pay_links WHERE id = ?", (lid,))          # geçmiş yüklemeler kalır (link_id sadece bilgi amaçlı)
    core.log_admin("Ödeme linki silindi", f"#{lid} {row['title']}")
    flash("Ödeme linki silindi.", "ok")
    return redirect(url_for("admin.admin_paylinks"))

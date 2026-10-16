"""İş mantığı yardımcıları: görsel işleme, komisyon, rozetler, puanlar, sayaçlar, API anahtarı."""
import hashlib
import io
import re
import secrets
import time
import uuid
from decimal import Decimal

from flask import request
from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

import core
import storage as media_store
from core import BizError, ex, q, q1

Image.MAX_IMAGE_PIXELS = 50_000_000  # sıkıştırma bombası koruması


MEDIA_NAME_RE = re.compile(r"^[0-9a-f]{32}\.(webp|jpg)$")

# --------------------------------------------------------------------------- rozetler
# anahtar: (etiket, css sınıfı, açıklama)
BADGES = {
    "store_member": ("Mağaza Üyesi", "bd-purple", "itemal mağaza üyeliği olan kurumsal satıcı"),
    "top_seller": ("Yıldız Satıcı", "bd-gold", "Yönetim tarafından seçilen üstün performanslı satıcı"),
    "trusted_seller": ("Güvenilir Satıcı", "bd-gold", "Yüksek satış adedi ve müşteri puanı ile kanıtlanmış satıcı"),
    "verified_seller": ("Onaylı Satıcı", "bd-green", "Kimliği ve mağazası itemal tarafından onaylandı"),
    "id_verified": ("Kimliği Doğrulandı", "bd-blue", "Ödeme öncesi kimlik doğrulaması tamamlandı"),
    "partner": ("İş Ortağı", "bd-purple", "itemal ile resmi iş ortaklığı bulunan satıcı"),
    "vip": ("VIP Satıcı", "bd-gold", "Yönetim tarafından seçilen ayrıcalıklı satıcı"),
    "sales_100": ("100+ Satış", "bd-green", "100 ve üzeri başarılı satış"),
    "sales_500": ("Satış Ustası", "bd-gold", "500 ve üzeri başarılı satış"),
    "perfect_rating": ("Kusursuz Puan", "bd-gold", "En az 10 yorumla 4,9 ve üzeri ortalama puan"),
    "fast_reply": ("Hızlı Yanıt", "bd-blue", "Yorumların çoğuna yanıt veren ilgili satıcı"),
    "veteran": ("Deneyimli Satıcı", "bd-purple", "6 aydan uzun süredir aktif ve 50+ satış"),
    "new_store": ("Yeni Mağaza", "bd-green", "Son 30 gün içinde açılan mağaza"),
    "loyal_buyer": ("Sadık Alıcı", "bd-blue", "10 ve üzeri sipariş veren alıcı"),
    "community": ("Topluluk Sesi", "bd-purple", "Satıcılara 5 ve üzeri yorum yazan üye"),
    "tier_gold": ("Altın Mağaza", "bd-gold", "Altın mağaza paketine sahip satıcı"),
    "tier_diamond": ("Elmas Mağaza", "bd-diamond", "Elmas mağaza paketine sahip, en üst seviye satıcı"),
    "fast_delivery": ("Hızlı Teslimat", "bd-cyan", "Hızlı teslimat rozeti paketine sahip satıcı"),
}
MANUAL_BADGES = ("trusted_seller", "store_member", "top_seller", "partner", "vip")

TICKET_CATEGORIES = {
    "odeme": "Ödeme / Bakiye",
    "siparis": "Sipariş / Kod sorunu",
    "hesap": "Hesap / Kimlik",
    "satici": "Satıcı işlemleri",
    "sikayet": "Şikayet",
    "diger": "Diğer",
}
TICKET_STATUS = {"open": ("Açık", "warn"), "answered": ("Yanıtlandı", "ok"), "closed": ("Kapalı", "muted")}
PRIORITIES = {"normal": ("Normal", "muted"), "high": ("Yüksek", "warn"), "urgent": ("Acil", "bad")}


def seller_stats(uid):
    sales = q1("SELECT COALESCE(SUM(quantity), 0) AS sold, COUNT(*) AS orders FROM orders WHERE seller_id = ? AND escrow_status != 'refunded'", (uid,))
    rev = q1(
        "SELECT COUNT(*) AS n, COALESCE(AVG(rating), 0) AS avg FROM reviews WHERE seller_id = ? AND is_hidden = 0", (uid,)
    )
    demo = q1("SELECT demo_sold FROM users WHERE id = ?", (uid,))
    extra = demo["demo_sold"] if demo else 0
    return {
        "sold": sales["sold"] + extra,
        "orders": sales["orders"] + extra,
        "reviews": rev["n"],
        "rating": round(rev["avg"], 1) if rev["n"] else 0,
    }


def user_badges(user, stats=None):
    """Otomatik (kimlik/satıcı/performans) + yöneticinin verdiği rozetleri döndürür."""
    keys = {r["badge"] for r in q("SELECT badge FROM user_badges WHERE user_id = ?", (user["id"],))}
    if user["kyc_status"] == "approved":
        keys.add("id_verified")
    if user["is_seller"]:
        keys.add("verified_seller")
        stats = stats or seller_stats(user["id"])
        try:
            min_rating = float(core.setting("trusted_min_rating", "4.5").replace(",", "."))
        except ValueError:
            min_rating = 4.5
        if (
            stats["sold"] >= core.setting_int("trusted_min_sales", 25)
            and stats["reviews"] >= 5
            and stats["rating"] >= min_rating
        ):
            keys.add("trusted_seller")
        if stats["sold"] >= 500:
            keys.add("sales_500")
        elif stats["sold"] >= 100:
            keys.add("sales_100")
        if stats["reviews"] >= 10 and stats["rating"] >= 4.9:
            keys.add("perfect_rating")
        if stats["reviews"] >= 5:
            replied = q1("SELECT COUNT(*) AS c FROM reviews WHERE seller_id = ? AND is_hidden = 0 AND seller_reply != ''", (user["id"],))["c"]
            if replied * 100 >= stats["reviews"] * 60:
                keys.add("fast_reply")
        age = q1("SELECT CAST(julianday('now') - julianday(?) AS INTEGER) AS d", (user["created_at"],))["d"] if user["created_at"] else 0
        if age is not None and age >= 180 and stats["sold"] >= 50:
            keys.add("veteran")
        if age is not None and age <= 30:
            keys.add("new_store")
    import packages                    # mağaza paketlerinden gelen rozetler (etkin paket varsa)

    keys.update(packages.badge_keys(user["id"]))
    if q1("SELECT COUNT(*) AS c FROM orders WHERE buyer_id = ?", (user["id"],))["c"] >= 10:
        keys.add("loyal_buyer")
    if q1("SELECT COUNT(*) AS c FROM seller_comments WHERE author_id = ? AND is_hidden = 0", (user["id"],))["c"] >= 5:
        keys.add("community")
    order = ["tier_diamond", "tier_gold", "store_member", "partner", "vip", "top_seller", "trusted_seller", "perfect_rating",
             "sales_500", "sales_100", "veteran", "fast_reply", "fast_delivery", "verified_seller", "id_verified", "new_store",
             "loyal_buyer", "community"]
    return [dict(key=k, label=BADGES[k][0], cls=BADGES[k][1], desc=BADGES[k][2]) for k in order if k in keys]


# --------------------------------------------------------------------------- komisyon
def commission_info(seller, category_id):
    """Öncelik: satıcıya özel oran > kategori oranı > genel oran. Etkin mağaza paketlerinin komisyon indirimi (puan)
    düşülür (sıfırın altına inmez). (oran, kaynak) döndürür. Mevcut siparişlerin oranı sipariş anında sabitlendiği
    için sonradan değişmez."""
    if seller["commission_rate"] is not None:
        rate, source = Decimal(str(seller["commission_rate"])), "Satıcıya özel oran"
    else:
        cat = q1("SELECT commission_rate FROM categories WHERE id = ?", (category_id,))
        if cat and cat["commission_rate"] is not None:
            rate, source = Decimal(str(cat["commission_rate"])), "Kategori oranı"
        else:
            rate, source = core.setting_pct("commission_percent", "5"), "Genel oran"
    try:
        sid = seller["id"]
    except (KeyError, IndexError, TypeError):
        sid = None
    if sid:
        import packages

        disc = Decimal(str(packages.commission_discount(sid)))
        if disc > 0 and rate > 0:
            new = max(rate - disc, Decimal(0))
            applied = rate - new
            source += " - paket indirimi (-" + packages.num(applied) + " puan)"
            rate = new.quantize(Decimal(1)) if new == new.to_integral_value() else new.normalize()
    return rate, source


def parse_rate(text):
    """'7,5' -> 7.5. Boşsa None (genel orana dön). Geçersizse BizError."""
    text = (text or "").strip().replace(",", ".").replace("%", "")
    if not text:
        return None
    try:
        val = float(text)
    except ValueError:
        raise BizError("Komisyon oranı sayı olmalı.")
    if not 0 <= val <= 50:
        raise BizError("Komisyon oranı 0 ile 50 arasında olmalı.")
    return round(val, 2)


# --------------------------------------------------------------------------- puanlar
def recalc_rating(listing_id):
    r = q1(
        "SELECT COUNT(*) AS n, COALESCE(SUM(rating), 0) AS s FROM reviews WHERE listing_id = ? AND is_hidden = 0", (listing_id,)
    )
    ex("UPDATE listings SET rating_sum = ?, rating_count = ? WHERE id = ?", (r["s"], r["n"], listing_id))


def rating_of(row):
    return round(row["rating_sum"] / row["rating_count"], 1) if row["rating_count"] else 0


# --------------------------------------------------------------------------- sayaçlar
def unread_messages(uid):
    return q1(
        "SELECT COUNT(*) AS c FROM messages m JOIN conversations v ON v.id = m.conversation_id"
        " WHERE m.read_at IS NULL AND m.sender_id != ?1 AND (v.buyer_id = ?1 OR v.seller_id = ?1)",
        (uid,),
    )["c"]


def answered_tickets(uid):
    return q1("SELECT COUNT(*) AS c FROM tickets WHERE user_id = ? AND status = 'answered'", (uid,))["c"]


# --------------------------------------------------------------------------- API anahtarı
def new_api_key():
    plain = "itm_" + secrets.token_urlsafe(32)
    return plain, plain[:10], hashlib.sha256(plain.encode()).hexdigest()


def hash_api_key(plain):
    return hashlib.sha256(plain.encode()).hexdigest()


# --------------------------------------------------------------------------- ödeme hesabı doğrulama
def _iban_ok(iban):
    if not re.fullmatch(r"TR\d{24}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    return int("".join(str(int(ch, 36)) for ch in rearranged)) % 97 == 1


def validate_payout(method, info):
    """Çekim hesabını yönteme göre doğrular; temizlenmiş değeri döndürür."""
    info = (info or "").strip()
    if method == "IBAN (Banka Havalesi)":
        iban = re.sub(r"\s+", "", info).upper()
        if not _iban_ok(iban):
            raise BizError("Geçerli bir TR IBAN gir (TR ile başlayan 26 karakter).")
        return iban
    if method == "Papara":
        no = re.sub(r"\s+", "", info).upper()
        if not re.fullmatch(r"(PL)?\d{8,12}", no):
            raise BizError("Geçerli bir Papara numarası gir.")
        return no
    if method == "Kripto (USDT - TRC20)":
        addr = re.sub(r"\s+", "", info)
        if not re.fullmatch(r"T[1-9A-HJ-NP-Za-km-z]{33}", addr):
            raise BizError("Geçerli bir TRC20 (T ile başlayan) cüzdan adresi gir.")
        return addr
    raise BizError("Geçerli bir çekim yöntemi seç.")


# --------------------------------------------------------------------------- görsel işleme
MAX_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS * 2


def _open_image(storage, max_bytes, min_side):
    """Yüklenen dosyayı gerçekten görsel mi diye Pillow ile doğrular. (PIL.Image, ham bayt) döndürür."""
    if not storage or not storage.filename:
        return None
    data = storage.stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise BizError(f"Görsel en fazla {max_bytes // (1024 * 1024)} MB olabilir.")
    try:
        probe = Image.open(io.BytesIO(data))
        if probe.width * probe.height > MAX_PIXELS:                 # dekompresyon bombası: piksel sayısı ayrıştırılmadan denetlenir
            raise BizError("Görselin çözünürlüğü çok yüksek (en fazla 40 megapiksel).")
        probe.verify()
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img = ImageOps.exif_transpose(img)
        img.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise BizError("Geçerli bir görsel yükle (JPG, PNG veya WEBP).")
    if fmt not in ("JPEG", "PNG", "WEBP"):
        raise BizError("Yalnızca JPG, PNG veya WEBP görseller yüklenebilir.")
    if min(img.size) < min_side:
        raise BizError(f"Görsel çok küçük; en az {min_side} piksel genişlik/yükseklik olmalı.")
    return img, data


def _flatten(img):
    """Şeffaflığı koyu zemine oturtup RGB'ye çevirir."""
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (26, 17, 64, 255))
        bg.alpha_composite(rgba)
        return bg.convert("RGB")
    return img.convert("RGB")


def save_cover(storage):
    """İlan kapağı: 1280x720 sınırlı ana görsel + 480x300 küçük görsel (EXIF/konum bilgisi temizlenir)."""
    opened = _open_image(storage, 6 * 1024 * 1024, 320)
    if not opened:
        return None
    img = _flatten(opened[0])
    name = uuid.uuid4().hex + ".webp"
    main = img.copy()
    main.thumbnail((1280, 720))
    media_store.save_image(main, "cover", name, "WEBP", quality=84, method=4)
    media_store.save_image(ImageOps.fit(img, (480, 300), Image.LANCZOS), "cover", "t_" + name, "WEBP", quality=80, method=4)
    return name


def save_avatar(storage):
    opened = _open_image(storage, 4 * 1024 * 1024, 120)
    if not opened:
        return None
    img = ImageOps.fit(_flatten(opened[0]), (256, 256), Image.LANCZOS)
    name = uuid.uuid4().hex + ".webp"
    media_store.save_image(img, "avatar", name, "WEBP", quality=85, method=4)
    return name


def save_store_banner(storage):
    """Mağaza sayfası üst görseli (4:1)."""
    opened = _open_image(storage, 6 * 1024 * 1024, 400)
    if not opened:
        return None
    img = ImageOps.fit(_flatten(opened[0]), (1600, 400), Image.LANCZOS)
    name = uuid.uuid4().hex + ".webp"
    media_store.save_image(img, "cover", name, "WEBP", quality=84, method=4)
    return name


def delete_cover(name):
    if not name or not MEDIA_NAME_RE.match(name):
        return
    media_store.delete("cover", name, "t_" + name)


def delete_avatar(name):
    if name and MEDIA_NAME_RE.match(name):
        media_store.delete("avatar", name)


# --------------------------------------------------------------------------- kimlik görseli denetimi
def _ahash(img):
    """8x8 ortalama (perceptual) hash - yeniden boyutlandırılmış/sıkıştırılmış aynı görseli yakalar."""
    small = img.convert("L").resize((8, 8), Image.LANCZOS)
    px = list(small.getdata())
    avg = sum(px) / 64
    bits = "".join("1" if p >= avg else "0" for p in px)
    return f"{int(bits, 2):016x}"


def hamming(a, b):
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except (TypeError, ValueError):
        return 64


def inspect_kyc_image(storage, label):
    """Kimlik fotoğrafını doğrular, EXIF'i temizleyip yüksek kalitede kaydeder, otomatik uyarıları üretir.

    Döndürür: {"name", "hash", "flags": [..]}  (dosya uploads/kyc altına yazılır)
    """
    opened = _open_image(storage, 8 * 1024 * 1024, 300)
    if not opened:
        raise BizError(f"{label} görselini yükle (JPG, PNG veya WEBP).")
    img = _flatten(opened[0])
    flags = []
    if min(img.size) < 600:
        flags.append(f"{label}: düşük çözünürlük ({img.size[0]}x{img.size[1]})")
    gray = img.convert("L")
    mean = ImageStat.Stat(gray).mean[0]
    if mean < 35:
        flags.append(f"{label}: görsel çok karanlık")
    elif mean > 235:
        flags.append(f"{label}: görsel aşırı parlak/boş")
    edge_var = ImageStat.Stat(gray.resize((600, int(600 * gray.size[1] / gray.size[0]) or 1)).filter(ImageFilter.FIND_EDGES)).var[0]
    if edge_var < 30:
        flags.append(f"{label}: görsel bulanık veya boş olabilir")
    big = img.copy()
    big.thumbnail((2000, 2000))
    name = uuid.uuid4().hex + ".jpg"
    media_store.save_image(big, "kyc", name, "JPEG", quality=88, optimize=True)
    return {"name": name, "hash": _ahash(img), "flags": flags}


def kyc_duplicate_flags(uid, id_number, hashes):
    """Aynı görsel/kimlik başka hesapta kullanılmış mı? Yönetici için uyarı satırları döndürür."""
    flags = []
    others = q(
        "SELECT k.user_id, u.username, k.front_hash, k.back_hash, k.selfie_hash, k.id_number FROM kyc_requests k"
        " JOIN users u ON u.id = k.user_id WHERE k.user_id != ? ORDER BY k.id DESC LIMIT 5000",
        (uid,),
    )
    seen = set()
    for o in others:
        for slot, mine in (("Ön yüz", hashes["front"]), ("Arka yüz", hashes["back"]), ("Selfie", hashes["selfie"])):
            for theirs in (o["front_hash"], o["back_hash"], o["selfie_hash"]):
                if theirs and hamming(mine, theirs) <= 4 and (o["username"], slot) not in seen:
                    seen.add((o["username"], slot))
                    flags.append(f"{slot} görseli '{o['username']}' hesabındaki bir görselle neredeyse aynı")
    if hashes["selfie"] and (hamming(hashes["selfie"], hashes["front"]) <= 4 or hamming(hashes["selfie"], hashes["back"]) <= 4):
        flags.append("Selfie, kimlik görselinin aynısı gibi görünüyor")
    if hashes["front"] and hamming(hashes["front"], hashes["back"]) <= 4:
        flags.append("Ön ve arka yüz görselleri aynı görünüyor")
    return flags


# --------------------------------------------------------------------------- ilan formu (satıcı + admin ortak)
def read_listing_form():
    title = core.field("title", 90)
    description = core.field("description", 2000)
    price = core.to_kurus(request.form.get("price"))
    cat = q1("SELECT id FROM categories WHERE id = ? AND is_active = 1", (request.form.get("category_id", type=int),))
    if not 5 <= len(title) <= 90:
        raise BizError("Başlık 5-90 karakter olmalı.")
    if len(description) < 20:
        raise BizError("Açıklama en az 20 karakter olmalı; alıcıya kodun ne olduğunu ve nasıl kullanılacağını anlat.")
    if not cat:
        raise BizError("Geçerli bir kategori seç.")
    if price is None or not 100 <= price <= 10_000_000:
        raise BizError("Fiyat 1 ₺ ile 100.000 ₺ arasında olmalı.")
    old_raw = (request.form.get("old_price") or "").strip()
    old_price = 0
    if old_raw:
        old_price = core.to_kurus(old_raw)
        if old_price is None or old_price <= price or old_price > price * 5:
            raise BizError("Eski fiyat, güncel fiyattan yüksek (en fazla 5 katı) olmalı ya da boş bırakılmalı.")
    return {"title": title, "description": description, "price": price, "category_id": cat["id"], "old_price": old_price}


def read_phone():
    """İlan verirken zorunlu telefon numarası (yalnızca yönetime görünür)."""
    phone = core.field("phone", 20)
    digits = re.sub(r"\D", "", phone)
    if not re.fullmatch(r"[0-9+\s()-]{7,20}", phone) or not 10 <= len(digits) <= 13:
        raise BizError("Geçerli bir telefon numarası gir. Örn. 0532 000 00 00")
    return phone


def clean_message(text, maxlen=1000):
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:maxlen]


# --------------------------------------------------------------------------- banner / poster görselleri
def save_banner(storage):
    """Slider ve reklam şeridi görseli: en fazla 1920x900, WEBP."""
    opened = _open_image(storage, 6 * 1024 * 1024, 200)
    if not opened:
        return None
    img = _flatten(opened[0])
    img.thumbnail((1920, 900))
    name = uuid.uuid4().hex + ".webp"
    media_store.save_image(img, "cover", name, "WEBP", quality=84, method=4)
    return name


def save_poster(storage):
    """Günün oyunları kartı için dikey (3:4) görsel."""
    opened = _open_image(storage, 6 * 1024 * 1024, 200)
    if not opened:
        return None
    img = ImageOps.fit(_flatten(opened[0]), (720, 960), Image.LANCZOS)
    name = uuid.uuid4().hex + ".webp"
    media_store.save_image(img, "cover", name, "WEBP", quality=84, method=4)
    return name


# --------------------------------------------------------------------------- bildirimler
_OK_WORDS = ("onaylandı", "tamamlandı", "bakiyene geçti", "yeni satış", "yüklendi", "eklendi", "kazandın", "teslim", "yayına", "yeni yorum", "tebrik", "aktif", "başarılı", "alındı", "hazır")
_BAD_WORDS = ("reddedildi", "engellendi", "kaldırıldı", "iptal", "itiraz", "yasak", "başarısız", "iade", "kapatıldı", "silindi")
_WARN_WORDS = ("bekliyor", "uyarı", "yeni cihaz", "güvenlik", "süresi", "kilitlendi", "dikkat", "azaldı", "tükendi")


def notif_kind(title, body=""):
    """Başlıktan bildirim türünü çıkarır: ok (başarılı), bad (olumsuz), warn (dikkat), info."""
    t = (title or "").lower()
    if any(w in t for w in _BAD_WORDS):
        return "bad"
    if any(w in t for w in _WARN_WORDS):
        return "warn"
    if any(w in t for w in _OK_WORDS):
        return "ok"
    return "info"


def notify(uid, title, body="", link="", kind=""):
    """Kullanıcıya uygulama içi bildirim düşer (çağıran işlem içinde çalışır). kind boşsa başlıktan çıkarılır."""
    core.ex(
        "INSERT INTO notifications(user_id, title, body, link, kind) VALUES (?,?,?,?,?)",
        (uid, (title or "")[:120], (body or "")[:600], (link or "")[:200], kind or notif_kind(title, body)),
    )


# --------------------------------------------------------------------------- emanet (escrow)
def release_order(oid, by="alıcı"):
    """Emanetteki tutarı satıcının bakiyesine aktarır. tx() içinde çağır; ikinci kez çalışmaz."""
    cur = ex(
        "UPDATE orders SET escrow_status = 'released', released_at = datetime('now'),"
        " confirmed_at = CASE WHEN ? = 'alıcı' THEN datetime('now') ELSE confirmed_at END"
        " WHERE id = ? AND escrow_status IN ('held', 'disputed')",
        (by, oid),
    )
    if cur.rowcount != 1:
        return False
    o = q1("SELECT * FROM orders WHERE id = ?", (oid,))
    core.change_balance(o["seller_id"], o["seller_earning"], "sale", f"#{oid} {o['listing_title']} x{o['quantity']}", "order", oid)
    notify(o["seller_id"], "Ödeme bakiyene geçti", f"#{oid} numaralı siparişin tutarı ({core.fmt_money(o['seller_earning'])}) bakiyene aktarıldı.", f"/satici/satislar")
    return True


def refund_order(oid, note=""):
    """Emanetteki siparişi alıcıya iade eder (yönetici işlemi). tx() içinde çağır."""
    cur = ex(
        "UPDATE orders SET escrow_status = 'refunded', released_at = datetime('now') WHERE id = ? AND escrow_status IN ('held', 'disputed')",
        (oid,),
    )
    if cur.rowcount != 1:
        return False
    o = q1("SELECT * FROM orders WHERE id = ?", (oid,))
    back = o["total"] - o["discount"]
    core.change_balance(o["buyer_id"], back, "refund", f"#{oid} {o['listing_title']} iadesi", "order", oid)
    notify(o["buyer_id"], "Siparişin iade edildi", f"#{oid} için {core.fmt_money(back)} bakiyene eklendi. {note}".strip(), f"/siparis/{oid}")
    notify(o["seller_id"], "Sipariş iade edildi", f"#{oid} numaralı sipariş alıcıya iade edildi. {note}".strip(), "/satici/satislar")
    return True


_last_sweep = [0.0]


def release_due(force=False):
    """Süresi dolan emanetleri otomatik serbest bırakır (istek başına en fazla 30 sn'de bir çalışır)."""
    now = time.time()
    if not force and now - _last_sweep[0] < 30:
        return 0
    _last_sweep[0] = now
    try:
        import community
        community.sweep(force=True)               # süresi dolan çekilişleri çeker
    except Exception:                              # çekiliş hatası emanet işlemini aksatmasın
        pass
    due = q("SELECT id FROM orders WHERE escrow_status = 'held' AND release_at IS NOT NULL AND release_at <= datetime('now') LIMIT 100")
    n = 0
    for row in due:
        with core.tx():
            if release_order(row["id"], by="otomatik"):
                n += 1
    return n


def held_total(uid):
    return q1("SELECT COALESCE(SUM(seller_earning), 0) AS s, COUNT(*) AS n FROM orders WHERE seller_id = ? AND escrow_status IN ('held', 'disputed')", (uid,))


def mono(name):
    """Kategori kutuları için 1-2 harflik kısaltma: 'Discord Nitro & Boost' -> 'DN'."""
    words = [w for w in re.split(r"[^0-9A-Za-zÇĞİÖŞÜçğıöşü]+", name or "") if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


# --------------------------------------------------------------------------- kuponlar
def coupon_check(code, user_id, total, category_id):
    """Kupon geçerliyse (kupon_satırı, indirim_kuruş) döndürür; değilse kullanıcıya gösterilecek BizError fırlatır."""
    code = (code or "").strip()
    if not code:
        raise BizError("Kupon kodunu gir.")
    c = q1("SELECT * FROM coupons WHERE code = ? COLLATE NOCASE", (code,))
    if not c or not c["is_active"]:
        raise BizError("Kupon kodu geçersiz.")
    now = core.utc_str()
    if c["starts_at"] and now < c["starts_at"]:
        raise BizError("Bu kupon henüz kullanıma açılmadı.")
    if c["expires_at"] and now > c["expires_at"]:
        raise BizError("Bu kuponun süresi dolmuş.")
    if c["max_uses"] and c["used_count"] >= c["max_uses"]:
        raise BizError("Bu kuponun kullanım hakkı bitmiş.")
    if c["per_user"]:
        used = q1("SELECT COUNT(*) AS n FROM coupon_uses WHERE coupon_id = ? AND user_id = ?", (c["id"], user_id))["n"]
        if used >= c["per_user"]:
            raise BizError("Bu kuponu daha önce kullandın.")
    if c["category_id"] and c["category_id"] != category_id:
        cat = q1("SELECT name FROM categories WHERE id = ?", (c["category_id"],))
        raise BizError(f"Bu kupon yalnızca {cat['name'] if cat else 'belirli bir kategori'} ilanlarında geçerli.")
    if total < c["min_total"]:
        raise BizError(f"Bu kupon için sepet tutarı en az {core.fmt_money(c['min_total'])} olmalı.")
    if c["kind"] == "percent":
        discount = int(total * float(c["value"]) / 100)
    else:
        discount = int(c["value"])
    if c["max_discount"]:
        discount = min(discount, c["max_discount"])
    discount = min(discount, total - 100)  # en az 1 TL ödenir
    if discount <= 0:
        raise BizError("Bu tutarda indirim uygulanamıyor.")
    return c, discount

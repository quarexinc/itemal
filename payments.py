"""Ödeme yöntemleri: hazır şablonlar, kullanıcıya gösterilecek yöntem listesi (kısa süreli önbellekli) ve ortak yardımcılar.

Yönetim: admin.payments (/admin/odeme-yontemleri). Kullanıcı: app.balance (/bakiye).
Her yöntem: ad, tür (bank|crypto|other), ödeme bilgileri (satır satır, "Etiket: değer" biçimi kopyalama düğmesi alır),
talimat, minimum/maksimum tutar, yükleme bonusu (%), tahmini süre, simge, renk ve rozet metni.
"""
import re
import time

import core
from core import q

KINDS = {"bank": "Banka", "crypto": "Kripto", "other": "Diğer"}
KIND_ICON = {"bank": "store", "crypto": "cpu", "other": "wallet"}
ICONS = ("wallet", "store", "cpu", "credit-card", "send", "globe", "bolt", "zap", "gem", "gift", "receipt", "link")
MAX_BONUS = 20

# (anahtar, ad, tür, bilgiler, talimat, minimum TL, tahmini süre, simge, renk, rozet)
TEMPLATES = [
    ("havale", "Banka Havalesi / EFT", "bank",
     "Banka: (banka adı)\nHesap sahibi: (ad soyad)\nIBAN: TR00 0000 0000 0000 0000 0000 00",
     "Açıklama kısmına kullanıcı adını yaz. Gönderim sonrası formu doldur.", 50, "5-30 dk", "store", "#38bdf8", "Önerilen"),
    ("fast", "FAST / Anlık Havale", "bank",
     "Banka: (banka adı)\nHesap sahibi: (ad soyad)\nIBAN: TR00 0000 0000 0000 0000 0000 00",
     "FAST ile gönderirsen bakiyen dakikalar içinde eklenir. Açıklamaya kullanıcı adını yaz.", 50, "5-15 dk", "bolt", "#22c55e", "Hızlı"),
    ("papara", "Papara", "other",
     "Papara No: (numaranı buraya yaz)\nHesap sahibi: (ad soyad)",
     "Açıklamaya kullanıcı adını yaz. Dekont/işlem numarasını referans alanına yaz.", 20, "5-20 dk", "wallet", "#a855f7", ""),
    ("usdt", "Kripto (USDT - TRC20)", "crypto",
     "Ağ: TRON (TRC20)\nCüzdan adresi: (adresini buraya yaz)",
     "Yalnızca TRC20 ağını kullan. İşlem hash (TxID) bilgisini referans alanına yaz.", 50, "10-30 dk", "cpu", "#14b8a6", ""),
    ("btc", "Kripto (Bitcoin)", "crypto",
     "Ağ: Bitcoin\nCüzdan adresi: (adresini buraya yaz)",
     "Gönderim sonrası işlem hash (TxID) bilgisini referans alanına yaz. Ağ onayı gerekir.", 200, "30-60 dk", "cpu", "#f59e0b", ""),
    ("ininal", "Ininal / Dijital Cüzdan", "other",
     "Cüzdan: (ininal, Paycell, Tosla vb.)\nNumara: (numaranı buraya yaz)\nHesap sahibi: (ad soyad)",
     "Açıklamaya kullanıcı adını yaz. Dekont görüntüsündeki işlem numarasını referansa yaz.", 20, "10-30 dk", "credit-card", "#ec4899", ""),
]
BY_KEY = {t[0]: t for t in TEMPLATES}

_cache = {"t": 0.0, "rows": []}


def clean_color(value):
    v = (value or "").strip()
    return v if re.fullmatch(r"#[0-9a-fA-F]{6}", v) else ""


def clean_icon(value, kind):
    v = (value or "").strip()
    return v if v in ICONS else KIND_ICON.get(kind, "wallet")


def public_methods():
    """Aktif yöntemler (sayfa altlığı ve rozetler için), 60 sn önbellekli. Yalnızca görünür alanlar."""
    now = time.time()
    if now - _cache["t"] > 60:
        try:
            _cache["rows"] = [dict(r) for r in q("SELECT id, name, kind, icon, color FROM payment_methods WHERE is_active = 1 ORDER BY sort_order, id")]
        except Exception:
            _cache["rows"] = []
        _cache["t"] = now
    return _cache["rows"]


def reset_cache():
    _cache["t"] = 0.0


def bonus_for(amount, pct):
    """Yükleme bonusu (kuruş); yüzde 0-MAX_BONUS arasına kırpılır."""
    try:
        pct = max(0.0, min(float(pct or 0), float(MAX_BONUS)))
    except (TypeError, ValueError):
        return 0
    return core.pct_of(amount, str(pct)) if pct else 0


def method_stats():
    """Yöntem kimliğine göre onaylı/bekleyen yükleme özetleri."""
    rows = q(
        "SELECT method_id, SUM(status = 'approved') AS ok_n, COALESCE(SUM(CASE WHEN status = 'approved' THEN amount END), 0) AS ok_sum,"
        " SUM(status = 'pending') AS pend_n FROM deposits WHERE method_id IS NOT NULL GROUP BY method_id"
    )
    return {r["method_id"]: r for r in rows}

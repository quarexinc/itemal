"""SQLite katmanı: şema, bağlantı ve varsayılan veriler.

Tüm para değerleri kuruş cinsinden INTEGER olarak saklanır (10,50 TL = 1050).
Kullanıcı bilgileri bu veritabanında tutulur; admin bilgileri .env dosyasındadır.
"""
import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import hrana

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT NOT NULL,
    phone           TEXT NOT NULL DEFAULT '',
    avatar          TEXT NOT NULL DEFAULT '',
    balance         INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    is_banned       INTEGER NOT NULL DEFAULT 0,
    is_seller       INTEGER NOT NULL DEFAULT 0,
    kyc_status      TEXT NOT NULL DEFAULT 'none',
    store_name      TEXT NOT NULL DEFAULT '',
    store_desc      TEXT NOT NULL DEFAULT '',
    commission_rate REAL,                      -- NULL: kategori/genel oran geçerli, dolu: satıcıya özel oran (%)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT
);

CREATE TABLE IF NOT EXISTS user_badges (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, badge)
);

CREATE TABLE IF NOT EXISTS kyc_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doc_type    TEXT NOT NULL DEFAULT 'kimlik',       -- kimlik | ehliyet
    full_name   TEXT NOT NULL,
    id_number   TEXT NOT NULL,
    birth_date  TEXT NOT NULL,
    id_front    TEXT NOT NULL,
    id_back     TEXT NOT NULL,
    selfie      TEXT NOT NULL,
    front_hash  TEXT NOT NULL DEFAULT '',
    back_hash   TEXT NOT NULL DEFAULT '',
    selfie_hash TEXT NOT NULL DEFAULT '',
    flags       TEXT NOT NULL DEFAULT '',             -- otomatik uyarılar (satır satır)
    checklist   TEXT NOT NULL DEFAULT '',             -- yöneticinin işaretlediği kontroller
    status      TEXT NOT NULL DEFAULT 'pending',
    admin_note  TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS seller_applications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_name  TEXT NOT NULL,
    description TEXT NOT NULL,
    experience  TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'pending',
    admin_note  TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 1,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    commission_rate REAL                               -- NULL: genel oran
);

CREATE TABLE IF NOT EXISTS listings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id    INTEGER NOT NULL REFERENCES users(id),
    category_id  INTEGER NOT NULL REFERENCES categories(id),
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    cover        TEXT NOT NULL DEFAULT '',
    price        INTEGER NOT NULL CHECK (price > 0),
    status       TEXT NOT NULL DEFAULT 'active',      -- active | paused | blocked | removed
    is_featured  INTEGER NOT NULL DEFAULT 0,
    sales_count  INTEGER NOT NULL DEFAULT 0,
    views        INTEGER NOT NULL DEFAULT 0,
    rating_sum   INTEGER NOT NULL DEFAULT 0,
    rating_count INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status, category_id);
CREATE INDEX IF NOT EXISTS idx_listings_seller ON listings(seller_id);

CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id        INTEGER NOT NULL REFERENCES users(id),
    seller_id       INTEGER NOT NULL REFERENCES users(id),
    listing_id      INTEGER NOT NULL REFERENCES listings(id),
    listing_title   TEXT NOT NULL,
    unit_price      INTEGER NOT NULL,
    quantity        INTEGER NOT NULL,
    total           INTEGER NOT NULL,
    commission_rate REAL NOT NULL DEFAULT 0,
    commission      INTEGER NOT NULL,
    seller_earning  INTEGER NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_orders_buyer  ON orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_seller ON orders(seller_id);

CREATE TABLE IF NOT EXISTS listing_codes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    code       TEXT NOT NULL,
    is_sold    INTEGER NOT NULL DEFAULT 0,
    order_id   INTEGER REFERENCES orders(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_codes_stock ON listing_codes(listing_id, is_sold);
CREATE INDEX IF NOT EXISTS idx_codes_order ON listing_codes(order_id);

CREATE TABLE IF NOT EXISTS reviews (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER UNIQUE REFERENCES orders(id),           -- NULL: demo yorum
    listing_id   INTEGER NOT NULL REFERENCES listings(id),
    seller_id    INTEGER NOT NULL REFERENCES users(id),
    buyer_id     INTEGER NOT NULL REFERENCES users(id),
    rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment      TEXT NOT NULL DEFAULT '',
    seller_reply TEXT NOT NULL DEFAULT '',
    replied_at   TEXT,
    is_hidden    INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    is_demo      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_reviews_seller  ON reviews(seller_id, is_hidden);
CREATE INDEX IF NOT EXISTS idx_reviews_listing ON reviews(listing_id, is_hidden);

CREATE TABLE IF NOT EXISTS conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id      INTEGER NOT NULL REFERENCES listings(id),
    buyer_id        INTEGER NOT NULL REFERENCES users(id),
    seller_id       INTEGER NOT NULL REFERENCES users(id),
    is_locked       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_message_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (listing_id, buyer_id)
);
CREATE INDEX IF NOT EXISTS idx_conv_buyer  ON conversations(buyer_id, last_message_at);
CREATE INDEX IF NOT EXISTS idx_conv_seller ON conversations(seller_id, last_message_at);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id       INTEGER NOT NULL REFERENCES users(id),
    body            TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    read_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);

CREATE TABLE IF NOT EXISTS tickets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    subject       TEXT NOT NULL,
    category      TEXT NOT NULL DEFAULT 'diger',
    order_id      INTEGER REFERENCES orders(id),
    priority      TEXT NOT NULL DEFAULT 'normal',      -- normal | high | urgent
    status        TEXT NOT NULL DEFAULT 'open',        -- open | answered | closed
    last_reply_by TEXT NOT NULL DEFAULT 'user',        -- user | staff
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tickets_user   ON tickets(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status, updated_at);

CREATE TABLE IF NOT EXISTS ticket_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author      TEXT NOT NULL,                          -- user | staff
    user_id     INTEGER REFERENCES users(id),
    body        TEXT NOT NULL,
    is_internal INTEGER NOT NULL DEFAULT 0,             -- yalnızca yöneticiler görür
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tmsg_ticket ON ticket_messages(ticket_id, id);

CREATE TABLE IF NOT EXISTS api_keys (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    key_prefix   TEXT NOT NULL,
    key_hash     TEXT NOT NULL UNIQUE,
    is_active    INTEGER NOT NULL DEFAULT 1,
    last_used_at TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payment_methods (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    kind         TEXT NOT NULL DEFAULT 'bank',    -- bank | crypto | other
    details      TEXT NOT NULL DEFAULT '',
    instructions TEXT NOT NULL DEFAULT '',
    min_amount   INTEGER NOT NULL DEFAULT 0,
    is_active    INTEGER NOT NULL DEFAULT 0,
    sort_order   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS deposits (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    method_id    INTEGER REFERENCES payment_methods(id),
    method_name  TEXT NOT NULL,
    amount       INTEGER NOT NULL CHECK (amount > 0),
    reference    TEXT NOT NULL DEFAULT '',
    note         TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    admin_note   TEXT NOT NULL DEFAULT '',
    link_id      INTEGER,                           -- ödeme linkiyle yapılan yüklemede pay_links.id
    link_url     TEXT NOT NULL DEFAULT '',          -- kullanıcının gönderildiği ödeme linki (o anki hali)
    provider_ref TEXT UNIQUE,                       -- webhook ile gelen işlem no (tekrarı engeller)
    auto         INTEGER NOT NULL DEFAULT 0,        -- 1: webhook ile otomatik onaylandı
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at  TEXT
);

CREATE TABLE IF NOT EXISTS withdrawals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    amount       INTEGER NOT NULL CHECK (amount > 0),
    fee          INTEGER NOT NULL DEFAULT 0,
    net          INTEGER NOT NULL,
    method       TEXT NOT NULL,
    account_info TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending', -- pending | approved | rejected
    admin_note   TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at  TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    kind          TEXT NOT NULL,
    amount        INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    ref_type      TEXT,
    ref_id        INTEGER,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id, id);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS admin_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    action     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    ip         TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Para ayarları TL cinsinden metin olarak tutulur.
DEFAULT_SETTINGS = {
    "site_name": "itemal",
    "site_tagline": "Güvenli e-pin ve dijital kod pazaryeri",
    "support_email": "destek@example.com",
    "announcement": "",
    "giveaway_enabled": "1",            # 1: satıcılar çekiliş açabilir
    "demo_sales": "1",                  # 1: örnek (demo) ilanlar satın alınabilir; stokları kendiliğinden yenilenir
    "commission_percent": "5",          # genel platform komisyonu (%); kategori/satıcı oranı varsa o geçerli
    "withdraw_fee_percent": "2",        # çekim kesintisi (%)
    "fee_store_name": "200",            # TL: mağaza adı değişikliği ücreti (ilk belirleme ücretsiz)
    "fee_store_slug": "300",            # TL: mağaza adresi değişikliği ücreti (ilk belirleme ücretsiz)
    "min_withdraw": "100",              # TL
    "min_deposit": "20",                # TL
    "max_qty_per_order": "10",
    "require_seller_approval": "1",     # 1: ilan vermek için onaylı satıcı olmak gerekir
    "withdraw_only_earnings": "1",      # 1: yalnızca satış kazancı çekilebilir (yüklenen bakiye çekilemez)
    "require_cover": "1",               # 1: yeni ilanda kapak görseli zorunlu
    "trusted_min_sales": "25",          # "Güvenilir Satıcı" rozeti için asgari satış adedi
    "trusted_min_rating": "4.5",        # ... ve asgari ortalama puan (en az 5 yorumla)
    "maintenance_mode": "0",            # 1: site bakımda (yönetici hariç kimse giremez)
    "allow_registration": "1",          # 0: yeni üyelik kapalı
    "require_seller_2fa": "0",          # 1: satıcı paneline iki adımlı doğrulamasız girilemez
    "home_ticker": "1",                 # ana sayfada canlı satış bandı
    "meta_description": "itemal: oyun kodları, hediye kartları ve dijital abonelikler için güvenli pazaryeri.",
    "social_discord": "",
    "social_telegram": "",
    "social_instagram": "",
    "support_hours": "Her gün 10:00 - 24:00",
    "escrow_days": "3",                 # alıcı onaylamazsa tutar bu kadar gün sonra satıcıya aktarılır
    "doping_max_banners": "8",          # ana sayfada aynı anda yayınlanabilecek satın alınmış reklam banner'ı sayısı
    "hero_seconds": "6",                # slider geçiş süresi (sn)
}

# (ad, slug, grup, renk, kısa açıklama, günün oyunu mu)
CATEGORY_SEED = [
    ("Discord Nitro & Boost", "discord", "Uygulama & Abonelik", "#5865F2", "Nitro, Nitro Basic ve sunucu boost kodları", 1),
    ("Steam Cüzdan Kodu", "steam", "PC & Konsol", "#1b9bd7", "TL ve USD cüzdan kodları", 1),
    ("Roblox Robux", "roblox", "PC & Konsol", "#e2231a", "Robux ve Roblox hediye kartları", 1),
    ("Valorant VP", "valorant-vp", "PC & Konsol", "#ff4655", "Valorant Points hediye kodları", 1),
    ("PUBG Mobile UC", "pubg-uc", "Mobil", "#eab308", "PUBG Mobile UC paketleri", 1),
    ("Fortnite V-Bucks", "fortnite", "PC & Konsol", "#8a5cff", "V-Bucks ve Fortnite kartları", 1),
    ("Free Fire Elmas", "free-fire", "Mobil", "#ff7a00", "Free Fire elmas paketleri", 0),
    ("Mobile Legends", "mobile-legends", "Mobil", "#38bdf8", "Diamond paketleri", 0),
    ("Genshin Impact", "genshin", "Mobil", "#5ec8f2", "Genesis Crystal paketleri", 0),
    ("Minecraft", "minecraft", "PC & Konsol", "#62b47a", "Minecraft hesap ve Minecoin kodları", 0),
    ("Riot Points (LoL)", "riot-points", "PC & Konsol", "#c89b3c", "League of Legends RP kodları", 0),
    ("Epic Games", "epic-games", "PC & Konsol", "#a1a1aa", "Epic Games cüzdan ve oyun kodları", 0),
    ("Battle.net / Blizzard", "battlenet", "PC & Konsol", "#148eff", "Blizzard bakiye ve oyun kodları", 0),
    ("EA FC Points", "ea-fc", "PC & Konsol", "#22c55e", "EA FC Points ve EA Play", 0),
    ("Xbox / PlayStation", "xbox-ps", "PC & Konsol", "#0e7cd6", "Xbox Game Pass ve PSN kartları", 0),
    ("Nintendo eShop", "nintendo", "PC & Konsol", "#e60012", "Nintendo eShop kartları", 0),
    ("Netflix", "netflix", "Uygulama & Abonelik", "#e50914", "Netflix hediye kartları", 0),
    ("Spotify", "spotify", "Uygulama & Abonelik", "#1db954", "Spotify Premium kodları", 0),
    ("Google Play Kartı", "google-play", "Hediye Kartları", "#34a853", "Google Play hediye kartları", 0),
    ("App Store & iTunes", "app-store", "Hediye Kartları", "#60a5fa", "Apple hediye kartları", 0),
]

BANNER_SEED = [
    # slot, başlık, alt başlık, buton, bağlantı, renk1, renk2, sıra
    ("hero", "Discord Nitro ve Boost kodları", "Sunucunu güçlendir. Ödeme sonrası kod saniyeler içinde sipariş sayfanda.", "Discord ilanları", "/ilanlar?kategori=discord", "#5865F2", "#1e2170", 0),
    ("hero", "Steam cüzdan kodları", "Oyun kütüphaneni büyüt. Emanet korumalı güvenli alışveriş.", "Steam ilanları", "/ilanlar?kategori=steam", "#1b9bd7", "#0a2540", 1),
    ("hero", "Satıcı ol, satışa başla", "İlanını yayınla, satışlarını takip et, kazancını IBAN veya Papara ile çek.", "Satıcı başvurusu", "/satici-basvuru", "#7c5cff", "#1b1140", 2),
    ("strip", "Puanlı ve rozetli satıcılar", "Rozetli satıcıları tercih et; her satış sonrası yorumlarla puanlanır.", "Satıcıları gör", "/ilanlar?sirala=puan", "#0f766e", "#052e2b", 0),
    ("strip", "Sorun mu yaşadın?", "Destek talebi aç, ekibimiz siparişini inceleyip dönüş yapsın.", "Destek talebi", "/destek/yeni", "#b45309", "#3b1d04", 1),
]

# Sahte IBAN'a para yatırılmasın diye başlangıçta PASİF gelir; admin panelinden düzenleyip aç.
DEFAULT_PAYMENT_METHODS = [
    ("Banka Havalesi / EFT", "bank",
     "Banka: (banka adı)\nHesap sahibi: (ad soyad)\nIBAN: TR00 0000 0000 0000 0000 0000 00",
     "Açıklama kısmına kullanıcı adını yaz. Gönderim sonrası aşağıdaki formu doldur.", 5000),
    ("Kripto (USDT - TRC20)", "crypto",
     "Ağ: TRON (TRC20)\nCüzdan adresi: (adresini buraya yaz)",
     "Yalnızca TRC20 ağını kullan. İşlem hash (TxID) bilgisini referans alanına yaz.", 5000),
    ("Papara", "other",
     "Papara No: (numaranı buraya yaz)",
     "Açıklamaya kullanıcı adını yaz. Dekont/işlem numarasını referans alanına yaz.", 2000),
]


def remote():
    """TURSO_DATABASE_URL tanımlıysa veritabanı uzaktadır (Vercel); değilse yerel SQLite dosyası."""
    return bool(hrana.configured())


def connect(path=None):
    """Otomatik commit modunda bağlantı; işlemler tx() ile açıkça yönetilir."""
    if remote():
        return hrana.connect()
    conn = sqlite3.connect(str(path), isolation_level=None, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def tx(conn):
    """Yazma kilidini baştan alan atomik işlem (satın alma/para hareketleri için)."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


SCHEMA2 = """
CREATE TABLE IF NOT EXISTS banners (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slot       TEXT NOT NULL DEFAULT 'hero',          -- hero | strip
    title      TEXT NOT NULL,
    subtitle   TEXT NOT NULL DEFAULT '',
    cta_text   TEXT NOT NULL DEFAULT '',
    link       TEXT NOT NULL DEFAULT '',
    image      TEXT NOT NULL DEFAULT '',
    color1     TEXT NOT NULL DEFAULT '#7c5cff',
    color2     TEXT NOT NULL DEFAULT '#1b1140',
    is_active  INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    starts_at  TEXT,
    ends_at    TEXT,
    views      INTEGER NOT NULL DEFAULT 0,
    clicks     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_ad      INTEGER NOT NULL DEFAULT 0,            -- 1: doping ile satın alınan reklam banner'ı
    listing_id INTEGER                                -- reklam banner'ının ilanı
);

CREATE TABLE IF NOT EXISTS coupons (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    kind         TEXT NOT NULL DEFAULT 'percent',     -- percent | fixed
    value        REAL NOT NULL,                       -- percent: yüzde, fixed: kuruş
    min_total    INTEGER NOT NULL DEFAULT 0,
    max_discount INTEGER NOT NULL DEFAULT 0,          -- percent için üst sınır (kuruş), 0: sınırsız
    max_uses     INTEGER NOT NULL DEFAULT 0,          -- 0: sınırsız
    used_count   INTEGER NOT NULL DEFAULT 0,
    per_user     INTEGER NOT NULL DEFAULT 1,
    category_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    starts_at    TEXT,
    expires_at   TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS coupon_uses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    coupon_id  INTEGER NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    order_id   INTEGER REFERENCES orders(id),
    amount     INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cuse ON coupon_uses(coupon_id, user_id);

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL DEFAULT '',
    link       TEXT NOT NULL DEFAULT '',
    is_read    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, is_read, id);

CREATE TABLE IF NOT EXISTS favorites (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, listing_id)
);

CREATE TABLE IF NOT EXISTS login_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip         TEXT NOT NULL DEFAULT '',
    agent      TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_user ON login_events(user_id, id);

-- Başarısız giriş özetleri (ham kullanıcı adı yazılmaz: security.mask_ident; user_id yalnızca hesap eşleştiyse dolu)
CREATE TABLE IF NOT EXISTS login_failures (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    ident      TEXT NOT NULL DEFAULT '',
    ip         TEXT NOT NULL DEFAULT '',
    agent      TEXT NOT NULL DEFAULT '',
    reason     TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_fail_user ON login_failures(user_id, id);
CREATE INDEX IF NOT EXISTS idx_login_fail_ip ON login_failures(ip, id);

CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,                       -- listing | user | order
    target_id   INTEGER NOT NULL,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason      TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'open',        -- open | resolved | dismissed
    admin_note  TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status, id);
CREATE INDEX IF NOT EXISTS idx_reports_target ON reports(kind, target_id);

CREATE TABLE IF NOT EXISTS seller_comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    author_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    is_hidden  INTEGER NOT NULL DEFAULT 0,
    is_demo    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (seller_id, author_id)
);
CREATE INDEX IF NOT EXISTS idx_scomments ON seller_comments(seller_id, is_hidden, id);

-- Hız sınırı sayaçları (giriş, kayıt, yükleme, yazma istekleri...)
CREATE TABLE IF NOT EXISTS rate_hits (
    scope TEXT NOT NULL,
    key   TEXT NOT NULL,
    ts    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rate_hits ON rate_hits(scope, key, ts);

CREATE INDEX IF NOT EXISTS idx_users_regip ON users(reg_ip);
CREATE INDEX IF NOT EXISTS idx_listings_deal ON listings(is_deal, status);
"""

# (tablo, sütun, tanım) - eski veritabanlarını da yükseltmek için idempotent
COLUMN_MIGRATIONS = [
    ("users", "reg_ip", "TEXT NOT NULL DEFAULT ''"),
    ("users", "last_ip", "TEXT NOT NULL DEFAULT ''"),
    ("users", "admin_note", "TEXT NOT NULL DEFAULT ''"),
    ("users", "is_demo", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "demo_sold", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "store_banner", "TEXT NOT NULL DEFAULT ''"),
    ("users", "sess_ver", "INTEGER NOT NULL DEFAULT 0"),           # artınca tüm eski oturumlar düşer ("tüm cihazlardan çıkış")
    ("users", "totp_secret", "TEXT NOT NULL DEFAULT ''"),           # iki adımlı doğrulama anahtarı (security.encrypt_secret ile şifreli)
    ("users", "totp_last_step", "INTEGER NOT NULL DEFAULT 0"),      # son kabul edilen TOTP adımı (aynı kodun yeniden kullanımı reddedilir)
    ("users", "totp_backup", "TEXT NOT NULL DEFAULT ''"),           # yedek kod hash'leri (JSON liste)
    ("users", "store_slug", "TEXT NOT NULL DEFAULT ''"),             # özel mağaza adresi: alanadi/<slug>
    ("users", "slug_changed_at", "TEXT"),
    ("payment_methods", "max_amount", "INTEGER NOT NULL DEFAULT 0"),   # 0: üst sınır yok
    ("payment_methods", "bonus_percent", "REAL NOT NULL DEFAULT 0"),    # yükleme bonusu (%)
    ("payment_methods", "eta", "TEXT NOT NULL DEFAULT ''"),             # tahmini süre metni (örn. 5-30 dk)
    ("payment_methods", "icon", "TEXT NOT NULL DEFAULT ''"),
    ("payment_methods", "color", "TEXT NOT NULL DEFAULT ''"),
    ("payment_methods", "badge", "TEXT NOT NULL DEFAULT ''"),           # kısa rozet (Önerilen, Hızlı...)
    ("deposits", "bonus", "INTEGER NOT NULL DEFAULT 0"),                # onayda bakiyeye ayrıca eklenecek bonus (kuruş)
    ("store_packages", "giveaway_slots", "INTEGER NOT NULL DEFAULT 0"),
    ("store_packages", "theme_unlock", "INTEGER NOT NULL DEFAULT 0"),
    ("store_packages", "priority_support", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "store_theme", "TEXT NOT NULL DEFAULT ''"),            # vitrin tema rengi (storeplus.THEMES anahtarı)
    ("users", "store_notice", "TEXT NOT NULL DEFAULT ''"),           # mağaza sayfası duyuru çubuğu
    ("users", "store_discord", "TEXT NOT NULL DEFAULT ''"),
    ("users", "store_telegram", "TEXT NOT NULL DEFAULT ''"),
    ("users", "store_instagram", "TEXT NOT NULL DEFAULT ''"),
    ("users", "store_web", "TEXT NOT NULL DEFAULT ''"),
    ("users", "store_vacation", "INTEGER NOT NULL DEFAULT 0"),       # 1: tatil modu (yeni sipariş alınmaz)
    ("users", "vacation_until", "TEXT"),                             # dolu ve geçmişse tatil kendiliğinden biter (UTC)
    ("users", "auto_reply", "TEXT NOT NULL DEFAULT ''"),             # yeni konuşmaya otomatik karşılama mesajı
    ("users", "sales_goal", "INTEGER NOT NULL DEFAULT 0"),           # aylık net kazanç hedefi (kuruş)
    ("users", "store_views", "INTEGER NOT NULL DEFAULT 0"),
    ("notifications", "kind", "TEXT NOT NULL DEFAULT ''"),           # ok | warn | bad | info (bildirim detayında durum rozeti)
    ("reviews", "is_demo", "INTEGER NOT NULL DEFAULT 0"),
    ("categories", "grp", "TEXT NOT NULL DEFAULT ''"),
    ("categories", "color", "TEXT NOT NULL DEFAULT ''"),
    ("categories", "tagline", "TEXT NOT NULL DEFAULT ''"),
    ("categories", "image", "TEXT NOT NULL DEFAULT ''"),
    ("categories", "is_daily", "INTEGER NOT NULL DEFAULT 0"),
    ("listings", "old_price", "INTEGER NOT NULL DEFAULT 0"),
    ("listings", "is_deal", "INTEGER NOT NULL DEFAULT 0"),
    ("listings", "is_demo", "INTEGER NOT NULL DEFAULT 0"),
    ("orders", "discount", "INTEGER NOT NULL DEFAULT 0"),
    ("deposits", "link_id", "INTEGER"),
    ("deposits", "link_url", "TEXT NOT NULL DEFAULT ''"),
    ("orders", "escrow_status", "TEXT NOT NULL DEFAULT 'released'"),   # held | released | disputed | refunded (eski siparişler serbest)
    ("orders", "release_at", "TEXT"),
    ("orders", "confirmed_at", "TEXT"),
    ("orders", "released_at", "TEXT"),
    ("orders", "coupon_code", "TEXT NOT NULL DEFAULT ''"),
    ("banners", "is_ad", "INTEGER NOT NULL DEFAULT 0"),
    ("banners", "listing_id", "INTEGER"),
]


REVIEWS_REBUILD = """
CREATE TABLE reviews_new (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER UNIQUE REFERENCES orders(id),
    listing_id   INTEGER NOT NULL REFERENCES listings(id),
    seller_id    INTEGER NOT NULL REFERENCES users(id),
    buyer_id     INTEGER NOT NULL REFERENCES users(id),
    rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment      TEXT NOT NULL DEFAULT '',
    seller_reply TEXT NOT NULL DEFAULT '',
    replied_at   TEXT,
    is_hidden    INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    is_demo      INTEGER NOT NULL DEFAULT 0
);
INSERT INTO reviews_new(id, order_id, listing_id, seller_id, buyer_id, rating, comment, seller_reply, replied_at, is_hidden, created_at)
    SELECT id, order_id, listing_id, seller_id, buyer_id, rating, comment, seller_reply, replied_at, is_hidden, created_at FROM reviews;
DROP TABLE reviews;
ALTER TABLE reviews_new RENAME TO reviews;
CREATE INDEX IF NOT EXISTS idx_reviews_seller  ON reviews(seller_id, is_hidden);
CREATE INDEX IF NOT EXISTS idx_reviews_listing ON reviews(listing_id, is_hidden);
"""


def _migrate(conn):
    # eski veritabanlarında reviews.order_id NOT NULL idi; demo yorumlar için boş olabilmeli
    info = {r["name"]: r for r in conn.execute("PRAGMA table_info(reviews)")}
    if info and info["order_id"]["notnull"]:
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.execute("BEGIN IMMEDIATE")
            for stmt in [x for x in REVIEWS_REBUILD.split(";\n") if x.strip()]:
                conn.execute(stmt)
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
    for table, col, ddl in COLUMN_MIGRATIONS:
        have = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        if have and col not in have:       # tablo henüz yoksa SCHEMA2 sütunlarıyla birlikte oluşturur
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")


def _flag(conn, key):
    """Tohumlama bayrağı: True dönerse bu tohum daha önce uygulanmamıştır (ve şimdi işaretlenir)."""
    if conn.execute("SELECT 1 FROM settings WHERE key = ?", (key,)).fetchone():
        return False
    conn.execute("INSERT INTO settings(key, value) VALUES (?, '1')", (key,))
    return True


SCHEMA3 = """
-- Yönetici girişi olayları (başarılı/başarısız giriş, kod denemeleri); kullanıcı adı ham yazılmaz (security.mask_ident)
CREATE TABLE IF NOT EXISTS admin_login_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    ip         TEXT NOT NULL DEFAULT '',
    ua         TEXT NOT NULL DEFAULT '',
    ua_hash    TEXT NOT NULL DEFAULT '',
    ident      TEXT NOT NULL DEFAULT '',
    result     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_admin_events ON admin_login_events(result, id);

-- Yönetimin tanımladığı ödeme linkleri (dış ödeme sayfaları): başlık + link + sabit fiyat
CREATE TABLE IF NOT EXISTS pay_links (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    url         TEXT NOT NULL,
    amount      INTEGER NOT NULL CHECK (amount > 0),   -- kuruş: ödeme onaylanınca bakiyeye eklenecek tutar
    is_active   INTEGER NOT NULL DEFAULT 1,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS media (
    kind       TEXT NOT NULL,                  -- cover | avatar | kyc
    name       TEXT NOT NULL,
    mime       TEXT NOT NULL,
    size       INTEGER NOT NULL DEFAULT 0,
    data       BLOB NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (kind, name)
);
"""

# Doping (ilan öne çıkarma): fiyat tablosu (kuruş) ve satın alınan dopingler.
# kind: market (Pazar vitrini) | category (Vitrin ürün / kategori vitrini) | banner (ana sayfa reklam banner'ı)
# Aynı ilan+tür için art arda alınan dopingler zincirlenir (yeni satırın starts_at'i öncekinin ends_at'idir).
SCHEMA_DOPING = """
CREATE TABLE IF NOT EXISTS doping_prices (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    kind      TEXT NOT NULL,
    hours     INTEGER NOT NULL,
    price     INTEGER NOT NULL,                  -- kuruş
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (kind, hours)
);

CREATE TABLE IF NOT EXISTS listing_dopings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    seller_id  INTEGER NOT NULL,
    kind       TEXT NOT NULL,
    hours      INTEGER NOT NULL,
    price      INTEGER NOT NULL,                 -- kuruş (satın alma anındaki fiyat)
    starts_at  TEXT NOT NULL,
    ends_at    TEXT NOT NULL,
    banner_id  INTEGER,
    req_key    TEXT UNIQUE,                      -- çift istek koruması (form başına tek kullanımlık anahtar)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_doping_active ON listing_dopings(kind, ends_at, starts_at);
CREATE INDEX IF NOT EXISTS idx_doping_listing ON listing_dopings(listing_id, kind, ends_at);
CREATE INDEX IF NOT EXISTS idx_doping_seller ON listing_dopings(seller_id, id);
CREATE INDEX IF NOT EXISTS idx_doping_banner ON listing_dopings(banner_id);
"""

# (tür, saat, fiyat kuruş)
DOPING_SEED = [
    ("market", 12, 1000), ("market", 24, 2000), ("market", 48, 4000), ("market", 168, 10000),
    ("category", 12, 2500), ("category", 24, 4500), ("category", 48, 5000), ("category", 168, 15000),
    ("banner", 12, 10000), ("banner", 24, 12000), ("banner", 48, 20000), ("banner", 168, 50000),
]

# Mağaza paketleri (mavi tik, altın/elmas mağaza, öne çıkan mağaza, düşük komisyon, hızlı teslimat rozeti)
SCHEMA_PKG = """
CREATE TABLE IF NOT EXISTS store_packages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    tagline             TEXT NOT NULL DEFAULT '',
    description         TEXT NOT NULL DEFAULT '',
    price               INTEGER NOT NULL DEFAULT 0,          -- kuruş
    duration_days       INTEGER NOT NULL DEFAULT 0,          -- 0: kalıcı
    is_active           INTEGER NOT NULL DEFAULT 1,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    icon                TEXT NOT NULL DEFAULT 'zap',
    color               TEXT NOT NULL DEFAULT '#7c5cff',
    tick                INTEGER NOT NULL DEFAULT 0,          -- mavi tik verir
    tier                TEXT NOT NULL DEFAULT '',            -- '' | gold | diamond
    featured            INTEGER NOT NULL DEFAULT 0,          -- mağazalar sayfasında öne çıkar
    commission_discount REAL NOT NULL DEFAULT 0,             -- komisyondan düşülen puan
    fast_badge          INTEGER NOT NULL DEFAULT 0,          -- "Hızlı Teslimat" rozeti
    giveaway_slots      INTEGER NOT NULL DEFAULT 0,          -- aynı anda açılabilecek ek çekiliş hakkı
    theme_unlock        INTEGER NOT NULL DEFAULT 0,          -- tüm vitrin temalarının kilidini açar
    priority_support    INTEGER NOT NULL DEFAULT 0,          -- destek talepleri öncelikli işlenir
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Her satın alma/tanımlama bir satır; aynı paket tekrar alınırsa yeni satır mevcut bitişten başlar (süre uzar).
CREATE TABLE IF NOT EXISTS user_packages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    package_id INTEGER NOT NULL REFERENCES store_packages(id),
    price      INTEGER NOT NULL DEFAULT 0,
    source     TEXT NOT NULL DEFAULT 'buy',                  -- buy | admin
    starts_at  TEXT NOT NULL,
    ends_at    TEXT,                                         -- NULL: kalıcı
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_up_user ON user_packages(user_id, ends_at);
CREATE INDEX IF NOT EXISTS idx_up_pkg ON user_packages(package_id);
"""

# (kod, ad, kısa açıklama, açıklama, fiyat kuruş, süre gün, sıra, simge, renk, tik, kademe, öne çıkan, komisyon indirimi, hızlı rozet,
#  ek çekiliş hakkı, tema kilidi, öncelikli destek)
PACKAGE_SEED = [
    ("mavi_tik", "Mavi Tik", "Mağaza adının yanında doğrulanmış mavi tik",
     "Alıcılar mavi tikli mağazalara daha çok güvenir: mavi tik, doğrulanmış mağaza demektir.", 25000, 0, 0, "vtick", "#1d9bf0", 1, "", 0, 0, 0, 0, 0, 0),
    ("altin_magaza", "Altın Mağaza", "Altın rozet, altın çerçeve ve liste önceliği",
     "Öne çıkmak isteyen mağazalar için: listede ve mağaza sayfanda dikkat çeker.", 40000, 30, 1, "vgold", "#f5b301", 0, "gold", 0, 0, 0, 0, 0, 0),
    ("elmas_magaza", "Elmas Mağaza", "Tüm ayrıcalıklar tek pakette",
     "Mağazanın en üst kademesi: elmas rozet ve animasyonlu çerçeve, mavi tik, öne çıkan yerleşim, komisyon indirimi, 7 ek çekiliş hakkı, tüm vitrin temaları ve öncelikli destek.", 90000, 30, 2, "vdiamond", "#6d8bff", 1, "diamond", 1, 1, 0, 7, 1, 1),
    ("one_cikan", "Öne Çıkan Mağaza", "Mağazalar sayfasında en üstte yer al",
     "Yeni kampanya ya da stok girişi sonrasında kısa süreli görünürlük için ideal.", 15000, 7, 3, "flame", "#f97316", 0, "", 1, 0, 0, 0, 0, 0),
    ("dusuk_komisyon", "Düşük Komisyon", "Komisyon oranın 1,5 puan düşer",
     "Paket süresince tüm satışlarında geçerlidir. Oran sıfırın altına inmez; mevcut siparişlerin komisyonu değişmez.", 30000, 30, 4, "percent", "#22c55e", 0, "", 0, 1.5, 0, 0, 0, 0),
    ("hizli_teslimat", "Hızlı Teslimat Rozeti", "Alıcılara hızlı teslimat güvencesi",
     "Kodları hızlı teslim ettiğini gösteren rozet; mağaza sayfanda ve rozet listesinde görünür.", 10000, 30, 5, "bolt", "#06b6d4", 0, "", 0, 0, 1, 0, 0, 0),
    ("cekilis_paketi", "Çekiliş Paketi", "7 ek çekiliş hakkı: aynı anda daha çok çekiliş aç",
     "Takipçilerini ve müşterilerini büyütmek için aynı anda 7 ek çekiliş açabilirsin (standart hak 3). Paket süresince geçerlidir.", 20000, 30, 6, "gift", "#ec4899", 0, "", 0, 0, 0, 7, 0, 0),
    ("premium_vitrin", "Premium Vitrin", "Tüm vitrin temaları ve özel renk seçenekleri",
     "Mağaza sayfanın rengini 9 temadan dilediğinle değiştir. Paket bitince tema varsayılana döner, seçimin saklanır.", 15000, 30, 7, "palette", "#a855f7", 0, "", 0, 0, 0, 0, 1, 0),
    ("oncelikli_destek", "Öncelikli Destek", "Destek taleplerin yönetimde öne alınır",
     "Açtığın tüm destek talepleri otomatik olarak yüksek öncelikle açılır ve ekibimiz tarafından önce görülür.", 12000, 30, 8, "life-buoy", "#14b8a6", 0, "", 0, 0, 0, 0, 0, 1),
]


# Mağaza+: özel mağaza adresi (benzersiz, büyük/küçük harf duyarsız) ve eski adres yönlendirmeleri.
SCHEMA_PLUS = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_slug ON users(store_slug COLLATE NOCASE) WHERE store_slug <> '';
CREATE TABLE IF NOT EXISTS store_slug_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug       TEXT NOT NULL COLLATE NOCASE,
    changed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_slug_hist ON store_slug_history(slug);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);

-- Satıcı takibi
CREATE TABLE IF NOT EXISTS seller_follows (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seller_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, seller_id)
);
CREATE INDEX IF NOT EXISTS idx_follow_seller ON seller_follows(seller_id, created_at);

-- Çekilişler (satıcı açar, katılımcılar katılır, süre dolunca ya da satıcı isteyince kura çekilir)
CREATE TABLE IF NOT EXISTS giveaways (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    prize         TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    winners       INTEGER NOT NULL DEFAULT 1,
    ends_at       TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open',          -- open | drawn | cancelled
    need_follow   INTEGER NOT NULL DEFAULT 0,
    need_purchase INTEGER NOT NULL DEFAULT 0,
    entry_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    drawn_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_gw_status ON giveaways(status, ends_at);
CREATE INDEX IF NOT EXISTS idx_gw_seller ON giveaways(seller_id, status);
CREATE TABLE IF NOT EXISTS giveaway_entries (
    giveaway_id INTEGER NOT NULL REFERENCES giveaways(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_winner   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (giveaway_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_gwe_user ON giveaway_entries(user_id);
"""


# Kod tarafındaki tohum/göç adımları değişince artırılır; şema metniyle birlikte sürüm damgasını belirler.
INIT_REVISION = 3


def schema_version():
    return hashlib.sha256((SCHEMA + SCHEMA2 + SCHEMA3 + SCHEMA_PKG + SCHEMA_DOPING + SCHEMA_PLUS + str(INIT_REVISION) + repr(COLUMN_MIGRATIONS)).encode("utf-8")).hexdigest()[:16]


def ensure_ready(path=None):
    """Şema güncel değilse (ya da ilk kurulumda) init_db çalıştırır. Güncelse tek bir sorgu yapar.

    Soğuk başlangıçta uzak veritabanına gereksiz gidiş-dönüş yapmamak için sürüm damgası settings tablosunda tutulur.
    """
    want = schema_version()
    conn = connect(path)
    try:
        try:
            row = conn.execute("SELECT value FROM settings WHERE key = 'schema_version'").fetchone()
        except sqlite3.Error:
            row = None
        if row and row[0] == want:
            return False
    finally:
        conn.close()
    init_db(path)
    conn = connect(path)
    try:
        conn.execute("INSERT INTO settings(key, value) VALUES ('schema_version', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (want,))
    finally:
        conn.close()
    return True


def init_db(path=None):
    if not remote():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.executescript(SCHEMA2)
        conn.executescript(SCHEMA3)
        conn.executescript(SCHEMA_PKG)
        conn.executescript(SCHEMA_DOPING)
        conn.executescript(SCHEMA_PLUS)
        for kind, hours, price in DOPING_SEED:     # doping fiyatları: yoksa ekler (yönetimin düzenlemeleri korunur)
            conn.execute("INSERT OR IGNORE INTO doping_prices(kind, hours, price) VALUES (?,?,?)", (kind, hours, price))
        for row in PACKAGE_SEED:                   # mağaza paketleri: yoksa ekler (yönetimin düzenlemeleri korunur)
            conn.execute(
                "INSERT OR IGNORE INTO store_packages(code, name, tagline, description, price, duration_days, sort_order,"
                " icon, color, tick, tier, featured, commission_discount, fast_badge, giveaway_slots, theme_unlock, priority_support)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                row,
            )
        if _flag(conn, "pkg_elmas_v2"):             # mevcut Elmas paketini yeni ayrıcalıklarla yükselt (düzenlenmiş fiyat korunur)
            conn.execute(
                "UPDATE store_packages SET giveaway_slots = 7, theme_unlock = 1, priority_support = 1, description = ? WHERE code = 'elmas_magaza'",
                (PACKAGE_SEED[2][3],),
            )
        # Kartla ödeme kaldırıldı: eski veritabanlarında açık kalan kart ödemelerini kapat (bakiye eklenmez)
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='card_payments'").fetchone():
            conn.execute(
                "UPDATE card_payments SET status = 'rejected', admin_note = 'Kartla ödeme yöntemi kaldırıldı', reviewed_at = datetime('now')"
                " WHERE status IN ('awaiting', 'pending')"
            )
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))
        if _flag(conn, "seed_categories_v3"):
            for i, (name, slug, grp, color, tagline, daily) in enumerate(CATEGORY_SEED):
                row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
                if row is None:
                    conn.execute(
                        "INSERT INTO categories(name, slug, sort_order, grp, color, tagline, is_daily) VALUES (?,?,?,?,?,?,?)",
                        (name, slug, i, grp, color, tagline, daily),
                    )
                else:
                    conn.execute(
                        "UPDATE categories SET sort_order = ?, grp = ?, color = ?, tagline = ?, is_daily = ? WHERE id = ?",
                        (i, grp, color, tagline, daily, row["id"]),
                    )
        if _flag(conn, "trim_categories_v1"):
            keep = {slug for _n, slug, *_r in CATEGORY_SEED}
            for row in conn.execute("SELECT id, slug FROM categories").fetchall():
                if row["slug"] in keep:
                    continue
                used = conn.execute("SELECT 1 FROM listings WHERE category_id = ? LIMIT 1", (row["id"],)).fetchone()
                if used:
                    conn.execute("UPDATE categories SET is_active = 0 WHERE id = ?", (row["id"],))
                else:
                    conn.execute("DELETE FROM categories WHERE id = ?", (row["id"],))
        if _flag(conn, "strip_demo_note_v1"):
            conn.execute(
                "UPDATE listings SET description = REPLACE(description, ' Bu ilan demo veridir; gerçek satışa açılmadan önce yönetim panelinden silinmelidir.', '')"
                " WHERE is_demo = 1"
            )
        if _flag(conn, "drop_shopier_v1"):               # Shopier kaldırıldı: eski API/OSB anahtarları ve ayarları silinir
            conn.execute("DELETE FROM settings WHERE key LIKE 'shopier\\_%' ESCAPE '\\'")
        if _flag(conn, "seed_paylink_v1"):
            conn.execute(
                "INSERT INTO pay_links(title, description, url, amount, is_active, sort_order) VALUES (?,?,?,?,0,0)",
                ("Örnek ödeme linki - 100 TL", "Pasif örnek: kendi ödeme linkini ve fiyatını yazıp Aktif yap.", "https://ornek-odeme.example.com/pay/100-tl", 10000),
            )
        if _flag(conn, "seed_banners_v1"):
            for slot, title, sub, cta, link, c1, c2, order in BANNER_SEED:
                conn.execute(
                    "INSERT INTO banners(slot, title, subtitle, cta_text, link, color1, color2, sort_order) VALUES (?,?,?,?,?,?,?,?)",
                    (slot, title, sub, cta, link, c1, c2, order),
                )
        if conn.execute("SELECT COUNT(*) FROM payment_methods").fetchone()[0] == 0:
            for i, (name, kind, details, instructions, min_amount) in enumerate(DEFAULT_PAYMENT_METHODS):
                conn.execute(
                    "INSERT INTO payment_methods(name, kind, details, instructions, min_amount, is_active, sort_order)"
                    " VALUES (?,?,?,?,?,0,?)",
                    (name, kind, details, instructions, min_amount, i),
                )
    finally:
        conn.close()

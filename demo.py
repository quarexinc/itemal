"""Vitrini doldurmak için demo veri: mağazalar, kapak görselli ilanlar, stok ve yorumlar. Yönetim panelinden yüklenir, tek tıkla silinir.

Tüm kayıtlar 'is_demo=1' ile işaretlenir. Demo ilanlar satın alınabilir (ayar: demo_sales); teslim edilen kodlar örnek koddur ve stok
azalınca kendiliğinden yenilenir. Demo satıcıların kazancı kimse tarafından çekilemez. Mağaza başına en fazla 2 ilan, en fazla 10 yorum (hepsi 5 puan) ve en fazla 300 satış üretilir.
Bu bir önizleme verisidir: canlıya çıkmadan önce silinmeli, gerçek satıcılar ve gerçek alıcı yorumları kullanılmalıdır.
"""
import random
import re
import secrets
import uuid
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from werkzeug.security import generate_password_hash

import core
import db as dbm
import demo_art
import services
import storage
from core import ex, q, q1

DEMO_VERSION = "5"
MAX_SALES = 300
MAX_REVIEWS = 10

STORES = [
    {
        "name": "Kodhane", "user": "kodhane", "logo": ("kodhane", "#1a1d24", "#0b0c10"), "banner": ("kodhane", "#0e1a2b", "#1e3a5f"),
        "card": "tek", "factor": 1.00, "age": 560, "sales": (250, 298), "reviews": 10, "reply_rate": .55,
        "cats": ["steam", "epic-games", "battlenet", "ea-fc", "xbox-ps", "nintendo", "minecraft"],
        "desc": "2019'dan beri PC ve konsol oyuncularına dijital kod satıyoruz. Steam, Epic, Battle.net ve EA kodlarında anında teslimat; sorun olursa aynı gün dönüş yapıyoruz.",
        "replies": ["Teşekkürler, iyi oyunlar.", "Memnun kalmana sevindik, yine bekleriz.", "Değerlendirmen için sağ ol."],
    },
    {
        "name": "PinPark", "user": "pinpark", "logo": ("pinpark", "#0f766e", "#14b8a6"), "banner": ("pinpark", "#0f766e", "#0b3d3a"),
        "card": "cift", "factor": .98, "age": 390, "sales": (180, 235), "reviews": 8, "reply_rate": .35,
        "cats": ["pubg-uc", "free-fire", "mobile-legends", "genshin", "roblox"],
        "desc": "Mobil oyun paketlerinde uzmanız: PUBG UC, Free Fire elmas, Mobile Legends diamond ve Genshin kristalleri. Kodlar ödeme sonrası saniyeler içinde sipariş sayfanda.",
        "replies": ["Teşekkür ederiz, keyifli oyunlar.", "Tercih ettiğin için teşekkürler."],
    },
    {
        "name": "Dijital Durak", "user": "dijitaldurak", "logo": ("durak", "#1e2a78", "#3b4fd1"), "banner": ("durak", "#1e2a78", "#0d1240"),
        "card": "duz", "factor": 1.02, "age": 250, "sales": (115, 165), "reviews": 6, "reply_rate": .2,
        "cats": ["discord", "netflix", "spotify", "google-play", "app-store"],
        "desc": "Discord Nitro, Netflix, Spotify ve mağaza hediye kartları. Abonelik ve kart kodlarında haftalık kampanyalı fiyatlar.",
        "replies": ["Teşekkürler!", "İyi kullanımlar dileriz."],
    },
    {
        "name": "Arena Pin", "user": "arenapin", "logo": ("arena", "#b91c1c", "#7f1d1d"), "banner": ("arena", "#7f1d1d", "#2a0a0a"),
        "card": "egik", "factor": .97, "age": 70, "sales": (42, 95), "reviews": 4, "reply_rate": .85,
        "cats": ["valorant-vp", "fortnite", "riot-points"],
        "desc": "Valorant VP, Riot Points ve Fortnite V-Bucks. Yeni açıldık; ilk siparişlerinde mesajla her adımda yanındayız.",
        "replies": ["Çok teşekkür ederiz, yeni açıldık, desteğin çok değerli.", "Sağ ol, bir sonraki siparişte görüşürüz.", "Teşekkürler, iyi oyunlar!"],
    },
]

# ürün türüne göre açıklama
DESC_BY_TYPE = {
    "wallet": "Kodu ilgili platformun 'Kod kullan' bölümüne girdiğinde bakiye hesabına anında yansır. Kod yalnızca Türkiye bölgesi hesaplarında geçerlidir.",
    "topup": "Sipariş sonrası sayfada görünen kodu oyun içi mağazadaki 'Kod kullan' alanına gir. Hesap şifreni asla istemiyoruz.",
    "sub": "Kod, servisin hediye kodu sayfasında tanımlanır. Mevcut aboneliğin varsa süre üzerine eklenir.",
}
TYPE_OF = {
    "steam": "wallet", "epic-games": "wallet", "battlenet": "wallet", "google-play": "wallet", "app-store": "wallet", "xbox-ps": "wallet",
    "nintendo": "wallet", "minecraft": "wallet", "ea-fc": "topup", "pubg-uc": "topup", "free-fire": "topup", "mobile-legends": "topup",
    "genshin": "topup", "roblox": "topup", "valorant-vp": "topup", "fortnite": "topup", "riot-points": "topup",
    "discord": "sub", "netflix": "sub", "spotify": "sub",
}

# slug -> [(başlık, fiyat TL)]
CATALOG = {
    "discord": [("Discord Nitro 1 Aylık Hediye Kodu", 89.9), ("Discord Nitro 1 Yıllık Kod", 799), ("Discord Nitro Basic 1 Aylık", 49.9),
                ("Discord Sunucu Boost 2x 1 Aylık", 59), ("Discord Nitro 3 Aylık Kod", 229)],
    "steam": [("Steam 100 TL Cüzdan Kodu", 104), ("Steam 250 TL Cüzdan Kodu", 258), ("Steam 500 TL Cüzdan Kodu", 512),
              ("Steam 1000 TL Cüzdan Kodu", 1019), ("Steam 20 USD Cüzdan Kodu", 690)],
    "roblox": [("Roblox 800 Robux Hediye Kartı", 349), ("Roblox 1700 Robux Hediye Kartı", 699), ("Roblox 4500 Robux Hediye Kartı", 1690)],
    "valorant-vp": [("Valorant 1000 VP Hediye Kodu", 245), ("Valorant 2050 VP Hediye Kodu", 490), ("Valorant 5350 VP Hediye Kodu", 1190)],
    "pubg-uc": [("PUBG Mobile 325 UC", 149), ("PUBG Mobile 660 UC", 299), ("PUBG Mobile 1800 UC", 799), ("PUBG Mobile 3850 UC", 1590)],
    "fortnite": [("Fortnite 1000 V-Bucks Kartı", 279), ("Fortnite 2800 V-Bucks Kartı", 699), ("Fortnite 5000 V-Bucks Kartı", 1190)],
    "free-fire": [("Free Fire 530 Elmas", 169), ("Free Fire 1080 Elmas", 329), ("Free Fire 2200 Elmas", 649)],
    "mobile-legends": [("Mobile Legends 86 Diamond", 79), ("Mobile Legends 344 Diamond", 289), ("Mobile Legends 1050 Diamond", 849)],
    "genshin": [("Genshin Impact 330 Genesis Crystal", 189), ("Genshin Impact 1090 Genesis Crystal", 589), ("Genshin Impact 3280 Genesis Crystal", 1699)],
    "minecraft": [("Minecraft Java & Bedrock Edition", 690), ("Minecraft 1720 Minecoin", 269), ("Minecraft 3500 Minecoin", 449)],
    "riot-points": [("League of Legends 1380 RP", 199), ("League of Legends 2800 RP", 399), ("League of Legends 7200 RP", 949)],
    "epic-games": [("Epic Games 250 TL Cüzdan Kodu", 259), ("Epic Games 500 TL Cüzdan Kodu", 515), ("Epic Games 1000 TL Cüzdan Kodu", 1025)],
    "battlenet": [("Battle.net 100 TL Bakiye Kodu", 105), ("Battle.net 250 TL Bakiye Kodu", 259), ("Battle.net 500 TL Bakiye Kodu", 515)],
    "ea-fc": [("EA FC 1050 Points", 289), ("EA FC 2200 Points", 579), ("EA FC 5900 Points", 1449)],
    "xbox-ps": [("PlayStation Store 500 TL Kart", 520), ("Xbox Game Pass Ultimate 1 Ay", 349), ("PlayStation Plus Essential 3 Ay", 690)],
    "nintendo": [("Nintendo eShop 25 USD Kart", 899), ("Nintendo eShop 50 USD Kart", 1749), ("Nintendo Switch Online 12 Ay", 749)],
    "netflix": [("Netflix 1 Aylık Hediye Kartı", 199), ("Netflix 3 Aylık Hediye Kartı", 579), ("Netflix 500 TL Hediye Kartı", 515)],
    "spotify": [("Spotify Premium 3 Aylık Kod", 179), ("Spotify Premium 6 Aylık Kod", 339), ("Spotify Premium 12 Aylık Kod", 599)],
    "google-play": [("Google Play 100 TL Hediye Kartı", 105), ("Google Play 250 TL Hediye Kartı", 259), ("Google Play 500 TL Hediye Kartı", 515)],
    "app-store": [("App Store & iTunes 100 TL Kart", 105), ("App Store & iTunes 250 TL Kart", 259), ("App Store & iTunes 500 TL Kart", 515)],
}

FIRST = ["Emre", "Burak", "Can", "Cem", "Deniz", "Eren", "Furkan", "Hakan", "Kerem", "Mert", "Oğuz", "Serkan", "Tolga", "Yusuf", "Berkay",
         "Onur", "Alper", "Barış", "Murat", "Selim", "Ozan", "Arda", "Kaan", "Umut", "Gökhan", "Zeynep", "Elif", "Ayşe", "Merve", "Selin",
         "Büşra", "Esra", "Derya", "Ceren", "İrem", "Buse", "Gizem", "Ece", "Nehir", "Damla", "Sena", "Melis", "Yağmur", "Aylin"]
LAST = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan",
        "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek", "Polat", "Korkmaz", "Erdoğan", "Güneş", "Acar", "Bulut", "Tekin", "Aksoy", "Avcı", "Bozkurt"]

COMMENTS = [
    "kod 1 dk icinde geldi sorunsuz calisti tesekkurler",
    "hizli teslimat direk aktif oldu",
    "fiyat cok iyiydi tek seferde girdi",
    "ikinci alisverisim yine sorun yok",
    "mesaja hemen donus yapti kodu da aninda geldi",
    "gece 3te aldim yine de aninda geldi valla",
    "baska yerden dolandirilmistim burda sorun cikmadi eyvallah",
    "aciklamadaki gibi bolge sorunu yok",
    "satici ilgili tekrar alirim",
    "arkadasima da onerdim o da aldi sorunsuz",
    "hizli fiyat uygun ne olsun",
    "kodu girerken takildim hemen yardimci oldu",
    "sorunsuz alisveris ellerine saglik",
    "beklediimden hizli geldi",
    "fiyat performans iyi",
    "siparis verdim kod direk sayfada bekleme yok",
    "hediye icin aldim sorunsuz ulasti",
    "3. kez aliyorum hep ayni kalite",
    "odedim 2 dk sonra elimdeydi",
    "ilk defa denedim memnun kaldim",
    "tek seferde girdi hata yok",
    "kod sorunsuz tanimlandi",
    "teslimat aninda aciklama net",
    "bi daha buradan alirim",
    "super hizli, tesekkurler!!",
    "sipariş verdim hemen geldi cok memnunum",
    "harika satici 10 numara",
    "kodu kullandim calisiyor sorun yok",
    "cok hizliydi inanamadim",
    "fiyatlar diger yerlerden ucuz ve guvenilir",
    "iyi satici kod calisti",
    "eyw kardes sagol",
    "hizli ve sorunsuz tavsiye ederim",
    "kod hemen geldi tesekkur ederim",
    "yine geldim yine memnun kaldim",
    "sorun yasamadim kod aktif",
    "acil lazimdi hemen halletti saol",
    "emeginize saglik cok pratik",
    "onaylamadan once denedim calisiyodu",
    "uygun fiyat, hizli teslim.",
    "sıkıntı yok kod çalıştı",
    "güvenilir mağaza rahat alabilirsiniz",
    "çok iyi çok hızlı",
    "kod geldi çalışıyor teşekkürler",
    "mükemmel bişey yok diyecek",
    "{b} kodu saniyeler icinde geldi sorunsuz",
    "{b} icin ilk alisverisimdi memnunum",
    "{b} fiyati diger yerlerden uygundu tek seferde girdi",
    "gece {b} lazimdi aninda verdi",
    "{b} kodunu arkadasa hediye ettim sorunsuz ulasti",
    "{b} alirken tereddut ettim ama sorun cikmadi",
    "{b} hizli geldi tesekkurler",
    "{b} aldim calisiyor",
    "{b} cok hizli ya",
]
SELLER_COMMENTS = [
    "guvenilir satici rahatlikla alabilirsiniz",
    "hep buradan aliyorum sorun cikmadi",
    "mesajlara hizli donuyor",
    "fiyatlari uygun kodlar hep calisiyor",
    "arkadasim tavsiye etmisti iyi ki gelmisim",
    "ilgili satici tesekkurler",
    "hizli teslimat, tavsiye ederim",
    "kodlar sorunsuz cikti",
    "musteri iliskileri cok iyi",
    "daha once 3 kere aldim hepsi sorunsuz",
    "yorumlara bakip aldim pisman olmadim",
    "gece yarisi bile cevap verdi",
    "temiz is kod sorunu yok",
    "fiyat performans mağazası",
    "emek vermis magaza saglik olsun",
]
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]


def _font(size):
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _hex(color):
    color = (color or "#7c5cff").lstrip("#")
    if len(color) != 6:
        color = "7c5cff"
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def make_poster(color, title, seed):
    """Görseli olmayan kategori için dikey (3:4) afiş üretir; dosya adını döner."""
    rnd = random.Random(seed)
    w, h = 720, 960
    base = _hex(color)
    dark = tuple(int(c * 0.16) for c in base)
    small = Image.new("RGB", (36, 48), dark)
    sp = small.load()
    for y in range(48):
        for x in range(36):
            t = (x / 36) * 0.35 + (y / 48) * 0.65
            sp[x, y] = tuple(int(base[i] + (dark[i] - base[i]) * t) for i in range(3))
    img = small.resize((w, h), Image.BICUBIC).convert("RGBA")
    over = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for _ in range(5):
        r = rnd.randint(120, 330)
        cx, cy = rnd.randint(-60, w + 60), rnd.randint(-40, int(h * .7))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, rnd.randint(14, 34)))
    for i in range(-h, w, 70):
        d.line((i, h, i + h, 0), fill=(255, 255, 255, 14), width=3)
    over = over.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, over)
    top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    mono = services.mono(title)
    f = _font(330 if len(mono) <= 2 else 250)
    tw = d.textlength(mono, font=f)
    d.text((w - tw - 20, 40), mono, font=f, fill=(255, 255, 255, 46))
    d.rectangle((54, int(h * .56), 54 + 150, int(h * .56) + 8), fill=(255, 255, 255, 190))
    img = Image.alpha_composite(img, top)
    name = uuid.uuid4().hex + ".webp"
    storage.save_image(img.convert("RGB"), "cover", name, "WEBP", quality=84, method=4)
    return name


def _get(key, default=""):
    r = q1("SELECT value FROM settings WHERE key = ?", (key,))
    return r["value"] if r else default


def _code():
    return "DEMO-" + "-".join("".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(5)) for _ in range(3))


def _label(title):
    """Kapak üzerindeki büyük yazı: '100 TL', 'Nitro 1 Ay', '12 Ay' ..."""
    m = re.search(r"(\d[\d.,]*)\s?(TL|USD|UC|VP|RP|Robux|Elmas|V-Bucks|Minecoin|Diamond|Points|Genesis Crystal)", title)
    if m:
        return f"{m.group(1)} {m.group(2).replace('Genesis ', '')}"[:14]
    m = re.search(r"(\d+)\s?(Aylık|Yıllık|Ay)\b", title)
    if m:
        unit = "Yıl" if m.group(2).startswith("Y") else "Ay"
        prefix = "Nitro " if "Nitro" in title else "Boost " if "Boost" in title else ""
        return f"{prefix}{m.group(1)} {unit}"
    return title.split(" ")[0][:10]


_TR = str.maketrans("çğıöşüÇĞİÖŞÜâÂ", "cgiosuCGIOSUaA")


def _ascii(text):
    return re.sub(r"[^a-z0-9]", "", text.translate(_TR).lower())


def _ts(rnd, days_min, days_max):
    t = datetime.utcnow() - timedelta(days=rnd.uniform(days_min, days_max))
    return t.strftime("%Y-%m-%d %H:%M:%S")


def _buyer_names(rnd, n):
    names = set()
    while len(names) < n:
        f, l = rnd.choice(FIRST), rnd.choice(LAST)
        pattern = rnd.randint(0, 4)
        fa, la = _ascii(f), _ascii(l)
        if pattern == 0:
            u = fa + la
        elif pattern == 1:
            u = fa + "_" + la
        elif pattern == 2:
            u = fa[0] + la + str(rnd.randint(1, 99))
        elif pattern == 3:
            u = fa + str(rnd.randint(1980, 2007))[2:]
        else:
            u = fa + la[:3] + str(rnd.randint(1, 99))
        if core.USERNAME_RE.match(u[:20]):
            names.add(u[:20])
    return sorted(names)


def _brand(cat):
    nm = cat["name"].split(" (")[0].split(" / ")[0]
    for cut in (" Nitro & Boost", " Cüzdan Kodu", " Kartı"):
        nm = nm.replace(cut, "")
    return nm


def _round_price(tl, factor):
    p = tl * factor
    if p >= 200:
        return float(int(round(p / 5.0) * 5))
    return float(int(round(p))) - 0.1 if p >= 50 else round(p, 1)


def _pick_weighted(rnd, seq, weights):
    return rnd.choices(seq, weights=weights, k=1)[0]


_PENDING = []


def _stash(img, kind, name, **params):
    import io

    buf = io.BytesIO()
    img.save(buf, "WEBP", **params)
    _PENDING.append((kind, name, buf.getvalue()))


def _flush():
    while _PENDING:
        kind, name, data = _PENDING.pop()
        storage.put(kind, name, data, "image/webp")


def _prepare_art(cats, per_store):
    """Mağaza logo/kapakları ve ürün kapaklarını (çok iş parçacıklı) üretir; dosya adlarını döndürür."""
    from concurrent.futures import ThreadPoolExecutor

    def one_cover(key):
        si, slug, title = key
        st = STORES[si]
        c = cats[slug]
        img = demo_art.make_card_cover(c["color"] or "#7c5cff", _brand(c), _label(title), st["card"], f"{slug}{si}{title}")
        name = uuid.uuid4().hex + ".webp"
        _stash(img, "cover", name, quality=80, method=3)
        _stash(img.resize((480, 300), Image.LANCZOS), "cover", "t_" + name, quality=76, method=3)
        return key, name

    def one_store(si):
        st = STORES[si]
        avatar_name = uuid.uuid4().hex + ".webp"
        _stash(demo_art.make_logo(*st["logo"]), "avatar", avatar_name, quality=90, method=4)
        banner_name = uuid.uuid4().hex + ".webp"
        _stash(demo_art.make_store_banner(*st["banner"], seed=st["user"]), "cover", banner_name, quality=82, method=4)
        return si, (avatar_name, banner_name)

    keys = [(si, slug, title) for si, items in per_store.items() for slug, title, _p in items]
    with ThreadPoolExecutor(max_workers=4) as pool:
        covers = dict(pool.map(one_cover, keys))
        stores = dict(pool.map(one_store, [si for si, items in per_store.items() if items]))
    _flush()                                      # görseller iş parçacıklarında kodlanır, ana iş parçacığında veritabanına yazılır
    return {"covers": covers, "stores": stores}


def load():
    """Demo veriyi yükler; eklenen ilan sayısını döner. Zaten yüklüyse hiçbir şey yapmaz."""
    if _get("demo_loaded", "0") == "1":
        return 0
    rnd = random.Random(20260929)
    cats = {c["slug"]: c for c in q("SELECT * FROM categories WHERE is_active = 1")}
    made_posters = []     # kategori posterleri artık üretilmez: sitenin hazır kategori bannerları (static_src/kategori) kullanılır
    owner = {slug: i for i, st in enumerate(STORES) for slug in st["cats"]}
    per_store = {i: [] for i in range(len(STORES))}
    for slug, items in CATALOG.items():
        if slug in cats and slug in owner:
            for it in items:
                per_store[owner[slug]].append((slug, *it))
    made = 0
    pw_hash = generate_password_hash(secrets.token_hex(24))  # kimse bilmiyor: demo hesaplara giriş yapılamaz
    art = _prepare_art(cats, per_store)   # ağır görsel üretimi veritabanı işleminin dışında yapılır
    with core.tx():
        # alıcı havuzu (yorum yazacak hesaplar)
        buyer_ids = []
        for u in _buyer_names(rnd, 30):
            if q1("SELECT 1 FROM users WHERE username = ?", (u,)):
                continue
            cur = ex(
                "INSERT INTO users(username, email, password_hash, is_seller, kyc_status, is_demo, created_at) VALUES (?,?,?,0,'none',1,?)",
                (u, f"demo+{u}@example.invalid", pw_hash, _ts(rnd, 15, 400)),
            )
            buyer_ids.append(cur.lastrowid)
        pending = []   # (store_index, seller_id, item) - ekleme sırası karışık olsun
        seller_ids = {}
        for si, st in enumerate(STORES):
            if not per_store[si]:
                continue
            uname = st["user"]
            if q1("SELECT 1 FROM users WHERE username = ?", (uname,)):
                uname += str(rnd.randint(10, 99))
            total_sold = rnd.randint(*st["sales"])
            avatar_name, banner_name = art["stores"][si]
            cur = ex(
                "INSERT INTO users(username, email, password_hash, is_seller, kyc_status, store_name, store_desc, avatar, store_banner, is_demo, demo_sold, created_at)"
                " VALUES (?,?,?,1,'approved',?,?,?,?,1,?,?)",
                (uname, f"demo+{uname}@example.invalid", pw_hash, st["name"], st["desc"], avatar_name, banner_name, total_sold, _ts(rnd, st["age"], st["age"] + 1)),
            )
            seller_ids[si] = (cur.lastrowid, total_sold)
            for item in per_store[si]:
                pending.append((si, item))
        rnd.shuffle(pending)
        # satışları mağazanın ilanlarına ağırlıklı böl
        weights = {}
        for si, item in pending:
            weights.setdefault(si, []).append(rnd.uniform(.3, 1.6))
        split = {}
        for si, ws in weights.items():
            total = seller_ids[si][1]
            s = sum(ws)
            parts = [max(1, int(total * w / s)) for w in ws]
            parts[-1] = max(1, total - sum(parts[:-1]))
            split[si] = parts
            ex("UPDATE users SET demo_sold = ? WHERE id = ?", (sum(parts), seller_ids[si][0]))
        counters = {si: 0 for si in weights}
        listing_rows = {si: [] for si in weights}   # (lid, sold, brand)
        for si, (slug, title, price) in pending:
            st = STORES[si]
            sid, _tot = seller_ids[si]
            sold = split[si][counters[si]]
            counters[si] += 1
            c = cats[slug]
            brand = _brand(c)
            tl = _round_price(price, st["factor"])
            deal = 1 if (c["is_daily"] and rnd.random() < .35) else 0
            old = int(round(tl * rnd.choice([1.12, 1.18, 1.25]) * 100)) if (deal or rnd.random() < .12) else 0
            cover = art["covers"][(si, slug, title)]
            created = _ts(rnd, 1, min(60, st["age"] - 2))
            desc = f"{title}. {DESC_BY_TYPE.get(TYPE_OF.get(slug, 'wallet'))}"
            cur = ex(
                "INSERT INTO listings(seller_id, category_id, title, description, cover, price, old_price, is_deal, is_featured,"
                " sales_count, views, rating_sum, rating_count, is_demo, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,0,0,1,?,?)",
                (sid, c["id"], title, desc, cover, int(round(tl * 100)), old, deal, 1 if rnd.random() < .1 else 0,
                 sold, rnd.randint(sold * 3, sold * 12), created, created),
            )
            lid = cur.lastrowid
            listing_rows[si].append((lid, sold, brand))
            for _ in range(rnd.randint(3, 22)):
                ex("INSERT OR IGNORE INTO listing_codes(listing_id, code) VALUES (?,?)", (lid, _code()))
            made += 1
        # yorumlar: hepsi 5 puan; mağaza başına sabit sayı (en fazla MAX_REVIEWS)
        for si, rows in listing_rows.items():
            st = STORES[si]
            sid = seller_ids[si][0]
            n_rev = min(MAX_REVIEWS, st["reviews"])
            who = rnd.sample(buyer_ids, n_rev)
            used = set()
            counts = {}
            for k in range(n_rev):
                lid, _s, brand = _pick_weighted(rnd, rows, [r[1] for r in rows])
                text = ""
                while not text or text in used:
                    text = rnd.choice(COMMENTS).format(b=brand)
                used.add(text)
                when = _ts(rnd, 1, min(80, st["age"] - 3))
                reply = rnd.choice(st["replies"]) if rnd.random() < st["reply_rate"] else ""
                ex(
                    "INSERT INTO reviews(order_id, listing_id, seller_id, buyer_id, rating, comment, seller_reply, replied_at, created_at, is_demo)"
                    " VALUES (NULL,?,?,?,5,?,?,?,?,1)",
                    (lid, sid, who[k], text, reply, when if reply else None, when),
                )
                counts[lid] = counts.get(lid, 0) + 1
            for lid, cnt in counts.items():
                ex("UPDATE listings SET rating_count = ?, rating_sum = ? WHERE id = ?", (cnt, cnt * 5, lid))
        # mağaza yorumları (profil düzeyinde)
        for si in listing_rows:
            sid = seller_ids[si][0]
            for author, text in zip(rnd.sample(buyer_ids, min(len(buyer_ids), rnd.randint(3, 5))), rnd.sample(SELLER_COMMENTS, 5)):
                ex(
                    "INSERT OR IGNORE INTO seller_comments(seller_id, author_id, body, is_demo, created_at) VALUES (?,?,?,1,?)",
                    (sid, author, text, _ts(rnd, 1, 60)),
                )
        for cid, name in made_posters:
            ex("UPDATE categories SET image = ? WHERE id = ?", (name, cid))
        ex("INSERT INTO settings(key, value) VALUES ('demo_posters', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
           (",".join(n for _c, n in made_posters),))
        ex("INSERT INTO settings(key, value) VALUES ('demo_version', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (DEMO_VERSION,))
        ex("INSERT INTO settings(key, value) VALUES ('demo_loaded', '1') ON CONFLICT(key) DO UPDATE SET value = '1'")
    return made


def clear():
    """Demo kayıtlarını ve görsellerini siler. (silinen_ilan, silinen_kullanıcı) döner."""
    with core.tx():
        ex("DELETE FROM reviews WHERE is_demo = 1")
        ex("DELETE FROM seller_comments WHERE is_demo = 1")
        listings = q("SELECT id, cover FROM listings WHERE is_demo = 1")
        users = q("SELECT id, avatar, store_banner FROM users WHERE is_demo = 1")
        for l in listings:
            if q1("SELECT 1 FROM orders WHERE listing_id = ? LIMIT 1", (l["id"],)):
                ex("UPDATE listings SET status = 'removed' WHERE id = ?", (l["id"],))
                continue
            ex("DELETE FROM listing_codes WHERE listing_id = ?", (l["id"],))
            ex("DELETE FROM listings WHERE id = ?", (l["id"],))
        left = {r["seller_id"] for r in q("SELECT DISTINCT seller_id FROM listings")}
        for u in users:
            if u["id"] in left or q1("SELECT 1 FROM orders WHERE seller_id = ? OR buyer_id = ? LIMIT 1", (u["id"], u["id"])):
                continue
            ex("DELETE FROM users WHERE id = ?", (u["id"],))
        keep = {slug for _n, slug, *_r in dbm.CATEGORY_SEED}
        for c in q("SELECT id, slug FROM categories WHERE is_active = 0"):
            if c["slug"] not in keep and not q1("SELECT 1 FROM listings WHERE category_id = ? LIMIT 1", (c["id"],)):
                ex("DELETE FROM categories WHERE id = ?", (c["id"],))
        posters = [n for n in _get("demo_posters", "").split(",") if n]
        for n in posters:
            ex("UPDATE categories SET image = '' WHERE image = ?", (n,))
        ex("INSERT INTO settings(key, value) VALUES ('demo_posters', '') ON CONFLICT(key) DO UPDATE SET value = ''")
        ex("INSERT INTO settings(key, value) VALUES ('demo_loaded', '0') ON CONFLICT(key) DO UPDATE SET value = '0'")
    for n in posters:
        services.delete_cover(n)
    for l in listings:
        if not q1("SELECT 1 FROM listings WHERE id = ?", (l["id"],)):
            services.delete_cover(l["cover"])
    for u in users:
        if not q1("SELECT 1 FROM users WHERE id = ?", (u["id"],)):
            services.delete_avatar(u["avatar"])
            services.delete_cover(u["store_banner"])
    return len(listings), len(users)


def autoseed():
    """Açılışta vitrini boş bırakmamak için demo veriyi kendiliğinden yükler.

    - İlan hiç yoksa ve daha önce denenmediyse yükler (silinen demo veri geri gelmez).
    - Eski sürüm demo veri yüklüyse yeni sürümle değiştirir.
    AUTO_DEMO=0 ile tamamen kapatılır.
    """
    import os
    if os.getenv("AUTO_DEMO", "1") != "1":
        return
    if _get("demo_loaded", "0") == "1":
        if _get("demo_version", "") != DEMO_VERSION:
            print("itemal: demo veri yenileniyor...", flush=True)
            clear()
            load()
        return
    if q1("SELECT 1 FROM listings LIMIT 1"):
        return
    import time
    now = int(time.time())
    row = q1("SELECT value FROM settings WHERE key = 'demo_autoseeded'")
    if row:
        # '1': daha önce yüklendi (silindiyse geri gelmez). Zaman damgası: yükleme yarım kaldıysa 5 dk sonra yeniden denenir.
        if not row["value"].isdigit() or row["value"] == "1" or now - int(row["value"]) < 300:
            return
        claimed = ex("UPDATE settings SET value = ? WHERE key = 'demo_autoseeded' AND value = ?", (str(now), row["value"]))
    else:
        claimed = ex("INSERT OR IGNORE INTO settings(key, value) VALUES ('demo_autoseeded', ?)", (str(now),))
    if claimed.rowcount:
        print("itemal: vitrin için demo veri hazırlanıyor (birkaç saniye)...", flush=True)
        try:
            load()
            ex("UPDATE settings SET value = '1' WHERE key = 'demo_autoseeded'")
        except BaseException:
            ex("DELETE FROM settings WHERE key = 'demo_autoseeded'")
            raise


def start_autoseed(app):
    """Demo yüklemesini arka planda başlatır; sunucu hemen açılır. Thread döner."""
    import threading

    def run():
        with app.app_context():
            try:
                autoseed()
            except Exception as err:  # pragma: no cover
                print("itemal: demo veri yüklenemedi:", err, flush=True)

    t = threading.Thread(target=run, name="demo-autoseed", daemon=True)
    t.start()
    return t

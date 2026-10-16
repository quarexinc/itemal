"""Kendi sunucumuzda üretilen CAPTCHA (dış servis yok). Pillow ile bozulmuş yazı çizilir.

Sözleşme (giriş, kayıt, yönetici girişi, destek formu aynı API'yi kullanır):
  new_challenge(scope)   oturumda yeni bir sınama kurar (5 dk ömürlü); düz cevabı döner (yalnızca resim çizimi için)
  verify(scope, answer)  cevabı doğrular. Büyük/küçük harf duyarsız. Sınama doğru ya da yanlış her kullanımda silinir
                         (tek kullanımlık); yanlış cevapta yenisi kurulur.
  captcha_block(scope)   Jinja global'i: <img> + giriş alanı (name="captcha") + "Yenile" bağlantısı (satır içi betik yok)
  GET /captcha/<scope>.png  PNG üretir (Cache-Control: no-store, IP başına dakikada 30)

Güvenlik: oturum çerezi imzalıdır ama şifreli değildir. Bu yüzden çerezde cevap değil, SECRET_KEY ile anahtarlanmış
HMAC bulunur (çevrimdışı kaba kuvvetle çözülemez). Çerez kopyalanıp yeniden oynatılamasın diye kullanılan her sınama
kimliği sunucuda (rate_hits, scope=cap_used) yakılır.
"""
import hashlib
import hmac
import io
import math
import random
import secrets
import time

from flask import Blueprint, Response, abort, request, session
from markupsafe import Markup, escape

import core

bp = Blueprint("captcha", __name__)

SCOPES = ("login", "register", "admin", "ticket", "report", "contact")      # beyaz liste
TTL = 300                       # sınama ömrü (sn)
ALPHABET = "ACDEFGHJKMNPRTUVWXY34679"        # 0/O, 1/I/l, 5/S, 2/Z, 8/B, 6/G gibi karışanlar yok
IMG_W, IMG_H = 240, 72
_FONT_FILES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
)


# --------------------------------------------------------------------------- sınama durumu (oturum + sunucu kaydı)
def _mac(scope, cid, answer):
    msg = f"captcha|{scope}|{cid}|{_norm(answer)}".encode()
    return hmac.new(core.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()[:32]


def _norm(answer):
    return "".join(str(answer or "").split()).upper()[:12]


def _make_text():
    n = random.SystemRandom().choice((5, 5, 6))
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def make_entry(scope, text, now=None):
    """Oturuma yazılacak kayıt: [kimlik, mac, bitiş]. (Testler de bunu kullanarak bilinen cevaplı sınama kurar.)"""
    cid = secrets.token_hex(8)
    return [cid, _mac(scope, cid, text), int((now or time.time()) + TTL)]


def new_challenge(scope):
    if scope not in SCOPES:
        raise ValueError("bilinmeyen captcha kapsamı")
    text = _make_text()
    store = session.get("cap")
    store = dict(store) if isinstance(store, dict) else {}
    now = time.time()
    store = {k: v for k, v in store.items() if isinstance(v, list) and len(v) == 3 and v[2] > now}      # süresi dolanları at
    store[scope] = make_entry(scope, text, now)
    session["cap"] = store
    return text


def _burn(cid):
    """Kimliği kalıcı olarak 'kullanıldı' işaretler; ilk kez yakılıyorsa True. Tek SQL ifadesi = atomik (eşzamanlı iki
    istek aynı sınamayı birlikte kullanamaz)."""
    cur = core.ex(
        "INSERT INTO rate_hits(scope, key, ts) SELECT 'cap_used', ?1, ?2 WHERE NOT EXISTS"
        " (SELECT 1 FROM rate_hits WHERE scope = 'cap_used' AND key = ?1)",
        (cid, time.time()),
    )
    return cur.rowcount == 1


def verify(scope, answer):
    store = session.get("cap")
    entry = store.get(scope) if isinstance(store, dict) else None
    ok = False
    if isinstance(entry, list) and len(entry) == 3 and scope in SCOPES:
        cid, mac, exp = entry
        # kullanıldı mı + süresi geçti mi + cevap doğru mu; her denemede sınama silinir
        fresh = _burn(str(cid)[:32])
        if fresh and time.time() <= exp and answer is not None:
            ok = hmac.compare_digest(str(mac), _mac(scope, cid, answer))
        store = dict(store)
        store.pop(scope, None)
        session["cap"] = store
    if not ok and scope in SCOPES:
        new_challenge(scope)                    # yanlış / süresi dolmuş: yenisi hazır
    return ok


def has_challenge(scope):
    store = session.get("cap")
    entry = store.get(scope) if isinstance(store, dict) else None
    return bool(isinstance(entry, list) and len(entry) == 3 and entry[2] > time.time())


# --------------------------------------------------------------------------- resim
def _load_font(size):
    from PIL import ImageFont

    for path in _FONT_FILES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                                    # eski Pillow
        return ImageFont.load_default()


def render_png(text):
    from PIL import Image, ImageDraw, ImageFilter

    rnd = random.SystemRandom()
    W, H = IMG_W, IMG_H
    bg = (rnd.randint(236, 248), rnd.randint(236, 248), rnd.randint(232, 248))
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    # arka plan: açık renkli lekeler + ince gürültü çizgileri (yazıdan önce, okunurluğu bozmayacak kadar soluk)
    for _ in range(14):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.randint(8, 26)
        c = tuple(max(200, v - rnd.randint(6, 26)) for v in bg)
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    for _ in range(5):
        c = (rnd.randint(150, 205), rnd.randint(150, 205), rnd.randint(150, 205))
        d.line([(rnd.randint(0, W), rnd.randint(0, H)), (rnd.randint(0, W), rnd.randint(0, H))], fill=c, width=rnd.randint(1, 2))

    n = len(text)
    slot = (W - 24) / n
    base_size = 42 if n <= 5 else 38
    for i, ch in enumerate(text):
        font = _load_font(base_size + rnd.randint(-4, 4))
        tile = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        color = (rnd.randint(10, 90), rnd.randint(10, 90), rnd.randint(40, 130))
        td.text((32, 32), ch, font=font, fill=color + (255,), anchor="mm")
        tile = tile.rotate(rnd.uniform(-24, 24), resample=Image.BICUBIC, expand=False)
        x = int(12 + i * slot + (slot - 64) / 2 + rnd.randint(-3, 3))
        y = int((H - 64) / 2 + rnd.randint(-5, 5))
        img.paste(tile, (x, y), tile)

    # dalga bozulması (sütun kaydırma)
    amp, period, phase = rnd.uniform(2.0, 3.6), rnd.uniform(46, 72), rnd.uniform(0, 6.28)
    src = img.copy()
    for x in range(W):
        dy = int(round(amp * math.sin(2 * math.pi * x / period + phase)))
        col = src.crop((x, 0, x + 1, H))
        img.paste(bg, (x, 0, x + 1, H))
        img.paste(col, (x, dy))
    d = ImageDraw.Draw(img)
    # yazının üstünden geçen eğri/çizgiler ve noktalar
    for _ in range(3):
        c = (rnd.randint(40, 140), rnd.randint(40, 140), rnd.randint(40, 140))
        pts = []
        y0, a2, p2, ph2 = rnd.randint(14, H - 14), rnd.uniform(5, 13), rnd.uniform(40, 90), rnd.uniform(0, 6.28)
        for x in range(0, W + 6, 6):
            pts.append((x, y0 + a2 * math.sin(2 * math.pi * x / p2 + ph2)))
        d.line(pts, fill=c, width=1)
    for _ in range(220):
        c = (rnd.randint(60, 200), rnd.randint(60, 200), rnd.randint(60, 200))
        d.point((rnd.randint(0, W - 1), rnd.randint(0, H - 1)), fill=c)
    img = img.filter(ImageFilter.GaussianBlur(0.45))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=False)
    return buf.getvalue()


@bp.route("/captcha/<scope>.png")
def image(scope):
    if scope not in SCOPES:
        abort(404)
    if core.rate_hit("captcha", 30, 60):                       # IP başına dakikada 30 resim
        resp = Response("Çok fazla istek. Biraz bekle.", status=429, mimetype="text/plain")
        resp.headers["Retry-After"] = "60"
        return resp
    resp = Response(render_png(new_challenge(scope)), mimetype="image/png")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Content-Disposition"] = "inline"
    return resp


# --------------------------------------------------------------------------- şablon yardımcısı
def captcha_block(scope):
    """Güvenli HTML. Resim ilk açılışta ve her 'Yenile' tıklamasında yeni sınama üretir; betik gerekmez
    (betik varsa 'Yenile' sayfayı yeniden yüklemeden resmi yeniler)."""
    if scope not in SCOPES:
        raise ValueError("bilinmeyen captcha kapsamı")
    rid = secrets.token_hex(3)
    src = f"/captcha/{scope}.png?r={rid}"
    here = escape(request.path if request else "/")
    return Markup(
        '<div class="captcha" data-captcha="{scope}">'
        '<label for="captcha-{scope}">Güvenlik doğrulaması</label>'
        '<div class="captcha-row">'
        '<img class="captcha-img" src="{src}" width="{w}" height="{h}" alt="Doğrulama resmi: resimdeki harf ve rakamları yaz" data-base="/captcha/{scope}.png">'
        '<a class="captcha-refresh" href="{here}" data-captcha-refresh>Yenile</a>'
        '</div>'
        '<input type="text" id="captcha-{scope}" name="captcha" required maxlength="8" autocomplete="off" autocapitalize="characters" '
        'spellcheck="false" inputmode="text" placeholder="Resimdeki karakterler">'
        '<div class="hint">Resimdeki harf ve rakamları yaz (büyük/küçük harf fark etmez). Okunamıyorsa Yenile bağlantısına tıkla.</div>'
        '</div>'
    ).format(scope=escape(scope), src=escape(src), w=IMG_W, h=IMG_H, here=here)


def install(app):
    """app.py'de tek satır: captcha.install(app). İki kez çağrılsa da güvenlidir."""
    if "captcha" not in app.blueprints:
        app.register_blueprint(bp)
    app.jinja_env.globals["captcha_block"] = captcha_block
    return app

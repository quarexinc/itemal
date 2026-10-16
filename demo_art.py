"""Demo veri için görsel üretimi: kart görünümlü ürün kapakları, mağaza logoları ve fotoğraf dokulu mağaza kapakları.

Yalnızca özgün geometrik şekiller ve düz yazı kullanılır; gerçek marka logosu veya oyun görseli çizilmez.
Gerçek görsellerle değiştirmek için mağaza sahibi satıcı panelinden logo/kapak yükler, yönetici de kategori afişi yükler.
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]


def font(size):
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def hex_rgb(color):
    color = (color or "#7c5cff").lstrip("#")
    if len(color) != 6:
        color = "7c5cff"
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient(size, c1, c2, angle_x=0.6):
    """Küçük ölçekte üretip büyütür (hızlı), köşegen degrade."""
    w, h = size
    sw, sh = max(8, w // 20), max(8, h // 20)
    small = Image.new("RGB", (sw, sh))
    px = small.load()
    for y in range(sh):
        for x in range(sw):
            t = x / sw * angle_x + y / sh * (1 - angle_x)
            px[x, y] = mix(c1, c2, t)
    return small.resize(size, Image.BICUBIC)


def _rounded_mask(size, radius, scale=3):
    w, h = size
    m = Image.new("L", (w * scale, h * scale), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * scale - 1, h * scale - 1), radius=radius * scale, fill=255)
    return m.resize(size, Image.LANCZOS)


def _grain(size, strength=10):
    noise = Image.effect_noise(size, 64).convert("RGB")
    return noise, strength


def _add_grain(img, strength=9):
    noise = Image.effect_noise(img.size, 60).convert("RGB")
    return Image.blend(img, ImageChops.overlay(img, noise), strength / 100)


def _fit_text(draw, text, max_w, start, minimum=28):
    size = start
    while size > minimum:
        f = font(size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return font(minimum)


# --------------------------------------------------------------------------- ürün kapağı
def _card_face(color, brand, label, variant, seed):
    """Hediye kartı yüzü (RGBA)."""
    rnd = random.Random(seed)
    cw, ch = 600, 376
    base = hex_rgb(color)
    face = _gradient((cw, ch), mix(base, (255, 255, 255), .22), mix(base, (0, 0, 0), .55), .55).convert("RGBA")
    over = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    # halkalar / parlama
    cx, cy = rnd.choice([(cw - 30, 20), (cw - 60, ch - 20), (40, ch - 10)])
    for r in (90, 150, 210, 270):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 34), width=3)
    d.polygon([(0, 0), (cw * .62, 0), (cw * .30, ch), (0, ch)], fill=(255, 255, 255, 20))
    if variant == 1:
        for i in range(-ch, cw, 34):
            d.line((i, ch, i + ch, 0), fill=(255, 255, 255, 14), width=8)
    over = over.filter(ImageFilter.GaussianBlur(.8))
    face = Image.alpha_composite(face, over)
    d = ImageDraw.Draw(face)
    pad = 38
    d.text((pad, 34), brand.upper(), font=_fit_text(d, brand.upper(), cw - 2 * pad - 170, 34, 20), fill=(255, 255, 255, 235))
    big = _fit_text(d, label, cw - 2 * pad, 104, 46)
    d.text((pad, ch - 168), label, font=big, fill=(255, 255, 255, 250))
    small = font(17)
    d.text((pad, ch - 58), "DİJİTAL KOD", font=small, fill=(255, 255, 255, 190))
    if variant == 0:  # çip
        chip = Image.new("RGBA", (64, 48), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle((0, 0, 63, 47), radius=9, fill=(236, 200, 120, 255))
        for y in (16, 31):
            cd.line((0, y, 63, y), fill=(160, 120, 50, 255), width=2)
        cd.line((32, 0, 32, 47), fill=(160, 120, 50, 255), width=2)
        face.alpha_composite(chip, (cw - pad - 64, 30))
    else:  # barkod benzeri şerit
        x = cw - pad - 110
        for _ in range(26):
            wbar = rnd.choice([2, 3, 4, 6])
            d.rectangle((x, 30, x + wbar, 74), fill=(255, 255, 255, 190))
            x += wbar + rnd.choice([3, 4, 6])
            if x > cw - pad:
                break
    # ince kenar ışığı
    edge = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(edge).rounded_rectangle((1, 1, cw - 2, ch - 2), radius=34, outline=(255, 255, 255, 70), width=2)
    face = Image.alpha_composite(face, edge)
    mask = _rounded_mask((cw, ch), 34)
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    out.paste(face, (0, 0), mask)
    return out, mask


def make_card_cover(color, brand, label, style, seed):
    """16:10 ürün görseli: bokeh zemin üzerinde gölgeli hediye kartı. style: 'tek' | 'cift' | 'duz' | 'egik'."""
    rnd = random.Random(seed)
    W, H = 1000, 625
    base = hex_rgb(color)
    bg = _gradient((W, H), mix(base, (8, 8, 14), .72), mix(base, (8, 8, 14), .90), .3).convert("RGBA")
    bokeh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bokeh)
    for _ in range(9):
        r = rnd.randint(40, 150)
        x, y = rnd.randint(-40, W + 40), rnd.randint(-40, H + 40)
        bd.ellipse((x - r, y - r, x + r, y + r), fill=mix(base, (255, 255, 255), rnd.uniform(.05, .4)) + (rnd.randint(28, 70),))
    bg = Image.alpha_composite(bg, bokeh.filter(ImageFilter.GaussianBlur(22)))

    cards = []  # (yüz, açı, merkez, ölçek, gölge)
    variant = {"tek": 0, "cift": 0, "duz": 1, "egik": 1}.get(style, 0)
    face, mask = _card_face(color, brand, label, variant, seed)
    if style == "cift":
        back, bmask = _card_face(color, brand, label, 1, seed + "b")
        back = Image.blend(back, Image.new("RGBA", back.size, (10, 10, 16, 255)), .45)
        back.putalpha(bmask)
        cards.append((back, 11, (W * .60, H * .44), .78))
        cards.append((face, -5, (W * .47, H * .56), .86))
    elif style == "duz":
        cards.append((face, 0, (W * .5, H * .52), .92))
    elif style == "egik":
        cards.append((face, -13, (W * .5, H * .56), 1.05))
    else:
        cards.append((face, -7, (W * .5, H * .54), .90))

    canvas = bg
    for img, angle, (cx, cy), scale in cards:
        s = int(img.width * scale), int(img.height * scale)
        card = img.resize(s, Image.LANCZOS).rotate(angle, resample=Image.BICUBIC, expand=True)
        alpha = card.split()[3]
        pad = 90
        sh_a = Image.new("L", (card.width + 2 * pad, card.height + 2 * pad), 0)
        sh_a.paste(alpha.point(lambda v: int(v * .62)), (pad, pad))
        sh_a = sh_a.filter(ImageFilter.GaussianBlur(26))
        shadow = Image.new("RGBA", sh_a.size, (0, 0, 0, 255))
        shadow.putalpha(sh_a)
        pos = (int(cx - card.width / 2), int(cy - card.height / 2))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(shadow, (pos[0] - pad, pos[1] - pad + 30), shadow)
        canvas = Image.alpha_composite(canvas, layer)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(card, pos, card)
        canvas = Image.alpha_composite(canvas, layer)
    # vinyet + tane
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-W * .25, -H * .35, W * 1.25, H * 1.35), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(90))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    canvas = Image.composite(canvas, Image.alpha_composite(canvas, dark), vig)
    return _add_grain(canvas.convert("RGB"), 7)


# --------------------------------------------------------------------------- mağaza logoları
def _logo_canvas(c1, c2):
    S = 1024
    bg = _gradient((S, S), c1, c2, .5).convert("RGBA")
    return bg, S


def make_logo(kind, c1, c2):
    """Özgün geometrik mağaza logosu (256x256 RGB)."""
    c1, c2 = hex_rgb(c1), hex_rgb(c2)
    bg, S = _logo_canvas(c1, c2)
    m = Image.new("L", (S, S), 0)   # beyaz şekil maskesi: 255 ekler, 0 oyar
    d = ImageDraw.Draw(m)
    accent = []
    if kind == "kodhane":  # K harfi + amber kare
        d.rectangle((290, 240, 400, 784), fill=255)
        d.line((400, 520, 700, 250), fill=255, width=118)
        d.line((470, 500, 740, 784), fill=255, width=118)
        accent.append(("rect", (700, 170, 790, 260), (245, 165, 36, 255)))
    elif kind == "pinpark":  # konum iğnesi
        d.ellipse((252, 172, 772, 692), fill=255)
        d.polygon([(292, 590), (732, 590), (512, 900)], fill=255)
        d.ellipse((392, 312, 632, 552), fill=0)
        d.ellipse((452, 372, 572, 492), fill=255)
    elif kind == "durak":  # altıgen içinde D
        cx, cy, R = 512, 512, 390
        hexa = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(30, 390, 60)]
        d.polygon(hexa, fill=255)
        r2 = R - 40
        hexa2 = [(cx + r2 * math.cos(math.radians(a)), cy + r2 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
        d.polygon(hexa2, fill=0)
        d.rectangle((380, 350, 510, 674), fill=255)
        d.pieslice((330, 350, 690, 674), -90, 90, fill=255)
        d.rectangle((440, 420, 510, 604), fill=0)
        d.pieslice((400, 420, 610, 604), -90, 90, fill=0)
    else:  # arena: A harfi + elmas
        d.polygon([(512, 200), (800, 800), (668, 800), (620, 690), (404, 690), (356, 800), (224, 800)], fill=255)
        d.polygon([(512, 388), (580, 560), (444, 560)], fill=0)
        accent.append(("poly", [(512, 100), (552, 145), (512, 190), (472, 145)], (255, 205, 96, 255)))
    white = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    white.putalpha(m)
    img = Image.alpha_composite(bg, white)
    ad = ImageDraw.Draw(img)
    for kindc, geo, col in accent:
        (ad.rectangle if kindc == "rect" else ad.polygon)(geo, fill=col)
    img.putalpha(_rounded_mask((S, S), int(S * .24), 1))
    img = img.resize((256, 256), Image.LANCZOS)
    flat = Image.new("RGB", (256, 256), (17, 17, 24))
    flat.paste(img, (0, 0), img)
    return flat


# --------------------------------------------------------------------------- mağaza kapağı
def make_store_banner(kind, c1, c2, seed):
    """Fotoğraf dokulu 4:1 mağaza kapağı (1600x400): bokeh, ışık çizgileri, tane, vinyet."""
    rnd = random.Random(seed)
    W, H = 1600, 400
    c1, c2 = hex_rgb(c1), hex_rgb(c2)
    img = _gradient((W, H), c1, c2, .8).convert("RGBA")
    light = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(light)
    if kind == "kodhane":  # sunucu/monitör ışıkları: yatay çizgiler
        for y in range(30, H, 26):
            x = rnd.randint(-100, W)
            length = rnd.randint(200, 900)
            d.line((x, y, x + length, y), fill=mix(c2, (255, 255, 255), .6) + (rnd.randint(35, 100),), width=rnd.choice([2, 3, 5]))
        for _ in range(16):
            x, y = rnd.randint(0, W), rnd.randint(0, H)
            r = rnd.randint(4, 9)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(120, 220, 255, 200))
    elif kind == "pinpark":  # büyük bokeh
        for _ in range(14):
            r = rnd.randint(50, 160)
            x, y = rnd.randint(0, W), rnd.randint(-20, H + 20)
            d.ellipse((x - r, y - r, x + r, y + r), fill=mix(c2, (255, 255, 255), rnd.uniform(.2, .7)) + (rnd.randint(40, 100),))
    elif kind == "durak":  # çapraz ışık huzmeleri
        for i in range(-H, W, 120):
            d.polygon([(i, H), (i + 60, H), (i + 60 + H, 0), (i + H, 0)], fill=(255, 255, 255, rnd.randint(10, 30)))
        for _ in range(9):
            r = rnd.randint(30, 90)
            x, y = rnd.randint(0, W), rnd.randint(0, H)
            d.ellipse((x - r, y - r, x + r, y + r), fill=mix(c2, (255, 255, 255), .5) + (60,))
    else:  # arena: petek ızgara
        size = 46
        for row in range(-1, H // size + 2):
            for col in range(-1, W // (size * 2) + 2):
                cx = col * size * 3 + (size * 1.5 if row % 2 else 0)
                cy = row * size * .87
                pts = [(cx + size * math.cos(math.radians(a)), cy + size * math.sin(math.radians(a))) for a in range(0, 360, 60)]
                d.polygon(pts, outline=(255, 255, 255, rnd.randint(8, 40)))
        for _ in range(7):
            r = rnd.randint(40, 120)
            x, y = rnd.randint(0, W), rnd.randint(0, H)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 120, 90, 55))
    light = light.filter(ImageFilter.GaussianBlur(3 if kind in ("kodhane", "arena") else 16))
    img = Image.alpha_composite(img, light)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-W * .1, -H * .5, W * 1.1, H * 1.5), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(80))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 150))
    img = Image.composite(img, Image.alpha_composite(img, dark), vig)
    return _add_grain(img.convert("RGB"), 10)

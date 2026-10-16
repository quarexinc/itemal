#!/usr/bin/env python3
"""Kategori banner gorsellerini uretir (tek seferlik gelistirici araci; hosting'te PIL gerekmez).

Cikti (static_src/kategori/; templates_gen.generate bunlari public/static/kategori/ altina kopyalar):
  <slug>.webp        genis banner 1600x480 (ad + aciklama yazili)      <= 120 KB
  mobil-<slug>.webp  mobil banner 640x400 (ad + aciklama yazili)       <= 60 KB
  kart-<slug>.webp   "Gunun oyunlari" karti 720x960 (yazisiz)          <= 60 KB
  genel*.webp        yeni kategoriler icin varsayilan yedek.

Her kategori icin farkli bir soyut kompozisyon cizilir; gercek logo/marka/karakter KULLANILMAZ.
Kullanim:  python3 tools/make_category_banners.py [slug ...]   (bos = hepsi)
"""
import io
import math
import os
import random
import re
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static_src", "kategori")
FONT_DIR = "/usr/share/fonts/truetype/google-fonts/"
F_BOLD = FONT_DIR + "Poppins-Bold.ttf"
F_MED = FONT_DIR + "Poppins-Medium.ttf"
F_REG = FONT_DIR + "Poppins-Regular.ttf"

# slug, ad, grup, renk, aciklama, tema, desen   (db.py tohumundaki kategorilerle ayni)
CATS = [
    ("discord", "Discord Nitro & Boost", "Uygulama & Abonelik", "#5865F2", "Nitro, Nitro Basic ve sunucu boost kodları", "cardstack", "grid"),
    ("steam", "Steam Cüzdan Kodu", "PC & Konsol", "#1b9bd7", "TL ve USD cüzdan kodları", "wallet", "circuit"),
    ("roblox", "Roblox Robux", "PC & Konsol", "#e2231a", "Robux ve Roblox hediye kartları", "cubes", "dots"),
    ("valorant-vp", "Valorant VP", "PC & Konsol", "#ff4655", "Valorant Points hediye kodları", "shards", "diag"),
    ("pubg-uc", "PUBG Mobile UC", "Mobil", "#eab308", "PUBG Mobile UC paketleri", "coins", "rings"),
    ("fortnite", "Fortnite V-Bucks", "PC & Konsol", "#8a5cff", "V-Bucks ve Fortnite kartları", "orbs", "hex"),
    ("free-fire", "Free Fire Elmas", "Mobil", "#ff7a00", "Free Fire elmas paketleri", "flamegems", "diag"),
    ("mobile-legends", "Mobile Legends", "Mobil", "#38bdf8", "Diamond paketleri", "shield", "grid"),
    ("genshin", "Genshin Impact", "Mobil", "#5ec8f2", "Genesis Crystal paketleri", "crystals", "dots"),
    ("minecraft", "Minecraft", "PC & Konsol", "#62b47a", "Minecraft hesap ve Minecoin kodları", "voxels", "grid"),
    ("riot-points", "Riot Points (LoL)", "PC & Konsol", "#c89b3c", "League of Legends RP kodları", "hexcoins", "hex"),
    ("epic-games", "Epic Games", "PC & Konsol", "#a1a1aa", "Epic Games cüzdan ve oyun kodları", "plates", "diag"),
    ("battlenet", "Battle.net / Blizzard", "PC & Konsol", "#148eff", "Blizzard bakiye ve oyun kodları", "vortex", "rings"),
    ("ea-fc", "EA FC Points", "PC & Konsol", "#22c55e", "EA FC Points ve EA Play", "soccer", "pitch"),
    ("xbox-ps", "Xbox / PlayStation", "PC & Konsol", "#0e7cd6", "Xbox Game Pass ve PSN kartları", "gamepad", "dots"),
    ("nintendo", "Nintendo eShop", "PC & Konsol", "#e60012", "Nintendo eShop kartları", "pixels", "pixelgrid"),
    ("netflix", "Netflix", "Uygulama & Abonelik", "#e50914", "Netflix hediye kartları", "cinema", "diag"),
    ("spotify", "Spotify", "Uygulama & Abonelik", "#1db954", "Spotify Premium kodları", "vinyl", "rings"),
    ("google-play", "Google Play Kartı", "Hediye Kartları", "#34a853", "Google Play hediye kartları", "gift", "dots"),
    ("app-store", "App Store & iTunes", "Hediye Kartları", "#60a5fa", "Apple hediye kartları", "tiles", "grid"),
    ("genel", "Dijital Kodlar", "E-pin Pazaryeri", "#7c5cff", "Oyun, abonelik ve hediye kartları tek yerde", "mix", "grid"),
]

SS = 2  # supersampling
LAYOUTS = {  # ad: (son genislik, son yukseklik, onek, kb sinir)
    "wide": (1600, 480, "", 120),
    "mobile": (640, 400, "mobil-", 60),
    "card": (720, 960, "kart-", 60),
}

# --------------------------------------------------------------------------- renk yardimcilari


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def clampc(c):
    return tuple(int(max(0, min(255, round(v)))) for v in c)


def hue_shift(c, dh=0.0, ds=1.0, dv=1.0):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
    h = (h + dh) % 1.0
    s = max(0, min(1, s * ds))
    v = max(0, min(1, v * dv))
    return tuple(x * 255 for x in colorsys.hsv_to_rgb(h, s, v))


WHITE = (255, 255, 255)
INK = (6, 7, 14)


def shade(c, b):
    """b>1 aciklastirir (beyaza karistirir), b<1 koyulastirir."""
    if b >= 1:
        return mix(c, WHITE, min(1, (b - 1) * 0.9))
    return tuple(v * b for v in c)


class Pal:
    def __init__(self, hexcolor):
        self.c = hex2rgb(hexcolor)
        self.dark = mix(self.c, INK, 0.88)
        self.mid = mix(self.c, INK, 0.60)
        self.hi = mix(self.c, WHITE, 0.45)
        self.pale = mix(self.c, WHITE, 0.75)
        self.acc = mix(hue_shift(self.c, 0.07, 1.05, 1.05), WHITE, 0.2)
        self.acc2 = mix(hue_shift(self.c, -0.08, 1.0, 1.0), WHITE, 0.15)
        self.deep = mix(self.c, INK, 0.45)


# --------------------------------------------------------------------------- cizim ilkelleri


def grad_img(size, stops, angle=90.0):
    """stops: [(t,(r,g,b)), ...]; angle derece (90 = yukaridan asagi)."""
    w, h = size
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    xs = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    ys = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    t = (xs * dx + ys * dy) / (abs(dx) + abs(dy) + 1e-6) * 0.5 + 0.5
    ts = [s[0] for s in stops]
    out = np.zeros((h, w, 4), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(t, ts, [s[1][ch] for s in stops])
    out[..., 3] = 255
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def rad_img(size, center, inner, outer, radius=None, power=1.0):
    """Radyal gradyan: merkezde inner, kenarda outer (RGB). center oransal."""
    w, h = size
    cx, cy = center[0] * w, center[1] * h
    r = radius or max(w, h) * 0.5
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    t = np.clip(d, 0, 1) ** power
    out = np.zeros((h, w, 4), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = inner[ch] * (1 - t) + outer[ch] * t
    out[..., 3] = 255
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def comp(L, img, x, y):
    W, H = L.size
    x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + img.width), min(H, y + img.height)
    if x1 <= x0 or y1 <= y0:
        return
    L.alpha_composite(img.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def new_layer(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _fill(img, bbox, cb, stops, angle, alpha, radial=None):
    x0, y0, x1, y1 = [int(v) for v in bbox]
    x0 -= 2; y0 -= 2; x1 += 3; y1 += 3
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return
    m = Image.new("L", (w, h), 0)
    cb(ImageDraw.Draw(m), x0, y0)
    if radial:
        g = rad_img((w, h), radial[0], radial[1], radial[2], radial[3] * max(w, h) if len(radial) > 3 else None)
    elif stops is None:
        g = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    else:
        g = grad_img((w, h), stops, angle)
    if alpha < 1:
        m = m.point(lambda v: int(v * alpha))
    g.putalpha(m)
    comp(img, g, x0, y0)


def stops_of(c1, c2=None, c3=None):
    if c2 is None:
        return [(0, c1), (1, c1)]
    if c3 is None:
        return [(0, c1), (1, c2)]
    return [(0, c1), (0.5, c2), (1, c3)]


def fpoly(img, pts, c1, c2=None, angle=90, alpha=1.0, c3=None):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    fpoly.last = bbox
    _fill(img, bbox, lambda d, ox, oy: d.polygon([(x - ox, y - oy) for x, y in pts], fill=255),
          stops_of(c1, c2, c3), angle, alpha)


def frr(img, box, r, c1, c2=None, angle=90, alpha=1.0, c3=None):
    _fill(img, box, lambda d, ox, oy: d.rounded_rectangle((box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy), r, fill=255),
          stops_of(c1, c2, c3), angle, alpha)


def fell(img, box, c1, c2=None, angle=90, alpha=1.0, c3=None):
    _fill(img, box, lambda d, ox, oy: d.ellipse((box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy), fill=255),
          stops_of(c1, c2, c3), angle, alpha)


def fell_rad(img, box, inner, outer, center=(0.38, 0.32), alpha=1.0, radius=0.78):
    _fill(img, box, lambda d, ox, oy: d.ellipse((box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy), fill=255),
          None, 0, alpha, radial=(center, inner, outer, radius))


def stroke(img, kind, geom, color, width, alpha=1.0):
    """kind: 'line' (noktalar), 'poly' (kapali), 'arc' (box,a0,a1), 'ell' (box), 'rr' (box,r)"""
    t = new_layer(img.size)
    d = ImageDraw.Draw(t)
    col = tuple(clampc(color)) + (int(255 * alpha),)
    width = max(1, int(width))
    if kind == "line":
        d.line(geom, fill=col, width=width, joint="curve")
    elif kind == "poly":
        d.line(list(geom) + [geom[0], geom[1]], fill=col, width=width, joint="curve")
    elif kind == "arc":
        d.arc(geom[0], geom[1], geom[2], fill=col, width=width)
    elif kind == "ell":
        d.ellipse(geom, outline=col, width=width)
    elif kind == "rr":
        d.rounded_rectangle(geom[0], geom[1], outline=col, width=width)
    img.alpha_composite(t)


def blur_alpha(img, radius):
    return img.filter(ImageFilter.GaussianBlur(radius))


def blit(L, piece, cx, cy, shadow=0.5, glow=None, off=(0.0, 0.05), sblur=0.05):
    """piece (RGBA) merkezi (cx,cy) olacak sekilde L uzerine golge/isima ile yerlestirir."""
    w, h = piece.size
    m = max(w, h)
    pad = int(m * 0.35)
    big = (w + 2 * pad, h + 2 * pad)
    a = Image.new("L", big, 0)
    a.paste(piece.getchannel("A"), (pad, pad))
    X, Y = int(cx - big[0] / 2), int(cy - big[1] / 2)
    if glow:
        col, amt, rad = glow
        g = Image.new("RGBA", big, tuple(clampc(col)) + (0,))
        g.putalpha(a.filter(ImageFilter.GaussianBlur(rad * m)).point(lambda v: min(255, int(v * amt))))
        comp(L, g, X, Y)
    if shadow:
        s = Image.new("RGBA", big, (0, 0, 0, 0))
        s.putalpha(a.filter(ImageFilter.GaussianBlur(m * sblur)).point(lambda v: int(v * shadow)))
        comp(L, s, X + int(off[0] * m), Y + int(off[1] * m))
    comp(L, piece, X + pad, Y + pad)


def persp(img, kx=0.0, ky=0.0):
    """Hafif perspektif: kx>0 sag kenari kisaltir, ky>0 alt kenari kisaltir (oran)."""
    w, h = img.size
    pad = int(max(w, h) * 0.05)
    base = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    base.paste(img, (pad, pad))
    W, H = base.size
    # hedef dortgen (sol-ust, sag-ust, sag-alt, sol-alt)
    dx, dy = kx * h * 0.5, ky * w * 0.5
    dst = [(0, 0 + max(0, -dx) * 0), (W, dx), (W, H - dx), (0, H)]
    if kx < 0:
        dst = [(0, -dx), (W, 0), (W, H), (0, H + dx)]
    if ky:
        dst = [(dy, 0), (W - dy, 0), (W, H), (0, H)]
    src = [(0, 0), (W, 0), (W, H), (0, H)]
    coeffs = _coeffs(dst, src)
    return base.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)


def _coeffs(dst, src):
    rows = []
    for (x, y), (u, v) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.array(rows, dtype=np.float64)
    B = np.array([c for p in src for c in p], dtype=np.float64)
    return tuple(np.linalg.solve(A, B).tolist())


def rot(img, ang):
    return img.rotate(ang, resample=Image.BICUBIC, expand=True)


def sparkle(L, cx, cy, r, color=WHITE, alpha=0.95, glow=True):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.16
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    if glow:
        g = new_layer(L.size)
        fell(g, (cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5), color, alpha=0.9)
        g = g.crop((int(cx - r * 2), int(cy - r * 2), int(cx + r * 2), int(cy + r * 2))).filter(ImageFilter.GaussianBlur(r * 0.35))
        comp(L, g, int(cx - r * 2), int(cy - r * 2))
    fpoly(L, pts, color, color, alpha=alpha)


def glow_dot(L, cx, cy, r, color, alpha=0.8):
    pad = int(r * 3)
    t = new_layer((pad * 2, pad * 2))
    fell(t, (pad - r, pad - r, pad + r, pad + r), color, alpha=alpha)
    t = t.filter(ImageFilter.GaussianBlur(r * 0.9))
    comp(L, t, int(cx - pad), int(cy - pad))
    fell(L, (cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45), WHITE, alpha=min(1, alpha + 0.1))


# --------------------------------------------------------------------------- nesneler (RGBA parca dondurur)

GEMS = {
    "brilliant": [  # (noktalar, parlaklik)
        ([(-0.55, -0.7), (0.55, -0.7), (0.4, -0.2), (-0.4, -0.2)], 1.45),
        ([(-1, -0.2), (-0.55, -0.7), (-0.4, -0.2)], 1.05),
        ([(1, -0.2), (0.55, -0.7), (0.4, -0.2)], 0.78),
        ([(-1, -0.2), (-0.4, -0.2), (0, 1)], 0.62),
        ([(-0.4, -0.2), (0, -0.2), (0, 1)], 1.0),
        ([(0, -0.2), (0.4, -0.2), (0, 1)], 0.82),
        ([(0.4, -0.2), (1, -0.2), (0, 1)], 0.5),
    ],
    "shard": [
        ([(0, -1), (-0.55, -0.35), (0, -0.2)], 1.5),
        ([(0, -1), (0, -0.2), (0.55, -0.35)], 0.95),
        ([(-0.55, -0.35), (0, -0.2), (0, 1)], 1.0),
        ([(-0.55, -0.35), (-0.12, 0.2), (0, 1)], 0.7),
        ([(0, -0.2), (0.55, -0.35), (0, 1)], 0.55),
    ],
    "hex": [
        ([(-0.5, -0.87), (0.5, -0.87), (0, 0)], 1.45),
        ([(0.5, -0.87), (1, 0), (0, 0)], 0.95),
        ([(-1, 0), (-0.5, -0.87), (0, 0)], 1.1),
        ([(-1, 0), (0, 0), (-0.5, 0.87)], 0.7),
        ([(0, 0), (1, 0), (0.5, 0.87)], 0.58),
        ([(-0.5, 0.87), (0, 0), (0.5, 0.87)], 0.82),
    ],
    "oct": [
        ([(-0.4, -1), (0.4, -1), (0.3, -0.45), (-0.3, -0.45)], 1.5),
        ([(-1, -0.4), (-0.4, -1), (-0.3, -0.45)], 1.1),
        ([(1, -0.4), (0.4, -1), (0.3, -0.45)], 0.8),
        ([(-1, -0.4), (-0.3, -0.45), (-0.45, 0.35)], 0.85),
        ([(-0.3, -0.45), (0.3, -0.45), (0.45, 0.35), (-0.45, 0.35)], 1.15),
        ([(1, -0.4), (0.3, -0.45), (0.45, 0.35)], 0.6),
        ([(-1, -0.4), (-0.45, 0.35), (0, 1)], 0.65),
        ([(-0.45, 0.35), (0.45, 0.35), (0, 1)], 0.9),
        ([(1, -0.4), (0.45, 0.35), (0, 1)], 0.45),
    ],
}


def gem_piece(r, color, style="brilliant", sx=1.0, sy=1.0):
    pad = int(r * 0.2)
    w, h = int(2 * r * sx) + 2 * pad, int(2 * r * sy) + 2 * pad
    img = new_layer((w, h))
    cx, cy = w / 2, h / 2
    for pts, b in GEMS[style]:
        P = [(cx + x * r * sx, cy + y * r * sy) for x, y in pts]
        c1 = shade(color, b * 1.06)
        c2 = shade(color, b * 0.9)
        fpoly(img, P, c1, c2, angle=60)
    # kenar cizgileri
    for pts, b in GEMS[style]:
        P = [(cx + x * r * sx, cy + y * r * sy) for x, y in pts]
        stroke(img, "poly", P, WHITE, max(2, r * 0.016), 0.28)
    # parilti
    f0 = GEMS[style][0][0]
    gx = sum(p[0] for p in f0) / len(f0)
    gy = sum(p[1] for p in f0) / len(f0)
    sparkle(img, cx + gx * r * sx - r * 0.1, cy + gy * r * sy, r * 0.22, WHITE, 0.9, glow=False)
    return img


def coin_piece(r, color, tilt=0.38, thick=0.12, emboss="ring"):
    w = int(2 * r) + 8
    flat = new_layer((w, w))
    c = w / 2
    fell_rad(flat, (4, 4, w - 4, w - 4), shade(color, 1.35), shade(color, 0.72), (0.34, 0.28), radius=0.85)
    stroke(flat, "ell", (4 + r * 0.04, 4 + r * 0.04, w - 4 - r * 0.04, w - 4 - r * 0.04), shade(color, 1.5), r * 0.05, 0.9)
    inner = r * 0.74
    stroke(flat, "ell", (c - inner, c - inner, c + inner, c + inner), shade(color, 0.6), r * 0.045, 0.55)
    stroke(flat, "ell", (c - inner + r * 0.03, c - inner + r * 0.03, c + inner + r * 0.03, c + inner + r * 0.03), shade(color, 1.6), r * 0.02, 0.5)
    ec = shade(color, 0.62)
    if emboss == "star":
        pts = []
        for i in range(10):
            a = math.pi / 5 * i - math.pi / 2
            rr = r * 0.5 if i % 2 == 0 else r * 0.22
            pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        fpoly(flat, pts, ec, ec, alpha=0.8)
    elif emboss == "cross":
        k = r * 0.52
        stroke(flat, "ell", (c - k, c - k, c + k, c + k), ec, r * 0.06, 0.8)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stroke(flat, "line", [(c + dx * k * 0.55, c + dy * k * 0.55), (c + dx * k * 1.3, c + dy * k * 1.3)], ec, r * 0.06, 0.8)
        fell(flat, (c - r * 0.07, c - r * 0.07, c + r * 0.07, c + r * 0.07), ec, alpha=0.9)
    elif emboss == "hex":
        pts = [(c + r * 0.5 * math.cos(math.pi / 3 * i + math.pi / 6), c + r * 0.5 * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
        stroke(flat, "poly", [v for p in pts for v in p], ec, r * 0.07, 0.85)
        pts2 = [(c + r * 0.26 * math.cos(math.pi / 3 * i + math.pi / 6), c + r * 0.26 * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
        fpoly(flat, pts2, ec, ec, alpha=0.75)
    elif emboss == "bolt":
        pts = [(c + 0.08 * r, c - 0.55 * r), (c - 0.3 * r, c + 0.08 * r), (c - 0.02 * r, c + 0.08 * r), (c - 0.1 * r, c + 0.55 * r), (c + 0.3 * r, c - 0.1 * r), (c + 0.02 * r, c - 0.1 * r)]
        fpoly(flat, pts, ec, ec, alpha=0.85)
    else:
        k = r * 0.4
        stroke(flat, "ell", (c - k, c - k, c + k, c + k), ec, r * 0.08, 0.8)
    th = max(2, int(r * thick))
    fh = max(2, int(w * tilt))
    out = new_layer((w, fh + th + 2))
    top = flat.resize((w, fh), Image.LANCZOS)
    # kenar (yan yuz)
    edge_col = shade(color, 0.55)
    for k in range(th, 0, -1):
        e = Image.new("RGBA", (w, fh), tuple(clampc(shade(edge_col, 1 + 0.25 * (k / th)))) + (255,))
        e.putalpha(top.getchannel("A"))
        out.alpha_composite(e, (0, k))
    out.alpha_composite(top, (0, 0))
    return out


def stack_coins(r, color, n, tilt=0.38, emboss="ring", spacing=0.2):
    th = r * 0.13
    step = r * spacing
    pc = coin_piece(r, color, tilt, 0.13, emboss)
    h = pc.height + int(step * (n - 1))
    out = new_layer((pc.width, h))
    for i in range(n):
        out.alpha_composite(pc, (0, int(step * (n - 1 - i))))
        # ince golge cizgisi
    return out


def card_piece(w, h, color, kind="wallet", r=None, alpha=1.0, variant=0):
    r = r or int(h * 0.09)
    pad = 6
    img = new_layer((w + 2 * pad, h + 2 * pad))
    box = (pad, pad, pad + w, pad + h)
    frr(img, box, r, shade(color, 1.28), shade(color, 0.62), angle=35, alpha=alpha)
    # ic cam katmani
    inner = new_layer(img.size)
    # buyuk yumusak daireler
    for (cxr, cyr, rr, a) in ((0.85, 0.15, 0.55, 0.2), (0.15, 1.0, 0.6, 0.16)):
        t = new_layer(img.size)
        fell(t, (pad + w * cxr - h * rr, pad + h * cyr - h * rr, pad + w * cxr + h * rr, pad + h * cyr + h * rr), WHITE, alpha=a)
        inner.alpha_composite(t)
    msk = Image.new("L", img.size, 0)
    ImageDraw.Draw(msk).rounded_rectangle(box, r, fill=255)
    inner.putalpha(ImageChops.multiply(inner.getchannel("A"), msk))
    img.alpha_composite(inner)
    # diyagonal parlama
    gl = new_layer(img.size)
    fpoly(gl, [(pad + w * 0.1, pad), (pad + w * 0.42, pad), (pad + w * 0.18, pad + h), (pad - w * 0.14, pad + h)], WHITE, WHITE, alpha=0.1)
    gl.putalpha(ImageChops.multiply(gl.getchannel("A"), msk))
    img.alpha_composite(gl)
    stroke(img, "rr", (box, r), WHITE, max(2, h * 0.012), 0.55)
    if kind in ("wallet", "code"):
        chip = (pad + w * 0.08, pad + h * 0.2, pad + w * 0.08 + h * 0.3, pad + h * 0.2 + h * 0.23)
        frr(img, chip, h * 0.04, (255, 230, 160), (210, 160, 70), angle=45)
        for k in (0.33, 0.66):
            stroke(img, "line", [(chip[0], chip[1] + (chip[3] - chip[1]) * k), (chip[2], chip[1] + (chip[3] - chip[1]) * k)], (140, 100, 40), max(1, h * 0.008), 0.7)
        stroke(img, "line", [((chip[0] + chip[2]) / 2, chip[1]), ((chip[0] + chip[2]) / 2, chip[3])], (140, 100, 40), max(1, h * 0.008), 0.7)
        # kod noktalari
        ry = pad + h * 0.66
        for g in range(4):
            for d in range(4):
                x = pad + w * 0.09 + g * w * 0.2 + d * h * 0.052
                fell(img, (x, ry, x + h * 0.034, ry + h * 0.034), WHITE, alpha=0.85)
        # sag ust sinyal yaylari
        for i in range(3):
            q = h * (0.05 + 0.04 * i)
            cx0, cy0 = pad + w * 0.9, pad + h * 0.2
            stroke(img, "arc", ((cx0 - q, cy0 - q, cx0 + q, cy0 + q), -50, 50), WHITE, max(2, h * 0.012), 0.7)
        # alt sag cubuklar
        frr(img, (pad + w * 0.62, pad + h * 0.82, pad + w * 0.9, pad + h * 0.855), h * 0.01, WHITE, WHITE, alpha=0.5)
    elif kind == "gift":
        rw = w * 0.14
        frr(img, (pad + w * 0.5 - rw / 2, pad, pad + w * 0.5 + rw / 2, pad + h), 0, shade(color, 1.9), shade(color, 1.3), angle=0, alpha=0.9)
        frr(img, (pad, pad + h * 0.5 - rw / 2, pad + w, pad + h * 0.5 + rw / 2), 0, shade(color, 1.9), shade(color, 1.3), angle=90, alpha=0.9)
        cx0, cy0 = pad + w * 0.5, pad + h * 0.5
        for sgn in (-1, 1):
            loop = [(cx0, cy0), (cx0 + sgn * w * 0.16, cy0 - h * 0.28), (cx0 + sgn * w * 0.3, cy0 - h * 0.12), (cx0 + sgn * w * 0.14, cy0 + h * 0.02)]
            fpoly(img, loop, shade(color, 2.0), shade(color, 1.4), angle=45, alpha=0.95)
        fell(img, (cx0 - h * 0.05, cy0 - h * 0.05, cx0 + h * 0.05, cy0 + h * 0.05), shade(color, 1.9), shade(color, 1.3))
        # clipping
        img.putalpha(ImageChops.multiply(img.getchannel("A"), Image.new("L", img.size, 255)))
        mm = Image.new("L", img.size, 0)
        ImageDraw.Draw(mm).rounded_rectangle((box[0] - h * 0.5, box[1] - h * 0.5, box[2] + h * 0.5, box[3] + h * 0.5), r, fill=0)
    elif kind == "plain":
        for i in range(3):
            frr(img, (pad + w * 0.08, pad + h * (0.62 + 0.1 * i), pad + w * (0.5 - 0.1 * i), pad + h * (0.65 + 0.1 * i)), h * 0.01, WHITE, WHITE, alpha=0.6 - 0.15 * i)
        fell(img, (pad + w * 0.08, pad + h * 0.15, pad + w * 0.08 + h * 0.26, pad + h * 0.15 + h * 0.26), WHITE, shade(color, 1.4), alpha=0.85)
    return img


def cube_piece(s, color, grid=1, noise=0.0, seed=0, bevel=True):
    """Izometrik kup. Dondurur: RGBA parca (genislik ~ 1.74 s)."""
    rnd = random.Random(seed)
    w = int(1.8 * s)
    h = int(2.1 * s)
    img = new_layer((w, h))
    cx, cy = w / 2, h / 2
    ex = (s * 0.866, s * 0.5)   # sag-asagi
    ey = (-s * 0.866, s * 0.5)  # sol-asagi
    ez = (0, -s)                 # yukari
    top0 = (cx, cy - s)
    faces = {
        "top": (top0, ex, ey, 1.28),
        "left": ((cx - s * 0.866, cy - s * 0.5), ex, ez * 1 if False else (0, s), 0.8),
        "right": ((cx, cy), (s * 0.866, -s * 0.5), (0, s), 0.55),
    }
    # ust yuz: orijin top0'dan ex ve ey ile (rombus)
    n = grid
    def quad(o, u, v, i, j, b):
        p0 = (o[0] + u[0] * i / n + v[0] * j / n, o[1] + u[1] * i / n + v[1] * j / n)
        p1 = (p0[0] + u[0] / n, p0[1] + u[1] / n)
        p2 = (p1[0] + v[0] / n, p1[1] + v[1] / n)
        p3 = (p0[0] + v[0] / n, p0[1] + v[1] / n)
        return [p0, p1, p2, p3], b
    spec = [
        ((cx, cy - s), (s * 0.866, s * 0.5), (-s * 0.866, s * 0.5), 1.3),                 # ust
        ((cx - s * 0.866, cy - s * 0.5), (s * 0.866, s * 0.5), (0, s), 0.85),              # sol
        ((cx, cy), (s * 0.866, -s * 0.5), (0, s), 0.55),                                   # sag
    ]
    for o, u, v, b in spec:
        for i in range(n):
            for j in range(n):
                pts, bb = quad(o, u, v, i, j, b)
                bj = bb * (1 + rnd.uniform(-noise, noise))
                col = shade(color, bj)
                fpoly(img, pts, col, shade(col, 0.92), angle=70)
                if n > 1:
                    stroke(img, "poly", pts, (0, 0, 0), max(1, s * 0.012), 0.18)
    # kenar parlamasi
    outline = [(cx, cy - s), (cx + s * 0.866, cy - s * 0.5), (cx + s * 0.866, cy + s * 0.5), (cx, cy + s), (cx - s * 0.866, cy + s * 0.5), (cx - s * 0.866, cy - s * 0.5)]
    if bevel:
        stroke(img, "poly", [v for p in outline for v in p], WHITE, max(2, s * 0.025), 0.35)
        stroke(img, "line", [(cx - s * 0.866, cy - s * 0.5), (cx, cy), (cx + s * 0.866, cy - s * 0.5)], WHITE, max(1, s * 0.02), 0.28)
        stroke(img, "line", [(cx, cy), (cx, cy + s)], WHITE, max(1, s * 0.02), 0.12)
    return img


def flame_piece(r, c1, c2):
    w, h = int(r * 2.4), int(r * 3.4)
    img = new_layer((w, h))
    cx = w / 2
    pts = []
    for i in range(0, 101):
        t = i / 100
        # sol kenar yukari, sag kenar asagi
        pass
    def side(sg):
        out = []
        for i in range(0, 41):
            t = i / 40.0
            y = h * 0.96 - t * h * 0.94
            wd = math.sin(math.pi * min(1, t * 1.05 + 0.02)) ** 0.8 * r * 0.95 * (1 - t * 0.35)
            wob = math.sin(t * 7 + (0 if sg > 0 else 1.3)) * r * 0.12 * t
            out.append((cx + sg * wd + wob + t ** 2 * r * 0.35, y))
        return out
    left = side(-1)
    right = side(1)
    poly = left + right[::-1]
    fpoly(img, poly, c2, c1, angle=270)
    inner = []
    for p in poly:
        inner.append((cx + (p[0] - cx) * 0.55 + r * 0.05, h * 0.96 + (p[1] - h * 0.96) * 0.62))
    fpoly(img, inner, mix(c1, WHITE, 0.55), mix(c2, WHITE, 0.35), angle=270, alpha=0.9)
    return img


def shield_piece(r, color):
    w, h = int(2 * r * 1.05), int(2 * r * 1.25)
    img = new_layer((w, h))
    cx = w / 2
    pts = []
    pts.append((cx, 0))
    for i in range(0, 21):
        t = i / 20
        pts.append((cx + w * 0.5 * (0.35 + 0.65 * math.sin(t * math.pi / 2)) , h * 0.1 + t * h * 0.35))
    for i in range(0, 31):
        t = i / 30
        x = cx + w * 0.5 * math.cos(t * math.pi / 2) ** 0.9
        y = h * 0.45 + t * h * 0.55
        pts.append((x, y))
    right = pts[:]
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    poly = right + left
    fpoly(img, poly, shade(color, 1.35), shade(color, 0.55), angle=70)
    # ic cerceve
    inner = [(cx + (x - cx) * 0.84, h * 0.5 + (y - h * 0.5) * 0.86 + h * 0.02) for x, y in poly]
    fpoly(img, inner, shade(color, 0.5), shade(color, 0.85), angle=70, alpha=0.95)
    stroke(img, "poly", [v for p in poly for v in p], WHITE, max(2, r * 0.04), 0.5)
    stroke(img, "poly", [v for p in inner for v in p], WHITE, max(2, r * 0.02), 0.3)
    return img


def controller_piece(w, color):
    h = int(w * 0.66)
    pad = int(w * 0.04)
    img = new_layer((w + 2 * pad, h + 2 * pad))
    X0, Y0 = pad, pad
    body = new_layer(img.size)
    # govde: merkez + iki kol
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((X0 + w * 0.12, Y0 + h * 0.1, X0 + w * 0.88, Y0 + h * 0.62), h * 0.26, fill=255)
    for sg in (-1, 1):
        cxg = X0 + w * (0.5 + sg * 0.33)
        # kol: egik elips
        grip = Image.new("L", img.size, 0)
        ImageDraw.Draw(grip).ellipse((cxg - w * 0.13, Y0 + h * 0.32, cxg + w * 0.13, Y0 + h * 0.98), fill=255)
        grip = grip.rotate(sg * 14, resample=Image.BICUBIC, center=(cxg, Y0 + h * 0.62))
        mask = ImageChops.lighter(mask, grip)
    mask = mask.filter(ImageFilter.GaussianBlur(w * 0.012)).point(lambda v: 255 if v > 128 else int(v * 2) if v > 64 else 0)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    g = grad_img(img.size, [(0, mix(color, (225, 235, 250), 0.55)), (0.55, mix(color, (150, 170, 200), 0.3)), (1, mix(color, INK, 0.4))], 75)
    g.putalpha(mask)
    img.alpha_composite(g)
    # ust parlama
    hl = grad_img(img.size, [(0, WHITE), (1, WHITE)])
    hm = Image.new("L", img.size, 0)
    ImageDraw.Draw(hm).rounded_rectangle((X0 + w * 0.14, Y0 + h * 0.12, X0 + w * 0.86, Y0 + h * 0.3), h * 0.12, fill=60)
    hm = ImageChops.multiply(hm, mask)
    hl.putalpha(hm.filter(ImageFilter.GaussianBlur(w * 0.01)))
    img.alpha_composite(hl)
    # kenar isigi
    edge = mask.filter(ImageFilter.MaxFilter(5))
    rim = ImageChops.subtract(edge, mask)
    rc = new_layer(img.size)
    rc.paste(Image.new("RGBA", img.size, (235, 245, 255, 255)), (0, 0), rim.point(lambda v: int(v * 0.8)))
    img.alpha_composite(rc)
    # analog kolu
    def stick(cx, cy, rr):
        fell(img, (cx - rr * 1.2, cy - rr * 1.2, cx + rr * 1.2, cy + rr * 1.2), (0, 0, 0), alpha=0.5)
        fell_rad(img, (cx - rr, cy - rr, cx + rr, cy + rr), mix(color, INK, 0.45), mix(color, INK, 0.88), (0.4, 0.3))
        stroke(img, "ell", (cx - rr * 0.62, cy - rr * 0.62, cx + rr * 0.62, cy + rr * 0.62), WHITE, max(2, rr * 0.08), 0.28)
        stroke(img, "ell", (cx - rr, cy - rr, cx + rr, cy + rr), WHITE, max(2, rr * 0.06), 0.5)
    stick(X0 + w * 0.3, Y0 + h * 0.44, w * 0.058)
    stick(X0 + w * 0.62, Y0 + h * 0.62, w * 0.058)
    # d-pad
    cx, cy = X0 + w * 0.43, Y0 + h * 0.62
    a, b = w * 0.016, w * 0.05
    for bx in ((cx - b, cy - a, cx + b, cy + a), (cx - a, cy - b, cx + a, cy + b)):
        frr(img, bx, w * 0.008, mix(color, INK, 0.5), mix(color, INK, 0.8), angle=90)
    # dort dugme
    bc = (X0 + w * 0.75, Y0 + h * 0.36)
    for i, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        x, y = bc[0] + dx * w * 0.052, bc[1] + dy * w * 0.052
        rr = w * 0.03
        col = [shade(color, 1.8), shade(color, 1.5), shade(color, 1.2), shade(color, 1.65)][i]
        glow = new_layer(img.size)
        fell(glow, (x - rr * 1.5, y - rr * 1.5, x + rr * 1.5, y + rr * 1.5), col, alpha=0.5)
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(rr * 0.8)))
        fell_rad(img, (x - rr, y - rr, x + rr, y + rr), mix(col, WHITE, 0.4), col, (0.4, 0.3))
    # orta dugmeler
    for dx in (-1, 1):
        frr(img, (X0 + w * 0.5 + dx * w * 0.06 - w * 0.016, Y0 + h * 0.26, X0 + w * 0.5 + dx * w * 0.06 + w * 0.016, Y0 + h * 0.3), w * 0.008, mix(color, INK, 0.5), mix(color, INK, 0.8))
    # tetik cizgisi
    for sg in (-1, 1):
        cxt = X0 + w * (0.5 + sg * 0.28)
        frr(img, (cxt - w * 0.1, Y0 + h * 0.07, cxt + w * 0.1, Y0 + h * 0.1), w * 0.015, shade(color, 1.3), shade(color, 0.8), alpha=0.8)
    return img


def vinyl_piece(r, color):
    w = int(2 * r) + 8
    img = new_layer((w, w))
    c = w / 2
    fell_rad(img, (4, 4, w - 4, w - 4), (46, 48, 54), (8, 9, 12), (0.5, 0.5), radius=0.75)
    for i in range(14):
        rr = r * (0.34 + i * 0.045)
        stroke(img, "ell", (c - rr, c - rr, c + rr, c + rr), WHITE, max(1, r * 0.004), 0.05 + 0.04 * (i % 3))
    # konik parlama
    gl = new_layer(img.size)
    for ang in (35, 215):
        a0, a1 = math.radians(ang - 14), math.radians(ang + 14)
        pts = [(c, c)] + [(c + r * 0.98 * math.cos(a0 + (a1 - a0) * k / 12), c + r * 0.98 * math.sin(a0 + (a1 - a0) * k / 12)) for k in range(13)]
        fpoly(gl, pts, WHITE, WHITE, alpha=0.2)
    gl = gl.filter(ImageFilter.GaussianBlur(r * 0.02))
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse((4, 4, w - 4, w - 4), fill=255)
    gl.putalpha(ImageChops.multiply(gl.getchannel("A"), m))
    img.alpha_composite(gl)
    lab = r * 0.3
    fell_rad(img, (c - lab, c - lab, c + lab, c + lab), shade(color, 1.5), shade(color, 0.7), (0.35, 0.3))
    for i in range(3):
        k = lab * (0.35 + 0.18 * i)
        stroke(img, "arc", ((c - k, c - k, c + k, c + k), 200 + i * 40, 320 + i * 40), WHITE, max(2, r * 0.012), 0.5)
    fell(img, (c - r * 0.03, c - r * 0.03, c + r * 0.03, c + r * 0.03), (10, 10, 14))
    stroke(img, "ell", (4, 4, w - 4, w - 4), WHITE, max(2, r * 0.012), 0.25)
    return img


def soccer_piece(r, color):
    w = int(2 * r) + 8
    img = new_layer((w, w))
    c = w / 2
    fell_rad(img, (4, 4, w - 4, w - 4), (255, 255, 255), (150, 170, 160), (0.36, 0.3), radius=0.9)
    pm = Image.new("L", img.size, 0)
    ImageDraw.Draw(pm).ellipse((4, 4, w - 4, w - 4), fill=255)
    dk = new_layer(img.size)
    ink = mix(color, INK, 0.8)
    def pent(cx, cy, rr, a0):
        return [(cx + rr * math.cos(a0 + i * 2 * math.pi / 5), cy + rr * math.sin(a0 + i * 2 * math.pi / 5)) for i in range(5)]
    cp = pent(c - r * 0.1, c - r * 0.08, r * 0.3, -math.pi / 2)
    fpoly(dk, cp, ink, mix(ink, WHITE, 0.15), angle=60)
    for i, p in enumerate(cp):
        ang = math.atan2(p[1] - (c - r * 0.08), p[0] - (c - r * 0.1))
        q = (p[0] + math.cos(ang) * r * 0.32, p[1] + math.sin(ang) * r * 0.32)
        stroke(dk, "line", [p, q], ink, r * 0.035, 0.9)
        op = pent(q[0] + math.cos(ang) * r * 0.22, q[1] + math.sin(ang) * r * 0.22, r * 0.27, ang + math.pi)
        fpoly(dk, op, ink, mix(ink, WHITE, 0.1), angle=60)
    dk.putalpha(ImageChops.multiply(dk.getchannel("A"), pm))
    img.alpha_composite(dk)
    sh = rad_img(img.size, (0.34, 0.28), (255, 255, 255), (0, 0, 0), r * 1.6, 1.1)
    sh.putalpha(ImageChops.multiply(pm, Image.new("L", img.size, 80)))
    sh2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dark = rad_img(img.size, (0.34, 0.28), (255, 255, 255), (0, 0, 0), r * 1.5, 1.3)
    dark_a = np.array(dark.convert("L"), dtype=np.float32)
    alpha = np.clip((255 - dark_a) * 0.5, 0, 140).astype(np.uint8)
    sh2 = Image.new("RGBA", img.size, (0, 10, 20, 0))
    sh2.putalpha(ImageChops.multiply(Image.fromarray(alpha), pm))
    img.alpha_composite(sh2)
    return img


# --------------------------------------------------------------------------- temalar
# Her tema: paint(L, cx, cy, S, pal, rnd, mode). S = kume yaricapi (piksel, supersampled).


def decor(L, cx, cy, S, pal, rnd, n=14, spread=1.25):
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        d = S * rnd.uniform(0.7, spread * 1.25)
        x, y = cx + math.cos(a) * d * 1.25, cy + math.sin(a) * d * 0.85
        r = S * rnd.uniform(0.012, 0.035)
        kind = rnd.random()
        if kind < 0.18:
            sparkle(L, x, y, S * rnd.uniform(0.07, 0.15), mix(pal.pale, WHITE, 0.5), 0.9)
        else:
            glow_dot(L, x, y, r * 1.6, mix(pal.hi, WHITE, 0.4), rnd.uniform(0.4, 0.8))


def layer_flat(w, color, alpha=1.0, bolt=False):
    pad = 6
    img = new_layer((w + 2 * pad, w + 2 * pad))
    box = (pad, pad, pad + w, pad + w)
    r = int(w * 0.17)
    frr(img, box, r, shade(color, 1.3), shade(color, 0.6), angle=40, alpha=alpha)
    gl = new_layer(img.size)
    fpoly(gl, [(pad, pad), (pad + w * 0.7, pad), (pad, pad + w * 0.7)], WHITE, WHITE, alpha=0.14)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    gl.putalpha(ImageChops.multiply(gl.getchannel("A"), m))
    img.alpha_composite(gl)
    stroke(img, "rr", (box, r), WHITE, max(2, w * 0.012), 0.6)
    inner = (pad + w * 0.1, pad + w * 0.1, pad + w * 0.9, pad + w * 0.9)
    stroke(img, "rr", (inner, int(r * 0.6)), WHITE, max(1, w * 0.007), 0.22)
    if bolt:
        c = pad + w / 2
        pts = [(c + 0.1 * w, c - 0.3 * w), (c - 0.17 * w, c + 0.04 * w), (c - 0.015 * w, c + 0.04 * w), (c - 0.1 * w, c + 0.3 * w), (c + 0.17 * w, c - 0.06 * w), (c + 0.015 * w, c - 0.06 * w)]
        g = new_layer(img.size)
        fpoly(g, pts, WHITE, WHITE, alpha=0.95)
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(w * 0.03)))
        fpoly(img, pts, WHITE, mix(color, WHITE, 0.6), angle=60)
    return img


def iso_flat(img, squash=0.52, thick=0.0):
    r = rot(img, 45)
    return r.resize((r.width, max(2, int(r.height * squash))), Image.LANCZOS)


def t_cardstack(L, cx, cy, S, pal, rnd, mode):
    # sunucu boost katmanlari: ucu uca bindirilmis cam katmanlar + isik huzmesi
    beam = new_layer(L.size)
    fpoly(beam, [(cx - S * 0.5, cy + S * 0.9), (cx + S * 0.5, cy + S * 0.9), (cx + S * 0.25, cy - S * 1.5), (cx - S * 0.25, cy - S * 1.5)], pal.hi, pal.c, angle=90, alpha=0.2)
    L.alpha_composite(beam.filter(ImageFilter.GaussianBlur(S * 0.2)))
    specs = [(0.78, pal.deep, 0.9, False, 1.0), (0.3, pal.c, 0.93, False, 1.1), (-0.2, pal.hi, 0.97, True, 1.2)]
    for dy, col, a, bolt, sz in specs:
        lf = iso_flat(layer_flat(int(S * 1.55 * sz), col, a, bolt))
        # yan kalinlik
        th = int(S * 0.07)
        sd = new_layer((lf.width, lf.height + th))
        dk = Image.new("RGBA", lf.size, tuple(clampc(shade(col, 0.45))) + (255,))
        dk.putalpha(lf.getchannel("A"))
        for k in range(th, 0, -2):
            sd.alpha_composite(dk, (0, k))
        sd.alpha_composite(lf, (0, 0))
        blit(L, sd, cx, cy + dy * S, shadow=0.45, glow=(pal.c, 0.45, 0.06) if bolt else None)
    for k in range(3):
        y = cy - S * (1.0 + k * 0.2)
        w = S * (0.32 - k * 0.05)
        pts = [(cx - w, y + w * 0.6), (cx, y), (cx + w, y + w * 0.6)]
        stroke(L, "line", pts, mix(pal.pale, WHITE, 0.5), S * 0.055, 0.95 - k * 0.3)
    for dx, dy, rr in ((-1.1, -0.35, 0.16), (1.15, -0.1, 0.2)):
        sparkle(L, cx + dx * S, cy + dy * S, S * rr, WHITE, 0.95)
    decor(L, cx, cy, S, pal, rnd, 12)


def t_wallet(L, cx, cy, S, pal, rnd, mode):
    back = card_piece(int(S * 1.85), int(S * 1.17), pal.deep, "plain", alpha=0.9)
    blit(L, rot(back, 14), cx + S * 0.45, cy - S * 0.42, shadow=0.5)
    cd = card_piece(int(S * 2.1), int(S * 1.32), pal.c, "wallet", alpha=0.98)
    cd = persp(rot(cd, -9), 0.0, 0.06)
    blit(L, cd, cx - S * 0.05, cy + S * 0.1, shadow=0.6, glow=(pal.c, 0.5, 0.06))
    for (dx, dy, rr, e) in ((0.95, 0.72, 0.24, "bolt"), (-0.95, 0.88, 0.17, "ring"), (1.1, -0.85, 0.15, "star")):
        pc = coin_piece(S * rr, mix(pal.hi, (255, 200, 80), 0.88), 0.42, 0.14, e)
        blit(L, rot(pc, rnd.uniform(-15, 15)), cx + dx * S, cy + dy * S, shadow=0.5)
    decor(L, cx, cy, S, pal, rnd, 12)


def t_cubes(L, cx, cy, S, pal, rnd, mode):
    spec = [(0.0, 0.42, 0.62, 0, pal.c), (-0.78, 0.2, 0.5, 1, mix(pal.c, pal.acc, 0.4)), (0.82, 0.18, 0.52, 2, mix(pal.c, WHITE, 0.15)),
            (0.1, -0.48, 0.5, 3, shade(pal.c, 1.12))]
    for dx, dy, sz, sd, col in spec:
        cp = cube_piece(S * sz, col, grid=2, noise=0.0, seed=sd)
        blit(L, rot(cp, rnd.uniform(-4, 4)), cx + dx * S, cy + dy * S, shadow=0.55, glow=(pal.c, 0.35, 0.05))
    # yuzen mini kupler
    for dx, dy, sz in ((-1.2, -0.7, 0.16), (1.25, -0.55, 0.13), (-0.2, -1.1, 0.1), (1.0, 0.95, 0.14)):
        cp = cube_piece(S * sz, mix(pal.hi, WHITE, 0.2), grid=1)
        blit(L, rot(cp, rnd.uniform(-20, 20)), cx + dx * S, cy + dy * S, shadow=0.4)
    decor(L, cx, cy, S, pal, rnd, 10)


def t_shards(L, cx, cy, S, pal, rnd, mode):
    # arkada keskin capraz seritler
    bg = new_layer(L.size)
    for k, (dx, w, a) in enumerate(((-0.9, 0.09, 0.22), (-0.55, 0.03, 0.3), (0.9, 0.16, 0.16), (1.2, 0.04, 0.3))):
        x = cx + dx * S
        pts = [(x - S * w, cy + S * 1.4), (x + S * w, cy + S * 1.4), (x + S * w + S * 0.85, cy - S * 1.4), (x - S * w + S * 0.85, cy - S * 1.4)]
        fpoly(bg, pts, pal.hi, pal.c, angle=90, alpha=a)
    L.alpha_composite(bg)
    spec = [(0.0, 0.05, 1.05, 0.62, 8, pal.c), (-0.78, 0.32, 0.72, 0.45, -18, shade(pal.c, 0.85)), (0.82, 0.3, 0.78, 0.5, 20, mix(pal.c, WHITE, 0.15)),
            (-1.25, 0.65, 0.4, 0.3, -30, pal.acc), (1.3, 0.7, 0.42, 0.3, 32, pal.acc2)]
    for dx, dy, hh, ww, ang, col in spec:
        g = gem_piece(S * hh, col, "shard", sx=ww / hh)
        blit(L, rot(g, ang), cx + dx * S, cy + dy * S, shadow=0.55, glow=(pal.c, 0.45, 0.06))
    decor(L, cx, cy, S, pal, rnd, 12)


def t_coins(L, cx, cy, S, pal, rnd, mode):
    gold = mix(pal.c, (255, 200, 60), 0.35)
    layout = [(-0.78, 0.42, 4, 0.45), (0.0, 0.35, 6, 0.55), (0.82, 0.45, 3, 0.42)]
    for dx, dy, n, rr in layout:
        st = stack_coins(S * rr, gold, n, 0.4, "cross", 0.22)
        blit(L, st, cx + dx * S, cy + dy * S + (0.55 - rr) * S * 0.2 - (n * rr * S * 0.08), shadow=0.55, glow=(gold, 0.3, 0.05))
    top = coin_piece(S * 0.38, mix(gold, WHITE, 0.15), 0.9, 0.16, "cross")
    blit(L, rot(top, -22), cx + S * 0.05, cy - S * 0.98, shadow=0.5, glow=(gold, 0.45, 0.06))
    dot = coin_piece(S * 0.17, gold, 0.9, 0.2, "ring")
    blit(L, rot(dot, 18), cx - S * 1.15, cy - S * 0.55, shadow=0.45)
    blit(L, rot(dot, -12), cx + S * 1.2, cy - S * 0.35, shadow=0.45)
    decor(L, cx, cy, S, pal, rnd, 12)


def sphere_piece(r, color):
    w = int(2 * r) + 8
    img = new_layer((w, w))
    c = w / 2
    fell_rad(img, (4, 4, w - 4, w - 4), shade(color, 1.6), shade(color, 0.45), (0.34, 0.28), radius=0.95)
    # alt yansima
    t = new_layer(img.size)
    fell(t, (c - r * 0.7, c + r * 0.45, c + r * 0.7, c + r * 0.95), shade(color, 1.8), alpha=0.35)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse((4, 4, w - 4, w - 4), fill=255)
    t = t.filter(ImageFilter.GaussianBlur(r * 0.07))
    t.putalpha(ImageChops.multiply(t.getchannel("A"), m))
    img.alpha_composite(t)
    fell(img, (c - r * 0.55, c - r * 0.7, c - r * 0.05, c - r * 0.38), WHITE, alpha=0.55)
    stroke(img, "ell", (4, 4, w - 4, w - 4), WHITE, max(2, r * 0.02), 0.35)
    return img


def t_orbs(L, cx, cy, S, pal, rnd, mode):
    # yorungeler
    for rx, ry, a, wd in ((1.35, 0.42, -18, 0.012), (1.15, 0.3, 24, 0.008)):
        t = new_layer(L.size)
        stroke(t, "ell", (cx - rx * S, cy - ry * S, cx + rx * S, cy + ry * S), pal.hi, S * wd, 0.55)
        # dondur
        t2 = t.rotate(a, resample=Image.BICUBIC, center=(cx, cy))
        L.alpha_composite(t2)
    g = gem_piece(S * 0.82, pal.c, "oct", sx=0.9)
    blit(L, g, cx, cy, shadow=0.55, glow=(pal.c, 0.6, 0.07))
    for dx, dy, rr, col in ((-1.0, -0.4, 0.3, pal.acc), (1.05, 0.35, 0.36, pal.hi), (0.55, -0.92, 0.2, pal.acc2), (-0.78, 0.7, 0.22, pal.hi)):
        sp = sphere_piece(S * rr, col)
        blit(L, sp, cx + dx * S, cy + dy * S, shadow=0.45, glow=(col, 0.4, 0.06))
    sg = gem_piece(S * 0.2, pal.pale, "brilliant")
    blit(L, rot(sg, 20), cx + S * 1.25, cy - S * 0.5, shadow=0.4)
    decor(L, cx, cy, S, pal, rnd, 14)


def t_flamegems(L, cx, cy, S, pal, rnd, mode):
    c1 = (255, 150, 30)
    c2 = (255, 70, 10)
    for dx, sc, a in ((0.0, 1.0, 0), (-0.8, 0.6, -10), (0.85, 0.66, 8)):
        f = flame_piece(S * 0.8 * sc, (255, 215, 90), c2)
        blit(L, rot(f, a), cx + dx * S, cy - S * (0.55 - (1 - sc) * 0.5) - (0 if dx == 0 else -S * 0.25), shadow=0, glow=(c1, 0.8, 0.09))
    for dx, dy, r, sx in ((0.0, 0.35, 0.78, 1.0), (-0.85, 0.65, 0.5, 1.0), (0.9, 0.62, 0.52, 1.0), (-0.35, 0.98, 0.36, 1.0), (0.4, 1.0, 0.34, 1.0)):
        g = gem_piece(S * r, mix(pal.c, (255, 120, 20), 0.2), "brilliant", sx=sx)
        blit(L, rot(g, rnd.uniform(-8, 8)), cx + dx * S, cy + dy * S, shadow=0.55, glow=(c1, 0.35, 0.05))
    # kivilcimlar
    for i in range(16):
        x = cx + rnd.uniform(-1.3, 1.3) * S
        y = cy - rnd.uniform(0.2, 1.6) * S
        glow_dot(L, x, y, S * rnd.uniform(0.012, 0.03), (255, rnd.randint(150, 220), 70), rnd.uniform(0.5, 0.95))


def t_shield(L, cx, cy, S, pal, rnd, mode):
    for rr, a in ((1.45, 0.12), (1.15, 0.2)):
        stroke(L, "ell", (cx - S * rr, cy - S * rr * 0.98, cx + S * rr, cy + S * rr * 0.98), pal.hi, S * 0.012, a)
    sh = shield_piece(S * 0.85, pal.c)
    blit(L, sh, cx, cy, shadow=0.6, glow=(pal.c, 0.55, 0.07))
    g = gem_piece(S * 0.42, mix(pal.hi, WHITE, 0.25), "brilliant")
    blit(L, g, cx, cy + S * 0.02, shadow=0.45, glow=(pal.hi, 0.5, 0.06))
    for dx, dy, r, a in ((-1.05, -0.5, 0.26, -15), (1.1, -0.35, 0.3, 14), (-0.95, 0.65, 0.2, 10), (1.0, 0.7, 0.22, -12)):
        gg = gem_piece(S * r, pal.acc if dx < 0 else pal.hi, "brilliant")
        blit(L, rot(gg, a), cx + dx * S, cy + dy * S, shadow=0.5, glow=(pal.c, 0.4, 0.06))
    decor(L, cx, cy, S, pal, rnd, 12)


def t_crystals(L, cx, cy, S, pal, rnd, mode):
    for rr, a, ang in ((1.4, 0.28, -25), (1.1, 0.22, 20)):
        t = new_layer(L.size)
        stroke(t, "ell", (cx - rr * S, cy - rr * S * 0.34, cx + rr * S, cy + rr * S * 0.34), WHITE, S * 0.01, a)
        L.alpha_composite(t.rotate(ang, resample=Image.BICUBIC, center=(cx, cy)))
    spec = [(0.0, -0.05, 1.18, 0.38, 0, pal.hi), (-0.62, 0.3, 0.82, 0.3, -17, pal.c), (0.62, 0.28, 0.9, 0.32, 15, mix(pal.c, WHITE, 0.2)),
            (-1.05, 0.55, 0.5, 0.2, -30, pal.acc), (1.1, 0.6, 0.52, 0.22, 28, pal.acc2)]
    for dx, dy, hh, ww, ang, col in spec:
        g = gem_piece(S * hh, col, "shard", sx=ww / hh)
        blit(L, rot(g, ang), cx + dx * S, cy + dy * S, shadow=0.5, glow=(pal.c, 0.5, 0.07))
    for dx, dy, r in ((-1.1, -0.8, 0.22), (1.15, -0.65, 0.18), (0.3, -1.25, 0.16), (-0.35, 1.2, 0.12)):
        sparkle(L, cx + dx * S, cy + dy * S, S * r, WHITE, 0.95)
    decor(L, cx, cy, S, pal, rnd, 8)


def t_voxels(L, cx, cy, S, pal, rnd, mode):
    cols = [pal.c, mix(pal.c, (200, 160, 90), 0.4), shade(pal.c, 0.8)]
    spec = [(0.0, 0.55, 0.5, 0), (-0.74, 0.8, 0.5, 1), (0.74, 0.8, 0.5, 2), (0.0, 0.0, 0.5, 0), (-0.38, 0.37, 0.5, 2)]
    # alttan uste, arkadan one
    spec = [(-0.74, 0.55, 0.43, 1), (0.74, 0.55, 0.43, 2), (0.0, 0.8, 0.43, 0), (0.0, 0.17, 0.43, 2), (-0.37, 0.38, 0.43, 0)]
    spec.sort(key=lambda t: t[1])
    for dx, dy, sz, i in spec:
        cp = cube_piece(S * sz, cols[i % 3], grid=4, noise=0.2, seed=int(dx * 10) + i)
        blit(L, cp, cx + dx * S, cy + dy * S - S * 0.15, shadow=0.55, glow=(pal.c, 0.35, 0.05))
    for dx, dy, sz in ((-1.2, -0.55, 0.14), (1.15, -0.35, 0.16), (0.6, -1.05, 0.1), (-0.5, -1.1, 0.12), (1.3, 0.75, 0.1)):
        cp = cube_piece(S * sz, mix(pal.hi, WHITE, 0.1), grid=2, noise=0.15, seed=int(dy * 7))
        blit(L, rot(cp, rnd.uniform(-25, 25)), cx + dx * S, cy + dy * S, shadow=0.4)
    decor(L, cx, cy, S, pal, rnd, 8)


def hexgrid_lines(L, cx, cy, S, pal, size, rows, cols_, alpha=0.2):
    for i in range(-cols_, cols_ + 1):
        for j in range(-rows, rows + 1):
            x = cx + i * size * 1.5
            y = cy + j * size * math.sqrt(3) + (size * math.sqrt(3) / 2 if i % 2 else 0)
            pts = [(x + size * math.cos(math.pi / 3 * k), y + size * math.sin(math.pi / 3 * k)) for k in range(6)]
            d = math.hypot(x - cx, y - cy) / (S * 1.6)
            a = alpha * max(0, 1 - d)
            if a > 0.01:
                stroke(L, "poly", [v for p in pts for v in p], pal.hi, max(1, S * 0.006), a)


def t_hexcoins(L, cx, cy, S, pal, rnd, mode):
    gold = mix(pal.c, (240, 190, 90), 0.2)
    hexgrid_lines(L, cx, cy, S, pal, S * 0.28, 4, 5, 0.28)
    big = stack_coins(S * 0.62, gold, 4, 0.42, "hex", 0.2)
    blit(L, big, cx, cy + S * 0.15, shadow=0.55, glow=(gold, 0.4, 0.06))
    top = coin_piece(S * 0.48, mix(gold, WHITE, 0.12), 0.85, 0.16, "hex")
    blit(L, rot(top, -16), cx + S * 0.1, cy - S * 0.9, shadow=0.5, glow=(gold, 0.5, 0.07))
    for dx, dy, r, a in ((-1.15, 0.5, 0.26, -14), (1.2, 0.3, 0.3, 12)):
        cc = coin_piece(S * r, gold, 0.85, 0.16, "hex")
        blit(L, rot(cc, a), cx + dx * S, cy + dy * S, shadow=0.45)
    g = gem_piece(S * 0.22, pal.hi, "hex")
    blit(L, g, cx - S * 1.0, cy - S * 0.75, shadow=0.4, glow=(pal.c, 0.4, 0.05))
    decor(L, cx, cy, S, pal, rnd, 10)


def chamfer(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def t_plates(L, cx, cy, S, pal, rnd, mode):
    steel = (140, 170, 220)
    # arkadan isik huzmesi
    bm = new_layer(L.size)
    fpoly(bm, [(cx + S * 0.2, cy - S * 1.6), (cx + S * 0.9, cy - S * 1.6), (cx + S * 0.1, cy + S * 1.2), (cx - S * 0.9, cy + S * 1.2)], WHITE, steel, angle=90, alpha=0.12)
    L.alpha_composite(bm.filter(ImageFilter.GaussianBlur(S * 0.05)))
    specs = [(0.42, -0.5, 1.45, 0.95, 0.5), (0.2, -0.12, 1.65, 1.05, 0.75), (-0.05, 0.32, 1.85, 1.15, 1.0)]
    for i, (dx, dy, w, h, tone) in enumerate(specs):
        pw, ph = int(S * w), int(S * h)
        pad = 6
        img = new_layer((pw + 2 * pad, ph + 2 * pad))
        pts = chamfer(pad, pad, pad + pw, pad + ph, int(ph * 0.22))
        fpoly(img, pts, mix(shade(pal.c, 1.45), steel, 0.12 * tone), shade(pal.c, 0.42 + 0.2 * tone), angle=40)
        stroke(img, "poly", [v for p in pts for v in p], WHITE, max(2, S * 0.014), 0.6)
        inner = chamfer(pad + pw * 0.05, pad + ph * 0.09, pad + pw * 0.95, pad + ph * 0.91, int(ph * 0.17))
        stroke(img, "poly", [v for p in inner for v in p], steel, max(1, S * 0.01), 0.45)
        fpoly(img, [(pad + pw * 0.15, pad), (pad + pw * 0.42, pad), (pad + pw * 0.1, pad + ph), (pad, pad + ph)], WHITE, WHITE, alpha=0.1)
        if i == 2:
            for g in range(4):
                for d in range(3):
                    x = pad + pw * 0.1 + g * pw * 0.2 + d * ph * 0.07
                    y = pad + ph * 0.62
                    fpoly(img, chamfer(x, y, x + ph * 0.05, y + ph * 0.05, 1), WHITE, WHITE, alpha=0.9)
            sparkle(img, pad + pw * 0.1 + ph * 0.14, pad + ph * 0.29, ph * 0.2, WHITE, 0.95)
            frr(img, (pad + pw * 0.62, pad + ph * 0.8, pad + pw * 0.9, pad + ph * 0.83), 2, steel, steel, alpha=0.9)
        blit(L, rot(img, -5), cx + dx * S, cy + dy * S, shadow=0.55, glow=(steel, 0.3, 0.05) if i == 2 else None)
    for dx, dy, rr in ((1.1, -0.95, 0.22), (-1.05, 0.5, 0.15)):
        sparkle(L, cx + dx * S, cy + dy * S, S * rr, WHITE, 0.95)
    decor(L, cx, cy, S, pal, rnd, 10)


def t_vortex(L, cx, cy, S, pal, rnd, mode):
    for i, rr in enumerate((1.35, 1.12, 0.9, 0.7, 0.5)):
        a0 = rnd.uniform(0, 360)
        for seg in range(3):
            s0 = a0 + seg * 120 + 8
            stroke(L, "arc", ((cx - rr * S, cy - rr * S * 0.9, cx + rr * S, cy + rr * S * 0.9), s0, s0 + 80 - i * 6), mix(pal.hi, WHITE, i * 0.08), S * (0.022 + 0.004 * i), 0.9 - i * 0.08)
        glow = new_layer(L.size)
        stroke(glow, "ell", (cx - rr * S, cy - rr * S * 0.9, cx + rr * S, cy + rr * S * 0.9), pal.c, S * 0.03, 0.25)
        L.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S * 0.02)))
    core = sphere_piece(S * 0.34, pal.hi)
    blit(L, core, cx, cy, shadow=0.0, glow=(pal.c, 0.9, 0.12))
    sparkle(L, cx, cy, S * 0.34, WHITE, 0.95)
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.5, 1.45)
        glow_dot(L, cx + math.cos(a) * rr * S, cy + math.sin(a) * rr * S * 0.9, S * rnd.uniform(0.014, 0.03), pal.pale, rnd.uniform(0.5, 0.9))


def t_soccer(L, cx, cy, S, pal, rnd, mode):
    # saha cizgileri
    for rr, a in ((1.4, 0.18), (1.05, 0.12)):
        stroke(L, "ell", (cx - S * rr, cy - S * rr * 0.4, cx + S * rr, cy + S * rr * 0.4), WHITE, S * 0.012, a)
    # hareket yaylari
    for k in range(4):
        rr = 1.0 + k * 0.1
        stroke(L, "arc", ((cx - S * rr, cy - S * rr, cx + S * rr, cy + S * rr), 195 + k * 4, 250 - k * 4), pal.hi, S * (0.03 - 0.006 * k), 0.5 - k * 0.1)
    ball = soccer_piece(S * 0.74, pal.c)
    blit(L, ball, cx + S * 0.05, cy - S * 0.05, shadow=0.55, glow=(pal.c, 0.45, 0.07))
    # zemin golgesi
    sh = new_layer(L.size)
    fell(sh, (cx - S * 0.7, cy + S * 0.72, cx + S * 0.8, cy + S * 0.9), (0, 0, 0), alpha=0.5)
    comp(L, sh.filter(ImageFilter.GaussianBlur(S * 0.07)), 0, 0)
    for dx, dy, r in ((-1.1, 0.6, 0.2), (1.15, -0.55, 0.22)):
        cc = coin_piece(S * r, mix(pal.hi, (255, 200, 80), 0.88), 0.85, 0.16, "star")
        blit(L, rot(cc, rnd.uniform(-18, 18)), cx + dx * S, cy + dy * S, shadow=0.45)
    decor(L, cx, cy, S, pal, rnd, 10)


def t_gamepad(L, cx, cy, S, pal, rnd, mode):
    for rr, a in ((1.4, 0.14), (1.1, 0.18)):
        stroke(L, "ell", (cx - S * rr, cy - S * rr * 0.75, cx + S * rr, cy + S * rr * 0.75), pal.hi, S * 0.01, a)
    cp = controller_piece(int(S * 2.35), pal.c)
    blit(L, rot(cp, -7), cx, cy + S * 0.05, shadow=0.6, glow=(pal.c, 0.5, 0.07))
    # kucuk yuzen dugmeler
    for dx, dy, r, col in ((-1.1, -0.75, 0.12, pal.acc), (1.18, -0.6, 0.15, pal.hi), (-1.25, 0.65, 0.1, pal.hi), (1.2, 0.72, 0.12, pal.acc2)):
        glow_dot(L, cx + dx * S, cy + dy * S, S * r * 0.6, col, 0.9)
    decor(L, cx, cy, S, pal, rnd, 10)


PIX_HEART = ["01100110", "11111111", "11111111", "11111111", "01111110", "00111100", "00011000"]
PIX_STAR = ["000010000", "000111000", "111111111", "011111110", "001111100", "011101110", "010000010"]
PIX_COIN = ["0011100", "0111110", "1111111", "1111111", "1111111", "0111110", "0011100"]
PIX_GEM = ["00111100", "01111110", "11111111", "01111110", "00111100", "00011000"]


def pixel_piece(bmp, p, color, hi=True):
    h, w = len(bmp), len(bmp[0])
    img = new_layer((w * p + 4, h * p + 4))
    for y, row in enumerate(bmp):
        for x, v in enumerate(row):
            if v == "1":
                x0, y0 = 2 + x * p, 2 + y * p
                frr(img, (x0, y0, x0 + p - 1, y0 + p - 1), 0, shade(color, 1.3), shade(color, 0.8), angle=60)
                if hi and y % 3 == 0 and x % 2 == 0:
                    fpoly(img, [(x0, y0), (x0 + p * 0.45, y0), (x0, y0 + p * 0.45)], WHITE, WHITE, alpha=0.3)
    return img


def t_pixels(L, cx, cy, S, pal, rnd, mode):
    pxs = S * 0.1
    spec = [(PIX_HEART, 0.0, 0.0, 1.6, pal.c), (PIX_STAR, -1.0, -0.65, 0.95, (255, 205, 60)), (PIX_COIN, 1.05, -0.35, 1.0, (255, 205, 60)),
            (PIX_GEM, 0.95, 0.8, 0.9, pal.acc2), (PIX_STAR, -0.9, 0.7, 0.6, pal.hi), (PIX_HEART, 0.45, -1.0, 0.55, pal.hi)]
    # ince piksel izgara zemini
    for k in range(-5, 6):
        x = cx + k * S * 0.22
        stroke(L, "line", [(x, cy + S * 1.05), (x, cy + S * 1.45)], pal.hi, 1.5 * SS, 0.12)
    for bmp, dx, dy, sc, col in spec:
        pc = pixel_piece(bmp, max(3, int(pxs * sc)), col)
        blit(L, pc, cx + dx * S, cy + dy * S, shadow=0.5, glow=(col, 0.4, 0.04))
    decor(L, cx, cy, S, pal, rnd, 8)


def t_cinema(L, cx, cy, S, pal, rnd, mode):
    # sinematik kirmizi seritler
    rb = new_layer(L.size)
    for k, (off, a, wd) in enumerate(((-0.55, 0.4, 0.34), (-0.1, 0.55, 0.26), (0.4, 0.4, 0.3))):
        pts = []
        for i in range(0, 41):
            t = i / 40
            x = cx + (-1.5 + 3.0 * t) * S
            y = cy + off * S + math.sin(t * 5 + k * 1.3) * S * 0.28 - S * 0.5 * t
            pts.append((x, y))
        up = [(x, y - wd * S * 0.5) for x, y in pts]
        dn = [(x, y + wd * S * 0.5) for x, y in pts]
        fpoly(rb, up + dn[::-1], pal.hi, pal.deep, angle=90, alpha=a * 0.6)
    L.alpha_composite(rb.filter(ImageFilter.GaussianBlur(S * 0.012)))
    # cam ekran
    sw, sh_ = int(S * 2.05), int(S * 1.3)
    pad = 8
    img = new_layer((sw + 2 * pad, sh_ + 2 * pad))
    box = (pad, pad, pad + sw, pad + sh_)
    frr(img, box, sh_ * 0.07, mix(pal.c, INK, 0.35), mix(pal.c, INK, 0.8), angle=50)
    for i in range(0, 8):  # film perforasyonu
        for yy in (pad + sh_ * 0.04, pad + sh_ * 0.93):
            x = pad + sw * (0.05 + i * 0.123)
            frr(img, (x, yy, x + sw * 0.05, yy + sh_ * 0.03), 3, (10, 10, 14), (10, 10, 14), alpha=0.8)
    glow = new_layer(img.size)
    fell(glow, (pad + sw * 0.5 - sh_ * 0.4, pad + sh_ * 0.5 - sh_ * 0.4, pad + sw * 0.5 + sh_ * 0.4, pad + sh_ * 0.5 + sh_ * 0.4), pal.hi, alpha=0.5)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(sh_ * 0.14)))
    tri = [(pad + sw * 0.5 - sh_ * 0.15, pad + sh_ * 0.5 - sh_ * 0.22), (pad + sw * 0.5 - sh_ * 0.15, pad + sh_ * 0.5 + sh_ * 0.22), (pad + sw * 0.5 + sh_ * 0.24, pad + sh_ * 0.5)]
    fpoly(img, tri, WHITE, mix(pal.pale, WHITE, 0.4), angle=0)
    frr(img, (pad + sw * 0.08, pad + sh_ * 0.82, pad + sw * 0.92, pad + sh_ * 0.835), 2, WHITE, WHITE, alpha=0.25)
    frr(img, (pad + sw * 0.08, pad + sh_ * 0.82, pad + sw * 0.5, pad + sh_ * 0.835), 2, pal.hi, pal.hi, alpha=0.95)
    stroke(img, "rr", (box, sh_ * 0.07), WHITE, max(2, S * 0.012), 0.55)
    gl = new_layer(img.size)
    fpoly(gl, [(pad + sw * 0.1, pad), (pad + sw * 0.4, pad), (pad + sw * 0.15, pad + sh_), (pad - sw * 0.1, pad + sh_)], WHITE, WHITE, alpha=0.09)
    img.alpha_composite(gl)
    blit(L, persp(rot(img, -6), 0.0, 0.0), cx, cy + S * 0.05, shadow=0.6, glow=(pal.c, 0.55, 0.07))
    decor(L, cx, cy, S, pal, rnd, 10)


def t_vinyl(L, cx, cy, S, pal, rnd, mode):
    for k in range(4):
        rr = 1.05 + k * 0.17
        stroke(L, "arc", ((cx + S * 0.3 - rr * S, cy - rr * S, cx + S * 0.3 + rr * S, cy + rr * S), -38, 38), pal.hi, S * (0.03 - 0.005 * k), 0.55 - 0.1 * k)
    v = vinyl_piece(S * 0.95, pal.c)
    blit(L, v, cx + S * 0.2, cy, shadow=0.6, glow=(pal.c, 0.5, 0.06))
    # ekolayzer cubuklari
    heights = [0.5, 0.9, 0.65, 1.2, 0.8, 0.55, 0.95]
    bw = S * 0.1
    for i, hh in enumerate(heights):
        x = cx - S * 1.25 + i * bw * 1.5 - S * 0.15
        frr(L, (x, cy + S * 0.95 - hh * S, x + bw, cy + S * 0.95), bw * 0.5, pal.hi, pal.deep, angle=90, alpha=0.95)
        glow = new_layer(L.size)
        frr(glow, (x, cy + S * 0.95 - hh * S, x + bw, cy + S * 0.95), bw * 0.5, pal.c, pal.c, alpha=0.5)
        L.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S * 0.03)))
    # nota
    nx, ny = cx + S * 1.3, cy - S * 0.8
    fell(L, (nx - S * 0.15, ny, nx + S * 0.05, ny + S * 0.14), pal.pale, pal.pale)
    stroke(L, "line", [(nx + S * 0.04, ny + S * 0.07), (nx + S * 0.04, ny - S * 0.5), (nx + S * 0.3, ny - S * 0.4)], pal.pale, S * 0.035, 0.9)
    decor(L, cx, cy, S, pal, rnd, 10)


def t_gift(L, cx, cy, S, pal, rnd, mode):
    back = card_piece(int(S * 1.8), int(S * 1.14), pal.deep, "plain", alpha=0.9)
    blit(L, rot(back, 12), cx + S * 0.55, cy - S * 0.45, shadow=0.5)
    cd = card_piece(int(S * 2.05), int(S * 1.3), pal.c, "gift", alpha=0.98)
    blit(L, persp(rot(cd, -8), 0, 0.05), cx - S * 0.05, cy + S * 0.15, shadow=0.6, glow=(pal.c, 0.5, 0.07))
    # konfeti
    palette = [pal.hi, pal.acc, pal.acc2, pal.pale, (255, 214, 90)]
    for i in range(26):
        x = cx + rnd.uniform(-1.4, 1.4) * S
        y = cy + rnd.uniform(-1.2, 1.1) * S
        w, h = S * rnd.uniform(0.04, 0.09), S * rnd.uniform(0.02, 0.04)
        t = new_layer((int(w * 2 + 6), int(w * 2 + 6)))
        frr(t, (3 + w * 0.5, 3 + w * 0.5, 3 + w * 1.5, 3 + w * 0.5 + h), h * 0.3, rnd.choice(palette), rnd.choice(palette))
        blit(L, rot(t, rnd.uniform(0, 180)), x, y, shadow=0.0)
    decor(L, cx, cy, S, pal, rnd, 8)


def tile_piece(s, c1, c2, glyph):
    pad = 6
    img = new_layer((int(s) + 2 * pad, int(s) + 2 * pad))
    box = (pad, pad, pad + s, pad + s)
    frr(img, box, s * 0.23, c1, c2, angle=60)
    gl = new_layer(img.size)
    fpoly(gl, [(pad, pad), (pad + s, pad), (pad, pad + s * 0.6)], WHITE, WHITE, alpha=0.14)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, s * 0.23, fill=255)
    gl.putalpha(ImageChops.multiply(gl.getchannel("A"), m))
    img.alpha_composite(gl)
    stroke(img, "rr", (box, s * 0.23), WHITE, max(2, s * 0.02), 0.4)
    c = pad + s / 2
    g = glyph % 4
    if g == 0:
        fell(img, (c - s * 0.2, c - s * 0.2, c + s * 0.2, c + s * 0.2), WHITE, alpha=0.85)
    elif g == 1:
        frr(img, (c - s * 0.2, c - s * 0.2, c + s * 0.2, c + s * 0.2), s * 0.05, WHITE, WHITE, alpha=0.85)
    elif g == 2:
        fpoly(img, [(c, c - s * 0.24), (c + s * 0.22, c + s * 0.16), (c - s * 0.22, c + s * 0.16)], WHITE, WHITE, alpha=0.85)
    else:
        stroke(img, "ell", (c - s * 0.2, c - s * 0.2, c + s * 0.2, c + s * 0.2), WHITE, s * 0.05, 0.85)
    return img


def t_tiles(L, cx, cy, S, pal, rnd, mode):
    cols = [pal.c, pal.acc, pal.acc2, pal.hi, mix(pal.c, WHITE, 0.2), shade(pal.c, 0.8)]
    n = 0
    s = S * 0.5
    for r in range(3):
        for c in range(3):
            x = cx + (c - 1) * s * 1.18 - S * 0.25 + (r - 1) * s * 0.18
            y = cy + (r - 1) * s * 1.18 - S * 0.12
            c1 = cols[(r * 3 + c) % len(cols)]
            tp = tile_piece(s, shade(c1, 1.25), shade(c1, 0.6), r * 3 + c)
            blit(L, rot(tp, -4), x, y, shadow=0.5, glow=None)
    cd = card_piece(int(S * 1.35), int(S * 0.86), pal.hi, "wallet", alpha=0.96)
    blit(L, rot(cd, -12), cx + S * 0.95, cy + S * 0.72, shadow=0.6, glow=(pal.c, 0.4, 0.06))
    decor(L, cx, cy, S, pal, rnd, 10)


def t_mix(L, cx, cy, S, pal, rnd, mode):
    cd = card_piece(int(S * 1.9), int(S * 1.2), pal.c, "wallet", alpha=0.98)
    blit(L, persp(rot(cd, -10), 0, 0.05), cx - S * 0.1, cy + S * 0.1, shadow=0.6, glow=(pal.c, 0.55, 0.07))
    g = gem_piece(S * 0.5, pal.hi, "brilliant")
    blit(L, rot(g, 12), cx + S * 0.95, cy - S * 0.55, shadow=0.5, glow=(pal.c, 0.5, 0.06))
    co = coin_piece(S * 0.32, (255, 205, 90), 0.85, 0.16, "star")
    blit(L, rot(co, -12), cx - S * 0.95, cy - S * 0.7, shadow=0.5)
    co2 = coin_piece(S * 0.22, (255, 205, 90), 0.85, 0.16, "bolt")
    blit(L, rot(co2, 16), cx + S * 1.1, cy + S * 0.7, shadow=0.5)
    cb = cube_piece(S * 0.2, pal.acc, grid=2)
    blit(L, rot(cb, 14), cx - S * 1.1, cy + S * 0.72, shadow=0.5)
    decor(L, cx, cy, S, pal, rnd, 14)


# tema -> (olcek, dikey kaydirma): kirpilan kompozisyonlari ayarlar
FIT = {"coins": (0.86, 0.04), "flamegems": (0.84, -0.05), "crystals": (0.86, 0.0), "pixels": (0.84, 0.03), "hexcoins": (0.85, 0.04),
       "tiles": (0.9, -0.02), "vinyl": (0.92, 0.0), "shards": (0.95, 0.0), "cardstack": (0.88, 0.02), "plates": (0.95, 0.0),
       "gift": (0.95, 0.0), "orbs": (0.95, 0.0), "mix": (0.95, 0.0)}

THEMES = {
    "cardstack": t_cardstack, "wallet": t_wallet, "cubes": t_cubes, "shards": t_shards, "coins": t_coins, "orbs": t_orbs,
    "flamegems": t_flamegems, "shield": t_shield, "crystals": t_crystals, "voxels": t_voxels, "hexcoins": t_hexcoins,
    "plates": t_plates, "vortex": t_vortex, "soccer": t_soccer, "gamepad": t_gamepad, "pixels": t_pixels, "cinema": t_cinema,
    "vinyl": t_vinyl, "gift": t_gift, "tiles": t_tiles, "mix": t_mix,
}

# --------------------------------------------------------------------------- arka plan


def background(W, H, pal, rnd, focus, pattern, mode):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    dark = np.array(pal.dark, dtype=np.float32)
    mid = np.array(pal.mid, dtype=np.float32)
    deep = np.array(pal.deep, dtype=np.float32)
    if mode == "card":
        t = np.clip(1 - v * 0.95 + (1 - u) * 0.05, 0, 1)
    else:
        t = np.clip(u * 0.85 + (1 - v) * 0.15, 0, 1)
    base = dark[None, None, :] * (1 - t[..., None]) + mid[None, None, :] * t[..., None]
    aspect = W / H
    fx, fy = focus

    def glow(x0, y0, rx, color, amount):
        d = np.sqrt(((u - x0) * aspect) ** 2 + (v - y0) ** 2) / rx
        g = np.exp(-(d ** 2)) * amount
        c = np.array(color, dtype=np.float32)
        return g[..., None], c[None, None, :]

    for (x0, y0, rx, color, amount) in (
        (fx, fy, 0.62 if mode != "card" else 0.5, pal.c, 0.72),
        (fx + (0.2 if mode != "card" else 0.25), fy - 0.25, 0.34, pal.acc, 0.38),
        (0.02 if mode != "card" else 0.95, 1.05 if mode != "card" else 0.02, 0.5, pal.acc2, 0.30),
    ):
        g, c = glow(x0, y0, rx, color, amount)
        base = 255 - (255 - base) * (1 - g * c / 255)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # desen
    pat = new_layer((W, H))
    pd = ImageDraw.Draw(pat)
    unit = (H if mode != "card" else W) / (8.5 if mode != "card" else 9.5)
    ink = tuple(clampc(pal.pale)) + (255,)
    if pattern == "grid":
        step = unit * 0.5
        x = 0.0
        while x < W:
            pd.line([(x, 0), (x, H)], fill=ink, width=SS)
            x += step
        y = 0.0
        while y < H:
            pd.line([(0, y), (W, y)], fill=ink, width=SS)
            y += step
    elif pattern == "dots":
        step = unit * 0.34
        y = step / 2
        while y < H:
            x = step / 2
            while x < W:
                pd.ellipse((x - SS * 1.4, y - SS * 1.4, x + SS * 1.4, y + SS * 1.4), fill=ink)
                x += step
            y += step
    elif pattern == "diag":
        step = unit * 0.42
        k = -H
        while k < W + H:
            pd.line([(k, H), (k + H, 0)], fill=ink, width=SS)
            k += step
    elif pattern == "hex":
        s = unit * 0.34
        for i in range(-2, int(W / (s * 1.5)) + 3):
            for j in range(-2, int(H / (s * 1.732)) + 3):
                x = i * s * 1.5
                y = j * s * 1.732 + (s * 0.866 if i % 2 else 0)
                pts = [(x + s * math.cos(math.pi / 3 * k), y + s * math.sin(math.pi / 3 * k)) for k in range(6)]
                pd.line(pts + [pts[0]], fill=ink, width=SS)
    elif pattern == "rings":
        for k in range(1, 14):
            r = unit * 0.5 * k
            pd.ellipse((fx * W - r, fy * H - r, fx * W + r, fy * H + r), outline=ink, width=SS)
    elif pattern == "circuit":
        step = unit * 0.5
        for _ in range(26):
            x = rnd.randrange(0, int(W / step)) * step
            y = rnd.randrange(0, int(H / step)) * step
            pts = [(x, y)]
            for _ in range(rnd.randint(2, 4)):
                if rnd.random() < 0.5:
                    x += rnd.choice((-1, 1)) * step * rnd.randint(1, 3)
                else:
                    y += rnd.choice((-1, 1)) * step * rnd.randint(1, 3)
                pts.append((x, y))
            pd.line(pts, fill=ink, width=SS)
            pd.ellipse((pts[-1][0] - SS * 3, pts[-1][1] - SS * 3, pts[-1][0] + SS * 3, pts[-1][1] + SS * 3), outline=ink, width=SS)
    elif pattern == "pitch":
        pd.line([(W * 0.5, 0), (W * 0.5, H)], fill=ink, width=SS * 2)
        r = H * 0.34
        pd.ellipse((W * 0.5 - r, H * 0.5 - r, W * 0.5 + r, H * 0.5 + r), outline=ink, width=SS * 2)
        pd.rectangle((W * 0.0 - 4, H * 0.28, W * 0.16, H * 0.72), outline=ink, width=SS * 2)
        pd.rectangle((W * 0.84, H * 0.28, W * 1.0 + 4, H * 0.72), outline=ink, width=SS * 2)
    elif pattern == "pixelgrid":
        step = unit * 0.3
        y = 0.0
        while y < H:
            x = 0.0
            while x < W:
                if rnd.random() < 0.1:
                    pd.rectangle((x + 2, y + 2, x + step - 2, y + step - 2), fill=ink)
                x += step
            y += step
    # desen solma maskesi (odakta gorunur, kenarda silinir)
    d = np.sqrt(((u - fx) * aspect) ** 2 + (v - fy) ** 2)
    fade = np.clip(1.1 - d / (0.95 if mode != "card" else 0.75), 0, 1)
    a = np.array(pat.getchannel("A"), dtype=np.float32) / 255 * fade * 0.075
    # sol yazi bolgesinde daha da hafif
    if mode != "card":
        a *= np.clip(0.4 + u * 1.2, 0, 1)
    pat_arr = np.array(img, dtype=np.float32)
    pc = np.array(pal.pale, dtype=np.float32)
    pat_arr[..., :3] = pat_arr[..., :3] * (1 - a[..., None]) + pc[None, None, :] * a[..., None]
    img = Image.fromarray(np.clip(pat_arr, 0, 255).astype(np.uint8), "RGBA")

    # bokeh (yumusak daireler)
    bk = new_layer((W, H))
    nb = 14 if mode != "card" else 12
    for _ in range(nb):
        r = rnd.uniform(0.03, 0.14) * H
        x = rnd.uniform(0, W)
        y = rnd.uniform(0, H)
        col = rnd.choice((pal.hi, pal.acc, pal.acc2, pal.pale))
        fell(bk, (x - r, y - r, x + r, y + r), col, alpha=rnd.uniform(0.04, 0.13))
        if rnd.random() < 0.5:
            stroke(bk, "ell", (x - r, y - r, x + r, y + r), WHITE, SS, 0.06)
    bk = bk.filter(ImageFilter.GaussianBlur(SS * 3))
    img.alpha_composite(bk)
    # kucuk parcaciklar
    pr = new_layer((W, H))
    for _ in range(46 if mode != "card" else 40):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(0.7, 2.6) * SS
        fell(pr, (x - r, y - r, x + r, y + r), WHITE, alpha=rnd.uniform(0.15, 0.6))
    img.alpha_composite(pr.filter(ImageFilter.GaussianBlur(0.6)))
    return img


def fit_font(path, size):
    return ImageFont.truetype(path, int(size))


def text_w(font, s, tracking=0.0):
    return font.getlength(s) + tracking * max(0, len(s) - 1)


def wrap_lines(text, font, max_w, max_lines):
    words = text.split()
    best = None
    if text_w(font, text) <= max_w:
        return [text]
    if max_lines >= 2:
        cands = []
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            wa, wb = text_w(font, a), text_w(font, b)
            if wa <= max_w and wb <= max_w:
                pen = 1e6 if b[:1] in "/&" else 0
                cands.append((max(wa, wb) + pen, [a, b]))
        if cands:
            return min(cands, key=lambda t: t[0])[1]
    if max_lines >= 3:
        # greedy
        lines, cur = [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if text_w(font, t) <= max_w:
                cur = t
            else:
                if not cur:
                    return None
                lines.append(cur)
                cur = wd
        lines.append(cur)
        if len(lines) <= max_lines and all(text_w(font, l) <= max_w for l in lines):
            return lines
    return None


def draw_text_block(base, name, group, tagline, pal, mode, W, H):
    """Sol blok: grup etiketi + ad + cizgi + aciklama."""
    S = SS
    if mode == "wide":
        x0 = W * 0.06
        max_w = W * 0.47
        name_max, name_min = 74 * S, 46 * S
        tag_size = 25 * S
        chip_size = 17 * S
    else:  # mobile
        x0 = W * 0.06
        max_w = W * 0.5
        name_max, name_min = 46 * S, 30 * S
        tag_size = 22 * S
        chip_size = 0
    # ad
    best = None
    for size in range(int(name_max), int(name_min) - 1, -2 * S):
        f = fit_font(F_BOLD, size)
        ln = wrap_lines(name, f, max_w, 1)
        if ln and size >= name_max * 0.78:
            best = (size, f, ln)
            break
    if not best:
        for size in range(int(name_max), int(name_min) - 1, -2 * S):
            f = fit_font(F_BOLD, size)
            ln = wrap_lines(name, f, max_w, 2)
            if ln:
                best = (size, f, ln)
                break
    if not best:
        f = fit_font(F_BOLD, name_min)
        ln = wrap_lines(name, f, max_w, 3) or [name]
        best = (name_min, f, ln)
    nsize, nfont, nlines = best
    lh = nsize * 1.12
    tfont = fit_font(F_MED, tag_size)
    tlines = wrap_lines(tagline, tfont, max_w * 0.96, 2) or [tagline]
    tlh = tag_size * 1.4
    chip_h = chip_size * 2.0
    block_h = (chip_h + chip_size * 0.9 if chip_size else 0) + lh * len(nlines) + nsize * 0.28 + 6 * S + nsize * 0.3 + tlh * len(tlines)
    y = (H - block_h) / 2 + (0 if mode == "wide" else -H * 0.02)
    layer = new_layer(base.size)
    d = ImageDraw.Draw(layer)
    sh = Image.new("L", base.size, 0)
    sd = ImageDraw.Draw(sh)
    if chip_size:
        cf = fit_font(F_BOLD, chip_size)
        label = group.replace("i", "İ").upper() if group else ""
        tr = chip_size * 0.14
        tw = text_w(cf, label, tr)
        cw = tw + chip_size * 2.6
        box = (x0, y, x0 + cw, y + chip_h)
        d.rounded_rectangle(box, chip_h / 2, fill=tuple(clampc(mix(pal.c, INK, 0.5))) + (170,), outline=tuple(clampc(pal.hi)) + (150,), width=SS)
        dot = chip_size * 0.32
        d.ellipse((x0 + chip_size * 0.9, y + chip_h / 2 - dot, x0 + chip_size * 0.9 + 2 * dot, y + chip_h / 2 + dot), fill=tuple(clampc(pal.hi)) + (255,))
        tx = x0 + chip_size * 0.9 + 2 * dot + chip_size * 0.6
        for ch in label:
            d.text((tx, y + chip_h / 2), ch, font=cf, fill=(255, 255, 255, 235), anchor="lm")
            tx += cf.getlength(ch) + tr
        y += chip_h + chip_size * 0.9
    # ad (golge icin ayri maske)
    name_mask = Image.new("L", base.size, 0)
    nd = ImageDraw.Draw(name_mask)
    for i, ln in enumerate(nlines):
        nd.text((x0, y + i * lh), ln, font=nfont, fill=255, anchor="la")
        sd.text((x0, y + i * lh), ln, font=nfont, fill=255, anchor="la")
    shadow = Image.new("RGBA", base.size, (0, 0, 8, 0))
    shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(7 * S)).point(lambda v: int(v * 0.65)))
    base.alpha_composite(shadow)
    # ad dolgusu: beyazdan acik tona dikey gradyan
    ng = grad_img(base.size, [(0, WHITE), (1, mix(pal.pale, WHITE, 0.55))], 90)
    ng.putalpha(name_mask)
    base.alpha_composite(layer)
    base.alpha_composite(ng)
    y += lh * len(nlines) + nsize * 0.12
    # vurgu cizgisi
    bar = new_layer(base.size)
    frr(bar, (x0, y, x0 + nsize * 1.6, y + 5 * S), 3 * S, pal.hi, pal.acc, angle=0)
    base.alpha_composite(bar)
    y += 5 * S + nsize * 0.3
    # aciklama
    tl = new_layer(base.size)
    td = ImageDraw.Draw(tl)
    tsh = Image.new("L", base.size, 0)
    tsd = ImageDraw.Draw(tsh)
    for i, ln in enumerate(tlines):
        td.text((x0, y + i * tlh), ln, font=tfont, fill=(236, 240, 250, 235), anchor="la")
        tsd.text((x0, y + i * tlh), ln, font=tfont, fill=255, anchor="la")
    tshadow = Image.new("RGBA", base.size, (0, 0, 8, 0))
    tshadow.putalpha(tsh.filter(ImageFilter.GaussianBlur(4 * S)).point(lambda v: int(v * 0.6)))
    base.alpha_composite(tshadow)
    base.alpha_composite(tl)


def scrim(base, mode, pal):
    """Yazi okunurlugu icin soldan koyulastirma."""
    W, H = base.size
    if mode == "card":
        return
    xs = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    end = 0.62 if mode == "wide" else 0.78
    a = np.clip(1 - xs / end, 0, 1) ** 1.35 * (0.62 if mode == "wide" else 0.58)
    a = np.repeat(a, H, axis=0)
    ink = np.array(mix(pal.dark, INK, 0.5), dtype=np.float32)
    arr = np.array(base, dtype=np.float32)
    arr[..., :3] = arr[..., :3] * (1 - a[..., None]) + ink[None, None, :] * a[..., None]
    base.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"))


def finish(img, rnd_seed, grain):
    """Vinyet + hafif film greni."""
    W, H = img.size
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx / W - 0.5) * 1.15) ** 2 + ((yy / H - 0.5) * 1.15) ** 2)
    vig = 1 - np.clip((d - 0.38) / 0.55, 0, 1) ** 1.6 * 0.42
    arr *= vig[..., None]
    rng = np.random.default_rng(rnd_seed)
    noise = rng.normal(0, grain, size=(H, W, 1)).astype(np.float32)
    arr += noise
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def encode(img, limit_kb, path):
    for q in (90, 88, 86, 84, 82, 80, 78, 75, 72, 68, 64):
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=q, method=6)
        if buf.tell() <= limit_kb * 1024:
            break
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    return buf.tell(), q


def render(args):
    slug, name, group, color, tagline, theme, pattern = args[:7]
    which = args[7] if len(args) > 7 else list(LAYOUTS)
    pal = Pal(color)
    res = []
    for mode in which:
        fw, fh, prefix, limit = LAYOUTS[mode]
        W, H = fw * SS, fh * SS
        seed = sum(ord(c) * (i + 3) for i, c in enumerate(slug)) + len(mode)
        rnd = random.Random(seed)
        sc, dyo = FIT.get(theme, (1.0, 0.0))
        if mode == "wide":
            focus = (0.745, 0.5 + dyo)
            S = H * 0.36 * sc
        elif mode == "mobile":
            focus = (0.80, 0.58 + dyo)
            S = H * 0.24 * sc
        else:
            focus = (0.5, 0.42 + dyo * 0.6)
            S = W * 0.33 * sc
        base = background(W, H, pal, rnd, focus, pattern, mode)
        if mode != "card":
            scrim(base, mode, pal)
        L = new_layer((W, H))
        THEMES[theme](L, focus[0] * W, focus[1] * H, S, pal, rnd, mode)
        base.alpha_composite(L)
        if mode != "card":
            draw_text_block(base, name, group, tagline, pal, mode, W, H)
        img = finish(base, seed, 1.8)
        img = img.resize((fw, fh), Image.LANCZOS)
        path = os.path.join(OUT, prefix + slug + ".webp")
        size, q = encode(img, limit, path)
        res.append((slug, mode, size, q))
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    jobs = [c for c in CATS if not want or c[0] in want]
    with Pool(min(4, os.cpu_count() or 2)) as p:
        for out in p.imap_unordered(render, jobs):
            for slug, mode, size, q in out:
                print(f"{slug:16s} {mode:7s} {size / 1024:6.1f} KB  q={q}", flush=True)


if __name__ == "__main__":
    main()

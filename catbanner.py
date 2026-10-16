"""Kategori görselleri.

Yüklenmiş görsel (categories.image) varsa o, yoksa public/static/kategori/ altındaki varsayılan banner
(kaynak: static_src/kategori/, templates_gen.generate kopyalar), o da yoksa genel yedek.
kind: 'wide' (1600x480), 'mobile' (640x400), 'card' (720x960).
"""
import re
from functools import lru_cache

from flask import url_for

import core
import services

_PREFIX = {"wide": "", "mobile": "mobil-", "card": "kart-"}
_DIR = core.BASE_DIR / "public" / "static" / "kategori"
_SLUG_CLEAN = re.compile(r"[^a-z0-9-]")


@lru_cache(maxsize=256)
def _default_file(kind, slug):
    """(dosya adı, sürüm) döner; dosya yoksa genel yedeğe düşer."""
    prefix = _PREFIX.get(kind, "")
    name = prefix + slug + ".webp"
    if not slug or not (_DIR / name).is_file():
        name = prefix + "genel.webp"
    try:
        version = int((_DIR / name).stat().st_mtime)
    except OSError:
        version = 0
    return name, version


def category_banner_url(cat, kind="wide"):
    row = cat if hasattr(cat, "keys") or isinstance(cat, dict) else None
    img = (row["image"] if row is not None and "image" in row.keys() else "") or ""
    if img and services.MEDIA_NAME_RE.match(img):
        return url_for("media_cover", name=img)
    slug = _SLUG_CLEAN.sub("", str((row["slug"] if row is not None and "slug" in row.keys() else "") or "").lower())
    name, version = _default_file(kind, slug)
    return url_for("static", filename="kategori/" + name) + (f"?v={version}" if version else "")

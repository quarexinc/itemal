"""Görsel depolama: dosya sistemi yerine veritabanındaki `media` tablosu.

Vercel gibi ortamlarda disk kalıcı olmadığı için kapak, avatar, banner ve kimlik görselleri BLOB olarak saklanır.
Yerelde (SQLite) aynı kod çalışır. Adlar rastgele uuid olduğundan herkese açık görseller değişmez kabul edilir.
"""
import io
import re

import core
from core import ex, q1

MIME = {"webp": "image/webp", "jpg": "image/jpeg", "png": "image/png"}


def put(kind, name, data, mime=None):
    mime = mime or MIME.get(name.rsplit(".", 1)[-1], "application/octet-stream")
    ex(
        "INSERT INTO media(kind, name, mime, size, data) VALUES (?,?,?,?,?)"
        " ON CONFLICT(kind, name) DO UPDATE SET mime = excluded.mime, size = excluded.size, data = excluded.data",
        (kind, name, mime, len(data), bytes(data)),
    )


_LEGACY_DIRS = {"cover": "covers", "avatar": "avatars", "kyc": "kyc"}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_]+\.(webp|jpg|png)$")


def _legacy(kind, name):
    """Eski sürümde uploads/ klasörüne yazılmış dosyayı bulursa veritabanına aktarıp (mime, bayt) döndürür."""
    folder = _LEGACY_DIRS.get(kind)
    if not folder or not _SAFE_NAME.match(name or ""):
        return None
    path = core.BASE_DIR / "uploads" / folder / name
    try:
        data = path.read_bytes()
    except OSError:
        return None
    put(kind, name, data)
    return MIME.get(name.rsplit(".", 1)[-1], "application/octet-stream"), data


def get(kind, name):
    """(mime, bayt) ya da None. Veritabanında yoksa eski uploads/ klasörüne bakar ve bulduğunu aktarır."""
    row = q1("SELECT mime, data FROM media WHERE kind = ? AND name = ?", (kind, name))
    if row:
        return row["mime"], bytes(row["data"])
    return _legacy(kind, name)


def delete(kind, *names):
    for name in names:
        if name:
            ex("DELETE FROM media WHERE kind = ? AND name = ?", (kind, name))


def total_size():
    row = q1("SELECT COALESCE(SUM(size), 0) AS s, COUNT(*) AS n FROM media")
    return row["s"], row["n"]


def save_image(img, kind, name, fmt="WEBP", **params):
    """Pillow görselini kodlayıp kaydeder (EXIF/konum bilgisi zaten yeniden kodlamayla düşer)."""
    buf = io.BytesIO()
    img.save(buf, fmt, **params)
    put(kind, name, buf.getvalue(), MIME["webp" if fmt.upper() == "WEBP" else "jpg"])

"""TOTP (RFC 6238) ve yedek kodlar. Yalnızca standart kütüphane; QR için isteğe bağlı `segno`.

Yönetici ve kullanıcı iki adımlı doğrulaması aynı API'yi kullanır:
  gen_secret()                       -> 32 karakterlik base32 gizli anahtar
  verify(secret, code, window, last) -> kabul edilen zaman adımı (int) ya da None
  otpauth_uri(secret, hesap, issuer) -> authenticator uygulamalarının okuduğu otpauth:// adresi
  qr_svg(text)                       -> satır içi SVG metni ya da None (segno yoksa)
  new_backup_codes(n)                -> (açık liste, hash listesi)
  check_backup(code, hashes)         -> eşleşen indeks ya da None
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

STEP = 30
DIGITS = 6
_BACKUP_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"     # 0/o, 1/l/i gibi karışan karakterler yok


def gen_secret():
    """160 bit rastgele -> 32 karakter base32 (dolgusuz)."""
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _key(secret_b32):
    s = "".join((secret_b32 or "").split()).upper()
    s += "=" * (-len(s) % 8)
    return base64.b32decode(s, casefold=True)


def _hotp(key, counter):
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    num = (struct.unpack(">I", mac[off:off + 4])[0] & 0x7FFFFFFF) % (10 ** DIGITS)
    return str(num).zfill(DIGITS)


def code_at(secret_b32, for_time=None):
    """Verilen anın 6 haneli kodu (test ve kurulum için)."""
    t = time.time() if for_time is None else for_time
    return _hotp(_key(secret_b32), int(t // STEP))


def verify(secret_b32, code, window=1, last_step=None, now=None):
    """Kodu doğrular. Geçerliyse kabul edilen zaman adımını döner; `last_step` ve öncesi reddedilir
    (aynı kodun yeniden kullanımı). Geçersizse None."""
    code = "".join(str(code or "").split())
    if len(code) != DIGITS or not code.isdigit() or not code.isascii():
        return None
    try:
        key = _key(secret_b32)
    except (ValueError, TypeError):
        return None
    counter = int((time.time() if now is None else now) // STEP)
    found = None
    for step in range(counter - window, counter + window + 1):         # tüm pencere taranır: süre, eşleşen adıma göre değişmez
        if hmac.compare_digest(_hotp(key, step).encode(), code.encode()):
            if last_step is None or step > last_step:
                found = step if found is None else max(found, step)
    return found


def otpauth_uri(secret, account, issuer="itemal"):
    label = quote(f"{issuer}:{account}", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer, safe='')}&algorithm=SHA1&digits={DIGITS}&period={STEP}"


def qr_svg(text):
    """Satır içi SVG (koyu zemin üstünde okunsun diye beyaz zeminli). segno yoksa None."""
    try:
        import segno
        import io

        buf = io.BytesIO()
        segno.make(text, error="m", micro=False).save(
            buf, kind="svg", scale=5, border=2, dark="#000000", light="#ffffff", xmldecl=False, nl=False, svgns=True
        )
        svg = buf.getvalue().decode("utf-8")
        return svg
    except Exception:
        return None


def _norm_backup(code):
    return "".join(ch for ch in str(code or "").lower() if ch.isalnum())


def _hash_backup(code):
    return hashlib.sha256(("itemal-backup|" + _norm_backup(code)).encode()).hexdigest()


def new_backup_codes(n=10):
    """('xxxxx-xxxxx' biçiminde açık kodlar, sha256 hash listesi). Açık kodlar yalnızca bir kez gösterilir."""
    plain = []
    for _ in range(n):
        raw = "".join(secrets.choice(_BACKUP_ALPHABET) for _ in range(10))
        plain.append(raw[:5] + "-" + raw[5:])
    return plain, [_hash_backup(c) for c in plain]


def check_backup(code, hash_list):
    """Eşleşen kodun indeksi ya da None. Tüm liste sabit zamanlı karşılaştırılır."""
    norm = _norm_backup(code)
    if len(norm) != 10:
        return None
    digest = _hash_backup(norm)
    hit = None
    for i, h in enumerate(hash_list or []):
        if hmac.compare_digest(str(h).encode(), digest.encode()) and hit is None:
            hit = i
    return hit

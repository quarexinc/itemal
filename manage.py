"""Yönetim komutları.

  python manage.py hash-admin     Yönetici şifresini sorar, .env'ye ADMIN_PASSWORD_HASH olarak yazar, düz metni siler.
  python manage.py build         templates/ ve public/static/ dosyalarını üretir (Vercel'e göndermeden önce çalıştır).
  python manage.py init-db        Veritabanı şemasını kurar/günceller (TURSO_DATABASE_URL tanımlıysa Turso'da).
  python manage.py migrate-files  Eski uploads/ klasöründeki görselleri veritabanına (media tablosuna) aktarır.
  python manage.py admin-2fa-reset  Yönetici iki adımlı doğrulama kaydını siler (telefon/yedek kodlar kaybolduysa acil kurtarma).
                                  Sonraki girişte ADMIN_2FA=required ise yeniden kurulum istenir. Geçici çözüm: .env'e ADMIN_2FA=off.
  python manage.py new-secret     Yeni rastgele SECRET_KEY üretir (yazdırır; .env'ye elle koy. Değişince herkes çıkış yapar
                                  ve varsa şifreli saklanan ayarlar okunamaz hale gelir).
"""
import getpass
import os
import re
import secrets
import stat
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

ENV = Path(__file__).resolve().parent / ".env"


def set_env_values(updates, remove=()):
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out, seen = [], set()
    for line in lines:
        m = re.match(r"^\s*([A-Z0-9_]+)\s*=", line)
        key = m.group(1) if m else None
        if key in remove:
            continue
        if key in updates:
            out.append(f"{key}='{updates[key]}'")
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}='{value}'")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def hash_admin():
    pw = getpass.getpass("Yeni yönetici şifresi (en az 12 karakter): ")
    if len(pw) < 12:
        sys.exit("Şifre en az 12 karakter olmalı.")
    if pw != getpass.getpass("Şifre tekrar: "):
        sys.exit("Şifreler eşleşmiyor.")
    set_env_values({"ADMIN_PASSWORD_HASH": generate_password_hash(pw)}, remove=("ADMIN_PASSWORD",))
    print(".env güncellendi: ADMIN_PASSWORD_HASH yazıldı, düz metin şifre silindi. Uygulamayı yeniden başlat.")


def new_secret():
    print(secrets.token_urlsafe(48))


def _load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv(ENV)
    except ImportError:
        pass


def build():
    import templates_gen

    base = Path(__file__).resolve().parent
    templates_gen.generate(str(base), force=True)
    print("Üretildi: templates/ ve public/static/")


def init_db_cmd():
    _load_env()
    import core
    import db as dbm

    ran = dbm.ensure_ready(core.DB_PATH)
    print(("Şema kuruldu/güncellendi" if ran else "Şema zaten güncel") + (" (Turso)" if dbm.remote() else " (yerel SQLite)"))


def admin_2fa_reset():
    """settings tablosundaki admin_2fa_* kayıtlarını siler (gizli anahtar, yedek kodlar, son adım)."""
    _load_env()
    import core
    import db as dbm

    dbm.ensure_ready(core.DB_PATH)
    conn = dbm.connect(core.DB_PATH)
    try:
        n = conn.execute("SELECT COUNT(*) FROM settings WHERE key LIKE 'admin\\_2fa\\_%' ESCAPE '\\'").fetchone()[0]
        conn.execute("DELETE FROM settings WHERE key LIKE 'admin\\_2fa\\_%' ESCAPE '\\'")
        conn.execute("INSERT INTO admin_log(action, detail, ip) VALUES (?,?,?)", ("İki adımlı doğrulama sıfırlandı", "komut satırı: manage.py admin-2fa-reset", "cli"))
    finally:
        conn.close()
    print("İki adımlı doğrulama kaydı silindi." if n else "Kayıtlı iki adımlı doğrulama yoktu.")
    print("Bir sonraki yönetici girişinde (ADMIN_2FA=required ise) kurulum yeniden istenir.")


def migrate_files():
    """uploads/covers, uploads/avatars, uploads/kyc -> media tablosu (var olan adlar atlanır)."""
    _load_env()
    import core
    import db as dbm
    import storage
    from flask import Flask

    dbm.ensure_ready(core.DB_PATH)
    app = Flask("migrate")
    n = 0
    with app.app_context():
        core.get_db()
        for kind, folder in (("cover", "covers"), ("avatar", "avatars"), ("kyc", "kyc")):
            d = Path(__file__).resolve().parent / "uploads" / folder
            if not d.is_dir():
                continue
            for f in sorted(d.iterdir()):
                if f.is_file() and not storage.get(kind, f.name):
                    storage.put(kind, f.name, f.read_bytes())
                    n += 1
        core.close_db()
    print(f"{n} dosya veritabanına aktarıldı.")


if __name__ == "__main__":
    cmds = {"hash-admin": hash_admin, "new-secret": new_secret, "build": build, "init-db": init_db_cmd, "migrate-files": migrate_files, "admin-2fa-reset": admin_2fa_reset}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]]()

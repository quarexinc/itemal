"""Şablonları ve statik dosyaları diske yazar. Uygulama her açılışta bunu çağırır."""
import os
import shutil

import assets
import assets_icons
import tpl_account
import tpl_doping
import tpl_admin1
import tpl_admin2
import tpl_admin3
import tpl_public
import tpl_seller
import tpl_packages
import tpl_paylink
import tpl_trust
import tpl_plus
import tpl_community

MODULES = (tpl_public, tpl_account, tpl_seller, tpl_admin1, tpl_admin2, tpl_admin3, tpl_trust, tpl_paylink, tpl_packages, tpl_doping, tpl_plus, tpl_community)


def all_templates():
    merged = {}
    for mod in MODULES:
        for name, body in mod.TEMPLATES.items():
            if name in merged:
                raise RuntimeError(f"Şablon adı çakışıyor: {name}")
            merged[name] = body
    merged["_sprite.html"] = assets_icons.sprite()
    return merged


def _write(path, text, force):
    if os.path.exists(path) and not force:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.lstrip("\n"))
    os.replace(tmp, path)


def _copy_binary(src, dst, force):
    """İkili dosyayı (görsel) kopyalar; hedef aynıysa dokunmaz."""
    if os.path.exists(dst):
        if not force:
            return
        if os.path.getsize(dst) == os.path.getsize(src):
            with open(src, "rb") as a, open(dst, "rb") as b:
                if a.read() == b.read():
                    return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".tmp"
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def copy_static_src(base_dir, force=True):
    """static_src/ (ikili kaynaklar: kategori bannerları) -> public/static/ (aynı alt yollarla)."""
    root = os.path.join(base_dir, "static_src")
    for folder, _dirs, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(".tmp"):
                continue
            src = os.path.join(folder, name)
            _copy_binary(src, os.path.join(base_dir, "public", "static", os.path.relpath(src, root)), force)


def generate(base_dir, force=True):
    """templates/ ve public/static/ klasörlerini oluşturur. force=False ise var olan dosyalara dokunmaz (elle düzenlemeler korunur)."""
    for name, body in all_templates().items():
        _write(os.path.join(base_dir, "templates", name), body, force)
    for name, body in assets.FILES.items():
        _write(os.path.join(base_dir, "public", "static", name), body, force)
    copy_static_src(base_dir, force)
